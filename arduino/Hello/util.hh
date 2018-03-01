/* Copyright 2017-18 Francis James Franklin
 * 
 * Open Source under the MIT License - see LICENSE in the project's root folder
 */

#ifndef ArduinoHello_util_hh
#define ArduinoHello_util_hh

#include <Arduino.h>

#include "comms.hh"

/* Turn echo on/off
 */
extern void echo (bool bOn);

/* I/O handling & nput parsing
 */
extern void io_setup (); // call from main setup() function
extern void io_check (); // check for input, and handle as necessary; update output streams also

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
extern void set_user_command (CommandStatus (*user_command) (Message & response, int argc, char ** argv));

#endif /* !ArduinoHello_util_hh */

