import math
import platform
import datetime

from typing import List

import numpy as np
import matplotlib.pyplot as __plt

OUTPUT = 0
INPUT = 1

LOW = 0
HIGH = 1

LED_BUILTIN = 13

A0 = 14
A1 = 15
A2 = 16
A3 = 17
A4 = 18
A5 = 19

class Stream(object):
    def __init__(self):
        self.baud = None

    def begin(self, baud: int):
        self.baud = baud

    def print(self, *args): # This won't work in Python 2
        print(*args, end='')

    def println(self, *args):
        print(*args)

Serial = Stream()

__timeStart = datetime.datetime.now()

__pin_mode = [OUTPUT] * 14
__pin_state = [LOW] * 14

__ax = None

__servo_patch = None

def servo_redraw(angle=0):
    if __ax is None: # The window has been closed
        return

    ro =   14
    ra =   70
    ox = 1485
    oy =  439

    global __servo_patch
    if __servo_patch is None:
        s = 0
        c = 1
        xy = np.asarray([ [ox+ra*c,oy-ra*s], [ox-ro*s,oy-ro*c], [ox+ro*s,oy+ro*c] ])
        __servo_patch = __plt.Polygon(xy, True, edgecolor=None, facecolor='w')
        __ax.add_patch(__servo_patch)

    if not Servo.locked():
        s = math.sin(math.radians(angle))
        c = math.cos(math.radians(angle))
        xy = np.asarray([ [ox+ra*c,oy-ra*s], [ox-ro*s,oy-ro*c], [ox+ro*s,oy+ro*c] ])
        __servo_patch.set_xy(xy)

class Servo(object):
    __servos: List['Servo'] = []

    __servo_target = 0
    __servo_actual = 0

    __servo_locked = True

    @staticmethod
    def locked():
        return Servo.__servo_locked

    @staticmethod
    def __redraw():
        Servo.__servo_locked = False
        servo_redraw(Servo.__servo_actual)
        Servo.__servo_locked = True

    @staticmethod
    def update(bMajor):
        if bMajor:
            for s in Servo.__servos:
                if s.pin == 3:
                    Servo.__servo_target = s.angle
                    break
        else:
            for s in Servo.__servos:
                if s.pin == 3:
                    if Servo.__servo_actual > Servo.__servo_target:
                        if Servo.__servo_actual - Servo.__servo_target > 4:
                            Servo.__servo_actual -= 4
                        else:
                            Servo.__servo_actual -= 1
                        Servo.__redraw()
                    elif Servo.__servo_actual < Servo.__servo_target:
                        if Servo.__servo_target - Servo.__servo_actual > 4:
                            Servo.__servo_actual += 4
                        else:
                            Servo.__servo_actual += 1
                        Servo.__redraw()
                    break

    def __init__(self):
        self.pin = -1
        self.angle = 0

        Servo.__servos.append(self)

    def attach(self, pin: int):
        if pin >= 0 and pin < 14:
            self.pin = pin

    def attached(self):
        return self.pin != -1

    def detach(self):
        if self.pin != -1:
            self.pin = -1

    def writeMicroseconds(self, us):
        if isinstance(us, int):
            if us < 1005:
                us = 1005
            if us > 1995:
                us = 1995
            self.angle = 90 + int(2 * (us - 1500) / 11)

    def write(self, angle):
        if isinstance(angle, int):
            if angle < 0:
                angle = 0
            if angle > 180:
                angle = 180
            self.angle = angle

    def read(self):
        return self.angle

def __pinSetState(pin, state):
    if __pin_mode[pin] == INPUT:
        __pin_state[pin] = state

__ledB_patch = None
__led8_patch = None
__led9_patch = None

def __ledB(state):
    if __ax is None: # The window has been closed
        return

    if state:
        rgb = (1.0, 1.0, 0)
    else:
        rgb = (0.3, 0.3, 0)

    global __ledB_patch
    if __ledB_patch is None:
        __ledB_patch = __plt.Rectangle((579, 525), 16, 20, fill=True, edgecolor=None, facecolor=rgb)
        __ax.add_patch(__ledB_patch)
    else:
        __ledB_patch.set_facecolor(rgb)

