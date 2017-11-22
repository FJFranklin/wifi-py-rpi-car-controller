#include "util.hh"

extern void user_command (int argc, char ** argv);
extern void user_interrupt ();

static const char s_echo[] PROGMEM = "usage: echo on|off";

static void input_add (char c);
static void input_delete ();
static void input_parse ();

static const int input_size = 64;
static char      input_buffer[input_size+3];
static char *    input_ptr = input_buffer;
static int       input_count = 0;
static char *    input_argv[(input_size/2)+1];

static bool      s_bEchoOn = true;

/* Suppress printing if echo is off.
 */

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

void command_echo (int argc, char ** argv) {
  bool bOkay = false;

  if (argc == 2) {
    String second(argv[1]);

    if (second == "on") {
      s_bEchoOn = true;
      bOkay = true;
    } else if (second == "off") {
      s_bEchoOn = false;
      bOkay = true;
    }
  }
  if (!bOkay)
    print_pgm (s_echo);
}

void input_check () {
  if (Serial.available () > 0) {
    byte c = Serial.read ();

    if (c < 32) {
      if ((c == 10) || (c == 13)) { // newline || carriage return
        input_parse ();
      } else if (c == 3) { // ^C
        user_interrupt ();
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

  if (argc) user_command (argc, input_argv);
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
