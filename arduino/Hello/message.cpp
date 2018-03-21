/* Copyright 2018 Francis James Franklin
 * 
 * Open Source under the MIT License - see LICENSE in the project's root folder
 */

#ifdef COBS_USER // Not for the Arduino
#include <cstdio>
typedef unsigned char uint8_t;
extern void cobs_user_send (uint8_t * data_buffer, int length);
#include "message.hh"
#else
#include <Arduino.h>
#include "comms.hh"
#endif

Message & Message::append_lu (unsigned long i) { // change number to string, and append
  static char buffer[12];
  sprintf (buffer, "%lu", i);
  *this += buffer;
  return *this;
}

Message & Message::append_int (int i) { // change number to string, and append
  static char buffer[12];
  sprintf (buffer, "%d", i);
  *this += buffer;
  return *this;
}

Message & Message::append_hex (uint8_t i) { // change number to string, and append
  static char buffer[4];
  sprintf (buffer, "%02x", (unsigned int) i);
  *this += buffer;
  return *this;
}

#ifndef COBS_USER // For the Arduino

Message & Message::pgm (const char * str) { // append string stored in PROGMEM
  if (str) {
    while (true) {
      byte c = pgm_read_byte_near (str++);
      if (!c) break;
      *this += (uint8_t) c;
    }
  }
  return *this;
}

void Message::pgm_list (const char ** list) { // send list of text messages stored in PROGMEM
  uint8_t address_src  = get_address_src ();
  uint8_t address_dest = get_address_dest ();

  Writer * W = Writer::lookup (address_dest);

  if (W) {
    W->add (new PGMListTask(address_src, address_dest, list));
  }
}

#endif

void Message::send () {
#ifdef COBS_USER // Not for the Arduino
  uint8_t * data_buffer = 0;

  int length = 0;

  encode (data_buffer, length); // this provides values for data_buffer and length

  cobs_user_send (data_buffer, length);
#else
  uint8_t address_src  = get_address_src ();
  uint8_t address_dest = get_address_dest ();

  Writer * W = Writer::lookup (address_dest);

  if (W) {
    MessageType type = get_type ();

    if (W->console () && !W->encoded ()) {
      *this += "\r\n";
    }

    uint8_t * data_buffer = get_buffer ();

    int length = (int) get_length ();

    if (W->encoded ()) {
      encode (data_buffer, length); // this provides values for data_buffer and length
    }
    W->add (new MessageTask(address_src, address_dest, type, data_buffer, length, true /* copy data */));
  }
#endif
  clear ();
}

Message & Message::operator-- () { // remove last character
  uint8_t length = get_length ();

  if (length > 0) {
    set_length (--length);
    buffer[4+length] = 0;
  }
  return *this;
}

Message & Message::operator+= (uint8_t uc) {
  uint8_t length = get_length ();

  if (length < MESSAGE_MAXSIZE) {
    buffer[4+(length++)] = uc;
  }
  set_length (length);
  buffer[4+length] = 0;

  return *this;
}

Message & Message::operator+= (const char * right) {
  if (right) {
    uint8_t length = get_length ();
    uint8_t spaces = MESSAGE_MAXSIZE - length;

    while (spaces--) {
      if (!*right) break;
      buffer[4+(length++)] = *right++;
    }
    set_length (length);
    buffer[4+length] = 0;
  }
  return *this;
}

Message & Message::operator= (const char * right) {
  uint8_t length = 0;

  if (right) {
    uint8_t spaces = MESSAGE_MAXSIZE;

    while (spaces--) {
      if (!*right) break;
      buffer[4+(length++)] = *right++;
    }
    set_length (length);
    buffer[4+length] = 0;
  }
  return *this;
}

Message::COBS_State Message::decode (uint8_t c) {
  if (!c) { // EOP
    if (cobsin) { // we were expecting something non-zero
      clear ();   // reset
      return cobs_UnexpectedEOP;
    }
    if (offset < 4) { // invalid packet
      clear ();   // reset
      return cobs_InvalidPacket;
    }
    if (get_length () != (offset - 4)) { // invalid packet
      clear ();   // reset
      return cobs_InvalidPacket;
    }
    buffer[offset] = 0;
    return cobs_HavePacket;
  }
  if (offset >= (MESSAGE_MAXSIZE + 4)) { // packet too long
    return cobs_TooLong;
  }
  if (cobsin) {
    --cobsin;
    buffer[offset++] = c;
  } else {
    cobsin = c - 1;
    if (offset) {
      buffer[offset++] = 0;
    }
  }
  return cobs_InProgress;
}

void Message::encode (uint8_t *& bytes, int & size) {
  uint8_t * ptr1 = buffer + get_length () + 3;
  uint8_t * ptr2 = buffer + MESSAGE_BUFSIZE - 1;

  uint8_t count = 0;

  *ptr2 = 0; // EOP

  while (true) {
    if (*ptr1 == 0) {
      *--ptr2 = ++count;
      count = 0;
    } else {
      *--ptr2 = *ptr1;
      ++count;
    }
    if (ptr1 == buffer) {
      *--ptr2 = ++count;
      break;
    }
    --ptr1;
  }

  bytes = ptr2;
  size = MESSAGE_BUFSIZE - (ptr2 - buffer);
}
