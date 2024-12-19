import math

class Q3D_Point(object):

    def __init__(self, xyz, **kwargs):
        self.__x = xyz[0]
        self.__y = xyz[1]
        self.__z = xyz[2]
        self.name  = "Point3D"
        self.props = kwargs

    def x(self):
        return self.__x

    def y(self):
        return self.__y

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
        gx = self.__Og.x() + l1 * self.__e1.x() + l2 * self.__e2.x() + l3 * self.__e3.x()
        gy = self.__Og.y() + l1 * self.__e1.y() + l2 * self.__e2.y() + l3 * self.__e3.y()
        gz = self.__Og.z() + l1 * self.__e1.z() + l2 * self.__e2.z() + l3 * self.__e3.z()
        return Q3D_Point((gx, gy, gz))

    def tuple_to_global(self, l123):
        l1, l2, l3 = l123
        gx = self.__Og.x() + l1 * self.__e1.x() + l2 * self.__e2.x() + l3 * self.__e3.x()
        gy = self.__Og.y() + l1 * self.__e1.y() + l2 * self.__e2.y() + l3 * self.__e3.y()
        gz = self.__Og.z() + l1 * self.__e1.z() + l2 * self.__e2.z() + l3 * self.__e3.z()
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

        if path.name == "Circle":
            Ox, Oy = path.center.start
            tx = offset_x + pscale_x * (cos_r * Ox - sin_r * Oy)
            ty = offset_y + pscale_y * (sin_r * Ox + cos_r * Oy)
            kwargs["offset"] = (offset_x + tx, offset_y + ty, offset_z)
            kwargs["rotate"] = 0.0
            data = self.nurbs_ellipse(path.radius, path.radius, **kwargs)
        elif path.name == "Ellipse":
            Ox, Oy = path.center.start
            tx = offset_x + pscale_x * (cos_r * Ox - sin_r * Oy)
            ty = offset_y + pscale_y * (sin_r * Ox + cos_r * Oy)
            kwargs["offset"] = (offset_x + tx, offset_y + ty, offset_z)
            kwargs["rotate"] = rotate + path.rotate
            data = self.nurbs_ellipse(path.semi_major, path.semi_minor, **kwargs)
        elif path.name == "Path":
            print("info: Path")
            item = path.chain
        else:
            print("* * * (oops: unsupported path type: '" + path.name + "') * * *")

        if item is None:
            return data

        Nline = 0
        Narcs = 0
        bErr  = False
        bPer  = False
        p0    = item.start

        while item is not None:
            if item.name == "Line":
                Nline += 1
            elif item.name == "Arc":
                Narcs += 1
            elif item.name == "Point":
                if p0 == item:
                    bPer = True
                else:
                    print("Note: non-periodic end-point")
                break
            else:
                print("* * * (oops: unsupported item type in path: '" + path.name + "') * * *")
                bErr = True
                break

            item = item.chain

        if bErr:
            return data
        if Narcs + Nline == 0:
            print("* * * (oops: no lines or arcs in path) * * *")
            return data

        cps  = []
        wts  = []
        item = path.chain
        cp_e = None

        while item is not None:
            if item.name == "Point":
                break

            p1 = item.start
            p2 = item.chain
            if p2.name != "Point":
                p2 = p2.start

            if item.name == "Line":
                seg_cps, seg_wts, seg_mmin = self.__cps_deg2_line((p1.x(), p1.y()), (p2.x(), p2.y()))
            elif item.name == "Arc":
                seg_cps, seg_wts, seg_mmin = self.__cps_deg2_arc((item.Ox(), item.Oy()),
                                                                 (p1.x(), p1.y()), (p2.x(), p2.y()),
                                                                 item.circle.radius, item.clockwise)

            Nscp = len(seg_cps)

            # Note: minimum mesh size can be reduced by assignment, but not increased
            item.mesh = seg_mmin
            p1.mesh = item.mesh
            p2.mesh = item.mesh

            for si in range(Nscp):
                x, y = seg_cps[si]
                tx   = offset_x + pscale_x * (cos_r * x - sin_r * y)
                ty   = offset_y + pscale_y * (sin_r * x + cos_r * y)
                cp3  = self.g_pt(tx, ty, offset_z)
                if si == 0:
                    cp3.mesh = p1.mesh
                else:
                    cp3.mesh = item.mesh
                if si == Nscp - 1:
                    cp_e = cp3 # the end point is not automatically added to the list
                    wt_e = seg_wts[Nscp - 1]
                else:
                    cps.append(cp3)
                    wts.append(seg_wts[si])

            item = item.chain

        if not bPer:
            cps.append(cp_e)
            wts.append(wt_e)

        kts, mps = self.__kts_mps(len(cps), bPer)

        return Q3D_NURBS_Data(2, cps, wts, kts, mps, bPer)

    def __cps_deg2_line(self, p_start, p_end):
        # return list of control point coordinates as (x,y), and a suggested minimum mesh size
        sx, sy = p_start
        ex, ey = p_end
        mx = (sx + ex) / 2.0
        my = (sy + ey) / 2.0

        cps = [(sx, sy), (mx, my), (ex, ey)]
        wts = [1.0, 1.0, 1.0]

        mesh_min = math.sqrt((ex - sx)**2 + (ey - sy)**2) / 2.0
        return cps, wts, mesh_min

    def __cps_deg2_arc(self, p_center, p_start, p_end, radius, bClockwise):
        # return list of control point coordinates as (x,y), and a suggested minimum mesh size
        ox, oy = p_center
        sx, sy = p_start
        ex, ey = p_end
        ts = math.atan2(sy - oy, sx - ox)
        te = math.atan2(ey - oy, ex - ox)
        if ts > te and not bClockwise:
            ts -= 2.0 * math.pi
        if te > ts and bClockwise:
            ts += 2.0 * math.pi

        angles, cha, Ncp = self.__angles((ts, te), False)
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

            x = ox + radius * math.cos(a) / rs
            y = oy + radius * math.sin(a) / rs
            cps.append((x, y))
            wts.append(rs)

        mesh_min = radius / 2.0
        return cps, wts, mesh_min

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
            kwargs["post_scale"]  = (1.0 / rs, 1.0)
            data = frame.nurbs_ellipse(semi_major, semi_minor, **kwargs)
            cps.append(data.cps)
            wts.append(data.wts)

            if deg1 is None:
                deg1 = data.deg
                kts1 = data.kts
                mps1 = data.mps
                per1 = data.per

        return Q3D_NURBS_Data((deg1, deg2), cps, wts, (kts1, kts2), (mps1, mps2), (per1, per2))
