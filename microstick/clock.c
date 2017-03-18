/*
 * File:   clock.c
 * Author: Francis James Franklin <fjf@alinameridon.com>
 *
 * Created on 11 March 2017
 */

#include "car/clock.h"
#include "car/command.h"

static car_time_t Time;
static char clock_string[6];

static uint8_t  ei0_flags = 0;
static uint16_t ei0_count = 0;

#define EI_1S     0x01  // count ext.int.0 for 1 s
#define EI_0_8MS  0x08  // count ext.int.0 for 0.8 ms
#define EI_20MS   0x20  // count ext.int.0 for 20 ms
#define EI_NOTIFY 0x40  // ping-notify on external interrupt 0

uint8_t car_clock_flags = 0;

const char * car_clock_string () {
  clock_string[0] = '0' + Time.clock.minutes / 10;
  clock_string[1] = '0' + Time.clock.minutes % 10;
  clock_string[2] = ':';
  clock_string[3] = '0' + Time.clock.seconds / 10;
  clock_string[4] = '0' + Time.clock.seconds % 10;
  clock_string[5] = 0;

  return clock_string;
}

void car_clock_init () {
  Time.clock.minutes = 0;
  Time.clock.seconds = 0;
  Time.clock.tenths  = 0;

  Time.timer.ticks = 0;
  Time.timer.t20ms = 0;

  T1CON = 0x0000; // Timer 1 disabled

  IPC0bits.T1IP = 0x01;  // priority
  IFS0bits.T1IF = false; // flag
  IEC0bits.T1IE = true;  // priority

  TMR1  = 0x0000;
  PR1   = 0x7BCA; // 31690 -> 0.8ms [31691(-1=0x7BCA)]
  T1CON = 0x8000; // Timer 1 enabled w/o prescaling, using internal oscillator
}

void car_clock_set_minutes (uint8_t minutes) {
  if (minutes < 60) {
    Time.clock.minutes = minutes;
  }
}

void car_clock_set_seconds (uint8_t seconds) {
  if (seconds < 60) {
    Time.clock.seconds = seconds;
  }
}

/* return value is approximate (0-802) number of microseconds into current tick
 */
uint16_t car_clock (car_time_t * T) {
  if (T) {
    *T = Time;
  }
  return (TMR1 << 1) / 79;
}

void __attribute__((__interrupt__, no_auto_psv)) _T1Interrupt (void) {
  car_clock_flags |= CAR_CLOCK_TICK;

  if (ei0_flags == EI_0_8MS) {
    ei0_flags = 0;
    IEC0bits.INT0IE = false;
  }

  if (++Time.timer.ticks == 25) {
    Time.timer.ticks = 0;
    car_clock_flags |= CAR_CLOCK_20MS;

    if (ei0_flags == EI_20MS) {
      ei0_flags = 0;
      IEC0bits.INT0IE = false;
    }

    if (++Time.timer.t20ms == 5) {
      Time.timer.t20ms = 0;
      car_clock_flags |= CAR_CLOCK_100MS;

      if (++Time.clock.tenths == 10) {
	Time.clock.tenths = 0;
	car_clock_flags |= CAR_CLOCK_SECOND;

	if (ei0_flags == EI_1S) {
	  ei0_flags = 0;
	  IEC0bits.INT0IE = false;
	}

	if (++Time.clock.seconds == 60) {
	  Time.clock.seconds = 0;
	  car_clock_flags |= CAR_CLOCK_MINUTE;

	  if (++Time.clock.minutes == 60) {
	    Time.clock.minutes = 0;
	    car_clock_flags |= CAR_CLOCK_HOUR;
	  }
	}
      }
    }
  }

  IFS0bits.T1IF = false;
}

void car_clock_ei0_off () {
  IEC0bits.INT0IE = false;
  IFS0bits.INT0IF = false;

  ei0_flags = 0;
}

void car_clock_ei0_count (uint8_t duration_code) { // code = 0x01 (1 second), 0x08 (0.8 ms), 0x20 (20 ms)
  IEC0bits.INT0IE = false;
  IFS0bits.INT0IF = false;

  INTCON2bits.INT0EP = false; // interrupt on positive edge

  ei0_flags = duration_code;
  ei0_count = 0;

  IEC0bits.INT0IE = true;
}

void car_clock_ei0_notify () {
  IEC0bits.INT0IE = false;
  IFS0bits.INT0IF = false;

  INTCON2bits.INT0EP = false; // interrupt on positive edge

  ei0_flags = EI_NOTIFY;

  IEC0bits.INT0IE = true;
}

void __attribute__((__interrupt__, no_auto_psv)) _INT0Interrupt (void) {
  if (ei0_flags == EI_NOTIFY) {
    car_command_flags |= CAR_COMMAND_PING;
  } else {
    ++ei0_count;
  }

  IFS0bits.INT0IF = false;
}
