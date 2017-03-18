/*
 * File:   command.c
 * Author: Francis James Franklin <fjf@alinameridon.com>
 *
 * Created on 11 March 2017
 */

#include "car/command.h"
#include "car/clock.h"

#define CAR_COMMAND_MAX 4

uint8_t car_command_flags = 0;

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

bool car_command_pending () {
  return cargs_count ? true : false;
}

void car_command_pending_exec () {
  car_command_t next;

  if (!car_command_next (&next)) {
    return;
  }

  switch (next.arg[0]) {
  case 0x00: //   "00          Null command - do nothing",
    break;
  case 0x01: //   "01          Ping!",
    car_command_flags |= CAR_COMMAND_PING;
    break;
  case 0x02: //   "02          Say hello",
    car_command_flags |= CAR_COMMAND_SAY_HELLO_1 | CAR_COMMAND_SAY_HELLO_2;
    break;
  case 0x03: //   "03          Tell time",
    car_command_flags |= CAR_COMMAND_TIME_ONCE;
    break;
  case 0x04: //   "04          Repeat (or stop repeating) time",
    if (car_command_flags & CAR_COMMAND_TIME_REPEAT) {
      car_command_flags &= ~CAR_COMMAND_TIME_REPEAT;
    } else {
      car_command_flags |= CAR_COMMAND_TIME_REPEAT;
    }
    break;
  case 0x0D: //   "0D          Echo off",
    car_command_flags &= ~CAR_COMMAND_ECHO;
    break;
  case 0x0E: //   "0E          Echo on",
    car_command_flags |= CAR_COMMAND_ECHO;
    break;
  case 0x0F: //   "0F          Reset all",
    // TODO
    car_clock_ei0_off ();
    car_clock_set_minutes (0);
    car_clock_set_seconds (0);
    car_command_flags &= CAR_COMMAND_ECHO;
    break;
  case 0x10: // PWM
#if 0
  "10          PWM: All channels off",
  "10,x0       PWM: ~ignored~",
  "10,x1       PWM: Channel x on (must be set up first)",
  "10,x2,HH,HH PWM: Channel x set period to 0xHHHH",
  "10,x3,HH,HH PWM: Channel x set duty cycle to 0xHHHH",
  "10,xF       PWM: Channel x off",
#endif
    break;
  case 0x16: // Adafruit 16-channel servo-controller, via I2C
#if 0
  "16          Servo: All channels off",
  "16,x0       Servo: ~ignored~",
  "16,x1       Servo: Channel x on (must be set up first)",
  "16,x2,HH,HH Servo: Channel x set period to 0xHHHH",
  "16,x2,HH,HH Servo: Channel x set duty cycle to 0xHHHH",
  "16,xF       Servo: Channel x off",
#endif
    break;
  case 0x2c: // I2C
#if 0
  "2c          I2C: Off",
  "2c,01       I2C: On w/ defaults for 100kHz",
  "2c,04       I2C: On w/ defaults for 400kHz",
  "2c,0A       I2C: (reserved)",
  "2c,0B,HH,HH I2C: set BRG to 0xHHHH",
  "2c,0E       I2C: list parameters",
  "2c,0F       I2C: list addresses",
#endif
    break;
  case 0x60: // Clock
    switch (next.arg[1]) {
    case 0x00: // Clock: Reset
      car_clock_set_minutes (0);
      car_clock_set_seconds (0);
      break;
    case 0x01: // Clock: Set minutes to 0xMM
      car_clock_set_minutes (next.arg[2]);
      break;
    case 0x02: // Clock: Set seconds to 0xSS
      car_clock_set_seconds (next.arg[2]);
      break;
    case 0x03: // Clock: Set minutes to 0xMM and seconds to 0xSS
      car_clock_set_minutes (next.arg[2]);
      car_clock_set_seconds (next.arg[3]);
      break;
    default:
      break;
    }
    break;
  case 0xE0: // External Interrupt No. 0
    switch (next.arg[1]) {
    case 0x00: // Ext.Int.0: Off
      car_clock_ei0_off ();
      break;
    case 0x01: // Ext.Int.0: Count for 1 s
    case 0x08: // Ext.Int.0: Count for 0.8 ms
    case 0x20: // Ext.Int.0: Count for 20 ms
      car_clock_ei0_count (next.arg[1]);
      break;
    case 0x0E: // Ext.Int.0: Notify on interrupt
      car_clock_ei0_notify ();
      break;
    default:
      break;
    }
    break;
  default:
    break;
  }
}

car_parse_t car_command_parser () {
  car_parse_t parser;

  parser.bytes_read = 0;

  return parser;
}

/* Returns true if byte is not rejected, or if final command cannot be added to queue
 * If command is complete, it is added automatically to the queue
 * 
 * This parser is expecting commands to be strings of up to 8 hex chars
 * delimited by newline '\n' or ')'; short commands need delimitation
 * e.g., "A3FF00F7)", giving 32 bits to convey command and any associated data.
 */
bool car_command_parse (car_parse_t * parser, uint32_t c) {
  uint8_t byte;
  uint8_t argi;

  if (!parser) return false;

  if (!parser->bytes_read) { // special case
    if ((c == '\n') || (c == ')')) return true;
  } else {
    if ((c == '\n') || (c == ')')) { // have a short command
      parser->bytes_read = 0;
      return car_command_add (&parser->command);
    }
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

  if (!parser->bytes_read) {
    parser->command.arg[0] = byte << 4;
    parser->command.arg[1] = 0;
    parser->command.arg[2] = 0;
    parser->command.arg[3] = 0;
  } else {
    argi = parser->bytes_read / 2;

    if (parser->bytes_read & 0x01) {
      parser->command.arg[argi] |= byte;
    } else {
      parser->command.arg[argi] = byte << 4;
    }
  }

  if (++parser->bytes_read == 8) {
    parser->bytes_read = 0;
    return car_command_add (&parser->command);
  }
  return true;
}
