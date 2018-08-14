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

#include "TouchInput.hh"
#include "Window.hh"

using namespace PyCCar;

static const char * application_name = "PyCCar";
static const char * script_filename  = "pyccarui"; // without extension

static const char * touch_device = "/dev/input/event0";
static const char * video_device = "/dev/fb0";
static const char * video_driver = "fbcon";

static TouchInput * TI = 0;

int main (int /* argc */, char ** /* argv */) {
  unsigned screen_width  = 800;
  unsigned screen_height = 480;

  unsigned refresh_interval = 15;

  TouchInput touch(true);
  TI = &touch;

  if (!TI->init (touch_device)) {
    fprintf (stderr, "%s: unable to open event device \"%s\" for reading!\n", application_name, touch_device);
    return -1;
  }

  Py_SetProgramName (const_cast<char *>(application_name));
  Py_Initialize ();

  if (PyCCarUI::ui_load (script_filename)) {
    if (PyCCarUI::init (video_driver, video_device, screen_width, screen_height)) {
      if (Window::init (screen_width, screen_height)) {
	TI->run (Window::root (), refresh_interval);
      } else {
	fputs ("Failed to initialise window manager!\n", stderr);
      }
    }
  }
  PyCCarUI::ui_free ();

  Py_Finalize ();
  return 0;
}
