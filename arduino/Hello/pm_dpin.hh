/* Copyright 2017 Francis James Franklin
 * 
 * Open Source under the MIT License - see LICENSE in the project's root folder
 */

/* Included directly by PinManager.cpp
 */

#define DPIN_SERVO (1<<0) // servo allowed
#define DPIN_D_OUT (1<<1) // digital out allowed
#define DPIN_PWM   (1<<2) // PWM allowed
#define DPIN_PWMON (1<<3) // PWM is active

class DPin {
public:
  unsigned int m_flags; // can it be used for...?
  int m_pin_no;

  enum PinType {
    pt_None = 0,
    pt_Servo,
    pt_PWM,
    pt_D_In,
    pt_D_Out
  } m_type;

  union {
    PinServo * servo;
    unsigned char duty_cycle;
    bool digital_value;
  } m_data;

  DPin (unsigned int flags, int pin_no) :
    m_flags(flags),
    m_pin_no(pin_no),
    m_type(pt_None)
  {
    // ...
  }

  ~DPin () {
    clear ();
  }

  void status () const {
    String state("D-Pin ");
    state = (state + m_pin_no) + " ";
    if (m_type == pt_None)
      state += "-";
    else if (m_type == pt_Servo)
      state += "servo";
    else if (m_type == pt_D_Out)
      state += "digital out";
    else if (m_type == pt_PWM)
      state += "PWM";

    Serial.println (state);
  }

  void clear () {
    if (m_type == pt_Servo) {
      delete m_data.servo;
    } else if (m_type == pt_D_Out) {
      pinMode (m_pin_no, INPUT);
    } else if (m_type == pt_PWM) {
      pinMode (m_pin_no, INPUT);
      m_flags &= ~DPIN_PWMON;
    }
    m_type = pt_None;
  }

  PinServo * servo () {
    if (m_type != pt_Servo) {
      clear ();

      m_data.servo = new PinServo(m_pin_no);

      if (m_data.servo) // TODO: Check - how does the arduino handle memory errors?
	m_type = pt_Servo;
    }
    return m_data.servo;
  }

  void dpin_write (bool value) {
    if (m_type != pt_D_Out) {
      clear ();

      pinMode (m_pin_no, OUTPUT);
      m_type = pt_D_Out;
    }
    m_data.digital_value = value;

    if (value)
      digitalWrite (m_pin_no, HIGH);
    else
      digitalWrite (m_pin_no, LOW);
  }

  void pwm (bool bOn) {
    if (m_type != pt_PWM) {
      clear ();

      pinMode (m_pin_no, OUTPUT);
      m_type = pt_PWM;
      m_data.duty_cycle = 0; // duty cycle defaults to 0
    }
    if (bOn) {
      analogWrite (m_pin_no, m_data.duty_cycle);
      m_flags |= DPIN_PWMON;
    } else {
      analogWrite (m_pin_no, 0);
      m_flags &= ~DPIN_PWMON;
    }
  }

  void pwm_duty (unsigned char duty_cycle) {
    if (m_type != pt_PWM) {
      clear ();

      pinMode (m_pin_no, OUTPUT);
      m_type = pt_PWM;
    }
    m_data.duty_cycle = duty_cycle;

    if (m_flags & DPIN_PWMON) // if the PWM is currently active, then update
      analogWrite (m_pin_no, m_data.duty_cycle);
  }
};
