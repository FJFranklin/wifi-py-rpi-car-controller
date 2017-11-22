#include <Arduino.h>
#include <Servo.h>

class PinServo {
public:
  Servo m_servo; // The Arduino Servo object

  int m_pin_no; // pins 2-13 on Arduino Uno
  int m_us_min; // servo signal goes high for at least <us_min> microseconds
  int m_us_max; // and for at most <us_max> microseconds
  union {
    int angle; // if set by angle
    int exact; // if set by duration in microseconds
  } m_value;
  bool m_bAngle; // true if set by angle; false if set exactly

  static void help ();

  PinServo (int pin_no);

  ~PinServo ();

  void on ();
  void off ();

  void set_min_max_microseconds (int us_min, int us_max);
  void set_angle (int angle);
  void set_exact (int exact);

  /* Called by PinManager::command ()
   */
  bool command (int argc, char ** argv);
};
