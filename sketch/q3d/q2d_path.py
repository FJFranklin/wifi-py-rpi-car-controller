import math

Q2D_Design_Tolerance = 1E-15 # tolerance for numerical errors

Q2D_Print_Info = False # print info for debugging

# ==== Q2D Arc-Line sketch path classes ==== #

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

    def unit(self):
        self.dx /= self.length
        self.dy /= self.length
        self.length = 1.0
        return self

    def add(self, rhs_vector, rhs_scale=1.0): # new vector = self + rhs_vector * rhs_scale
        return Q2D_Vector(self.x() + rhs_vector.x() * rhs_scale,
                          self.y() + rhs_vector.y() * rhs_scale)

    def sum(self, rhs): # new vector = self + rhs
        return Q2D_Vector.from_to(self.x() + rhs.x(), self.y() + rhs.y())

    def difference(self, rhs): # new vector = self - rhs
        return Q2D_Vector.from_to(self.x() - rhs.x(), self.y() - rhs.y())

class Q2D_Object(object):

    def __init__(self, name, **kwargs):
        self.name = name
        self.props = kwargs
        self.start = None # starting point of curve
        self.chain = None # next Q2D_Object in chain

    @property
    def mesh(self):
        return self.props.get("mesh")

    @mesh.deleter
    def mesh(self):
        self.props.pop("mesh", None)

    @mesh.setter
    def mesh(self, value):
        if value is not None:
            bUpdate = True
            if "mesh" in self.props:
                min_mesh = self.props["mesh"]
                if value >= min_mesh:
                    bUpdate = False
            if bUpdate:
                self.props["mesh"] = value

class Q2D_Point(Q2D_Object):

    def __init__(self, xy, **kwargs):
        Q2D_Object.__init__(self, "Point", **kwargs)
        self.start = xy
        self.__point = None

    def x(self):
        return self.start[0]

    def y(self):
        return self.start[1]

    def point(self):
        if self.__point is None:
            self.__point = Point2D.Create(self.start[0], self.start[1])
        return self.__point

    def cartesian_relative(self, dx, dy): # new point displaced from self; cartesian components
        return Q2D_Point((self.start[0] + dx, self.start[1] + dy))

    def polar_relative(self, r, theta): # new point displaced from self; polar components
        x = self.x() + r * math.cos(theta)
        y = self.y() + r * math.sin(theta)
        return Q2D_Point((x, y))

    def vector_relative(self, v): # new point displaced from self by vector v
        return Q2D_Point((self.start[0] + v.x(), self.start[1] + v.y()))

    def distance(self, p): # distance between points
        return ((self.start[0] - p.x())**2 + (self.start[1] - p.y())**2)**0.5

    @staticmethod
    def from_to(from_point, to_point): # define vector between two points
        return Q2D_Vector.from_to(to_point.x() - from_point.x(), to_point.y() - from_point.y())

class Q2D_Line(Q2D_Object):

    def __init__(self, start, direction, **kwargs):
        Q2D_Object.__init__(self, "Line", **kwargs)
        self.start = start
        self.direction = direction

    def parallel(self, offset, reverse=False):
        if reverse:
            d = self.direction.copy().reverse()
        else:
            d = self.direction
        return Q2D_Line(self.start.cartesian_relative(-offset * self.direction.y(), offset * self.direction.x()), d)

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

    def poly_points(self, interval):
        points = []
        if self.chain is not None:
            p1 = self.start
            p2 = self.chain
            if p2.name != "Point":
                p2 = p2.start

            dx = p2.x() - p1.x()
            dy = p2.y() - p1.y()
            length = math.sqrt(dx**2 + dy**2)

            count = int(math.ceil(length / interval))
            for c in range(0, count):
                x = p1.x() + (dx * c) / count
                y = p1.y() + (dy * c) / count
                points += [[x, y]]

        return points

