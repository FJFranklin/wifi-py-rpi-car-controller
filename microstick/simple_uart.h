#ifndef __SIMPLE_UART_H__
#define __SIMPLE_UART_H__

#include <stdint.h>
#include <stdbool.h>

#define UART_BUFLENGTH 20

struct uart_data {
  struct {
    uint8_t *head;
    uint8_t *tail;
    uint8_t *end;
    
    uint8_t buf[UART_BUFLENGTH];

    uint8_t pending;
    uint8_t spaces;

    bool bSleeping;
  } tx, rx;
  char uart_no;
};
typedef struct uart_data uart_t;

extern uart_t * uart_create (char uart_no /* ='1','2',etc. */, uint16_t brg /* = 0x55 (85) for 115200 @ 39613750 Hz */);
extern void     uart_print (uart_t * U, const char * str); // This writes the whole string, so use with caution!
extern uint8_t  uart_write (uart_t * U, const char * str, uint8_t count); /* returns #bytes written */
extern bool     uart_read_char (uart_t * U, char * c);
extern uint8_t  uart_read (uart_t * U, char * buf, uint8_t buflength);

/* e.g.:

   char c;
   uart_t * U1 = uart_create ('1', 85);
   while (true) {
      while (!uart_read_char (U1, &c)); // wait for an audience
      uart_print (U1, "Hello, world!\n");
   }
 */

#endif /* !__SIMPLE_UART_H__ */
