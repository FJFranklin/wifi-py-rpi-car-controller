from datetime import datetime
import threading

import server
import ticktock

def run_queue (queue_controller): # DO NOT TOUCH
    queue_controller.run ()
    return

# It is possible to create a separate thread dedicated to checking the sensors, which might send events when necessary.
# I have no idea how to stream the camera. That will probably need to be handled in server.py, though.

class car_controller (object):
    def __init__ (self):
        self.queue_controller = ticktock.qController (self, 0.5) # 0.5 = half a second, which is quite slow; try 0.05, maybe
# Initialise variables here:

# ----
        return

    def tock (self, data):
# This function is called periodically. Here is where you check the sensors or adjust the motor settings, etc.
# Don't try to do too much - there may be more important things being added to the queue... 
        print ('tock')
        self.queue_controller.event ('ping!')
# ----
        return True

    def event (self, name, value):
# This is probably a command relayed from the human controller, but is certainly more urgent than tock()
        print (name)
# ----
        return True

    def query (self, name, value):
        response = ''
# This is a request from the human interface
# IMPORTANT: Do not change any local variables! This is a request for information, not a request for action.
        if name == 'circles':
            if value == 'blue_xy':
                t_now = datetime.now ()
                cx = (((t_now.second %  6) + t_now.microsecond / 1000000.0) - 3) / 3
                cy = (((t_now.second % 10) + t_now.microsecond / 1000000.0) - 5) / 5
                cx = cx * 200 + 250
                cy = cy * 200 + 250
                response = str (cx) + ',' + str (cy)
        if name == 'clock':
            if value == 'time':
                t_now = datetime.now ()
                c_s = -6 * t_now.second
                c_m = -6 * t_now.minute - t_now.second / 10
                c_h = 360 - 30 * t_now.hour - t_now.minute / 2
                response = str (c_h) + ',' + str (c_m) + ',' + str (c_s)
# ----
        print ('query: ' + response)
        return response

# ======== DO NOT TOUCH ANYTHING BELOW THIS LINE ========

    def command (self, name, value):
        self.queue_controller.event (name, value)
        return

    def stop (self):
        self.queue_controller.stop ()
        return

    def run_in_background (self):
        t = threading.Thread (target=run_queue, args=(self.queue_controller,))
        t.start ()
        return

if __name__ == "__main__":
    C = car_controller ()
    C.run_in_background ()
    S = server.global_server ()
    S.set_handler (C)
    S.run ()