class Q2D_Ellipse(Q2D_Object):

    def __init__(self, center, semi_major, semi_minor, rotate=0.0, **kwargs):
        Q2D_Object.__init__(self, "Ellipse", **kwargs)
        self.center = center
        self.semi_major  = semi_major
        self.semi_minor  = semi_minor
        self.rotate = rotate
        self.x = Q2D_Vector(rotate)
        self.y = Q2D_Vector(rotate + math.pi / 2)

    # local coordinate system is a unit circle centered at the origin
    def __local_point_to_global(self, lx, ly):
        gx = lx * self.semi_major * self.x.dx + ly * self.semi_minor * self.y.dx
        gy = lx * self.semi_major * self.x.dy + ly * self.semi_minor * self.y.dy
        return self.center.cartesian_relative(gx, gy)

    def __local_angle_to_global(self, theta):
        return math.atan2(math.sin(theta) * self.semi_minor, math.cos(theta) * self.semi_major)

    def __global_angle_to_local(self, theta):
        return math.atan2(math.sin(theta) / self.semi_minor, math.cos(theta) / self.semi_major)

    def point_on_circumference(self, theta):
        theta = self.__global_angle_to_local(theta - self.rotate)
        return self.__local_point_to_global(math.cos(theta), math.sin(theta))

    def project(self, point, opposite=False):
        if opposite:
            v = Q2D_Point.from_to(point, self.center)
        else:
            v = Q2D_Point.from_to(self.center, point)
        return self.point_on_circumference(v.theta)

    def poly_points(self, interval):
        points = []

        theta = 0.0
        while theta < 2 * math.pi:
            point = self.point_on_circumference(theta)
            points += [[point.x(), point.y()]]
            radius = self.center.distance(point)
            theta = theta + interval / radius

        return points

class Q2D_Circle(Q2D_Ellipse):

    def __init__(self, center, radius, **kwargs):
        Q2D_Ellipse.__init__(self, center, radius, radius, **kwargs)
        self.name = "Circle"
        self.radius = radius

    def convert_to_ellipse(self):
        self.name = "Ellipse"

class Q2D_Arc(Q2D_Object):

    def __init__(self, start, circle, clockwise=False, **kwargs):
        Q2D_Object.__init__(self, "Arc", **kwargs)
        self.start = start
        self.circle = circle
        self.clockwise = clockwise

    def center(self):
        return self.circle.center.start

    def Ox(self):
        return self.circle.center.x()

    def Oy(self):
        return self.circle.center.y()

    def concentric(self, offset):
        if self.clockwise:
            offset = -offset
        if self.circle.radius - offset <= 0:
            return None

        v_center = Q2D_Point.from_to(self.start, self.circle.center) # vector pointing inwards
        cc_start = self.start.cartesian_relative(offset * v_center.dx, offset * v_center.dy)

        return Q2D_Arc(cc_start, Q2D_Circle(self.circle.center, self.circle.radius - offset), self.clockwise)

    def poly_points(self, interval):
        points = []
        if self.chain is not None:
            p1 = self.start
            p2 = self.chain
            if p2.name != "Point":
                p2 = p2.start
            t1 = math.atan2(p1.start[1] - self.circle.center.start[1], p1.start[0] - self.circle.center.start[0])
            t2 = math.atan2(p2.start[1] - self.circle.center.start[1], p2.start[0] - self.circle.center.start[0])
            if self.clockwise:
                if t1 <= t2:
                    if t2 > 0:
                        t2 -= 2.0 * math.pi
                    else:
                        t1 += 2.0 * math.pi
                arc_length = (t1 - t2) * self.circle.radius
            else:
                if t2 <= t1:
                    if t2 < 0:
                        t2 += 2.0 * math.pi
                    else:
                        t1 -= 2.0 * math.pi
                arc_length = (t2 - t1) * self.circle.radius

            count = int(math.ceil(arc_length / interval))
            for c in range(0, count):
                point = self.circle.point_on_circumference(t1 + ((t2 - t1) * c) / count)
                points += [[point.x(), point.y()]]

        return points

