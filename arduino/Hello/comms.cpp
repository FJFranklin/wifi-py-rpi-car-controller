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

void Writer::add_task (Task * task) {
  if (!task) return;

  if (task->address_dest == local_address) { // don't send anything to ourselves!
    return;
  }
  if (task->address_dest == s_broadcast) {   // handle broadcast messages elsewhere
    return;
  }

  if (task->address_dest == input_default) { // default address for normal responses
    Channel_0->add (task);
    return;
  }
  if (task->address_dest == s_pkt_default) { // default address for packet responses
    Channel_0->add (task);
    return;
  }

  /* Otherwise, need to work out which channel to send the messages to... // TODO // FIXME
   */
  Channel_0->add (task);
}

MessageTask::MessageTask (Message::MessageType type, uint8_t address_src, uint8_t address_dest, uint8_t * buffer, uint8_t length, bool bCopyBuffer) :
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
  // if (s_bEchoOn && (address != local_address)) { // don't send to self
    if (address) {
      // ...
    } else {
      text += "\r\n";
      Writer::add_task (new MessageTask(type, local_address, address, (uint8_t *) text.c_str (), (uint8_t) text.length ()));
      // Serial.print (text);
      // Serial.print ("\r\n");
    }
  // }
  text = "";
}
