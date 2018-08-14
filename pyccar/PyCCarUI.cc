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

static PyObject * s_PyCCarUI = 0;

/* Module functions:
   def ui_set_property(win_id, property, value):
   def ui_init(driver, device, screen_w, screen_h):
   def ui_draw(win_id):
   def ui_refresh():
 */
PyObject * s_set_p   = 0;
PyObject * s_init    = 0;
PyObject * s_draw    = 0;
PyObject * s_refresh = 0;

bool PyCCarUI::ui_load (const char * script_filename) {
  if (!PyCCarUI) {
    PyObject * pystr = PyString_FromString (script_filename);
    if (pystr) {
      // fputs ("module loading...\n", stderr);
      s_PyCCarUI = PyImport_Import (pystr);
      Py_DECREF (pystr);

      if (s_PyCCarUI) {
	s_set_p   = PyObject_GetAttrString (s_PyCCarUI, "ui_set_property");
	s_init    = PyObject_GetAttrString (s_PyCCarUI, "ui_init");
	s_draw    = PyObject_GetAttrString (s_PyCCarUI, "ui_draw");
	s_refresh = PyObject_GetAttrString (s_PyCCarUI, "ui_refresh");
	// fputs ("module loaded:\n", stderr);
      }
      if (s_set_p) {
	// fputs ("set_property:", stderr);
	if (!PyCallable_Check (s_set_p)) {
	  Py_XDECREF (s_set_p);
	  s_set_p = 0;
	  // fputs (" x", stderr);
	}
	// fputs ("\n", stderr);
      }
      if (s_init) {
	// fputs ("init:", stderr);
	if (!PyCallable_Check (s_init)) {
	  Py_XDECREF (s_init);
	  s_init = 0;
	  // fputs (" x", stderr);
	}
	// fputs ("\n", stderr);
      }
      if (s_draw) {
	// fputs ("draw:", stderr);
	if (!PyCallable_Check (s_draw)) {
	  Py_XDECREF (s_draw);
	  s_draw = 0;
	  // fputs (" x", stderr);
	}
	// fputs ("\n", stderr);
      }
      if (s_refresh) {
	// fputs ("refresh:", stderr);
	if (!PyCallable_Check (s_refresh)) {
	  Py_XDECREF (s_refresh);
	  s_refresh = 0;
	  // fputs (" x", stderr);
	}
	// fputs ("\n", stderr);
      }
    }
  }
  if (!s_refresh || !s_draw || !s_init || !s_set_p) {
    fputs ("PyCCar: UI load error!\n", stderr);
  }
  return s_refresh;
}

void PyCCarUI::ui_free () {
  if (s_refresh) {
    Py_XDECREF (s_refresh);
    s_refresh = 0;
  }
  if (s_draw) {
    Py_XDECREF (s_draw);
    s_draw = 0;
  }
  if (s_init) {
    Py_XDECREF (s_init);
    s_init = 0;
  }
  if (s_set_p) {
    Py_XDECREF (s_set_p);
    s_set_p = 0;
  }
  if (s_PyCCarUI) {
    Py_DECREF (s_PyCCarUI);
    s_PyCCarUI = 0;
  }
}

bool PyCCarUI::init (const char * driver, const char * device, unsigned screen_width, unsigned screen_height) {
  PyObject * args = Py_BuildValue ("ssII", driver, device, screen_width, screen_height);

  if (args) {
    PyObject * result = PyObject_CallObject (s_init, args);
    Py_DECREF(args);

    if (result) {
      Py_DECREF (result);
      return true;
    }
  }
  return false;
}

bool PyCCarUI::refresh () {
  PyObject * result = PyObject_CallObject (s_refresh, 0);

  if (result) {
    Py_DECREF (result);
    return true;
  }
  return false;
}

bool PyCCarUI::set_property (const char * property, PyObject * value) {
  PyObject * args = Py_BuildValue ("IsO", m_id, property, value);

  if (args) {
    PyObject * result = PyObject_CallObject (s_set_p, args);
    Py_DECREF(args);

    if (result) {
      Py_DECREF (result);
      return true;
    }
  }
  return false;
}

bool PyCCarUI::draw () {
  PyObject * args = Py_BuildValue ("I", m_id);

  if (args) {
    PyObject * result = PyObject_CallObject (s_draw, args);
    Py_DECREF(args);

    if (result) {
      Py_DECREF (result);
      return true;
    }
  }
  return false;
}

bool PyCCarUI::set_bbox (int x, int y, unsigned width, unsigned height) {
  bool bOkay = false;

  PyObject * value = Py_BuildValue ("iiII", x, y, width, height);
  if (value) {
    bOkay = set_property ("bbox", value);
    Py_DECREF (value);
  }
  return bOkay;
}

bool PyCCarUI::set_flags (unsigned flags) {
  bool bOkay = false;

  PyObject * value = Py_BuildValue ("I", flags);
  if (value) {
    bOkay = set_property ("flags", value);
    Py_DECREF (value);
  }
  return bOkay;
}