class Q2D_Path(object):

    @staticmethod
    def polygon(points): # where points = [(x1,y1) .. (xN,yN)], N > 2
        path = None
        if len(points) > 2:
            p0 = Q2D_Point(points[0])
            p1 = p0

            for i in range(1, len(points)):
                p2 = Q2D_Point(points[i])
                line_12 = Q2D_Line(p1, Q2D_Point.from_to(p1, p2))
                if i == 1:
                    path = Q2D_Path(line_12)
                else:
                    path.append(line_12)
                p1 = p2

            line_12 = Q2D_Line(p1, Q2D_Point.from_to(p1, p0))
            path.append(line_12)
            path.end_point(p0)

        return path

    def __init__(self, line_or_arc):
        self.name = "Path"
        self.chain = line_or_arc
        self.current = line_or_arc

    def __append(self, line_arc_point):
        self.current.chain = line_arc_point
        self.current = self.current.chain

    def end_point(self, point):
        self.__append(point)

    def __append_line_to_line(self, line, transition, kwargs):
        lhs_arc  = None
        rhs_line = None

        radius = 0
        if transition is not None:
            if transition > 0:
                radius = transition

        l1 = self.current
        l2 = line

        d1 = l1.direction
        d2 = l2.direction

        pi = l1.intersection(l2, radius)
        if pi is None:
            if Q2D_Print_Info:
                print('Unable to add line to line - no intersection')
        else:
            if radius > 0:
                if Q2D_Print_Info:
                    print('Adding line to line with transition')
                p1 = l1.project(pi)
                p2 = l2.project(pi)

                clockwise = d2.cross(d1) > 0
                lhs_arc  = Q2D_Arc(p1, Q2D_Circle(pi, radius), clockwise)
                rhs_line = Q2D_Line(p2, d2)
            else:
                if Q2D_Print_Info:
                    print('Adding line to line without transition')
                rhs_line = Q2D_Line(pi, d2)

        return lhs_arc, rhs_line

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
    def __intersect_line(line, circle, sense):
        point = None
        tangent = False

        midpoint = line.project(circle.center)
        cp = Q2D_Point.from_to(circle.center, midpoint)
        cross = cp.cross(line.direction)

        if abs(cp.length - circle.radius) < Q2D_Design_Tolerance:
            if Q2D_Print_Info:
                print("tangent: error = {e}".format(e=(cp.length - circle.radius)))
            point = midpoint
            tangent = True # check sense
        elif cp.length > circle.radius:
            if Q2D_Print_Info:
                print("line does not intersect circle; missed by {d}".format(d=(cp.length - circle.radius)))
        else: # cp.length < circle.radius:
            if Q2D_Print_Info:
                print("line intersects circle")
            dv = line.direction.copy()
            dv.length = (circle.radius**2.0 - cp.length**2.0)**0.5

            if sense:
                point = midpoint.vector_relative(dv)
            else:
                point = midpoint.vector_relative(dv.reverse())

        return point, cross, tangent

    def __append_line_to_arc(self, line, transition, kwargs):
        lhs_arc  = None
        rhs_line = None

        arc = self.current

        farside  = kwargs.get('farside',  False)
        co_sense = kwargs.get('co_sense', True)

        #if 'co_sense' in kwargs:
        #    co_sense = kwargs['co_sense']
        #else:
        #    co_sense = True
        #if 'farside' in kwargs:
        #    farside = kwargs['farside']
        #else:
        #    farside = False

        if not arc.clockwise:
            sense = not co_sense
        else:
            sense = co_sense

        point, cross, tangent = Q2D_Path.__intersect_line(line, arc.circle, sense)
        if transition is None:
            if point is None:
                if Q2D_Print_Info:
                    print('Unable to add line without transition')
            else:
                if Q2D_Print_Info:
                    print('Adding line without transition')
                rhs_line = Q2D_Line(point, line.direction)
        else:
            if not arc.clockwise:
                offset = -transition
            else:
                offset = transition

            if point is not None:
                if Q2D_Print_Info:
                    print('point = ({x}, {y}); cross={c}; tangent={t}'.format(x=point.x(), y=point.y(), c=cross, t=tangent))

            if tangent:
                if (cross > 0.0 and not arc.clockwise) or (cross < 0.0 and arc.clockwise):
                    if not co_sense:
                        if Q2D_Print_Info:
                            print('Co-sense transition should be used here')
                else:
                    if co_sense:
                        if Q2D_Print_Info:
                            print('Contra-sense transition should be used here')

                if co_sense:
                    if Q2D_Print_Info:
                        print('Adding (tangent) line (without transition)')
                    rhs_line = Q2D_Line(line.project(point), line.direction)
                else:
                    if Q2D_Print_Info:
                        print('Adding (tangent) line (with counter-sense transition)')
                    o = Q2D_Circle(arc.circle.center, arc.circle.radius + transition)
                    l = line.parallel(offset)
                    p, c, t = Q2D_Path.__intersect_line(l, o, not farside)
                    #print 'point = (', p.x(), p.y(), '); cross =', c, 'tangent =', t
                    lhs_arc  = Q2D_Arc(arc.circle.project(p), Q2D_Circle(p, transition), clockwise=(not arc.clockwise))
                    rhs_line = Q2D_Line(line.project(p), line.direction)
            elif point is None:
                if (cross > 0.0 and not arc.clockwise) or (cross < 0.0 and arc.clockwise):
                    if not co_sense:
                        if Q2D_Print_Info:
                            print('Co-sense transition should be used here')
                else:
                    if co_sense:
                        if Q2D_Print_Info:
                            print('Contra-sense transition should be used here')

                if co_sense:
                    if transition > arc.circle.radius:
                        o = Q2D_Circle(arc.circle.center, transition - arc.circle.radius)
                        l = line.parallel(-offset)
                        p, c, t = Q2D_Path.__intersect_line(l, o, not farside)
                        if p is not None:
                            if Q2D_Print_Info:
                                print('Adding line (with co-sense transition)')
                            #print 'point = (', p.x(), p.y(), '); cross =', c, 'tangent =', t
                            lhs_arc  = Q2D_Arc(arc.circle.project(p, True), Q2D_Circle(p, transition), clockwise=arc.clockwise)
                            rhs_line = Q2D_Line(line.project(p), line.direction)
                        else:
                            if Q2D_Print_Info:
                                print('Unable to add line with specified (co-sense) transition; try increasing the transition radius')
                    else:
                        if Q2D_Print_Info:
                            print('Unable to add line with specified (co-sense) transition; require transition radius > arc radius')
                else:
                    o = Q2D_Circle(arc.circle.center, arc.circle.radius + transition)
                    if arc.clockwise:
                        l = line.parallel( transition)
                    else:
                        l = line.parallel( transition)
                    p, c, t = Q2D_Path.__intersect_line(l, o, not farside)
                    if p is not None:
                        if Q2D_Print_Info:
                            print('Adding line (with counter-sense transition)')
                        #print 'point = (', p.x(), p.y(), '); cross =', c, 'tangent =', t
                        lhs_arc  = Q2D_Arc(arc.circle.project(p), Q2D_Circle(p, transition), clockwise=(not arc.clockwise))
                        rhs_line = Q2D_Line(line.project(p), line.direction)
                    else:
                        if Q2D_Print_Info:
                            print('Unable to add line with specified (counter-sense) transition')
            else: # line intersects circle
                if co_sense:
                    if transition < arc.circle.radius:
                        o = Q2D_Circle(arc.circle.center, arc.circle.radius - transition)
                        l = line.parallel(-offset)
                        p, c, t = Q2D_Path.__intersect_line(l, o, not farside)
                        if p is not None:
                            if Q2D_Print_Info:
                                print('Adding line (with co-sense transition)')
                            #print 'point = (', p.x(), p.y(), '); cross =', c, 'tangent =', t
                            lhs_arc  = Q2D_Arc(arc.circle.project(p), Q2D_Circle(p, transition), clockwise=arc.clockwise)
                            rhs_line = Q2D_Line(line.project(p), line.direction)
                        else:
                            if Q2D_Print_Info:
                                print('Unable to add line with specified (co-sense) transition; try increasing the transition radius')
                    else:
                        if Q2D_Print_Info:
                            print('Unable to add line with specified (co-sense) transition; require transition radius > arc radius')
                else:
                    o = Q2D_Circle(arc.circle.center, arc.circle.radius + transition)
                    l = line.parallel(offset)
                    p, c, t = Q2D_Path.__intersect_line(l, o, not farside)
                    if p is not None:
                        if Q2D_Print_Info:
                            print('Adding (counter-sense) arc (with transition)')
                        #print('point = (', p.x(), p.y(), '); cross =', c, 'tangent =', t)
                        lhs_arc  = Q2D_Arc(arc.circle.project(p), Q2D_Circle(p, transition), clockwise=(not arc.clockwise))
                        rhs_line = Q2D_Line(line.project(p), line.direction)

        return lhs_arc, rhs_line

    def __append_arc_to_line(self, arc, transition, kwargs):
        lhs_arc = None
        rhs_arc = None

        line = self.current

        farside  = kwargs.get('farside',  False)
        co_sense = kwargs.get('co_sense', True)

        #if 'co_sense' in kwargs:
        #    co_sense = kwargs['co_sense']
        #else:
        #    co_sense = True
        #if 'farside' in kwargs:
        #    farside = kwargs['farside']
        #else:
        #    farside = False

        if arc.clockwise:
            sense = not co_sense
        else:
            sense = co_sense

        point, cross, tangent = Q2D_Path.__intersect_line(line, arc.circle, sense)
        if transition is None:
            if point is None:
                if Q2D_Print_Info:
                    print('Unable to add arc without transition')
            else:
                if Q2D_Print_Info:
                    print('Adding arc without transition')
                rhs_arc = Q2D_Arc(point, arc.circle, clockwise=arc.clockwise)
        else:
            if arc.clockwise:
                offset = -transition
            else:
                offset = transition

            if point is not None:
                if Q2D_Print_Info:
                    print('point = ({x}, {y}); cross={c}; tangent={t}'.format(x=point.x(), y=point.y(), c=cross, t=tangent))

            if tangent:
                if (cross > 0.0 and not arc.clockwise) or (cross < 0.0 and arc.clockwise):
                    if not co_sense:
                        if Q2D_Print_Info:
                            print('Co-sense transition should be used here')
                else:
                    if co_sense:
                        if Q2D_Print_Info:
                            print('Contra-sense transition should be used here')

                if co_sense:
                    if Q2D_Print_Info:
                        print('Adding (tangent) arc (without transition)')
                    rhs_arc = Q2D_Arc(point, arc.circle, clockwise=arc.clockwise)
                else:
                    if Q2D_Print_Info:
                        print('Adding (counter-sense tangent) arc (with transition)')
                    o = Q2D_Circle(arc.circle.center, arc.circle.radius + transition)
                    l = line.parallel(-offset)
                    p, c, t = Q2D_Path.__intersect_line(l, o, farside)
                    #print 'point = (', p.x(), p.y(), '); cross =', c, 'tangent =', t
                    lhs_arc = Q2D_Arc(line.project(p), Q2D_Circle(p, transition), clockwise=(not arc.clockwise))
                    rhs_arc = Q2D_Arc(arc.circle.project(p), arc.circle, clockwise=arc.clockwise)
            elif point is None:
                if (cross > 0.0 and not arc.clockwise) or (cross < 0.0 and arc.clockwise):
                    if not co_sense:
                        if Q2D_Print_Info:
                            print('Co-sense transition should be used here')
                else:
                    if co_sense:
                        if Q2D_Print_Info:
                            print('Contra-sense transition should be used here')

                if co_sense:
                    if transition > arc.circle.radius:
                        o = Q2D_Circle(arc.circle.center, transition - arc.circle.radius)
                        l = line.parallel(offset)
                        p, c, t = Q2D_Path.__intersect_line(l, o, farside)
                        if p is not None:
                            if Q2D_Print_Info:
                                print('Adding (co-sense) arc (with transition)')
                            #print 'point = (', p.x(), p.y(), '); cross =', c, 'tangent =', t
                            lhs_arc = Q2D_Arc(line.project(p), Q2D_Circle(p, transition), clockwise=arc.clockwise)
                            rhs_arc = Q2D_Arc(arc.circle.project(p, True), arc.circle, clockwise=arc.clockwise)
                        else:
                            if Q2D_Print_Info:
                                print('Unable to add (co-sense) arc with specified transition; try increasing the transition radius')
                    else:
                        if Q2D_Print_Info:
                            print('Unable to add (co-sense) arc with specified transition; require transition radius > arc radius')
                else:
                    o = Q2D_Circle(arc.circle.center, arc.circle.radius + transition)
                    l = line.parallel(-offset)
                    p, c, t = Q2D_Path.__intersect_line(l, o, farside)
                    if p is not None:
                        if Q2D_Print_Info:
                            print('Adding (counter-sense) arc (with transition)')
                        #print('point = (', p.x(), p.y(), '); cross =', c, 'tangent =', t)
                        lhs_arc = Q2D_Arc(line.project(p), Q2D_Circle(p, transition), clockwise=(not arc.clockwise))
                        rhs_arc = Q2D_Arc(arc.circle.project(p), arc.circle, clockwise=arc.clockwise)
                    else:
                        if Q2D_Print_Info:
                            print('Unable to add (counter-sense) arc with specified transition')
            else: # line intersects circle
                if co_sense:
                    if transition < arc.circle.radius:
                        o = Q2D_Circle(arc.circle.center, arc.circle.radius - transition)
                        l = line.parallel(offset)
                        p, c, t = Q2D_Path.__intersect_line(l, o, farside)
                        if p is not None:
                            if Q2D_Print_Info:
                                print('Adding (co-sense) arc (with transition)')
                            #print('point = (', p.x(), p.y(), '); cross =', c, 'tangent =', t)
                            lhs_arc = Q2D_Arc(line.project(p), Q2D_Circle(p, transition), clockwise=arc.clockwise)
                            rhs_arc = Q2D_Arc(arc.circle.project(p), arc.circle, clockwise=arc.clockwise)
                        else:
                            if Q2D_Print_Info:
                                print('Unable to add (co-sense) arc with specified transition; try increasing the transition radius')
                    else:
                        if Q2D_Print_Info:
                            print('Unable to add (co-sense) arc with specified transition; require transition radius > arc radius')
                else:
                    o = Q2D_Circle(arc.circle.center, arc.circle.radius + transition)
                    l = line.parallel(-offset)
                    p, c, t = Q2D_Path.__intersect_line(l, o, farside)
                    if p is not None:
                        if Q2D_Print_Info:
                            print('Adding (counter-sense) arc (with transition)')
                        #print('point = (', p.x(), p.y(), '); cross =', c, 'tangent =', t)
                        lhs_arc = Q2D_Arc(line.project(p), Q2D_Circle(p, transition), clockwise=(not arc.clockwise))
                        rhs_arc = Q2D_Arc(arc.circle.project(p), arc.circle, clockwise=arc.clockwise)

        return lhs_arc, rhs_arc

    def __append_arc_to_arc(self, rhs, transition, kwargs):
        lhs_arc = None
        rhs_arc = None

        lhs = self.current

        if transition is None:
            print("Q2D_Path.__append_arc_to_arc: error: transition radius must be positive * * *")
        elif transition <= 0.0:
            print("Q2D_Path.__append_arc_to_arc: error: transition radius must be positive * * *")

        # don't swap the sense of farside:
        farside     = kwargs.get('farside',  False)
        lhs_cosense = kwargs.get('co_sense', True)

        #if 'farside' in kwargs:
        #    farside = kwargs['farside']
        #else:
        #    farside = False
        #if 'co_sense' in kwargs:
        #    lhs_cosense = kwargs['co_sense']
        #else:
        #    lhs_cosense = True

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
            if Q2D_Print_Info:
                print("Unable to intersect arcs")
        else:
            if Q2D_Print_Info:
                print("Adding arc with transition")
            lhs_point = lhs.circle.project(point, lhs_invert)
            rhs_point = rhs.circle.project(point, rhs_invert)
            lhs_arc = Q2D_Arc(lhs_point, Q2D_Circle(point, transition), clockwise=clockwise)
            rhs_arc = Q2D_Arc(rhs_point, rhs.circle, clockwise=rhs.clockwise)

        return lhs_arc, rhs_arc

    def append(self, line_or_arc, transition=None, **kwargs):
        tarc = None # transition curve
        pnew = None # new line or arc

        if self.current.name == "Line":
            if line_or_arc.name == "Line":
                tarc, pnew = self.__append_line_to_line(line_or_arc, transition, kwargs)
            elif line_or_arc.name == "Arc":
                tarc, pnew = self.__append_arc_to_line(line_or_arc, transition, kwargs)
        elif self.current.name == "Arc":
            if line_or_arc.name == "Line":
                tarc, pnew = self.__append_line_to_arc(line_or_arc, transition, kwargs)
            elif line_or_arc.name == "Arc":
                tarc, pnew = self.__append_arc_to_arc(line_or_arc, transition, kwargs)

        if tarc is not None:
            tarc.mesh = kwargs.get('transition_mesh', None)
            self.__append(tarc)
            print("append: transition curve with mesh {m}".format(m=tarc.mesh))

        if pnew is not None:
            pnew.mesh = line_or_arc.props.get('mesh', None)
            pnew.mesh = kwargs.get('mesh', None)
            self.__append(pnew)
            print("append: curve with mesh {m}".format(m=pnew.mesh))

    def offset_path(self, offset):
        path = None
        endp = None
        item = self.chain

        while item is not None:
            if item.name == "Line":
                line = item.parallel(offset)
                if path is None:
                    path = Q2D_Path(line)
                    endp = line.start
                else:
                    path.__append(line)
            elif item.name == "Arc":
                arc = item.concentric(offset)
                if arc is None:
                    print("* * * Path segment skipped... behaviour undefined! * * *")
                    item = item.chain
                    continue
                if path is None:
                    path = Q2D_Path(arc)
                    endp = arc.start
                else:
                    path.__append(arc)
            else:
                if path:
                    path.end_point(endp)

            item = item.chain

        return path
        
    def poly_points(self, arc_interval, line_interval=None):
        points = []
        item = self.chain

        while item is not None:
            if item.name == "Line":
                if line_interval is not None:
                    points += item.poly_points(line_interval)
                else:
                    points += [[item.start.x(), item.start.y()]]
            elif item.name == "Arc":
                points += item.poly_points(arc_interval)

            item = item.chain

        return points

