/* Copyright 2017 Francis James Franklin
 * 
 * Open Source under the MIT License - see LICENSE in the project's root folder
 */

#include "util.hh"
#include "pinservo.hh"
#include "pinmanager.hh"
#include "sd.hh"

#include "pm_apin.hh"
#include "pm_dpin.hh"

static const char s_usage_help[] PROGMEM = "help [all|servo]";
static const char s_usage_echo[] PROGMEM = "echo on|off";
static const char s_usage_list[] PROGMEM = "list [digital|analog]";
static const char s_usage_dclr[] PROGMEM = "dclr [<pin#2-13>]*";
static const char s_usage_dout[] PROGMEM = "dout [[~]<pin#2-13>]*";
static const char s_usage_din[] PROGMEM  = "din [<pin#2-12>]*";
static const char s_usage_dup[] PROGMEM  = "dup [[~]<pin#2-12>]*";
static const char s_usage_led[] PROGMEM  = "led on|off";

static const char s_usage_pwm_on_off[] PROGMEM = "pwm <pin#3,5-6,9-11> on|off";
static const char s_usage_pwm_duty[] PROGMEM   = "pwm <pin#3,5-6,9-11> duty <0-255>";

static const char s_err_help[] PROGMEM   = "help: expected one of: \"all\", \"digital\", \"servo\", \"pwm\"";

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
    unsigned int flags = APIN_ANALOG;

    AP[i] = new APin (flags, i);
  }

  /* initialise digital pins
   */
  for (int i = 0; i < 14; i++) {
    unsigned int flags = 0;

    if (i > 1) {
      flags |= DPIN_SERVO | DPIN_D_OUT | DPIN_D_CLR;
      if (i < 13)
	flags |= DPIN_D_IN;
    }

    DP[i] = new DPin (flags, i);
  }

  DP[ 3]->m_flags |= DPIN_PWM; // conflicts with tone() (uses Timer 2)
  DP[ 5]->m_flags |= DPIN_PWM;
  DP[ 6]->m_flags |= DPIN_PWM;
  // DP[ 9]->m_flags |= DPIN_PWM; // conflicts with Servo library (uses Timer 1)
  // DP[10]->m_flags |= DPIN_PWM; // conflicts with Servo library: see https://arduino-info.wikispaces.com/Timers-Arduino
  DP[11]->m_flags |= DPIN_PWM; // conflicts with tone() & SPI (MOSI)
}

PinManager::~PinManager () {
  for (int i = 0; i < 6; i++)
    delete AP[i];

  for (int i = 0; i < 14; i++)
    delete DP[i];
}

static CommandStatus s_command (uint8_t address_src, int argc, char ** argv) { // callback for util input command
  return s_PM->command (address_src, argc, argv);
}

void PinManager::input_callbacks (CommandStatus (*user_command_callback) (uint8_t address_src, String & first, int argc, char ** argv),
				  void (*user_interrupt_callback) ())
{
  user_command = user_command_callback;

  set_user_interrupt (user_interrupt_callback);
  set_user_command (s_command);
}

void PinManager::update (void (*notification_handler) (int pin_no, bool bDigital)) {
  /* TODO: set notifications
   */

  for (int i = 0; i < 6; i++) {
    if (AP[i]->notification ()) {
      // TODO: Handle internally if required ??
      //       Notifications may be requested by the command line, the user's program, or internally; how to manage?
      //       Query: Are pin change interrupts on analog pins only relevant for digital input?

      if (notification_handler)
	notification_handler (i, false);
    }
  }

  for (int i = 0; i < 14; i++) {
    if (DP[i]->notification ()) {
      // TODO: Handle internally if required ??
      //       Notifications may be requested by the command line, the user's program, or internally; how to manage?

      if (notification_handler)
	notification_handler (i, false);
    }
  }
}

