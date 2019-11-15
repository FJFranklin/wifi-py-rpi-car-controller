#define RangeCheck(x,L) ((x) > (L)) ? (L) : (((x) < -(L)) ? -(L) : (x))

void send_command(char code, unsigned long value = 0);
bool have_command(char & code, unsigned long & value);

unsigned long previous_time = 0;

float target_vx = 0; // command-requested velocity vector components [-1..1]
float target_vy = 0; // where vx=-1 is left, vx=1 is right, vx=0 is straight

float actual_vx = 0; // actual velocity vector components [-1..1]
float actual_vy = 0; // e.g., calculated from encoders

float slip_left = 0; // traction to slip-threshold ratio
float slip_right = 0;

bool bEnableSafetyStop = true;

void setup() {
  Serial.begin(115200);

  pinMode(LED_BUILTIN, OUTPUT);

  previous_time = millis();
}

static inline float byte_to_norm(unsigned long value) { // convert integer in range 0..254 to floating point number in range -1..1
  float f = 0;

  if (value < 255) {
    f = (-127.0 +(float) value) / 127.0;
  }
  return f;
}

static inline unsigned long norm_to_byte(float value) { // convert floating point number in range -1..1 to integer in range 0..254
  int ival = (int) round(127 * value);

  return (unsigned long) (127 + RangeCheck(ival, 127));
}

float eff_div_v(float v) { // motor efficiency divided by velocity fraction, i.e., v in [0..1]
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
  const float friction = 0.2;

  const float slip_T = friction * 9.81 * mass / 4;

  float max_T1 = eff_div_v(abs(v1)) * motor / max_speed;
  float max_T2 = eff_div_v(abs(v2)) * motor / max_speed;

  float target_v1;
  float target_v2;

  if (target_vy >= 0) {
    target_v1 = target_vy + target_vy * target_vx - target_vx;
    target_v2 = target_vy - target_vy * target_vx + target_vx;
  } else {
    target_v1 = target_vy - target_vy * target_vx - target_vx;
    target_v2 = target_vy + target_vy * target_vx + target_vx;
  }

  // v. clumsy control system:
  float T1 = max_T1 * ((target_v1 > v1) ? 1 : -1); // applied tractions
  float T2 = max_T2 * ((target_v2 > v2) ? 1 : -1);

  slip_right = T1 / slip_T;
  slip_left  = T2 / slip_T;

  T1 = RangeCheck(T1, slip_T); // traction limit because of friction / slip
  T2 = RangeCheck(T2, slip_T); // limit traction to range [-slip_T..slip_T]

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
    Serial.print(", slip=");
    Serial.print(slip_T);
    Serial.print("; acc: a=");
    Serial.print(a);
    Serial.print(", alpha=");
    Serial.print(alpha);
    Serial.print(" > ");
  }

  v1 += dv + domega * gauge / 1.414; // assumes square-ish vehicle
  v2 += dv - domega * gauge / 1.414;

  v1 = RangeCheck(v1, 1); // limit v1 to range [-1..1]
  v2 = RangeCheck(v2, 1);

  actual_vy = (v1 + v2) / 2;

  float dy = (actual_vy >= 0) ? (1 - actual_vy) : (1 + actual_vy);
  if (dy > 0) {
    actual_vx = (v2 - v1) / (2 * dy);
    actual_vx = RangeCheck(actual_vx, 1); // limit actual_vx to range [-1..1]
  } else {
    actual_vx = 0; // doesn't actually matter; may look odd on the screen, though
  }
}

void every_milli() { // runs once a millisecond, on average
  char code;
  unsigned long value;

  while (have_command(code, value)) {
    // process the command-value pair
    // e.g.:
    if (value < 255) {
      if (code == 'x') {
        target_vx = byte_to_norm(value);
      }
      if (code == 'y') {
        target_vy = byte_to_norm(value);
      }
    }
    if (code == 'p') {
      Serial.print(" < ping! > ");
    }
    if (code == 'q') { // emergency stop...
      Serial.print(" < command: stop! > ");
      target_vx = 0;
      target_vy = 0;
    }
    if (code == 'Q') { // silence on the input line - no connection? suggest an emergency stop...
      Serial.print(" < auto: stop! > ");
      target_vx = 0;
      target_vy = 0;
    }
  }

  fake_car(); // mimic a car to create a feedback loop
}

void every_tenth(int tenth) { // runs once every tenth of a second, where tenth = 0..9
  digitalWrite(LED_BUILTIN, tenth == 0 || tenth == 8); // double blink per second

  send_command('x', norm_to_byte(actual_vx)); // send latest info on velocity
  send_command('y', norm_to_byte(actual_vy));
  send_command('l', norm_to_byte(slip_left)); // send latest info on traction / slip
  send_command('r', norm_to_byte(slip_right));
}

void every_second() { // runs once every second
  Serial.println(""); // break the line for human readability in the console
  // fake_car(true);  // this will print out the values (for debugging purposes)
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
    count = 0; // reset counter - this triggers once per second if no commands are input

    if (bEnableSafetyStop) {
      code = 'Q';
      value = 0;
      return true;
    }
    return false;
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
