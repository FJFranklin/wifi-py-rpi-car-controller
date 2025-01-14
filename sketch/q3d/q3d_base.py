import math

from q2d_path import Q2D_Curve, Q2D_NURBS_Curve, Q2D_NURBS_Path

class Q3D_Point(object):

    def __init__(self, xyz, **kwargs):
        self.__x = xyz[0]
        self.__y = xyz[1]
        self.__z = xyz[2]
        self.geom  = "Point3D"
        self.props = kwargs

    def desc(self):
        d = self.geom + " [{p}]".format(p=self.props)
        return d

    @property
    def x(self):
        return self.__x

    @property
    def y(self):
        return self.__y

    @property
    def z(self):
        return self.__z

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

    def coincident(self, p): # true if both points are in exactly the same place
        return (self.x == p.x) and (self.y == p.y) and (self.z == p.z)

class Q3D_Vector(object):

    def x(self):
        return self.__x

    def y(self):
        return self.__y

    def z(self):
        return self.__z

    def __init__(self, dx, dy, dz):
        self.__x = dx
        self.__y = dy
        self.__z = dz
        self.__length = (self.__x**2 + self.__y**2 + self.__z**2)**0.5

    def scale_vector(self, scalar):
        return Q3D_Vector(self.__x * scalar, self.__y * scalar, self.__z * scalar)

    def unit(self):
        self.__x /= self.__length
        self.__y /= self.__length
        self.__z /= self.__length
        self.__length = 1.0
        return self

    def add(self, rhs_vector, rhs_scale=1.0): # new vector = self + rhs_vector * rhs_scale
        return Q3D_Vector(self.__x + rhs_vector.x() * rhs_scale,
                          self.__y + rhs_vector.y() * rhs_scale,
                          self.__z + rhs_vector.z() * rhs_scale)

class Q3D_NURBS_Data(object):
    def __init__(self, degree, control_points, weights, knots, multiplicities, periodic):
        self.deg = degree
        self.kts = knots
        self.mps = multiplicities
        self.cps = control_points
        self.wts = weights
        self.per = periodic

    def is_surface(self):
        return type(self.deg) is tuple

