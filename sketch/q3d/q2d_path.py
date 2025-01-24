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

    __counter = 0

    def __init__(self, geom, **kwargs):
        self._geom  = geom
        self.__name = kwargs.get("name", None)

        Q2D_Object.__counter += 1
        self.__id = "_2D_" + str(Q2D_Object.__counter)

    @property
    def unique_id(self):
        return self.__id

    @property
    def geom(self):
        return self._geom

    @property
    def name(self):
        if self.__name is None:
            n = self.__id
        else:
            n = self.__name
        return n

    @name.setter
    def name(self, value):
        self.__name = value

    def desc(self):
        d = self.geom + "(id=" + self.__id
        if self.__name is not None:
            d += ",name='" + self.__name + "'"
        d += ")"
        return d

class Q2D_Point(Q2D_Object):

    def __init__(self, xy, **kwargs):
        Q2D_Object.__init__(self, "Point", **kwargs)
        x, y = xy
        self.__x = x
        self.__y = y
        self.__mesh = kwargs.get("mesh", None)

    @property
    def mesh(self):
        return self.__mesh

    @mesh.deleter
    def mesh(self):
        self.__mesh = None

    @mesh.setter
    def mesh(self, value):
        if value is not None:
            bUpdate = True
            if self.__mesh is not None:
                min_mesh = self.__mesh
                if value >= min_mesh:
                    bUpdate = False
            if bUpdate:
                self.__mesh = value

    @property
    def x(self):
        return self.__x

    @property
    def y(self):
        return self.__y

    def cartesian_relative(self, dx, dy): # new point displaced from self; cartesian components
        return Q2D_Point((self.x + dx, self.y + dy))

    def polar_relative(self, r, theta): # new point displaced from self; polar components
        x = self.x + r * math.cos(theta)
        y = self.y + r * math.sin(theta)
        return Q2D_Point((x, y))

    def vector_relative(self, v): # new point displaced from self by vector v
        return Q2D_Point((self.x + v.x(), self.y + v.y()))

    def distance(self, p): # distance between points
        return ((self.x - p.x)**2 + (self.y - p.y)**2)**0.5

    def coincident(self, p): # true if both points are in exactly the same place
        return (self.x == p.x) and (self.y == p.y)

    @staticmethod
    def from_to(from_point, to_point): # define vector between two points
        return Q2D_Vector.from_to(to_point.x - from_point.x, to_point.y - from_point.y)

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
            points += [[point.x, point.y]]
            radius = self.center.distance(point)
            theta = theta + interval / radius

        return points

class Q2D_Circle(Q2D_Ellipse):

    def __init__(self, center, radius, **kwargs):
        Q2D_Ellipse.__init__(self, center, radius, radius, **kwargs)
        self._geom = "Circle"
        self.radius = radius

    def convert_to_ellipse(self):
        self._geom = "Ellipse"

