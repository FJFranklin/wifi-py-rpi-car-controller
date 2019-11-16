This version of the dashboard assumes that files are being served by an MQTT server with websockets functionality. (As of Buster, the Raspberry Pi's standard repository has a working websockets-enabled mosquitto.)

The dashboard is a web-browser-based user interface created using web standards (HTML, SVG, CSS & Javascript), and is served as static files by mosquitto's websockets listener. The Raspberry Pi should be set up as a WiFi access point, and then any smartphone, etc., can load the UI. The UI then interacts with the mosquitto broker, sending commands and receiving feedback.

A second client, the 'car' (or, really, another intermediary), also connects to the broker (using MQTT), receiving commands and sending feedback. This client relays the commands to and feedback from the hardware controller, e.g., an Arduino connected via USB serial.

The Raspberry Pi client (car) and the Arduino (cardy) communicate via a very simple protocol: a letter (A-Za-z) followed by 0-10 digits (0-9) and a final comma (,). Thus "x27,y56,l,r0," is a sequence of four packets; "l," is equivalent to "l0,".

The Arduino code, cardy, mimics a four-wheel vehicle driven by two electric motors.

A sample mosquitto.conf is included, along with cariot.service to start as a service during boot.
