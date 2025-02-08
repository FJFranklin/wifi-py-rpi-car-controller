import math
import inspect
import abc

try:
    # Python <  3.11
    from typing_extensions import Self
except:
    # Python >= 3.11
    from typing import Self

Q2D_Design_Tolerance: float = 1E-15 # tolerance for numerical errors

Q2D_Print_Info: bool = False # print info for debugging

def Q2D_Info(message):
    if Q2D_Print_Info:
        frame = inspect.currentframe().f_back
        fname = frame.f_code.co_name
        if 'self' in frame.f_locals:
            cname = frame.f_locals['self'].__class__.__name__
        else:
            cname = ""
        print(cname + "::" + fname + ": " + message)

def Q2D_Error(message):
    frame = inspect.currentframe().f_back
    fname = frame.f_code.co_name
    if 'self' in frame.f_locals:
        cname = frame.f_locals['self'].__class__.__name__
    else:
        cname = ""
    raise RuntimeError(cname + "::" + fname + ": " + message)

def Q2D_Remap_Angle(angle: float) -> float:
    """Map angle to be in range (-pi,pi]."""
    while angle > math.pi:
        angle -= 2.0 * math.pi
    while angle <= -math.pi:
        angle += 2.0 * math.pi
    return angle

# ==== Q2D Arc-Line sketch path classes ==== #

class Q2D_Vector(object):
    """A 2D vector object with both cartesian and polar representation.
    """

    @staticmethod
    def from_to(dx: float, dy: float) -> 'Q2D_Vector':
        """Create a 2D vector with xy-components."""
        length = (dx**2.0 + dy**2.0)**0.5
        return Q2D_Vector(math.atan2(dy, dx), length)

    @property
    def theta(self) -> float:
        return self.__theta

    @theta.setter
    def theta(self, angle: float) -> None:
        """Set new vector angle and recalculate components."""
        self.__theta = Q2D_Remap_Angle(angle)
        self.__dx = math.cos(angle)
        self.__dy = math.sin(angle)

    @property
    def length(self) -> float:
        """The length of the vector."""
        return self.__length

    @length.setter
    def length(self, value: float) -> None:
        """Set the length of the vector (must be strictly greater than zero)."""
        if value <= 0:
            Q2D_Error("Vector length must be strictly greater than zero.")
        self.__length = value

    def __init__(self, theta: float, length:float = 1.0) -> None:
        """New 2D vector instance with specified polar angle and (optional) length."""
        self.length = length
        self.theta = theta

    def x(self, unit: bool = False) -> float:
        """x-component of the 2D vector; optionally as the x-component of the parallel unit vector."""
        dx = self.__dx
        if not unit:
            dx *= self.__length
        return dx

    def y(self, unit: bool = False):
        """y-component of the 2D vector; optionally as the y-component of the parallel unit vector."""
        dy = self.__dy
        if not unit:
            dy *= self.__length
        return dy

    def copy(self, unit: bool = False) -> 'Q2D_Vector':
        """Create a copy of the 2D vector; optionally as a unit vector."""
        length = 1.0
        if not unit:
            length = self.__length
        return Q2D_Vector(self.theta, length)

    def rotate(self, phi: float = None) -> 'Q2D_Vector':
        """Perform an in-place rotation; defaults to 90 degrees."""
        if phi is None: # 90 degree
            self.theta = self.__theta + math.pi / 2
        else:
            self.theta = self.__theta + phi
        return self

    def reverse(self) -> 'Q2D_Vector':
        """Perform an in-place reversal, i.e., rotate 180 degrees."""
        self.theta = self.__theta + math.pi
        return self

    def scale(self, scalar: float) -> 'Q2D_Vector':
        """Perform an in-place scaling."""
        if scalar == 0:
            Q2D_Error("Vector length must not be zero")
        if scalar < 0:
            self.reverse()
            scalar = -scalar
        self.length = self.__length *  scalar
        return self

    def dot(self, rhs: 'Q2D_Vector', just_cosine: bool = False) -> float:
        """Calculate the dot product of this and another vector; or, optionally, the cosine of the angle."""
        cos = self.__dx * rhs.x(True) + self.__dy * rhs.y(True)
        if not just_cosine:
            cos *= self.__length * rhs.length
        return cos

    def angle(self, rhs: 'Q2D_Vector') -> float:
        """Calculate the angle between this and another vector, mapped to (-pi,pi]."""
        return Q2D_Remap_Angle(rhs.theta - self.__theta)

    def cross(self, rhs: 'Q2D_Vector') -> float:
        """Calculate the normal component of the cross product of this and another vector."""
        return self.__length * (self.__dx * rhs.y() - self.__dy * rhs.x())

    def unit(self) -> 'Q2D_Vector':
        """Set vector length to 1."""
        self.__length = 1.0
        return self

    def add(self, rhs_vector: 'Q2D_Vector', rhs_scale: float = 1.0) -> 'Q2D_Vector':
        """Copy self and add (optionally scaled) vector."""
        return Q2D_Vector(self.x() + rhs_vector.x() * rhs_scale,
                          self.y() + rhs_vector.y() * rhs_scale)

    def is_parallel(self, rhs, allow_antiparallel: bool = False) -> bool:
        """True if specified vector is parallel to this; optionally allow antiparallel also."""
        dt = abs(rhs.theta - self.__theta)
        parallel = dt < Q2D_Design_Tolerance or abs(2 * math.pi - dt) < Q2D_Design_Tolerance
        antillel = abs(math.pi - dt) < Q2D_Design_Tolerance
        return parallel or (antillel and allow_antiparallel)