class Q2D_Curve(Q2D_Object):

    def __init__(self, geom, **kwargs):
        Q2D_Object.__init__(self, geom, **kwargs)
        self.__vertex = [] # list of vertices, not including any arc centres or control points
        self.__edge   = [] # list of edges
        self.__mesh   = kwargs.get("mesh", None)
        self.props = {}

        # Only the *first* vertex of a curve can be [None]-type, but no edges or vertices can then be added to it
        # A *defined* curve has no [None]-type vertices, at least one edge, and No. vertices = No. edges + 1
        # A *component* curve has all [None]-type edges; otherwise, edges must not be [None]-type

    def __getitem__(self, key): # find first instance of edge or vertex by name
        value = None
        if key is not None:
            for e in self.__edge:
                if e.name == key:
                    value = e
                    break
            if value is None:
                for v in self.__vertex:
                    if v.name == key:
                        value = v
                        break
        return value
        
    @property
    def mesh(self):
        return self.__mesh

    @mesh.deleter
    def mesh(self):
        self.__mesh = None

    @mesh.setter
    def mesh(self, value):
        if value is not None:
            bUpdate = True
            if self.__mesh is not None:
                min_mesh = self.__mesh
                if value >= min_mesh:
                    bUpdate = False
            if bUpdate:
                self.__mesh = value

            for e in self.__edge:
                if e is not None:
                    e.mesh = value
            for v in self.__vertex:
                if v is not None:
                    v.mesh = value

    def curve_print(self, indent=""):
        Nv = len(self.__vertex)
        Ne = len(self.__edge)

        print(indent + self.desc() + "[mesh={m}] has {v} vertices and {e} edges".format(m=self.mesh, v=Nv, e=Ne))

        indent += "    "
        for iv in range(Nv):
            v = self.__vertex[iv]
            if v is None:
                print(indent + "vertex {i} ({n})[mesh={m}] [None]".format(i=iv, n=v.desc(), m=v.mesh))
            elif v.geom == "Point3D":
                print(indent + "vertex {i} ({n}) @ ({x:.4f}, {y:.4f}, {z:.4f})".format(i=iv, n=v.desc(), x=v.x, y=v.y, z=v.z))
            else:
                print(indent + "vertex {i} ({n})[mesh={m}] @ ({x:.4f}, {y:.4f})".format(i=iv, n=v.desc(), m=v.mesh, x=v.x, y=v.y))

            if iv >= Ne:
                continue

            e = self.__edge[iv]
            if e is None:
                print(indent + "edge {i} [None]".format(i=iv))
            else:
                e.curve_print(indent)

    @property # first vertex, or None
    def start(self):
        v0 = None
        if len(self.__vertex) > 0:
            v0 = self.__vertex[0]
        return v0

    @property # last vertex (distinct from first), or None
    def end(self):
        vf = None
        if len(self.__vertex) > 1:
            vf = self.__vertex[-1]
        return vf

    @property # last edge, or None
    def last(self):
        ef = None
        if len(self.__edge) > 0:
            ef = self.__edge[-1]
        return ef

    @property # list of vertices
    def vertices(self):
        return self.__vertex

    @property # list of edges
    def edges(self):
        return self.__edge

    def _curve_begin(self, vertex): # start the curve by adding the initial vertex
        bAdded = True

        if len(self.__vertex) > 0:
            print("* * * Q2D_Curve::curve_begin(): error: attempt to begin existing curve")
            bAdded = False
        else:
            self.__vertex.append(vertex)

        return bAdded

    def _curve_append_vertex(self, vertex): # add next vertex
        bAdded = True

        if len(self.__vertex) == 0:
            bAdded = self._curve_begin(vertex)
        elif vertex is None:
            print("* * * Q2D_Curve::curve_append_vertex(): error: attempt to append [None]-vertex to curve")
            bAdded = False
        else:
            if len(self.__vertex) == len(self.__edge): # set this new vertex as the end-point vertex of the last curve
                last = self.last # last edge in list
                if last is not None:
                    lvx = last.vertices
                    if not vertex.coincident(lvx[-1]):
                        bAdded = last._curve_append_vertex(vertex)
            else:
                bAdded = self._curve_append_edge(None) # add (with checks) a [None]-edge between vertices

            if bAdded:
                v0 = self.__vertex[0]
                if v0.coincident(vertex): # if we return to the start, add in the starting vertex as next point
                    self.__vertex.append(v0)
                else:
                    self.__vertex.append(vertex)

        return bAdded

    def _curve_append_edge(self, edge): # add edge starting at existing curve end-point
        bAdded = True

        if len(self.__edge) > 0:
            if edge is None and self.__edge[0] is not None:
                print("* * * Q2D_Curve::curve_append_edge(): error: attempt to append [None]-edge to non-component curve")
                return False
            if edge is not None and self.__edge[0] is None:
                print("* * * Q2D_Curve::curve_append_edge(): error: attempt to append defined edge to component curve")
                return False

        if len(self.__vertex) == len(self.__edge):
            if edge is None:
                print("* * * Q2D_Curve::curve_append_edge(): error: attempt to append [None]-edge out of sequence")
                bAdded = False
            else:
                bAdded = self._curve_append_vertex(edge.start)
                if bAdded:
                    self.__edge.append(edge)
        elif self.__vertex[0] is None:
            print("* * * Q2D_Curve::curve_append_edge(): error: attempt to append edge to curve with undefined start")
            bAdded = False
        else:
            self.__edge.append(edge)

        return bAdded

    def curve_defined(self): # return true if at least one edge and if both ends of the curve are specified
        return len(self.__edge) > 0 and len(self.__vertex) == len(self.__edge) + 1

    def component_curve(self): # return true if any (and thus all) edges are [None]-type
        bCompC = False
        if len(self.__edge) > 0:
            if self.__edge[0] is None:
                bCompC = True
        return bCompC

    def curve_closed(self): # return true if final vertex is the initial vertex
        bClosed = False
        if len(self.__vertex) > 1:
            if self.__vertex[0] == self.__vertex[-1]:
                bClosed = True
        return bClosed