class Q3D_Frame(object):
    def local_to_global(self, l123):
        l1, l2, l3 = l123
        gx = self.__Og.x + l1 * self.__e1.x() + l2 * self.__e2.x() + l3 * self.__e3.x()
        gy = self.__Og.y + l1 * self.__e1.y() + l2 * self.__e2.y() + l3 * self.__e3.y()
        gz = self.__Og.z + l1 * self.__e1.z() + l2 * self.__e2.z() + l3 * self.__e3.z()
        return Q3D_Point((gx, gy, gz))

    def tuple_to_global(self, l123):
        l1, l2, l3 = l123
        gx = self.__Og.x + l1 * self.__e1.x() + l2 * self.__e2.x() + l3 * self.__e3.x()
        gy = self.__Og.y + l1 * self.__e1.y() + l2 * self.__e2.y() + l3 * self.__e3.y()
        gz = self.__Og.z + l1 * self.__e1.z() + l2 * self.__e2.z() + l3 * self.__e3.z()
        return (gx, gy, gz)

    def g_pt(self, local_x, local_y, local_z, **kwargs):
        return Q3D_Point(self.tuple_to_global((local_x, local_y, local_z)), **kwargs)

    def local_translate(self, l123):
        self.__Og = Q3D_Point(self.tuple_to_global(l123))

    def e1_rotate(self, theta):
        c = math.cos(theta)
        s = math.sin(theta)
        b2 = self.__e2.scale_vector(c).add(self.__e3,  s).unit()
        b3 = self.__e3.scale_vector(c).add(self.__e2, -s).unit()
        self.__e2 = b2
        self.__e3 = b3

    def e2_rotate(self, theta):
        c = math.cos(theta)
        s = math.sin(theta)
        b3 = self.__e3.scale_vector(c).add(self.__e1,  s).unit()
        b1 = self.__e1.scale_vector(c).add(self.__e3, -s).unit()
        self.__e3 = b3
        self.__e1 = b1

    def e3_rotate(self, theta):
        c = math.cos(theta)
        s = math.sin(theta)
        b1 = self.__e1.scale_vector(c).add(self.__e2,  s).unit()
        b2 = self.__e2.scale_vector(c).add(self.__e1, -s).unit()
        self.__e1 = b1
        self.__e2 = b2

    def __init__(self, Oxyz, vec_e1, vec_e2, vec_e3):
        self.__Og = Oxyz
        self.__e1 = vec_e1
        self.__e2 = vec_e2
        self.__e3 = vec_e3

    def copy(self):
        return Q3D_Frame(self.__Og, self.__e1, self.__e2, self.__e3)

    def sketch_reset(orientation='XY', origin=(0,0,0)):
        O = Q3D_Point(origin)

        if orientation == 'YX':
            B1 = Q3D_Vector( 0.0, 1.0, 0.0)
            B2 = Q3D_Vector( 1.0, 0.0, 0.0)
            B3 = Q3D_Vector( 0.0, 0.0,-1.0)
        elif orientation == 'YZ':
            B1 = Q3D_Vector( 0.0, 1.0, 0.0)
            B2 = Q3D_Vector( 0.0, 0.0, 1.0)
            B3 = Q3D_Vector( 1.0, 0.0, 0.0)
        elif orientation == 'ZY':
            B1 = Q3D_Vector( 0.0, 0.0, 1.0)
            B2 = Q3D_Vector( 0.0, 1.0, 0.0)
            B3 = Q3D_Vector(-1.0, 0.0, 0.0)
        elif orientation == 'XZ':
            B1 = Q3D_Vector( 1.0, 0.0, 0.0)
            B2 = Q3D_Vector( 0.0, 0.0, 1.0)
            B3 = Q3D_Vector( 0.0,-1.0, 0.0)
        elif orientation == 'ZX':
            B1 = Q3D_Vector( 0.0, 0.0, 1.0)
            B2 = Q3D_Vector( 1.0, 0.0, 0.0)
            B3 = Q3D_Vector( 0.0, 1.0, 0.0)
        else: #if orientation == 'XY':
            B1 = Q3D_Vector( 1.0, 0.0, 0.0)
            B2 = Q3D_Vector( 0.0, 1.0, 0.0)
            B3 = Q3D_Vector( 0.0, 0.0, 1.0)

        return Q3D_Frame(O, B1, B2, B3)

    def __angles(self, theta, bPeriodic):
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

    def __kts_mps(self, Ncp, bPeriodic):
        # knots and multiplicities for degree 2 curve
        kts = []
        if bPeriodic:
            mps = [2]
        else:
            mps = [3]
        Narc = int(Ncp / 2)
        for a in range(Narc):
            kts.append(a * 1.0 / Narc)
            if a:
                mps.append(2)
        mps.append(mps[0])
        kts.append(1.0)
        return kts, mps

    def nurbs_ellipse(self, semi_major, semi_minor, **kwargs):
        mesh_min = (semi_major + semi_minor) / 4.0

        base_weight = kwargs.get("base_weight", 1.0)
        post_scale  = kwargs.get("post_scale",  (1.0, 1.0))
        offset      = kwargs.get("offset",      (0.0, 0.0, 0.0))
        rotate      = kwargs.get("rotate",      0.0)
        mesh        = kwargs.get("mesh",        mesh_min)

        if mesh_min < mesh:
            mesh = mesh_min

        # order of transformations: rotate, post-scale, offset
        if rotate:
            cos_r = math.cos(rotate)
            sin_r = math.sin(rotate)
        else:
            cos_r = 1.0
            sin_r = 0.0
        pscale_x, pscale_y = post_scale
        offset_x, offset_y, offset_z = offset

        angles, cha, Ncp = self.__angles(None, True)
        kts, mps = self.__kts_mps(Ncp, True)

        # The initial control point and weight need to be added
        # at the end by the caller to close the loop
        cps = []
        wts = [] # weights get scaled by base_weight

        ha = False
        for a in angles:
            if ha:
                rs = 1.0 / cha
                ha = False
            else:
                rs = 1.0
                ha = True
            x = rs * math.cos(a) * semi_major
            y = rs * math.sin(a) * semi_minor
            tx = offset_x + pscale_x * (cos_r * x - sin_r * y)
            ty = offset_y + pscale_y * (sin_r * x + cos_r * y)
            cp = self.g_pt(tx, ty, offset_z, mesh=mesh)
            cps.append(cp)
            wts.append(base_weight / rs)
        return Q3D_NURBS_Data(2, cps, wts, kts, mps, True)

    def nurbs_path(self, path, **kwargs):
        base_weight = kwargs.get("base_weight", 1.0)
        post_scale  = kwargs.get("post_scale",  (1.0, 1.0))
        offset      = kwargs.get("offset",      (0.0, 0.0, 0.0))
        rotate      = kwargs.get("rotate",      0.0)

        if rotate:
            cos_r = math.cos(rotate)
            sin_r = math.sin(rotate)
        else:
            cos_r = 1.0
            sin_r = 0.0
        pscale_x, pscale_y = post_scale
        offset_x, offset_y, offset_z = offset

        data = None
        item = None

        if path.geom == "Circle" or path.geom == "Ellipse":
            Ox = path.center.x
            Oy = path.center.y
            tx = offset_x + pscale_x * (cos_r * Ox - sin_r * Oy)
            ty = offset_y + pscale_y * (sin_r * Ox + cos_r * Oy)
            kwargs["offset"] = (offset_x + tx, offset_y + ty, offset_z)
            if path.geom == "Circle":
                kwargs["rotate"] = 0.0
                data = self.nurbs_ellipse(path.radius, path.radius, **kwargs)
            elif path.geom == "Ellipse":
                kwargs["rotate"] = rotate + path.rotate
                data = self.nurbs_ellipse(path.semi_major, path.semi_minor, **kwargs)
            return data

        if path.geom != "Path":
            print("* * * Q3D_Frame::nurbs_path: unsupported path type: '" + path.geom + "'")
            return None
        if not path.curve_defined():
            print("* * * Q3D_Frame::nurbs_path: undefined path")
            return None
        if path.component_curve():
            print("* * * Q3D_Frame::nurbs_path: cannot convert a component curve to a Nurbs path")
            return None

        Nline = 0
        Narcs = 0
        bErr  = False
        bPer  = path.curve_closed()

        for item in path.edges:
            if item is None:
                print("* * * Q3D_Frame::nurbs_path: unexpected [None]-edge in path")
                bErr = True
                break
            if item.geom == "Line":
                Nline += 1
            elif item.geom == "Arc":
                Narcs += 1
            else:
                print("* * * Q3D_Frame::nurbs_path: unsupported item type in path: '" + item.geom + "'")
                bErr = True
                break

        if bErr:
            return None
        if Narcs + Nline == 0:
            print("* * * Q3D_Frame::nurbs_path: no lines or arcs in path")
            return None

        cps  = []
        wts  = []
        cp_e = None

        for item in path.edges:
            p1 = item.start
            p2 = item.end

            if item.geom == "Line":
                seg_cps, seg_wts = item.nurbs_cps_wts(2)
            elif item.geom == "Arc":
                seg_cps, seg_wts = item.nurbs_cps_wts()

            Nscp = len(seg_cps)

            for si in range(Nscp):
                x, y = seg_cps[si]
                tx   = offset_x + pscale_x * (cos_r * x - sin_r * y)
                ty   = offset_y + pscale_y * (sin_r * x + cos_r * y)
                cp3  = self.g_pt(tx, ty, offset_z)
                if si == 0:
                    cp3.mesh = p1.mesh
                if si == Nscp - 1:
                    cp3.mesh = p2.mesh
                    cp_e = cp3 # the end point is not automatically added to the list
                    wt_e = seg_wts[Nscp - 1]
                else:
                    cps.append(cp3)
                    wts.append(seg_wts[si])

        if not bPer:
            cps.append(cp_e)
            wts.append(wt_e)

        kts, mps = self.__kts_mps(len(cps), bPer)

        return Q3D_NURBS_Data(2, cps, wts, kts, mps, bPer)

    def nurbs_torus(self, radius, semi_major, semi_minor, **kwargs):
        pitch = kwargs.get("pitch", 0.0)
        theta = kwargs.get("theta", None)

        # the initial control points and weights need to be
        # added at the end by the caller to close the surface
        deg1 = None
        kts1 = None
        mps1 = None
        per1 = None
        deg2 = 2
        cps = []
        wts = []

        if pitch == 0.0 and theta is not None:
            t1, t2 = theta
            if math.fabs(t2 - t1) >= 2.0 * math.pi:
                theta = None # we have a full torus
        if pitch == 0.0 and theta is None:
            per2 = True      # doubly periodic surface
        else:
            per2 = False

        angles, cha, Ncp = self.__angles(theta, per2)
        kts2, mps2 = self.__kts_mps(Ncp, per2)

        ha = False
        for a in angles:
            if ha:
                rs = cha
                ha = False
            else:
                rs = 1.0
                ha = True

            frame = self.copy()
            frame.e1_rotate(a)
            frame.local_translate((pitch * a * 0.5 / math.pi, radius / rs, 0))

            kwargs["base_weight"] = rs
            kwargs["post_scale"]  = (1.0, 1.0 / rs)
            data = frame.nurbs_ellipse(semi_major, semi_minor, **kwargs)
            cps.append(data.cps)
            wts.append(data.wts)

            if deg1 is None:
                deg1 = data.deg
                kts1 = data.kts
                mps1 = data.mps
                per1 = data.per

        return Q3D_NURBS_Data((deg1, deg2), cps, wts, (kts1, kts2), (mps1, mps2), (per1, per2))

