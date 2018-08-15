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

#ifndef __PyCCar_hh__
#define __PyCCar_hh__

#include <Python.h>

/* interface flags
 */
#define PyCCar_VISIBLE 0x01 // whether the window/button is visible
#define PyCCar_BORDER  0x02 // whether the window/button has a border
#define PyCCar_ENABLED 0x04 // whether the window/button is enabled
#define PyCCar_ACTIVE  0x08 // whether the window/button is active
#define PyCCar_SUBMENU 0x10 // whether the window/button has a submenu
#define PyCCar_BLANK   0x20 // whether the window/button is blank (if visible, but regardless of type)

class PyCCarUI {
private:
  unsigned m_id;
public:
  PyCCarUI (unsigned win_id) :
    m_id(win_id)
  {
    // ...
  }

  ~PyCCarUI () {
    // ...
  }

  static bool ui_load (const char * script_filename);
  static void ui_free ();

  static bool init (const char * driver, const char * device, unsigned screen_width, unsigned screen_height);
  static bool init (unsigned screen_width, unsigned screen_height);
  static bool refresh ();

  bool draw ();
  bool set_property (const char * property, PyObject * value);

  /* Set properties
   */
  bool set_bbox (int x, int y, unsigned width, unsigned height);
  bool set_flags (unsigned flags);
  bool set_type (const char * window_type);
  bool set_bg_color (unsigned char r, unsigned char g, unsigned char b);
  bool set_fg_color (unsigned char r, unsigned char g, unsigned char b);
  bool set_fg_disabled (unsigned char r, unsigned char g, unsigned char b);
  bool set_font_size (unsigned size);
  bool set_label (const char * text);
  bool set_spacing (unsigned inset);
  bool set_border_active (unsigned thickness);
  bool set_border_inactive (unsigned thickness);
  bool set_thickness (unsigned thickness);
  bool set_scroll (unsigned s_min, unsigned s_max);
};

#endif /* ! __PyCCar_hh__ */
