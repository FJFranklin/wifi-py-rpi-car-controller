/* Copyright 2017-18 Francis James Franklin
 * 
 * Open Source under the MIT License - see LICENSE in the project's root folder
 */

#include "pinmanager.hh"

CommandStatus  user_command (Message & response, String & first, int argc, char ** argv);
void           user_interrupt ();
void           notification (int pin_no, bool bDigital);

void           time_check ();

static const char s_hello[] PROGMEM = "This is a simple 'hello' program. Just say 'hi'! (Type 'help all' for more options.)";

#define LOOPTIME_1ms   (1<<0)
#define LOOPTIME_10ms  (1<<1)
#define LOOPTIME_100ms (1<<2)
#define LOOPTIME_1s    (1<<3)

PinManager * PM = 0;

unsigned long last_millis;

unsigned char time_flags;
unsigned char time_1ms;
unsigned char time_10ms;
unsigned char time_100ms;
unsigned long time_1s;

/* input_check() feeds any input back to user_command() via PinManager as an array of strings
 */
CommandStatus user_command (Message & response, String & first, int argc, char ** argv) {
  CommandStatus cs = cs_Okay;

  if (first.equalsIgnoreCase ("hello") || first.equalsIgnoreCase ("hi")) {
    response = "Hello.";
    response.send ();
  } else if (first.equalsIgnoreCase ("help")) {
    response.pgm (s_hello);
    response.send ();
  } else { // mainly for debugging purposes, write out the arguments
    response.set_type (Message::Text_Error);
    for (int arg = 0; arg < argc; arg++) {
      if (arg) {
	response += ',';
      }
      response += '"';
      response += argv[arg];
      response += '"';
    }
    response.send ();
    cs = cs_UnknownCommand;
  }

  return cs;
}

void user_interrupt () {
  // ...
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
  io_setup ();

  /* Instantiate PinManager and set the input callbacks 
   */
  PM = PinManager::manager ();
  PM->input_callbacks (user_command, user_interrupt);

  Message response(local_address, input_default);
  response.pgm (s_hello);
  response.send ();

  input_reset ();

  time_flags = 0;
  time_1ms = 0;
  time_10ms = 0;
  time_100ms = 0;
  time_1s = 0;

  last_millis = millis ();
}

void notification (int pin_no, bool bDigital) { // passes pin no. & clears notification
  Serial.print ("\r\nNotification: ");
  if (!bDigital)
    Serial.print ("A");
  Serial.print (pin_no);
}

void loop () { // approximately 178 loops per millisecond on the Uno when idling

  /* The more urgent the task, the sooner it should appear within loop()
   */

  PM->update (notification);

  time_check (); // update our clock

  if (time_flags & LOOPTIME_1ms) { // things to do roughly every millisecond
    // ...
    time_flags &= ~LOOPTIME_1ms;
    return;
  }

  if (time_flags & LOOPTIME_10ms) { // things to do roughly every 10 milliseconds
    // ...
    time_flags &= ~LOOPTIME_10ms;
    return;
  }

  if (time_flags & LOOPTIME_100ms) { // things to do roughly every 100 milliseconds
    if ((time_100ms == 0) || (time_100ms == 3))
      PM->cmd_led (true);
    else
      PM->cmd_led (false);
    // ...
    time_flags &= ~LOOPTIME_100ms;
    return;
  }

  if (time_flags & LOOPTIME_1s) { // things to do roughly every second
    // ...
    time_flags &= ~LOOPTIME_1s;
    return;
  }

  io_check (); // check & handle any input/output
}