class Q3D_NURBS_Curve(Q2D_Curve): # convert non-periodic component NURBS curve from 2D to 3D
    def __init__(self, frame, nurbs_curve_2d, **kwargs):
        Q2D_Curve.__init__(self, "NURBS-Curve-3D", **kwargs)
        if nurbs_curve_2d.geom != "NURBS-Curve" or not nurbs_curve_2d.curve_defined():
            print("* * * Q3D_NURBS_Curve::__init__: source geometry must be a fully defined 2D NURBS curve")
        else:
            base_weight = kwargs.get("base_weight", 1.0)
            post_scale  = kwargs.get("post_scale",  (1.0, 1.0))
            offset      = kwargs.get("offset",      (0.0, 0.0, 0.0))
            rotate      = kwargs.get("rotate",      0.0)

            self.wts = []
            for wt in nurbs_curve_2d.wts:
                self.wts.append(base_weight * wt)

            self.deg = nurbs_curve_2d.deg
            self.kts = nurbs_curve_2d.kts
            self.mps = nurbs_curve_2d.mps

            # order of transformations: rotate, post-scale, offset
            if rotate:
                cos_r = math.cos(rotate)
                sin_r = math.sin(rotate)
            else:
                cos_r = 1.0
                sin_r = 0.0
            pscale_x, pscale_y = post_scale
            offset_x, offset_y, offset_z = offset

            Ncp = len(nurbs_curve_2d.cps)

            arc_ends = kwargs.get("arc_ends")
            if arc_ends is not None:
                v3i, v3f = arc_ends
            else:
                v3i = None
                v3f = None

            self.cps = []
            for cpi in range(Ncp):
                if cpi == 0 and v3i is not None:
                    self.cps.append(v3i)
                    continue
                if cpi == Ncp - 1 and v3f is not None:
                    self.cps.append(v3f)
                    continue
                cp2 = nurbs_curve_2d.cps[cpi]
                tx  = offset_x + pscale_x * (cos_r * cp2.x - sin_r * cp2.y)
                ty  = offset_y + pscale_y * (sin_r * cp2.x + cos_r * cp2.y)
                cp3 = frame.g_pt(tx, ty, offset_z, mesh=cp2.mesh)
                self.cps.append(cp3)
            for cp3 in self.cps:
                self._curve_append_vertex(cp3)

