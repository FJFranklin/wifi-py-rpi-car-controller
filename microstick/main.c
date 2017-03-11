/*
 * File:   main.c
 * Author: Francis James Franklin <fjf@alinameridon.com>
 *
 * Created on 8 March 2017
 */

#include <xc.h>

#include "car/uart.h"
#include "car/clock.h"
#include "car/command.h"

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

void simple_test () {
  char c;

  uint16_t microseconds;

  car_time_t    now;

  car_parse_t   parser = car_command_parser (); // command parser
  car_command_t command;
  car_uart_t *  U1 = car_uart_create ('1', 85);

  car_clock_init ();

  while (true) {
    microseconds = car_clock (&now);

    if (microseconds < 10) {
      // ...
      continue;
    }
    // ...

    if (car_command_next (&command)) {
      car_uart_write (U1, "A command!\n", 11); // non-blocking write
      // ...
    }
    if (car_clock_flags & CAR_CLOCK_TICK) { // every 0.8 ms
      car_clock_flags &= ~CAR_CLOCK_TICK;
      // ...
      while (car_uart_read_char (U1, &c)) { // could be as many as 12 bytes since last tick
	car_command_parse (&parser, c);
      }
    }
    if (car_clock_flags & CAR_CLOCK_SECOND) { // every second
      car_clock_flags &= ~CAR_CLOCK_SECOND;
      // ...
      car_uart_print (U1, car_clock_string ());
      car_uart_print (U1, "\n");
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
