#include "util.hh"
#include "pinservo.hh"
#include "pinmanager.hh"

static const char s_usage_help[] PROGMEM = "help [all|servo]";
static const char s_usage_echo[] PROGMEM = "echo on|off";
static const char s_usage_list[] PROGMEM = "list [digital|analog]";
static const char s_usage_dout[] PROGMEM = "dout [~]<pin#2-13> [[~]<pin#2-13>]*";
static const char s_usage_led[] PROGMEM  = "led on|off";

static const char s_err_help[] PROGMEM   = "help: expected one of: \"all\", \"servo\"";
static const char s_err_pin_no[] PROGMEM = "invalid pin number";

class APin {
public:
  unsigned int m_flags;

  APin (unsigned int flags) :
    m_flags(flags)
  {
    // ...
  }

  ~APin () {
    // ...
  }

  void status (int pin_no) const {
    String state("A-Pin A");
    state = (state + pin_no) + " -";

    Serial.println (state);
  }
};

#define DPIN_SERVO (1<<0)
#define DPIN_D_OUT (1<<1)

class DPin {
public:
  unsigned int m_flags; // can it be used for...?
  int m_pin_no;

  enum PinType {
    pt_None = 0,
    pt_Servo,
    pt_D_In,
    pt_D_Out
  } m_type;

  union {
    PinServo * servo;
    bool digital_value;
  } m_data;

  DPin (unsigned int flags, int pin_no) :
    m_flags(flags),
    m_pin_no(pin_no),
    m_type(pt_None)
  {
    // ...
  }

  ~DPin () {
    clear ();
  }

  void status () const {
    String state("D-Pin ");
    state = (state + m_pin_no) + " ";
    if (m_type == pt_None)
      state += "-";
    else if (m_type == pt_Servo)
      state += "servo";
    else if (m_type == pt_D_Out)
      state += "digital out";

    Serial.println (state);
  }

  void clear () {
    if (m_type == pt_Servo) {
      delete m_data.servo;
    } else if (m_type == pt_D_Out) {
      pinMode (m_pin_no, INPUT);
    }
    m_type = pt_None;
  }

  PinServo * servo () {
    if (m_type != pt_Servo) {
      clear ();

      m_data.servo = new PinServo(m_pin_no);

      if (m_data.servo) // TODO: Check - how does the arduino handle memory errors?
	m_type = pt_Servo;
    }
    return m_data.servo;
  }

  void dpin_write (bool value) {
    if (m_type != pt_D_Out) {
      clear ();

      pinMode (m_pin_no, OUTPUT);
      m_type = pt_D_Out;
    }
    m_data.digital_value = value;

    if (value)
      digitalWrite (m_pin_no, HIGH);
    else
      digitalWrite (m_pin_no, LOW);
  }
};


PinManager::PinManager () {
  /* initialise analog pins
   */
  for (int i = 0; i < 6; i++) {
    unsigned int flags = 0;
    // ...
    AP[i] = new APin (flags);
  }

  /* initialise digital pins
   */
  for (int i = 0; i < 14; i++) {
    unsigned int flags = 0;

    if (i > 1)
      flags |= DPIN_SERVO | DPIN_D_OUT;

    DP[i] = new DPin (flags, i);
  }
}

PinManager::~PinManager () {
  for (int i = 0; i < 6; i++)
    delete AP[i];

  for (int i = 0; i < 14; i++)
    delete DP[i];
}

