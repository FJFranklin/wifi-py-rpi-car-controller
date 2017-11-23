#include "util.hh"

static const char s_err_command[] PROGMEM = "(command error)";
static const char s_interrupt[] PROGMEM   = "\r\n(interrupt)";

static void input_add (char c);
static void input_delete ();
static void input_parse ();

static const int input_size = 64;
static char      input_buffer[input_size+3];
static char *    input_ptr = input_buffer;
static int       input_count = 0;
static char *    input_argv[(input_size/2)+1];

/* Function callbacks
 */
static void (*s_fn_interrupt) () = 0;                     // If the user presses CTRL-C.
static bool (*s_fn_command) (int argc, char ** argv) = 0; // Handle the user's command

void set_user_interrupt (void (*user_interrupt) ()) {
  s_fn_interrupt = user_interrupt;
}

void set_user_command (bool (*user_command) (int argc, char ** argv)) {
  s_fn_command = user_command;
}

/* Suppress printing if echo is off.
 */
static bool s_bEchoOn = true;

void echo (bool bOn) {
  s_bEchoOn = bOn;
}

void print_pgm (const char * str_pgm) {
  if (!s_bEchoOn) return;

  while (true) {
    byte c = pgm_read_byte_near (str_pgm++);
    if (!c) break;
    Serial.write (c);
  }
  Serial.print ("\r\n");
}

void print_str (const char * str) {
  if (s_bEchoOn) {
    Serial.print (str);
  }
}

void print_char (char c) {
  if (s_bEchoOn) {
    Serial.write (c);
  }
}

void input_check () {
  if (Serial.available () > 0) {
    byte c = Serial.read ();

    if (c < 32) {
      if ((c == 10) || (c == 13)) { // newline || carriage return
        input_parse ();
      } else if (c == 3) { // ^C
	print_pgm (s_interrupt);
	if (s_fn_interrupt)
	  s_fn_interrupt ();
      }
      input_reset ();
    } else if (c == 127) {
      input_delete ();
    } else if (c < 127) {
      input_add ((char) c);
    }
  }
}

void input_reset () {
  input_ptr = input_buffer;

  *input_ptr++ = '>';
  *input_ptr++ = ' ';
  *input_ptr = 0;

  input_count = 0;

  print_str (input_buffer);
}

static void input_parse () {
  char * ptr = input_buffer + 2;
  int    argc = 0;

  print_str ("\r\n");

  while (*ptr) {
    if (*ptr == ' ') {
      ++ptr;
      continue;
    }
    input_argv[argc++] = ptr;
    while (*ptr && (*ptr != ' ')) ++ptr;
    if (*ptr) *ptr++ = 0;
  }
  input_argv[argc] = 0;

  if (argc && s_fn_command) {
    if (!s_fn_command (argc, input_argv))
      print_pgm (s_err_command);
  }
}

static void input_add (char c) {
  if (input_count < input_size) { // otherwise just ignore
    print_char (c);
    *input_ptr++ = c;
    *input_ptr = 0;
    ++input_count;
  }
}

static void input_delete () {
  if (input_count > 0) { // otherwise just ignore
    print_str ("\b \b");
    *--input_ptr = 0;
    --input_count;
  }
}
