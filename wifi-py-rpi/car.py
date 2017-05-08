import paho.mqtt.client as mqtt

import time
import threading

import ticktock

# MQTT constants

# local implementation dependent
mqtt_server_host = "192.168.99.234"
# default port for MQTT
mqtt_server_port = 1883

addr_sys_exit = "/wifi-py-rpi-car-controller/system/exit"
addr_car_xy   = "/wifi-py-rpi-car-controller/car/XY"
addr_dash_xy  = "/wifi-py-rpi-car-controller/dash/XY"

# It is possible to create a separate thread dedicated to checking the sensors, which might send events when necessary.
# I have no idea how to stream the camera. That will probably need to be handled in server.py, though.

class car_controller (object):
    def __init__ (self):
        self.queue_controller = ticktock.qController (self, 0.1) # 0.1 = tenth of a second
        # Initialise variables here:
        self.latest_position = "0 0"
        # ----
        return

    def tock (self, data):
        # This function is called periodically. Here is where you check the sensors or adjust the motor settings, etc.
        # Don't try to do too much - there may be more important things being added to the queue... 
        print ('tock: latest position = ' + self.latest_position)
        client.publish (addr_car_xy, self.latest_position)
        # ----
        return True

    def event (self, name, value):
        # This is probably a command relayed from the human controller, but is certainly more urgent than tock()
        print ('event: name=' + name + ', value=' + value)
        if name == addr_dash_xy:
            self.latest_position = value
        # ----
        return True

# ======== DO NOT TOUCH ANYTHING BELOW THIS LINE ========

    def command (self, name, value):
        self.queue_controller.event (name, value)
        return

    def stop (self):
        self.queue_controller.stop ()
        return

    def run (self):
        self.queue_controller.run ()
        return

# MQTT callbacks

def on_connect (client, car, rc):
    print ("MQTT: on_connect: response code = " + str (rc))
    client.subscribe (addr_sys_exit)
    client.subscribe (addr_dash_xy)

def on_message (client, car, msg):
    print ("topic [" + msg.topic + "] -> data [" + msg.payload + "]")
    if msg.topic == addr_sys_exit:
        if msg.payload == "car":
            car.stop ()
    else:
        car.command (msg.topic, msg.payload)

if __name__ == "__main__":
    car = car_controller ()

    client = mqtt.Client (client_id='car', clean_session=True, userdata=car, protocol=mqtt.MQTTv31)
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect (mqtt_server_host, mqtt_server_port, 60) # ping once a minute
    client.loop_start ()

    car.run ()