class Q2D_Object(object):
    """Q2D_Object is the base class for all 2D path objects.
    """

    __counter: int = 0

    def __init__(self, geom: str, **kwargs) -> None:
        """New instance of Q2D_Object base class with unique ID. (keywords: name)"""
        self._geom  = geom
        self.__name = None

        Q2D_Object.__counter += 1
        self.__id = "_2D_" + str(Q2D_Object.__counter)

        self.name = kwargs.get("name", None)

    @property
    def unique_id(self) -> str:
        """Unique ID of object as a string."""
        return self.__id

    @property
    def geom(self) -> str:
        """Geometry class of object as a string."""
        return self._geom

    @property
    def name(self) -> str:
        """Name of object as a string, if set; otherwise the unique ID."""
        if self.__name is None:
            n = self.__id
        else:
            n = self.__name
        return n

    @name.setter
    def name(self, value: str) -> None:
        """Set name of object as a string."""
        if value is not None:
            if type(value) is not str:
                Q2D_Error("Keyword 'name' must be a str.")
            self.__name = value

    @abc.abstractmethod
    def desc(self) -> str:
        """Brief description of object as a string."""
        d = self._geom + "(id=" + self.__id
        if self.__name is not None:
            d += ",name='" + self.__name + "'"
        d += ")"
        return d

class Q2D_Point(Q2D_Object):

    """2D geometry class 'Point'.
    """

    def __init__(self, xy: tuple, **kwargs) -> None:
        """New instance of Q2D_Point at specified 2D coordinate. (keywords: mesh)"""
        Q2D_Object.__init__(self, "Point", **kwargs)

        x, y = xy

        # Avoid numerical not-quite-zeros
        if abs(x) < Q2D_Design_Tolerance:
            x = 0
        if abs(y) < Q2D_Design_Tolerance:
            y = 0

        self.__x = float(x)
        self.__y = float(y)
        self.__mesh = None

        self.mesh = kwargs.get("mesh", None)

    @property
    def mesh(self) -> float | None:
        """Mesh size associated with point; or None if not set."""
        return self.__mesh

    @mesh.setter
    def mesh(self, value: float) -> None:
        """Set new mesh size associated with point; ignored unless new mesh size is smaller."""
        if value is not None:
            new_mesh = float(value)
            if new_mesh <= 0:
                Q2D_Error("New mesh size must be a positive number.")

            if self.__mesh is None:
                self.__mesh = new_mesh
            elif self.__mesh > new_mesh:
                self.__mesh = new_mesh

    @property
    def x(self) -> float:
        """x-coordinate of the 2D point."""
        return self.__x

    @property
    def y(self) -> float:
        """y-coordinate of the 2D point."""
        return self.__y

    def cartesian_relative(self, dx: float, dy: float) -> 'Q2D_Point':
        """Create new point relative to this one, specified by Cartesian displacement."""
        return Q2D_Point((self.__x + dx, self.__y + dy))

    def polar_relative(self, r: float, theta: float) -> 'Q2D_Point':
        """Create new point relative to this one, specified by Polar displacement."""
        x = self.__x + r * math.cos(theta)
        y = self.__y + r * math.sin(theta)
        return Q2D_Point((x, y))

    def vector_relative(self, v: Q2D_Vector) -> 'Q2D_Point':
        """Create new point relative to this one, specified by vector."""
        return Q2D_Point((self.__x + v.x(), self.__y + v.y()))

    def distance(self, p: 'Q2D_Point') -> float:
        """Calculate distance between this point and another."""
        return ((self.__x - p.x)**2 + (self.__y - p.y)**2)**0.5

    def coincident(self, p: 'Q2D_Point') -> bool:
        """True if this point and another are in the same place."""
        bXco = abs(self.__x - p.x) < Q2D_Design_Tolerance
        bYco = abs(self.__y - p.y) < Q2D_Design_Tolerance
        return bXco and bYco

    @staticmethod
    def from_to(from_point: 'Q2D_Point', to_point: 'Q2D_Point') -> Q2D_Vector:
        """Create a new vector defined between two points."""
        return Q2D_Vector.from_to(to_point.x - from_point.x, to_point.y - from_point.y)

