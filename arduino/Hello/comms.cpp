/* Copyright 2018 Francis James Franklin
 * 
 * Open Source under the MIT License - see LICENSE in the project's root folder
 */

#include "comms.hh"
#include "util.hh"

#ifdef ENABLE_CHANNEL_1_BLE
#include "Adafruit_BluefruitLE_SPI.h"

#define BLUEFRUIT_SPI_CS               8
#define BLUEFRUIT_SPI_IRQ              7
#define BLUEFRUIT_SPI_RST              4

#define BLE_BUFSIZE                 1024
#endif

#ifndef ARDUINO_SAMD_ZERO
#include <EEPROM.h>
#endif
Channel * channels[CHANNEL_COUNT];

uint8_t local_address;     // Get from EEPROM; shuold be unique & in range 0x01-0x7e
uint8_t input_default = 0; // default address for normal responses is 0, which is just Serial

static uint8_t s_pkt_default; // default address for packet responses is (local_address | 0x80)

Network s_net;

Network & Network::network () {
  return s_net;
}

void Network::broadcast () {
  uint8_t * data_buffer = 0;

  int length = 0;

  Message message(local_address, ADDRESS_BROADCAST, Message::Broadcast_Address);
  message.encode (data_buffer, length); // this provides values for data_buffer and length

  for (int ch = 0; ch < CHANNEL_COUNT; ch++) {
    if (channels[ch]) {
      Writer * W = channels[ch]->writer;

      if (W->encoded ()) {
	W->add (new MessageTask(local_address, ADDRESS_BROADCAST, Message::Broadcast_Address, data_buffer, length, true /* copy data */));
      }
    }
  }
}

Network::Network () :
  m_handler(0)
{
  for (uint8_t p = 0; p < 64; p++) {
    m_ports[p] = 0xff;
  }
}

int Network::get_channel (uint8_t address) const { // returns channel number (0-6), or -1 if none set, for address (1-126)
  if (address == ADDRESS_BROADCAST) { // error - handle broadcast elsewhere
    return -1;
  }
  address &= 0x7f; // ignore the 8th bit

  uint8_t index = address >> 1;
  bool bHighNibble = address & 1;

  uint8_t channel = m_ports[index];

  if (!bHighNibble) {
    channel &= 0x0f;
  } else {
    channel = (channel & 0xf0) >> 4;
  }
  return (channel < CHANNEL_COUNT) ? (int) channel : -1;
}

void Network::set_channel (uint8_t address, uint8_t channel) { // returns channel number (0-6) for address (1-126)
  if (address == ADDRESS_BROADCAST) { // ignore
    return;
  }

  if (channel < CHANNEL_COUNT) {
    address &= 0x7f; // ignore the 8th bit

    uint8_t index = address >> 1;
    bool bHighNibble = address & 1;

    if (!bHighNibble) {
      m_ports[index] = (m_ports[index] & 0xf0) | channel;
    } else {
      m_ports[index] = (m_ports[index] & 0x0f) | (channel << 4);
    }
  }
}

