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

#include "TouchInput.hh"
#include "Timer.hh"
#include "Window.hh"

class TouchTimer : public Timer {
private:
  TouchInput * m_TI;

  unsigned long m_interval;
  unsigned long m_lasttime;

public:
  TouchTimer (TouchInput * input, unsigned long interval) :
    m_TI(input),
    m_interval(interval),
    m_lasttime(0)
  {
    // ...
  }

  virtual ~TouchTimer () {
    // ...
  }

  virtual void tick (unsigned long time) {
    m_TI->tick ();
    
    if (time - m_lasttime > m_interval) {
      m_lasttime += m_interval;

      // TODO: move to WindowManager::update()
      int x, y;
      switch (m_TI->next (x, y)) {
      case TouchInput::te_None:
	break;
      case TouchInput::te_Begin:
	{
	  fprintf (stderr, "begin:  %d, %d\n", x, y);
	  break;
	}
      case TouchInput::te_Change:
	{
	  fprintf (stderr, "change: %d, %d\n", x, y);
	  break;
	}
      case TouchInput::te_End:
	{
	  fprintf (stderr, "end:    %d, %d\n", x, y);
	  break;
	}
      }
    }

    if (time > 30000) {
      stop ();
    }
  }
};