class Q2D_Ellipse(Q2D_Object):

    """2D geometry class 'Ellipse' as a generalisation of 'Circle' (see Q2D_Circle).
    """

    def __init__(self, center: Q2D_Point, semi_major: float, semi_minor: float, rotate: float = 0.0, **kwargs) -> None:
        """New instance of Q2D_Ellipse with specified center, axes and rotation."""
        Q2D_Object.__init__(self, "Ellipse", **kwargs)
        self.center = center
        self.semi_major = semi_major
        self.semi_minor = semi_minor
        self.rotate = rotate
        self.__e_major = Q2D_Vector(rotate)
        self.__e_minor = Q2D_Vector(rotate + math.pi / 2)

    # local coordinate system is a unit circle centered at the origin
    def __local_point_to_global(self, lx: float, ly: float) -> Q2D_Point:
        """Map from unit circle coordinates and create point on the ellipse."""
        gx = lx * self.semi_major * self.__e_major.x(True) + ly * self.semi_minor * self.__e_minor.x(True)
        gy = lx * self.semi_major * self.__e_major.y(True) + ly * self.semi_minor * self.__e_minor.y(True)
        return self.center.cartesian_relative(gx, gy)

    def __local_angle_to_global(self, theta: float) -> float:
        """Adjust angle from unit circle frame to (non-rotated) elliptic."""
        return math.atan2(math.sin(theta) * self.semi_minor, math.cos(theta) * self.semi_major)

    def __global_angle_to_local(self, theta: float) -> float:
        """Adjust angle from (non-rotated) elliptic frame to unit circle."""
        return math.atan2(math.sin(theta) / self.semi_minor, math.cos(theta) / self.semi_major)

    def point_on_circumference(self, theta: float) -> Q2D_Point:
        """Create new point on ellipse in specified direction."""
        theta = self.__global_angle_to_local(theta - self.rotate)
        return self.__local_point_to_global(math.cos(theta), math.sin(theta))

    def project(self, point: Q2D_Point, opposite: bool = False) -> Q2D_Point:
        """Create new point by projecting specified point onto the ellipse."""
        if opposite:
            v = Q2D_Point.from_to(point, self.center)
        else:
            v = Q2D_Point.from_to(self.center, point)
        return self.point_on_circumference(v.theta)

    def poly_points(self, interval: float) -> list:
        """Return list of coordinates (with approximate spacing 'interval') describing the ellipse as a polygon."""
        points = []

        theta = 0.0
        while theta < 2 * math.pi:
            point = self.point_on_circumference(theta)
            points += [[point.x, point.y]]
            radius = self.center.distance(point)
            theta = theta + interval / radius

        return points

class Q2D_Circle(Q2D_Ellipse):

    """2D geometry class 'Circle'.
    """

    def __init__(self, center, radius, **kwargs):
        """New instance of Q2D_Circle with specified center and radius."""
        Q2D_Ellipse.__init__(self, center, radius, radius, **kwargs)
        self._geom = "Circle"
        self.__radius = radius

    @property
    def radius(self) -> float:
        """Circle radius."""
        if self._geom != "Circle":
            Q2D_Error("Request for radius property but not a circle.")
        return self.__radius

    def convert_to_ellipse(self):
        """Convert circle into an ellipse."""
        self._geom = "Ellipse"

