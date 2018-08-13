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

/*! \file InputTouch.hh
    \brief Manage a Linux event stream for a touchscreen
    
    Intended for use with a HyperPixel 4.0 touchscreen used in console mode.
*/

#ifndef __TouchInput_hh__
#define __TouchInput_hh__

#include <fcntl.h>
#include <unistd.h>

#include <linux/input.h>

class TouchInput {
public:
  enum TouchEvent {
    te_None = 0,
    te_Begin,
    te_Change,
    te_End
  } m_te;

private:
  const char * m_device_name;

  int m_devfd;

  int m_touch_x1;
  int m_touch_y1;
  int m_touch_x2;
  int m_touch_y2;

  bool m_rescale;

  bool m_touch_new;
  bool m_touch_end;
  bool m_touch_yes;

  unsigned long ev_length;
  unsigned long ev_count;

  struct input_event ev[64];

public:
  TouchInput (const char * device, bool rescale = false) :
    m_te(te_None),
    m_device_name(device),
    m_devfd(-1),
    m_touch_x1(0),
    m_touch_y1(0),
    m_touch_x2(0),
    m_touch_y2(0),
    m_rescale(rescale),
    m_touch_new(false),
    m_touch_end(false),
    m_touch_yes(false),
    ev_length(sizeof(ev)),
    ev_count(0)
  {
    // ...
  }

  ~TouchInput () {
    if (m_devfd >= 0) {
      close (m_devfd);
    }
  }

  bool init () {
    if (m_devfd < 0) {
      m_devfd = open (m_device_name, O_RDONLY | O_NONBLOCK /* O_NDELAY */);
      if (m_devfd == -1) {
	fprintf (stderr, "Failed to open \"%s\" - exiting.\n", m_device_name);
	return false;
      }

      unsigned char byte;

      while (read (m_devfd, &byte, 1) > 0) {
	// empty the input buffer
      }
    }
    return (m_devfd >= 0);
  }

private:
  void touch_event_begin () {
    if (m_te == te_End)
      m_te = te_Change;
    else
      m_te = te_Begin;
  }

  void touch_event_end () {
    if (m_te == te_End)
      m_te = te_Change;
    else
      m_te = te_End;
  }

  void touch_event_change () {
    if (m_te == te_None)
      m_te = te_Change;
  }

  void handle (const struct input_event * event) {
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
	    m_touch_x1 = event->value * 5 / 3;
	  else
	    m_touch_x1 = event->value;
	  break;
	}
      case 1:
	{
	  if (m_rescale)
	    m_touch_y1 = event->value * 3 / 5;
	  else
	    m_touch_y1 = event->value;
	  break;
	}
      case 53:
	{
	  if (m_rescale)
	    m_touch_x2 = event->value * 5 / 3;
	  else
	    m_touch_x2 = event->value;
	  break;
	}
      case 54:
	{
	  if (m_rescale)
	    m_touch_y2 = event->value * 3 / 5;
	  else
	    m_touch_y2 = event->value;
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

public:
  TouchEvent next (int & x, int & y) {
    TouchEvent te = m_te;
    m_te = te_None;

    x = m_touch_x1;
    y = m_touch_y1;

    return te;
  }

  void touch2 (int & x, int & y) const {
    x = m_touch_x2;
    y = m_touch_y2;
  }

  void tick () {
    if (m_devfd < 0) {
      return;
    }
    unsigned char * ptr = reinterpret_cast<unsigned char *>(ev);

    int bytes_read = read (m_devfd, ptr + ev_count, ev_length - ev_count);
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
};

#endif /* ! __TouchInput_hh__ */
