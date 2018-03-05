/* Copyright 2018 Francis James Franklin
 * 
 * Open Source under the MIT License - see LICENSE in the project's root folder
 */

// To build: c++ -o cobs_user -DCOBS_USER cobs_user.cc message.cpp

#include <cstdio>
#include <cstring>

#include <fcntl.h>
#include <unistd.h>
#include <sys/types.h>

typedef unsigned char uint8_t;

#include "message.hh"

uint8_t address_src  = 0x7f;
uint8_t address_dest = 0;

int device_fd = -1;

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
      fprintf (stderr, "\nstick [--help] [/dev/<ID>]\n\n");
      fprintf (stderr, "  --help     Display this help.\n");
      fprintf (stderr, "  /dev/<ID>  Connect to /dev/<ID> instead of default [/dev/ttyACM0].\n\n");
      return 0;
    }
    if (strncmp (argv[arg], "/dev/", 5) == 0) {
      device = argv[arg];
    } else {
      fprintf (stderr, "stick [--help] [/dev/<ID>]\n");
      return -1;
    }
  }

  /* set up serial
   */
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

  Message to_send(address_src, address_dest, Message::Request_Address);
  to_send.send ();

  Message received;

  while (true) { // TODO: implement a timeout
    int count = read (device_fd, buffer, 1);
    if (count < 0) {
      fprintf (stderr, "Failed to read from device \"%s\" - exiting.\n", device);
      break;
    } else if (count == 0) {
      continue;
    }

    Message::COBS_State state = received.decode (buffer[0]);

    if (state == Message::cobs_HavePacket) { // we have a valid response
      if (received.get_type () == Message::Supply_Address) {
	address_src  = received.get_address_dest ();
	address_dest = received.get_address_src ();

	fprintf (stderr, "Address updated to %02x, supplied by device %02x.\n", (int) address_src, (int) address_dest);
	fprintf (stderr, "Broadcasting address.\n");

	to_send.set_address_src (address_src);
	to_send.set_address_dest (address_dest);
	to_send.set_type (Message::Broadcast_Address);
	to_send.send ();

	fprintf (stderr, "Sending ping...");

	to_send.set_type (Message::Ping);
	to_send.send ();
      }
      if (received.get_type () == Message::Pong) {
	fprintf (stderr, "acknowledged.\n");
	break;
	// Okay, the network is responding to us. Time to do something interesting... // TODO
      }

      received.clear ();
    }
  }

  close (device_fd);
  return 0;
}