class Q2D_Curve(Q2D_Object):

    """2D geometry virtual class for path component curves.

    Only the *first* vertex of a curve can be [None]-type, but no edges or vertices can then be added to it
    A *defined* curve has no [None]-type vertices, at least one edge, and No. vertices = No. edges + 1
    A *component* curve has all [None]-type edges; otherwise, edges must not be [None]-type

    A curve has an associated mesh size and a public 'props' dictionary for general use.
    """

    def __init__(self, geom: str, **kwargs) -> None:
        """New instance of Q2D_Curve with specified geometry."""
        Q2D_Object.__init__(self, geom, **kwargs)
        self.__vertex = [] # list of vertices, not including any arc centres or control points
        self.__edge   = [] # list of edges
        self.__mesh   = kwargs.get("mesh", None)
        self.props = {}

    def __getitem__(self, key: str) -> Q2D_Object: # find first instance of edge or vertex by name
        """Search for component edge or vertex with specified name."""
        value = None
        if key is not None:
            for e in self.__edge:
                if e is None:
                    continue
                if e.name == key:
                    value = e
                    break
            if value is None:
                for v in self.__vertex:
                    if v is None:
                        continue
                    if v.name == key:
                        value = v
                        break
        return value
        
    @property
    def mesh(self) -> float | None:
        """Mesh size associated with curve; or None if not set."""
        return self.__mesh

    @mesh.setter
    def mesh(self, value: float) -> None:
        """Set new mesh size associated with curve and its components; ignored unless new mesh size is smaller."""
        if value is not None:
            new_mesh = float(value)
            if new_mesh <= 0:
                Q2D_Error("New mesh size must be a positive number.")

            if self.__mesh is None:
                self.__mesh = new_mesh
            elif self.__mesh > new_mesh:
                self.__mesh = new_mesh

            for e in self.__edge:
                if e is not None:
                    e.mesh = new_mesh
            for v in self.__vertex:
                if v is not None:
                    v.mesh = new_mesh

    def curve_print(self, indent: str = "") -> None:
        """Diagnostic tool to print out curve component information."""
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
    def start(self) -> Q2D_Point | None:
        """The first vertex of the curve, or None if not set."""
        v0 = None
        if len(self.__vertex) > 0:
            v0 = self.__vertex[0]
        return v0

    @property # last vertex (distinct from first), or None
    def end(self) -> Q2D_Point | None:
        """The last vertex of the curve (after the first), or None if not set."""
        vf = None
        if len(self.__vertex) > 1:
            vf = self.__vertex[-1]
        return vf

    @property # last edge, or None
    def last(self) -> Self | None:
        """The last component curve (edge) of the curve, or None if not set."""
        ef = None
        if len(self.__edge) > 0:
            ef = self.__edge[-1]
        return ef

    @property # list of vertices
    def vertices(self) -> list:
        """A list  of all vertices."""
        return self.__vertex

    @property # list of edges
    def edges(self) -> list:
        """A list  of all component curves (edges)."""
        return self.__edge

    def _curve_begin(self, vertex: Q2D_Point): # start the curve by adding the initial vertex
        """Start a new curve definition by specifying the first vertex."""
        if len(self.__vertex) > 0:
            Q2D_Error("Attempt to begin existing curve.")

        self.__vertex.append(vertex)

    def _curve_append_vertex(self, vertex: Q2D_Point): # add next vertex
        """Add a new vertex to an existing curve."""

        if len(self.__vertex) == 0:
            return self._curve_begin(vertex)

        if vertex is None:
            Q2D_Error("Attempt to append [None]-vertex to curve.")

        if len(self.__vertex) == len(self.__edge): # set this new vertex as the end-point vertex of the last curve
            last = self.last # last edge in list
            if last is not None:
                lvx = last.vertices
                if not vertex.coincident(lvx[-1]):
                    last._curve_append_vertex(vertex)
        else:
            self._curve_append_edge(None) # add (with checks) a [None]-edge between vertices

        v0 = self.__vertex[0]
        if v0.coincident(vertex): # if we return to the start, add in the starting vertex as next point
            self.__vertex.append(v0)
        else:
            self.__vertex.append(vertex)

    def _curve_append_edge(self, edge: 'Q2D_Curve'): # add edge starting at existing curve end-point
        """Add component curve (edge) starting at existing curve end-point."""

        if len(self.__edge) > 0:
            if edge is None and self.__edge[0] is not None:
                Q2D_Error("Attempt to append [None]-edge to non-component curve")
            if edge is not None and self.__edge[0] is None:
                Q2D_Error("Attempt to append defined edge to component curve")

        if len(self.__vertex) == len(self.__edge):
            if edge is None:
                Q2D_Error("Attempt to append [None]-edge out of sequence")

            self._curve_append_vertex(edge.start)
            self.__edge.append(edge)
        elif self.__vertex[0] is None:
            Q2D_Error("Attempt to append edge to curve with undefined start")
        else:
            self.__edge.append(edge)

    def curve_defined(self) -> bool:
        """True if at least one edge and if both ends of the curve are specified."""
        return len(self.__edge) > 0 and len(self.__vertex) == len(self.__edge) + 1

    def component_curve(self) -> bool:
        """True if any (and thus all) edges are [None]-type."""
        bCompC = False
        if len(self.__edge) > 0:
            if self.__edge[0] is None:
                bCompC = True
        return bCompC

    def curve_closed(self) -> bool:
        """True if final vertex is the initial vertex."""
        bClosed = False
        if len(self.__vertex) > 1:
            bClosed = self.__vertex[0].coincident(self.__vertex[-1])
        return bClosed

