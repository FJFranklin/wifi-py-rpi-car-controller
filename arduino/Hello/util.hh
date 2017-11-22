#ifndef ArduinoHello_util_hh
#define ArduinoHello_util_hh

#include <Arduino.h>

/* Specifically for printing a string stored in program memory (using PROGMEM),
 * with the option of a trailing newline.
 * 
 * Suppress printing if echo is off.
 */
extern void print_pgm (const char * str_pgm); // adds a newline automatically at the end

/* Suppress printing if echo is off.
 */
extern void print_str (const char * str);
extern void print_char (char c);

/* Turn echo on/off
 */
extern void command_echo (int argc, char ** argv); // usage: echo on|off

/* Input parsing
 */
extern void input_check (); // check for input, and handle as necessary
extern void input_reset (); // reset the input buffer

#endif /* !ArduinoHello_util_hh */
