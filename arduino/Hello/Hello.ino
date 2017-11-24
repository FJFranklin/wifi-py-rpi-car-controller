/* Copyright 2017 Francis James Franklin
 * 
 * Open Source under the MIT License - see LICENSE in the project's root folder
 */

#include "util.hh"
#include "pinmanager.hh"

bool user_command (int argc, char ** argv);
void user_interrupt ();

void reset_all ();

static const char s_hello[] PROGMEM = "This is a simple 'hello' program. Just say 'hi'! (Type 'help all' for more options.)";

/* input_check() feeds any input back to user_command() via PinManager as an array of strings
 */
CommandStatus user_command (String & first, int argc, char ** argv) {
  CommandStatus cs = cs_Okay;

  if (first.equalsIgnoreCase ("hello") || first.equalsIgnoreCase ("hi")) {
    Serial.println ("Hello.");
  } else if (first.equalsIgnoreCase ("help")) {
    print_pgm (s_hello);
  } else { // mainly for debugging purposes, write out the arguments
    for (int arg = 0; arg < argc; arg++) {
      Serial.print ('"');
      Serial.print (argv[arg]);
      Serial.println ('"');
    }
    cs = cs_UnknownCommand;
  }

  return cs;
}

void user_interrupt () {
  // ...
}

void reset_all () {
  print_pgm (s_hello);
  input_reset ();
}

void setup () {
  // put your setup code here, to run once:
  Serial.begin (115200);

  /* Instantiate PinManager and set the input callbacks 
   */
  PinManager::manager()->input_callbacks (user_command, user_interrupt);

  reset_all ();
}

void loop () {
  // put your main code here, to run repeatedly:
  input_check ();
}
