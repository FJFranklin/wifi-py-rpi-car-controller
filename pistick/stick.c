/*
 * File:   stick.c
 * Author: Francis James Franklin <fjf@alinameridon.com>
 *
 * Created on 16 March 2017
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

#include "stick.h"

void list () {
  int count = 0;

  while (help[count]) {
    fprintf (stdout, "  %s\n", help[count]);
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

  if (argc > 2) {
    fprintf (stderr, "stick [--help] [--list] [--usb] [/dev/ID]\n");
    return -1;
  } else if (argc > 1) {
    if (strcmp (argv[1], "--help") == 0) {
      fprintf (stderr, "\nstick [--help] [--list] [--usb] [/dev/<ID>]\n\n");
      fprintf (stderr, "  --help     Display this help.\n");
      fprintf (stderr, "  --list     List available commands.\n");
      fprintf (stderr, "  --usb      Connect to /dev/ttyUSB0 instead of default /dev/serial0.\n");
      fprintf (stderr, "  /dev/<ID>  Connect to /dev/<ID> instead of default /dev/serial0.\n\n");
      return 0;
    }
    if (strcmp (argv[1], "--list") == 0) {
      list ();
      return 0;
    }
    if (strcmp (argv[1], "--usb") == 0) {
      device = "/dev/ttyUSB0";
    } else if (strncmp (argv[1], "/dev/", 5) == 0) {
      device = argv[1];
    } else {
      fprintf (stderr, "stick [--help] [--list] [--usb] [/dev/ID]\n");
      return -1;
    }
  }

  fd = open (device, O_RDWR | O_NOCTTY | O_NDELAY);
  if (fd == -1) {
    fprintf (stderr, "Failed to open \"%s\" - exiting.\n", device);
    return -1;
  }

  /* set up serial
   */
  if (fd == -1) {
    fprintf (stderr, "error: unable to open serial device\n");
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

  if (write (fd, (const unsigned char *) "0D\n0F)02)0E)", 12) < 0) {
    fprintf (stderr, "error: unable to write to serial\n");
    return -1;
  }

  while (1) {
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
	if (write (fd, (const unsigned char *) "0D\n0F)02)0E)", 12) < 0) {
	  fprintf (stderr, "error: unable to write to serial\n");
	  break;
	}
	continue;
      }
      if (c == '?') {
	fprintf (stderr, "\n");
	list ();
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
