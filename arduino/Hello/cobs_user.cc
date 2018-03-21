/* Copyright 2018 Francis James Franklin
 * 
 * Open Source under the MIT License - see LICENSE in the project's root folder
 */

// To build: c++ -o cobs_user -DCOBS_USER cobs_user.cc message.cpp

#include <cstdio>
#include <cstring>

#include <fcntl.h>
#include <unistd.h>
#include <errno.h>
#include <signal.h>
#include <time.h>
#include <sys/types.h>

typedef unsigned char uint8_t;

#include "message.hh"

uint8_t addr_self = ADDRESS_UNKNOWN; // our address
uint8_t addr_host = ADDRESS_UNKNOWN; // address of our host device

int device_fd = -1;
int verbosity = 0;

const char * text_command = 0;

bool packet (Message & received);

static volatile bool bExit = false;

void interrupt (int /* dummy */) {
  bExit = true;
}

bool bTimeout = false;

struct timespec time_zero;

void reset_timeout () {
  if (bTimeout) {
    clock_gettime (CLOCK_MONOTONIC, &time_zero);
  }
}

bool times_up () {
  if (!bTimeout) return false;

  struct timespec time_now;

  clock_gettime (CLOCK_MONOTONIC, &time_now);

  if (time_now.tv_sec == time_zero.tv_sec) {
    return (time_now.tv_nsec - time_zero.tv_nsec) > 200000000L; // 0.2 ms
  }
  if (time_now.tv_sec - time_zero.tv_sec == 1) {
    return (1000000000L + time_now.tv_nsec - time_zero.tv_nsec) > 200000000L; // 0.2 ms
  }
  return true;
}

void cobs_user_send (uint8_t * data_buffer, int length) { // called by Message::send ()
  if (device_fd >= 0) {
    ssize_t result = write (device_fd, data_buffer, length);
    if (result == -1) {
      fprintf (stderr, "Failed to write to device\n");
    } else if (result < length) {
      fprintf (stderr, "Incomplete write to device: %d bytes of %d written.\n", (int) result, length);
    }
  }
}

int main (int argc, char ** argv) {
  const char * device = "/dev/ttyACM0";

  for (int arg = 1; arg < argc; arg++) {
    if (strcmp (argv[arg], "--help") == 0) {
      fprintf (stderr, "\ncobs_user [--help] [-v] [/dev/<ID>] [--text=<command>]\n\n");
      fprintf (stderr, "  --help     Display this help.\n");
      fprintf (stderr, "  -v         Increase verbosity of reporting.\n");
      fprintf (stderr, "  /dev/<ID>  Connect to /dev/<ID> instead of default [/dev/ttyACM0].\n\n");
      return 0;
    }
    if (strcmp (argv[arg], "-v") == 0) {
      ++verbosity;
    } else if (strncmp (argv[arg], "--text=", 7) == 0) {
      text_command = argv[arg] + 7;
      bTimeout = true;
    } else if (strncmp (argv[arg], "/dev/", 5) == 0) {
      device = argv[arg];
    } else {
      fprintf (stderr, "cobs_user [--help] [-v] [/dev/<ID>] [--text=<command>]\n");
      return -1;
    }
  }

  signal (SIGINT, interrupt);

  /* set up serial
   */
  if (verbosity)
    fprintf (stderr, "Opening \"%s\"...\n", device);

  device_fd = open (device, O_RDWR | O_NOCTTY | O_NONBLOCK /* O_NDELAY */);
  if (device_fd == -1) {
    fprintf (stderr, "Failed to open \"%s\" - exiting.\n", device);
    return -1;
  }

  uint8_t buffer[16];
  buffer[0] = 0;
  cobs_user_send (buffer, 1); // send a single zero to trigger COBS mode

  while (read (device_fd, buffer, 1) == 1); // empty the input buffer

  if (verbosity)
    fprintf (stderr, "Requesting address...\n");

  Message(addr_self, addr_host, Message::Request_Address).send ();

  Message received;

  reset_timeout ();

  while (!bExit) { // TODO: implement a timeout
    if (times_up ()) {
      break;
    }

    int count = read (device_fd, buffer, 1);
    if (count < 0) {
      if (errno == EAGAIN) {
	continue;
      } else {
	fprintf (stderr, "Failed to read from device \"%s\" - exiting.\n", device);
	break;
      }
    } else if (count == 0) {
      continue;
    }

    if (verbosity > 2) {
      if ((buffer[0] >= 32) && (buffer[0] < 127))
	fputc (buffer[0], stderr);
      else
	fprintf (stderr, ".%02x.", (unsigned int) buffer[0]);
    }

    if (received.decode (buffer[0]) == Message::cobs_HavePacket) { // we have a valid response
      if (!packet (received)) {
	break;
      }
      received.clear ();
    }
  }
  if (verbosity)
    fprintf (stderr, "bye bye!\n");

  close (device_fd);
  return 0;
}

bool packet (Message & received) {
  bool bOkay = true;

  uint8_t address_src  = received.get_address_src ();
  uint8_t address_dest = received.get_address_dest ();

  Message::MessageType type = received.get_type ();

  if (type == Message::Supply_Address) {
    addr_self = address_dest; // our new address
    addr_host = address_src;  // address of our host device

    if (verbosity)
      fprintf (stderr, "Address updated to %02x, supplied by host device %02x.\n", (unsigned int) addr_self, (unsigned int) addr_host);

    if (verbosity)
      fprintf (stderr, "Broadcasting address.\n");

    Message(addr_self, ADDRESS_BROADCAST, Message::Broadcast_Address).send ();

    if (verbosity)
      fprintf (stderr, "Sending ping to host.\n");

    Message(addr_self, addr_host, Message::Ping).send ();
  } else if (address_dest != addr_self) {
    if (address_dest == ADDRESS_BROADCAST) {
      if (verbosity > 1)
	fprintf (stderr, "[%02x] Broadcast event.\n", (unsigned int) address_src);
    } // else { // do nothing }
  } else if (type == Message::Ping) {
    if (verbosity)
      fprintf (stderr, "[%02x] Ping received; sending response.\n", (unsigned int) address_src);

    Message(addr_self, address_src, Message::Pong).send ();
  } else if (type == Message::Pong) {
    if (verbosity)
      fprintf (stderr, "[%02x] Ping acknowledged. Network established & ready for use.\n", (unsigned int) address_src);

    /* Make command here.
     */
    if (text_command) {
      Message to_send(addr_self, addr_host, Message::Text_Command);
      to_send = text_command;
      to_send.send ();
      reset_timeout ();
    }
    // ...
  } else if (type == Message::Text_Response) {
    fprintf (stderr, "[%02x] - %s\n", (unsigned int) address_src, received.c_str ());
    reset_timeout ();
  } else if (type == Message::Text_Error) {
    fprintf (stderr, "[%02x] ! %s\n", (unsigned int) address_src, received.c_str ());
    reset_timeout ();
  } else {
    if (verbosity)
      fprintf (stderr, "Message received of type=%02x.\n", (unsigned int) type);
  }
  return bOkay;
}