class Q2D_Line(Q2D_Curve):

    """2D geometry class 'Line'. A Q2D_Curve with a reference/starting vertex and a defined direction.
    """

    def __init__(self, start: Q2D_Point, direction: Q2D_Vector, **kwargs) -> None:
        """New instance of Q2D_Line with reference 2D point and vector-direction."""
        Q2D_Curve.__init__(self, "Line", **kwargs)
        self._curve_begin(start)
        self.direction = direction

    def parallel(self, offset: float, reverse: bool = False) -> 'Q2D_Line':
        """Create new Q2D_Line parallel to this with specified offset (+ve to left); optionally reverse the direction."""
        if reverse:
            d = self.direction.copy().reverse()
        else:
            d = self.direction
        return Q2D_Line(self.start.cartesian_relative(-offset * self.direction.y(True), offset * self.direction.x(True)), d)

    def is_parallel(self, rhs: 'Q2D_Line') -> bool:
        """True if specified line is parallel (or antiparallel) to this."""
        return self.direction.is_parallel(rhs.direction, True)

    def intersection(self, rhs: 'Q2D_Line', offset: float = 0.0, interior: bool = True) -> Q2D_Point:
        """Create new 2D point at intersection with specified line; optional (non-directional) offset; optionally the exterior intersection."""
        if self.is_parallel(rhs):
            Q2D_Error("Attempt to find intersection of parallel lines.")

        d1 = self.direction
        d2 =  rhs.direction
        det = d2.cross(d1)

        if interior and det > 0:
            p1 = self.parallel(-offset).start
            p2 =  rhs.parallel(-offset).start
        else:
            p1 = self.parallel( offset).start
            p2 =  rhs.parallel( offset).start

        c1 = p1.y * d1.x(True) - p1.x * d1.y(True)
        c2 = p2.y * d2.x(True) - p2.x * d2.y(True)
        y = (d1.y(True) * c2 - d2.y(True) * c1) / det
        x = (d1.x(True) * c2 - d2.x(True) * c1) / det

        return Q2D_Point((x, y))

    def project(self, point: Q2D_Point) -> Q2D_Point:
        """Create a new point by projecting a point onto this line."""
        rhs = Q2D_Line(point, self.direction.copy().rotate())
        return self.intersection(rhs)

    def is_colinear(self, rhs: 'Q2D_Line') -> bool:
        """True if specified line is colinear with this."""
        return rhs.start.coincident(self.project(rhs.start))

    def nurbs_cps_wts(self, degree: int) -> tuple[list, list]:
        """Build lists of control point coordinates as (x,y) and weights for a NURBS representation. Note: degree must be 2."""

        if degree != 2:
            Q2D_Error("Only degree=2 is supported currently.")
        if not self.curve_defined():
            Q2D_Error("Curve not fully defined.")

        p0 = self.vertices[0]
        p1 = self.vertices[1]

        sx, sy = p0.x, p0.y
        ex, ey = p1.x, p1.y

        mx = (sx + ex) / 2.0
        my = (sy + ey) / 2.0

        cps = [(sx, sy), (mx, my), (ex, ey)]
        wts = [1.0, 1.0, 1.0]

        return cps, wts

    def poly_points(self, interval: float) -> list:
        """Return list of coordinates (with approximate spacing 'interval') describing the line."""
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

    """2D geometry class 'Arc'. A Q2D_Curve with a reference circle and a defined direction.
    """

    def __init__(self, start: Q2D_Point, circle: Q2D_Circle, clockwise: bool = False, **kwargs) -> None:
        """New instance of Q2D_Arc with reference circle, start point (or None), and direction (default is anticlockwise)."""
        Q2D_Curve.__init__(self, "Arc", **kwargs)
        self._curve_begin(start)
        self.circle = circle
        self.clockwise = clockwise

    @property
    def Ox(self) -> float:
        """x-coordinate of circle center."""
        return self.circle.center.x

    @property
    def Oy(self) -> float:
        """y-coordinate of circle center."""
        return self.circle.center.y

    def check_offset(self, offset: float) -> tuple[bool,float]:
        """Check if an offset-arc is possible; if so return the same offset, otherwise return the limit."""
        bPossible = True
        if self.clockwise:
            if -offset > self.circle.radius:
                offset = -self.circle.radius
                bPossible = False
        else:
            if offset > self.circle.radius:
                offset = self.circle.radius
                bPossible = False
        return bPossible, offset

    def concentric(self, offset: float) -> 'Q2D_Arc':
        """Create new arc offset from this one; for an anticlockwise arc, positive offset is inwards."""
        if self.clockwise:
            offset = -offset
        if self.circle.radius - offset <= 0:
            Q2D_Error("Offset makes arc vanish.")

        v_center = Q2D_Point.from_to(self.start, self.circle.center) # vector pointing inwards
        cc_start = self.start.cartesian_relative(offset * v_center.x(True), offset * v_center.y(True))

        return Q2D_Arc(cc_start, Q2D_Circle(self.circle.center, self.circle.radius - offset), self.clockwise)

    @staticmethod
    def nurbs_angles(theta: tuple, bPeriodic: bool) -> tuple[list,float,int]:
        """Split angular range into smaller arcs, compute the cosine of the half-angle and number of NURBS control points."""
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

    def nurbs_cps_wts(self) -> tuple[list,list]:
        """Create list of control point coordinates as (x,y) and associated weights."""

        if not self.curve_defined():
            Q2D_Error("Curve not fully defined.")

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

    def poly_points(self, interval: float) -> list:
        """Return list of coordinates (with approximate spacing 'interval') describing the arc."""
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

    """2D geometry class 'Path'. A composite Q2D_Curve built out of lines and arcs.
    """

    @staticmethod
    def polygon(points: list) -> 'Q2D_Path':
        """Build a new polygonal Q2D_Path with vertices listed as [(x1,y1) .. (xN,yN)], N > 2."""
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
    def circle(circ: Q2D_Circle) -> 'Q2D_Path':
        """Build a new Q2D_Path describing the specified circle."""
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

    def __init__(self, line_or_arc: Q2D_Curve = None, **kwargs) -> None:
        """New instance of Q2D_Path; optionally with first component curve (Arc or Line)."""
        Q2D_Curve.__init__(self, "Path", **kwargs)

        if line_or_arc is not None:
            if line_or_arc.geom == "Arc" or line_or_arc.geom == "Line":
                self._curve_append_edge(line_or_arc)

    def end_point(self, point: Q2D_Point) -> None:
        """Add final vertex to the path."""
        if point.geom == "Point":
            self._curve_append_vertex(point)
        else:
            Q2D_Error("Invalid geometry type.")

    def __append(self, line_arc_point: Q2D_Object) -> None:
        """Append vertex or component curve (edge) to the path."""
        if line_arc_point.geom == "Point":
            self._curve_append_vertex(line_arc_point)
        elif line_arc_point.geom == "Line" or line_arc_point.geom == "Arc":
            self._curve_append_edge(line_arc_point)
        else:
            Q2D_Error("Invalid geometry type.")

    def __append_line_to_line(self, line: Q2D_Line, transition: float, kwargs: dict) -> tuple[Q2D_Arc,Q2D_Line]:
        """Append line to the path, where the current end of the path is also a line; with transition curve."""
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
    def __intersect_circle(lhs: Q2D_Circle, rhs: Q2D_Circle, kwargs: dict) -> Q2D_Point | None:
        """Create new 2D point (or None if none) at intersection of two circles; optionally choose the second intersection."""
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
    def __intersect_line(line: Q2D_Line, circle: Q2D_Circle, sense: bool) -> tuple[Q2D_Point,float,bool]:
        """Create new 2D point (or None if none) at intersection of line and circle with choice of sense."""
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

    def __append_line_to_arc(self, line: Q2D_Line, transition: float, kwargs: dict) -> tuple[Q2D_Arc,Q2D_Line]:
        """Append line to the path, where the current end of the path is an arc; with transition curve."""
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
                Q2D_Info('Adding line without transition')
                rhs_line = Q2D_Line(point, line.direction)
        else:
            if not arc.clockwise:
                offset = -transition
            else:
                offset = transition

            if point is not None:
                Q2D_Info('point = ({x}, {y}); cross={c}; tangent={t}'.format(x=point.x, y=point.y, c=cross, t=tangent))

            if tangent:
                if (cross > 0.0 and not arc.clockwise) or (cross < 0.0 and arc.clockwise):
                    if not co_sense:
                        Q2D_Info('Co-sense transition should be used here')
                else:
                    if co_sense:
                        Q2D_Info('Contra-sense transition should be used here')

                if co_sense:
                    Q2D_Info('Adding (tangent) line (without transition)')
                    rhs_line = Q2D_Line(line.project(point), line.direction)
                else:
                    Q2D_Info('Adding (tangent) line (with counter-sense transition)')
                    o = Q2D_Circle(arc.circle.center, arc.circle.radius + transition)
                    l = line.parallel(offset)
                    p, c, t = Q2D_Path.__intersect_line(l, o, not farside)
                    #print 'point = (', p.x(), p.y(), '); cross =', c, 'tangent =', t
                    lhs_arc  = Q2D_Arc(arc.circle.project(p), Q2D_Circle(p, transition), clockwise=(not arc.clockwise))
                    rhs_line = Q2D_Line(line.project(p), line.direction)
            elif point is None:
                if (cross > 0.0 and not arc.clockwise) or (cross < 0.0 and arc.clockwise):
                    if not co_sense:
                        Q2D_Info('Co-sense transition should be used here')
                else:
                    if co_sense:
                        Q2D_Info('Contra-sense transition should be used here')

                if co_sense:
                    if transition > arc.circle.radius:
                        o = Q2D_Circle(arc.circle.center, transition - arc.circle.radius)
                        l = line.parallel(-offset)
                        p, c, t = Q2D_Path.__intersect_line(l, o, not farside)
                        if p is not None:
                            Q2D_Info('Adding line (with co-sense transition)')
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
                        Q2D_Info('Adding line (with counter-sense transition)')
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
                            Q2D_Info('Adding line (with co-sense transition)')
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
                        Q2D_Info('Adding (counter-sense) arc (with transition)')
                        #print('point = (', p.x(), p.y(), '); cross =', c, 'tangent =', t)
                        lhs_arc  = Q2D_Arc(arc.circle.project(p), Q2D_Circle(p, transition), clockwise=(not arc.clockwise))
                        rhs_line = Q2D_Line(line.project(p), line.direction)

        return lhs_arc, rhs_line

    def __append_arc_to_line(self, arc: Q2D_Arc, transition: float, kwargs: dict) -> tuple[Q2D_Arc,Q2D_Arc]:
        """Append arc to the path, where the current end of the path is a line; with transition curve."""

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
                Q2D_Error("Unable to add arc without transition")
            Q2D_Info('Adding arc without transition')
            rhs_arc = Q2D_Arc(point, arc.circle, clockwise=arc.clockwise)
        else:
            if arc.clockwise:
                offset = -transition
            else:
                offset = transition

            if point is not None:
                Q2D_Info('point = ({x}, {y}); cross={c}; tangent={t}'.format(x=point.x, y=point.y, c=cross, t=tangent))

            if tangent:
                if (cross > 0.0 and not arc.clockwise) or (cross < 0.0 and arc.clockwise):
                    if not co_sense:
                        Q2D_Info('Co-sense transition should be used here')
                else:
                    if co_sense:
                        Q2D_Info('Contra-sense transition should be used here')

                if co_sense:
                    Q2D_Info('Adding (tangent) arc (without transition)')
                    rhs_arc = Q2D_Arc(point, arc.circle, clockwise=arc.clockwise)
                else:
                    Q2D_Info('Adding (counter-sense tangent) arc (with transition)')
                    o = Q2D_Circle(arc.circle.center, arc.circle.radius + transition)
                    l = line.parallel(-offset)
                    p, c, t = Q2D_Path.__intersect_line(l, o, farside)
                    #print 'point = (', p.x(), p.y(), '); cross =', c, 'tangent =', t
                    lhs_arc = Q2D_Arc(line.project(p), Q2D_Circle(p, transition), clockwise=(not arc.clockwise))
                    rhs_arc = Q2D_Arc(arc.circle.project(p), arc.circle, clockwise=arc.clockwise)
            elif point is None:
                if (cross > 0.0 and not arc.clockwise) or (cross < 0.0 and arc.clockwise):
                    if not co_sense:
                        Q2D_Info('Co-sense transition should be used here')
                else:
                    if co_sense:
                        Q2D_Info('Contra-sense transition should be used here')

                if co_sense:
                    if transition > arc.circle.radius:
                        o = Q2D_Circle(arc.circle.center, transition - arc.circle.radius)
                        l = line.parallel(offset)
                        p, c, t = Q2D_Path.__intersect_line(l, o, farside)
                        if p is not None:
                            Q2D_Info('Adding (co-sense) arc (with transition)')
                            #print 'point = (', p.x(), p.y(), '); cross =', c, 'tangent =', t
                            lhs_arc = Q2D_Arc(line.project(p), Q2D_Circle(p, transition), clockwise=arc.clockwise)
                            rhs_arc = Q2D_Arc(arc.circle.project(p, True), arc.circle, clockwise=arc.clockwise)
                        else:
                            Q2D_Error('Unable to add (co-sense) arc with specified transition; try increasing the transition radius')
                    else:
                        Q2D_Error('Unable to add (co-sense) arc with specified transition; require transition radius > arc radius')
                else:
                    o = Q2D_Circle(arc.circle.center, arc.circle.radius + transition)
                    l = line.parallel(-offset)
                    p, c, t = Q2D_Path.__intersect_line(l, o, farside)
                    if p is not None:
                        Q2D_Info('Adding (counter-sense) arc (with transition)')
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
                            Q2D_Info('Adding (co-sense) arc (with transition)')
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
                        Q2D_Info('Adding (counter-sense) arc (with transition)')
                        #print('point = (', p.x(), p.y(), '); cross =', c, 'tangent =', t)
                        lhs_arc = Q2D_Arc(line.project(p), Q2D_Circle(p, transition), clockwise=(not arc.clockwise))
                        rhs_arc = Q2D_Arc(arc.circle.project(p), arc.circle, clockwise=arc.clockwise)

        return lhs_arc, rhs_arc

    def __append_arc_to_arc(self, rhs: Q2D_Arc, transition: float, kwargs: dict) -> tuple[Q2D_Arc,Q2D_Arc]:
        """Append arc to the path, where the current end of the path is an arc; with transition curve."""
        lhs_arc = None
        rhs_arc = None

        lhs = self.last

        if lhs.circle.center.coincident(rhs.circle.center):
            if lhs.circle.radius != rhs.circle.radius:
                Q2D_Error("Q2D_Path.__append_arc_to_arc: Unable to transition between concentric circles.")
            # we're continuing along the same circle
            if rhs.start is None:
                Q2D_Error("Q2D_Path.__append_arc_to_arc: Transition vertex must be specified when continuing on same circle.")
            if lhs.clockwise != rhs.clockwise:
                print("Q2D_Path.__append_arc_to_arc: warning: Path reverses along itself.")
            if transition > 0.0:
                print("Q2D_Path.__append_arc_to_arc: warning: Non-zero transition radius ignored.")
            return None, rhs # success... ignoring transition curve settings and arc direction

        if transition <= 0.0: # [FIXME: Why not implement 0 also?]
            Q2D_Error("Q2D_Path.__append_arc_to_arc: Transition radius must be positive.")

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
            Q2D_Error("Q2D_Path.__append_arc_to_arc: Unable to intersect arcs.")

        Q2D_Info("Adding arc with transition")
        lhs_point = lhs.circle.project(point, lhs_invert)
        rhs_point = rhs.circle.project(point, rhs_invert)
        lhs_arc = Q2D_Arc(lhs_point, Q2D_Circle(point, transition), clockwise=clockwise)
        rhs_arc = Q2D_Arc(rhs_point, rhs.circle, clockwise=rhs.clockwise)

        return lhs_arc, rhs_arc

    def append(self, line_or_arc: Q2D_Curve, transition: float = 0.0, **kwargs) -> tuple[Q2D_Arc,Q2D_Curve]:
        """Append component curve (edge: Line or Arc) to the path with optional transition curve."""
        if transition is None:
            transition = 0.0
        if transition < 0.0:
            Q2D_Error("Transition radius must not be negative.")

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

    def offset_path(self, offset): # FIXME
        if not self.curve_defined():
            Q2D_Error("Path must be fully defined in order to create offset path!")
        if not self.curve_closed():
            Q2D_Error("Path must be closed in order to create offset path!")
            
        path = Q2D_Path()
        endp = None
        for item in self.edges:
            if item is None:
                Q2D_Error("Unexpected [None]-edge!")

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
        
    def poly_points(self, arc_interval: float, line_interval: float = 0.0) -> list:
        """Return list of coordinates (with approximate spacing 'interval') describing the path."""
        # TODO: Redo all poly_points to use mesh
        # TODO: Would be better to distinguish between Shapes and Curves,
        #       e.g., class ShapeLine and class CurveLine, ShapeCircle amd CurveArc
        points = []
        for item in self.edges:
            if item is None:
                continue
            if item.geom == "Line":
                if line_interval > 0.0:
                    points += item.poly_points(line_interval)
                else:
                    v0 = item.start
                    points += [[v0.x, v0.y]]
            elif item.geom == "Arc":
                points += item.poly_points(arc_interval)

        return points # [FIXME: For open paths this misses the end-point now.]

