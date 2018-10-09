import datetime

import numpy as np
from numpy import linalg as LA

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
#import matplotlib.lines as mlines
from matplotlib.collections import PatchCollection

class RTSim(object):

    # Public Methods:

    def __init__(self, seconds):
        self._timeStart = None
        self._timeCurrent = 0

        self._position   = np.zeros((2, 3))
        self._speed      = np.zeros((3, 2))

        self._pingTime   = np.ones((2)) * -100
        self._pingAngle  = np.zeros((3))

        # For plotting sonar hits
        self._pingPoints = np.zeros((100, 2))
        self._pingCount  = 0
        self._pingMax    = 100

        # For plotting path of robot
        self._posPoints  = np.zeros((100, 2))
        self._posCount   = 0
        self._posMax     = 100

        # Default barriers
        self._barriers = (
            ( -5.05, -5.00,  0.05, 10    ),
            ( -5.00,  5.00, 10,     0.05 ),
            ( -5.00, -5.05, 10,     0.05 ),
            (  5.00, -5.00,  0.05, 10    ),
            ( -3.00, -3.00,  0.05,  8    ),
            (  2.95, -5.00,  0.05,  8    ),
            ( -1.00, -0.10,  2.00,  0.2  )
        )

        # Default start (top-left)
        self._position[0,0:2] = [-4.5, 4.5]
        self._position[1,0:2] = self._position[0,0:2]

        # Default end (bottom-right)
        self._target = np.asarray((4.5, -4.5))

        self._create_figure()
        self._update_figure()

        # Reset the clock for start of simulation
        self._timeStart = datetime.datetime.now()

        self.setup()

        lastMicros = 0
        lastMillis = 0
        lastSecond = 0

        count_ms = 0
        count_20 = 0

        # Finish when target is reached
        while LA.norm(self._position[0,0:2] - self._target) > 0.5:
            thisMicros = self.micros()

            thisTime = thisMicros / 1000000
            if thisTime > seconds: # timeout
                break

            if lastMicros < thisMicros: # periodic motion update
                lastMicros = thisMicros
                self._update_motion()

            if self._pingTime[0] > self._pingTime[1]:
                if thisTime - self._pingTime[0] > 0.04: # % 40ms after send
                    self._pingTime[1] = thisTime
                    self._ping_calculate()

            thisMillis = self.millis()
            if lastMillis < thisMillis:
                count_ms = count_ms + (thisMillis - lastMillis)
                self._update_servos(False, thisMillis - lastMillis) # % servo-actual updates only
                lastMillis = thisMillis

                if count_ms >= 20:
                    while count_ms >= 20:
                        count_20 = count_20 + 1
                        count_ms = count_ms - 20

                    self._update_servos(True, 0) # servo-target updates only every 20ms

                    if count_20 >= 5:
                        count_20 = count_20 - 5
                        self._update_figure() # update figure every 0.1s

            if lastSecond < int(thisTime): # update measured position
                lastSecond = int(thisTime)
                self._update_position()

                if self._posCount == self._posMax:
                    self._posMax = self._posMax + 100
                    self._posPoints = np.resize(self._posPoints, (self._posMax, 2))
                self._posPoints[self._posCount,:] = self._position[0,0:2]
                self._posCount = self._posCount + 1

            self.loop()

        # Check to see if we're here because the course completed:
        if LA.norm(self._position[0,0:2] - self._target) <= 0.5:
            print('Success! Course completed in ', self.millis() / 1000, 's', sep='')

    def get_target(self):
        return np.copy(self._target)

    def new_target(self):
        self._target = self._position[0,0:2]
        while LA.norm(self._position[0,0:2] - self._target) < 3:
            self._target = np.random.uniform(-4.5, 4.5, (1,2))
        return np.copy(self._target)

    def reset_barriers(self, seed):
        # Reset random number generator from seed provided
        np.random.seed(seed)
        # Generate a set of barriers
        par  = np.random.uniform(0,1,(7))
        b1x  = -3.5 + par[0]
        b1y1 = -4 + 2 * par[1]
        b1y2 = b1y1 + 1
        b2x  = 2.5 + par[2]
        b2y2 = 4 - 2 * par[3]
        b2y1 = b2y2 - 1
        b3x1 = b1x + 1 + par[4]
        b3x2 = b2x - 1 - par[5]
        b3y  = -1 + 2 * par[6]
        self._barriers = (
            (-5.05,     -5.00,    0.05,     10.00),
            (-5.00,      5.00,   10.00,      0.05),
            (-5.00,     -5.05,   10.00,      0.05),
            ( 5.00,     -5.00,    0.05,     10.00),
            ( b1x,       b1y2,    0.05,      5.00-b1y2),
            ( b1x,      -5.00,    0.05,      b1y1-(-5.00)),
            ( b2x,       b2y2,    0.05,      5.00-b2y2),
            ( b2x,      -5.00,    0.05,      b2y1-(-5.00)),
            ( b3x2-0.05, b3y-2,   0.05,      2),
            ( b3x1,      b3y+0.2, 0.05,      2),
            ( b3x1,      b3y,     b3x2-b3x1, 0.2)
        )
        # Reset random number generator from system clock
        t = datetime.datetime.now()
        np.random.seed(t.microsecond)
        # Reset initial position
        par = np.random.uniform(0, 1, (3))
        self._position[0,2] = 359 * par[0]
        self._position[0,1] = -4.5 + 9 * par[1]
        self._position[0,0] = -4.5
        self._position[1,:] = self._position[0,:]
        # Reset target
        self._target[0] =  4.5
        self._target[1] = -4.5 + 9 * par[2]

    def micros(self):
        ut = 0
        if self._timeStart:
            dt = datetime.datetime.now() - self._timeStart
            ut = dt.seconds * 1000000 + dt.microseconds
        return ut

    def millis(self):
        return int(self.micros() / 1000)

    def set_wheel_speeds(self, left, right):
        if left < -127:
            left = -127
        elif left > 127:
            left = 127
        else:
            left = int(left + 0.5)

        if right < -127:
            right = -127
        elif right > 127:
            right = 127
        else:
            right = int(right + 0.5)

        self._speed[0,:] = [left, right]

    def set_ping_angle(self, angle):
        while angle >= 360:
            angle = angle - 360
        while angle < 0:
            angle = angle + 360

        self._pingAngle[0] = int(angle + 0.5)

    def ping_send(self):
        thisTime = self.micros() / 1000000
        if thisTime - self._pingTime[0] >= 0.1: # 100 milliseconds
            self._pingTime[0] = thisTime

    def get_GPS(self):
        return self._position[1,0:2]

    def get_compass(self):
        return self._position[1,2]

    # Private Methods:

    def _update_motion(self):
        thisTime = self.micros() / 1000000
        dt = thisTime - self._timeCurrent
        self._timeCurrent = thisTime

        speed_l = self._speed[2,0] / 508 # -0.25..0.25m/s
        speed_r = self._speed[2,1] / 508 # -0.25..0.25m/s

        pos = np.copy(self._position[0,0:2])
        ori = self._position[0,2] * np.pi / 180 # convert to radians from compass degrees

        if speed_l == speed_r:
            dir = np.asarray([np.sin(ori), np.cos(ori)])
            pos = pos + dir * speed_l * dt
        elif speed_l + speed_r == 0:
            ang_speed = speed_l / 0.1 # clockwise
            theta = ang_speed * dt    # radians
            # So new position & orientation:
            ori = ori + theta
        else:
            # Vector to wheel from robot centre
            wheel = 0.1 * np.asarray([np.cos(ori), -np.sin(ori)])
            # Centre of motion
            gamma = (speed_l + speed_r) / (speed_l - speed_r)
            centre = pos + gamma * wheel
            # Radius of motion
            radius = gamma / 10
            # Tangential & angular speed of robot centred at pos
            av_speed = (speed_l + speed_r) / 2
            ang_speed = av_speed / radius # radians/s - clockwise
            # Movement, therefore:
            theta = ang_speed * dt # radians
            # So new position & orientation:
            ori = ori + theta
            vec = pos - centre
            cos_theta = np.cos(theta)
            sin_theta = np.sin(theta)
            vec[:] = [vec[0] * cos_theta + vec[1] * sin_theta, -vec[0] * sin_theta + vec[1] * cos_theta]
            pos = centre + vec

        if self._position_valid(pos):
            self._position[0,0:2] = pos

            # Convert back to degrees and confine to 0-359
            ori = ori * 180 / np.pi
            while ori >= 360:
                ori = ori - 360
            while ori < 0:
                ori = ori + 360

            self._position[0,2] = ori
        else:
            self._speed[2,0:2] = [0, 0]

    def _update_servos(self, bTargetUpdate, steps):
        if bTargetUpdate:
            self._speed[1,:] = self._speed[0,:]
            self._pingAngle[1] = self._pingAngle[0]
        else:
            while steps:
                if self._speed[2,0] > self._speed[1,0]:
                    self._speed[2,0] = self._speed[2,0] - 0.25
                if self._speed[2,0] < self._speed[1,0]:
                    self._speed[2,0] = self._speed[2,0] + 0.25
                if self._speed[2,1] > self._speed[1,1]:
                    self._speed[2,1] = self._speed[2,1] - 0.25
                if self._speed[2,1] < self._speed[1,1]:
                    self._speed[2,1] = self._speed[2,1] + 0.25

                pingDiff = self._pingAngle[2] - self._pingAngle[1]
                if pingDiff:
                    if ((pingDiff >= 0) and (pingDiff <= 180)) or (pingDiff <= -180):
                        self._pingAngle[2] = self._pingAngle[2] - 0.25
                        if self._pingAngle[2] < 0:
                            self._pingAngle[2] = 359
                    else:
                        self._pingAngle[2] = self._pingAngle[2] + 0.25
                        if self._pingAngle[2] > 359:
                            self._pingAngle[2] = 0

                steps = steps - 1

    def _create_figure(self):
        xsize = 1500
        ysize = 1500
        dpi_osx = 192 # Something very illogical here.
        self._fig = plt.figure(figsize=(xsize / dpi_osx, ysize / dpi_osx), dpi=(dpi_osx/2))

        self._ax = self._fig.add_subplot(111)
        self._ax.set_position([0.07, 0.06, 0.90, 0.90])
        self._ax.set_facecolor('white')

        plt.ion()
        plt.show()

    def _update_figure(self):
        self._ax.cla () # clear everything

        patches = []

        # The barriers
        for b in self._barriers:
            x, y, w, h = b
            barrier = mpatches.Rectangle((x, y), w, h, edgecolor='black', facecolor='lightblue')
            patches.append(barrier)

        # The target
        x = self._target[0]
        y = self._target[1]

        target = mpatches.Circle((x, y), radius=0.3, edgecolor='red', facecolor='white')
        patches.append(target)

        # The robot
        x = self._position[0,0]
        y = self._position[0,1]

        robot = mpatches.Circle((x, y), radius=0.2, edgecolor='black', facecolor='lightcoral')
        patches.append(robot)

        ori = self._position[0,2] # clockwise from North in degrees

        wheel = np.asarray([[0.09,-0.1],[0.09,0.1],[0.13,0.1],[0.13,-0.1]])
        patches.append(self._draw_poly(wheel, ori, None, 'blue'))
        wheel = np.asarray([[-0.13,-0.1],[-0.13,0.1],[-0.09,0.1],[-0.09,-0.1]])
        patches.append(self._draw_poly(wheel, ori, None, 'blue'))

        arrow = np.asarray([[0,0.2],[0.09,0],[-0.09,0]])
        patches.append(self._draw_poly(arrow, ori, None, 'black'))

        # The sonar beam
        ori = ori + self._pingAngle[2]
        sonar = np.asarray([[0,0],[-0.05,1],[0.05,1]])
        patches.append(self._draw_poly(sonar, ori, None, 'red'))

        self._ax.add_collection(PatchCollection(patches, match_original=True))

        # Record of movement and sonar hits
        if self._pingCount:
            self._ax.scatter(self._pingPoints[0:self._pingCount,0], self._pingPoints[0:self._pingCount,1], marker='*', color='red')
        if self._posCount:
            self._ax.scatter(self._posPoints[0:self._posCount,0], self._posPoints[0:self._posCount,1], marker='^', color='black')

        # Show time in the corner
        time_str = 'Time: ' + str(self.millis() / 1000)
        plt.text(4.7, 4.7, time_str, horizontalalignment='right', color='black')

        # and finally...
        self._ax.set_xlim([-5.1, 5.1])
        self._ax.set_ylim([-5.1, 5.1])
        plt.draw()
        plt.pause(0.000001)

    def _draw_poly(self, vertices, angle, edge_color, face_color):
        cos_a =  np.cos(angle * np.pi / 180)
        sin_a = -np.sin(angle * np.pi / 180)
        X = self._position[0,0] + vertices[:,0] * cos_a - vertices[:,1] * sin_a
        Y = self._position[0,1] + vertices[:,0] * sin_a + vertices[:,1] * cos_a
        vertices[:,0] = X
        vertices[:,1] = Y
        return mpatches.Polygon(vertices, True, edgecolor=edge_color, facecolor=face_color)

    def _update_position(self): # update measured position
        self._position[1,0] = int(self._position[0,0] * 100 + 0.5) / 100
        self._position[1,1] = int(self._position[0,1] * 100 + 0.5) / 100
        self._position[1,2] = int(self._position[0,2] + 0.5)
        if self._position[1,2] == 360:
            self._position[1,2] = 0

    def _ping_calculate(self):
        angle = 90 - (self._position[0,2] + self._pingAngle[2])
        while angle < 0:
            angle = angle + 360
        angle = angle * np.pi / 180

        dirvec = np.asarray([np.cos(angle), np.sin(angle)])
        pos = self._position[0,0:2]

        line = np.zeros((4))

        closest_distance = -1
        closest_point = [0,0]

        for b in self._barriers:
            x, y, w, h = b

            line[0:4] = [x, y, x+w, y]
            distance, point = self._intersection(pos, dirvec, line);
            if (distance >= 0) and ((closest_distance < 0) or (distance < closest_distance)): # we have an intersection
                closest_distance = distance
                closest_point = point

            line[0:4] = [x, y, x, y+h]
            distance, point = self._intersection(pos, dirvec, line)
            if (distance >= 0) and ((closest_distance < 0) or (distance < closest_distance)): # we have an intersection
                closest_distance = distance
                closest_point = point

            line[0:4] = [x+w, y+h, x, y+h]
            distance, point = self._intersection(pos, dirvec, line)
            if (distance >= 0) and ((closest_distance < 0) or (distance < closest_distance)): # we have an intersection
                closest_distance = distance
                closest_point = point

            line[0:4] = [x+w, y+h, x+w, y]
            distance, point = self._intersection(pos, dirvec, line)
            if (distance >= 0) and ((closest_distance < 0) or (distance < closest_distance)): # we have an intersection
                closest_distance = distance
                closest_point = point

        if closest_distance >= 0:
            if self._pingCount == self._pingMax:
                self._pingMax = self._pingMax + 100
                self._pingPoints = np.resize(self._pingPoints, (self._pingMax, 2))
            self._pingPoints[self._pingCount,:] = closest_point
            self._pingCount = self._pingCount + 1
            closest_distance = int(closest_distance * 100 + 0.5) / 100

        self.ping_receive(closest_distance)

    def _intersection(self, pos, dirvec, line):
        distance = -1 # -ve distance => no intersection
        point = np.zeros((2))

        # lines are horizontal or vertical
        if (line[0] == line[2]) and dirvec[0]: # vertical
            t = (line[0] - pos[0]) / dirvec[0]
            if (t >= 0) and (t <= 1):
                s = (t * dirvec[1] - (line[1] - pos[1])) / (line[3] - line[1])
                if (s >= 0) and (s <= 1): # valid intersection
                    point = t * dirvec + pos
                    distance = t

        if (line[1] == line[3]) and dirvec[1]: # horizontal
            t = (line[1] - pos[1]) / dirvec[1]
            if (t >= 0) and (t <= 1):
                s = (t * dirvec[0] - (line[0] - pos[0])) / (line[2] - line[0])
                if (s >= 0) and (s <= 1): # valid intersection
                    point = t * dirvec + pos
                    distance = t

        return distance, point

    def _position_valid(self, pos):
        bValidity = True

        line = np.zeros((4))
        dirvec = np.zeros((2))

        for b in self._barriers:
            x, y, w, h = b

            # discard barriers that are obviously too far away
            if x - pos[0] > 0.2:
                continue
            if pos[0] - (x + w) > 0.2:
                continue
            if y - pos[1] > 0.2:
                continue
            if pos[1] - (y + h) > 0.2:
                continue

            # Check corners first
            if LA.norm(pos - [x, y]) < 0.2:
                bValidity = False
                break
            if LA.norm(pos - [x+w, y]) < 0.2:
                bValidity = False
                break
            if LA.norm(pos - [x, y+h]) < 0.2:
                bValidity = False
                break
            if LA.norm(pos - [x+w, y+h]) < 0.2:
                bValidity = False
                break

            # Finally check barrier lines
            line[0:4] = [x, y, x+w, y]
            if y >= pos[1]:
                dirvec[0:2] = [0,1]
            else:
                dirvec[0:2] = [0,-1]
            distance, point = self._intersection(pos, dirvec, line)
            if (distance >= 0) and (distance < 0.2): # we have an intersection
                bValidity = False
                break

            line[0:4] = [x,y,x,y+h]
            if x >= pos[0]:
                dirvec[0:2] = [1,0]
            else:
                dirvec[0:2] = [-1,0]
            distance, point = self._intersection(pos, dirvec, line)
            if (distance >= 0) and (distance < 0.2): # we have an intersection
                bValidity = False
                break

            line[0:4] = [x+w,y+h,x,y+h]
            if y + h >= pos[1]:
                dirvec[0:2] = [0,1]
            else:
                dirvec[0:2] = [0,-1]
            distance, point = self._intersection(pos, dirvec, line)
            if (distance >= 0) and (distance < 0.2): # we have an intersection
                bValidity = False
                break

            line[0:4] = [x+w,y+h,x+w,y]
            if x + w >= pos[0]:
                dirvec[0:2] = [1,0]
            else:
                dirvec[0:2] = [-1,0]
            distance, point = self._intersection(pos, dirvec, line)
            if (distance >= 0) and (distance < 0.2): # we have an intersection
                bValidity = False
                break

        return bValidity
