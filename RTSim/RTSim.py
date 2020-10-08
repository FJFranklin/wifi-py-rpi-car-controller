import datetime

import numpy as np
from numpy import linalg as LA

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
#import matplotlib.lines as mlines
from matplotlib.collections import PatchCollection

class RTSim(object):

    # Public Methods:

    def __init__(self, seconds, test_name, id_number):
        self.__result = {}
        self.__result['ID']    = id_number
        self.__result['Trial'] = test_name

        self.__barrier_no = id_number
        self.__trial_type = test_name

        self.__timeStart = None
        self.__timeCurrent = 0

        self.__position   = np.zeros((2, 3))
        self.__speed      = np.zeros((3, 2))
        self.__target     = np.zeros(2)

        self.__pingTime   = np.ones((2)) * -100
        self.__pingAngle  = np.zeros((3))

        # For plotting sonar hits
        self.__pingPoints = np.zeros((100, 2))
        self.__pingCount  = 0
        self.__pingMax    = 100

        # For plotting path of robot
        self.__posPoints  = np.zeros((100, 2))
        self.__posCount   = 0
        self.__posMax     = 100

        self.__watchGapX  = [-2.75, 3.20]

        print(self.__trial_type)
        if self.__trial_type == 'default':
            # Default barriers
            self.__barriers = (
                ( -5.05, -5.00,  0.05, 10.0  ),
                ( -5.00,  5.00, 10.0,   0.05 ),
                ( -5.00, -5.05, 10.0,   0.05 ),
                (  5.00, -5.00,  0.05, 10.0  ),
                ( -3.00, -3.00,  0.05,  8.0  ),
                (  2.95, -5.00,  0.05,  8.0  ),
                ( -1.00, -0.10,  2.00,  0.2  )
            )
            # Default start (top-left), looking North
            self.__position[0,0:2] = [-4.5, 4.5]
            self.__position[0,2]   = 0
            # Default end (bottom-right)
            self.__target[0:2]     = [ 4.5,-4.5]

        elif self.__trial_type == 'random':
            self.reset_barriers()
            par = np.random.uniform(0,1,(4))
            self.__position[0,2]   = float(np.random.randint(360))
            self.__position[0,0:2] = -4.75 + [0.5,9.5] * par[0:2]
            self.__target[0:2]     =  4.75 - [0.5,9.5] * par[2:4]

        else:
            self.reset_barriers(self.__barrier_no)
            if self.__trial_type == 'TNT':      # Top-North-Top
                self.__position[0,2]   = 0
                self.__position[0,0:2] = [-4.5, 4.5]
                self.__target[0:2]     = [ 4.5, 4.5]
            elif self.__trial_type == 'CWC':    # Center-West-Center
                self.__position[0,2]   = 270
                self.__position[0,0:2] = [-4.5, 0]
                self.__target[0:2]     = [ 4.5, 0]
            else: # self.__trial_type == 'BSB': # Bottom-South-Bottom
                self.__position[0,2]   = 180
                self.__position[0,0:2] = [-4.5,-4.5]
                self.__target[0:2]     = [ 4.5,-4.5]

        self.__update_position()

        self.__create_figure()
        self.__update_figure()

        # Reset the clock for start of simulation
        self.__timeStart = datetime.datetime.now()

        self.setup()

        lastMicros = 0
        lastMillis = 0
        lastSecond = 0

        count_ms = 0
        count_20 = 0

        # Finish when target is reached
        while LA.norm(self.__position[0,0:2] - self.__target) > 0.5:
            thisMicros = self.micros()

            thisTime = thisMicros / 1000000
            if thisTime > seconds: # timeout
                break

            if lastMicros < thisMicros: # periodic motion update
                lastMicros = thisMicros
                self.__update_motion()

                if self.__position[0,0] > self.__watchGapX[0]:
                    if 'Gap 1' not in self.__result:
                        self.__result['Gap 1'] = thisTime
                        print('Gap 1 passed @', thisTime)
                if self.__position[0,0] > self.__watchGapX[1]:
                    if 'Gap 2' not in self.__result:
                        self.__result['Gap 2'] = thisTime
                        print('Gap 2 passed @', thisTime)

            if self.__pingTime[0] > self.__pingTime[1]:
                if thisTime - self.__pingTime[0] > 0.04: # % 40ms after send
                    self.__pingTime[1] = thisTime
                    self.__ping_calculate()

            thisMillis = self.millis()
            if lastMillis < thisMillis:
                count_ms = count_ms + (thisMillis - lastMillis)
                self.__update_servos(False, thisMillis - lastMillis) # % servo-actual updates only
                lastMillis = thisMillis

                if count_ms >= 20:
                    while count_ms >= 20:
                        count_20 = count_20 + 1
                        count_ms = count_ms - 20

                    self.__update_servos(True, 0) # servo-target updates only every 20ms

                    if count_20 >= 5:
                        count_20 = count_20 - 5
                        if self.__fig is not None:
                            self.__update_figure() # update figure every 0.1s

            if lastSecond < int(thisTime): # update measured position
                lastSecond = int(thisTime)
                self.__update_position()

                if self.__posCount == self.__posMax:
                    self.__posMax = self.__posMax + 100
                    self.__posPoints = np.resize(self.__posPoints, (self.__posMax, 2))
                self.__posPoints[self.__posCount,:] = self.__position[0,0:2]
                self.__posCount = self.__posCount + 1

            self.loop()

        # Check to see if we're here because the course completed:
        if LA.norm(self.__position[0,0:2] - self.__target) <= 0.5:
            thisTime = self.millis() / 1000
            print('Success! Course completed in ', thisTime, 's', sep='')
            self.__result['Time'] = thisTime

    def get_target(self):
        return np.copy(self.__target)

    def new_target(self):
        self.__target = self.__position[0,0:2]
        while LA.norm(self.__position[0,0:2] - self.__target) < 3:
            self.__target = np.random.uniform(-4.5, 4.5, (2))
        return np.copy(self.__target)

    def new_position(self):
        self.__position[0,0:2] = self.__target
        while (LA.norm(self.__position[0,0:2] - self.__target) < 3) or not self.__position_valid(self.__position[0,0:2]):
            par = np.random.uniform(0,1,(3))
            self.__position[0,0:2] = -4.5 + 9 * par[0:2]
            self.__position[0,2] = 359 * par[2]
        self.__update_position()

    def reset_barriers(self, seed=None):
        if seed is not None:
            # Reset random number generator from seed provided
            np.random.seed(seed)
        else:
            # Reset random number generator from system clock
            t = datetime.datetime.now()
            np.random.seed(t.microsecond)

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
        self.__barriers = (
            (-5.05,     -5.00,    0.05,     10.00),
            (-5.00,      5.00,   10.00,      0.05),
            (-5.00,     -5.05,   10.00,      0.05),
            ( 5.00,     -5.00,    0.05,     10.00),
            ( b1x,       b1y2,    0.05,      5.00-b1y2),
            ( b1x,      -5.00,    0.05,      b1y1-(-5.00)),
            ( b2x,       b2y2,    0.05,      5.00-b2y2),
            ( b2x,      -5.00,    0.05,      b2y1-(-5.00)),
            ( b3x2-0.05, b3y-2,   0.05,      2.0),
            ( b3x1,      b3y+0.2, 0.05,      2.0),
            ( b3x1,      b3y,     b3x2-b3x1, 0.2)
        )

    def micros(self):
        ut = 0
        if self.__timeStart:
            dt = datetime.datetime.now() - self.__timeStart
            ut = dt.seconds * 1000000 + dt.microseconds
        return ut

    def millis(self):
        return int(self.micros() / 1000)

    def set_wheel_speeds(self, left, right):
        limit = 127 # ~~~~ This is the line to change the maximum speed of the robot ~~~~
        if left < -limit:
            left = -limit
        elif left > limit:
            left = limit
        else:
            left = int(left + 0.5)

        if right < -limit:
            right = -limit
        elif right > limit:
            right = limit
        else:
            right = int(right + 0.5)

        self.__speed[0,:] = [left, right]

    def set_ping_angle(self, angle):
        while angle >= 360:
            angle = angle - 360
        while angle < 0:
            angle = angle + 360

        self.__pingAngle[0] = int(angle + 0.5)

    def ping_send(self):
        thisTime = self.micros() / 1000000
        if thisTime - self.__pingTime[0] >= 0.1: # 100 milliseconds
            self.__pingTime[0] = thisTime

    def get_GPS(self):
        return self.__position[1,0:2]

    def get_compass(self):
        return self.__position[1,2]

    def get_result(self):
        return self.__result

    # Private Methods:

    def __update_motion(self):
        thisTime = self.micros() / 1000000
        dt = thisTime - self.__timeCurrent
        self.__timeCurrent = thisTime

        speed_l = self.__speed[2,0] / 508 # -0.25..0.25m/s
        speed_r = self.__speed[2,1] / 508 # -0.25..0.25m/s

        pos = np.copy(self.__position[0,0:2])
        ori = self.__position[0,2] * np.pi / 180 # convert to radians from compass degrees

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

        if self.__position_valid(pos):
            self.__position[0,0:2] = pos

            # Convert back to degrees and confine to 0-359
            ori = ori * 180 / np.pi
            while ori >= 360:
                ori = ori - 360
            while ori < 0:
                ori = ori + 360

            self.__position[0,2] = ori
        else:
            self.__speed[2,0:2] = [0, 0]

    def __update_servos(self, bTargetUpdate, steps):
        if bTargetUpdate:
            self.__speed[1,:] = self.__speed[0,:]
            self.__pingAngle[1] = self.__pingAngle[0]
        else:
            while steps:
                if self.__speed[2,0] > self.__speed[1,0]:
                    self.__speed[2,0] = self.__speed[2,0] - 0.25
                if self.__speed[2,0] < self.__speed[1,0]:
                    self.__speed[2,0] = self.__speed[2,0] + 0.25
                if self.__speed[2,1] > self.__speed[1,1]:
                    self.__speed[2,1] = self.__speed[2,1] - 0.25
                if self.__speed[2,1] < self.__speed[1,1]:
                    self.__speed[2,1] = self.__speed[2,1] + 0.25

                pingDiff = self.__pingAngle[2] - self.__pingAngle[1]
                if pingDiff:
                    if ((pingDiff >= 0) and (pingDiff <= 180)) or (pingDiff <= -180):
                        self.__pingAngle[2] = self.__pingAngle[2] - 0.25
                        if self.__pingAngle[2] < 0:
                            self.__pingAngle[2] = 359
                    else:
                        self.__pingAngle[2] = self.__pingAngle[2] + 0.25
                        if self.__pingAngle[2] > 359:
                            self.__pingAngle[2] = 0

                steps = steps - 1

    def __call__(self, event): # sometimes helps - FIXME
        self.__fig = None

    def __create_figure(self):
        xsize = 1500
        ysize = 1500
        dpi_osx = 192 # Something very illogical here.
        self.__fig = plt.figure(figsize=(xsize / dpi_osx, ysize / dpi_osx), dpi=(dpi_osx/2))
        self.__fig.canvas.mpl_connect('close_event', self)

        self.__ax = self.__fig.add_subplot(111)
        self.__ax.set_position([0.07, 0.06, 0.90, 0.90])
        self.__ax.set_facecolor('white')

        plt.ion()
        plt.show()

    def __update_figure(self):
        self.__ax.cla () # clear everything

        patches = []

        # The barriers
        for b in self.__barriers:
            x, y, w, h = b
            barrier = mpatches.Rectangle((x, y), w, h, edgecolor='black', facecolor='lightblue')
            patches.append(barrier)

        # The target
        x = self.__target[0]
        y = self.__target[1]

        target = mpatches.Circle((x, y), radius=0.3, edgecolor='red', facecolor='white')
        patches.append(target)

        # The robot
        x = self.__position[0,0]
        y = self.__position[0,1]

        robot = mpatches.Circle((x, y), radius=0.2, edgecolor='black', facecolor='lightcoral')
        patches.append(robot)

        ori = self.__position[0,2] # clockwise from North in degrees

        wheel = np.asarray([[0.09,-0.1],[0.09,0.1],[0.13,0.1],[0.13,-0.1]])
        patches.append(self.__draw_poly(wheel, ori, None, 'blue'))
        wheel = np.asarray([[-0.13,-0.1],[-0.13,0.1],[-0.09,0.1],[-0.09,-0.1]])
        patches.append(self.__draw_poly(wheel, ori, None, 'blue'))

        arrow = np.asarray([[0,0.2],[0.09,0],[-0.09,0]])
        patches.append(self.__draw_poly(arrow, ori, None, 'black'))

        # The sonar beam
        ori = ori + self.__pingAngle[2]
        sonar = np.asarray([[0,0],[-0.05,1],[0.05,1]])
        patches.append(self.__draw_poly(sonar, ori, None, 'red'))

        self.__ax.add_collection(PatchCollection(patches, match_original=True))

        # Record of movement and sonar hits
        if self.__pingCount:
            self.__ax.scatter(self.__pingPoints[0:self.__pingCount,0], self.__pingPoints[0:self.__pingCount,1], marker='*', color='red')
        if self.__posCount:
            self.__ax.scatter(self.__posPoints[0:self.__posCount,0], self.__posPoints[0:self.__posCount,1], marker='^', color='black')

        # Show time in the corner
        time_str = 'Time: ' + str(self.millis() / 1000)
        plt.text(4.7, 4.7, time_str, horizontalalignment='right', color='black')

        # and finally...
        self.__ax.set_xlim([-5.1, 5.1])
        self.__ax.set_ylim([-5.1, 5.1])
        plt.draw()
        plt.pause(0.000001)

    def __draw_poly(self, vertices, angle, edge_color, face_color):
        cos_a =  np.cos(angle * np.pi / 180)
        sin_a = -np.sin(angle * np.pi / 180)
        X = self.__position[0,0] + vertices[:,0] * cos_a - vertices[:,1] * sin_a
        Y = self.__position[0,1] + vertices[:,0] * sin_a + vertices[:,1] * cos_a
        vertices[:,0] = X
        vertices[:,1] = Y
        return mpatches.Polygon(vertices, True, edgecolor=edge_color, facecolor=face_color)

    def __update_position(self): # update measured position
        self.__position[1,0] = int(self.__position[0,0] * 100 + 0.5) / 100
        self.__position[1,1] = int(self.__position[0,1] * 100 + 0.5) / 100
        self.__position[1,2] = int(self.__position[0,2] + 0.5)
        if self.__position[1,2] == 360:
            self.__position[1,2] = 0

    def __ping_calculate(self):
        angle = 90 - (self.__position[0,2] + self.__pingAngle[2])
        while angle < 0:
            angle = angle + 360
        angle = angle * np.pi / 180

        dirvec = np.asarray([np.cos(angle), np.sin(angle)])
        pos = self.__position[0,0:2]

        line = np.zeros((4))

        closest_distance = -1
        closest_point = [0,0]

        for b in self.__barriers:
            x, y, w, h = b

            line[0:4] = [x, y, x+w, y]
            distance, point = self.__intersection(pos, dirvec, line);
            if (distance >= 0) and ((closest_distance < 0) or (distance < closest_distance)): # we have an intersection
                closest_distance = distance
                closest_point = point

            line[0:4] = [x, y, x, y+h]
            distance, point = self.__intersection(pos, dirvec, line)
            if (distance >= 0) and ((closest_distance < 0) or (distance < closest_distance)): # we have an intersection
                closest_distance = distance
                closest_point = point

            line[0:4] = [x+w, y+h, x, y+h]
            distance, point = self.__intersection(pos, dirvec, line)
            if (distance >= 0) and ((closest_distance < 0) or (distance < closest_distance)): # we have an intersection
                closest_distance = distance
                closest_point = point

            line[0:4] = [x+w, y+h, x+w, y]
            distance, point = self.__intersection(pos, dirvec, line)
            if (distance >= 0) and ((closest_distance < 0) or (distance < closest_distance)): # we have an intersection
                closest_distance = distance
                closest_point = point

        if closest_distance >= 0:
            if self.__pingCount == self.__pingMax:
                self.__pingMax = self.__pingMax + 100
                self.__pingPoints = np.resize(self.__pingPoints, (self.__pingMax, 2))
            self.__pingPoints[self.__pingCount,:] = closest_point
            self.__pingCount = self.__pingCount + 1
            closest_distance = int(int(closest_distance * 100 + 0.5) / 100)

        self.ping_receive(closest_distance)

    def __intersection(self, pos, dirvec, line):
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

    def __position_valid(self, pos):
        bValidity = True

        line = np.zeros((4))
        dirvec = np.zeros((2))

        for b in self.__barriers:
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
            distance, _point = self.__intersection(pos, dirvec, line)
            if (distance >= 0) and (distance < 0.2): # we have an intersection
                bValidity = False
                break

            line[0:4] = [x,y,x,y+h]
            if x >= pos[0]:
                dirvec[0:2] = [1,0]
            else:
                dirvec[0:2] = [-1,0]
            distance, _point = self.__intersection(pos, dirvec, line)
            if (distance >= 0) and (distance < 0.2): # we have an intersection
                bValidity = False
                break

            line[0:4] = [x+w,y+h,x,y+h]
            if y + h >= pos[1]:
                dirvec[0:2] = [0,1]
            else:
                dirvec[0:2] = [0,-1]
            distance, _point = self.__intersection(pos, dirvec, line)
            if (distance >= 0) and (distance < 0.2): # we have an intersection
                bValidity = False
                break

            line[0:4] = [x+w,y+h,x+w,y]
            if x + w >= pos[0]:
                dirvec[0:2] = [1,0]
            else:
                dirvec[0:2] = [-1,0]
            distance, _point = self.__intersection(pos, dirvec, line)
            if (distance >= 0) and (distance < 0.2): # we have an intersection
                bValidity = False
                break

        return bValidity
