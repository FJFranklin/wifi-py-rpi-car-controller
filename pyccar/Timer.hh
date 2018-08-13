/* Copyright (c) 2018 Francis James Franklin
 * 
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without modification, are permitted provided
 * that the following conditions are met:
 * 
 * 1. Redistributions of source code must retain the above copyright notice, this list of conditions and
 *    the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and
 *    the following disclaimer in the documentation and/or other materials provided with the distribution.
 * 3. The name of the author may not be used to endorse or promote products derived from this software
 *    without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT
 * NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 * DISCLAIMED.  IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
 * EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
 * LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
 * ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

#ifndef __Timer_hh__
#define __Timer_hh__

#include <time.h>
#include <unistd.h>

static unsigned long bInit = false;

static unsigned long time_secs;
static unsigned long time_nano;

static unsigned long timer_millis () {
  unsigned long us = 0;

  struct timespec ts;
  clock_gettime (CLOCK_MONOTONIC, &ts);
  unsigned long new_time_secs = (unsigned long) ts.tv_sec;
  unsigned long new_time_nano = (unsigned long) ts.tv_nsec;

  if (!bInit) {
    time_secs = new_time_secs;
    time_nano = new_time_nano;
    bInit = true;
  } else {
    if (new_time_nano < time_nano) {
      us  = (1000000000UL + new_time_nano - time_nano) / 1000000UL;
      us += 1000UL * (new_time_secs - time_secs - 1);
    } else {
      us  = (new_time_nano - time_nano) / 1000000UL;
      us += 1000UL * (new_time_secs - time_secs);
    }
  }
  return us;
}

class Timer {
private:
  bool bStop;

  unsigned long last_timer_check;

public:
  Timer () :
    bStop(false),
    last_timer_check(0)
  {
    // ...
  }

  virtual ~Timer () {
    // ...
  }

  virtual void tick (unsigned long time) {
    // ...
  }

  void run () {
    bStop = false;

    while (!bStop) {
      unsigned long time = timer_millis ();  // just call this the once

      if (last_timer_check < time) { // time is in milliseconds
	last_timer_check = time;     // note current time
	tick (time);
      }

      usleep (1);
    }
  }

  void stop () {
    bStop = true;
  }
};

#endif /* ! __Timer_hh__ */
