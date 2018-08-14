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

/*! \file TouchInput.cc
    \brief Manage a Linux event stream for a touchscreen
    
    Developed for use with a HyperPixel 4.0 touchscreen used in console mode.
*/

#include "pyccar.hh"

#include <cstdio>

#include <time.h>
#include <fcntl.h>
#include <unistd.h>

#include <linux/input.h>

#include "TouchInput.hh"

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

using namespace PyCCar;

void TouchInput::run (Handler & handler, unsigned long interval) {
  if (m_timer_active) { // already active; just return
    return;
  }

  unsigned long last_milli = timer_millis ();
  unsigned long last_event = last_milli;

  m_timer_active = true;

  while (m_timer_active) {
    unsigned long time = timer_millis ();  // just call this the once

    if (last_milli < time) { // time is in milliseconds
      last_milli = time;     // note current time
      tick ();
    }
    if (interval) {
      if (last_event + interval <= time) {
	last_event += interval;
	event_process (handler);
      }
    }
    usleep (1);
  }
}

TouchInput::TouchInput (bool rescale) :
  m_te(te_None),
  m_devfd(-1),
  m_rescale(rescale),
  m_touch_new(false),
  m_touch_end(false),
  m_touch_yes(false),
  m_timer_active(false),
  ev_count(0)
{
  m_touch.t1.x = 0;
  m_touch.t1.y = 0;
  m_touch.t2.x = 0;
  m_touch.t2.y = 0;
}

TouchInput::~TouchInput () {
  if (m_devfd >= 0) {
    close (m_devfd);
  }
}

bool TouchInput::init (const char * device) {
  if (m_devfd < 0) {
    m_devfd = open (device, O_RDONLY | O_NONBLOCK /* O_NDELAY */);
    if (m_devfd == -1) {
      fprintf (stderr, "Failed to open \"%s\" - exiting.\n", device);
      return false;
    }

    unsigned char byte;

    while (read (m_devfd, &byte, 1) > 0) {
      // empty the input buffer
    }
  }
  return (m_devfd >= 0);
}

void TouchInput::handle (const struct input_event * event) {
  if (event->type == EV_SYN) {
    if (m_touch_new) {
      m_touch_new = false;
      m_touch_yes = true;
      touch_event_begin ();
    } else if (m_touch_end) {
      m_touch_end = false;
      m_touch_yes = false;
      touch_event_end ();
    } else if (m_touch_yes) {
      touch_event_change ();
    }
  }
  if (event->type == EV_ABS) {
    switch (event->code) {
    case 0:
      {
	if (m_rescale)
	  m_touch.t1.x = event->value * 5 / 3;
	else
	  m_touch.t1.x = event->value;
	break;
      }
    case 1:
      {
	if (m_rescale)
	  m_touch.t1.y = event->value * 3 / 5;
	else
	  m_touch.t1.y = event->value;
	break;
      }
    case 53:
      {
	if (m_rescale)
	  m_touch.t2.x = event->value * 5 / 3;
	else
	  m_touch.t2.x = event->value;
	break;
      }
    case 54:
      {
	if (m_rescale)
	  m_touch.t2.y = event->value * 3 / 5;
	else
	  m_touch.t2.y = event->value;
	break;
      }
    case 57:
      {
	if (event->value == -1) {
	  if (m_touch_yes)
	    m_touch_end = true;
	} else {
	  if (!m_touch_yes)
	    m_touch_new = true;
	}
	break;
      }
    default:
      break;
    }
  }
}

void TouchInput::tick () {
  if (m_devfd < 0) {
    return;
  }
  struct input_event * ev = reinterpret_cast<struct input_event *>(ev_buffer);

  int bytes_read = read (m_devfd, ev_buffer + ev_count, TouchInput_BUFSIZE - ev_count);
  if (bytes_read > 0) {
    ev_count += bytes_read;

    int count = ev_count / sizeof (struct input_event);

    for (int c = 0; c < count; c++) {
      handle (ev + c);
      ev_count -= sizeof (struct input_event);
    }
    if (ev_count) {
      ev[0] = ev[count];
    }
  }
}