CommandStatus PinManager::command (uint8_t address_src, int argc, char ** argv) {
  CommandStatus cs = cs_UnknownCommand;

  String first(argv[0]);

  if ((first == "help") && (argc > 1)) { // second argument must exist and should be one of: all, digital, servo, pwm, ...
    cs = cs_IncorrectUsage;

    if (argc > 1) {
      String second(argv[1]);
      bool bAll = false;

      if (second == "all") {
	Message::pgm_message(s_usage_help).send (address_src);
	Message::pgm_message(s_usage_echo).send (address_src);
	Message::pgm_message(s_usage_list).send (address_src);
	Message::pgm_message(s_usage_led).send (address_src);
	bAll = true;
	cs = cs_Okay;
      }
      if (bAll || (second == "digital")) {
	Message::pgm_message(s_usage_dclr).send (address_src);
	Message::pgm_message(s_usage_dout).send (address_src);
	Message::pgm_message(s_usage_din).send (address_src);
	Message::pgm_message(s_usage_dup).send (address_src);
	cs = cs_Okay;
      }
      if (bAll || (second == "servo")) {
	PinServo::help (address_src);
	cs = cs_Okay;
      }
      if (bAll || (second == "pwm")) {
	Message::pgm_message(s_usage_pwm_on_off).send (address_src);
	Message::pgm_message(s_usage_pwm_duty).send (address_src);
	cs = cs_Okay;
      }
    }
    if (cs != cs_Okay) {
      Message response(Message::Text_Error);
      response.append_pgm (s_err_help); // "help: expected one of: \"all\", \"digital\", \"servo\", \"pwm\"";
      response.send (address_src);
    }
  } else if (first == "ping") {
    cs = cs_Okay;

    char channel_no = '0';
    const char * message = argv[0];

    if (argc > 1) {
      channel_no = *argv[1];
    }
    if (argc > 2) {
      message = argv[2];
    }

    serial_ping (channel_no, message);
  } else if (first == "list") {
    cs = cs_Okay;

    bool bAnalog  = true;
    bool bDigital = true;

    if (argc > 1) {
      String second(argv[1]);

      if (second == "analog") {
	bDigital = false;
      } else if (second == "digital") {
	bAnalog = false;
      } else {
	cs = cs_IncorrectUsage;
      }
    }
    if (cs == cs_Okay) {
      list (address_src, bAnalog, bDigital);
    }
  } else if (first == "dclr") {
    cs = cs_Okay;

    for (int arg = 1; arg < argc; arg++) {
      int pin_no = parse_pin_no (argv[arg], DPIN_D_CLR, true);

      if (pin_no < 0) { // oops
	cs = cs_InvalidPin;
	  continue;
	}

      DP[pin_no]->clear ();
    }
  } else if (first == "ain") {
    Message response;

    cs = cs_Okay;

    bool bFirst = true;

    for (int arg = 1; arg < argc; arg++) {
      int pin_no = parse_pin_no (argv[arg], APIN_ANALOG, false);

      if (pin_no < 0) { // oops
	cs = cs_InvalidPin;
	  continue;
	}

      if (bFirst)
	bFirst = false;
      else
	response.text += ' ';

      response.text += String (AP[pin_no]->apin_read ());
    }
    if (!bFirst) {
      response.send (address_src);
    }
  } else if (first == "din") {
    Message response;

    cs = cs_Okay;

    bool bFirst = true;

    for (int arg = 1; arg < argc; arg++) {
      int pin_no = parse_pin_no (argv[arg], DPIN_D_IN, true);

      if (pin_no < 0) { // oops
	cs = cs_InvalidPin;
	  continue;
	}

      if (bFirst)
	bFirst = false;
      else
	response.text += ' ';

      if (DP[pin_no]->dpin_read ())
	response.text += '1';
      else
	response.text += '0';
    }
    if (!bFirst) {
      response.send (address_src);
    }
  } else if (first == "dout") {
    cs = cs_Okay;

    for (int arg = 1; arg < argc; arg++) {
      bool bHigh = true;
      char * ptr = argv[arg];
      
      if (*ptr == '~') { // set low rather than high
	bHigh = false;
	if (*++ptr == 0) { // unexpected end-of-string! a ~ by itself
	  cs = cs_IncorrectUsage;
	  continue;
	}
      }

      int pin_no = parse_pin_no (ptr, DPIN_D_OUT, true);

      if (pin_no < 0) { // oops
	cs = cs_InvalidPin;
	  continue;
	}

      DP[pin_no]->dpin_write (bHigh);
    }
  } else if (first == "dup") {
    cs = cs_Okay;

    for (int arg = 1; arg < argc; arg++) {
      bool bUp = true;
      char * ptr = argv[arg];
      
      if (*ptr == '~') { // set down rather than up
	bUp = false;
	if (*++ptr == 0) { // unexpected end-of-string! a ~ by itself
	  cs = cs_IncorrectUsage;
	  continue;
	}
      }

      int pin_no = parse_pin_no (ptr, DPIN_D_IN, true);

      if (pin_no < 0) { // oops
	cs = cs_InvalidPin;
	  continue;
	}

      DP[pin_no]->dpin_input (bUp);
    }
  } else if (first == "led") {
    cs = cs_IncorrectUsage;

    if (argc > 1) {
      String second(argv[1]);

      if (second == "on") {
	DP[13]->dpin_write (true);
	cs = cs_Okay;
      } else if (second == "off") {
	DP[13]->dpin_write (false);
	cs = cs_Okay;
      }
    }
  } else if (first == "echo") {
    cs = cs_IncorrectUsage;

    if (argc > 1) {
      String second(argv[1]);

      if (second == "on") {
	echo (true);
	cs = cs_Okay;
      } else if (second == "off") {
	echo (false);
	cs = cs_Okay;
      }
    }
  } else if (first == "servo") {
    cs = cs_Okay;

    int pin_no = -1;

    if (argc > 1) // there *must* be a second argument
      pin_no = parse_pin_no (argv[1], DPIN_SERVO, true);

    if (pin_no < 0) { // oops
      cs = cs_InvalidPin;
    } else { // we have a valid pin!
      PinServo * PS = DP[pin_no]->servo ();
      cs = PS->command (address_src, argc, argv); // let the class instance handle the rest
    }
  } else if (first == "pwm") {
    cs = cs_Okay;

    int pin_no = -1;

    if (argc > 1) // there *must* be a second argument
      pin_no = parse_pin_no (argv[1], DPIN_PWM, true);

    if (pin_no < 0) { // oops
      cs = cs_InvalidPin;
    } else { // we have a valid pin!
      cs = cs_IncorrectUsage;

      if (argc > 2) { // need a 3rd argument at least
	String third(argv[2]);

	if (third == "on") {
	  DP[pin_no]->pwm (true);
	  cs = cs_Okay;
	} else if (third == "off") {
	  DP[pin_no]->pwm (false);
	  cs = cs_Okay;
	} else if ((third == "duty") && (argc > 3)) { // need a 4th argument for the duty cycle
	  String duty(argv[3]);
	  int cycle = duty.toInt ();

	  if ((cycle >= 0) && (cycle <= 255)) {
	    DP[pin_no]->pwm_duty ((unsigned char) cycle);
	    cs = cs_Okay;
	  }
	}
      }
    }
  }
  
  if (cs == cs_UnknownCommand) {
    SD_Manager * SD = SD_Manager::manager ();
    if (SD) {
      cs = SD->command (address_src, first, argc, argv);
    }
  }

  if (user_command && (cs == cs_UnknownCommand)) {
    cs = user_command (address_src, first, argc, argv);
  }

  return cs;
}