class Q2D_Frame(object):
    @staticmethod
    def map_angle(angle):
        TwoPi = 2.0 * math.pi
        while angle >= TwoPi:
            angle -= TwoPi
        while angle < 0.0:
            angle += TwoPi
        return angle

    def __init__(self, theta=0.0):
        self.__Og = Q2D_Point((0.0, 0.0))
        self.theta = theta

    @property
    def Og(self):
        return self.__Og

    @property
    def e1(self):
        return self.__e1

    @property
    def e2(self):
        return self.__e2

    @property
    def theta(self):
        return self.__theta

    @theta.setter
    def theta(self, value): # sets orientation relative to global xy-space
        TwoPi = 2.0 * math.pi
        self.__theta = Q2D_Frame.map_angle(value)
        self.__e1 = Q2D_Vector(self.__theta)
        self.__e2 = Q2D_Vector(self.__theta + math.pi / 2.0)

    def e3_rotate(self, theta): # rotate local frame relative to current rotation
        self.theta = self.__theta + theta
        return self

    def l2g(self, l): # translate from local to global space, where l is a Q2D_Point
        gx = self.__Og.x() + l.x() * self.__e1.x() + l.y() * self.__e2.x()
        gy = self.__Og.y() + l.x() * self.__e1.y() + l.y() * self.__e2.y()
        return Q2D_Point((gx, gy))

    def tuple_to_global(self, l12): # translate from local to global space, where l12 is an (x, y) tuple
        l1, l2 = l12
        gx = self.__Og.x() + l1 * self.__e1.x() + l2 * self.__e2.x()
        gy = self.__Og.y() + l1 * self.__e1.y() + l2 * self.__e2.y()
        return (gx, gy)

    def local_point_set_origin(self, l):
        self.__Og = self.l2g(l)
        return self

    def local_tuple_set_origin(self, l12):
        self.__Og = Q2D_Point(self.local_to_global(l12))
        return self

    def global_point_set_origin(self, g):
        self.__Og = g
        return self

    def global_tuple_set_origin(self, g12):
        self.__Og = Q2D_Point(g12)
        return self

    def g_pt(self, local_x, local_y, **kwargs):
        return Q2D_Point(self.tuple_to_global((local_x, local_y)), **kwargs)

    def g_vec(self, local_theta=0.0):
        return Q2D_Vector(Q2D_Frame.map_angle(self.__theta + local_theta))

    def copy(self):
        frame = Q2D_Frame(self.__theta)
        return frame.global_point_set_origin(self.__Og)
