/* Copyright (c) 2019 Francis James Franklin
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

#include <errno.h>
#include <time.h>
#include <unistd.h>

#include "Ticker.hh"

Ticker::Sleeper::~Sleeper() {
  // ...
}

Ticker::~Ticker() {
  // ...
}

void Ticker::get_time(unsigned long & secs, unsigned long & nano) {
  struct timespec ts;
  clock_gettime (CLOCK_MONOTONIC, &ts);
  secs = (unsigned long) ts.tv_sec;
  nano = (unsigned long) ts.tv_nsec;
}

unsigned long Ticker::millis () {
  unsigned long new_time_secs;
  unsigned long new_time_nano;
  get_time(new_time_secs, new_time_nano);

  unsigned long us = 0;

  if (new_time_nano < m_time_nano) {
    us  = (1000000000UL + new_time_nano - m_time_nano) / 1000000UL;
    us += 1000UL * (new_time_secs - m_time_secs - 1);
  } else {
    us  = (new_time_nano - m_time_nano) / 1000000UL;
    us += 1000UL * (new_time_secs - m_time_secs);
  }
  return us;
}

void Ticker::loop() {
  unsigned long ms0 = millis();

  m_bLoop = true;
  while (m_bLoop) {
    unsigned long ms1 = millis();

    if (ms0 != ms1) {
      ms0 = ms1;
      tick();
    }
    if (m_S) {
      m_S->sleep();
    } else {
      usleep(1);
    }
  }
}

void Ticker::tick() {
  if (++m_ms_count == 1000) {
    m_ms_count = 0;
    second();
  }
}

void Ticker::second() {
  // ...
}
