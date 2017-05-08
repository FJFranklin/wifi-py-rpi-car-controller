import time
import threading
from Queue import PriorityQueue

qPriorityHigh   = 0
qPriorityNormal = 1
qPriorityLow    = 2

class qData (object):
    def __init__ (self, event_type, data=None):
        self.event_type = event_type
        self.event_data = data
        return

def qController_tick (queue_controller):
    queue_controller.tick ()
    return

class qController (object):
    def __init__ (self, event_handler, timer_interval):
        self.handler = event_handler
        self.timer_interval = timer_interval
        self.TickTock = PriorityQueue ()
        self.lock = threading.Lock ()
        self.bListening = False
        return
        
    def stop (self):
        if self.bListening:
            q = qData ('stop')
            self.TickTock.put ((qPriorityHigh, q))
        return

    def event (self, event_type, data=None):
        if self.bListening:
            q = qData (event_type, data)
            self.TickTock.put ((qPriorityNormal, q))
        return

    def tick (self):
        time.sleep (self.timer_interval)
        if self.bListening:
            q = qData ('tick')
            self.TickTock.put ((qPriorityLow, q))
        return

    def tick_start (self):
        t = threading.Thread (target=qController_tick, args=(self,)) # add a new delayed event to the queue
        t.start ()
        return

    def run (self):
        if not self.lock.acquire (False):
            return False

        # clear the queue, just in case of multiple calls to run()
        while not self.TickTock.empty ():
            try:
                self.TickTock.get (False)
            except Empty:
                continue
            self.TickTock.task_done ()

        self.bListening = True

        self.tick_start ()

        while True:
            p, q = self.TickTock.get ()

            if q.event_type == 'stop':
                break

            if q.event_type == 'tick':
                if self.handler.tock (q.event_data) == False:
                    break
                self.tick_start ()

            elif self.handler.event (q.event_type, q.event_data) == False:
                break

            self.TickTock.task_done ()

        self.bListening = False
        self.lock.release ()
        return True
