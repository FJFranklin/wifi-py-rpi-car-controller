import numpy as np

import matplotlib
matplotlib.use('TkAgg')
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt

import cameratransform as ct

def random_unit_vector():
    norm = 0
    while norm < 1E-15:
        gauss = np.random.normal(0, 1, 3)
        norm  = np.linalg.norm(gauss)
    return gauss / norm
        
def nudge(direction, weight):
    rows, _ = direction.shape
    for row in range(rows):
        new_direction = direction[row,:] * (1 - weight) + weight * random_unit_vector()
        direction[row,:] = new_direction / np.linalg.norm(new_direction)
    return direction

def wrap(coordinate, side):
    if np.isscalar(coordinate):
        if coordinate >= side:
            coordinate -= side
        elif coordinate < 0:
            coordinate += side
        return coordinate

    for index in range(len(coordinate)):
        if coordinate[index] >= side:
            coordinate[index] -= side
        elif coordinate[index] < 0:
            coordinate[index] += side

    return coordinate

def cube_check(xyz, center, radius):
    r = None
    xyz -= center
    if max(abs(xyz)) <= radius:
        r = np.linalg.norm(xyz)
    return r

class Environment(object):
    def __init__(self, cube_side, insect_count:int, show_3D=True):
        self.side = cube_side
        self.N = insect_count
        self.data = np.zeros((self.N, 7))

        self.origin = np.ones(3) * self.side / 2

        # Give each insect a random speed between 0.25 and 1.25 m/s
        self.data[:,0] = np.random.rand(self.N)

        # Give each insect a random initial position
        self.data[:,1:4] = np.random.rand(self.N, 3) * self.side

        for row in range(self.N):
            # Give each insect a random initial direction (unit vector)
            self.data[row,4:7] = random_unit_vector()

        self.ax = None
        if show_3D:
            plt.figure()
            self.ax = plt.axes(projection='3d')

            self.ax.set_xlim(0, self.side)
            self.ax.set_ylim(0, self.side)
            self.ax.set_zlim(0, self.side)

            self.ax.set_xlabel('X')
            self.ax.set_ylabel('Y')
            self.ax.set_zlabel('Z')

            self.points = self.ax.scatter(self.data[:,1], self.data[:,2], self.data[:,3], 'b.')

            plt.show(block=False)

    def subset(self, center, radius):
        insects = []
        for row in range(self.N):
            r = None
            for axis_z in range(-1,2):
                z = self.data[row,3] + self.side * axis_z
                for axis_y in range(-1,2):
                    y = self.data[row,2] + self.side * axis_y
                    for axis_x in range(-1,2):
                        x = self.data[row,1] + self.side * axis_x
                        r = cube_check(np.asarray([x, y, z]), center, radius)
                        if r is not None:
                            break
                    if r is not None:
                        break
                if r is not None:
                    break
            if r is not None:
                if r <= radius:
                    insects.append([x, y, z, r])
        return np.asarray(insects)

    def update(self, dt, **kwargs):
        # update insect positions
        newpos = self.data[:,1:4] + (self.data[:,4:7].T * self.data[:,0]).T * dt
        newpos[:,0] = wrap(newpos[:,0], self.side)
        newpos[:,1] = wrap(newpos[:,1], self.side)
        newpos[:,2] = wrap(newpos[:,2], self.side)
        self.data[:,1:4] = newpos

        # update insect directions
        self.data[:,4:7] = nudge(self.data[:,4:7], dt)

        # update 3D plot, if it was requested & created
        if self.ax is not None:
            self.points._offsets3d = (self.data[:,1], self.data[:,2], self.data[:,3])

            self.ax.figure.canvas.draw_idle()
            self.ax.figure.canvas.flush_events()

