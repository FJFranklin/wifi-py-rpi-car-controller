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

#ifndef Car_Ticker_hh
#define Car_Ticker_hh

class Ticker {
public:
  class Sleeper {
  public:
    virtual void sleep() = 0;

    virtual ~Sleeper();
  };
private:
  Sleeper * m_S;

  bool m_bLoop;

  unsigned m_ms_count;

  unsigned long m_time_secs;
  unsigned long m_time_nano;

  void get_time(unsigned long & secs, unsigned long & nano);

protected:
  inline void set_sleeper(Sleeper * S) { m_S = S; }

public:
  Ticker() :
    m_S(0),
    m_bLoop(true),
    m_ms_count(999)
  {
    get_time(m_time_secs, m_time_nano);
  }
  virtual ~Ticker();

  unsigned long millis();

  inline void stop() {
    m_bLoop = false;
  }
  void loop();

  virtual void tick();
  virtual void second();
};

#endif /* ! Car_Ticker_hh */
