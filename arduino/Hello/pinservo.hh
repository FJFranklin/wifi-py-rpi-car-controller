/* Copyright 2017 Francis James Franklin
 * 
 * Open Source under the MIT License - see LICENSE in the project's root folder
 */

#include <Arduino.h>
#include <Servo.h>

class PinServo {
private:
  Servo m_servo; // The Arduino Servo object

  int m_pin_no; // pins 2-13 on Arduino Uno
  int m_us_min; // servo signal goes high for at least <us_min> microseconds
  int m_us_max; // and for at most <us_max> microseconds
  union {
    int angle; // if set by angle
    int exact; // if set by duration in microseconds
  } m_value;
  bool m_bAngle; // true if set by angle; false if set exactly

public:
  static void help (uint8_t address_src);

  PinServo (int pin_no);

  ~PinServo ();

private:
  void on ();
  void off ();

  void set_min_max_microseconds (int us_min, int us_max);
  void set_angle (int angle);
  void set_exact (int exact);

public:
  /* Called by PinManager::command ()
   */
  CommandStatus command (uint8_t address_src, int argc, char ** argv);

  inline CommandStatus cmd_servo (bool bOn) {
    CommandStatus cs = cs_Okay;

    if (bOn)
      on ();
    else
      off ();

    return cs;
  }

  inline CommandStatus cmd_servo_angle (unsigned int angle) {
    CommandStatus cs = cs_IncorrectUsage;

    if ((angle >= 0) && (angle <= 180)) {
      set_angle (angle);
      cs = cs_Okay;
    }

    return cs;
  }

  inline CommandStatus cmd_servo_microseconds (unsigned int us) {
    CommandStatus cs = cs_IncorrectUsage;

    if ((us >= 10) && (us < 10000)) {
      set_exact (us);
      cs = cs_Okay;
    }

    return cs;
  }

  inline CommandStatus cmd_servo_minmax (unsigned int range_min, unsigned int range_max) {
    CommandStatus cs = cs_IncorrectUsage;

    if ((range_min >= 500) && (range_min < range_max) && (range_max <= 2500)) {
      set_min_max_microseconds (range_min, range_max);
      cs = cs_Okay;
    }

    return cs;
  }
};

