import math

from q3d_base import *
from q2d_path import *

class Q3D_Draw(object):

    __counter = 0

    def __new_expr_id(self):
        Q3D_Draw.__counter += 1
        return Q3D_Draw.__counter

    def __init__(self, mesh_default=0.1):
        self.mesh = mesh_default

    def __draw_point(self, point, **kwargs):
        # check to see if this point has been added already
        if "id" in point.props:
            return point.props["id"]

        # use the minimum mesh size out of: (1) the current default;
        # (2) keyword-specified, if any; (3) point-specific dictionary
        mesh = self.mesh
        if "mesh" in kwargs:
            kw_mesh = kwargs["mesh"]
            if kw_mesh is not None:
                if mesh is None:
                    mesh = kw_mesh
                elif kw_mesh < mesh:
                    mesh = kw_mesh
        if "mesh" in point.props:
            pp_mesh = point.props["mesh"]
            if pp_mesh is not None:
                if mesh is None:
                    mesh = pp_mesh
                elif pp_mesh < mesh:
                    mesh = pp_mesh
        print("mesh: {s} / {k} / {p} => {f} ({x:.3f},{y:.3f})".format(s=self.mesh, k=kwargs.get("mesh"),
                                                                      p=point.props.get("mesh"), f=mesh,
                                                                      x=point.x, y=point.y))
        p_id = self.__new_expr_id()
        gmsh.model.occ.addPoint(point.x, point.y, point.z, mesh, p_id)
        point.props["id"] = p_id
        return p_id

    def __draw_loop(self, segments):
        loop_id = self.__new_expr_id()
        gmsh.model.occ.addCurveLoop(segments, loop_id)
        return loop_id

    def __pp_curve(self, name, loops): # create physical planar surface
        gmsh.model.occ.synchronize()
        physcurv_id = self.__new_expr_id()
        gmsh.model.addPhysicalGroup(1, loops, tag=physcurv_id, name=name)
        return physcurv_id

    def __pp_surface(self, name, loops): # create physical planar surface
        plane_id = self.__new_expr_id()
        gmsh.model.occ.addPlaneSurface(loops, plane_id)
        gmsh.model.occ.synchronize()
        physsurf_id = self.__new_expr_id()
        gmsh.model.addPhysicalGroup(2, [plane_id], tag=physsurf_id, name=name)
        return (plane_id, physsurf_id)

    def __draw_nurbs_curve(self, name, data, cps_wts, **kwargs):
        bSurface = kwargs.get("surface", True)

        if cps_wts is None:
            cps = []
            wts = data.wts
            for cp in data.cps:
                cps.append(self.__draw_point(cp, **kwargs))
            if data.per: # periodic; need to add the beginning in as the end
                cps.append(cps[0])
                wts.append(wts[0])
        else:
            cps, wts = cps_wts

        loop_id = None
        plane_id = None
        phys_id = None
        curve_id = self.__new_expr_id()
        gmsh.model.occ.addBSpline(cps, tag=curve_id, degree=data.deg, weights=wts,
                                  knots=data.kts, multiplicities=data.mps)
        if data.per:
            if bSurface:
                loop_id = self.__draw_loop([curve_id])
                pp = self.__pp_surface(name, [loop_id])
                plane_id, phys_id = pp
            else:
                loop_id = None
                plane_id = None
                phys_id = self.__pp_curve(name, [curve_id])
        else:
            loop_id = None
            plane_id = None
            phys_id = self.__pp_curve(name, [curve_id])
        return (curve_id, loop_id, plane_id, phys_id)

    def __draw_nurbs_surface(self, name, data, **kwargs):
        face_f_ids = None
        face_b_ids = None

        deg1, deg2 = data.deg
        kts1, kts2 = data.kts
        mps1, mps2 = data.mps
        per1, per2 = data.per
        dim1 = len(data.cps[0])
        dim2 = len(data.cps)
        cps = []
        wts = []
        for i2 in range(dim2):
            cpsf = []
            wtsf = []
            cp_list = data.cps[i2]
            wt_list = data.wts[i2]
            for i1 in range(dim1):
                cp = cp_list[i1]
                wt = wt_list[i1]
                cp_id = self.__draw_point(cp, **kwargs)
                cps.append(cp_id)
                wts.append(wt)
                if per1 and i1 == 0:
                    cp_wt_1st = (cp_id, wt)
                if per1 and not per2:
                    if i2 == 0 or i2 == dim2 - 1:
                        cpsf.append(cp_id)
                        wtsf.append(wt)
            if per1:
                cp_id, wt = cp_wt_1st
                cps.append(cp_id)
                wts.append(wt)
                if not per2:
                    if i2 == 0:
                        face_name = name + "_front"
                    elif i2 == dim2 - 1:
                        face_name = name + "_back"
                    if i2 == 0 or i2 == dim2 - 1:
                        cpsf.append(cp_id)
                        wtsf.append(wt)
                        face_data = Q3D_NURBS_Data(deg1, None, None, kts1, mps1, per1)
                        face_ids = self.__draw_nurbs_curve(face_name, face_data, (cpsf, wtsf), **kwargs)
                    if i2 == 0:
                        face_f_ids = face_ids
                    elif i2 == dim2 - 1:
                        face_b_ids = face_ids
        if per1:
            dim1 += 1
        if per2:
            for i1 in range(dim1):
                cps.append(cps[i1])
                wts.append(wts[i1])
            dim2 += 1

        surface_id = self.__new_expr_id()
        gmsh.model.occ.addBSplineSurface(cps, dim1, tag=surface_id, degreeU=deg1, degreeV=deg2,
                                         weights=wts, knotsU=kts1, knotsV=kts2,
                                         multiplicitiesU=mps1, multiplicitiesV=mps2)
        gmsh.model.occ.synchronize()

        physsurf_id = self.__new_expr_id()
        gmsh.model.addPhysicalGroup(2, [surface_id], tag=physsurf_id, name=name)

        return (surface_id, physsurf_id, face_f_ids, face_b_ids)

    def draw_nurbs(self, name, data, **kwargs):
        if data.is_surface():
            return self.__draw_nurbs_surface(name, data, **kwargs)
        return self.__draw_nurbs_curve(name, data, None, **kwargs)

    def __draw_circle_arc(self, arc_center, arc_start, arc_end):
        curve_id = self.__new_expr_id()
        gmsh.model.occ.addCircleArc(arc_start, arc_center, arc_end, tag=curve_id)
        return curve_id

    def __draw_circle(self, circle, frame, **kwargs):
        c0 = circle.center

        c0.mesh = circle.radius / 2.0
        kw_min_mesh = kwargs.get("mesh")
        if kw_min_mesh is not None:
            c0.mesh = kw_min_mesh

        mesh = c0.mesh

        x0 = circle.center.start[0]
        y0 = circle.center.start[1]

        p0 = self.__draw_point(frame.g_pt(x0, y0,                 0.0, mesh=mesh))
        p1 = self.__draw_point(frame.g_pt(x0 + circle.radius, y0, 0.0, mesh=mesh))
        p2 = self.__draw_point(frame.g_pt(x0, y0 + circle.radius, 0.0, mesh=mesh))
        p3 = self.__draw_point(frame.g_pt(x0 - circle.radius, y0, 0.0, mesh=mesh))
        p4 = self.__draw_point(frame.g_pt(x0, y0 - circle.radius, 0.0, mesh=mesh))

        c1 = self.__draw_circle_arc(p0, p1, p2) # TODO: add axis vector
        c2 = self.__draw_circle_arc(p0, p2, p3)
        c3 = self.__draw_circle_arc(p0, p3, p4)
        c4 = self.__draw_circle_arc(p0, p4, p1)

        return self.__draw_loop([c1,c2,c3,c4])

    def __angles(self, theta, mesh):
        # split range into angles of 120 degrees or less
        # also return: mesh list of corresponding mesh sizes

        t1, t2 = theta
        m1, m2 = mesh
        if m1 is None:
            m1 = self.mesh
        if m2 is None:
            m2 = self.mesh

        Narc = int(math.ceil(math.fabs(t2 - t1) * 1.5 / math.pi))

        angles = [t1]
        meshes = [m1]
        for a in range(1, Narc):
            angles.append(t1 + (t2 - t1) * a * 1.0 / Narc)
            meshes.append(m1 + (m2 - m1) * a * 1.0 / Narc)
        angles.append(t2)
        meshes.append(m2)

        return Narc, angles, meshes

    def __draw_arc(self, arc, frame, arc_ends, **kwargs):
        segs = []

        c0 = arc.circle.center

        kw_min_mesh = kwargs.get("mesh", arc.circle.radius / 2.0)
        c0.mesh = kw_min_mesh

        x0 = arc.Ox
        y0 = arc.Oy
        p0 = self.__draw_point(frame.g_pt(x0, y0, 0.0, mesh=c0.mesh))

        v3i, v3f = arc_ends # 3D points at curve ends

        p1 = arc.start
        p2 = arc.end

        p1.mesh = kw_min_mesh
        p2.mesh = kw_min_mesh

        t1 = math.atan2(p1.y - y0, p1.x - x0)
        t2 = math.atan2(p2.y - y0, p2.x - x0)
        # Note: math.atan2 returns -pi..pi
        if arc.clockwise:
            if t1 <= t2:
                t1 += 2.0 * math.pi
        else:
            if t2 <= t1:
                t2 += 2.0 * math.pi

        Narc, angles, meshes = self.__angles((t1, t2), (p1.mesh, p2.mesh))
        pa = [v3i]
        for n in range(Narc-1): # create points first
            a = angles[n+1]
            m = meshes[n+1]
            x = x0 + arc.circle.radius * math.cos(a)
            y = y0 + arc.circle.radius * math.sin(a)
            pa.append(self.__draw_point(frame.g_pt(x, y, 0.0, mesh=m)))

        pa.append(v3f)

        for n in range(Narc): # cthen draw the curves
            if arc.clockwise:
                a1 = pa[n+1]
                a2 = pa[n]
            else:
                a1 = pa[n]
                a2 = pa[n+1]
            s = self.__draw_circle_arc(p0, a1, a2)
            if arc.clockwise:
                segs.append(-s)
            else:
                segs.append(s)

        return segs

    def __draw_line(self, line, frame, arc_ends, **kwargs):
        v3i, v3f = arc_ends # 3D points at curve ends

        curve_id = self.__new_expr_id()
        gmsh.model.occ.addLine(v3i, v3f, curve_id)
        return curve_id

    def __draw_path(self, path, frame, **kwargs):
        if not path.curve_defined():
            print("* * * Q3D_Draw::__draw_path: path is not defined")
            return None
        if path.component_curve():
            print("* * * Q3D_Draw::__draw_path: unable to draw component path")
            return None
        if not path.curve_closed():
            print("* * * Q3D_Draw::__draw_path: path not a loop - unsupported") # FIXME
            return None

        bErr = False

        e2D = path.edges
        v2D = path.vertices
        v3D = []
        for v2 in v2D:
            if v2 is None:
                print("* * * Q3D_Draw::__draw_path: unexpected [None]-vertex in path")
                bErr = True
                break
            v3 = frame.g_pt(v2.x, v2.y, 0.0, mesh=v2.mesh)
            v3D.append(self.__draw_point(v3))

        arc_segs = []
        for ei in range(len(e2D)):
            item = e2D[ei]
            v3i  = v3D[ei]
            v3f  = v3D[ei+1]
            ends = (v3i, v3f)

            if item is None:
                print("* * * Q3D_Draw::__draw_path: unexpected [None]-edge in path")
                bErr = True
                break
            if item.geom == "Line":
                s = self.__draw_line(item, frame, ends, **kwargs)
                arc_segs.append(s)
            elif item.geom == "Arc":
                segs = self.__draw_arc(item, frame, ends, **kwargs)
                arc_segs = arc_segs + segs
            else:
                print("* * * Q3D_Draw::__draw_path: unsupported item type in path: '" + item.geom + "'")
                bErr = True
                break

        if bErr:
            return None

        return self.__draw_loop(arc_segs)

    def draw_path(self, path, frame=None, **kwargs):
        if frame is None:
            frame = Q3D_Frame.sketch_reset()

        loop_id = None

        if path.geom == "Path":
            loop_id = self.__draw_path(path, frame, **kwargs)
        elif path.geom == "Circle":
            loop_id = self.__draw_circle(path, frame, **kwargs)

        return loop_id

    def __draw_nurbs_curve_3d(self, curve, **kwargs):
        cps = []
        for cp in curve.cps:
            cps.append(self.__draw_point(cp))

        curve_id = self.__new_expr_id()
        gmsh.model.occ.addBSpline(cps, tag=curve_id, degree=curve.deg, weights=curve.wts,
                                  knots=curve.kts, multiplicities=curve.mps)
        curve.props["gmsh:id"] = curve_id
        return curve_id

    def draw_nurbs_path_3d(self, path, **kwargs):
        if path.geom != "NURBS-Path-3D":
            return None

        name = kwargs.get("name", path.name)
        if name is None:
            name = "untitled"

        curve_ids = []
        for curve in path.edges:
            curve_ids.append(self.__draw_nurbs_curve_3d(curve))

        if path.curve_closed():
            path_id = self.__draw_loop(curve_ids)
            phys_id = self.__pp_curve(name, curve_ids)
        else:
            path_id = self.__new_expr_id()
            phys_id = self.__new_expr_id()
            print("* * * Q3D_Draw::draw_nurbs_path_3d: Open paths are not yet implemented") # FIXME

        path.props["gmsh:id"] = path_id
        path.props["gmsh:pc"] = phys_id

        return path_id, phys_id

    def make_surface(self, name, loop_ids):
        return self.__pp_surface(name, loop_ids)