def __led8(state):
    if __ax is None: # The window has been closed
        return

    if state:
        rgb = (0,   0, 1.0)
    else:
        rgb = (0,   0, 0.3)

    global __led8_patch
    if __led8_patch is None:
        __led8_patch = __plt.Circle((1005, 763), 20, fill=True, edgecolor='k', facecolor=rgb)
        __ax.add_patch(__led8_patch)
    else:
        __led8_patch.set_facecolor(rgb)

def __led9(state):
    if __ax is None: # The window has been closed
        return

    if state:
        rgb = (0, 1.0,   0)
    else:
        rgb = (0, 0.3,   0)

    global __led9_patch
    if __led9_patch is None:
        __led9_patch = __plt.Circle((1005, 679), 20, fill=True, edgecolor='k', facecolor=rgb)
        __ax.add_patch(__led9_patch)
    else:
        __led9_patch.set_facecolor(rgb)


__button1_bbox = [ 978, 205, 54, 54, 20 ]
__button2_bbox = [ 978, 290, 54, 54, 20 ]
__button1_patch = None
__button2_patch = None
__button1_highlight = False
__button2_highlight = False
__button1_active = False
__button2_active = False

def __button_check(event):
    b = None

    if __ax is None: # The window has been closed
        return b

    inv = __ax.transData.inverted()
    x, y = inv.transform((event.x, event.y))
    #print('({ex} -> {x}, {ey} -> {y})'.format(x=x, y=y, ex=event.x, ey=event.y))

    global __button1_highlight
    __button1_highlight = False
    if x >= __button1_bbox[0] and x < __button1_bbox[0] + __button1_bbox[2] and y >= __button1_bbox[1] and y < __button1_bbox[1] + __button1_bbox[3]:
        b = 1
        __button1_highlight = True

    global __button2_highlight
    __button2_highlight = False
    if x >= __button2_bbox[0] and x < __button2_bbox[0] + __button2_bbox[2] and y >= __button2_bbox[1] and y < __button2_bbox[1] + __button2_bbox[3]:
        b = 2
        __button2_highlight = True

    return b

def __button1():
    if __ax is None: # The window has been closed
        return

    global __button1_highlight
    if __button1_highlight:
        edge_rgb = 'k'
    else:
        edge_rgb = 'w'

    global __button1_active
    if __button1_active:
        face_rgb = 'g'
    else:
        face_rgb = 'r'

    global __button1_patch
    if __button1_patch is None:
        __button1_patch = __plt.Rectangle((__button1_bbox[0], __button1_bbox[1]), __button1_bbox[2], __button1_bbox[3], fill=True, edgecolor=edge_rgb, facecolor=face_rgb)
        __ax.add_patch(__button1_patch)
        __ax.add_patch(__plt.Circle((__button1_bbox[0] + __button1_bbox[2]/2, __button1_bbox[1] + __button1_bbox[3]/2), __button1_bbox[4], fill=True, edgecolor=None, facecolor='k'))
    else:
        __button1_patch.set_edgecolor(edge_rgb)
        __button1_patch.set_facecolor(face_rgb)

def __button2():
    if __ax is None: # The window has been closed
        return

    global __button2_highlight
    if __button2_highlight:
        edge_rgb = 'k'
    else:
        edge_rgb = 'w'

    global __button2_active
    if __button2_active:
        face_rgb = 'g'
    else:
        face_rgb = 'r'

    global __button2_patch
    if __button2_patch is None:
        __button2_patch = __plt.Rectangle((__button2_bbox[0], __button2_bbox[1]), __button2_bbox[2], __button2_bbox[3], fill=True, edgecolor=edge_rgb, facecolor=face_rgb)
        __ax.add_patch(__button2_patch)
        __ax.add_patch(__plt.Circle((__button2_bbox[0] + __button2_bbox[2]/2, __button2_bbox[1] + __button2_bbox[3]/2), __button2_bbox[4], fill=True, edgecolor=None, facecolor='k'))
    else:
        __button2_patch.set_edgecolor(edge_rgb)
        __button2_patch.set_facecolor(face_rgb)

