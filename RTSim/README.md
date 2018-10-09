RTSim - Robot Simulator
=======================

https://www.staff.ncl.ac.uk/francisfranklin/robot/

## Overview

Automated vehicles are increasingly part of our society, in the forms of cars, taxi-copters and lawn-mowing robots. All of these must get from A to B while navigating maps and avoiding obstacles. They have a wide range of sensors to help them, from GPS positioning and magnetic compass orientation to proximity detectors, cameras, accelerometers and gyros, and must control motors and servos in order to move and react to their environment.

These robots, therefore, must perform multiple tasks at once, taking input from sensors and controlling actuators, all while responding to instructions from humans and preventing accidents. They can’t afford to do one task at a time – unless it is a very quick task. Imagine if a car’s attention were dedicated entirely to making an indicator blink:

1. light on
2. do nothing for one second
3. light off
4. do nothing for one second
5. & repeat – goto Step 1…

A second is a very long time for a computer. Even ‘slow’ devices like an Arduino Uno can do millions of calculations per second. The above indicator sequence should really be:

1. light on
2. do something else for one second
3. light off
4. do something else for one second
5. & repeat – goto Step 1…

Perhaps there’s nothing else to do but twiddle thumbs, but better to sit and keep watch than set the alarm and go to sleep.

**RTSim** is a Matlab or Python simulation of an Arduino-controlled robot. The robot is circular with diameter 0.4m, and has two independently controlled bidirectional wheels. It is equipped with GPS, a compass, and a sonar (*ping!*) device that can detect obstacles up to 1m away. The sonar can be orientated at any angle relative to the robot, but needs at least 0.1s between pings.

## Matlab

The following two files should be in your Matlab working folder:

- RTSim.m – do not edit this.
- RTRobot.m – edit this.

As with the Arduino, `setup()` runs once at the beginning, and then `loop()` is run repeatedly (until the robot reaches its destination). To start the simulation, just type the following in the Matlab command window:
```python
RTRobot(30);
```
where the ’30’ (or whatever) is how long you want the simulation to last.

The methods available for controlling the robot are:

### `obj.reset_barriers (seed);`
Generate map for seed (any positive integer) with random initial and target positions; use this in `setup()`.
### `target = obj.new_target ();`
Sets (and returns) a random target to aim for; use this in `setup()`.
### `target = obj.get_target ();`
Returns the current target to aim for.
### `time_us = obj.micros ();`
Microseconds since program started.
### `time_ms = obj.millis();`
Milliseconds since program started.
### `obj.set_wheel_speeds (left, right);`
Set left and right wheel speeds (-127..127).
### `obj.set_ping_angle (angle);`
Set angle (0..359) of sonar sensor.
### `obj.ping_send ();`
Send a ping; the sonar takes 40ms to respond, but 100ms before another ping can be sent.
### `position = obj.get_GPS ();`
The current position; updates once a second.
### `orientation = obj.get_compass ();`
The orientation [degrees]; updates once a second. 

## Python

The following two files should be in your Python working folder (e.g., `H:\\Python`):

- RTSim.py – do not edit this.
- RTRobot.py – edit this.

When you start the Python application and command window (e.g., IDLE, or IDLEX if you have it), you will need to set the working directory:
```python
import os
os.chdir('H:\\Python')
```

As with the Arduino, `setup()` runs once at the beginning, and then `loop()` is run repeatedly (until the robot reaches its destination). To start the simulation, just type the following in the Python command window:
```python
import RTRobot
RTRobot.RTRobot(30)
```
where the ’30’ (or whatever) is how long you want the simulation to last.

The methods available for controlling the robot are:

### `self.reset_barriers(seed)`
Generate map for seed (any positive integer) with random initial and target positions; use this in `setup()`.
### `target = self.new_target()`
Sets (and returns) a random target to aim for; use this in `setup()`.
### `target = self.get_target()`
Returns the current target to aim for.
### `time_us = self.micros()`
Microseconds since program started.
### `time_ms = self.millis()`
Milliseconds since program started.
### `self.set_wheel_speeds(left, right)`
Set left and right wheel speeds (-127..127).
### `self.set_ping_angle(angle)`
Set angle (0..359) of sonar sensor.
### `self.ping_send()`
Send a ping; the sonar takes 40ms to respond, but 100ms before another ping can be sent.
### `position = self.get_GPS()`
The current position; updates once a second.
### `orientation = self.get_compass()`
The orientation [degrees]; updates once a second. 

--------

## License

Unless otherwise stated, the code and examples here are
provided under the MIT License:

Copyright (c) 2018 Francis James Franklin

Permission is hereby granted, free of charge, to any person
obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the
Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software,
and to permit persons to whom the Software is furnished to
do so, subject to the following conditions:

The above copyright notice and this permission notice shall
be included in all copies or substantial portions of the
Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS
OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