if __name__ == '__main__':
    from q2d_tests import Q2D_Arc_Test

    bPlotEllipseTests = False
    bPlotTorusTests = False
    bPlotPathTests = False
    bPlotNurbsPathTests = True
    bPlotPathEllipseTests = False
    bPlotPathSimpleTests = False
    bPlotPathCompoundTests = False
    bBuildMesh = True

    from q2d_tests import Q2D_Arc_Test

    import gmsh
    import sys

    gmsh.initialize(sys.argv)

    gmsh.model.add("torus")

    Geo = Q3D_Draw(0.5)

    def test_ellipse(orientation, origin, semi_major, semi_minor, **kwargs):
        frame = Q3D_Frame.sketch_reset(orientation, origin)
        data = frame.nurbs_ellipse(semi_major, semi_minor)
        return Geo.draw_nurbs("ellipse-" + orientation, data, **kwargs)

    def test_torus(orientation, origin, radius, semi_major, semi_minor, pitch=0.0, theta=None, **kwargs):
        frame = Q3D_Frame.sketch_reset(orientation, origin)
        data = frame.nurbs_torus(radius, semi_major, semi_minor, pitch, theta)
        return Geo.draw_nurbs("torus-" + orientation, data, **kwargs)

    if bPlotEllipseTests:
        C1 = test_ellipse('XY', (-1.0, 0.0, 0.0), 1.0, 1.0)
        C2 = test_ellipse('YZ', ( 0.0,-1.0, 0.0), 0.8, 0.3, mesh=0.1)
        C3 = test_ellipse('ZX', ( 0.0, 0.0,-1.0), 0.2, 0.9)

    if bPlotTorusTests:
        S1 = test_torus('XY', ( 1.0, 0.0, 0.0),   1, 0.2, 0.2, mesh=0.05)
        S2 = test_torus('YZ', ( 0.5, 0.0, 1.0),   1, 0.2, 0.2, 0.0, (-0.25*math.pi,1.25*math.pi))
        S3 = test_torus('ZX', ( 0.0, 0.0, 0.5), 0.6, 0.1, 0.3, 0.5, ( 0.25*math.pi,4.25*math.pi))

    if bPlotNurbsPathTests:
        test = 5
        paths = Q2D_Arc_Test(test)
        frame = Q3D_Frame.sketch_reset()
        count = 0
        for path in paths:
            if path.curve_closed():
                text = " (closed)"
            else:
                text = " (open)"
            print("Converting path: test-" + str(test) + str(count) + text)
            N2D_path = Q2D_NURBS_Path(path)
            N3D_path = Q3D_NURBS_Path(frame, N2D_path)
            path_id, phys_id = Geo.draw_nurbs_path_3d(N3D_path)
            if path.curve_closed():
                Geo.make_surface("test-" + str(test), [path_id])
            print("done.")
            count += 1

    if bPlotPathTests:
        test = 5
        paths = Q2D_Arc_Test(test)
        frame = Q3D_Frame.sketch_reset()
        count = 0
        for path in paths:
            print("Converting path: test-" + str(test) + str(count))
            data = frame.nurbs_path(path)
            if data:
                Geo.draw_nurbs("test-" + str(test) + str(count), data, surface=True)
            count += 1
            print("done.")

    if bPlotPathEllipseTests:
        C = Q2D_Circle(Q2D_Point((0.9, 0.1)), 0.05)
        E = Q2D_Ellipse(Q2D_Point((1.0, 0.0)), 0.2, 0.1, rotate=math.pi/4.0)
        frame = Q3D_Frame.sketch_reset()
        for angle in range(0, 360, 20):
            data = frame.nurbs_path(E, rotate=math.radians(angle))
            if data:
                Geo.draw_nurbs("e-" + str(angle), data)
            data = frame.nurbs_path(C, rotate=math.radians(angle))
            if data:
                Geo.draw_nurbs("c-" + str(angle), data)

    if bPlotPathSimpleTests:
        test = 5
        paths = Q2D_Arc_Test(test)
        frame = Q3D_Frame.sketch_reset()
        count = 0
        for path in paths:
            print("Drawing path: test-" + str(test) + str(count))
            loop = Geo.draw_path(path, frame)
            Geo.make_surface("test-" + str(test), [loop])
            count += 1
            print("done.")

    if bPlotPathCompoundTests:
        test = 2
        paths = Q2D_Arc_Test(test)
        frame = Q3D_Frame.sketch_reset()
        symmetry = 5
        for p in range(symmetry):
            loops = []
            count = 0
            for path in paths:
                print("Drawing path: test-" + str(test) + str(count))
                loops.append(Geo.draw_path(path, frame))
                count += 1
                print("done.")
            Geo.make_surface("test-" + str(test), loops)
            frame.e2_rotate(math.pi * 2.0 / symmetry)

    if bBuildMesh:
        gmsh.model.mesh.generate(2)

    if "-nopopup" not in sys.argv:
        gmsh.fltk.run()

    gmsh.finalize()
