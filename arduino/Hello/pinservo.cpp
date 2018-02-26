/* Copyright 2017 Francis James Franklin
 * 
 * Open Source under the MIT License - see LICENSE in the project's root folder
 */

#include "util.hh"
#include "pinservo.hh"

static const char s_usage_minmax[] PROGMEM = "servo <pin#2-13> minmax <min.us [544]> <max.us [2400]>";
static const char s_usage_angle[] PROGMEM  = "servo <pin#2-13> angle <0-180 [90]>";
static const char s_usage_us[] PROGMEM     = "servo <pin#2-13> microseconds <microseconds>";
static const char s_usage_on[] PROGMEM     = "servo <pin#2-13> on";
static const char s_usage_off[] PROGMEM    = "servo <pin#2-13> off";

static const char s_servo_re_minmax[] PROGMEM = "servo: minmax values out of range (500 <= min < max <= 2500)";
static const char s_servo_re_angle[] PROGMEM  = "servo: angle value out of range (0 <= value <= 180)";
static const char s_servo_re_us[] PROGMEM     = "servo: microseconds value out of range (10 <= value < 10000)";

void PinServo::help (uint8_t address_src) {
  Message::pgm_message(s_usage_minmax).send (address_src);
  Message::pgm_message(s_usage_angle).send (address_src);
  Message::pgm_message(s_usage_us).send (address_src);
  Message::pgm_message(s_usage_on).send (address_src);
  Message::pgm_message(s_usage_off).send (address_src);
}

PinServo::PinServo (int pin_no) :
  m_pin_no(pin_no),
  m_us_min(544),
  m_us_max(2400),
  m_bAngle(true)
{
  m_value.angle = 90;
  // ...
}

PinServo::~PinServo () {
  off ();
}

void PinServo::on () {
  if (!m_servo.attached ())
    m_servo.attach (m_pin_no, m_us_min, m_us_max);
  if (m_bAngle)
    m_servo.write (m_value.angle);
  else
    m_servo.writeMicroseconds (m_value.exact);
}

void PinServo::off () {
  if (m_servo.attached ())
    m_servo.detach ();
}

void PinServo::set_min_max_microseconds (int us_min, int us_max) {
  m_us_min = us_min;
  m_us_max = us_max;

  if (m_servo.attached ()) {
    off ();
    on ();
  }
}

void PinServo::set_angle (int angle) {
  m_bAngle = true;
  m_value.angle = angle;
  if (m_servo.attached ())
    m_servo.write (angle);
}

void PinServo::set_exact (int exact) {
  m_bAngle = false;
  m_value.exact = exact;
  if (m_servo.attached ())
    m_servo.writeMicroseconds (exact);
}

CommandStatus PinServo::command (uint8_t address_src, int argc, char ** argv) {
  /* To get here, the first word in the argv array is "servo"; the second is the pin number.
   * There must be a third, the sub-command (with optional parameters) handled here.
   */
  CommandStatus cs = cs_Okay;

  String third(argv[2]);

  if (third == "minmax") { // add some limits for safety & sanity
    if (argc == 5) {
      String us_min(argv[3]);
      String us_max(argv[4]);
      int d_min = us_min.toInt ();
      int d_max = us_max.toInt ();

      if ((d_min >= 500) && (d_min < d_max) && (d_max <= 2500)) {
	set_min_max_microseconds (d_min, d_max);
      } else {
	Message response(Message::Text_Error);
	response.append_pgm (s_servo_re_minmax);
	response.send (address_src); // "servo: minmax values out of range (500 <= min < max <= 2500)";
	cs = cs_IncorrectUsage;
      }
    } else {
      Message response(Message::Text_Error);
      response.append_pgm (s_usage_minmax);
      response.send (address_src); // "usage 1: servo <pin#2-13> minmax <min.us [544]> <max.us [2400]>";
      cs = cs_IncorrectUsage;
    }
  } else if (third == "angle") { // must be 0-180
    if (argc == 4) {
      String angle(argv[3]);
      int d_angle = angle.toInt ();

      if ((d_angle >= 0) && (d_angle <= 180)) {
	set_angle (d_angle);
      } else {
	Message response(Message::Text_Error);
	response.append_pgm (s_servo_re_angle);
	response.send (address_src); // "servo: angle value out of range (0 <= value <= 180)";
	cs = cs_IncorrectUsage;
      }
    } else {
      Message response(Message::Text_Error);
      response.append_pgm (s_usage_angle);
      response.send (address_src); // "usage 2: servo <pin#2-13> angle <0-180 [90]>";
      cs = cs_IncorrectUsage;
    }
  } else if (third == "microseconds") { // add some limits for safety & sanity
    if (argc == 4) {
      String exact(argv[3]);
      int d_exact = exact.toInt ();

      if ((d_exact >= 10) && (d_exact < 10000)) {
	set_exact (d_exact);
      } else {
	Message response(Message::Text_Error);
	response.append_pgm (s_servo_re_us);
	response.send (address_src); // "servo: microseconds value out of range (10 <= value < 10000)";
	cs = cs_IncorrectUsage;
      }
    } else {
      Message response(Message::Text_Error);
      response.append_pgm (s_usage_us);
      response.send (address_src); // "usage 3: servo <pin#2-13> microseconds <microseconds>";
      cs = cs_IncorrectUsage;
    }
  } else if (third == "on") {
    on ();
  } else if (third == "off") {
    off ();
  } else {
    // unexpected sub-command
    cs = cs_IncorrectUsage;
  }

  return cs;
}

