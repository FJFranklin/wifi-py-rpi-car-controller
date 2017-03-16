/*
 * File:   stick.c
 * Author: Francis James Franklin <fjf@alinameridon.com>
 *
 * Created on 16 March 2017
 */

#include <stdio.h>
#include <stdlib.h>
#include <sys/select.h>
#include <sys/time.h>
#include <sys/types.h>
#include <unistd.h>
#include <fcntl.h>
#include <termios.h>

int main () {
  char c;

  fd_set fdset;

  struct timeval tv;
  struct termios ttystate, ttysave, options;

  unsigned char buffer[16];

  int count;
  int fd = open ("/dev/serial0", O_RDWR | O_NOCTTY | O_NDELAY);

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

  while (1) {
    count = read (fd, buffer, 10);
    if (count > 0) {
      buffer[count] = 0;
      fprintf (stdout, "%s", (const char *) buffer);
    }

    tv.tv_sec = 0;
    tv.tv_usec = 10000;

    FD_ZERO (&fdset);
    FD_SET (fileno (stdin), &fdset);

    select (fileno (stdin) + 1, &fdset, 0, 0, &tv);

    if (FD_ISSET (fileno (stdin), &fdset)) { // character
      c = fgetc (stdin);
      if (c == 'q') {
	fprintf (stderr, "quit: 'q' pressed... bye bye!\n");
	break;
      }
      if (write (fd, &c, 1) < 0) {
	fprintf (stderr, "error: unable to write to serial\n");
	break;
      }
    }
  }

  /* probably unnecessary - restore terminal
   */
  tcsetattr (STDIN_FILENO, TCSANOW, &ttysave);

  close (fd); // close serial

  return 0;
}
