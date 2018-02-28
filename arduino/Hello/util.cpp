/* Copyright 2017-18 Francis James Franklin
 * 
 * Open Source under the MIT License - see LICENSE in the project's root folder
 */

#include <EEPROM.h>

#include "util.hh"

#ifdef CORE_TEENSY
/* An Arduino Library that facilitates packet-based serial communication using COBS or SLIP encoding
 * https://github.com/bakercp/PacketSerial
 */
#include <PacketSerial.h>

static PacketSerial PS0;
static PacketSerial PS1;
static PacketSerial PS2;

#endif /* CORE_TEENSY */

static bool s_bUsePacketSerial = false;
static bool s_bEchoOn = true;

static const char s_err_usage[] PROGMEM   = "(incorrect usage - see: help all)";
static const char s_err_pin_no[] PROGMEM  = "(invalid pin number)";
static const char s_err_command[] PROGMEM = "(command error)";
static const char s_interrupt[] PROGMEM   = "\r\n(interrupt)";

static void input_push (byte c);
static void input_add (char c);
static void input_delete ();
static void input_parse (uint8_t address_src, const char * buffer, size_t size);

static const int input_size = 253;
static char      input_bufcpy[input_size+1];
static char      input_buffer[input_size+3];
static char *    input_ptr = input_buffer;
static int       input_count = 0;
static char *    input_argv[(input_size/2)+1];

/* Function callbacks
 */
static void (*s_fn_interrupt) () = 0;                                                   // If the user presses CTRL-C.
static CommandStatus (*s_fn_command) (uint8_t address_src, int argc, char ** argv) = 0; // Handle the user's command

void set_user_interrupt (void (*user_interrupt) ()) {
  s_fn_interrupt = user_interrupt;
}

void set_user_command (CommandStatus (*user_command) (uint8_t address_src, int argc, char ** argv)) {
  s_fn_command = user_command;
}

/* Suppress printing if echo is off.
 */
void echo (bool bOn) {
  s_bEchoOn = bOn;
}

#if 0

#define CMD_CLI_Command   0
#define CMD_CLI_Response  1

static void s_packet (uint8_t /* channel_no */, const uint8_t * buffer, size_t size) {
  if (size < 4) {
    // minimum packet size is 4
    return;
  }

  uint8_t address_dest = buffer[0];
  uint8_t address_src  = buffer[1];
  uint8_t pkt_command  = buffer[2];
  uint8_t pkt_data_len = buffer[3];

  if (pkt_data_len > 252) {
    // too long; packet total length < 256
    return;
  }
  if ((uint8_t) (pkt_data_len + 4) != size) {
    // incomplete/broken packet
    return;
  }

  if (address_dest == local_address) {    // the packet has reached its destination
    if (pkt_command == CMD_CLI_Command) { // it's a simple command
      input_parse (address_src, (const char *) (buffer + 4), pkt_data_len);
    } else {
      // TODO: handle
    }
  } else {
    // TODO: redirect
  }
}

static void s_PS0_onPacketReceived (const uint8_t * buffer, size_t size) {
  s_packet (0, buffer, size);
}

static void s_PS1_onPacketReceived (const uint8_t * buffer, size_t size) {
  s_packet (1, buffer, size);
}

static void s_PS2_onPacketReceived (const uint8_t * buffer, size_t size) {
  s_packet (2, buffer, size);
}

static void s_input_check_stream (Stream * S, char channel_no) { // for diagnostics only
  if (S->available () > 0) {
    Serial.print ("[#");
    Serial.write (channel_no);
    while (S->available () > 0) {
      byte c = S->read ();
      Serial.print (' ');
      Serial.print (c, HEX);
    }
    Serial.print (" ] ");
  }
}

#endif

void io_setup () {
  Writer::init_channels ();
}

void io_check () {
  /* Check & update output streams
   */
  Writer::update_all ();

#if 0
  PS1.update ();
  PS2.update ();

  s_input_check_stream (&Serial4, '4');
  s_input_check_stream (&Serial5, '5');

  if (s_bUsePacketSerial) {
    PS0.update ();
    return; // don't process any further input on Serial
  }
#endif /* CORE_TEENSY */

  while (true) {
    int c = Serial.peek ();
    if (c > 0) {
      input_push ((byte) Serial.read ());
      continue;
    }
    if (c == 0) {
      s_bUsePacketSerial = true;
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
      Message::pgm_message(s_interrupt).send ();
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

  Serial.print (input_buffer);
}

static void input_parse (uint8_t address_src, const char * buffer, size_t size) {
  if (!buffer || (size > 255)) {
    // too long!
    return;
  }

  char * ptr = input_bufcpy;
  int    argc = 0;

  memcpy (input_bufcpy, buffer, size);
  input_bufcpy[size] = 0;

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
    CommandStatus cs = s_fn_command (address_src, argc, input_argv);

    if (cs != cs_Okay) {
      Message response(Message::Text_Error);

      if (cs == cs_InvalidPin) {
	response.append_pgm (s_err_pin_no);
      } else if (cs == cs_IncorrectUsage) {
	response.append_pgm (s_err_usage);
      } else {
	response.append_pgm (s_err_command);
      }
      response.send (address_src);
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
