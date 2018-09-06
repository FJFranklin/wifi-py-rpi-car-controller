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

#define ButtonID_None  0
#define ButtonID_Exit  1
#define ButtonID_Main  2
#define ButtonID_Back  ButtonID_Main
#define ButtonID_Up    3
#define ButtonID_Down  4
#define ButtonID_Item0 5

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
//m_rel_x(0),
//m_rel_y(0),
  m_W(width),
  m_H(height),
  m_id(0),
  m_flags(0),
  m_bDirty(true),
  m_bTouchable(true)
{
  ui().set_bbox (m_abs_x, m_abs_y, m_W, m_H);

  /* Settings for root window
   */
  m_flags = PyCCar_VISIBLE | PyCCar_BLANK;
  ui().set_flags (m_flags);
}

Window::Window (Window & parent, int rel_x, int rel_y, unsigned width, unsigned height) :
  m_parent(&parent),
  m_child_bottom(0),
  m_child_top(0),
  m_sibling_lower(0),
  m_sibling_upper(0),
  m_abs_x(parent.m_abs_x + rel_x),
  m_abs_y(parent.m_abs_y + rel_y),
//m_rel_x(rel_x),
//m_rel_y(rel_y),
  m_W(width),
  m_H(height),
  m_id(s_id_next ()),
  m_flags(0),
  m_bDirty(true),
  m_bTouchable(false)
{
  parent.add_child (this);

  ui().set_bbox (m_abs_x, m_abs_y, m_W, m_H);
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
    ui().set_flags (m_flags);

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

bool Window::touch_event (TouchInput::TouchEvent te, const struct TouchInput::touch_event_data & event_data) {
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
  return true; // keep the timer running
}

void Window::redraw () {
  if (!visible ())
    return;

  /* Draw self first
   */
  ui().draw ();

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

    ui().set_flags (m_flags);

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

    ui().set_flags (m_flags);
    redraw ();
  }
}

void Button::touch_enter () {
  // ...
}

void Button::touch_leave () {
  set_active (false);
}

bool Button::touch_event (TouchInput::TouchEvent te, const struct TouchInput::touch_event_data & event_data) {
  bool response = true; // keep the timer running

  if (te == TouchInput::te_End) {
    if (active ()) { // a touch-end event in a highlighted button - the button has been pressed
      set_active (false);

      if (m_handler) {
	response = m_handler->button_press (m_button_id);
      }
    } else {         // not currently highlighted - uncertain selection? => ditch the event
      // ...
    }
  } else {
    set_active (true);
  }

  return response;
}

Menu::Item::Item (unsigned id, const char * str) :
  m_id(id),
  m_label(0),
  m_next(0),
  m_submenu(0),
  m_bEnabled(true)
{
  set_label (str);
}

Menu::Item::~Item () {
  if (m_label) {
    delete [] m_label;
  }
}

void Menu::Item::set_label (const char * str) {
  if (m_label) {
    delete [] m_label;
  }
  if (!str) {
    str = "";
  }
  m_label = new char[strlen (str) + 1];
  if (m_label) {
    strcpy (m_label, str);
  }
}

void Menu::Item::set_submenu (Menu * menu) {
  if (m_submenu) {
    delete m_submenu;
  }
  m_submenu = menu;
}

Menu::Menu (struct Info * info) :
  m_parent(0),
  m_item_first(0),
  m_item_last(0),
  m_length(0),
  m_offset(0)
{
  if (info) {
    struct Info * I = info;

    while (I->m_id) {
      Item * item = add (I->m_id, I->m_label);

      if (item && I->m_submenu) {
	Menu * M = new Menu(I->m_submenu);
	if (M) {
	  M->m_parent = this;
	  item->set_submenu (M);
	}
      }
      ++I;
    }
  }
}

Menu::~Menu () {
  while (m_item_first) {
    Item * item = m_item_first;
    m_item_first = m_item_first->m_next;
    delete item;
  }
}

Menu::Item * Menu::add (unsigned id, const char * label) {
  Item * I = new Item(id, label);
  if (I) {
    if (!m_item_first) {
      m_item_first = I;
    } else {
      m_item_last->m_next = I;
    }
    m_item_last = I;
    ++m_length;
  }
  return I;
}

Menu::Item * Menu::item_no (unsigned no) { // by order in list
  Item * I = 0;

  if (no < m_length) {
    I = m_item_first;
    while (no) {
      I = I->m_next;
      --no;
    }
  }
  return I;
}

Menu::Item * Menu::find_id (unsigned id) { // recursive search for item by id
  Item * I = 0;

  if (m_length) {
    Item * item = m_item_first;
    for (unsigned i = 0; i < m_length; i++) {
      if (item->id () == id) {
	I = item;
	break;
      }
      if (item->m_submenu) {
	I = item->m_submenu->find_id (id);
	if (I)
	  break;
      }
      item = item->m_next;
    }
  }
  return I;
}

