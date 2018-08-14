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

#include "pyccar.hh"
#include "Window.hh"

using namespace PyCCar;

static unsigned s_id_counter = 0;

static inline unsigned s_id_next () {
  return ++s_id_counter;
}

static bool s_set_bbox (unsigned win_id, int x, int y, unsigned width, unsigned height) {
  bool bOkay = false;

  PyObject * value = Py_BuildValue ("iiII", x, y, width, height);
  if (value) {
    bOkay = ui_win_set_property (win_id, "bbox", value);
    Py_DECREF (value);
  }
  return bOkay;
}

static bool s_set_flags (unsigned win_id, unsigned flags) {
  bool bOkay = false;

  PyObject * value = Py_BuildValue ("I", flags);
  if (value) {
    bOkay = ui_win_set_property (win_id, "flags", value);
    Py_DECREF (value);
  }
  return bOkay;
}

static Window * s_root = 0;

Window & Window::root () {
  return *s_root;
}

bool Window::set_flags (unsigned flags) {
  s_set_flags (m_id, flags);
}

Window::Window (unsigned width, unsigned height) :
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
  m_bVisible(true),
  m_bTouchable(true)
{
  PyCCarUI(m_id).set_bbox (m_id, m_abs_x, m_abs_y, m_W, m_H);

  /* Settings for root window
   */
  PyCCarUI(m_id).set_flags (PyCCar_VISIBLE | PyCCar_BLANK);
}

Window::Window (Window & parent, int rel_x, int rel_y, unsigned width, unsigned height) :
  m_parent(&parent),
  m_child_bottom(0),
  m_child_top(0),
  m_sibling_lower(0),
  m_sibling_upper(0),
  m_abs_x(parent.m_abs_x + rel_x),
  m_abs_y(parent.m_abs_y + rel_y),
  m_rel_x(rel_x),
  m_rel_y(rel_y),
  m_W(width),
  m_H(height),
  m_id(s_id_next ()),
  m_bDirty(true),
  m_bVisible(false),
  m_bTouchable(false)
{
  parent.add_child (this);

  PyCCarUI(m_id).set_bbox (m_id, m_abs_x, m_abs_y, m_W, m_H);
}

Window::~Window () {
  // ...
}

bool Window::init (unsigned width, unsigned height) {
  if (!s_root && width && height) {
    try {
      s_root = new Window(width, height);
    } catch (...) {
      s_root = 0;
    }
  }
  return s_root;
}

void Window::add_child (Window * child) {
  if (m_child_top) {
    child->m_sibling_lower = m_child_top;
    child->m_sibling_upper = 0;
    m_child_top->m_sibling_upper = child;
    m_child_top    = child;
  } else {
    child->m_sibling_lower = 0;
    child->m_sibling_upper = 0;
    m_child_bottom = child;
    m_child_top    = child;
  }
}

bool Window::coord_in_bounds (int x, int y) {
  if ((x < m_abs_x) || (y < m_abs_y)) {
    return false;
  }
  if ((x >= m_abs_x + m_W) || (y >= m_abs_y + m_H)) {
    return false;
  }
  return true;
}

bool Window::handle_touch (TouchInput::TouchEvent te, int rel_x, int rel_y) {
  return true; // catch & ignore...
}

bool Window::touch_event (TouchInput::TouchEvent te, const struct TouchInput::touch_event_data & event_data) {
#if 1
  switch (te) {
  case TouchInput::te_None:
    break;
  case TouchInput::te_Begin:
    {
      fprintf (stderr, "begin:  %d, %d\n", event_data.t1.x, event_data.t1.y);
      break;
    }
  case TouchInput::te_Change:
    {
      fprintf (stderr, "change: %d, %d\n", event_data.t1.x, event_data.t1.y);
      break;
    }
  case TouchInput::te_End:
    {
      fprintf (stderr, "end:    %d, %d\n", event_data.t1.x, event_data.t1.y);
      break;
    }
  }
#endif
  bool bHandled = false;

  int x = event_data.t1.x;
  int y = event_data.t1.y;

  /* Check children first, top to bottom
   */
  Window * child = m_child_top;

  while (child && !bHandled) {
    if (child->visible ()) {
      if (child->coord_in_bounds (x, y)) {
	bHandled = child->touch_event (te, event_data);
      }
    }
    child = child->m_sibling_lower;
  }

  /* If not handled by a child, handle it ourselves
   */
  if (!bHandled && m_bTouchable) {
    bHandled = handle_touch (te, x - m_abs_x, y - m_abs_y);
  }

  return bHandled;
}

void Window::redraw () {
  /* Draw self first
   */
  ui_win_draw (m_id);
  set_dirty (false);

  /* Draw children, bottom to top
   */
  Window * child = m_child_bottom;

  while (child) {
    if (child->visible ()) {
      child->redraw ();
    }
    child = child->m_sibling_upper;
  }
}
