import math

from q3d_base import *
from q2d_path import *
from q2d_tests import Q2D_Arc_Test

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
            if kw_mesh < mesh:
                mesh = kw_mesh
        if "mesh" in point.props:
            pp_mesh = point.props["mesh"]
            if pp_mesh < mesh:
                mesh = pp_mesh
        print("mesh: {s} / {k} / {p} => {f} ({x:.3f},{y:.3f})".format(s=self.mesh, k=kwargs.get("mesh"),
                                                                      p=point.props.get("mesh"), f=mesh,
                                                                      x=point.x(), y=point.y()))
        p_id = self.__new_expr_id()
        gmsh.model.occ.addPoint(point.x(), point.y(), point.z(), mesh, p_id)
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

        c0.mesh = arc.circle.radius / 2.0
        kw_min_mesh = kwargs.get("mesh")
        if kw_min_mesh is not None:
            c0.mesh = kw_min_mesh

        x0 = arc.circle.center.start[0]
        y0 = arc.circle.center.start[1]
        p0 = self.__draw_point(frame.g_pt(x0, y0, 0.0, mesh=c0.mesh), **kwargs)

        arc_final = True
        p1 = arc.start
        p2 = arc.chain
        if p2.name != "Point":
            p2 = p2.start
            arc_final = False
        if kw_min_mesh is not None:
            p1.mesh = kw_min_mesh
            p2.mesh = kw_min_mesh

        t1 = math.atan2(p1.start[1] - y0, p1.start[0] - x0)
        t2 = math.atan2(p2.start[1] - y0, p2.start[0] - x0)
        # Note: math.atan2 returns -pi..pi
        if arc.clockwise:
            if t1 <= t2:
                t1 += 2.0 * math.pi
        else:
            if t2 <= t1:
                t2 += 2.0 * math.pi

        if arc_ends is None:
            arc0 = self.__draw_point(frame.g_pt(p1.start[0], p1.start[1], 0.0, mesh=p1.mesh), **kwargs)
            arc1 = arc0
        else:
            arc0, arc1 = arc_ends

        Narc, angles, meshes = self.__angles((t1, t2), (p1.mesh, p2.mesh))
        pa = [arc1]
        for n in range(Narc): # create points first
            a = angles[n+1]
            m = meshes[n+1]
            x = x0 + arc.circle.radius * math.cos(a)
            y = y0 + arc.circle.radius * math.sin(a)
            pa.append(self.__draw_point(frame.g_pt(x, y, 0.0, mesh=m), **kwargs))

        arc2 = pa[Narc]

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

        arc_ends = (arc0, arc2)
        return segs, arc_ends

    def __draw_line(self, line, frame, arc_ends, **kwargs):
        p1 = line.start
        p2 = line.chain
        if arc_ends is None:
            if p2.name != "Point":
                p2 = p2.start
            gpt0 = frame.g_pt(p1.start[0], p1.start[1], 0.0, mesh=p1.mesh)
            gpt1 = frame.g_pt(p2.start[0], p2.start[1], 0.0, mesh=p2.mesh)
            path0 = self.__draw_point(gpt0, **kwargs)
            path1 = self.__draw_point(gpt1, **kwargs)
            arc_ends = (path0, path1)
            line0 = path0
            line1 = path1
        else:
            path0, path1 = arc_ends
            line0 = path1
            if p2.name != "Point":
                p2 = p2.start
                gpt1 = frame.g_pt(p2.start[0], p2.start[1], 0.0, mesh=p2.mesh)
                line1 = self.__draw_point(gpt1, **kwargs)
            else:
                line1 = path0
            arc_ends = (path0, line1)

        curve_id = self.__new_expr_id()
        gmsh.model.occ.addLine(line0, line1, curve_id)
        return curve_id, arc_ends

    def __draw_path(self, path, frame, **kwargs):
        item = path.chain
        p2_prev = None
        while item is not None:
            p1 = item
            p2 = item.chain
            if item.name != "Point":
                p1 = p1.start
                if p2.name != "Point":
                    p2 = p2.start
                p1.mesh = item.mesh
                p2.mesh = item.mesh
            if p2_prev is not None:
                p2_prev.mesh = p1.mesh
                p1.mesh = p2_prev.mesh
            p2_prev = p2
            item = item.chain

        item = path.chain
        arc_segs = []
        arc_ends = None
        while item is not None:
            if item.name == "Line":
                print('item({n}).mesh={m}, p1.mesh={o}'.format(n=item.name, m=item.mesh, o=item.start.mesh))
                s, arc_ends = self.__draw_line(item, frame, arc_ends, **kwargs)
                arc_segs.append(s)
            elif item.name == "Arc":
                print('item({n}).mesh={m}, p1.mesh={o}'.format(n=item.name, m=item.mesh, o=item.start.mesh))
                segs, arc_ends = self.__draw_arc(item, frame, arc_ends, **kwargs)
                arc_segs = arc_segs + segs
            item = item.chain

        return self.__draw_loop(arc_segs)

    def draw_path(self, path, frame=None, **kwargs):
        if frame is None:
            frame = Q3D_Frame.sketch_reset()

        loop_id = None

        if path.name == "Path":
            loop_id = self.__draw_path(path, frame, **kwargs)
        elif path.name == "Circle":
            loop_id = self.__draw_circle(path, frame, **kwargs)

        return loop_id

    def make_surface(self, name, loop_ids):
        return self.__pp_surface(name, loop_ids)

bPlotEllipseTests = False
bPlotTorusTests = False
bPlotPathTests = True
bPlotPathEllipseTests = False
bPlotPathSimpleTests = False
bBuildMesh = True

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
    test = 2
    paths = Q2D_Arc_Test(test)
    frame = Q3D_Frame.sketch_reset()
    for p in range(6):
        loops = []
        count = 0
        for path in paths:
            print("Drawing path: test-" + str(test) + str(count))
            loops.append(Geo.draw_path(path, frame))
            count += 1
            print("done.")
        Geo.make_surface("test-" + str(test), loops)
        frame.e2_rotate(math.pi/3.0)

if bBuildMesh:
    gmsh.model.mesh.generate(2)

if "-nopopup" not in sys.argv:
    gmsh.fltk.run()

gmsh.finalize()