int PinManager::parse_pin_no (const char * str, unsigned int flags, bool bDigital) const { // returns pin no if valid, otherwise -1
  int pin_no = -1;

  const char * ptr = str;

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
    pin_no = -1;
  }
  return pin_no;
}

void PinManager::list (uint8_t address_src, bool bAnalog, bool bDigital) const {
  if (bAnalog)
    for (int i = 0; i < 6; i++)
      Message(AP[i]->status ()).send (address_src);

  if (bDigital)
    for (int i = 0; i < 14; i++)
      Message(DP[i]->status ()).send (address_src);
}

/* set digital pin <pin_no> to high (true, 1) or low (false, 0)
 */
CommandStatus PinManager::cmd_dout (int pin_no, bool value) {
  if ((pin_no < 0) || (pin_no > 13))
    return cs_InvalidPin;

  if (!(DP[pin_no]->m_flags & DPIN_D_OUT))
    return cs_InvalidPin;

  DP[pin_no]->dpin_write (value);

  return cs_Okay;
}

/* read digital pin <pin_no> (0-1)
 */
CommandStatus PinManager::cmd_din (int pin_no, bool & bState) {
  if ((pin_no < 0) || (pin_no > 13))
    return cs_InvalidPin;

  if (!(DP[pin_no]->m_flags & DPIN_D_IN))
    return cs_InvalidPin;

  bState = DP[pin_no]->dpin_read ();

  return cs_Okay;
}

