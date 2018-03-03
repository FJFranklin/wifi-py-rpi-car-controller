/* Copyright 2018 Francis James Franklin
 * 
 * Open Source under the MIT License - see LICENSE in the project's root folder
 */

#include "comms.hh"
#include "util.hh"

#include <EEPROM.h>

Channel * channels[CHANNEL_COUNT];

uint8_t local_address;     // Get from EEPROM; shuold be unique & in range 0x01-0x7f
uint8_t input_default = 0; // default address for normal responses is 0, which is just Serial

static uint8_t s_pkt_default;                        // default address for packet responses is (local_address | 0x80)
static uint8_t s_broadcast = (input_default | 0x80); // broadcast address, i.e., 0x80

Network s_net;

Network::Network () {
  for (uint8_t p = 0; p < 63; p++) {
    m_ports[p] = 0xff;
  }
}

int Network::get_channel (uint8_t address) const { // returns channel number (0-6), or -1 if none set, for address (1-126)
  address &= 0x7f; // ignore the 8th bit

  uint8_t index = (address - 1) >> 1;
  bool bLowNibble = address & 1;

  uint8_t channel = m_ports[index];

  if (bLowNibble) {
    channel &= 0x0f;
  } else {
    channel = (channel & 0xf0) >> 4;
  }
  return (channel < CHANNEL_COUNT) ? (int) channel : -1;
}

void Network::set_channel (uint8_t address, uint8_t channel) { // returns channel number (0-6) for address (1-126)
  if (channel < CHANNEL_COUNT) {
    address &= 0x7f; // ignore the 8th bit

    uint8_t index = (address - 1) >> 1;
    bool bLowNibble = address & 1;

    if (bLowNibble) {
      m_ports[index] = (m_ports[index] & 0xf0) | channel;
    } else {
      m_ports[index] = (m_ports[index] & 0x0f) | (channel << 4);
    }
  }
}

void Network::message_received (Message & message) {
  // TODO
}

void Network::interrupt (Message & message) {
  // TODO
}

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

class SerialReader : public Reader {
private:
  Message m_input;

  Stream & m_serial;

public:
  SerialReader (Stream & serial) :
    m_input(0,0,Message::Text_Command), // Message addresses & type to be fixed later
    m_serial(serial)
  {
    // ...
  }

  ~SerialReader () {
    // ...
  }
private:
  void push_encoded (uint8_t c) {
    // TODO
  }
  void push_console (uint8_t c) {
    if ((c == 10) || (c == 13)) { // newline || carriage return
      m_serial.write (c);

      m_input.set_address_src (input_default);
      m_input.set_address_dest (local_address);
      m_input.set_type (Message::Text_Command);

      if (m_handler) {
	m_handler->message_received (m_input);
      }
      m_input.clear ();
    } else if (c == 3) { // ^C
      m_input.clear ();

      m_input.set_address_src (input_default);
      m_input.set_address_dest (local_address);
      m_input.set_type (Message::User_Interrupt);

      if (m_handler) {
	m_handler->interrupt (m_input);
      }
      m_serial.print ("\r\n");
    } else if (c == 127) { // delete
      if (m_input.get_length () > 0) { // otherwise just ignore
	m_serial.print ("\b \b");
	--m_input;
      }
    } else if ((c >= 32) && (c < 127)) {
      if (m_input.get_length () < MESSAGE_MAXSIZE) { // otherwise just ignore
	m_serial.write (c);
	m_input += c;
      }
    }
  }
  void send_raw () {
    m_input.set_address_src (input_default);
    m_input.set_address_dest (local_address);
    m_input.set_type (Message::Raw_Data);

    if (m_handler) {
      m_handler->message_received (m_input);
    }
    m_input.clear ();
  }
  void push_raw (uint8_t c) {
    m_input += c;

    if (m_input.get_length () == MESSAGE_MAXSIZE) {
      send_raw ();
    }
  }
public:
  virtual void update () {
    while (m_serial.available ()) {
      uint8_t c = m_serial.read ();

      if (encoded ()) {
	push_encoded (c);
      } else if (console ()) {
	push_console (c);
      } else {
	push_raw (c);
      }
    }
    if (!encoded () && !console ()) { // for raw data, send everything we've got
      if (m_input.get_length ()) {        // if we have anything, that is
	send_raw ();
      }
    }
  }
};

