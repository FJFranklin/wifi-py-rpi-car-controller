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

class Window;

static unsigned s_id_counter = 0;
static unsigned s_id_next () {
  return ++s_id_counter;
}

static Window * s_root = 0;

class Window {
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
protected:
  bool m_bTouchable;
private:
  void add_child (Window * child) {
  }

  Window (unsigned width, unsigned height) :
    m_parent(0),
    m_child_bottom(0),
    m_child_top(0),
    m_sibling_lower(0),
    m_sibling_upper(0),
    m_abs_x(0),
    m_abs_y(0),
    m_rel_x(0),
    m_rel_y(0),
    m_W(width),
    m_H(height),
    m_id(0),
    m_bDirty(true),
    m_bTouchable(true)
  {
    // TODO: set root window properties
    // ui_window_bbox (m_id, m_abs_x, m_abs_y, m_W, m_H);
  }

protected:
  Window (Window & parent, int rel_x, int rel_y, unsigned width, unsigned height) :
    m_parent(&parent),
    m_child_bottom(0),
    m_child_top(0),
    m_sibling_lower(0),
    m_sibling_upper(0),
    m_abs_x(parent.abs_x + rel_x),
    m_abs_y(parent.abs_y + rel_y),
    m_rel_x(rel_x),
    m_rel_y(rel_y),
    m_W(width),
    m_H(height),
    m_id(s_id_next ()),
    m_bDirty(true),
    m_bTouchable(false)
  {
    parent->add_child (this);
    // TODO: set default window properties
    // ui_window_bbox (m_id, m_abs_x, m_abs_y, m_W, m_H);
  }

public:
  ~Window () {
    // ...
  }

  static Window & root () {
    return *s_root;
  }
  static Window * root (unsigned width, unsigned height) {
    if (!s_root && width && height) {
      try {
	s_root = new Window(width, height);
      } catch (...) {
	s_root = 0;
      }
    }
    return s_root;
  }

  inline unsigned id () const {
    return m_id;
  }

  inline void set_dirty (bool bDirty) {
    m_bDirty = bDirty;
  }
  inline bool dirty () const {
    return m_bDirty;
  }

  bool touch_in_bounds (int x, int y) {
    if ((x < m_abs_x) || (y < m_abs_y)) {
      return false;
    }
    if ((x >= m_abs_x + m_W) || (y >= m_abs_y + m_H)) {
      return false;
    }
    return true;
  }
protected:
  virtual void handle_touch (TouchInput::TouchEvent te, int rel_x, int rel_y) {
    // catch & ignore...
  }
public:
  void touch_event (TouchInput::TouchEvent te, int x, int y) {
    if (m_bTouchable) {
      handle_touch (te, x - m_abs_x, y - m_abs_y);
    } else {
      m_parent->touch_event (te, x, y); // propagate event to parent
    }
  }

  virtual void redraw () {
    // TODO: request redraw by window ID
    // ui_window_redraw (m_id);
    set_dirty (false);
  }
};

#endif /* ! __Window_hh__ */
