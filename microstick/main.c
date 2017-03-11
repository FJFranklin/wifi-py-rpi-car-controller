/*
 * File:   newmainXC16.c
 * Author: fjf
 *
 * Created on 08 March 2017, 10:18
 */

#include <stdint.h>
#include <stdbool.h>

#include <xc.h>
#include "simple_uart.h"

// #include "libpic30.h"
// #include "uart.h"

// #pragma config BWRP = OFF        // Boot Segment Write-Protect Bit->Boot Segment may be written                                     
// #pragma config BSS = DISABLED    // Boot Segment Code-Protect Level bits->No Protection (other than BWRP)                       
// #pragma config BSS2 = OFF        // Boot Segment Control Bit->No Boot Segment                                                       
#pragma config GWRP = OFF        // General Segment Write-Protect Bit->General Segment may be written                               
// #pragma config GSS = DISABLED    // General Segment Code-Protect Level bits->No Protection (other than GWRP)                    
// #pragma config CWRP = OFF        // Configuration Segment Write-Protect Bit->Configuration Segment may be written                   
// #pragma config CSS = DISABLED    // Configuration Segment Code-Protect Level bits->No Protection (other than CWRP)              
// #pragma config AIVTDIS = DISABLE // Alternate Interrupt Vector Table Disable Bit ->Disable Alternate Vector Table            

// FOSCSEL
#pragma config FNOSC = FRCPLL    // Initial oscillator Source Selection Bits->Fast RC Oscillator with divide-by-N with PLL module (FRCPLL)
#pragma config IESO = ON         // Two Speed Oscillator Start-Up Bit->Start up device with FRC,then automatically switch to user selected oscillator source

// FOSC
#pragma config POSCMD = NONE     // Primary Oscillator Mode Select Bits->Primary Oscillator disabled                             
#pragma config OSCIOFNC = OFF    // OSC2 Pin I/O Function Enable Bit->OSC2 is clock output                                      
#pragma config IOL1WAY = ON      // Peripheral Pin Select Configuration Bit->Allow Only One reconfiguration                       
#pragma config FCKSM = CSDCMD    // Clock Switching Mode Bits->Both Clock Switching and Fail-safe Clock Monitor are disabled    
// #pragma config PLLKEN = ON       // PLL Lock Enable Bit->Clock switch to PLL source will wait until the PLL lock signal is valid   

// FWDT
#pragma config WDTPOST = PS32768 // Watchdog Timer Postscaler Bits->1:32768                                                  
#pragma config WDTPRE = PR128    // Watchdog Timer Prescaler Bit->1:128                                                         
#pragma config FWDTEN = OFF      // Watchdog Timer Enable Bits->WDT and SWDTEN Disabled                                           
#pragma config WINDIS = OFF      // Watchdog Timer Window Enable Bit->Watchdog timer in Non-Window Mode                           
// #pragma config WDTWIN = WIN25    // Watchdog Window Select Bits->WDT Window is 25% of WDT period                                

// FPOR
// #pragma config BOREN0 = ON       // Brown Out Reset Detection Bit->BOR is Enabled

// FICD
#pragma config ICS = PGD1        // ICD Communication Channel Select Bits->Communicate on PGEC1 and PGED1

static bool     bTick      = false;
static bool     bTick_dSec = false;
static bool     bTimerTick = true;
static uint16_t timerCount = 0;
static uint16_t dSec_Count = 0;

uint16_t app_time_s = 0;
uint16_t app_time_m = 0;
uint16_t app_time_h = 0;

void __attribute__((__interupt__, no_auto_psv)) _T1Interrupt (void) {
  IFSO0bits.T1IF = false;

  if (bTimerTick) {      // counted 10 microseconds
    bTimerTick = false;

    PR1 = 0x7A3E;
    /* End of 10 microsecond period */

  } else {               // rest of 0.8 ms period
    bTick      = true;   // interrupt never sets this to false; 0.8 ms
    bTimerTick = true;   // interrupt internal flag

    PR1 = 0x018B;
    /* Beginning of 10 microsecond period */

    if (++timerCount == 1250) {
      timerCount = 0;
      bTick_dSec = true; // interrupt never sets this to false; 100 ms

      /* The internal clock
       */
      if (++dSec_Count == 10) {
	dSec_Count = 0;
	if (++app_time_s == 60) {
	  app_time_s = 0;
	  if (++app_time_m == 60) {
	    app_time_m = 0;
	    ++app_time_f;
	  }
	}
      }
    }
  }
}

struct command_args {
  uint8_t arg[4];
};
static struct command_args cargs_queue[4];
static uint8_t cargs_count;

static bool com_queue_add (const struct command_args * cargs) {
  if (cargs_count < 4) {
    cargs_queue[cargs_count++] = *cargs;
    return true;
  }
  return false;
}

static bool com_queue_next (struct command_args * cargs) {
  int i;

  if (cargs_count) {
    *cargs = cargs_queue[0];
    --cargs_count;

    for (i = 0; i < cargs_count; i++) {
      cargs_queue[i] = cargs_queue[i+1];
    }
  }
  return false;
}

