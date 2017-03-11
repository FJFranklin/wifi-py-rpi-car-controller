/*
 * File:   clock.c
 * Author: Francis James Franklin <fjf@alinameridon.com>
 *
 * Created on 11 March 2017
 */

#include "car/clock.h"

static car_time_t Time;
static char clock_string[6];

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

  if (++Time.timer.ticks == 25) {
    Time.timer.ticks = 0;
    car_clock_flags |= CAR_CLOCK_20MS;

    if (++Time.timer.t20ms == 5) {
      Time.timer.t20ms = 0;
      car_clock_flags |= CAR_CLOCK_100MS;

      if (++Time.clock.tenths == 10) {
	Time.clock.tenths = 0;
	car_clock_flags |= CAR_CLOCK_SECOND;

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
