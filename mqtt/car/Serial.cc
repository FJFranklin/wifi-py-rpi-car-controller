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
#include <cstdlib>
#include <cstring>

#include <fcntl.h>
#include <unistd.h>
#include <errno.h>
#include <termios.h>

#include "Serial.hh"

Serial::Command::~Command() {
  // ...
}

Serial::Serial(Serial::Command * C, const char * device_name, bool bFixBaud) :
  m_C(C),
  m_device(device_name),
  m_fd(-1),
  m_length(0),
  m_bFixBAUD(bFixBaud)
{
  connect();
}

Serial::~Serial() {
  disconnect();
}

void Serial::read() {
  if (m_fd < 0) {
    return;
  }

  unsigned char byte;

  while (true) {
    int count = ::read(m_fd, &byte, 1);
    if (count < 0) {
      if (errno == EAGAIN) {
	break;
      } else {
	fprintf(stderr, "Serial: Failed to read from device.\n");
	disconnect();
	break;
      }
    } else if (count == 0) {
      break;
    }

    if ((byte >= 'A' && byte <= 'Z') || (byte >= 'a' && byte <= 'z')) {
      m_buffer[0] = byte;
      m_length = 1;
    } else if (byte >= '0' && byte <= '9') {
      if (m_length > 0 && m_length < 11) {
	m_buffer[m_length++] = byte;
      } else {
	m_length = 0;
      }
    } else if (byte == ',') {
      if (m_length > 1) {
	m_buffer[m_length] = 0;
	if (m_C) {
	  m_C->serial_command(m_buffer[0], strtoul(m_buffer+1, 0, 10));
	}
      } else if (m_length == 1) {
	if (m_C) {
	  m_C->serial_command(m_buffer[0], 0);
	}
      }
      m_length = 0;
    } else {
      m_length = 0;
    }
  }
}

void Serial::write(char command, unsigned long value) {
  static char buffer[16];

  if (m_fd < 0) {
    return;
  }

  buffer[0] = command;

  if (value) {
    sprintf(buffer + 1, "%lu,", value);
  } else {
    buffer[1] = ',';
    buffer[2] = 0;
  }

  int count = strlen(buffer);

  ssize_t result = ::write(m_fd, buffer, count);

  if (result == -1) {
    fprintf(stderr, "Serial: Failed to write to device\n");
    disconnect();
  } else if (result < count) {
    fprintf(stderr, "Serial: Incomplete write to device: %d bytes of %d written.\n", (int) result, count);
    disconnect();
  }
}

void Serial::connect() {
  m_fd = open(m_device, O_RDWR | O_NOCTTY | O_NONBLOCK /* O_NDELAY */);
  if (m_fd == -1) {
    fprintf(stderr, "Failed to open \"%s\" - exiting.\n", m_device);
    return;
  }

  if (m_bFixBAUD) {
    struct termios options;

    tcgetattr(m_fd, &options);

    options.c_cflag = CS8 | CLOCAL | CREAD;
    options.c_iflag = IGNPAR;
    options.c_oflag = 0;
    options.c_lflag = 0;

    cfsetispeed(&options, B115200);
    cfsetospeed(&options, B115200);

    tcflush(m_fd, TCIFLUSH);
    tcsetattr(m_fd, TCSANOW, &options);
  }

  unsigned char byte;

  while (::read(m_fd, &byte, 1) > 0) {
    // empty the input buffer
  }

  if (m_C) {
    m_C->serial_connect();
  }
}

void Serial::disconnect() {
  if (m_fd >= 0) {
    close(m_fd);
    m_fd = -1;

    if (m_C) {
      m_C->serial_disconnect();
    }
  }
}
