wifi-py-rpi-car-controller
==========================

**Overview**

In this project, the focus is on communication over WiFi,
with the aim of being able to control a car or other vehicle
using a web interface. The method requires two Raspberry Pi
(or other Linux) computers.

One RPi, the "controller", is set up as a WiFi hub
(e.g., with hostapd) and DHCP server (e.g., using dnsmasq).
This creates a private network which anyone may connect to -
the security of the network can of course be configured -
over WiFi. The "controller" also runs a web server and MQTT
broker with websockets support; I am using mosquitto, which
provites a default MQTT broker as well as a web server /
websockets interface. The webserver serves the
HTML/Javascript/CSS files that create the web interface.

The other RPi, the "car", connects via WiFi to the MQTT
broker, and the MQTT broker then acts as a middle man,
relaying data between the browser(s) and the "car". The
"car", of course, is responsible for the remote device,
i.e., it must check the sensors for obstacles, update the
current drive settings, adjust the steering, etc.

Given all these requirements, I have created this project
that implements the basic logic:

- Written in Python and using threading and Queue for event
management, and Paho.MQTT (Python).

- The web interface is written as a client-side scripted
interface based on HTML and SVG, and again Paho.MQTT
(Javascript).

--------

**License**

Unless otherwise stated, the code and examples here are
provided under the MIT License:

Copyright (c) 2017 Francis James Franklin

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
