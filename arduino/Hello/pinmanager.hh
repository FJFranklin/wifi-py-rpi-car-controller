/* Copyright 2017 Francis James Franklin
 * 
 * Open Source under the MIT License - see LICENSE in the project's root folder
 */

#include "util.hh"

class APin;
class DPin;

class PinManager {
private:
  APin * AP[6];
  DPin * DP[14];

  CommandStatus (*user_command) (String & first, int argc, char ** argv);

  PinManager ();

public:
  ~PinManager ();

  static PinManager * manager (); // PinManager is instantiated only once

  /* Allow PinManager to intercept and handle user's commands, and then forward any that are not recognised
   */  
  void input_callbacks (CommandStatus (*user_command_callback) (String & first, int argc, char ** argv), void (*user_interrupt_callback) ());

  /* call at the start of each loop iteration
   */
  void update (void (*notification_handler) (int pin_no, bool bDigital) = 0);

  CommandStatus command (int argc, char ** argv); // commands handled by PinManager

private:
  int parse_pin_no (const char * str, unsigned int flags, bool bDigital) const; // returns pin no if valid, otherwise -1

  void list (bool bAnalog, bool bDigital) const;

public:
  /* set digital pin <pin_no> to high (true, 1) or low (false, 0)
   */
  CommandStatus cmd_dout (int pin_no, bool value);

  /* read digital pin <pin_no> (0-1)
   */
  CommandStatus cmd_din (int pin_no, bool & bState);

  /* read analog pin A<pin_no> (0-1023)
   */
  CommandStatus cmd_ain (int pin_no, int & value);

  /* set digital pin <pin_no> to read with internal pull-up resistor
   */
  CommandStatus cmd_dup (int pin_no, bool bPullUp);

  /* deassociate & clear state of digital pin <pin_no>
   */
  CommandStatus cmd_dclr (int pin_no);

  /* turn LED (digital pin #13) on or off
   */
  inline CommandStatus cmd_led (bool bOn) {
    return cmd_dout (13, bOn);
  }

  /* use (digital) pin <pin_no> as PWM and turn on/off
   */
  CommandStatus cmd_pwm (int pin_no, bool bOn);

  /* set PWM duty cycle (0-255) for (digital) pin <pin_no>
   */
  CommandStatus cmd_pwm_duty (int pin_no, unsigned char duty_cycle);

  /* use (digital) pin <pin_no> as a servo controller and turn on/off
   */
  CommandStatus cmd_servo (int pin_no, bool bOn);

  /* set high/low range for servo on (digital) pin <pin_no>
   */
  CommandStatus cmd_servo_minmax (int pin_no, unsigned int range_min, unsigned int range_max);

  /* set angle (0-180) for servo on (digital) pin <pin_no>
   */
  CommandStatus cmd_servo_angle (int pin_no, unsigned int angle);

  /* set exact value for high for servo on (digital) pin <pin_no>
   */
  CommandStatus cmd_servo_microseconds (int pin_no, unsigned int microseconds);

};
