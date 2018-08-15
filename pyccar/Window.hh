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

#ifndef __Window_hh__
#define __Window_hh__

#include "pyccar.hh"
#include "TouchInput.hh"

namespace PyCCar {

  class Window : public TouchInput::Handler {
  private:
    Window * m_parent;

    Window * m_child_bottom;
    Window * m_child_top;
    Window * m_sibling_lower;
    Window * m_sibling_upper;

    int m_abs_x;
    int m_abs_y;
    int m_rel_x;
    int m_rel_y;

    unsigned m_W;
    unsigned m_H;

    unsigned m_id;

    bool m_bDirty;
    bool m_bVisible;
  protected:
    bool m_bTouchable;

  private:
    Window (unsigned width, unsigned height);

  protected:
    Window (Window & parent, int rel_x, int rel_y, unsigned width, unsigned height);

  public:
    virtual ~Window ();

    static Window & root ();

    static bool init (unsigned width, unsigned height);

    inline unsigned id () const {
      return m_id;
    }

    inline void set_dirty (bool bDirty) {
      m_bDirty = bDirty;
    }
    inline bool dirty () const {
      return m_bDirty;
    }

    inline void set_visible (bool bVisible) {
      if (id ())
	m_bVisible = bVisible;
    }
    inline bool visible () const {
      return m_bVisible;
    }

    bool coord_in_bounds (int x, int y);

    virtual TouchInput::Handler * touch_handler (const struct TouchInput::touch_event_data & event_data);

    virtual void touch_enter ();
    virtual void touch_leave ();
    virtual void touch_event (TouchInput::TouchEvent te, const struct TouchInput::touch_event_data & event_data);

    virtual void redraw ();

  private:
    void add_child (Window * child);
  };

  class Button : public Window {
  private:
    bool m_bEnabled;
    bool m_bActive;

  public:
    Button (Window & parent, int rel_x, int rel_y, unsigned width, unsigned height);

    virtual ~Button ();

    virtual void touch_enter ();
    virtual void touch_leave ();
    virtual void touch_event (TouchInput::TouchEvent te, const struct TouchInput::touch_event_data & event_data);
  };

} // namespace PyCCar

#endif /* ! __Window_hh__ */
