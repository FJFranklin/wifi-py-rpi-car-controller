/* Copyright 2017-18 Francis James Franklin
 * 
 * Open Source under the MIT License - see LICENSE in the project's root folder
 */

#include <EEPROM.h>

#include "util.hh"

uint8_t local_address; // Get from EEPROM

static uint8_t s_src_default = 0; // default address for responses is 0, which is just Serial

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

Message Message::pgm_message (const char * pgm) { // create new message with string stored in PROGMEM
  Message M;
  M.append_pgm (pgm);
  return M;
}

void Message::append_pgm (const char * pgm) { // append string stored in PROGMEM
  if (!pgm) return;

  while (true) {
    byte c = pgm_read_byte_near (pgm++);
    if (!c) break;
    text += (char) c;
  }
}

void Message::send (uint8_t address) {
  if (s_bEchoOn && (address != local_address)) { // don't send to self
    if (address) {
      // ...
    } else {
      Serial.print (text);
      Serial.print ("\r\n");
    }
  }
  text = "";
}

/* Suppress printing if echo is off.
 */
void echo (bool bOn) {
  s_bEchoOn = bOn;
}

#ifdef CORE_TEENSY

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

#endif /* CORE_TEENSY */

void input_setup () {
  local_address = EEPROM.read (0);

  Serial.begin (115200);
#ifdef CORE_TEENSY
  Serial1.begin (2000000);
  Serial2.begin (2000000);

  PS0.setStream (&Serial);
  PS1.setStream (&Serial1);
  PS2.setStream (&Serial2);

  PS0.setPacketHandler (s_PS0_onPacketReceived);
  PS1.setPacketHandler (s_PS1_onPacketReceived);
  PS2.setPacketHandler (s_PS2_onPacketReceived);

  Serial4.begin (9600); // or 500000 for fast serial compatible across Teensy 3.x range
  Serial5.begin (9600);
#endif /* CORE_TEENSY */
}

void serial_ping (char channel_no, const char * str) {
  if (!s_bUsePacketSerial && (channel_no == '0')) {
    Serial.print (str);
  }
#ifdef CORE_TEENSY
  if (s_bUsePacketSerial && (channel_no == '0')) {
    PS0.send ((const uint8_t *) str, strlen (str));
  }
  if (channel_no == '1') {
    PS1.send ((const uint8_t *) str, strlen (str));
  }
  if (channel_no == '2') {
    PS2.send ((const uint8_t *) str, strlen (str));
  }
  if (channel_no == '4') {
    Serial4.print (str);
  }
  if (channel_no == '5') {
    Serial5.print (str);
  }
#endif /* CORE_TEENSY */
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

void input_check () {
#ifdef CORE_TEENSY
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
      input_parse (s_src_default, input_buffer + 2, input_count);
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

