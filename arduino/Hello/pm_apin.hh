/* Copyright 2017 Francis James Franklin
 * 
 * Open Source under the MIT License - see LICENSE in the project's root folder
 */

/* Included directly by PinManager.cpp
 */

class APin {
public:
  unsigned int m_flags;

  APin (unsigned int flags) :
    m_flags(flags)
  {
    // ...
  }

  ~APin () {
    // ...
  }

  void status (int pin_no) const {
    String state("A-Pin A");
    state = (state + pin_no) + " -";

    Serial.println (state);
  }
};
