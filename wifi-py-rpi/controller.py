import paho.mqtt.client as mqtt
import sys

mqtt_server_host = "127.0.0.1"
mqtt_server_port = 1883

addr_sys_exit = "/wifi-py-rpi-car-controller/system/exit"

def on_connect (client, userdata, rc):
    print ("Connected, response code = " + str (rc))
    client.subscribe (addr_sys_exit)

def on_message (client, userdata, msg):
    print ("topic [" + msg.topic + "] -> data [" + msg.payload + "]")
    if msg.topic == addr_sys_exit:
        if msg.payload == "controller":
            sys.exit ()

client = mqtt.Client (client_id='controller', clean_session=True, userdata=None, protocol=mqtt.MQTTv31)
client.on_connect = on_connect
client.on_message = on_message

client.connect (mqtt_server_host, mqtt_server_port, 60)
client.loop_forever ()