class Q2D_NURBS_Curve(Q2D_Curve): # non-periodic component curve
    """2D geometry class 'NURBS-Curve'. A Q2D_Curve with a NURBS representation of a Line or Arc.
    """

    def __init__(self, line_or_arc: Q2D_Line | Q2D_Arc, **kwargs) -> None:
        """New instance of Q2D_NURBS_Curve with specified Line or Arc geometry."""
        Q2D_Curve.__init__(self, "NURBS-Curve", **kwargs)

        if line_or_arc.geom != "Line" and line_or_arc.geom != "Arc":
            Q2D_Error("Source geometry must be a fully defined Line or Arc")
        if not line_or_arc.curve_defined():
            Q2D_Error("Source geometry must be a fully defined Line or Arc")

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

        self._curve_append_vertex(line_or_arc.end)

class Q2D_NURBS_Path(Q2D_Curve): # path converted to multiple Nurbs curves
    """2D geometry class 'NURBS-Path'. A Q2D_Curve with a NURBS representation of a Line-Arc path.
    """

    def __init__(self, path: Q2D_Path, **kwargs) -> None:
        """New instance of Q2D_NURBS_Path with specified Line-Arc path geometry."""
        Q2D_Curve.__init__(self, "NURBS-Path", **kwargs)

        if path.geom != "Path" or not path.curve_defined():
            Q2D_Error("Source geometry must be a fully defined Path.")

        for e in path.edges:
            self._curve_append_edge(Q2D_NURBS_Curve(e, **kwargs))

        self._curve_append_vertex(path.end)