def __button_reset():
    global __button1_highlight
    __button1_highlight = False

    global __button1_active
    __button1_active = False

    __button1()

    global __button2_highlight
    __button2_highlight = False

    global __button2_active
    __button2_active = False

    __button2()

def __mouse_press(event):
    b = __button_check(event)

    if b == 1:
        global __button1_active
        if __button1_active:
            __button1_active = False
            __pinSetState(12, LOW)
        else:
            __button1_active = True
            __pinSetState(12, HIGH)

    if b == 2:
        global __button2_active
        if __button2_active:
            __button2_active = False
            __pinSetState(11, LOW)
        else:
            __button2_active = True
            __pinSetState(11, HIGH)

    __button1()
    __button2()

def __mouse_move(event):
    __button_check(event)
    __button1()
    __button2()

def __mouse_leave(_event):
    global __button1_highlight
    __button1_highlight = False
    __button1()

    global __button2_highlight
    __button2_highlight = False
    __button2()

def __close(_event):
    #print('close event received')
    global __ax
    __ax = None

__tref = 0
__last = 0
def __sync():
    if __ax is None:
        return

    now = millis()

    global __tref
    if now - __tref > 19:
        __tref = now
        Servo.update(True)  # major update

    global __last
    if now > __last:
        __last = now
        Servo.update(False) # minor update

    __plt.draw()
    __plt.pause(0.00001)

def delay(ms):
    if __ax is None:
        return

    start = millis()

    while True:
        __sync()
        if millis() - start >= ms:
            break

def ArduinoSim(setup, loop):
    fig = __plt.figure()
    fig.canvas.mpl_connect('close_event', __close)

    fig.canvas.mpl_connect('button_press_event',   __mouse_press)
    fig.canvas.mpl_connect('motion_notify_event',  __mouse_move)
    fig.canvas.mpl_connect('axes_leave_event',     __mouse_leave)

    global __ax
    __ax = fig.add_subplot(111)
    __ax.set_position([0, 0, 1, 1])

    img = __plt.imread("ArduinoSim.png")
    __ax.imshow(img)

    __ledB(LOW)
    __led8(LOW)
    __led9(LOW)

    __button_reset()

    servo_redraw()

    __plt.ion()
    __plt.show()

    global __timeStart
    __timeStart = datetime.datetime.now()

    setup()
    while __ax is not None:
        loop()
        __sync()

def micros():
    dt = datetime.datetime.now() - __timeStart
    return dt.seconds * 1000000 + dt.microseconds

def millis():
    return int(micros() / 1000)

def pinMode(pin: int, mode):
    if pin >= 0 and pin < 14:
        if mode:
            __pin_mode[pin] = INPUT
        else:
            __pin_mode[pin] = OUTPUT

def map(x, from_lo, from_hi, to_lo, to_hi):
    return int(to_lo + ((to_hi - to_lo) * (x - from_lo)) / (from_hi - from_lo))

def analogRead(pin: int):
    if pin < A0 or pin > A5:
        return 0
    return micros() & 1023

def digitalRead(pin: int):
    state = LOW
    if pin >= 0 and pin < 14:
        state = __pin_state[pin]
    return state

def digitalWrite(pin: int, state):
    if pin >= 0 and pin < 14:
        if __pin_mode[pin] == OUTPUT:
            old_state = __pin_state[pin]
            if state:
                new_state = HIGH
            else:
                new_state = LOW
            if new_state != old_state:
                __pin_state[pin] = new_state
                if pin == 8:
                    __led8(new_state)
                if pin == 9:
                    __led9(new_state)
                if pin == LED_BUILTIN:
                    __ledB(new_state)
