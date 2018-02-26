/* Copyright 2017-18 Francis James Franklin
 * 
 * Open Source under the MIT License - see LICENSE in the project's root folder
 */

#ifndef ArduinoHello_util_hh
#define ArduinoHello_util_hh

#include <Arduino.h>

extern uint8_t local_address; // From EEPROM; valid device addresses are 1-127

class Message {
public:
  enum MessageType {
    Text_Command  = 0,
    Text_Response = 1,
    Text_Error    = 2
  } type;

  String text;

  Message (MessageType mt = Text_Response) :
    type(mt)
  {
    // ...
  }

  Message (const String & S) :
    type(Text_Response),
    text(S)
  {
    // ...
  }

  ~Message () {
    // ...
  }

  static Message pgm_message (const char * pgm); // create new message with string stored in PROGMEM

  void append_pgm (const char * pgm);            // append string stored in PROGMEM

  void send (uint8_t address = 0); // default address for Serial
};

/* Turn echo on/off
 */
extern void echo (bool bOn);

/* Raw send string to Serial for testing, where channel_no = '0' or, on Teensy, also '1', '2', '4', '5'
 */
extern void serial_ping (char channel_no, const char * str);

/* Input parsing
 */
extern void input_setup (); // call from main setup() function
extern void input_check (); // check for input, and handle as necessary
extern void input_reset (); // reset the input buffer

enum CommandStatus {
  cs_Okay = 0,
  cs_UnknownCommand,
  cs_IncorrectUsage,
  cs_InvalidPin
};

/* Set callback functions for user command & interrupt
 */
extern void set_user_interrupt (void (*user_interrupt) ());
extern void set_user_command (CommandStatus (*user_command) (uint8_t address_src, int argc, char ** argv));

#endif /* !ArduinoHello_util_hh */

