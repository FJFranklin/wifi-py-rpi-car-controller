/* Copyright 2017-18 Francis James Franklin
 * 
 * Open Source under the MIT License - see LICENSE in the project's root folder
 */

#include "util.hh"

static bool s_bEchoOn = true;

static const char s_err_usage[] PROGMEM   = "(incorrect usage - see: help all)";
static const char s_err_pin_no[] PROGMEM  = "(invalid pin number)";
static const char s_err_command[] PROGMEM = "(command error)";
static const char s_interrupt[] PROGMEM   = "\r\n(interrupt)";

/* Suppress printing if echo is off.
 */
void echo (bool bOn) {
  s_bEchoOn = bOn;
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

ArgList::ArgList (Message & message) :
  m_buffer((char *) message.get_buffer ()),
  m_count(0)
{
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

static Command   s_command;
static Command * s_command_ptr = 0;

Command * Command::command () {
  if (!s_command_ptr) {
    s_command_ptr = &s_command;
    channels[CHANNEL_CONSOLE]->reader->set_handler (s_command_ptr);
  }
  return s_command_ptr;
}

void Command::message_received (Message & message) {
  if (m_user_command && (message.get_type () == Message::Text_Command) && message.get_length ()) {
    m_response.clear ();
    m_response.set_address_src (message.get_address_dest ());
    m_response.set_address_dest (message.get_address_src ());
    m_response.set_type (Message::Text_Response);

    ArgList Args(message);

    if (Args.count () && m_user_command) {
      CommandStatus cs = m_user_command (m_response, Args);

      if (cs != cs_Okay) {
	m_response.clear ();
	m_response.set_type (Message::Text_Error);

	if (cs == cs_InvalidPin) {
	  m_response.pgm (s_err_pin_no);
	} else if (cs == cs_IncorrectUsage) {
	  m_response.pgm (s_err_usage);
	} else {
	  m_response.pgm (s_err_command);
	}
	m_response.send ();
      }
    }
  }
}

void Command::interrupt (Message & message) {
  if (m_user_interrupt) {
    m_response.clear ();
    m_response.set_address_src (message.get_address_dest ());
    m_response.set_address_dest (message.get_address_src ());
    m_response.set_type (message.get_type ());
    m_user_interrupt (m_response);
  }
}
