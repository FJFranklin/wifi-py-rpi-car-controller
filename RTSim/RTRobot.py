import numpy as np

from RTSim import RTSim

class RTRobot(RTSim):
    def __init__(self, seconds):
        # usage: RTRobot (seconds)
        RTSim.__init__(self, seconds)

    def setup(self):
        # setup() is called once at the beginning

        # For example:
        self.set_wheel_speeds(-127, -126)
        self.journey_step = 1
        self.last_ping_time = 0
        self.last_ping_distance = -1

        self.set_ping_angle(-180)

        self.target = self.get_target()
        # or, for a more challenging exercise, get a random target:
        # self.target = self.new_target()

    def loop(self):
        # loop() is called repeatedly

        # For example:
        currentTime = self.millis() / 1000

        if currentTime > 4:
            self.ping_send() # it won't actually send more often than every 0.1s

        if self.journey_step == 1:
            self.set_wheel_speeds(-127, -126)

        elif self.journey_step == 2:
            self.set_wheel_speeds(-10, 10)
            orientation = self.get_compass()
            if orientation > 180 and orientation < 270:
                self.journey_step = 3
                print('Step 3')

        elif self.journey_step == 3:
            orientation = self.get_compass()
            if orientation >= 235:
                self.set_wheel_speeds(-127, -120)
            else:
                self.set_wheel_speeds(-120, -127)

        elif self.journey_step == 4:
            self.set_wheel_speeds(-10, 10)
            orientation = self.get_compass()
            self.set_ping_angle(450-orientation)
            if orientation < 190:
                self.journey_step = 5
                print('Step 5')

        elif self.journey_step == 5:
            orientation = self.get_compass()
            self.set_ping_angle(450-orientation)
            if self.last_ping_distance < 0:
                self.journey_step = 6
                print('Step 6')
            elif self.last_ping_distance < 0.5:
                self.set_wheel_speeds(-127, -125)
            elif self.last_ping_distance > 0:
                self.set_wheel_speeds(-125, -127)

        elif self.journey_step == 6:
            self.set_wheel_speeds(-60, -80)
            orientation = self.get_compass()
            self.set_ping_angle(450-orientation)
            if orientation < 90:
                self.journey_step = 7
                print('Step 7')

        elif self.journey_step == 7:
            vector = self.get_GPS() - self.target
            ori = self.get_compass()
            aim = 90 - np.arctan2(vector[1],vector[0]) * 180 / np.pi
            dtheta = aim - ori
            while dtheta > 180:
                dtheta = dtheta - 360
            while dtheta <= -180:
                dtheta = dtheta + 360
            if dtheta > 0:
                self.set_wheel_speeds(-120, -127)
            else:
                self.set_wheel_speeds(-127, -120)

        else:
            self.set_wheel_speeds(0, 0) # halt

    def ping_receive(self, distance):
        self.last_ping_time = self.millis()
        self.last_ping_distance = distance

        # response to an obj.ping_send()
        if distance >= 0:
            if self.journey_step == 1:
                self.journey_step = 2
                print('Step 2')
            if self.journey_step == 3:
                self.set_wheel_speeds(-10, -10)
                if distance < 0.5:
                    self.journey_step = 4
                    print('Step 4')

        # For example:
        if False: # distance >= 0:                    # a -ve distance implies nothing seen
            position = self.get_GPS()        # roughly where we are
            orientation = self.get_compass() # which direction we're looking
            print('position=(', position[0], ',', position[1], '), orientation=', orientation, '; distance=', distance, sep='')
