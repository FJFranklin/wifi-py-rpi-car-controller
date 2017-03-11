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

#endif /* !__CAR_COMMAND_H__ */
