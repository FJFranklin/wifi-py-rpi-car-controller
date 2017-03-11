/*
 * File:   uart.h
 * Author: Francis James Franklin <fjf@alinameridon.com>
 *
 * Created on 10 March 2017
 */

#ifndef __CAR_UART_H__
#define __CAR_UART_H__

#include <stdint.h>
#include <stdbool.h>

#include <xc.h>

#define CAR_UART_BUFLENGTH 20

struct car_uart_data {
  struct {
    uint8_t *head;
    uint8_t *tail;
    uint8_t *end;
    
    uint8_t buf[CAR_UART_BUFLENGTH];

    uint8_t pending;
    uint8_t spaces;

    bool bSleeping;
  } tx, rx;
  char uart_no;
};
typedef struct car_uart_data car_uart_t;

extern car_uart_t * car_uart_create (char car_uart_no /* ='1','2',etc. */, uint16_t brg /* = 0x55 (85) for 115200 @ 39613750 Hz */);
extern void         car_uart_print (car_uart_t * U, const char * str); // This writes the whole string, so use with caution!
extern uint8_t      car_uart_write (car_uart_t * U, const char * str, uint8_t count); /* returns #bytes written */
extern bool         car_uart_read_char (car_uart_t * U, char * c);
extern uint8_t      car_uart_read (car_uart_t * U, char * buf, uint8_t buflength);

#endif /* !__CAR_UART_H__ */
