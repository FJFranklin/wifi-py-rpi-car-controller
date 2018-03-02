/* Copyright 2017-18 Francis James Franklin
 * 
 * Open Source under the MIT License - see LICENSE in the project's root folder
 */

#include <EEPROM.h>

#include "util.hh"

static bool s_bEchoOn = true;

static const char s_err_usage[] PROGMEM   = "(incorrect usage - see: help all)";
static const char s_err_pin_no[] PROGMEM  = "(invalid pin number)";
static const char s_err_command[] PROGMEM = "(command error)";
static const char s_interrupt[] PROGMEM   = "\r\n(interrupt)";

static void input_push (byte c);
static void input_add (char c);
static void input_delete ();
static void input_parse (uint8_t address_src, const char * buffer, size_t size);

static const int input_size = MESSAGE_MAXSIZE; // i.e., 250
static char      input_buffer[input_size+3];
static char *    input_ptr = input_buffer;
static int       input_count = 0;

/* Function callbacks
 */
static void (*s_fn_interrupt) () = 0;                                                 // If the user presses CTRL-C.
static CommandStatus (*s_fn_command) (Message & response, const ArgList & Args) = 0;  // Handle the user's command

void set_user_interrupt (void (*user_interrupt) ()) {
  s_fn_interrupt = user_interrupt;
}

void set_user_command (CommandStatus (*user_command) (Message & response, const ArgList & Args)) {
  s_fn_command = user_command;
}

/* Suppress printing if echo is off.
 */
void echo (bool bOn) {
  s_bEchoOn = bOn;
}

void io_setup () {
  Writer::init_channels ();
}

void io_check () {
  /* Check & update output streams
   */
  Writer::update_all ();

  while (true) {
    int c = Serial.peek ();
    if (c > 0) {
      input_push ((byte) Serial.read ());
      continue;
    }
    break;
  }
}

static void input_push (byte c) {
  if (c < 32) {
    if ((c == 10) || (c == 13)) { // newline || carriage return
      Serial.write (c);
      input_parse (input_default, input_buffer + 2, input_count);
    } else if (c == 3) { // ^C
      Message(local_address, input_default).pgm(s_interrupt).send ();
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

void input_reset () {
  input_ptr = input_buffer;

  *input_ptr++ = '>';
  *input_ptr++ = ' ';
  *input_ptr = 0;

  input_count = 0;

  // Serial.print (input_buffer); // command prompt pointless for asynchronous communication
}

static void input_parse (uint8_t address_src, const char * buffer, size_t size) {
  if (!buffer || (size > MESSAGE_MAXSIZE)) {
    // too long!
    return;
  }

  Message response(local_address, address_src);

  ArgList Args(buffer, size);

  if (Args.count () && s_fn_command) {
    CommandStatus cs = s_fn_command (response, Args);

    if (cs != cs_Okay) {
      response.clear ();
      response.set_type (Message::Text_Error);

      if (cs == cs_InvalidPin) {
	response.pgm (s_err_pin_no);
      } else if (cs == cs_IncorrectUsage) {
	response.pgm (s_err_usage);
      } else {
	response.pgm (s_err_command);
      }
      response.send ();
    }
  }
}

static void input_add (char c) {
  if (input_count < input_size) { // otherwise just ignore
    Serial.print (c);
    *input_ptr++ = c;
    *input_ptr = 0;
    ++input_count;
  }
}

static void input_delete () {
  if (input_count > 0) { // otherwise just ignore
    Serial.print ("\b \b");
    *--input_ptr = 0;
    --input_count;
  }
}

bool Arg::equals (const char * rhs, bool bCaseSensitive) const {
  if (!m_arg || !rhs) {
    return false;
  }
  if (bCaseSensitive) {
    return (strcmp (m_arg, rhs) == 0);
  }
  return (strcasecmp (m_arg, rhs) == 0);
}

int Arg::toInt () const {
  return m_arg ? atoi (m_arg) : 0;
}

ArgList::ArgList (const char * buffer, uint8_t size) :
  m_count(0)
{
  memcpy (m_buffer, buffer, size);
  m_buffer[size] = 0;

  char * ptr = m_buffer;

  while (*ptr && (m_count < INPUT_MAXARGS)) {
    if (*ptr == ' ') {
      ++ptr;
      continue;
    }
    m_args[m_count++] = ptr;

    while (*ptr && (*ptr != ' ')) {
      ++ptr;
    }
    if (*ptr) *ptr++ = 0;
  }
}