class Bird(object):
    def __init__(self, environment, sight_range):
        self.E = environment
        self.sight = sight_range

        self.speed = 10
        self.eaten = 0

        # Camera orientation
        self.heading = 0 # compass direction
        self.tilt = 90   # 0 = vertically down
        self.roll = 0

        # intrinsic camera parameters
        f = 6.2    # in mm
        sensor_size = (5, 5)      # in mm
        image_size = (1000, 1000) # in px

        self.cam = ct.Camera(ct.RectilinearProjection(focallength_mm=f, sensor=sensor_size, image=image_size), ct.SpatialOrientation())

        self.cam.pos_x_m     = self.E.origin[0]
        self.cam.pos_y_m     = self.E.origin[1]
        self.cam.elevation_m = self.E.origin[2]
        self.cam.heading_deg = self.heading
        self.cam.tilt_deg    = self.tilt
        self.cam.roll_deg    = self.roll

        plt.figure()
        self.cax = plt.axes()

        plt.show(block=False)

    def update(self, dt, **kwargs):
        dr = self.speed * dt
        dz = dr * np.sin(np.radians(self.tilt - 90))
        dr = dr * np.cos(np.radians(self.tilt - 90))
        dx = dr * np.cos(np.radians(90 - self.heading))
        dy = dr * np.sin(np.radians(90 - self.heading))

        # update bird positions
        self.cam.pos_x_m     = wrap(self.cam.pos_x_m + dx,     self.E.side)
        self.cam.pos_y_m     = wrap(self.cam.pos_y_m + dy,     self.E.side)
        self.cam.elevation_m = wrap(self.cam.elevation_m + dz, self.E.side)

        # update bird speed (maximum acceleration is 1 m/s2)
        limit = 1 * dt
        if 'speed' in kwargs:
            target_speed = kwargs['speed']
            if target_speed >= 1 and target_speed <= 20 and target_speed != self.speed:
                dv = target_speed - self.speed
                if dv > 0:
                    if dv < limit:
                        self.speed += dv
                    else:
                        self.speed += limit
                else:
                    if -dv < limit:
                        self.speed -= dv
                    else:
                        self.speed -= limit
        # update bird orientation (maximum rotation speed is 30 deg/s)
        limit = 30 * dt
        if 'heading' in kwargs:
            target_heading = kwargs['heading']
            if target_heading >= 0 and target_heading < 360 and target_heading != self.heading:
                angle = target_heading - self.heading
                if angle > 180:
                    angle -= 360
                elif angle < -180:
                    angle += 360
                if angle > 0:
                    if angle < limit:
                        self.heading += angle
                    else:
                        self.heading += limit
                else:
                    if -angle < limit:
                        self.heading -= angle
                    else:
                        self.heading -= limit
                if self.heading >= 360:
                    self.heading -= 360
                elif self.heading < 0:
                    self.heading += 360
                self.cam.heading_deg = self.heading
        if 'tilt' in kwargs:
            target_tilt = kwargs['tilt']
            if target_tilt >= 45 and target_tilt <= 135 and target_tilt != self.tilt:
                angle = target_tilt - self.tilt
                if angle > 0:
                    if angle < limit:
                        self.tilt += angle
                    else:
                        self.tilt += limit
                else:
                    if -angle < limit:
                        self.tilt -= angle
                    else:
                        self.tilt -= limit
                self.cam.tilt_deg = self.tilt

        # plot insects and collect list of target insects
        self.cax.cla()
        self.cax.set_xlim(-1.6, 1.6)
        self.cax.set_ylim(-1.6, 1.6)
        plt.text(-1.5, 1.4, 'Heading:')
        plt.text(-1.5, 1.2, 'Tilt:')
        plt.text(-1.5, 1.0, 'Speed:')
        plt.text(-1.5, 0.8, 'Eaten:')
        plt.text(-1.0, 1.4, '%.1f' % self.heading)
        plt.text(-1.0, 1.2, '%.1f' % self.tilt)
        plt.text(-1.0, 1.0, '%.1f' % self.speed)
        plt.text(-1.0, 0.8, str(self.eaten))

        targets = []
        insects = E.subset(np.asarray([self.cam.pos_x_m, self.cam.pos_y_m, self.cam.elevation_m]), self.sight)
        rows = insects.shape[0]
        for row in range(rows):
            r = insects[row,3] # distance to insect
            if r < self.sight:
                if r < 0.1: # yummy!
                    self.eaten += 1
                p = self.cam.imageFromSpace(insects[row,0:3])
                if not np.isnan(p[0]):
                    m = chr(np.random.randint(49, 53))
                    xy = np.arctan((p-500)/500) # +/- pi/2
                    self.cax.scatter(xy[0], xy[1], s=((25-r)**2), marker=m)
                    targets.append([np.around(xy[0], 2), np.around(xy[1], 2), np.around(r, 2)])

        self.cax.figure.canvas.draw_idle()
        self.cax.figure.canvas.flush_events()

        return np.asarray(targets)

E = Environment(60, 500, show_3D=False)
B = Bird(E, 20)

while True:
    dt = 0.1     # time step
    E.update(dt) # update insect field

    # heading = compass direction 0-359 degrees
    # tilt    = 45 - glide down; 90 - level flight; 135 - soar up
    # speed   = 1 (slowest); 20 (fastest)
    targets = B.update(dt, heading=75, tilt=120, speed=5)
    # targets is a matrix where each row represents an insect and the three columns are X, Y, R,
    # where R is the distance to the insect
    #print(targets)
    plt.pause(0.01)