class Q2D_Line(Q2D_Curve):
    # Q2D_Line is a Q2D_Curve with a reference/starting vertex but no edge or end-point vertex

    def __init__(self, start, direction, **kwargs):
        Q2D_Curve.__init__(self, "Line", **kwargs)
        self._curve_begin(start)
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

        c1 = p1.y * d1.x() - p1.x * d1.y()
        c2 = p2.y * d2.x() - p2.x * d2.y()
        y = (d1.y() * c2 - d2.y() * c1) / det
        x = (d1.x() * c2 - d2.x() * c1) / det

        return Q2D_Point((x, y))

    def project(self, point):
        rhs = Q2D_Line(point, self.direction.copy().rotate())
        return self.intersection(rhs)

    def nurbs_cps_wts(self, degree):
        # return list of control point coordinates as (x,y)

        if degree != 2:
            print("* * * Q2D_Line::nurbs_cps_wts: only degree=2 is supported currently.")
            return None, None
        if not self.curve_defined():
            print("* * * Q2D_Line::nurbs_cps_wts: curve not defined.")
            return None, None

        p0 = self.vertices[0]
        p1 = self.vertices[1]

        sx, sy = p0.x, p0.y
        ex, ey = p1.x, p1.y

        mx = (sx + ex) / 2.0
        my = (sy + ey) / 2.0

        cps = [(sx, sy), (mx, my), (ex, ey)]
        wts = [1.0, 1.0, 1.0]

        return cps, wts

    def poly_points(self, interval):
        points = []
        if self.curve_defined():
            vertices = self.vertices
            p1 = vertices[0]
            p2 = vertices[1]

            dx = p2.x - p1.x
            dy = p2.y - p1.y
            length = math.sqrt(dx**2 + dy**2)

            count = int(math.ceil(length / interval))
            for c in range(0, count):
                x = p1.x + (dx * c) / count
                y = p1.y + (dy * c) / count
                points += [[x, y]]

        return points

