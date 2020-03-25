from ArduinoSim import *

switch1pin = 12 # pin number for top switch

servopin = 3    # pin number for the servo

# A variable to keep track of the last time we did something:
previousTime = 0

# A binary variable:
bOn = False

# Create a servo controller
S = Servo()

def setup():
    # millis() gives us time in milliseconds since the beginning of the simulation
    global previousTime
    previousTime = millis()

    pinMode(switch1pin, INPUT)

    # Attach the servo to pin 3
    S.attach(servopin)

def loop():
    # Set up a real-time clock (this triggers every half-second):
    currentTime = millis()
    global previousTime
    if currentTime - previousTime > 500:
        previousTime += 500

        # bOn is an internal switch that gets flicked on and off every half-second
        global bOn
        if bOn:
            bOn = False
        else:
            bOn = True

        # Use the internal switch to control the LED on the Uno; LED_BUILTIN is connected to pin 13
        if bOn:
            digitalWrite(LED_BUILTIN, HIGH)
        else:
            digitalWrite(LED_BUILTIN, LOW)

        # Have the servo position change if the top button is pressed
        switch1state = digitalRead(switch1pin)

        if switch1state:
            S.write(135)
        else:
            S.write(45)

if __name__ == "__main__":
    ArduinoSim(setup, loop)
