/* Copyright 2018 Francis James Franklin
 * 
 * Open Source under the MIT License - see LICENSE in the project's root folder
 */

#include "comms.hh"
#include "util.hh"

#include <EEPROM.h>

Writer * Channel_0 = 0;
Writer * Channel_1 = 0;
Writer * Channel_2 = 0;
Writer * Channel_3 = 0;
Writer * Channel_4 = 0;
Writer * Channel_5 = 0;
Writer * Channel_6 = 0;

uint8_t local_address;     // Get from EEPROM; shuold be unique & in range 0x01-0x7f
uint8_t input_default = 0; // default address for normal responses is 0, which is just Serial

static uint8_t s_pkt_default;                        // default address for packet responses is (local_address | 0x80)
static uint8_t s_broadcast = (input_default | 0x80); // broadcast address, i.e., 0x80

void Writer::update () {
  if (!next) return;

  if (next->update (*this)) { // task complete; remove & advance
    Task * task = next;
    next = task->next;
    delete task;
  }
}

void Writer::add (Task * task) {
  if (!task) return;

  if (!next) { // nothing queued, just add
    next = task;
  } else if (task->priority < next->priority) { // first item in queue has lower priority; insert at front
    task->next = next;
    next = task;
  } else { // work through the queue
    Task * T = next;

    while (true) {
      if (!T->next) { // nothing else queued, just add at end
	T->next = task;
      } else if (task->priority < T->next->priority) { // next item in queue has lower priority; insert here
	task->next = next;
	next = task;
      } else {
	T = T->next;
	continue;
      }
      break;
    }
  }
}

class SerialWriter : public Writer {
private:
  Stream & m_serial;

public:
  SerialWriter (Stream & serial) :
    m_serial(serial)
  {
    // ...
  }

  ~SerialWriter () {
    // ...
  }

  virtual int available () {
    return m_serial.availableForWrite ();
  }

  virtual int write (uint8_t * buffer, int length) {
    if (!buffer || (length < 1)) return -1; // error

    int nbytes = available ();

    if (length > nbytes) {
      length = nbytes;
    }
    return m_serial.write (buffer, length);
  }
};

void Writer::init_channels () {
  local_address = EEPROM.read (0);

  if ((local_address == 0) || (local_address > 0x7f)) { // oops - not set properly?
    local_address = 0x7f;
  }

  s_pkt_default = local_address | 0x80;

  Serial.begin (115200);

  Channel_0 = new SerialWriter(Serial);

#if 0
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
#endif
}

void Writer::update_all () {
  if (Channel_0) Channel_0->update ();
  if (Channel_1) Channel_1->update ();
  if (Channel_2) Channel_2->update ();
  if (Channel_3) Channel_3->update ();
  if (Channel_4) Channel_4->update ();
  if (Channel_5) Channel_5->update ();
  if (Channel_6) Channel_6->update ();
}

Writer * Writer::channel (uint8_t address) {
  if (address == local_address) { // don't send anything to ourselves!
    return 0;
  }
  if (address == s_broadcast) {   // handle broadcast messages elsewhere
    return 0;
  }

  if (address == input_default) { // default address for normal responses
    return Channel_0;
  }
  if (address == s_pkt_default) { // default address for packet responses
    return Channel_0;
  }

  /* Otherwise, need to work out which channel to send the messages to... // TODO // FIXME
   */
  return 0;
}

MessageTask::MessageTask (uint8_t address_src, uint8_t address_dest, Message::MessageType type, uint8_t * buffer, int length, bool bCopyBuffer) :
  Task(Task::p_High,address_src,address_dest),
  m_buffer(buffer),
  m_ptr(0),
  m_length(length),
  m_type(type),
  m_bCopyBuffer(bCopyBuffer)
{
  if (!buffer) {
    m_length = 0;
  }
  if (m_length && m_bCopyBuffer) {
    m_buffer = new uint8_t[m_length];

    if (m_buffer) {
      memcpy (m_buffer, buffer, m_length);
    }
  }
  m_ptr = m_buffer;
}

MessageTask::~MessageTask () {
  if (m_buffer && m_bCopyBuffer) delete [] m_buffer;
}

bool MessageTask::update (Writer & W) { // returns true when task complete
  uint8_t bytes_remaining = m_length - (m_ptr - m_buffer);
  uint8_t bytes_writable = W.available ();
  uint8_t bytes = bytes_remaining;

  bool bComplete = true;

  if (bytes_writable < bytes_remaining) {
    bytes = bytes_writable;
    bComplete = false;
  }
  W.write (m_ptr, bytes);

  m_ptr += bytes;

  return bComplete;
}

Message & Message::append_int (int i) { // change number to string, and append
  static char buffer[12];
  sprintf (buffer, "%d", i);
  *this += buffer;
  return *this;
}

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

void Message::send () {
  uint8_t address_src  = get_address_src ();
  uint8_t address_dest = get_address_dest ();

  Writer * W = Writer::channel (address_dest);

  if (W) {
    MessageType type = get_type ();

    uint8_t * data_buffer = get_buffer ();

    int length = (int) get_length ();

    if (W->encoded ()) {
      encode (data_buffer, length); // this provides values for data_buffer and length
    } else if (W->newlines ()) {
	*this += "\r\n";
    }
    W->add (new MessageTask(address_src, address_dest, type, buffer, length, true /* copy data */));
  }
  clear ();
}

Message & Message::operator+= (uint8_t uc) {
  uint8_t length = get_length ();

  if (length < MESSAGE_MAXSIZE) {
    buffer[4+(length++)] = uc;
  }
  set_length (length);

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
    buffer[offset++] = 0;
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
      break;
    }
    --ptr1;
  }

  bytes = ptr2;
  size = MESSAGE_BUFSIZE - (ptr2 - buffer);
}
