/* Copyright 2017-18 Francis James Franklin
 * 
 * Open Source under the MIT License - see LICENSE in the project's root folder
 */

#ifndef ArduinoHello_util_hh
#define ArduinoHello_util_hh

#include <Arduino.h>

#include "comms.hh"

/* Turn echo on/off
 */
extern void echo (bool bOn);

enum CommandStatus {
  cs_Okay = 0,
  cs_UnknownCommand,
  cs_IncorrectUsage,
  cs_InvalidPin
};

class Arg {
private:
  const char * m_arg;

public:
  Arg (const char * arg) :
    m_arg(arg)
  {
    // ...
  }

  ~Arg () {
    // ...
  }

  inline const char * c_str () const {
    return m_arg;
  }

  bool equals (const char * rhs, bool bCaseSensitive = true) const;

  inline bool operator! () const {
    return (m_arg == 0);
  }

  int toInt () const;
};

inline bool operator== (const Arg & lhs, const char * rhs) {
  return lhs.equals (rhs);
}

#define INPUT_MAXARGS 32 // an arbitrary choice; theoretically could be (MESSAGE_MAXSIZE/2)+1 = 126

class ArgList {
private:
  char * m_buffer;
  char * m_args[INPUT_MAXARGS]; // i.e., 32

  uint8_t m_count;

public:
  ArgList (Message & message);

  ~ArgList () {
    // ...
  }

  inline uint8_t count () const {
    return m_count;
  }

  inline Arg operator[] (uint8_t index) const {
    return (index < m_count) ? Arg(m_args[index]) : Arg(0);
  }
};

class Command : public MessageHandler {
private:
  Message m_response;

  CommandStatus (*m_user_command) (Message & response, const ArgList & Args);

  void (*m_user_interrupt) (Message & response);

public:
  Command () :
    m_response(0,0,Message::Text_Response), // to fix later
    m_user_command(0),
    m_user_interrupt(0)
  {
    // ...
  }

  ~Command () {
    // ...
  }

  /* Set callback functions for user command & interrupt
   */
  inline void set_user_command (CommandStatus (*user_command) (Message & response, const ArgList & Args)) {
    m_user_command = user_command;
  }
  inline void set_user_interrupt (void (*user_interrupt) (Message & response)) {
    m_user_interrupt = user_interrupt;
  }

  virtual void message_received (Message & message);

  static Command * command ();
};

#endif /* !ArduinoHello_util_hh */