bool PinManager::command (const String & first, int argc, char ** argv) {
  bool bOkay = true;

  if (first == "help") { // second argument must exist and should be one of: all, servo, ...
    bOkay = false;

    if (argc > 1) {
      String second(argv[1]);
      bool bAll = false;

      if (second == "all") {
	print_pgm (s_usage_help);
	print_pgm (s_usage_echo);
	print_pgm (s_usage_list);
	print_pgm (s_usage_dout);
	print_pgm (s_usage_led);
	bAll = true;
	bOkay = true;
      }
      if (bAll || (second == "servo")) {
	PinServo::help ();
	bOkay = true;
      }
    }
    if (!bOkay) {
      print_pgm (s_err_help); // "help: expected one of: \"all\", \"servo\"";
    }
  } else if (first == "list") {
    bool bAnalog  = true;
    bool bDigital = true;

    if (argc > 1) {
      String second(argv[1]);

      if (second == "analog") {
	bDigital = false;
      } else if (second == "digital") {
	bAnalog = false;
      } else {
	bOkay = false;
      }
    }
    if (bOkay) {
      list (bAnalog, bDigital);
    }
  } else if (first == "dout") {
    for (int arg = 1; arg < argc; arg++) {
      bool bHigh = true;
      char * ptr = argv[arg];
      
      if (*ptr == '~') { // set low rather than high
	bHigh = false;
	if (*++ptr == 0) { // unexpected end-of-string! a ~ by itself
	  bOkay = false;
	  continue;
	}
      }

      int pin_no = parse_pin_no (ptr, DPIN_D_OUT, true);

      if (pin_no < 0) { // oops
	bOkay = false;
	  continue;
	}

      DP[pin_no]->dpin_write (bHigh);
    }
  } else if (first == "led") {
    bOkay = false;

    if (argc > 1) {
      String second(argv[1]);

      if (second == "on") {
	DP[13]->dpin_write (true);
	bOkay = true;
      } else if (second == "off") {
	DP[13]->dpin_write (false);
	bOkay = true;
      }
    }
  } else if (first == "servo") {
    int pin_no = -1;

    if (argc > 1) // there *must* be a second argument
      pin_no = parse_pin_no (argv[1], DPIN_SERVO, true);

    if (pin_no < 0) { // oops
      bOkay = false;
    } else { // we have a valid pin!
      PinServo * PS = DP[pin_no]->servo ();

      if (PS)
	bOkay = PS->command (argc, argv); // let the class instance handle the rest
      else
	bOkay = false;
    }
  }

  return bOkay;
}

int PinManager::parse_pin_no (const char * str, unsigned int flags, bool bDigital) const { // returns pin no if valid, otherwise -1
  int pin_no = -1;

  char * ptr = str;

  bool bOkay = true;
    
  while (*ptr) { // allow only (and a maximum of two) decimal digits
    if (ptr - str > 2) {
      bOkay = false;
      break;
    }
    if ((*ptr < '0') || (*ptr > '9')) {
      bOkay = false;
      break;
    }
    ++ptr;
  }

  if (bOkay) {         // we have a 1-2 digit number
    String second(str);
    pin_no = second.toInt ();

    if (bDigital) {    // digital pin
      if (pin_no > 13) // too high!
	bOkay = false;
    } else {           // analog pin
      if (pin_no > 5) // too high!
	bOkay = false;
    }
  }
  if (bOkay) {         // we have a valid 1-2 digit number, but let's check flags
    if (bDigital) {
      if ((DP[pin_no]->m_flags & flags) != flags)
	bOkay = false;
    } else {
      if ((AP[pin_no]->m_flags & flags) != flags)
	bOkay = false;
    }
  }
  if (!bOkay) {
    print_pgm (s_err_pin_no); // "invalid pin number";
    pin_no = -1;
  }

  return pin_no;
}

void PinManager::list (bool bAnalog, bool bDigital) const {
  if (bAnalog)
    for (int i = 0; i < 6; i++)
      AP[i]->status (i);

  if (bDigital)
    for (int i = 0; i < 14; i++)
      DP[i]->status ();
}

void PinManager::dpin_write (int pin_no, bool value) {
  if ((pin_no < 0) || (pin_no > 13))
    return;

  if (DP[pin_no]->m_flags & DPIN_D_OUT)
    DP[pin_no]->dpin_write (value);
}