#ifdef ENABLE_CHANNEL_0
static SerialWriter SW_0(Serial);
static SerialReader SR_0(Serial);
static Channel s_channel_0(&SW_0, &SR_0);
#endif
#ifdef ENABLE_CHANNEL_1
static SerialWriter SW_1(Serial1);
static SerialReader SR_1(Serial1);
static Channel s_channel_1(&SW_1, &SR_1);
#endif
#ifdef ENABLE_CHANNEL_2
static SerialWriter SW_2(Serial2);
static SerialReader SR_2(Serial2);
static Channel s_channel_2(&SW_2, &SR_2);
#endif
#ifdef ENABLE_CHANNEL_3
static SerialWriter SW_3(Serial3);
static SerialReader SR_3(Serial3);
static Channel s_channel_3(&SW_3, &SR_3);
#endif
#ifdef ENABLE_CHANNEL_4
static SerialWriter SW_4(Serial4);
static SerialReader SR_4(Serial4);
static Channel s_channel_4(&SW_4, &SR_4);
#endif
#ifdef ENABLE_CHANNEL_5
static SerialWriter SW_5(Serial5);
static SerialReader SR_5(Serial5);
static Channel s_channel_5(&SW_5, &SR_5);
#endif
#ifdef ENABLE_CHANNEL_6
static SerialWriter SW_6(Serial6);
static SerialReader SR_6(Serial6);
static Channel s_channel_6(&SW_6, &SR_6);
#endif

void set_local_address (uint8_t address) { // Program a new address in EEPROM; use with caution
  if ((address > 0) && (address < 0x7f)) {
    EEPROM.write (0, address);
  }
  local_address = EEPROM.read (0);
}

void Channel::init_all () {
  local_address = EEPROM.read (0);

  if ((local_address == 0) || (local_address >= 0x7f)) { // oops - not set properly?
    local_address = 0x7f;
  }

  s_pkt_default = local_address | 0x80;

  for (int ch = 0; ch < CHANNEL_COUNT; ch++) {
    channels[ch] = 0;
  }

#ifdef ENABLE_CHANNEL_0
  channels[0] = &s_channel_0;
  Serial.begin (CHANNEL_0_BAUD);
#endif
#ifdef ENABLE_CHANNEL_1
  channels[1] = &s_channel_1;
  Serial1.begin (CHANNEL_1_BAUD);
#endif
#ifdef ENABLE_CHANNEL_2
  channels[2] = &s_channel_2;
  Serial2.begin (CHANNEL_2_BAUD);
#endif
#ifdef ENABLE_CHANNEL_3
  channels[3] = &s_channel_3;
  Serial3.begin (CHANNEL_3_BAUD);
#endif
#ifdef ENABLE_CHANNEL_4
  channels[4] = &s_channel_4;
  Serial4.begin (CHANNEL_4_BAUD);
#endif
#ifdef ENABLE_CHANNEL_5
  channels[5] = &s_channel_5;
  Serial5.begin (CHANNEL_5_BAUD);
#endif
#ifdef ENABLE_CHANNEL_6
  channels[6] = &s_channel_6;
  Serial6.begin (CHANNEL_6_BAUD);
#endif
}

void Channel::update_all () {
  for (int ch = 0; ch < CHANNEL_COUNT; ch++) {
    if (channels[ch]) {
      channels[ch]->update ();
    }
  }
}

Writer * Writer::lookup (uint8_t address) {
  if (address == local_address) { // don't send anything to ourselves!
    return 0;
  }
  if (address == s_broadcast) {   // handle broadcast messages elsewhere
    return 0;
  }

  if (address == input_default) { // default address for normal responses
    return channels[CHANNEL_CONSOLE]->writer;
  }

  /* Otherwise, need to work out which channel to send the messages to... // TODO // FIXME
   */
  int ch = s_net.get_channel (address);

  if (ch < 0) {
    return 0;
  }
  return channels[ch]->writer;
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

  Writer * W = Writer::lookup (address_dest);

  if (W) {
    MessageType type = get_type ();

    if (W->console ()) {
      *this += "\r\n";
    }

    uint8_t * data_buffer = get_buffer ();

    int length = (int) get_length ();

    if (W->encoded ()) {
      encode (data_buffer, length); // this provides values for data_buffer and length
    }
    W->add (new MessageTask(address_src, address_dest, type, data_buffer, length, true /* copy data */));
  }
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
