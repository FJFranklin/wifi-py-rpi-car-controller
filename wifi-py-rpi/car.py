import paho.mqtt.client as mqtt
import time
import sys

mqtt_server_host = "192.168.99.234"
mqtt_server_port = 1883

addr_sys_exit = "/wifi-py-rpi-car-controller/system/exit"
addr_car_xy   = "/wifi-py-rpi-car-controller/car/XY"
addr_dash_xy  = "/wifi-py-rpi-car-controller/dash/XY"

latest_position = "0 0"

def on_connect (client, userdata, rc):
    print ("Connected, response code = " + str (rc))
    client.subscribe (addr_sys_exit)
    client.subscribe (addr_dash_xy)

def on_message (client, userdata, msg):
    global latest_position
    print ("topic [" + msg.topic + "] -> data [" + msg.payload + "]")
    if msg.topic == addr_sys_exit:
        if msg.payload == "car":
            sys.exit ()
    if msg.topic == addr_dash_xy:
        latest_position = msg.payload

client = mqtt.Client (client_id='car', clean_session=True, userdata=None, protocol=mqtt.MQTTv31)
client.on_connect = on_connect
client.on_message = on_message

client.connect (mqtt_server_host, mqtt_server_port, 60) # ping once a minute
client.loop_start ()

while True:
    client.publish (addr_car_xy, latest_position)
    time.sleep (0.1)