class Q2D_Arc(Q2D_Curve):
    # Q2D_Arc is a Q2D_Curve with a reference/starting vertex but no edge or end-point vertex

    def __init__(self, start, circle, clockwise=False, **kwargs):
        Q2D_Curve.__init__(self, "Arc", **kwargs)
        self._curve_begin(start)
        self.circle = circle
        self.clockwise = clockwise

    @property
    def Ox(self):
        return self.circle.center.x

    @property
    def Oy(self):
        return self.circle.center.y

    def concentric(self, offset):
        if self.clockwise:
            offset = -offset
        if self.circle.radius - offset <= 0:
            return None

        v_center = Q2D_Point.from_to(self.start, self.circle.center) # vector pointing inwards
        cc_start = self.start.cartesian_relative(offset * v_center.dx, offset * v_center.dy)

        return Q2D_Arc(cc_start, Q2D_Circle(self.circle.center, self.circle.radius - offset), self.clockwise)

    @staticmethod
    def nurbs_angles(theta, bPeriodic):
        # split range into angles of 120 degrees or less, and half-angles
        # also return: cha  the cosine of the half-angle
        #              Ncp  number of control points for degree 2 curve
        if theta is not None:
            t1, t2 = theta
        else:
            t1 = 0.0
            t2 = 2.0 * math.pi
        Narc = int(math.ceil(math.fabs(t2 - t1) * 1.5 / math.pi))
        cha = math.cos(math.fabs(t2 - t1) * 0.5 / Narc)
        angles = []
        Ncp = 2 * Narc
        for a in range(Ncp):
            angles.append(t1 + (t2 - t1) * a * 1.0 / Ncp)
        if not bPeriodic:
            Ncp += 1
            angles.append(t2)
        return angles, cha, Ncp

    def nurbs_cps_wts(self):
        # return list of control point coordinates as (x,y)

        if not self.curve_defined():
            print("* * * Q2D_Arc::nurbs_cps_wts: curve not defined.")
            return None, None

        p0 = self.vertices[0]
        p1 = self.vertices[1]

        sx, sy = p0.x, p0.y
        ex, ey = p1.x, p1.y

        ts = math.atan2(sy - self.Oy, sx - self.Ox)
        te = math.atan2(ey - self.Oy, ex - self.Ox)
        if ts > te and not self.clockwise:
            ts -= 2.0 * math.pi
        if te > ts and self.clockwise:
            ts += 2.0 * math.pi

        angles, cha, Ncp = Q2D_Arc.nurbs_angles((ts, te), False)
        cps = []
        wts = []

        ha = False
        for a in angles:
            if ha:
                rs = cha
                ha = False
            else:
                rs = 1.0
                ha = True

            x = self.Ox + self.circle.radius * math.cos(a) / rs
            y = self.Oy + self.circle.radius * math.sin(a) / rs

            cps.append((x, y))
            wts.append(rs)

        return cps, wts

    def poly_points(self, interval):
        points = []
        if self.curve_defined():
            vertices = self.vertices
            p1 = vertices[0]
            p2 = vertices[1]
            t1 = math.atan2(p1.y - self.Oy, p1.x - self.Ox)
            t2 = math.atan2(p2.y - self.Oy, p2.x - self.Ox)
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
                points += [[point.x, point.y]]

        return points

