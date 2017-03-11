#include <xc.h>
#include "simple_uart.h"

static uart_t Uart_1, *U1 = 0;

static uart_t * uart_init (char uart_no) {
  uart_t * U = 0;

  switch (uart_no) {
  case '1':
    U = &Uart_1;
    break;
  default:
    break;
  }
  if (U) {
    U->rx.head = U->rx.buf;
    U->rx.tail = U->rx.buf;
    U->rx.end  = U->rx.buf + UART_BUFLENGTH;
    U->rx.pending = 0;
    U->rx.spaces  = UART_BUFLENGTH;
    U->rx.bSleeping = false; // 'true' would indicate an error

    U->tx.head = U->tx.buf;
    U->tx.tail = U->tx.buf;
    U->tx.end  = U->tx.buf + UART_BUFLENGTH;
    U->tx.pending = 0;
    U->tx.spaces  = UART_BUFLENGTH;
    U->tx.bSleeping = true;

    U->uart_no = uart_no;
  }
  return U;
}

uart_t * uart_create (char uart_no, uint16_t brg /* = 0x55 (85) for 115200 @ 39613750 Hz */) {
  uart_t * U = 0;

  switch (uart_no) {
  case '1':
    if (!U1) {
      U1 = uart_init (uart_no);

      U1MODE = 0x0008; // disable UARTEN
      U1STA  = 0x0000; // clear status
      U1BRG  = brg;

      U1MODEbits.UARTEN = true;  // enable UARTEN
      U1STAbits.UTXEN   = true;  // UART1 controls the pin

      IFS0bits.U1TXIF   = false; // clear interrupt flags
      IFS0bits.U1RXIF   = false;
      IFS4bits.U1EIF    = false;

      IEC0bits.U1RXIE   = true;  // enable receive interrupt
      IEC0bits.U1TXIE   = false; // disable transmit interrupt
      IEC4bits.U1EIE    = true;  // enable receive overflow error interrupt
    }
    U = U1;
    break;
  default:
    break;
  }
  return U;
}

void uart_print (uart_t * U, const char * str) { // This writes the whole string, so use with caution!
  const char * ptr1 = str;
  const char * ptr2 = str;

  if (!U || !str) return;

  while (*ptr2) {
    if (!U->tx.spaces) continue; // & this is the problem...
    if (ptr2 - ptr1 == U->tx.spaces) {
      uart_write (U, ptr1, ptr2 - ptr1);
      ptr1 = ptr2;
    }
    ++ptr2;
  }
  if (ptr2 > ptr1) {
    uart_write (U, ptr1, ptr2 - ptr1);
  }
}

uint8_t uart_write (uart_t * U, const char * str, uint8_t count) {
  uint8_t i;
  uint8_t c;

  const char * ptr = str;

  if (!U || !str || !count) return 0;

  switch (U->uart_no) { // disable interrupt
  case '1':
  default:
    IEC0bits.U1TXIE = false;
    break;
  }

  /* Write to buffer
   */
  if (count > U->tx.spaces) {
    count = U->tx.spaces;
  }
  for (i = 0; i < count; i++) {
    c = (uint8_t) *ptr++;
    *U->tx.head++ = c;
    if (U->tx.head == U->tx.end) {
      U->tx.head = U->tx.buf;
    }
  }
  U->tx.spaces  -= count;
  U->tx.pending += count;
  
  switch (U->uart_no) { // enable interrupt
  case '1':
  default:
    if (U->tx.bSleeping) { // need to trigger the interrupt "manually"
      U->tx.bSleeping = false;
      IFS0bits.U1TXIF = true;
    }
    IEC0bits.U1TXIE = true;
    break;
  }

  return count;
}

void __attribute__ ( ( interrupt, no_auto_psv ) ) _U1TXInterrupt (void) {
  IFS0bits.U1TXIF = false;

  if (!Uart_1.tx.pending) { // nothing else to send
    Uart_1.tx.bSleeping = true;
    IEC0bits.U1TXIE = false;
    return;
  }

  while (Uart_1.tx.pending && !U1STAbits.UTXBF) { // there's a 4-deep FIFO transmit buffer
    U1TXREG = *Uart_1.tx.tail++;
    if (Uart_1.tx.tail == Uart_1.tx.end) {
      Uart_1.tx.tail = Uart_1.tx.buf;
    }
    Uart_1.tx.pending--;
    Uart_1.tx.spaces++;
  }
}

bool uart_read_char (uart_t * U, char * c) {
  if (!U || !c || !U->rx.pending) return false;

  uart_read (U, c, 1);

  return true;
}

uint8_t uart_read (uart_t * U, char * buf, uint8_t buflength) {
  uint8_t i;
  uint8_t c;

  char * ptr = buf;

  if (!U || !buf || !buflength) return 0;

  switch (U->uart_no) { // disable interrupt
  case '1':
  default:
    IEC0bits.U1RXIE = false;
    break;
  }

  /* Read from buffer
   */
  if (buflength > U->rx.pending) {
    buflength = U->rx.pending;
  }
  for (i = 0; i < buflength; i++) {
    c = *U->rx.tail++;
    *ptr++ = (char) c;
    if (U->rx.tail == U->rx.end) {
      U->rx.tail = U->rx.buf;
    }
  }
  U->rx.spaces  += buflength;
  U->rx.pending -= buflength;
  
  switch (U->uart_no) { // enable interrupt
  case '1':
  default:
    IEC0bits.U1RXIE = true;
    break;
  }

  return buflength;
}

void __attribute__ ( ( interrupt, no_auto_psv ) ) _U1RXInterrupt (void) {
  IFS0bits.U1RXIF = false;

  if (!Uart_1.rx.spaces) { // nowhere to put received bytes
    return;
  }

  while (Uart_1.rx.spaces && U1STAbits.URXDA) { // there's a 4-deep FIFO receive buffer
    *Uart_1.rx.head++ = U1RXREG;
    if (Uart_1.rx.head == Uart_1.rx.end) {
      Uart_1.rx.head = Uart_1.rx.buf;
    }
    Uart_1.rx.pending++;
    Uart_1.rx.spaces--;
  }
}

void __attribute__ ( ( interrupt, no_auto_psv ) ) _U1ErrInterrupt (void) {
  IFS4bits.U1EIF = false;

  if (U1STAbits.OERR) {
    U1STAbits.OERR = 0; // reset the receive buffer
    Uart_1.rx.bSleeping = true; // make a note
  }
}
