#include "util.hh"
#include "pinmanager.hh"

void user_command (int argc, char ** argv);
void user_interrupt ();

void reset_all ();

static const char s_hello[] PROGMEM       = "This is a simple 'hello' program. Just say 'hi'! (Type 'help all' for more options.)";
static const char s_interrupt[] PROGMEM   = "\r\n(interrupt)";
static const char s_err_command[] PROGMEM = "(command error)";

PinManager PM;

/* input_check() feeds any input back to user_command() as an array of strings
 */
void user_command (int argc, char ** argv) {
  String first(argv[0]);

  if (first.equalsIgnoreCase ("hello") || first.equalsIgnoreCase ("hi")) {
    Serial.println ("Hello.");
  } else if (first.equalsIgnoreCase ("help") && (argc == 1)) {
    print_pgm (s_hello);
  } else if ((first == "help") ||
	     (first == "list") ||
	     (first == "dout") ||
	     (first == "led") ||
	     (first == "pwm") ||
	     (first == "servo")) {
    if (!PM.command (first, argc, argv)) {
      print_pgm (s_err_command);
    }
  } else if (first == "echo") {
    command_echo (argc, argv);
  } else { // mainly for debugging purposes, write out the arguments
    for (int arg = 0; arg < argc; arg++) {
      Serial.print ('"');
      Serial.print (argv[arg]);
      Serial.println ('"');
    }
  }
}

/* If the user presses CTRL-C.
 */
void user_interrupt () {
  print_pgm (s_interrupt);
  // stop all activities
}

void reset_all () {
  // ...
  print_pgm (s_hello);
  input_reset ();
}

void setup () {
  // put your setup code here, to run once:
  Serial.begin (115200);
  reset_all ();
}

void loop () {
  // put your main code here, to run repeatedly:
  input_check ();
}