class Q2D_Frame(object):
    """A convenience class for defining new 2D points relative to a 2D coordinate system.
    """
    def __init__(self, theta: float = 0.0) -> None:
        """New instance of Q2D_Frame centered at the origin; optionally at a specified angle."""
        self.__Og = Q2D_Point((0.0, 0.0))
        self.theta = theta

    @property
    def Og(self) -> Q2D_Point:
        """The local origin as a 2D point."""
        return self.__Og

    @property
    def e1(self) -> Q2D_Vector:
        """The basis vector for the local x-axis."""
        return self.__e1

    @property
    def e2(self) -> Q2D_Vector:
        """The basis vector for the local y-axis."""
        return self.__e2

    @property
    def theta(self) -> float:
        """The angle of the local coordinate system."""
        return self.__theta

    @theta.setter
    def theta(self, value: float) -> None: # sets orientation relative to global xy-space
        """Set the angle of the local coordinate system and adjust the basis vectors."""
        self.__theta = Q2D_Remap_Angle(value)
        self.__e1 = Q2D_Vector(self.__theta)
        self.__e2 = Q2D_Vector(self.__theta + math.pi / 2.0)

    def e3_rotate(self, theta: float) -> Self: # rotate local frame relative to current rotation
        """Rotate the local coordinate system relative to current rotation."""
        self.theta = self.__theta + theta
        return self

    def l2g(self, l: Q2D_Point) -> Q2D_Point: # translate from local to global space, where l is a Q2D_Point
        """Translate a Q2D_Point from local to global coordinates."""
        gx = self.__Og.x + l.x() * self.__e1.x() + l.y() * self.__e2.x()
        gy = self.__Og.y + l.x() * self.__e1.y() + l.y() * self.__e2.y()
        return Q2D_Point((gx, gy))

    def tuple_to_global(self, l12: tuple[float,float]) -> tuple[float,float]: # translate from local to global space, where l12 is an (x, y) tuple
        """Translate an (x,y) tuple from local to global coordinates."""
        l1, l2 = l12
        gx = self.__Og.x + l1 * self.__e1.x() + l2 * self.__e2.x()
        gy = self.__Og.y + l1 * self.__e1.y() + l2 * self.__e2.y()
        return (gx, gy)

    def local_point_set_origin(self, l: Q2D_Point) -> Self:
        """Move the origin to a Q2D_Point in local coordinates."""
        self.__Og = self.l2g(l)
        return self

    def local_tuple_set_origin(self, l12: tuple[float,float]) -> Self:
        """Move the origin to an (x,y) tuple in local coordinates."""
        self.__Og = Q2D_Point(self.local_to_global(l12))
        return self

    def global_point_set_origin(self, g: Q2D_Point) -> Self:
        """Move the origin to a Q2D_Point in global coordinates."""
        self.__Og = g
        return self

    def global_tuple_set_origin(self, g12: tuple[float,float]) -> Self:
        """Move the origin to an (x,y) tuple in global coordinates."""
        self.__Og = Q2D_Point(g12)
        return self

    def g_pt(self, local_x: float, local_y: float, **kwargs) -> Q2D_Point:
        """Create a global Q2D_Point by specifying local x and y coordinates."""
        return Q2D_Point(self.tuple_to_global((local_x, local_y)), **kwargs)

    def g_vec(self, local_theta: float = 0.0) -> Q2D_Vector:
        """Create a global Q2D_Vector by specifying the angle to the local coordinate system."""
        return Q2D_Vector(self.__theta + local_theta)

    def copy(self) -> Self:
        """Create a copy of the current frame."""
        frame = Q2D_Frame(self.__theta)
        return frame.global_point_set_origin(self.__Og)

def Q2D_BBox(paths: list[Q2D_Path]) -> tuple: # FIXME
    """Determine the bounding box for a list of paths."""
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
