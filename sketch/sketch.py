import math

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.collections import PatchCollection

def DEG(a):
    return math.radians(a)

Q2D_Design_Tolerance = 1E-15

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

    def parallel(self, offset):
        return Q2D_Line(self.start.cartesian_relative(-offset * self.direction.y(), offset * self.direction.x()), self.direction)

    def intersection(self, rhs, offset=0.0, interior=True):
        # First check the lines aren't parallel
        d1 = self.direction
        d2 =  rhs.direction
        det = d2.cross(d1)
        if det == 0: # oops, they are
            return None

        if interior and det > 0:
            p1 = self.parallel(-offset).start
            p2 =  rhs.parallel(-offset).start
        else:
            p1 = self.parallel( offset).start
            p2 =  rhs.parallel( offset).start

        c1 = p1.y() * d1.x() - p1.x() * d1.y()
        c2 = p2.y() * d2.x() - p2.x() * d2.y()
        y = (d1.y() * c2 - d2.y() * c1) / det
        x = (d1.x() * c2 - d2.x() * c1) / det

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

    def project(self, point, opposite=False):
        if opposite:
            v = Q2D_Point.from_to(point, self.center)
        else:
            v = Q2D_Point.from_to(self.center, point)
        return self.center.polar_relative(self.radius, v.theta)

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

    def __append_line_to_line(self, line, transition, kwargs):
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
                self.__append(Q2D_Arc(p1, Q2D_Circle(pi, radius), clockwise))

                self.__append(Q2D_Line(p2, d2))
            else:
                self.__append(Q2D_Line(pi, d2))

    @staticmethod
    def __intersect_circle(lhs, rhs, kwargs=None):
        point = None

        cc = Q2D_Point.from_to(lhs.center, rhs.center)
        if cc.length < lhs.radius + rhs.radius:
            dtheta = math.acos(0.5 * (cc.length + (lhs.radius**2.0 - rhs.radius**2.0) / cc.length) / lhs.radius)

            farside = False
            if kwargs is not None:
                if 'farside' in kwargs:
                    farside = kwargs['farside']

            if farside:
                point = lhs.center.polar_relative(lhs.radius, cc.theta + dtheta)
            else:
                point = lhs.center.polar_relative(lhs.radius, cc.theta - dtheta)

        return point

    @staticmethod
    def __intersect_line(line, circle, kwargs=None):
        point = None
        tangent = False

        midpoint = line.project(circle.center)
        cp = Q2D_Point.from_to(circle.center, midpoint)
        cross = cp.cross(line.direction)

        if abs(cp.length - circle.radius) < Q2D_Design_Tolerance:
            print "tangent: error =", cp.length - circle.radius
            point = midpoint
            tangent = True # check sense
        elif cp.length > circle.radius:
            print "line does not intersect circle; missed by", cp.length - circle.radius
        else: # cp.length < circle.radius:
            print "line intersects circle"
            dv = line.direction.copy()
            dv.length = (circle.radius**2.0 - cp.length**2.0)**0.5

            farside = False
            if kwargs is not None:
                if 'farside' in kwargs:
                    farside = kwargs['farside']

            if farside:
                point = midpoint.vector_relative(dv)
            else:
                point = midpoint.vector_relative(dv.reverse())

        return point, cross, tangent

    def __append_line_to_arc(self, line, transition, kwargs):
        arc = self.current

        # swap the sense of farside:
        if 'farside' in kwargs:
            farside = not kwargs['farside']
        else:
            farside = True
        ikwargs = { 'farside': farside }

        point, cross, tangent = Q2D_Path.__intersect_line(line, arc.circle, ikwargs)
        if transition is None:
            if point is None:
                print 'Unable to add line without transition'
            else:
                print 'Adding line without transition'
                self.__append(Q2D_Line(point, line.direction))
        else:
            if point is not None:
                print 'point = (', point.x(), point.y(), '); cross =', cross, 'tangent =', tangent

            if tangent:
                if (cross > 0.0 and not arc.clockwise) or (cross < 0.0 and arc.clockwise):
                    print 'Adding (tangent) line (without transition)'
                    self.__append(Q2D_Arc(point, arc.circle))
                else:
                    print 'Adding (tangent) line (with counter-sense transition)'
                    o = Q2D_Circle(arc.circle.center, arc.circle.radius + transition)
                    if arc.clockwise:
                        l = line.parallel( transition)
                    else:
                        l = line.parallel(-transition)
                    p, c, t = Q2D_Path.__intersect_line(l, o, ikwargs)
                    #print 'point = (', p.x(), p.y(), '); cross =', c, 'tangent =', t
                    self.__append(Q2D_Arc(arc.circle.project(p), Q2D_Circle(p, transition), clockwise=(not arc.clockwise)))
                    self.__append(Q2D_Line(line.project(p), line.direction))
            elif point is None:
                if (cross > 0.0 and not arc.clockwise) or (cross < 0.0 and arc.clockwise):
                    if transition > arc.circle.radius:
                        o = Q2D_Circle(arc.circle.center, transition - arc.circle.radius)
                        if arc.clockwise:
                            l = line.parallel(-transition)
                        else:
                            l = line.parallel( transition)
                        p, c, t = Q2D_Path.__intersect_line(l, o, ikwargs)
                        if p is not None:
                            print 'Adding line (with co-sense transition)'
                            #print 'point = (', p.x(), p.y(), '); cross =', c, 'tangent =', t
                            self.__append(Q2D_Arc(arc.circle.project(p, True), Q2D_Circle(p, transition), clockwise=arc.clockwise))
                            self.__append(Q2D_Line(line.project(p), line.direction))
                        else:
                            print 'Unable to add line with specified (co-sense) transition; try increasing the transition radius'
                    else:
                        print 'Unable to add line with specified (co-sense) transition; require transition radius > arc radius'
                else:
                    o = Q2D_Circle(arc.circle.center, arc.circle.radius + transition)
                    if arc.clockwise:
                        l = line.parallel( transition)
                    else:
                        l = line.parallel(-transition)
                    p, c, t = Q2D_Path.__intersect_line(l, o, ikwargs)
                    if p is not None:
                        print 'Adding line (with counter-sense transition)'
                        #print 'point = (', p.x(), p.y(), '); cross =', c, 'tangent =', t
                        self.__append(Q2D_Arc(arc.circle.project(p), Q2D_Circle(p, transition), clockwise=(not arc.clockwise)))
                        self.__append(Q2D_Line(line.project(p), line.direction))
                    else:
                        print 'Unable to add line with specified (counter-sense) transition'
            else: # line intersects circle
                if not farside:
                    if transition < arc.circle.radius:
                        o = Q2D_Circle(arc.circle.center, arc.circle.radius - transition)
                        if arc.clockwise:
                            l = line.parallel(-transition)
                        else:
                            l = line.parallel( transition)
                        p, c, t = Q2D_Path.__intersect_line(l, o, ikwargs)
                        if p is not None:
                            print 'Adding line (with co-sense transition)'
                            #print 'point = (', p.x(), p.y(), '); cross =', c, 'tangent =', t
                            self.__append(Q2D_Arc(arc.circle.project(p), Q2D_Circle(p, transition), clockwise=arc.clockwise))
                            self.__append(Q2D_Line(line.project(p), line.direction))
                        else:
                            print 'Unable to add line with specified (co-sense) transition; try increasing the transition radius'
                    else:
                        print 'Unable to add line with specified (co-sense) transition; require transition radius > arc radius'
                else:
                    o = Q2D_Circle(arc.circle.center, arc.circle.radius + transition)
                    if arc.clockwise:
                        l = line.parallel( transition)
                    else:
                        l = line.parallel(-transition)
                    p, c, t = Q2D_Path.__intersect_line(l, o, ikwargs)
                    if p is not None:
                        print 'Adding (counter-sense) arc (with transition)'
                        #print 'point = (', p.x(), p.y(), '); cross =', c, 'tangent =', t
                        self.__append(Q2D_Arc(arc.circle.project(p), Q2D_Circle(p, transition), clockwise=(not arc.clockwise)))
                        self.__append(Q2D_Line(line.project(p), line.direction))

    def __append_arc_to_line(self, arc, transition, kwargs):
        line = self.current

        # don't swap the sense of farside:
        if 'farside' in kwargs:
            farside = kwargs['farside']
        else:
            farside = False
        ikwargs = { 'farside': farside }

        point, cross, tangent = Q2D_Path.__intersect_line(line, arc.circle, ikwargs)
        if transition is None:
            if point is None:
                print 'Unable to add arc without transition'
            else:
                print 'Adding arc without transition'
                self.__append(Q2D_Arc(point, arc.circle))
        else:
            if point is not None:
                print 'point = (', point.x(), point.y(), '); cross =', cross, 'tangent =', tangent

            if tangent:
                if (cross > 0.0 and not arc.clockwise) or (cross < 0.0 and arc.clockwise):
                    print 'Adding (tangent) arc (without transition)'
                    self.__append(Q2D_Arc(point, arc.circle))
                else:
                    print 'Adding (counter-sense tangent) arc (with transition)'
                    o = Q2D_Circle(arc.circle.center, arc.circle.radius + transition)
                    if arc.clockwise:
                        l = line.parallel( transition)
                    else:
                        l = line.parallel(-transition)
                    p, c, t = Q2D_Path.__intersect_line(l, o, ikwargs)
                    #print 'point = (', p.x(), p.y(), '); cross =', c, 'tangent =', t
                    self.__append(Q2D_Arc(line.project(p), Q2D_Circle(p, transition), clockwise=(not arc.clockwise)))
                    self.__append(Q2D_Arc(arc.circle.project(p), arc.circle, clockwise=arc.clockwise))
            elif point is None:
                if (cross > 0.0 and not arc.clockwise) or (cross < 0.0 and arc.clockwise):
                    if transition > arc.circle.radius:
                        o = Q2D_Circle(arc.circle.center, transition - arc.circle.radius)
                        if arc.clockwise:
                            l = line.parallel(-transition)
                        else:
                            l = line.parallel( transition)
                        p, c, t = Q2D_Path.__intersect_line(l, o, ikwargs)
                        if p is not None:
                            print 'Adding (co-sense) arc (with transition)'
                            #print 'point = (', p.x(), p.y(), '); cross =', c, 'tangent =', t
                            self.__append(Q2D_Arc(line.project(p), Q2D_Circle(p, transition), clockwise=arc.clockwise))
                            self.__append(Q2D_Arc(arc.circle.project(p, True), arc.circle, clockwise=arc.clockwise))
                        else:
                            print 'Unable to add (co-sense) arc with specified transition; try increasing the transition radius'
                    else:
                        print 'Unable to add (co-sense) arc with specified transition; require transition radius > arc radius'
                else:
                    o = Q2D_Circle(arc.circle.center, arc.circle.radius + transition)
                    if arc.clockwise:
                        l = line.parallel( transition)
                    else:
                        l = line.parallel(-transition)
                    p, c, t = Q2D_Path.__intersect_line(l, o, ikwargs)
                    if p is not None:
                        print 'Adding (counter-sense) arc (with transition)'
                        #print 'point = (', p.x(), p.y(), '); cross =', c, 'tangent =', t
                        self.__append(Q2D_Arc(line.project(p), Q2D_Circle(p, transition), clockwise=(not arc.clockwise)))
                        self.__append(Q2D_Arc(arc.circle.project(p), arc.circle, clockwise=arc.clockwise))
                    else:
                        print 'Unable to add (counter-sense) arc with specified transition'
            else: # line intersects circle
                if farside:
                    if transition < arc.circle.radius:
                        o = Q2D_Circle(arc.circle.center, arc.circle.radius - transition)
                        if arc.clockwise:
                            l = line.parallel(-transition)
                        else:
                            l = line.parallel( transition)
                        p, c, t = Q2D_Path.__intersect_line(l, o, ikwargs)
                        if p is not None:
                            print 'Adding (co-sense) arc (with transition)'
                            #print 'point = (', p.x(), p.y(), '); cross =', c, 'tangent =', t
                            self.__append(Q2D_Arc(line.project(p), Q2D_Circle(p, transition), clockwise=arc.clockwise))
                            self.__append(Q2D_Arc(arc.circle.project(p), arc.circle, clockwise=arc.clockwise))
                        else:
                            print 'Unable to add (co-sense) arc with specified transition; try increasing the transition radius'
                    else:
                        print 'Unable to add (co-sense) arc with specified transition; require transition radius > arc radius'
                else:
                    o = Q2D_Circle(arc.circle.center, arc.circle.radius + transition)
                    if arc.clockwise:
                        l = line.parallel( transition)
                    else:
                        l = line.parallel(-transition)
                    p, c, t = Q2D_Path.__intersect_line(l, o, ikwargs)
                    if p is not None:
                        print 'Adding (counter-sense) arc (with transition)'
                        #print 'point = (', p.x(), p.y(), '); cross =', c, 'tangent =', t
                        self.__append(Q2D_Arc(line.project(p), Q2D_Circle(p, transition), clockwise=(not arc.clockwise)))
                        self.__append(Q2D_Arc(arc.circle.project(p), arc.circle, clockwise=arc.clockwise))

    def __append_arc_to_arc(self, rhs, transition, kwargs):
        lhs = self.current

        # don't swap the sense of farside:
        if 'farside' in kwargs:
            farside = kwargs['farside']
        else:
            farside = False
        if 'co_sense' in kwargs:
            lhs_cosense = kwargs['co_sense']
        else:
            lhs_cosense = True

        if lhs.clockwise == rhs.clockwise:
            rhs_cosense = lhs_cosense
        else:
            rhs_cosense = not lhs_cosense

        lhs_invert = False
        if lhs_cosense:
            clockwise = lhs.clockwise
            if transition < lhs.circle.radius:
                lhs_o = Q2D_Circle(lhs.circle.center, lhs.circle.radius - transition)
            else:
                lhs_invert = True
                lhs_o = Q2D_Circle(lhs.circle.center, transition - lhs.circle.radius)
        else:
            clockwise = not lhs.clockwise
            lhs_o = Q2D_Circle(lhs.circle.center, transition + lhs.circle.radius)

        rhs_invert = False
        if rhs_cosense:
            if transition < rhs.circle.radius:
                rhs_o = Q2D_Circle(rhs.circle.center, rhs.circle.radius - transition)
            else:
                rhs_invert = True
                rhs_o = Q2D_Circle(rhs.circle.center, transition - rhs.circle.radius)
        else:
            rhs_o = Q2D_Circle(rhs.circle.center, transition + rhs.circle.radius)

        point = Q2D_Path.__intersect_circle(lhs_o, rhs_o, kwargs)

        if point is None:
            print "Unable to intersect arcs"
        else:
            print "Adding arc with transition"
            lhs_point = lhs.circle.project(point, lhs_invert)
            rhs_point = rhs.circle.project(point, rhs_invert)
            self.__append(Q2D_Arc(lhs_point, Q2D_Circle(point, transition), clockwise=clockwise))
            self.__append(Q2D_Arc(rhs_point, rhs.circle, clockwise=rhs.clockwise))

    def append(self, line_or_arc, transition=None, **kwargs):
        if self.current.name == "Line":
            if line_or_arc.name == "Line":
                self.__append_line_to_line(line_or_arc, transition, kwargs)
            elif line_or_arc.name == "Arc":
                self.__append_arc_to_line(line_or_arc, transition, kwargs)
        elif self.current.name == "Arc":
            if line_or_arc.name == "Line":
                self.__append_line_to_arc(line_or_arc, transition, kwargs)
            elif line_or_arc.name == "Arc":
                self.__append_arc_to_arc(line_or_arc, transition, kwargs)

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
            p1 = arc.chain
            if p1.name != "Point":
                p1 = p1.start
            p2 = arc.start
        else:
            p1 = arc.start
            p2 = arc.chain
            if p2.name != "Point":
                p2 = p2.start
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

