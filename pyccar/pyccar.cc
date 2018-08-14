#include "pyccar.hh"

#include "TouchInput.hh"
#include "Window.hh"

using namespace PyCCar;

static const char * application_name = "PyCCar";
static const char * script_filename  = "pyccarui"; // without extension

static const char * touch_device = "/dev/input/event0";
static const char * video_device = "/dev/fb0";
static const char * video_driver = "fbcon";

static TouchInput * TI = 0;

static PyObject * PyCCarUI = 0;

/* Module functions
 */
static PyObject * ui_init    = 0;
static PyObject * ui_redraw  = 0;
static PyObject * ui_refresh = 0;

static bool s_load_ui () {
  if (!PyCCarUI) {
    PyObject * pystr = PyString_FromString (script_filename);
    if (pystr) {
      // fputs ("module loading...\n", stderr);
      PyCCarUI = PyImport_Import (pystr);
      Py_DECREF (pystr);

      if (PyCCarUI) {
	ui_init    = PyObject_GetAttrString (PyCCarUI, "ui_init");
	ui_redraw  = PyObject_GetAttrString (PyCCarUI, "ui_redraw");
	ui_refresh = PyObject_GetAttrString (PyCCarUI, "ui_refresh");
	// fputs ("module loaded:\n", stderr);
      }
      if (ui_init) {
	// fputs ("init:", stderr);
	if (!PyCallable_Check (ui_init)) {
	  Py_XDECREF (ui_init);
	  ui_init = 0;
	  // fputs (" x", stderr);
	}
	// fputs ("\n", stderr);
      }
      if (ui_redraw) {
	// fputs ("redraw:", stderr);
	if (!PyCallable_Check (ui_redraw)) {
	  Py_XDECREF (ui_redraw);
	  ui_redraw = 0;
	  // fputs (" x", stderr);
	}
	// fputs ("\n", stderr);
      }
      if (ui_refresh) {
	// fputs ("refresh:", stderr);
	if (!PyCallable_Check (ui_refresh)) {
	  Py_XDECREF (ui_refresh);
	  ui_refresh = 0;
	  // fputs (" x", stderr);
	}
	// fputs ("\n", stderr);
      }
    }
  }
  if (!ui_refresh || !ui_redraw || !ui_init) {
    fputs ("PyCCar: UI load error!\n", stderr);
  }
  return ui_refresh;
}

static void s_free_ui () {
  if (ui_refresh) {
    Py_XDECREF (ui_refresh);
    ui_refresh = 0;
  }
  if (ui_redraw) {
    Py_XDECREF (ui_redraw);
    ui_redraw = 0;
  }
  if (ui_init) {
    Py_XDECREF (ui_init);
    ui_init = 0;
  }
  if (PyCCarUI) {
    Py_DECREF (PyCCarUI);
    PyCCarUI = 0;
  }
}

static bool s_init_video (const char * driver, const char * device, unsigned screen_width, unsigned screen_height) {
  PyObject * args = Py_BuildValue ("ssII", driver, device, screen_width, screen_height);

  if (args) {
    PyObject * result = PyObject_CallObject (ui_init, args);
    Py_DECREF(args);

    if (result) {
      Py_DECREF (result);
      return true;
    }
  }
  return false;
}

static void s_redraw (PyObject * args) {
  PyObject * result = PyObject_CallObject (ui_redraw, args);
  if (result) {
    Py_DECREF (result);
  }
}

static void s_refresh () {
  PyObject * result = PyObject_CallObject (ui_refresh, 0);
  if (result) {
    Py_DECREF (result);
  }
}

static PyObject * pyccar_info (PyObject * self, PyObject * args) {
  if (!PyArg_ParseTuple (args, ":info")) { // FIXME
    return 0; // set run-time exception?
  }

  // ...

  return Py_BuildValue ("i", 0);
}

static PyMethodDef PyCCarMethods[] = {
  { "info", pyccar_info, METH_VARARGS, "Return details of requested element to refresh." },
  { 0, 0, 0, 0 }
};

int main (int /* argc */, char ** /* argv */) {
  TouchInput touch(true);
  TI = &touch;

  if (!TI->init (touch_device)) {
    fprintf (stderr, "%s: unable to open event device \"%s\" for reading!\n", application_name, touch_device);
    return -1;
  }

  Py_SetProgramName (const_cast<char *>(application_name));
  Py_Initialize ();

  Py_InitModule (application_name, PyCCarMethods);

  if (s_load_ui ()) {
    if (s_init_video (video_driver, video_device, 800, 480)) {
      if (Window::init (800, 480)) {
	TI->run (Window::root (), 15);
      } else {
	fputs ("Failed to initialise window manager!\n", stderr);
      }
    }
  }
  s_free_ui ();

  Py_Finalize ();
  return 0;
}
