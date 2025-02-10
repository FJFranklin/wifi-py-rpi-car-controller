import argparse
import sys

import gmsh

from q2d_tests import Q2D_Arc_Test
from q2d_path  import *
from q3d_base  import *
from q3d_gmsh  import *

tests_descs = [
    ['p-nurbs', 'Piecewise NURBS curves (Gmsh)'],
    ['w-nurbs', 'Single whole NURBS curves (Gmsh)'],
    ['simple',  'Simple line-arc construction (Gmsh)'],
    ['mpl',     'Simple line-arc construction (Matplotlib)'],
    ['frame-p', '3D frame rotation with path selection (Gmsh)'],
    ['frame-e', '3D frame rotation with ellipse pattern (Gmsh)'],
    ['ellipse', 'Periodic NURBS ellipse test (Gmsh)'],
    ['torus-e', 'Doubly periodic NURBS torus test (Gmsh)'],
    ['nurbs3D', 'Piecewise NURBS curves (Q3D Base)'],
    ['nurbs2D', 'Piecewise NURBS curves (Q2D Base)']
]
tests = [td[0] for td in tests_descs]

parser = argparse.ArgumentParser(description="Tests for sketch-Q2D/Q3D for Gmsh/OpenCASCADE")

parser.add_argument('--path',  help='Path set to use (integer 0-7) [0].',                    default=0, type=int)
parser.add_argument('--test',  help='Test to run (use --list for info) [' + tests[0] + '].', default=tests[0], choices=tests)
parser.add_argument('--list',  help='List tests with brief explanations.',                   action='store_true')
parser.add_argument('--show',  help='Run Gmsh to show created paths/mesh, if any [True].',   action='store_true')
parser.add_argument('--mesh',  help='Use Gmsh to generate mesh, if possible [True].',        action='store_true')

args = parser.parse_args()

if args.list:
    for td in tests_descs:
        print('{t:10}'.format(t=td[0]) + td[1])
    sys.exit(0)

gmsh.initialize()

gmsh.model.add("sketch-tests")

Geo = Q3D_Draw(0.5)

if args.test == 'p-nurbs':
    print("Test: Piecewise NURBS curves (Gmsh)")
    test = args.path
    paths, bCompound = Q2D_Arc_Test(test)
    frame = Q3D_Frame.sketch_reset()
    count = 0
    p_ids = []
    for path in paths:
        if path.curve_closed():
            text = " (closed)"
        else:
            text = " (open)"
        print("Converting path: test-" + str(test) + str(count) + text)
        N2D_path = Q2D_NURBS_Path(path)
        N3D_path = Q3D_NURBS_Path(frame, N2D_path)
        path_id, phys_id = Geo.draw_nurbs_path_3d(N3D_path)
        if path.curve_closed() and path.mesh:
            if bCompound:
                p_ids.append(path_id)
            else:
                Geo.make_surface("test-" + str(test), [path_id])
        print("done.")
        count += 1
    if len(p_ids) > 0:
        print("Making physical surface with compound path")
        Geo.make_surface("test-" + str(test), p_ids)
        print("done.")

if args.test == 'w-nurbs':
    print("Test: Single whole NURBS curves (Gmsh)")
    test = args.path
    paths, bCompound = Q2D_Arc_Test(test)
    frame = Q3D_Frame.sketch_reset()
    count = 0
    p_ids = []
    for path in paths:
        if path.curve_closed():
            text = " (closed)"
        else:
            text = " (open)"
        print("Converting path: test-" + str(test) + str(count) + text)
        data = frame.nurbs_path(path)
        if data:
            ids = Geo.draw_nurbs("test-" + str(test) + str(count), data, surface=False)
            curve_id, loop_id, plane_id, phys_id = ids
            if path.curve_closed() and path.mesh:
                if bCompound:
                    p_ids.append(loop_id)
                else:
                    Geo.make_surface("test-" + str(test), [loop_id])
        print("done.")
        count += 1
    if len(p_ids) > 0:
        print("Making physical surface with compound path")
        Geo.make_surface("test-" + str(test), p_ids)
        print("done.")
              
if args.test == 'simple':
    print("Test: Simple line-arc construction (Gmsh)")
    test = args.path
    paths, bCompound = Q2D_Arc_Test(test)
    frame = Q3D_Frame.sketch_reset()
    count = 0
    p_ids = []
    for path in paths:
        if path.curve_closed():
            text = " (closed)"
        else:
            text = " (open)"
        print("Plotting path: test-" + str(test) + str(count) + text)
        loop_id = Geo.draw_path(path, frame)
        if path.curve_closed() and path.mesh:
            if bCompound:
                p_ids.append(loop_id)
            else:
                Geo.make_surface("test-" + str(test), [loop_id])
        print("done.")
        count += 1
    if len(p_ids) > 0:
        print("Making physical surface with compound path")
        Geo.make_surface("test-" + str(test), p_ids)
        print("done.")

