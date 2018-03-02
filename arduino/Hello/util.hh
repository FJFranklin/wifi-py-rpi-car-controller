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

/* I/O handling & nput parsing
 */
extern void io_setup (); // call from main setup() function
extern void io_check (); // check for input, and handle as necessary; update output streams also

extern void input_reset (); // reset the input buffer

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
  char m_buffer[MESSAGE_MAXSIZE+1]; // i.e., 251

  char * m_args[INPUT_MAXARGS]; // i.e., 32

  uint8_t m_count;

public:
  ArgList (const char * buffer, uint8_t size);

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

/* Set callback functions for user command & interrupt
 */
extern void set_user_interrupt (void (*user_interrupt) ());
extern void set_user_command (CommandStatus (*user_command) (Message & response, const ArgList & Args));

#endif /* !ArduinoHello_util_hh */

