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
//  int m_rel_x;
//  int m_rel_y;

    unsigned m_W;
    unsigned m_H;

    unsigned m_id;
  protected:
    unsigned m_flags;

  private:
    bool m_bDirty;
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
    inline PyCCarUI ui () const {
      return PyCCarUI(m_id);
    }

    inline void set_dirty (bool bDirty) { // FIXME: what to do about this?
      m_bDirty = bDirty;
    }
    inline bool dirty () const {
      return m_bDirty;
    }

    inline bool visible () const {
      return m_flags & PyCCar_VISIBLE;
    }
    void set_visible (bool bVisible);

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
  public:
    class Handler {
    public:
      virtual void button_press (unsigned button_id) = 0;
      virtual ~Handler () { }
    };

  private:
    Handler * m_handler;
    unsigned  m_button_id;

  public:
    Button (Window & parent, int rel_x, int rel_y, unsigned width, unsigned height);

    virtual ~Button ();

    inline void set_callback (Handler * handler, unsigned button_id) {
      m_handler   = handler;
      m_button_id = button_id;
    }

    inline bool enabled () const {
      return m_flags & PyCCar_ENABLED;
    }
    void set_enabled (bool bEnabled);
  private:
    inline bool active () const {
      return m_flags & PyCCar_ACTIVE;
    }
    void set_active (bool bActive);
  public:
    virtual void touch_enter ();
    virtual void touch_leave ();
    virtual void touch_event (TouchInput::TouchEvent te, const struct TouchInput::touch_event_data & event_data);
  };

  class Menu {
  public:
    class Item {
    private:
      friend class Menu;

      unsigned  m_id;
      char *    m_label;
      Item *    m_next;
    public:
      Menu *    m_submenu;
      bool      m_bEnabled;

      Item (unsigned id, const char * str);

      ~Item ();

      inline unsigned id () const {
	return m_id;
      }
      inline const char * label () const {
	return m_label;
      }
      void set_label (const char * str);
    };

  private:
    Item *   m_item_first;
    Item *   m_item_last;

    unsigned m_length;
    unsigned m_offset;

  public:
    Menu ();

    ~Menu ();

    inline int length () const {
      return m_length;
    }

    inline void set_offset (unsigned offset) {
      m_offset = offset;
    }
    inline int offset () const {
      return m_offset;
    }

    Item * add (unsigned id, const char * label);

    Item * item_no (unsigned no); // by order in list
    Item * find_id (unsigned id); // recursive search for item by id
  };

  class ScrollableMenu : public Button {
  public:
  private:
    Button * m_Item[6];

    Button * m_Up;
    Button * m_Down;
    Window * m_Scroll;

    Menu *   m_menu;

  public:
    ScrollableMenu (Window & parent, int rel_x, int rel_y, unsigned width, unsigned height);

    virtual ~ScrollableMenu ();

    void set_menu (Menu * menu);
  };
} // namespace PyCCar

#endif /* ! __Window_hh__ */
