/* Copyright 2018 Francis James Franklin
 * 
 * Open Source under the MIT License - see LICENSE in the project's root folder
 */

#ifndef ArduinoHello_comms_hh
#define ArduinoHello_comms_hh

#include <Arduino.h>

#include "message.hh"

#define ENABLE_CHANNEL_0 // for Serial or, equivalently, SerialUSB
#define ENABLE_CHANNEL_1
#ifdef CORE_TEENSY
#define ENABLE_CHANNEL_2
#define ENABLE_CHANNEL_3
#define ENABLE_CHANNEL_4
// #define ENABLE_CHANNEL_5
// #define ENABLE_CHANNEL_6
#endif /* CORE_TEENSY */

#define CHANNEL_COUNT   7 // Number of serial channels

#define CHANNEL_0_BAUD  115200 // (although may differ in practice if it's a USB connection)
#define CHANNEL_1_BAUD 2000000 // 2000000 capability on Teensy 3.x. Note 1. Raspberry Pi & Arduino should be able
#define CHANNEL_2_BAUD 1000000 // 2000000 capability                        to handle 1000000 without glitches.
#define CHANNEL_3_BAUD  500000 // 2000000 capability                Note 2. Teensy LC okay at 500000.
#define CHANNEL_4_BAUD    9600 // 2000000 capability
#define CHANNEL_5_BAUD  921600 // 2000000 capability; 4608000 possible but with 0.16% error on Teensy 3.5/3.6
#define CHANNEL_6_BAUD 4608000 // 2000000 capability                         ( -0.79% )             ( 3.2 )

extern uint8_t local_address; // From EEPROM; valid device addresses are 1-127
extern uint8_t input_default; // address 0, reserved for direct input over Serial

extern void set_local_address (uint8_t address); // Program a new address in EEPROM

class Reader;
class Writer;

class Channel;

extern Channel * channels[CHANNEL_COUNT];

class MessageHandler {
public:
  virtual ~MessageHandler () {
    // ...
  }

  virtual void message_received (Message & message) = 0;
};

class Task {
public:
  enum Priority {
    p_High   = 0, // can't be interrupted
    p_Normal = 1,
    p_Low    = 2
  };

private:
  friend Writer;

  Task * next;

  Priority priority;
protected:
  uint8_t address_src;
  uint8_t address_dest;

  virtual bool update (Writer & W) = 0; // returns true when task complete

public:
  Task (Priority p, uint8_t src, uint8_t dest) :
    next(0),
    priority(p),
    address_src(src),
    address_dest(dest)
  {
    // ...
  }

  virtual ~Task () { }
};

class Writer {
private:
  Task * next;
protected:
  uint8_t m_channel_number;
private:
  bool m_bEncoded;
  bool m_bConsole;

public:
  Writer (uint8_t channel_number) :
    next(0),
    m_channel_number(channel_number),
    m_bEncoded(false),
    m_bConsole(true)
  {
    // ...
  }

  inline bool encoded () const {
    return m_bEncoded;
  }
  inline void set_encoded (bool bEncoded) {
    m_bEncoded = bEncoded;
  }
  inline bool console () const {
    return m_bConsole;
  }
  inline void set_console (bool bConsole) {
    m_bConsole = bConsole;
  }

  void update ();

  void add (Task * task);

  virtual int available () = 0;

  virtual int write (uint8_t * buffer, int length) = 0;

  virtual ~Writer () { }

  static Writer * lookup (uint8_t address);
};

class Reader {
protected:
  MessageHandler * m_handler;

  uint8_t m_channel_number;
private:
  bool m_bEncoded;
  bool m_bConsole;

public:
  Reader (uint8_t channel_number) :
    m_handler(0),
    m_channel_number(channel_number),
    m_bEncoded(false),
    m_bConsole(true)
  {
    // ...
  }

  virtual ~Reader () {
    // ...
  }

  inline bool encoded () const {
    return m_bEncoded;
  }
  inline void set_encoded (bool bEncoded) {
    m_bEncoded = bEncoded;
  }
  inline bool console () const {
    return m_bConsole;
  }
  inline void set_console (bool bConsole) {
    m_bConsole = bConsole;
  }

  inline void set_handler (MessageHandler * handler) { // for raw data only; if console or encoded, this handler is ignored
    m_handler = handler;
  }

  virtual void update () = 0;
};

class Channel {
public:
  Writer * writer;
  Reader * reader;

  Channel (Writer * W, Reader * R) :
    writer(W),
    reader(R)
  {
    // ...
  }

  ~Channel () {
    // ...
  }

  inline void set_encoded (bool bEncoded) {
    if (writer) writer->set_encoded (bEncoded);
    if (reader) reader->set_encoded (bEncoded);
  }
  inline void set_console (bool bConsole) {
    if (writer) writer->set_console (bConsole);
    if (reader) reader->set_console (bConsole);
  }

  inline void update () {
    if (writer) writer->update ();
    if (reader) reader->update ();
  }

  static void init_all ();
  static void update_all ();
};

class MessageTask : public Task {
public:
  uint8_t * m_buffer;
  uint8_t * m_ptr;

  int m_length; // encoded buffer length may be > 255, i.e., MESSAGE_BUFSIZE

  Message::MessageType m_type;

  bool m_bCopyBuffer;

  MessageTask (uint8_t address_src, uint8_t address_dest, Message::MessageType type, uint8_t * buffer, int length, bool bCopyBuffer = true);

  ~MessageTask ();

  virtual bool update (Writer & W);
};

class PGMListTask : public Task {
public:
  Message message;

  const char ** pgm_str_ptr;

  PGMListTask (uint8_t address_src, uint8_t address_dest, const char ** list) :
    Task(Task::p_Low, address_src, address_dest),
    message(address_src, address_dest, Message::Text_Response),
    pgm_str_ptr(list)
  {
    // ...
  }

  ~PGMListTask () {
    // ...
  }

  virtual bool update (Writer & W);
};

class Network {
private:
  MessageHandler * m_handler;

  uint8_t m_ports[64];

public:
  Network ();

  ~Network () {
    // 
  }

  inline void set_handler (MessageHandler * handler) {
    m_handler = handler;
  }

  int get_channel (uint8_t address) const; // returns channel number (0-6), or -1 if none set, for address (1-126)

  void set_channel (uint8_t address, uint8_t channel); // returns channel number (0-6) for address (1-126)

  void message_received (uint8_t channel_number, Message & message);

  static Network & network ();
};

#endif /* !ArduinoHello_comms_hh */
