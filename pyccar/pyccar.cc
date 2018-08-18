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

#include <cstring>

#include "TouchInput.hh"
#include "Window.hh"

using namespace PyCCar;

static const char * application_name = "PyCCar";
static const char * script_filename  = "pyccarui"; // without extension

static const char * touch_device = "/dev/input/event0";
static const char * video_device = "/dev/fb0";
static const char * video_driver = "fbcon";

static TouchInput * TI = 0;

int main (int argc, char ** argv) {
  bool bFrameBuffer = false;
  bool bHyperPixel  = false;

  unsigned screen_width  = 480; // 800;
  unsigned screen_height = 320; // 480;

  unsigned refresh_interval = 15;

  for (int arg = 1; arg < argc; arg++) {
    if (strcmp (argv[arg], "--frame-buffer")) {
      bFrameBuffer = true;
    }
    if (strcmp (argv[arg], "--hyperpixel")) {
      screen_width  = 800;
      screen_height = 480;
      bHyperPixel = true;
    }
    if (strncmp (argv[arg], "--fb-device=", 12)) {
      video_device = argv[arg] + 12;
    }
    if (strncmp (argv[arg], "--touch-device=", 15)) {
      touch_device = argv[arg] + 15;
    }
    if (strcmp (argv[arg], "--help")) {
      fprintf (stdout, "%s [--frame-buffer] [--hyperpixel] [--fb-device=<dev>] [--touch-device=]\n\n"
	       "  --frame-buffer       Use the framebuffer as the display.\n"
	       "  --hyperpixel         This has an 800x480 display; touch coordinates need rescaling.\n"
	       "  --fb-device=<dev>    Framebuffer device [default: /dev/fb0].\n"
	       "  --touch-device=<dev> Touch event input device [default: /dev/input/event0].\n"
	       "\n"
	       , argv[0]);
      return 0;
    }
  }

  TouchInput touch(screen_width, screen_height);
  TI = &touch;

  /* Q. Is there a better way to do this calibration? // FIXME
   */
  if (bHyperPixel) {
    TI->m_range_max_x = 480;
    TI->m_range_max_y = 800;
  } else {
    TI->m_range_min_x = 3920;
    TI->m_range_max_x = 150;
    TI->m_range_min_y = 220;
    TI->m_range_max_y = 3780;
    TI->m_bFlip = true;
  }

  if (!TI->init (touch_device)) {
    fprintf (stderr, "%s: unable to open event device \"%s\" for reading!\n", application_name, touch_device);
    return -1;
  }

  Py_SetProgramName (const_cast<char *>(application_name));
  Py_Initialize ();
  PySys_SetArgv (argc, argv);

  if (PyCCarUI::ui_load (script_filename)) {
    bool bUI = false;

    if (bFrameBuffer)
      bUI = PyCCarUI::init (video_driver, video_device, screen_width, screen_height);
    else
      bUI = PyCCarUI::init (screen_width, screen_height);

    if (bUI) {
      if (Window::init (screen_width, screen_height)) {
	// TODO: create UI
	Window::root().redraw ();
	TI->run (refresh_interval);
      } else {
	fputs ("Failed to initialise window manager!\n", stderr);
      }
    }
  }
  PyCCarUI::ui_free ();

  Py_Finalize ();
  return 0;
}