origin = Q2D_Point((0.0, 0.0))

pstart = Q2D_Point((-3.0, 7.5))
lstart = Q2D_Line(pstart, Q2D_Vector(0.0))
path = Q2D_Path(lstart)

circle = Q2D_Circle(Q2D_Point((-2.0, 7.0)), 0.4)
arc = Q2D_Arc(origin, circle, clockwise=False)
path.append(arc, transition=0.1, farside=False)
path.append(lstart.parallel(-1.0), transition=0.5, farside=False)

circle = Q2D_Circle(Q2D_Point((-1.0, 6.5)), 0.4)
arc = Q2D_Arc(origin, circle, clockwise=False)
path.append(arc, transition=0.1, farside=True)
path.append(Q2D_Line(Q2D_Point((-0.9, 6.5)), Q2D_Vector(DEG(270.0))), transition=0.1, farside=True)

circle = Q2D_Circle(Q2D_Point((-1.0, 5.0)), 0.4)
arc = Q2D_Arc(origin, circle, clockwise=False)
path.append(arc, transition=0.1, farside=True)
path.append(Q2D_Line(Q2D_Point((-1.0, 6.5)), Q2D_Vector(DEG( 90.0))), transition=0.1, farside=True)

circle = Q2D_Circle(Q2D_Point((-1.0, 6.5)), 0.4)
arc = Q2D_Arc(origin, circle, clockwise=False)
path.append(arc, transition=0.1, farside=True)
path.append(lstart.parallel(-0.9), transition=0.1, farside=True)

