/* Copyright 2017 Francis James Franklin
 * 
 * Open Source under the MIT License - see LICENSE in the project's root folder
 */

/* Included directly by PinManager.cpp
 */

#define APIN_ANALOG (1<<0)

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

  void status () const {
    String state("A-Pin A");

    state = (state + m_pin_no) + " analog";

    Serial.println (state);
  }

  int apin_read () {
    m_data = analogRead (m_pin_no);

    return m_data;
  }
};
