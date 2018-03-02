/* Copyright 2018 Francis James Franklin
 * 
 * Open Source under the MIT License - see LICENSE in the project's root folder
 */

#ifndef ArduinoHello_comms_hh
#define ArduinoHello_comms_hh

#include <Arduino.h>

#define MESSAGE_BUFSIZE  256
#define MESSAGE_MAXSIZE  (MESSAGE_BUFSIZE-6) // maximum message data length is therefore 250 characters
                                             // which must therefore be the maximum allowable path length

#define ENABLE_CHANNEL_0 // for Serial or, equivalently, SerialUSB
#define ENABLE_CHANNEL_1
#ifdef CORE_TEENSY
#define ENABLE_CHANNEL_2
#define ENABLE_CHANNEL_3
#define ENABLE_CHANNEL_4
// #define ENABLE_CHANNEL_5
// #define ENABLE_CHANNEL_6
#endif /* CORE_TEENSY */

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

extern Channel * Channel_0;
extern Channel * Channel_1;
extern Channel * Channel_2;
extern Channel * Channel_3;
extern Channel * Channel_4;
extern Channel * Channel_5;
extern Channel * Channel_6;

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

  bool m_bEncoded;
  bool m_bNewlines;

public:
  Writer () :
    next(0),
    m_bEncoded(false),
    m_bNewlines(true)
  {
    // ...
  }

  inline bool encoded () const {
    return m_bEncoded;
  }
  inline void set_encoded (bool bEncoded) {
    m_bEncoded = bEncoded;
  }
  inline bool newlines () const {
    return m_bNewlines;
  }
  inline void set_newlines (bool bNewlines) {
    m_bNewlines = bNewlines;
  }

  void update ();

  void add (Task * task);

  virtual int available () = 0;

  virtual int write (uint8_t * buffer, int length) = 0;

  virtual ~Writer () { }

  static void init_channels ();
  static void update_all ();

  static Writer * channel (uint8_t address);
};

class Reader {
public:
  inline void update () {
    // ...
  }
};

class Channel {
public:
  Writer * writer;
  Reader * reader;

  Channel (Writer * W) :
    writer(W),
    reader(0)
  {
    // ...
  }

  ~Channel () {
    // ...
  }

  inline void update () {
    if (writer) writer->update ();
    if (reader) reader->update ();
  }
};

class Message {
public:
  enum MessageType {
    Text_Command  = 0,
    Text_Response = 1,
    Text_Error    = 2
  };

  enum COBS_State {
    cobs_HavePacket = 0,
    cobs_InProgress,
    cobs_UnexpectedEOP,
    cobs_InvalidPacket,
    cobs_TooLong
  };

private:
  uint8_t buffer[MESSAGE_BUFSIZE];
  uint8_t offset;
  uint8_t cobsin;
public:
  inline void set_address_src (uint8_t address_src) {
    buffer[0] = address_src;
  }
  inline void set_address_dest (uint8_t address_dest) {
    buffer[1] = address_dest;
  }
  inline void set_type (MessageType type) {
    buffer[2] = (uint8_t) type;
  }
private:
  inline void set_length (uint8_t length) {
    buffer[3] = length;
  }
public:
  inline uint8_t get_address_src () const {
    return buffer[0];
  }
  inline uint8_t get_address_dest () const {
    return buffer[1];
  }
  inline MessageType get_type () const {
    return (MessageType) buffer[2];
  }
  inline uint8_t get_length () const {
    return buffer[3];
  }
private:
  inline uint8_t * get_buffer () {
    return buffer + 4;
  }
public:
  inline void clear () {
    offset = 0;
    cobsin = 0;
    set_length (0);
  }

  Message (uint8_t address_src, uint8_t address_dest, MessageType type = Text_Response) : 
    offset(0),
    cobsin(0)
  {
    set_address_src (address_src);
    set_address_dest (address_dest);
    set_type (type);
    set_length (0);
  }

  ~Message () {
    // ...
  }

  Message & operator+= (uint8_t uc);
  Message & operator+= (const char * right);
  Message & operator= (const char * right);

  Message & append_lu (unsigned long i); // change number to string, and append
  Message & append_int (int i);          // change number to string, and append
  Message & append_hex (uint8_t i);      // change number to string, and append
  Message & pgm (const char * str);      // append string stored in PROGMEM

  void send ();

  void encode (uint8_t *& bytes, int & size);

  COBS_State decode (uint8_t c);
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

#endif /* !ArduinoHello_comms_hh */
