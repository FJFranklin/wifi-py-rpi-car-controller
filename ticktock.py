import time
import threading
from Queue import PriorityQueue

qPriorityHigh   = 0
qPriorityNormal = 1
qPriorityLow    = 2

class qData (object):
    def __init__ (self, event_type, data=None, handler=None):
        self.event_type = event_type
        self.event_data = data
        self.event_handler = handler
        return

def qController_tick (queue_controller):
    queue_controller.tick ()
    return

class qController (object):
    def __init__ (self, default_event_handler, timer_interval):
        self.controller = default_event_handler
        self.timer_interval = timer_interval
        self.TickTock = PriorityQueue ()
        return
        
    def stop (self):
        q = qData ('stop')
        self.TickTock.put ((qPriorityHigh, q))
        return

    def tick (self):
        time.sleep (self.timer_interval)
        q = qData ('tick')
        self.TickTock.put ((qPriorityLow, q))

    def event (self, event_type, data=None, handler=None):
        q = qData (event_type, data, handler)
        if handler is None:
            q.event_handler = self.controller
        self.TickTock.put ((qPriorityNormal, q))

    def run (self):
        t = threading.Thread (target=qController_tick, args=(self,)) # add a delayed event to the queue
        t.start ()

        while True:
            p, q = self.TickTock.get ()

            if q.event_type == 'stop':
                break

            event_handler = q.event_handler

            if q.event_type == 'tick':
                if event_handler is None: # assume this is our local timer
                    if self.controller.tock (q.event_data) == False:
                        break
                    t = threading.Thread (target=qController_tick, args=(self,)) # add a new delayed event to the queue
                    t.start ()
                else: # another ticker wants a tock...
                    if event_handler.tock (q.event_data) == False:
                        break

            elif event_handler is not None:
                if event_handler.event (q.event_type, q.event_data) == False:
                    break

            self.TickTock.task_done ()
        return
