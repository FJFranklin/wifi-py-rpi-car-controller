/* Copyright 2017 Francis James Franklin
 * 
 * Open Source under the MIT License - see LICENSE in the project's root folder
 */

/* Included directly by PinManager.cpp
 */

#define DPIN_D_CLR  (1<<0) // digital clear allowed
#define DPIN_D_IN   (1<<1) // digital in allowed
#define DPIN_D_OUT  (1<<2) // digital out allowed
#define DPIN_SERVO  (1<<3) // servo allowed
#define DPIN_PWM    (1<<4) // PWM allowed
#define DPIN_PWMON  (1<<5) // PWM is active
#define DPIN_PULLUP (1<<6) // digital in with pull-up
#define DPIN_NOTIFY (1<<7) // flag for notification

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

  void set_notification (bool bNotify = true) {
    if (bNotify)
      m_flags |= DPIN_NOTIFY;
    else
      m_flags &= ~DPIN_NOTIFY;
  }

  bool notification () { // return notification flag state, & reset state to false
    bool bNotify = m_flags & DPIN_NOTIFY;
    m_flags &= ~DPIN_NOTIFY;
    return bNotify;
  }

  String status () const {
    String state("D-Pin ");

    state = (state + m_pin_no) + " ";

    if (m_type == pt_None) {
      state += "-";
    } else if (m_type == pt_Servo) {
      state += "servo";
    } else if (m_type == pt_D_In) {
      state += "digital in";
      if (m_flags & DPIN_PULLUP)
	state += " (up)";
    } else if (m_type == pt_D_Out) {
      state += "digital out";
    } else if (m_type == pt_PWM) {
      state += "PWM";
      if (m_flags & DPIN_PWMON)
	state += " (active)";
    }

    return state;
  }

  void clear () {
    if (m_type == pt_Servo) {
      delete m_data.servo;
    } else if (m_type == pt_D_In) {
      m_flags &= ~DPIN_PULLUP;
    } else if (m_type == pt_D_Out) {
      // ...
    } else if (m_type == pt_PWM) {
      m_flags &= ~DPIN_PWMON;
    }
    pinMode (m_pin_no, INPUT);
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

  void dpin_input (bool bPullUp = false) {
    if (m_type != pt_D_In) {
      clear ();

      if (bPullUp) {
	pinMode (m_pin_no, INPUT_PULLUP);
	m_flags |= DPIN_PULLUP;
      }
      m_type = pt_D_In;
    } else if (bPullUp && ((m_flags & DPIN_PULLUP) == 0)) { // need to change
      pinMode (m_pin_no, INPUT_PULLUP);
      m_flags |= DPIN_PULLUP;
    } else if (!bPullUp && (m_flags & DPIN_PULLUP)) { // need to change
      pinMode (m_pin_no, INPUT);
      m_flags &= ~DPIN_PULLUP;
    }
    if (digitalRead (m_pin_no) == HIGH)
      m_data.digital_value = true;
    else
      m_data.digital_value = false;
  }

  bool dpin_read () {
    if (m_type != pt_D_In)
      dpin_input ();

    if (digitalRead (m_pin_no) == HIGH)
      m_data.digital_value = true;
    else
      m_data.digital_value = false;

    return m_data.digital_value;
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

