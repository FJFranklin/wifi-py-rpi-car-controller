/* Copyright 2017-18 Francis James Franklin
 * 
 * Open Source under the MIT License - see LICENSE in the project's root folder
 */

/* Included directly by PinManager.cpp
 */

#define APIN_ANALOG (1<<0)
#define APIN_NOTIFY (1<<7)

class APin {
public:
  /* Note: Analog pins can be used as digital pins (GPIO), with some caveats;
   *       for simplicity, this is not implemented here.
   */
  unsigned int m_flags;

  int m_pin_no;

  int m_data;

  APin (unsigned int flags, int pin_no) :
    m_flags(flags),
    m_pin_no(pin_no),
    m_data(0)
  {
    // ...
  }

  ~APin () {
    // ...
  }

  void set_notification (bool bNotify = true) {
    if (bNotify)
      m_flags |= APIN_NOTIFY;
    else
      m_flags &= ~APIN_NOTIFY;
  }

  bool notification () { // return notification flag state, & reset state to false
    bool bNotify = m_flags & APIN_NOTIFY;

    m_flags &= ~APIN_NOTIFY;

    return bNotify;
  }

  void status (Message & response) const {
    response = "A-Pin A";
    response.append_int (m_pin_no);
    response += " analog";

    response.send ();
  }

  int apin_read () {
    m_data = analogRead (m_pin_no);

    return m_data;
  }
};

