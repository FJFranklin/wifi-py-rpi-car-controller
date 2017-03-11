/*
 * File:   command.c
 * Author: Francis James Franklin <fjf@alinameridon.com>
 *
 * Created on 11 March 2017
 */

#include "car/command.h"

#define CAR_COMMAND_MAX 4

static car_command_t cargs_queue[CAR_COMMAND_MAX];
static uint8_t cargs_count = 0;

bool car_command_add (const car_command_t * cargs) {
  if (cargs_count < 4) {
    cargs_queue[cargs_count++] = *cargs;
    return true;
  }
  return false;
}

bool car_command_next (car_command_t * cargs) {
  bool bCommandQueued = cargs_count ? true : false;

  int i;

  if (bCommandQueued) {
    *cargs = cargs_queue[0];
    --cargs_count;

    for (i = 0; i < cargs_count; i++) {
      cargs_queue[i] = cargs_queue[i+1];
    }
  }
  return bCommandQueued;
}

car_parse_t car_command_parser () {
  car_parse_t parser;

  parser.bytes_read = 0;

  return parser;
}

/* Returns true if byte is not rejected, or if final command cannot be added to queue
 * If command is complete, it is added automatically to the queue
 * 
 * This parser is expecting commands to be strings of 8 hex chars, optionally in brackets
 * e.g., "(A3FF00F7)", giving 32 bits to convey command and any associated data.
 */
bool car_command_parse (car_parse_t * parser, uint32_t c) {
  uint8_t byte;
  uint8_t argi;

  if (!parser) return false;

  if (!parser->bytes_read) { // special case
    if ((c == '(') || (c == ')')) return true;
  }

  if ((c >= '0') && (c <= '9')) {
    byte = c - '0';
  } else if ((c >= 'A') && (c <= 'F')) {
    byte = 10 + (c - 'A');
  } else if ((c >= 'a') && (c <= 'f')) {
    byte = 10 + (c - 'a');
  } else { // unwanted (non-hex) character; discard & start again
    parser->bytes_read = 0;
    return false;
  }

  argi = parser->bytes_read / 2;

  if (parser->bytes_read & 0x01) {
    parser->command.arg[argi] |= byte;
  } else {
    parser->command.arg[argi] = byte << 4;
  }

  if (++parser->bytes_read == 8) {
    parser->bytes_read = 0;
    return car_command_add (&parser->command);
  }
  return true;
}