void simple_test () {
  char c;
  char buf[10];
  char com[8];

  uint8_t com_count = 0;

  struct command_args cargs;
  struct command_args cnext;

  uart_t * U1 = uart_create ('1', 85);

  while (true) {
    if (com_queue_next (&cnext)) {
      // ...
    }
    if (bTick) {      // every 0.8 ms
      bTick = false;
      // ...
      while (uart_read_char (U1, &c)) { // could be as many as 12 bytes since last tick
	if ((c >= '0') && (c <= '9')) {
	  com[com_count++] = c - '0';
	} else if ((c >= 'A') && (c <= 'F')) {
	  com[com_count++] = 10 + (c - 'A');
	} else if ((c >= 'a') && (c <= 'f')) {
	  com[com_count++] = 10 + (c - 'a');
	} else { // discard & start again
	  com_count = 0;
	}
	if (com_count == 8) {
	  cargs.arg[0] = ((uint8_t) com[0] << 4) | (uint8_t) com[1];
	  cargs.arg[1] = ((uint8_t) com[2] << 4) | (uint8_t) com[3];
	  cargs.arg[2] = ((uint8_t) com[4] << 4) | (uint8_t) com[5];
	  cargs.arg[3] = ((uint8_t) com[6] << 4) | (uint8_t) com[7];
	  com_queue_add (&cargs);
	  com_count = 0;
	}
      }
    }
    if (bTick_dSec) { // every 100 ms
      bTick_dSec = false;
      // ...
      if (!dSec_Count) { // each new second
	buf[0] = '0' + (app_time_h % 100) / 10;
	buf[1] = '0' + (app_time_h %  10);
	buf[2] = ':';
	buf[3] = '0' +  app_time_m / 10;
	buf[4] = '0' + (app_time_m % 10);
	buf[5] = ':';
	buf[6] = '0' +  app_time_s / 10;
	buf[7] = '0' + (app_time_s % 10);
	buf[8] = '\n';
	buf[9] = 0;
	uart_print (U1, buf);
      }
    }
  }
}

int main(void) {
    char c;
    int bFirst = 1;

    // CF no clock failure; NOSC FRCPLL; CLKLOCK unlocked; OSWEN Switch is Complete;                                            
    __builtin_write_OSCCONL((uint8_t) (0x100 & 0x00FF));
    // FRCDIV FRC/2; PLLPRE 2; DOZE 1:8; PLLPOST 1:2; DOZEN disabled; ROI disabled;                                             
    CLKDIV = 0x3100;
    OSCTUN = 0x0;

    // ROON disabled; ROSEL disabled; RODIV Base clock value; ROSSLP disabled;                                                  
    // REFOCON = 0x0;
                                                                                                                   
    PLLFBD = 0x54; // PLLDIV 84;

    CORCONbits.RND    = 0; // Unbiased convergent rounding
    CORCONbits.SATB   = 0; // Accumulator B saturation disabled
    CORCONbits.SATA   = 0; // Accumulator A saturation disabled
    CORCONbits.ACCSAT = 0; // Accumulator saturation mode normal (1.31))

    RCON = 0x0; // clear brown-out reset bit

    /* The Microstick J3 header used for UART has RXD on RB10 and TXD on RB11
     * a.k.a. RP10 and RP11 (a.k.a. PWM1H/L3)
     */
    LATA     = 0x0000; // Output latches
    LATB     = 0x0800; // RB11 high (TXD); rest low
    TRISA    = 0x0000; // GPIO directions
    TRISB    = 0x0400; // Set Pin RB10 as input (1); rest as output (0)
    CNPU1    = 0x0000; // change notification pull-up
    CNPU2    = 0x0000;
    ODCA     = 0x0000; // open-drain control
    ODCB     = 0x0000;
    AD1PCFGL = 0x001F; // set all analog-capable pins to be digital

    /* Need to unlock registers for Peripheral Pin Select
     */
    OSCCON = 0x46; 
    OSCCON = 0x57; 
    __builtin_write_OSCCONL(OSCCON & 0xbf); // unlock PPS                                                                       

    RPINR18bits.U1RXR = 0x000A; // RB10->UART1:U1RX;                                                                           
    RPOR5bits.RP11R   = 0x0003; // RB11->UART1:U1TX;                                                                             

    __builtin_write_OSCCONL(OSCCON | 0x40); //   lock PPS                                                                       

    T1CON = 0x0000; // Timer 1 disabled

    IPC0bits.T1IP = 0x01;  // priority
    IFS0bits.T1IF = false; // flag
    IEC0bits.T1IE = true;  // priority

    TMR1  = 0x0000;
    PR1   = 0x018B; // 31690 -> 0.8ms [31691(-1=0x7BCA) = 396(-1=18B) + 31295 (-1=7A3E)]
    T1CON = 0x8000; // Timer 1 enabled w/o prescaling, using internal oscillator

    simple_test ();
    return 0;
    /* Having remapped the UART1 pins, set up the UART1 module:
     */
    U1MODE = 0x0008;       // clear all; use high precision baud generator
    U1BRG  = 0x0055;       // 115200 <= Frequency 39613750 Hz / BRG 85
    U1STA  = 0x0000;       // clear status register                                                                                         

    // IEC0bits.U1RXIE = 1;   // interrupt enable

    U1MODEbits.UARTEN = 1; // enable the UART
    U1STAbits.UTXEN = 1;   // UART has control of transmit pin

    IFS0bits.U1RXIF = 0;   // clear the receive flag                                                                              

    while (1) {
        if (U1STAbits.URXDA) { // there is data to be read
            c = U1RXREG;
        } else {
            continue;
        }
        if (bFirst) { // ignore first byte received
            bFirst = 0;
            continue;
        }
        if (U1STAbits.UTXEN == 0) U1STAbits.UTXEN = 1; // enable UART TX                                                            
        while (U1STAbits.UTXBF == 1);                  // if buffer is full, wait                                                                  
        U1TXREG = c + 1;
    }

    return 0;
}