class Q2D_Path(Q2D_Curve):

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

    @staticmethod
    def circle(circ):
        Ox = circ.center.x
        Oy = circ.center.y
        r  = circ.radius
        pe = Q2D_Point((Ox + r, Oy))
        pn = Q2D_Point((Ox, Oy + r))
        pw = Q2D_Point((Ox - r, Oy))
        ps = Q2D_Point((Ox, Oy - r))

        path = Q2D_Path()
        path.append(Q2D_Arc(pe, circ, False))
        path.append(Q2D_Arc(pn, circ, False))
        path.append(Q2D_Arc(pw, circ, False))
        path.append(Q2D_Arc(ps, circ, False))
        path.end_point(pe)

        return path

    def __init__(self, line_or_arc=None, **kwargs):
        Q2D_Curve.__init__(self, "Path", **kwargs)

        if line_or_arc is not None:
            if line_or_arc.geom == "Arc" or line_or_arc.geom == "Line":
                self._curve_append_edge(line_or_arc)

    def end_point(self, point):
        if point.geom == "Point":
            self._curve_append_vertex(point)

    def __append(self, line_arc_point):
        if line_arc_point.geom == "Point":
            self._curve_append_vertex(line_arc_point)
        else:
            self._curve_append_edge(line_arc_point)

    def __append_line_to_line(self, line, transition, kwargs):
        lhs_arc  = None
        rhs_line = None

        radius = 0
        if transition is not None:
            if transition > 0:
                radius = transition

        l1 = self.last
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
    def __intersect_circle(lhs, rhs, kwargs):
        point = None

        cc = Q2D_Point.from_to(lhs.center, rhs.center)
        if cc.length < lhs.radius + rhs.radius:
            dtheta = math.acos(0.5 * (cc.length + (lhs.radius**2.0 - rhs.radius**2.0) / cc.length) / lhs.radius)

            farside = kwargs.get('farside', False)
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

        arc = self.last

        farside  = kwargs.get('farside',  False)
        co_sense = kwargs.get('co_sense', True)

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

        line = self.last

        farside  = kwargs.get('farside',  False)
        co_sense = kwargs.get('co_sense', True)

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

        lhs = self.last

        if lhs.circle.center.coincident(rhs.circle.center):
            if lhs.circle.radius != rhs.circle.radius:
                print("Q2D_Path.__append_arc_to_arc: error: unable to transition between concentric circles * * *")
                return None, None
            # we're continuing along the same circle
            if rhs.start is None:
                print("Q2D_Path.__append_arc_to_arc: error: transition vertex must be specified when continuing on same circle * * *")
                return None, None
            return None, rhs # success... ignoring transition curve settings and arc direction
        if transition is None:
            print("Q2D_Path.__append_arc_to_arc: error: transition radius must be positive * * *")
            return None, None
        if transition <= 0.0:
            print("Q2D_Path.__append_arc_to_arc: error: transition radius must be positive * * *")
            return None, None

        # don't swap the sense of farside:
        farside     = kwargs.get('farside',  False)
        lhs_cosense = kwargs.get('co_sense', True)

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

        last = self.last
        if last is None:
            if line_or_arc.geom == "Line" or line_or_arc.geom == "Arc":
                pnew = line_or_arc
        elif last.geom == "Line":
            if line_or_arc.geom == "Line":
                tarc, pnew = self.__append_line_to_line(line_or_arc, transition, kwargs)
            elif line_or_arc.geom == "Arc":
                tarc, pnew = self.__append_arc_to_line(line_or_arc, transition, kwargs)
        elif last.geom == "Arc":
            if line_or_arc.geom == "Line":
                tarc, pnew = self.__append_line_to_arc(line_or_arc, transition, kwargs)
            elif line_or_arc.geom == "Arc":
                tarc, pnew = self.__append_arc_to_arc(line_or_arc, transition, kwargs)

        if tarc is not None:
            self.__append(tarc)
        if pnew is not None:
            self.__append(pnew)

        return tarc, pnew

    def offset_path(self, offset):
        if not self.curve_defined():
            print("* * * Q2D_Path::offset_path: path must be fully defined in order to create offset path!")
            return None
        if not self.curve_closed():
            print("* * * Q2D_Path::offset_path: path must be closed in order to create offset path!")
            return None
            
        path = Q2D_Path()
        endp = None
        for item in self.edges:
            if item is None:
                print("* * * Q2D_Path::offset_path: error: unexpected [None]-edge!")
                continue
            if item.geom == "Line":
                line = item.parallel(offset)
                path.__append(line)
                if endp is None:
                    endp = line.start
            elif item.geom == "Arc":
                arc = item.concentric(offset)
                if arc is None:
                    print("* * * Q2D_Path::offset_path: vanishing arc!")
                    endp = None
                    break
                path.__append(arc)
                if endp is None:
                    endp = arc.start

        if endp is None:
            path = None
        else:
            path.end_point(endp)

        return path
        
    def poly_points(self, arc_interval, line_interval=None):
        points = []
        for item in self.edges:
            if item is None:
                continue
            if item.geom == "Line":
                if line_interval is not None:
                    points += item.poly_points(line_interval)
                else:
                    v0 = item.start
                    points += [[v0.x, v0.y]]
            elif item.geom == "Arc":
                points += item.poly_points(arc_interval)

        return points

