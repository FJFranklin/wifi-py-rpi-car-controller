/* Copyright (c) 2019 Francis James Franklin
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

#include <cstdio>
#include <cstring>

#include "Client.hh"
#include "Serial.hh"

class Car : public Client, public Serial::Command {
private:
  Serial m_S;

  float x_actual;
  float y_actual;
  float slip_l;
  float slip_r;

  const char * m_pattern;

  int m_length;

public:
  Car(const char * serial, bool verbose=false) :
    Client("car", verbose),
    m_S(this, serial, true, verbose),
    x_actual(0),
    y_actual(0)
  {
    set_sleeper(&m_S);

    m_pattern = "/wifi-py-rpi-car-controller/#";
    m_length = strlen(m_pattern) - 1;
  }
  virtual ~Car() {
    // ...
  }
  virtual void serial_connect() {
    fprintf(stdout, "car: connected to Arduino\n");
  }
  virtual void serial_disconnect() {
    fprintf(stdout, "car: disconnected from Arduino\n");
  }
  virtual void serial_command(char command, unsigned long value) {
    switch(command) {
    case 'x':
      {
	x_actual = (-127 + (float) value) / 127;
      }
      break;
    case 'y':
      {
	y_actual = (-127 + (float) value) / 127;
      }
      break;
    case 'l':
      {
	slip_l = (-127 + (float) value) / 127;
      }
      break;
    case 'r':
      {
	slip_r = (-127 + (float) value) / 127;
      }
      break;
    default:
      break;
    }
  }
  virtual void tick() { // every millisecond
    static unsigned count = 0;
    static char buffer[32];

    if (++count == 100) {
      count = 0;
      sprintf(buffer, "%.3f %.3f", x_actual, y_actual);
      publish("/wifi-py-rpi-car-controller/car/XY", buffer);
      sprintf(buffer, "%.3f %.3f", slip_l, slip_r);
      publish("/wifi-py-rpi-car-controller/car/slip", buffer);
    }

    Client::tick(); // network update
  }
  virtual void second() { // every second
    if (!m_S.connected()) {
      m_S.connect();
    }
    Client::second();
  }
  virtual void setup() {
    if (!subscribe(m_pattern)) {
      if (verbose())
	fprintf(stdout, "car: Failed to subscribe with pattern %s\n", m_pattern);
    }
  }
  virtual void message(const char * topic, const char * message, int length) {
    static char buf[32];

    if (length > 31) {
      length = 31;
    }
    strncpy(buf, message, length);
    buf[length] = 0;

    topic += m_length;

    if (verbose())
      fprintf(stdout, "car: message=\"%s\" @ %s\n", buf, topic);

    if (strcmp(topic, "system/exit") == 0) {
      if (strcmp(message, "car") == 0) {
	stop();
      } else if (strcmp(message, "controller") == 0) {
	// Do something to shutdown the Raspberry Pi??
      }
    } else if (strcmp(topic, "dash/XY") == 0) {
      float x, y;
      if (sscanf(message, "%f %f", &x, &y) == 2) {
	int ix = (int) ((1 + x) * 127);
	int iy = (int) ((1 + y) * 127);
	ix = (ix < 0) ? 0 : ((ix > 254) ? 254 : ix);
	iy = (iy < 0) ? 0 : ((iy > 254) ? 254 : iy);
	m_S.write('x', (unsigned long) ix);
	m_S.write('y', (unsigned long) iy);
      }
    }
  }
};

int main(int argc, char ** argv) {
  const char * serial = "/dev/ttyACM0";

  bool verbose = false;
  
  for (int arg = 1; arg < argc; arg++) {
    if (strcmp(argv[arg], "--help") == 0) {
      fprintf(stderr, "\ncar [--help] [--verbose] [/dev/<ID>]\n\n");
      fprintf(stderr, "  --help     Display this help.\n");
      fprintf(stderr, "  --verbose  Print debugging info.\n");
      fprintf(stderr, "  /dev/<ID>  Connect to /dev/<ID> instead of default [/dev/ttyACM0].\n\n");
      return 0;
    }
    if (strcmp(argv[arg], "--verbose") == 0) {
      verbose = true;
    } else if (strncmp(argv[arg], "/dev/", 5) == 0) {
      serial = argv[arg];
    } else {
      fprintf(stderr, "car [--help] [--verbose] [/dev/ID]\n");
      return -1;
    }
  }

  Car(serial, verbose).loop();
  return 0;
}
