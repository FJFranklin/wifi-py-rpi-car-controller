/* Copyright 2018 Francis James Franklin
 * 
 * Open Source under the MIT License - see LICENSE in the project's root folder
 */

#ifndef ArduinoHello_comms_hh
#define ArduinoHello_comms_hh

#include <Arduino.h>

extern uint8_t local_address; // From EEPROM; valid device addresses are 1-127
extern uint8_t input_default; // address 0, reserved for direct input over Serial

class Writer;

extern Writer * Channel_0;
extern Writer * Channel_1;
extern Writer * Channel_2;
extern Writer * Channel_3;
extern Writer * Channel_4;
extern Writer * Channel_5;
extern Writer * Channel_6;

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

public:
  Writer () :
    next(0)
  {
    // ...
  }

  void update ();
private:
  void add (Task * task);
public:
  virtual int available () = 0;

  virtual int write (uint8_t * buffer, int length) = 0;

  virtual ~Writer () { }

  static void init_channels ();
  static void update_all ();
  static void add_task (Task * task);
};

class Message { // TODO: This needs a rewrite // FIXME
public:
  enum MessageType {
    Text_Command  = 0,
    Text_Response = 1,
    Text_Error    = 2
  } type;

  String text;

  Message (MessageType mt = Text_Response) :
    type(mt)
  {
    // ...
  }

  Message (const String & S) :
    type(Text_Response),
    text(S)
  {
    // ...
  }

  ~Message () {
    // ...
  }

  static Message pgm_message (const char * pgm); // create new message with string stored in PROGMEM

  void append_pgm (const char * pgm);            // append string stored in PROGMEM

  void send (uint8_t address = 0); // default address for Serial
};

class MessageTask : public Task {
public:
  uint8_t * m_buffer;
  uint8_t * m_ptr;

  uint8_t m_length;

  Message::MessageType m_type;

  bool m_bCopyBuffer;

  MessageTask (Message::MessageType type, uint8_t address_src, uint8_t address_dest, uint8_t * buffer, uint8_t length, bool bCopyBuffer = true);

  ~MessageTask ();

  virtual bool update (Writer & W);
};

#endif /* !ArduinoHello_comms_hh */
