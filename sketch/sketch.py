import math

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.collections import PatchCollection

def DEG(a):
    return math.radians(a)

class Q2D_Vector(object):

    @staticmethod
    def from_to(dx, dy): # define vector from xy-components
        length = (dx**2.0 + dy**2.0)**0.5
        return Q2D_Vector(math.atan2(dy, dx), length)

    def __init__(self, theta, length=1.0):
        self.length = length
        self.theta = theta
        self.dx = math.cos(theta)
        self.dy = math.sin(theta)

    def x(self, unit=False): # x-component of vector; optionally as a unit vector
        dx = self.dx
        if not unit:
            dx *= self.length
        return dx

    def y(self, unit=False): # y-component of vector; optionally as a unit vector
        dy = self.dy
        if not unit:
            dy *= self.length
        return dy

    def copy(self, unit=False): # copy the vector; optionally as a unit vector
        length = 1.0
        if not unit:
            length = self.length
        return Q2D_Vector(self.theta, length)

    def rotate(self, phi=None): # in-place rotation; defaults to 90 degrees
        if phi is None: # 90 degree
            self.theta += math.pi / 2
        else:
            self.theta += phi
        while self.theta > math.pi:
            self.theta -= 2.0 * math.pi
        while self.theta < -math.pi:
            self.theta += 2.0 * math.pi
        self.dx = math.cos(self.theta)
        self.dy = math.sin(self.theta)
        return self

    def reverse(self): # in-place reversal
        self.rotate(math.pi)
        return self

    def scale(self, scalar): # in-place scaling
        if scalar < 0:
            self.reverse()
            self.length *= -scalar
        else:
            self.length *= scalar
        return self

    def dot(self, rhs, just_cosine=False): # the dot product, or optionally the cosine of the angle
        cos = self.dx * rhs.dx + self.dy * rhs.dy
        if not just_cosine:
            cos *= self.length * rhs.length
        return cos

    def angle(self, rhs): # the angle between the vectors
        phi = rhs.theta - self.theta
        while phi > math.pi:
            phi -= 2.0 * math.pi
        while phi < -math.pi:
            phi += 2.0 * math.pi
        return phi

    def cross(self, rhs): # normal component of the cross-product
        return self.x() * rhs.y() - self.y() * rhs.x()

    def sum(self, rhs): # new vector = self + rhs
        return Q2D_Vector.from_to(self.x() + rhs.x(), self.y() + rhs.y())

    def difference(self, rhs): # new vector = self - rhs
        return Q2D_Vector.from_to(self.x() - rhs.x(), self.y() - rhs.y())

class Q2D_Object(object):

    def __init__(self, name):
        self.name = name
        self.start = None # starting point of curve
        self.chain = None # next Q2D_Object in chain

class Q2D_Point(Q2D_Object):

    def __init__(self, xy):
        Q2D_Object.__init__(self, "Point")
        self.start = xy

    def x(self):
        return self.start[0]

    def y(self):
        return self.start[1]

    def cartesian_relative(self, dx, dy): # new point displaced from self; cartesian components
        return Q2D_Point((self.start[0] + dx, self.start[1] + dy))

    def polar_relative(self, r, theta): # new point displaced from self; polar components
        x = self.x() + r * math.cos(theta)
        y = self.y() + r * math.sin(theta)
        return Q2D_Point((x, y))

    def vector_relative(self, v): # new point displaced from self by vector v
        return Q2D_Point((self.start[0] + v.x(), self.start[1] + v.y()))

    @staticmethod
    def from_to(from_point, to_point): # define vector between two points
        return Q2D_Vector.from_to(to_point.x() - from_point.x(), to_point.y() - from_point.y())

class Q2D_Line(Q2D_Object):

    def __init__(self, start, direction):
        Q2D_Object.__init__(self, "Line")
        self.start = start
        self.direction = direction

    def intersection(self, rhs, offset=0.0, interior=True):
        # First check the lines aren't parallel
        v1 = self.direction.copy(True).rotate()
        v2 =  rhs.direction.copy(True).rotate()
        det = v2.cross(v1)
        if det == 0: # oops, they are
            return None
        if interior and det > 0:
            v1.reverse()
            v2.reverse()

        p1 = self.start.vector_relative(v1.copy().scale(offset))
        p2 =  rhs.start.vector_relative(v2.copy().scale(offset))
        c1 = p1.x() * v1.x() + p1.y() * v1.y()
        c2 = p2.x() * v2.x() + p2.y() * v2.y()
        y = (v2.x() * c1 - v1.x() * c2) /  det
        x = (v2.y() * c1 - v1.y() * c2) / -det

        return Q2D_Point((x, y))

    def project(self, point):
        rhs = Q2D_Line(point, self.direction.copy().rotate())
        return self.intersection(rhs)

class Q2D_Circle(object):

    def __init__(self, center, radius):
        self.center = center
        self.radius = radius

    def point_on_circumference(self, theta):
        return self.center.polar_relative(self.radius, theta)

    def tangent_in_direction(self, direction):
        p = self.point_on_circumference(direction.theta - math.pi / 2.0)
        return Q2D_Line(p, direction)

class Q2D_Arc(Q2D_Object):

    def __init__(self, start, circle, clockwise=False):
        Q2D_Object.__init__(self, "Arc")
        self.start = start
        self.circle = circle
        self.clockwise = clockwise

