/* Copyright 2017-18 Francis James Franklin
 * 
 * Open Source under the MIT License - see LICENSE in the project's root folder
 */

#include "util.hh"

class SD_Manager {
  bool m_bLocked;

private:
  SD_Manager () :
    m_bLocked(false)
  {
    // ...
  }

public:
  static SD_Manager * manager ();

  ~SD_Manager () {
    // ...
  }

  CommandStatus command (uint8_t address_src, const String & first, int argc, char ** argv);

  bool lock () {
    if (m_bLocked) {
      return false;
    }
    m_bLocked = true;
    return true;
  }

  void unlock () {
    m_bLocked = false;
  }
};