/* read analog pin A<pin_no> (0-1023)
 */
CommandStatus PinManager::cmd_ain (int pin_no, int & value) {
  if ((pin_no < 0) || (pin_no > 5))
    return cs_InvalidPin;

  if (!(AP[pin_no]->m_flags & APIN_ANALOG))
    return cs_InvalidPin;

  value = AP[pin_no]->apin_read ();

  return cs_Okay;
}

/* set digital pin <pin_no> to read with internal pull-up resistor
 */
CommandStatus PinManager::cmd_dup (int pin_no, bool bPullUp) {
  if ((pin_no < 0) || (pin_no > 13))
    return cs_InvalidPin;

  if (!(DP[pin_no]->m_flags & DPIN_D_IN))
    return cs_InvalidPin;

  DP[pin_no]->dpin_input (bPullUp);

  return cs_Okay;
}

/* deassociate & clear state of digital pin <pin_no>
 */
CommandStatus PinManager::cmd_dclr (int pin_no) {
  if ((pin_no < 0) || (pin_no > 13))
    return cs_InvalidPin;

  if (!(DP[pin_no]->m_flags & DPIN_D_CLR))
    return cs_InvalidPin;

  DP[pin_no]->clear ();

  return cs_Okay;
}

/* use (digital) pin <pin_no> as PWM and turn on/off
 */
CommandStatus PinManager::cmd_pwm (int pin_no, bool bOn) {
  if ((pin_no < 0) || (pin_no > 13))
    return cs_InvalidPin;

  if (!(DP[pin_no]->m_flags & DPIN_PWM))
    return cs_InvalidPin;

  DP[pin_no]->pwm (bOn);

  return cs_Okay;
}

/* set PWM duty cycle (0-255) for (digital) pin <pin_no>
 */
CommandStatus PinManager::cmd_pwm_duty (int pin_no, unsigned char duty_cycle) {
  if ((pin_no < 0) || (pin_no > 13))
    return cs_InvalidPin;

  if (!(DP[pin_no]->m_flags & DPIN_PWM))
    return cs_InvalidPin;

  DP[pin_no]->pwm_duty (duty_cycle);

  return cs_Okay;
}

/* use (digital) pin <pin_no> as a servo controller and turn on/off
 */
CommandStatus PinManager::cmd_servo (int pin_no, bool bOn) {
  if ((pin_no < 0) || (pin_no > 13))
    return cs_InvalidPin;

  if (!(DP[pin_no]->m_flags & DPIN_SERVO))
    return cs_InvalidPin;

  PinServo * PS = DP[pin_no]->servo ();

  return PS->cmd_servo (bOn);
}

/* set high/low range for servo on (digital) pin <pin_no>
 */
CommandStatus PinManager::cmd_servo_minmax (int pin_no, unsigned int range_min, unsigned int range_max) {
  if ((pin_no < 0) || (pin_no > 13))
    return cs_InvalidPin;

  if (!(DP[pin_no]->m_flags & DPIN_SERVO))
    return cs_InvalidPin;

  PinServo * PS = DP[pin_no]->servo ();

  return PS->cmd_servo_minmax (range_min, range_max);
}

/* set angle (0-180) for servo on (digital) pin <pin_no>
 */
CommandStatus PinManager::cmd_servo_angle (int pin_no, unsigned int angle) {
  if ((pin_no < 0) || (pin_no > 13))
    return cs_InvalidPin;

  if (!(DP[pin_no]->m_flags & DPIN_SERVO))
    return cs_InvalidPin;

  PinServo * PS = DP[pin_no]->servo ();

  return PS->cmd_servo_angle (angle);
}

/* set exact value for high for servo on (digital) pin <pin_no>
 */
CommandStatus PinManager::cmd_servo_microseconds (int pin_no, unsigned int microseconds) {
  if ((pin_no < 0) || (pin_no > 13))
    return cs_InvalidPin;

  if (!(DP[pin_no]->m_flags & DPIN_SERVO))
    return cs_InvalidPin;

  PinServo * PS = DP[pin_no]->servo ();

  return PS->cmd_servo_microseconds (microseconds);
}