ScrollableMenu::ScrollableMenu (Window & parent, int rel_x, int rel_y, unsigned width, unsigned height) :
  Window(parent, rel_x, rel_y, width, height),
  m_Back(0),
  m_Up(0),
  m_Down(0),
  m_Scroll(0)
{
  for (int i = 0; i < 6; i++) {
    m_Item[i] = 0;
  }

  unsigned scroll_width  = ((width < height) ? width : height) / 5;
  unsigned scroll_height = height - 2 * scroll_width;

  unsigned item_width  = width - scroll_width;
  unsigned item_height = height / 6;

  for (int i = 0; i < 6; i++) {
    m_Item[i] = new Button(*this, 0, i * item_height, item_width, item_height);

    if (m_Item[i]) {
      m_Item[i]->set_visible (false);
      m_Item[i]->set_handler (this, ButtonID_Item0 + i);
      m_Item[i]->ui().set_type ("Menu Item");
      // TODO - font size, ??
    }
  }

  m_Up     = new Button(*this, item_width,                            0, scroll_width, scroll_width);
  m_Down   = new Button(*this, item_width, scroll_width + scroll_height, scroll_width, scroll_width);
  m_Scroll = new Button(*this, item_width,                 scroll_width, scroll_width, scroll_height);

  if (m_Up) {
    m_Up->set_enabled (false);
    m_Up->set_handler (this, ButtonID_Up);
    m_Up->ui().set_type ("Up");
    // TODO
  }
  if (m_Down) {
    m_Down->set_enabled (false);
    m_Down->set_handler (this, ButtonID_Down);
    m_Down->ui().set_type ("Down");
    // TODO
  }
  if (m_Scroll) {
    m_Scroll->set_visible (false);
    m_Scroll->ui().set_type ("Scroll");
    // TODO - min, max
  }
}

ScrollableMenu::~ScrollableMenu () {
  for (int i = 0; i < 6; i++) {
    if (m_Item[i]) {
      delete m_Item[i];
    }
  }
  if (m_Up) {
    delete m_Up;
  }
  if (m_Down) {
    delete m_Down;
  }
  if (m_Scroll) {
    delete m_Scroll;
  }
}

void ScrollableMenu::manage_menu (Menu * menu, Button * back, Button::Handler * app_manager) {
  m_menu = menu;
  m_Back = back;
  m_app = app_manager;
  // TODO
  // manage visibility, etc.
  // need back() & close() methods to manage submenus & button-clicks
  // menus need parents
  // implement handler here & redirect
}

bool ScrollableMenu::button_press (unsigned button_id) {
  bool response = true; // keep the timer running

  switch (button_id) {
  case ButtonID_Back:
    {
      menu_back ();
      break;
    }
  case ButtonID_Up:
    {
      menu_up ();
      break;
    }
  case ButtonID_Down:
    {
      menu_down ();
      break;
    }
  default:
    {
      button_id -= ButtonID_Item0;
      // ...
      break;
    }
  }

  return response;
}

void ScrollableMenu::menu_back () {
  // ...
}

void ScrollableMenu::menu_up () {
  // ...
}

void ScrollableMenu::menu_down () {
  // ...
}

MenuManager::MenuManager (Handler * H, struct Menu::Info * main_info, struct Menu::Info * exit_info) :
  m_handler(H),
  m_Main(0), // alt. Back
  m_Exit(0),
  m_menu_Main(main_info),
  m_menu_Exit(exit_info),
  m_off_x(0),
  m_off_y(0),
  m_W(Window::root().window_width ()),
  m_H(Window::root().window_height ())
{
  m_off_x = ((m_W < m_H) ? m_W : m_H) / 5;

  m_W -= m_off_x;

  m_Main = new Button(Window::root(), 0,             0, m_off_x, m_off_x);
  m_Exit = new Button(Window::root(), 0, m_H - m_off_x, m_off_x, m_off_x);

  m_Menu = new ScrollableMenu(Window::root(), m_off_x, m_off_y, m_W, m_H);

  if (m_Main) {
    m_Main->set_visible (true);
    m_Main->set_enabled (true);
    m_Main->set_handler (this, ButtonID_Back);
    m_Main->ui().set_type ("Back"); // FIXME
    // TODO
  }
  if (m_Exit) {
    m_Exit->set_visible (true);
    m_Exit->set_enabled (true);
    m_Exit->set_handler (this, ButtonID_Exit);
    m_Exit->ui().set_type ("Exit");
    // TODO
  }
}

MenuManager::~MenuManager () {
  if (m_Menu) {
    delete m_Menu;
  }
  if (m_Main) {
    delete m_Main;
  }
  if (m_Exit) {
    delete m_Exit;
  }
}

bool MenuManager::button_press (unsigned menu_id) {
  bool response = true; // keep the timer running

  if (menu_id == ButtonID_Exit) { // setup & start exit menu
    if (m_handler)
      if (m_handler->notify_menu_will_open ()) {
	m_Exit->set_enabled (false);
	// 
      }
  } else if (menu_id == ButtonID_Back) { // setup & start main menu
    if (m_handler)
      if (m_handler->notify_menu_will_open ()) {
	m_Exit->set_enabled (false);
	// 
      }
  } else {
    // return from menu sequence - tidy up
    m_Exit->set_enabled (true);

    if (m_handler) {
      response = m_handler->notify_menu_closed (menu_id);
    }
  }

  return response;
}
