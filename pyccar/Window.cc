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

static Window * s_root = 0;

Window & Window::root () {
  return *s_root;
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
  m_flags(0),
  m_bDirty(true),
  m_bVisible(true),
  m_bTouchable(true)
{
  PyCCarUI(id ()).set_bbox (m_abs_x, m_abs_y, m_W, m_H);

  /* Settings for root window
   */
  m_flags = PyCCar_VISIBLE | PyCCar_BLANK;
  PyCCarUI(id ()).set_flags (m_flags);
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
  m_flags(0),
  m_bDirty(true),
  m_bVisible(false),
  m_bTouchable(false)
{
  parent.add_child (this);

  PyCCarUI(id ()).set_bbox (m_abs_x, m_abs_y, m_W, m_H);
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

void Window::set_visible (bool bVisible) {
  if (m_parent && (bVisible != visible ())) { // the root window is always visible
    if (bVisible) {
      m_flags |=  PyCCar_VISIBLE;
    } else {
      m_flags &= ~PyCCar_VISIBLE;
    }
    PyCCarUI(id ()).set_flags (m_flags);

    if (bVisible) {
      redraw ();
    } else {
      m_parent->redraw ();
    }
  }
}

bool Window::coord_in_bounds (int x, int y) {
  if ((x < m_abs_x) || (y < m_abs_y)) {
    return false;
  }
  if ((x >= m_abs_x + static_cast<int>(m_W)) || (y >= m_abs_y + static_cast<int>(m_H))) {
    return false;
  }
  return true;
}

TouchInput::Handler * Window::touch_handler (const struct TouchInput::touch_event_data & event_data) {
  TouchInput::Handler * handler = 0;

  /* Check children first, top to bottom
   */
  Window * child = m_child_top;

  while (child && !handler) {
    if (child->visible ()) {
      if (child->coord_in_bounds (event_data.t1.x, event_data.t1.y)) {
	handler = child->touch_handler (event_data);
      }
    }
    child = child->m_sibling_lower;
  }

  /* If not handled by a child, maybe we can handle it ourselves
   */
  if (!handler && m_bTouchable) {
    handler = this;
  }
  return handler;
}

void Window::touch_enter () {
#if 1
  fputs ("<enter>\n", stderr);
#endif
}

void Window::touch_leave () {
#if 1
  fputs ("<leave>\n", stderr);
#endif
}

void Window::touch_event (TouchInput::TouchEvent te, const struct TouchInput::touch_event_data & event_data) {
#if 1
  switch (te) {
  case TouchInput::te_None:
    fputs ("(none)\n", stderr);
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
}

void Window::redraw () {
  if (!visible ())
    return;

  /* Draw self first
   */
  PyCCarUI(id ()).draw ();

  set_dirty (false);

  /* Draw children, bottom to top
   */
  Window * child = m_child_bottom;

  while (child) {
    child->redraw ();
    child = child->m_sibling_upper;
  }
}

Button::Button (Window & parent, int rel_x, int rel_y, unsigned width, unsigned height) :
  Window(parent, rel_x, rel_y, width, height),
  m_handler(0),
  m_button_id(0)
{
  m_flags = PyCCar_BORDER;
  set_enabled (true);
}

Button::~Button () {
  // ...
}

void Button::set_enabled (bool bEnabled) {
  if (bEnabled != enabled ()) {
    if (bEnabled)
      m_flags |=  PyCCar_ENABLED;
    else
      m_flags &= ~PyCCar_ENABLED;

    PyCCarUI(id ()).set_flags (m_flags);

    if (!enabled () && active ()) {
      set_active (false);
    } else {
      redraw ();
    }
    m_bTouchable = enabled ();
  }
}

void Button::set_active (bool bActive) {
  if (bActive != active ()) {
    if (bActive)
      m_flags |=  PyCCar_ACTIVE;
    else
      m_flags &= ~PyCCar_ACTIVE;

    PyCCarUI(id ()).set_flags (m_flags);
    redraw ();
  }
}

void Button::touch_enter () {
  // ...
}

void Button::touch_leave () {
  set_active (false);
}

void Button::touch_event (TouchInput::TouchEvent te, const struct TouchInput::touch_event_data & event_data) {
  if (te == TouchInput::te_End) {
    if (active ()) { // a touch-end event in a highlighted button - the button has been pressed
      set_active (false);

      if (m_handler) {
	m_handler->button_press (m_button_id);
      }
    } else {         // not currently highlighted - uncertain selection? => ditch the event
      // ...
    }
  } else {
    set_active (true);
  }
}
