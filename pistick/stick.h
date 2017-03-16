#ifndef __PISTICK_STICK_H__
#define __PISTICK_STICK_H__

const char * help[] = {
  "00          Null command - do nothing",
  "01          Ping!",
  "02          Say hello",
  "03          Tell time",
  "04          Repeat time",
  "0D          Echo off",
  "0E          Echo on",
  "0F          Reset all",
  "10          PWM: All channels off",
  "10,x0       PWM: ~ignored~",
  "10,x1       PWM: Channel x on (must be set up first)",
  "10,x2,HH,HH PWM: Channel x set period to 0xHHHH",
  "10,x3,HH,HH PWM: Channel x set duty cycle to 0xHHHH",
  "10,xF       PWM: Channel x off",
  "16          Servo: All channels off",
  "16,x0       Servo: ~ignored~",
  "16,x1       Servo: Channel x on (must be set up first)",
  "16,x2,HH,HH Servo: Channel x set period to 0xHHHH",
  "16,x2,HH,HH Servo: Channel x set duty cycle to 0xHHHH",
  "16,xF       Servo: Channel x off",
  "2c          I2C: Off",
  "2c,01       I2C: On w/ defaults for 100kHz",
  "2c,04       I2C: On w/ defaults for 400kHz",
  "2c,0A       I2C: (reserved)",
  "2c,0B,HH,HH I2C: set BRG to 0xHHHH",
  "2c,0F       I2C: list addresses",
  "60          Clock: Reset",
  "60,01,MM    Clock: Set minutes to 0xMM",
  "60,02,SS    Clock: Set seconds to 0xSS",
  "60,03,MM,SS Clock: Set minutes to 0xMM and seconds to 0xSS",
  "E0          Ext.Int.0: Off",
  "E0,01       Ext.Int.0: Notify on interrupt",
  "E0,08       Ext.Int.0: Count for 0.8ms",
  "E0,20       Ext.Int.0: Count for 20ms",
  0
};


#endif /* ! __PISTICK_STICK_H__ */
