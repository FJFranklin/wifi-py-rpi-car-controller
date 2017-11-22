/*
 * File:   stick.cc
 * Author: Francis James Franklin <fjf@alinameridon.com>
 *
 * 21.11.2017 Changed to C++ with option added for Arduino communication
 * 16.03.2017 Created - C program for serial communication with PIC
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/select.h>
#include <sys/time.h>
#include <sys/types.h>
#include <unistd.h>
#include <fcntl.h>
#include <termios.h>

#include "stick.hh"

void list_pic_help () {
  int count = 0;

  while (s_help[count]) {
    fprintf (stdout, "  %s\n", s_help[count]);
    ++count;
  }
}

int main (int argc, char ** argv) {
  char c;

  fd_set fdset;

  struct timeval tv;
  struct termios ttystate, ttysave, options;

  unsigned char buffer[16];

  const char * device = "/dev/serial0";

  int count;
  int fd;

  bool bArduino = false;

  for (int arg = 1; arg < argc; arg++) {
    if (strcmp (argv[arg], "--help") == 0) {
      fprintf (stderr, "\nstick [--help] [--list] [--usb] [--arduino] [/dev/<ID>]\n\n");
      fprintf (stderr, "  --help     Display this help.\n");
      fprintf (stderr, "  --list     List available PIC commands.\n");
      fprintf (stderr, "  --usb      Connect to /dev/ttyUSB0 by default.\n");
      fprintf (stderr, "  --arduino  Connect to /dev/ttyACM0 by default, and omit PIC-specific behaviour.\n");
      fprintf (stderr, "  /dev/<ID>  Connect to /dev/<ID> instead of default [/dev/serial0].\n\n");
      return 0;
    }
    if (strcmp (argv[arg], "--list") == 0) {
      list_pic_help ();
      return 0;
    }
    if (strcmp (argv[arg], "--usb") == 0) {
      device = "/dev/ttyUSB0"; // first serial-over-usb on linux
    } else if (strcmp (argv[arg], "--arduino") == 0) {
      device = "/dev/ttyACM0"; // first serial-over-usb on pi
      bArduino = true;
    } else if (strncmp (argv[arg], "/dev/", 5) == 0) {
      device = argv[arg];
    } else {
      fprintf (stderr, "stick [--help] [--list] [--usb] [--arduino] [/dev/ID]\n");
      return -1;
    }
  }

  /* set up serial
   */
  fd = open (device, O_RDWR | O_NOCTTY | O_NDELAY);
  if (fd == -1) {
    fprintf (stderr, "Failed to open \"%s\" - exiting.\n", device);
    return -1;
  }

  tcgetattr (fd, &options);

  options.c_cflag = B115200 | CS8 | CLOCAL | CREAD;
  options.c_iflag = IGNPAR;
  options.c_oflag = 0;
  options.c_lflag = 0;

  tcflush (fd, TCIFLUSH);
  tcsetattr (fd, TCSANOW, &options);

  /* set up terminal
   */
  tcgetattr (STDIN_FILENO, &ttystate);

  ttysave = ttystate;

  ttystate.c_lflag &= ~(ICANON | ECHO);
  ttystate.c_cc[VMIN] = 1;

  tcsetattr (STDIN_FILENO, TCSANOW, &ttystate);

  if (!bArduino)
    if (write (fd, (const unsigned char *) "0D\n0F)02)0E)", 12) < 0) {
      fprintf (stderr, "error: unable to write to serial\n");
      return -1;
    }

  while (true) {
    count = read (fd, buffer, 10);
    if (count > 0) {
      buffer[count] = 0;
      fprintf (stdout, "%s", (const char *) buffer);
      fflush (stdout);
    }

    tv.tv_sec = 0;
    tv.tv_usec = 10000;

    FD_ZERO (&fdset);
    FD_SET (fileno (stdin), &fdset);

    select (fileno (stdin) + 1, &fdset, 0, 0, &tv);

    if (FD_ISSET (fileno (stdin), &fdset)) { // character
      c = fgetc (stdin);
      if (c == 4) { // CTRL-D - End of Transmission
	fprintf (stderr, "\nbye bye!\n");
	break;
      }
      if (c == 27) { // ESC
	if (!bArduino) {
	  if (write (fd, (const unsigned char *) "0D\n0F)02)0E)", 12) < 0) {
	    fprintf (stderr, "error: unable to write to serial\n");
	    break;
	  }
	  continue;
	}
	c = 3; // send ^C to the Uno
      }
      if ((c == '?') && !bArduino) {
	fprintf (stderr, "\n");
	list_pic_help ();
	continue;
      }
      if (write (fd, &c, 1) < 0) {
	fprintf (stderr, "error: unable to write to serial\n");
	break;
      }
      usleep (100000);
    }
  }

  /* probably unnecessary - restore terminal
   */
  tcsetattr (STDIN_FILENO, TCSANOW, &ttysave);

  close (fd); // close serial

  return 0;
}