circle = Q2D_Circle(Q2D_Point((0.0, 7.0)), 0.4)
arc = Q2D_Arc(origin, circle, clockwise=True)
path.append(arc, transition=0.1, farside=False)
path.append(lstart, transition=0.5, farside=False)

circle = Q2D_Circle(Q2D_Point((3.0, 5.0)), 2.0)
point0 = circle.point_on_circumference(DEG(270.0))
arc = Q2D_Arc(point0, circle, clockwise=True)
path.append(arc, transition=2.35, farside=True)

point1 = Q2D_Point((0.5, 5.0))
point2 = Q2D_Point((0.0, 2.0))
path.append(Q2D_Line(point1, Q2D_Vector(DEG(270.0))), 0.35, farside=True)
path.append(Q2D_Line(point2, Q2D_Vector(DEG(150.0))), 1.0)
path.append(Q2D_Line(origin, Q2D_Vector(DEG(315.0))), 0.5)
path.append(Q2D_Line(origin, Q2D_Vector(DEG(  0.0))))

circle = Q2D_Circle(Q2D_Point((4.0, 0.5)), 1.5)
arc = Q2D_Arc(point0, circle, clockwise=True)
path.append(arc, transition=0.5, farside=True)

point3 = Q2D_Point((0.0, 2.0))
path.append(Q2D_Line(point3, Q2D_Vector(DEG(180.0))), 0.25, farside=False)
path.end_point(point3)

plotter = Q2D_Plotter([-4,6], [-2,8])
plotter.draw(path)

point = Q2D_Point((-2.0, -1.5))
arc_1 = Q2D_Arc(point, Q2D_Circle(Q2D_Point((-2.0, -1.0)), 0.5), clockwise=True)
arc_2 = Q2D_Arc(point, Q2D_Circle(Q2D_Point((-3.0,  4.0)), 0.5), clockwise=True)
arc_3 = Q2D_Arc(point, Q2D_Circle(Q2D_Point((-3.25, 1.0)), 0.5), clockwise=False)
path2 = Q2D_Path(arc_1)
path2.append(arc_2, transition=4.5, farside=True,  co_sense=False)
path2.append(arc_3, transition=2.5, farside=False, co_sense=True)
path2.append(arc_1, transition=3.5, farside=False, co_sense=False)
path2.end_point(point)
plotter.draw(path2)

plotter.show()