class Q3D_NURBS_Path(Q2D_Curve): # path converted to multiple Nurbs curves
    def __init__(self, frame, path, **kwargs):
        Q2D_Curve.__init__(self, "NURBS-Path-3D", **kwargs)
        if path.geom != "NURBS-Path" or not path.curve_defined():
            print("* * * Q3D_NURBS_Path::__init__: source geometry must be a fully defined NURBS Path")
        else:
            base_weight = kwargs.get("base_weight", 1.0)
            post_scale  = kwargs.get("post_scale",  (1.0, 1.0))
            offset      = kwargs.get("offset",      (0.0, 0.0, 0.0))
            rotate      = kwargs.get("rotate",      0.0)

            # order of transformations: rotate, post-scale, offset
            if rotate:
                cos_r = math.cos(rotate)
                sin_r = math.sin(rotate)
            else:
                cos_r = 1.0
                sin_r = 0.0
            pscale_x, pscale_y = post_scale
            offset_x, offset_y, offset_z = offset

            cps = []
            for cp2 in path.vertices:
                tx  = offset_x + pscale_x * (cos_r * cp2.x - sin_r * cp2.y)
                ty  = offset_y + pscale_y * (sin_r * cp2.x + cos_r * cp2.y)
                cp3 = frame.g_pt(tx, ty, offset_z, mesh=cp2.mesh)
                cps.append(cp3)

            v3i = cps[0]
            self._curve_append_vertex(v3i)
            for cpi in range(1,len(cps)):
                v3f = cps[cpi]
                ends = (v3i, v3f)
                curve_2d = path.edges[cpi-1]
                curve_3d = Q3D_NURBS_Curve(frame, curve_2d, arc_ends=ends, **kwargs)
                self._curve_append_edge(curve_3d)
                self._curve_append_vertex(v3f)
                v3i = v3f
