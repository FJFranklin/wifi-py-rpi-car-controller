/* Copyright 2017 Francis James Franklin
 * 
 * Open Source under the MIT License - see LICENSE in the project's root folder
 */

#include "util.hh"
#include "pinservo.hh"
#include "pinmanager.hh"

#include "pm_apin.hh"
#include "pm_dpin.hh"

static const char s_usage_help[] PROGMEM = "help [all|servo]";
static const char s_usage_echo[] PROGMEM = "echo on|off";
static const char s_usage_list[] PROGMEM = "list [digital|analog]";
static const char s_usage_dout[] PROGMEM = "dout [[~]<pin#2-13>]*";
static const char s_usage_led[] PROGMEM  = "led on|off";

static const char s_usage_pwm_on_off[] PROGMEM = "pwm <pin#3,5-6,9-11> on|off";
static const char s_usage_pwm_duty[] PROGMEM   = "pwm <pin#3,5-6,9-11> duty <0-255>";

static const char s_err_help[] PROGMEM   = "help: expected one of: \"all\", \"servo\", \"pwm\"";
static const char s_err_pin_no[] PROGMEM = "invalid pin number";

static PinManager * s_PM = 0;

PinManager * PinManager::manager () {
  if (!s_PM) {
    s_PM = new PinManager ();
  }
  return s_PM;
}

PinManager::PinManager () :
  user_command(0)
{
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

  DP[ 3]->m_flags |= DPIN_PWM;
  DP[ 5]->m_flags |= DPIN_PWM;
  DP[ 6]->m_flags |= DPIN_PWM;
  DP[ 9]->m_flags |= DPIN_PWM;
  DP[10]->m_flags |= DPIN_PWM;
  DP[11]->m_flags |= DPIN_PWM;
}

PinManager::~PinManager () {
  for (int i = 0; i < 6; i++)
    delete AP[i];

  for (int i = 0; i < 14; i++)
    delete DP[i];
}

static bool s_command (int argc, char ** argv) { // callback for util input command
  return s_PM->command (argc, argv);
}

void PinManager::input_callbacks (bool (*user_command_callback) (String & first, int argc, char ** argv), void (*user_interrupt_callback) ()) {
  user_command = user_command_callback;

  set_user_interrupt (user_interrupt_callback);
  set_user_command (s_command);
}

bool PinManager::command (int argc, char ** argv) {
  bool bOkay = true;
  String first(argv[0]);

  if ((first == "help") && (argc > 1)) { // second argument must exist and should be one of: all, servo, pwm, ...
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
      if (bAll || (second == "pwm")) {
	print_pgm (s_usage_pwm_on_off);
	print_pgm (s_usage_pwm_duty);
	bOkay = true;
      }
    }
    if (!bOkay) {
      print_pgm (s_err_help); // "help: expected one of: \"all\", \"servo\", \"pwm\"";
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
  } else if (first == "echo") {
    bOkay = false;

    if (argc > 1) {
      String second(argv[1]);

      if (second == "on") {
	echo (true);
	bOkay = true;
      } else if (second == "off") {
	echo (false);
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
  } else if (first == "pwm") {
    int pin_no = -1;

    if (argc > 1) // there *must* be a second argument
      pin_no = parse_pin_no (argv[1], DPIN_PWM, true);

    if (pin_no < 0) { // oops
      bOkay = false;
    } else { // we have a valid pin!
      bOkay = false;

      if (argc > 2) { // need a 3rd argument at least
	String third(argv[2]);

	if (third == "on") {
	  DP[pin_no]->pwm (true);
	  bOkay = true;
	} else if (third == "off") {
	  DP[pin_no]->pwm (false);
	  bOkay = true;
	} else if ((third == "duty") && (argc > 3)) { // need a 4th argument for the duty cycle
	  String duty(argv[3]);
	  int cycle = duty.toInt ();

	  if ((cycle >= 0) && (cycle <= 255)) {
	    DP[pin_no]->pwm_duty ((unsigned char) cycle);
	    bOkay = true;
	  }
	}
      }
    }
  } else if (user_command) {
    bOkay = user_command (first, argc, argv);
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