class Q2D_NURBS_Curve(Q2D_Curve): # non-periodic component curve
    def __init__(self, line_or_arc, **kwargs):
        Q2D_Curve.__init__(self, "NURBS-Curve", **kwargs)
        if not line_or_arc.curve_defined():
            print("* * * Q2D_NURBS_Curve::__init__: source geometry must be a fully defined Line or Arc")
        else:
            self._curve_begin(line_or_arc.start)
            if line_or_arc.geom == "Line":
                self.deg = 1
                self.kts = [0.0, 1.0]
                self.mps = [2, 2]
                self.cps = [line_or_arc.start, line_or_arc.end]
                self.wts = [1.0, 1.0]
            elif line_or_arc.geom == "Arc":
                self.deg = 2
                cps, wts = line_or_arc.nurbs_cps_wts()
                Ncp = len(cps)
                self.cps = [line_or_arc.start]
                for cp in range(1,Ncp-1):
                    pt = Q2D_Point(cps[cp])
                    self.cps.append(pt)
                    self._curve_append_vertex(pt)
                self.cps.append(line_or_arc.end)
                self.wts = wts
                self.kts = []
                self.mps = [3]
                Narc = int(Ncp / 2)
                for a in range(Narc):
                    self.kts.append(a * 1.0 / Narc)
                    if a:
                        self.mps.append(2)
                self.kts.append(1.0)
                self.mps.append(self.mps[0])
            else:
                print("* * * Q2D_NURBS_Curve::__init__: source geometry must be a fully defined Line or Arc")
            self._curve_append_vertex(line_or_arc.end)

class Q2D_NURBS_Path(Q2D_Curve): # path converted to multiple Nurbs curves
    def __init__(self, path, **kwargs):
        Q2D_Curve.__init__(self, "NURBS-Path", **kwargs)
        if path.geom != "Path" or not path.curve_defined():
            print("* * * Q2D_NURBS_Path::__init__: source geometry must be a fully defined Path")

        for e in path.edges:
            self._curve_append_edge(Q2D_NURBS_Curve(e, **kwargs))

        self._curve_append_vertex(path.end)

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
        gx = self.__Og.x + l.x() * self.__e1.x() + l.y() * self.__e2.x()
        gy = self.__Og.y + l.x() * self.__e1.y() + l.y() * self.__e2.y()
        return Q2D_Point((gx, gy))

    def tuple_to_global(self, l12): # translate from local to global space, where l12 is an (x, y) tuple
        l1, l2 = l12
        gx = self.__Og.x + l1 * self.__e1.x() + l2 * self.__e2.x()
        gy = self.__Og.y + l1 * self.__e1.y() + l2 * self.__e2.y()
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

def Q2D_BBox(paths):
    xmin = -0.5 # FIXME: Q2D_Curve should have function for bounding box estimate
    xmax = -0.5
    ymin =  0.5
    ymax =  0.5
    bFirst = True
    for path in paths:
        np = Q2D_NURBS_Path(path)
        for e in np.edges:
            for v in e.vertices:
                if bFirst:
                    bFirst = False
                    xmin = v.x
                    xmax = v.x
                    ymin = v.y
                    ymax = v.y
                    continue
                if v.x > xmax:
                    xmax = v.x
                if v.x < xmin:
                    xmin = v.x
                if v.y > ymax:
                    ymax = v.y
                if v.y < ymin:
                    ymin = v.y
    x_range = xmax - xmin
    y_range = ymax - ymin
    x_middle = (xmax + xmin) / 2.0
    y_middle = (ymax + ymin) / 2.0
    if x_range > y_range:
        xmin = x_middle - x_range * 0.55
        xmax = x_middle + x_range * 0.55
        ymin = y_middle - x_range * 0.55
        ymax = y_middle + x_range * 0.55
    else:
        xmin = x_middle - y_range * 0.55
        xmax = x_middle + y_range * 0.55
        ymin = y_middle - y_range * 0.55
        ymax = y_middle + y_range * 0.55

    return xmin, xmax, ymin, ymax
