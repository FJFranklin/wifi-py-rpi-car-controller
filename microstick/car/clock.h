/*
 * File:   clock.h
 * Author: Francis James Franklin <fjf@alinameridon.com>
 *
 * Created on 11 March 2017
 */

#ifndef __CAR_CLOCK_H__
#define __CAR_CLOCK_H__

#include <stdint.h>
#include <stdbool.h>

#include <xc.h>

struct car_time_data {
  struct car_clock_data {
    uint16_t minutes : 6; // 0-60
    uint16_t seconds : 6; // 0-60
    uint16_t tenths  : 4; // tenths of seconds
  } clock;
  struct car_timer_data {
    uint8_t ticks : 5; // counts ticks: 0-24 (25 ticks is 20 ms)
    uint8_t t20ms : 3; // counts 20 ms: 0-4 (5 adding to 100 ms)
  } timer;
};
typedef struct car_time_data car_time_t;

extern void         car_clock_init ();
extern uint16_t     car_clock (car_time_t * T); // return value is number microseconds into current 0.8 ms (800 microseconds) tick
extern const char * car_clock_string ();        // returns current clock time in "MM:SS" format

/* The bits defined below are set by the clock timer, but never cleared.
 * The user may clear these, if wished.
 */
extern uint8_t car_clock_flags;

#define CAR_CLOCK_TICK    0x01  // 0.8 ms
#define CAR_CLOCK_20MS    0x02  // 20 ms
#define CAR_CLOCK_100MS   0x04  // 100 ms
#define CAR_CLOCK_SECOND  0x08  // 1 s
#define CAR_CLOCK_MINUTE  0x10  // 1 minute
#define CAR_CLOCK_HOUR    0x20  // 1 hour

/* Clear the flag, returning true if set *** Why doesn't this work? ***
 */
extern inline __attribute((always_inline)) bool car_clock_clear (uint8_t flag) {
  bool bSet = (car_clock_flags & flag) ? true : false;
  car_clock_flags &= ~flag;
  return bSet;
}

#endif /* !__CAR_CLOCK_H__ */