class Q2D_Path(object):

    def __init__(self, line_or_arc):
        self.chain = line_or_arc
        self.current = line_or_arc

    def __append(self, line_arc_point):
        self.current.chain = line_arc_point
        self.current = self.current.chain

    def end_point(self, point):
        self.__append(point)

    def __append_line_to_line(self, line, transition):
        radius = 0
        if transition is not None:
            if transition > 0:
                radius = transition

        l1 = self.current
        l2 = line

        d1 = l1.direction
        d2 = l2.direction

        pi = l1.intersection(l2, radius)
        if pi is not None:
            if radius > 0:
                p1 = l1.project(pi)
                p2 = l2.project(pi)

                clockwise = d2.cross(d1) > 0
                #if d2.cross(d1) > 0:
                #    clockwise = True
                #else:
                #    clockwise = False
                self.__append(Q2D_Arc(p1, Q2D_Circle(pi, radius), clockwise))

                self.__append(Q2D_Line(p2, d2))
            else:
                self.__append(Q2D_Line(pi, d2))

    def __append_line_to_arc(self, line, transition):
        if transition is None:
            self.__append(self.current.circle.tangent_in_direction(line.direction))
        else:
            None

    def __append_arc_to_line(self, arc, transition):
        if transition is None:
            self.__append(arc)
        else:
            None

    def __append_arc_to_arc(self, arc, transition):
        None

    def append(self, line_or_arc, transition=None):
        if self.current.name == "Line":
            if line_or_arc.name == "Line":
                self.__append_line_to_line(line_or_arc, transition)
            elif line_or_arc.name == "Arc":
                self.__append_arc_to_line(line_or_arc, transition)
        elif self.current.name == "Arc":
            if line_or_arc.name == "Line":
                self.__append_line_to_arc(line_or_arc, transition)
            elif line_or_arc.name == "Arc":
                self.__append_arc_to_arc(line_or_arc, transition)

class Q2D_Plotter(object):

    def __init__(self, x_range, y_range):
        xsize = 1500
        ysize = 1500
        dpi_osx = 192 # Something very illogical here.
        self._fig = plt.figure(figsize=(xsize / dpi_osx, ysize / dpi_osx), dpi=(dpi_osx/2))

        self._ax = self._fig.add_subplot(111)
        self._ax.set_facecolor('white')
        self._ax.set_position([0.07, 0.06, 0.90, 0.90])

        self._ax.set_xlim(x_range)
        self._ax.set_ylim(y_range)

    def show(self):
        plt.show()

    def __draw_point(self, point, center=False):
        if center:
            marker = '+'
            color = 'green'
        else:
            marker = '.'
            color = 'blue'
        self._ax.scatter(point.start[0], point.start[1], marker=marker, color=color)

    def __draw_circle(self, circle):
        x_axis = 2.0 * circle.radius
        y_axis = 2.0 * circle.radius
        patch = mpatches.Ellipse(circle.center.start, x_axis, y_axis, edgecolor='green', linestyle='--', facecolor=None, fill=False, linewidth=1)
        self._ax.add_patch(patch)
        self.__draw_point(circle.center, True)

    def __draw_arc(self, arc):
        self.__draw_circle(arc.circle)
        if arc.clockwise:
            p1 = arc.chain.start
            p2 = arc.start
        else:
            p1 = arc.start
            p2 = arc.chain.start
        t1 = math.degrees(math.atan2(p1.start[1] - arc.circle.center.start[1], p1.start[0] - arc.circle.center.start[0]))
        t2 = math.degrees(math.atan2(p2.start[1] - arc.circle.center.start[1], p2.start[0] - arc.circle.center.start[0]))
        if t2 < t1:
            t2 += 360.0
        x_axis = 2.0 * arc.circle.radius
        y_axis = 2.0 * arc.circle.radius
        patch = mpatches.Arc(arc.circle.center.start, x_axis, y_axis, theta1=t1, theta2=t2, edgecolor='blue', facecolor=None, fill=False)
        self._ax.add_patch(patch)
        self.__draw_point(arc.circle.center, True)
        self.__draw_point(arc.start)

    def __draw_line(self, line):
        p1 = line.start
        p2 = line.chain
        if p2.name != "Point":
            p2 = p2.start
        self._ax.plot([p1.start[0], p2.start[0]], [p1.start[1], p2.start[1]], '-', color='blue', linewidth=1)
        self.__draw_point(p1)

    def draw(self, path):
        item = path.chain

        while item is not None:
            if item.name == "Line":
                self.__draw_line(item)
            elif item.name == "Arc":
                self.__draw_arc(item)
            else:
                self.__draw_point(item)
            item = item.chain

circle = Q2D_Circle(Q2D_Point((3, 5)), 2)
point = circle.point_on_circumference(DEG(270))
arc = Q2D_Arc(point, circle)
path = Q2D_Path(arc)
origin = Q2D_Point((0, 0))
point2 = Q2D_Point((0, 2))
path.append(Q2D_Line(origin, Q2D_Vector(DEG(270))))
path.append(Q2D_Line(point2, Q2D_Vector(DEG(150))), 1)
path.append(Q2D_Line(origin, Q2D_Vector(DEG(315))), 0.5)
path.end_point(origin)

plotter = Q2D_Plotter([-4,6], [-2,8])
plotter.draw(path)
plotter.show()