void Network::message_received (uint8_t channel_number, Message & message) {
  uint8_t address_src  = message.get_address_src ();
  uint8_t address_dest = message.get_address_dest ();

  if (address_src != ADDRESS_UNKNOWN) {
    set_channel (address_src, channel_number);
  }

  if (address_dest == local_address) {
    switch (message.get_type ()) { // handle special cases, or pass along

    case Message::Raw_Data:
    case Message::Request_Address:
    case Message::Supply_Address:
    case Message::Broadcast_Address:
    case Message::Text_Response:
    case Message::Text_Error:
      // shouldn't be here
      break;

    case Message::Ping:
      message.clear ();
      message.set_address_src (address_dest);
      message.set_address_dest (address_src);
      message.set_type (Message::Pong);
      message.send ();
      break;

    case Message::No_Route:
      // TODO: remove from ports list + ??
    default:
      if (m_handler) {
	m_handler->message_received (message);
      }
      break;
    }
  } else if (address_dest == ADDRESS_BROADCAST) {
    if (message.get_type () == Message::Broadcast_Address) {
      uint8_t * data_buffer = 0;

      int length = 0;

      message.encode (data_buffer, length); // this provides values for data_buffer and length

      for (int ch = 0; ch < CHANNEL_COUNT; ch++) {
	if (ch == channel_number) {
	  continue; // don't send it back the way it came
	}
	if (channels[ch]) {
	  Writer * W = channels[ch]->writer;

	  if (W->encoded ()) {
	    W->add (new MessageTask(address_src, ADDRESS_BROADCAST, Message::Broadcast_Address, data_buffer, length, true /* copy data */));
	  }
	}
      }
    } // else { // do nothing }
  } else if (address_dest == ADDRESS_UNKNOWN) {
    if (message.get_type () == Message::Request_Address) { // an external connection requesting an address
      set_channel (s_pkt_default, channel_number);
      message.clear ();
      message.set_address_src (local_address);
      message.set_address_dest (s_pkt_default);
      message.set_type (Message::Supply_Address);
      message.send ();
    } // else { // do nothing }
  } else { // this message is just passing through; send it on its way...
    message.send ();
  }
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
  SerialWriter (Stream & serial, uint8_t channel_number) :
    Writer(channel_number),
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
  SerialReader (Stream & serial, uint8_t channel_number) :
    Reader(channel_number),
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
    //    Serial.write (c);
    if (m_input.decode (c) == Message::cobs_HavePacket) { // we have a valid response
      s_net.message_received (m_channel_number, m_input);

      m_input.clear ();
    }
  }
  void push_console (uint8_t c) {
    if (c == 0) { // looks like an encoded stream
      channels[m_channel_number]->set_encoded (true);
      m_input.clear ();
    } else if ((c == 10) || (c == 13)) { // newline || carriage return
      m_serial.write (c);

      if (m_input.get_length ()) {
	m_input.set_address_src (input_default);
	m_input.set_address_dest (local_address);
	m_input.set_type (Message::Text_Command);

	s_net.message_received (m_channel_number, m_input);

	m_input.clear ();
      }
    } else if (c == 3) { // ^C
      m_input.clear ();

      m_input.set_address_src (input_default);
      m_input.set_address_dest (local_address);
      m_input.set_type (Message::User_Interrupt);

      s_net.message_received (m_channel_number, m_input);

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

#ifdef ENABLE_CHANNEL_1_BLE

static Adafruit_BluefruitLE_SPI s_ble(BLUEFRUIT_SPI_CS, BLUEFRUIT_SPI_IRQ, BLUEFRUIT_SPI_RST);

static bool s_ble_connected = false;

static bool s_ble_check (Adafruit_BluefruitLE_SPI & ble) {
  if (s_ble_connected) {
    if (!ble.isConnected ()) { // we've lost the connection
      s_ble_connected = false;

      ble.sendCommandCheckOK ("AT+HWModeLED=MODE");
    }
  } else {
    if (ble.isConnected ()) { // we've just established a connection
      s_ble_connected = true;

      ble.sendCommandCheckOK ("AT+HWModeLED=DISABLE");
    }
  }
  return s_ble_connected;
}

class BLEWriter : public Writer {
private:
  Adafruit_BluefruitLE_SPI & m_ble;

public:
  BLEWriter (Adafruit_BluefruitLE_SPI & ble, uint8_t channel_number) :
    Writer(channel_number),
    m_ble(ble)
  {
    // ...
  }

  ~BLEWriter () {
    // ...
  }

  virtual int available () {
    int count = 0;

    if (s_ble_check (m_ble)) {
      m_ble.println ("AT+BLEUARTFIFO=TX");

      long bytes = m_ble.readline_parseInt ();

      if (bytes > 200) // limit single transaction length // AT commands limited to 240 bytes?? - check
	count = 200;
      else if (bytes > 0)
	count = (int) bytes - 1;
    }
    return count;
  }

  virtual int write (uint8_t * buffer, int length) {
    if (!buffer || (length < 1)) return -1; // error

    int nbytes = available ();

    uint8_t * ptr = buffer;

    if (nbytes > 1) {
      m_ble.print ("AT+BLEUARTTX=");

      while (length && (nbytes > 1)) {
	if (*ptr == '\n') {
	  --length;
	  ++ptr;
	  continue;
	}
	if (*ptr == '\r') {
	  m_ble.print ('\\');
	  m_ble.print ('n');
	  --nbytes;
	} else {
	  m_ble.write (*ptr);
	}
	--nbytes;
	--length;
	++ptr;
      }
      m_ble.println ();
    }
    return ptr - buffer;
  }
};

class BLEReader : public Reader {
private:
  char m_buffer[BLE_BUFSIZE];

  Message m_input;

  Adafruit_BluefruitLE_SPI & m_ble;

public:
  BLEReader (Adafruit_BluefruitLE_SPI & ble, uint8_t channel_number) :
    Reader(channel_number),
    m_input(0,0,Message::Text_Command), // Message addresses & type to be fixed later
    m_ble(ble)
  {
    // ...
  }

  ~BLEReader () {
    // ...
  }
private:
  void push_encoded (uint8_t c) {
    //    Serial.write (c);
    if (m_input.decode (c) == Message::cobs_HavePacket) { // we have a valid response
      s_net.message_received (m_channel_number, m_input);

      m_input.clear ();
    }
  }
  void push_console (uint8_t c) {
    if (c == 0) { // looks like an encoded stream
      // error
      m_input.clear ();
    } else if ((c == 10) || (c == 13)) { // newline || carriage return
      if (strcmp (m_input.c_str (), "OK") == 0) {
	m_input.clear ();
      } else if (m_input.get_length ()) {
	m_input.set_address_src (input_default);
	m_input.set_address_dest (local_address);
	m_input.set_type (Message::Text_Command);

	s_net.message_received (m_channel_number, m_input);

	m_input.clear ();
      }
    } else if ((c >= 32) && (c < 127)) {
      if (m_input.get_length () < MESSAGE_MAXSIZE) { // otherwise just ignore
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
  int get_bytes () {
    int count = 0;

    if (s_ble_check (m_ble)) {
      m_ble.println ("AT+BLEUARTFIFO=RX");

      long bytes = m_ble.readline_parseInt ();

      if (bytes > 1023) // limit is 1024
	count = 0;
      else {
	count = 1023 - (int) bytes;
      }
    }
    if (count) {
      m_ble.println ("AT+BLEUARTRX");

      count = m_ble.readline (m_buffer, BLE_BUFSIZE - 1, true);
      m_buffer[count] = 0;

      if (strcmp (m_buffer, "OK")) {
	m_ble.waitForOK ();
      } else {
	count = 0;
	m_buffer[0] = 0;
      }
    }
    return count;
  }
public:
  virtual void update () {
    while (get_bytes ()) {
      const char * ptr = m_buffer;

      while (*ptr) {
	uint8_t c = *ptr++;

	if (encoded ()) {
	  push_encoded (c);
	} else if (console ()) {
	  push_console (c);
	} else {
	  push_raw (c);
	}
      }
    }
    if (!encoded () && !console ()) { // for raw data, send everything we've got
      if (m_input.get_length ()) {        // if we have anything, that is
	send_raw ();
      }
    }
  }
};

#endif /* ENABLE_CHANNEL_1_BLE */

#ifdef ENABLE_CHANNEL_0
static SerialWriter SW_0(Serial,0);
static SerialReader SR_0(Serial,0);
static Channel s_channel_0(&SW_0, &SR_0);
#endif
#ifdef ENABLE_CHANNEL_1
static SerialWriter SW_1(Serial1,1);
static SerialReader SR_1(Serial1,1);
static Channel s_channel_1(&SW_1, &SR_1);
#endif
#ifdef ENABLE_CHANNEL_2
static SerialWriter SW_2(Serial2,2);
static SerialReader SR_2(Serial2,2);
static Channel s_channel_2(&SW_2, &SR_2);
#endif
#ifdef ENABLE_CHANNEL_3
static SerialWriter SW_3(Serial3,3);
static SerialReader SR_3(Serial3,3);
static Channel s_channel_3(&SW_3, &SR_3);
#endif
#ifdef ENABLE_CHANNEL_4
static SerialWriter SW_4(Serial4,4);
static SerialReader SR_4(Serial4,4);
static Channel s_channel_4(&SW_4, &SR_4);
#endif
#ifdef ENABLE_CHANNEL_5
static SerialWriter SW_5(Serial5,5);
static SerialReader SR_5(Serial5,5);
static Channel s_channel_5(&SW_5, &SR_5);
#endif
#ifdef ENABLE_CHANNEL_6
static SerialWriter SW_6(Serial6,6);
static SerialReader SR_6(Serial6,6);
static Channel s_channel_6(&SW_6, &SR_6);
#endif

#ifdef ENABLE_CHANNEL_1_BLE
static BLEWriter BW_1(s_ble, 1);
static BLEReader BR_1(s_ble, 1);
static Channel s_channel_1(&BW_1, &BR_1);
#endif

void set_local_address (uint8_t address) { // Program a new address in EEPROM; use with caution
#ifndef ARDUINO_SAMD_ZERO
  if ((address > 0) && (address < 0x7f)) {
    EEPROM.write (0, address);
  }
  local_address = EEPROM.read (0);
#else
  local_address = address;
#endif
}

void Channel::init_all () {
#ifndef ARDUINO_SAMD_ZERO
  local_address = EEPROM.read (0);
#else
  local_address = *((volatile uint8_t *) 0x0080A040);
#endif
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

#ifdef ENABLE_CHANNEL_1_BLE
  if (s_ble.begin ()) {
    channels[1] = &s_channel_1;
  }
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
  if (address == ADDRESS_BROADCAST) {   // handle broadcast messages elsewhere
    return 0;
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

bool PGMListTask::update (Writer & W) { // returns true when task complete
  if (!pgm_str_ptr) return true;
  if (!*pgm_str_ptr) return true;

  message.clear ();
  message.pgm (*pgm_str_ptr++);

  Message::MessageType type = message.get_type ();

  if (W.console () && !W.encoded ()) {
    message += "\r\n";
  }

  uint8_t * data_buffer = message.get_buffer ();

  int length = (int) message.get_length ();

  if (W.encoded ()) {
    message.encode (data_buffer, length); // this provides values for data_buffer and length
  }
  W.add (new MessageTask(address_src, address_dest, type, data_buffer, length, false /* don't copy data */));

  return false;
}
