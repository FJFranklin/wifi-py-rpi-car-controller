/* Copyright 2017 Francis James Franklin
 * 
 * Open Source under the MIT License - see LICENSE in the project's root folder
 */

#include "pinmanager.hh"

bool user_command (int argc, char ** argv);
void user_interrupt ();

void reset_all ();
void time_check ();

static const char s_hello[] PROGMEM = "This is a simple 'hello' program. Just say 'hi'! (Type 'help all' for more options.)";

#define LOOPTIME_1ms   (1<<0)
#define LOOPTIME_10ms  (1<<1)
#define LOOPTIME_100ms (1<<2)
#define LOOPTIME_1s    (1<<3)

unsigned long last_millis;

unsigned char time_flags;
unsigned char time_1ms;
unsigned char time_10ms;
unsigned char time_100ms;
unsigned long time_1s;

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

  time_flags = 0;
  time_1ms = 0;
  time_10ms = 0;
  time_100ms = 0;
  time_1s = 0;

  last_millis = millis ();
}

void time_check () {
  unsigned long current_millis = millis ();

  if (last_millis != current_millis) { // this code runs approximately every millisecond; delays may occur elsewhere
    time_1ms += (current_millis - last_millis);
    last_millis = current_millis;
    
    /* every 1 ms
     */
    time_flags |= LOOPTIME_1ms;

    if (time_1ms >= 10) {
      time_1ms -= 10;
      ++time_10ms;

      /* every 10 ms
       */
      time_flags |= LOOPTIME_10ms;

      if (time_10ms >= 10) {
	time_10ms -= 10;
	++time_100ms;

	/* every 100 ms
	 */
	time_flags |= LOOPTIME_100ms;

	if (time_100ms >= 10) {
	  time_100ms -= 10;
	  ++time_1s;

	  /* every 1 s
	   */
	  time_flags |= LOOPTIME_1s;
	}
      }
    }
  }
}

void setup () {
  Serial.begin (115200);

  /* Instantiate PinManager and set the input callbacks 
   */
  PinManager::manager()->input_callbacks (user_command, user_interrupt);

  reset_all ();
}

void loop () { // approximately 178 loops per millisecond on the Uno when idling
  time_check ();

  if (time_flags & LOOPTIME_1ms) {
    // ...
    time_flags &= ~LOOPTIME_1ms;
    return;
  }

  if (time_flags & LOOPTIME_10ms) {
    // ...
    time_flags &= ~LOOPTIME_10ms;
    return;
  }

  if (time_flags & LOOPTIME_100ms) {
    // ...
    time_flags &= ~LOOPTIME_100ms;
    return;
  }

  if (time_flags & LOOPTIME_1s) {
#if 0
    if (time_1s & 1)
      Serial.print ("\r\ntick...");
    else
      Serial.print (" tock.");
#endif
    // ...
    time_flags &= ~LOOPTIME_1s;
    return;
  }

  input_check ();
}