if args.test == 'mpl':
    from q2d_plotter import Q2D_Plotter
    print("Test: Simple line-arc construction (Matplotlib)")
    test = args.path
    paths, bCompound = Q2D_Arc_Test(test)
    xmin, xmax, ymin, ymax = Q2D_BBox_Multi(paths, 0.1)
    plotter = Q2D_Plotter([xmin,xmax],[ymin,ymax])
    count = 0
    for path in paths:
        if path.curve_closed():
            text = " (closed)"
        else:
            text = " (open)"
        print("Plotting path: test-" + str(test) + str(count) + text)
        plotter.draw(path)
        print("done.")
        count += 1
    plotter.show()

if args.test == 'frame-p':
    print("Test: 3D frame rotation with path selection (Gmsh)")
    test = args.path
    paths, bCompound = Q2D_Arc_Test(test)
    frame = Q3D_Frame.sketch_reset()
    symmetry = 5
    for p in range(symmetry):
        count = 0
        p_ids = []
        for path in paths:
            if path.curve_closed():
                text = " (closed)"
            else:
                text = " (open)"
            print("Symmetry {p}/{s}: Plotting path: test-".format(p=p, s=symmetry) + str(test) + str(count) + text)
            loop_id = Geo.draw_path(path, frame)
            if path.curve_closed() and path.mesh:
                if bCompound:
                    p_ids.append(loop_id)
                else:
                    Geo.make_surface("test-" + str(test), [loop_id])
            print("done.")
            count += 1
        if len(p_ids) > 0:
            print("Making physical surface with compound path")
            Geo.make_surface("test-" + str(test), p_ids)
            print("done.")
        frame.e2_rotate(math.pi * 2.0 / symmetry)

if args.test == 'frame-e':
    print("Test: 3D frame rotation with ellipse pattern (Gmsh)")
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

if args.test == 'ellipse':
    print("Test: Periodic NURBS ellipse test (Gmsh)")

    def test_ellipse(orientation, origin, semi_major, semi_minor, **kwargs):
        frame = Q3D_Frame.sketch_reset(orientation, origin)
        data = frame.nurbs_ellipse(semi_major, semi_minor)
        return Geo.draw_nurbs("ellipse-" + orientation, data, **kwargs)

    C1 = test_ellipse('XY', (-1.0, 0.0, 0.0), 1.0, 1.0)
    C2 = test_ellipse('YZ', ( 0.0,-1.0, 0.0), 0.8, 0.3, mesh=0.1)
    C3 = test_ellipse('ZX', ( 0.0, 0.0,-1.0), 0.2, 0.9)

if args.test == 'torus-e':
    print("Test: Doubly periodic NURBS torus test (Gmsh)")

    def test_torus(orientation, origin, radius, semi_major, semi_minor, pitch=0.0, theta=None, **kwargs):
        frame = Q3D_Frame.sketch_reset(orientation, origin)
        data = frame.nurbs_torus(radius, semi_major, semi_minor, pitch=pitch, theta=theta)
        return Geo.draw_nurbs("torus-" + orientation, data, **kwargs)

    S1 = test_torus('XY', ( 1.0, 0.0, 0.0),   1, 0.2, 0.2, mesh=0.05)
    S2 = test_torus('YZ', ( 0.5, 0.0, 1.0),   1, 0.2, 0.2, 0.0, (-0.25*math.pi,1.25*math.pi))
    S3 = test_torus('ZX', ( 0.0, 0.0, 0.5), 0.6, 0.1, 0.3, 0.5, ( 0.25*math.pi,4.25*math.pi))

if args.test == 'nurbs3D':
    print("Test: Piecewise NURBS curves (Q3D Base)")
    test = args.path
    paths, bCompound = Q2D_Arc_Test(test)
    frame = Q3D_Frame.sketch_reset()
    count = 0
    for path in paths:
        if path.curve_closed():
            text = " (closed)"
        else:
            text = " (open)"
        print("1. Converting path" + text + " to single NURBS curve (test={t}, path={c}):".format(t=test, c=count))
        data = frame.nurbs_path(path)
        print("...done.")
        print("2. Converting path to NURBS path (test={t}, path={c}):".format(t=test, c=count))
        N2Dpath = Q2D_NURBS_Path(path)
        N3Dpath = Q3D_NURBS_Path(frame, N2Dpath)
        print("...done.")
        count += 1

if args.test == 'nurbs2D':
    print("Test: Piecewise NURBS curves (Q2D Path)")
    test = args.path
    paths, bCompound = Q2D_Arc_Test(test)
    for p in paths:
        p.curve_print()
        Q2D_NURBS_Path(p).curve_print()
        print(" => No. poly points = {n}".format(n=len(p.poly_points(0.01, 0.02))))

if args.mesh:
    gmsh.model.mesh.generate(2)

if args.show:
    gmsh.fltk.run()

gmsh.finalize()
