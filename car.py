from datetime import datetime
import threading
import numpy as np

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
        if name == 'circle_blue_xy':
            t = datetime.now().microsecond / 1000000.0
            cx = (1 + np.cos (t * 2 * np.pi)) * 200 + 50
            cy = (1 + np.sin (t * 2 * np.pi)) * 200 + 50
            response = str (cx) + ',' + str (cy)
# ----
        print ('query: ' + response)
        return response

# ======== DO NOT TOUCH ANYTHING BELOW THIS LINE ========

    def command (self, name, value):
        if name == 'stop':
            self.queue_controller.quit ()
        else:
            self.queue_controller.event (name, value)

        response = ''
        return response

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
