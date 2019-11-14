void send_command(char code, unsigned long value = 0);
bool have_command(char & code, unsigned long & value);

unsigned long previous_time = 0;

int target_vx = 0; // command-requested velocity vector components [-127..127]
int target_vy = 0; // where vx=-127 is left, vx=127 is right, vx=0 is straight

int actual_vx = 0; // actual velocity vector components [-127..127]
int actual_vy = 0; // i.e., calculated from encoders

void setup() {
  Serial.begin(115200);

  pinMode(LED_BUILTIN, OUTPUT);

  previous_time = millis();
}

float eff_div_v(float v) {
  float edv = 0;

  if (v <= 0.5) {
    edv = 2 * 0.9375 * (2 * v * (2 * v - 3) + 3);
  } else {
    edv = (v - 0.5) / 0.5;
    edv = 0.9375 * (1 - 0.1 * edv * edv) / v;

    if (v > 0.95) {
      float decay = (v - 0.95) / 0.06;
      edv *= 1 - decay * decay;
    }
  }
  return edv;
}

void fake_car(bool bPrint = false) { // mimic a car to create a feedback loop
  static float v1 = 0; // velocity motor 1 [-1..1]
  static float v2 = 0; // velocity motor 2 [-1..1]

  const float mass = 40;            // kg
  const float inertia = 45;         // kg.m2
  const float max_speed = 15 / 3.6; // m/s
  const float motor = 250;          // rating, W
  const float dt = 1E-3;            // s (time step)
  const float gauge = 1.5;          // x-axis separation of wheels

  const float coefficient = motor / max_speed;

  float max_T1 = coefficient * eff_div_v(abs(v1));
  float max_T2 = coefficient * eff_div_v(abs(v2));

  float vx = ((float) target_vx) / 127;
  float vy = ((float) target_vy) / 127;

  float target_v1;
  float target_v2;

  if (target_vx >= 0) {
    target_v1 = vy + vy * vx - vx;
    target_v2 = vy - vy * vx + vx;
  } else {
    target_v1 = vy + vy * vx + vx;
    target_v2 = vy - vy * vx - vx;
  }

  // v. clumsy control system:
  float T1 = max_T1 * ((target_v1 > v1) ? 1 : -1) / 20; // applied tractions
  float T2 = max_T2 * ((target_v2 > v2) ? 1 : -1) / 20;

  float a = (T1 + T2) / mass;
  float alpha = (T1 - T2) * (gauge / 2) / inertia;

  float dv = a * dt;
  float domega = alpha * dt;

  if (bPrint) {
    Serial.print(" < v1=");
    Serial.print(v1);
    Serial.print(", v2=");
    Serial.print(v2);
    Serial.print("; target: v1=");
    Serial.print(target_v1);
    Serial.print(", v2=");
    Serial.print(target_v2);
    Serial.print("; traction: T1=");
    Serial.print(T1);
    Serial.print(", T2=");
    Serial.print(T2);
    Serial.print("; acc: a=");
    Serial.print(a);
    Serial.print(", alpha=");
    Serial.print(alpha);
    Serial.print(" > ");
  }

  v1 += dv + domega * gauge / 1.414;
  v2 += dv - domega * gauge / 1.414;

  v1 = (v1 > 1) ? 1 : ((v1 < -1) ? -1 : v1); // range check
  v2 = (v2 > 1) ? 1 : ((v2 < -1) ? -1 : v2);

  vy = (v1 + v2) / 2;
  if (vy >= 0) {
    vx = (v2 - v1) / (2 * (1 - vy));
  } else {
    vx = (v1 - v2) / (2 * (1 + vy));
  }
  actual_vx = (int) round(127 * vx);
  actual_vy = (int) round(127 * vy);
}

void every_milli() { // runs once a millisecond, on average
  char code;
  unsigned long value;

  while (have_command(code, value)) {
    // process the command-value pair
    // e.g.:
    if (value < 255) {
      if (code == 'x') {
        target_vx = -127 + (int) value;
      }
      if (code == 'y') {
        target_vy = -127 + (int) value;
      }
    }
    if (code == 'p') {
      Serial.print(" < ping! > ");
    }
    if (false && code == 'Q') { // silence on the input line - no connection? suggest an emergency stop...
      Serial.print(" < stop! > ");
      target_vx = 0;
      target_vy = 0;
    }
  }

  fake_car(); // mimic a car to create a feedback loop
}

void every_tenth(int tenth) { // runs once every tenth of a second, where tenth = 0..9
  digitalWrite(LED_BUILTIN, tenth == 0 || tenth == 8); // double blink per second

  send_command('x', (unsigned long) (127 + actual_vx)); // send latest info on velocity
  send_command('y', (unsigned long) (127 + actual_vy));
}

void every_second() { // runs once every second
  Serial.println(""); // break the line for human readability in the console
  fake_car(true);
}

void loop() {
  // add code here that can't wait



  // our little internal real-time clock:
  static int count_ms = 0;
  static int count_tenths = 0;

  unsigned long current_time = millis();

  if (current_time != previous_time) {
    ++previous_time;
    every_milli();

    if (++count_ms == 100) {
      count_ms = 0;
      every_tenth(count_tenths);

      if (++count_tenths == 10) {
        count_tenths = 0;
        every_second();
      }
    }
  }
}

void send_command(char code, unsigned long value) {
  Serial.print(code);
  if (value) {
    Serial.print(value);
  }
  Serial.print(',');
}

bool have_command(char & code, unsigned long & value) {
  static int count = 0;
  static int length = 0;
  static char buffer[16];

  if (++count == 1000) { // silence or junk on the input line! (emergency stop support feature)
    code = 'Q';
    value = 0;
    count = 0;
    return true;
  }
  while (Serial.available()) {
    char next = (char) Serial.read();

    if ((next >= 'A' && next <= 'Z') || (next >= 'a' && next <= 'z')) {
      buffer[0] = next;
      length = 1;
    } else if (next >= '0' && next <= '9') {
      if (length > 0 && length < 11) {
        buffer[length++] = next;
      } else {
        length = 0;
      }
    } else if (next == ',') {
      if (length > 1) {
        buffer[length] = 0;
        code = buffer[0];
        value = strtoul(buffer+1, 0, 10);
        count = 0; // reset the timeout
        break;
      } else if (length == 1) {
        code = buffer[0];
        value = 0;
        count = 0; // reset the timeout
        break;
      }
      length = 0;
    } else {
      length = 0;
    }
  }
  return count == 0;
}
