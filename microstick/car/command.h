/*
 * File:   command.h
 * Author: Francis James Franklin <fjf@alinameridon.com>
 *
 * Created on 11 March 2017
 */

#ifndef __CAR_COMMAND_H__
#define __CAR_COMMAND_H__

#include <stdint.h>
#include <stdbool.h>

struct car_command_data {
  uint8_t arg[4];
};
typedef struct car_command_data car_command_t;

extern bool car_command_add (const car_command_t * cargs);
extern bool car_command_next (car_command_t * cargs);
extern bool car_command_pending ();
extern void car_command_pending_exec ();

struct car_command_parse_data {
  car_command_t command;
  uint8_t       bytes_read;
};
typedef struct car_command_parse_data car_parse_t;

/* Use to get an initialised parsing struct:
 */
extern car_parse_t car_command_parser ();

/* Returns true if byte is not rejected, or if final command cannot be added to queue
 * If command is complete, it is added automatically to the queue
 */
extern bool car_command_parse (car_parse_t * parser, uint32_t byte);

/* The bits defined below are set by the clock timer, but never cleared.
 * The user may clear these, if wished.
 */
extern uint8_t car_command_flags;

#define CAR_COMMAND_PING         0x01  // ping
#define CAR_COMMAND_SAY_HELLO_1  0x02  // an up-to-three-part welcome message
#define CAR_COMMAND_SAY_HELLO_2  0x04  // -"-
#define CAR_COMMAND_TIME_ONCE    0x08  // tell the time once
#define CAR_COMMAND_TIME_REPEAT  0x10  // tell the time every second
#define CAR_COMMAND_ECHO         0x20  // echo received characters

#endif /* !__CAR_COMMAND_H__ */
