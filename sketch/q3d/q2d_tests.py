import math

from q2d_path import *

def Q2D_Arc_Test(arc_test):
    def DEG(a):
        return math.radians(a)

    paths = []
    bCompound = False

    if arc_test == 0:
        offset = -0.1
        radius = 0.5
        transition = 0.1

        ox = -2.5
        oy =  0.0
        clockwise = False

        p_tl = Q2D_Point((ox - 1.0, oy + 1.0))
        p_tr = Q2D_Point((ox + 1.0, oy + 1.0))
        p_bl = Q2D_Point((ox - 1.0, oy - 1.0))
        p_br = Q2D_Point((ox + 1.0, oy - 1.0))

        l_t = Q2D_Line(p_tr, Q2D_Vector(DEG(180))) # ref-point is ignored - except at very beginning
        l_l = Q2D_Line(p_tl, Q2D_Vector(DEG(270))) # ref-point is ignored
        l_b = Q2D_Line(p_bl, Q2D_Vector(DEG(  0))) # ref-point is ignored
        l_r = Q2D_Line(p_br, Q2D_Vector(DEG( 90))) # ref-point is ignored

        path = Q2D_Path(l_t)
        path.append(l_l,  transition=0.25)
        path.append(l_b,  )
        path.append(l_r,  transition=0.75)
        path.end_point(p_tr)

        paths.append(path)

        offset = -0.1
        radius = 0.5
        transition = 0.1

        ox =  1.5
        oy =  0.0

        p_or = Q2D_Point((ox - 0.0, oy - radius))
        p_oo = Q2D_Point((ox - 0.0, oy + 0.0))
        p_tl = Q2D_Point((ox - 1.0, oy + 1.0))
        p_tr = Q2D_Point((ox + 1.0, oy + 1.0))
        p_bl = Q2D_Point((ox - 1.0, oy - 1.0))
        p_br = Q2D_Point((ox + 1.0, oy - 1.0))

        c_oo = Q2D_Circle(p_oo, radius)
        c_tl = Q2D_Circle(p_tl, radius)
        c_tr = Q2D_Circle(p_tr, radius)
        c_bl = Q2D_Circle(p_bl, radius)
        c_br = Q2D_Circle(p_br, radius)

        a_oo = Q2D_Arc(p_or, c_oo, False)
        a_tl = Q2D_Arc(None, c_tl, False)
        a_tr = Q2D_Arc(None, c_tr, False)
        a_bl = Q2D_Arc(None, c_bl, True)
        a_br = Q2D_Arc(None, c_br, True)

        path = Q2D_Path(a_oo)
        path.append(a_tl, transition=1.0, farside=False, co_sense=False)
        path.append(a_bl, transition=2.0, farside=True, co_sense=True)
        path.append(a_br, transition=2.0, farside=False, co_sense=True)
        path.append(a_tr, transition=2.0, farside=True, co_sense=False)
        path.append(a_oo, transition=1.0, farside=False, co_sense=False)
        path.end_point(p_or)

        paths.append(path)

    elif arc_test == 1:
        offset = -0.1
        radius = 0.5
        transition = 0.1

        ox = -2.0
        oy =  2.0
        clockwise = False

        p_tl = Q2D_Point((ox - 1.0, oy + 1.0))
        p_tr = Q2D_Point((ox + 1.0, oy + 1.0))
        p_bl = Q2D_Point((ox - 1.0, oy - 1.0))
        p_br = Q2D_Point((ox + 1.0, oy - 1.0))

        c_tl = Q2D_Circle(p_tl, radius)
        c_tr = Q2D_Circle(p_tr, radius)
        c_bl = Q2D_Circle(p_bl, radius)
        c_br = Q2D_Circle(p_br, radius)

        a_tl = Q2D_Arc(p_tl, c_tl, clockwise) # start-point is ignored
        a_tr = Q2D_Arc(p_tr, c_tr, clockwise) # start-point is ignored
        a_bl = Q2D_Arc(p_bl, c_bl, clockwise) # start-point is ignored
        a_br = Q2D_Arc(p_br, c_br, clockwise) # start-point is ignored

        m_t = Q2D_Point((ox + 0.0, oy + 1.0 + offset))
        m_l = Q2D_Point((ox - 1.0 - offset, oy + 0.0))
        m_b = Q2D_Point((ox + 0.0, oy - 1.0 - offset))
        m_r = Q2D_Point((ox + 1.0 + offset, oy + 0.0))

        l_t = Q2D_Line(m_t, Q2D_Vector(DEG(180))) # ref-point is ignored - except at very beginning
        l_l = Q2D_Line(m_l, Q2D_Vector(DEG(270))) # ref-point is ignored
        l_b = Q2D_Line(m_b, Q2D_Vector(DEG(  0))) # ref-point is ignored
        l_r = Q2D_Line(m_r, Q2D_Vector(DEG( 90))) # ref-point is ignored

        path = Q2D_Path(l_t)
        path.append(a_tl, transition=transition, farside=False, co_sense=False)
        path.append(l_l,  transition=transition, farside=False, co_sense=False)
        path.append(a_bl, transition=transition, farside=False, co_sense=True)
        path.append(l_b,  transition=transition, farside=False, co_sense=True)
        path.append(a_br, transition=transition, farside=True,  co_sense=True)
        path.append(l_r,  transition=transition, farside=True,  co_sense=True)
        path.append(a_tr, transition=transition, farside=True,  co_sense=False)
        path.append(l_t,  transition=transition, farside=True,  co_sense=False)
        path.end_point(m_t)

        paths.append(path)

        ox = 2.0
        oy = 2.0
        clockwise = True

        p_tl = Q2D_Point((ox - 1.0, oy + 1.0))
        p_tr = Q2D_Point((ox + 1.0, oy + 1.0))
        p_bl = Q2D_Point((ox - 1.0, oy - 1.0))
        p_br = Q2D_Point((ox + 1.0, oy - 1.0))

        c_tl = Q2D_Circle(p_tl, radius)
        c_tr = Q2D_Circle(p_tr, radius)
        c_bl = Q2D_Circle(p_bl, radius)
        c_br = Q2D_Circle(p_br, radius)

        a_tl = Q2D_Arc(p_tl, c_tl, clockwise) # start-point is ignored
        a_tr = Q2D_Arc(p_tr, c_tr, clockwise) # start-point is ignored
        a_bl = Q2D_Arc(p_bl, c_bl, clockwise) # start-point is ignored
        a_br = Q2D_Arc(p_br, c_br, clockwise) # start-point is ignored

        m_t = Q2D_Point((ox + 0.0, oy + 1.0 + offset))
        m_l = Q2D_Point((ox - 1.0 - offset, oy + 0.0))
        m_b = Q2D_Point((ox + 0.0, oy - 1.0 - offset))
        m_r = Q2D_Point((ox + 1.0 + offset, oy + 0.0))

        l_t = Q2D_Line(m_t, Q2D_Vector(DEG(180))) # ref-point is ignored - except at very beginning
        l_l = Q2D_Line(m_l, Q2D_Vector(DEG(270))) # ref-point is ignored
        l_b = Q2D_Line(m_b, Q2D_Vector(DEG(  0))) # ref-point is ignored
        l_r = Q2D_Line(m_r, Q2D_Vector(DEG( 90))) # ref-point is ignored

        path = Q2D_Path(l_t)
        path.append(a_tl, transition=transition, farside=False, co_sense=False)
        path.append(l_l,  transition=transition, farside=False, co_sense=False)
        path.append(a_bl, transition=transition, farside=False, co_sense=True)
        path.append(l_b,  transition=transition, farside=False, co_sense=True)
        path.append(a_br, transition=transition, farside=True,  co_sense=True)
        path.append(l_r,  transition=transition, farside=True,  co_sense=True)
        path.append(a_tr, transition=transition, farside=True,  co_sense=False)
        path.append(l_t,  transition=transition, farside=True,  co_sense=False)
        path.end_point(m_t)

        paths.append(path)

        offset = 0.4
        radius = 0.3
        transition = 0.5

        ox = -2.0
        oy = -2.0

        p_tl = Q2D_Point((ox - 1.0, oy + 1.0))
        p_tr = Q2D_Point((ox + 1.0, oy + 1.0))
        p_bl = Q2D_Point((ox - 1.0, oy - 1.0))
        p_br = Q2D_Point((ox + 1.0, oy - 1.0))

        c_tl = Q2D_Circle(p_tl, radius)
        c_tr = Q2D_Circle(p_tr, radius)
        c_bl = Q2D_Circle(p_bl, radius)
        c_br = Q2D_Circle(p_br, radius)

        a_tl = Q2D_Arc(p_tl, c_tl, True)  # start-point is ignored
        a_tr = Q2D_Arc(p_tr, c_tr, True)  # start-point is ignored
        a_bl = Q2D_Arc(p_bl, c_bl, False) # start-point is ignored
        a_br = Q2D_Arc(p_br, c_br, False) # start-point is ignored

        m_t = Q2D_Point((ox + 0.0, oy + 1.0 + offset))
        m_l = Q2D_Point((ox - 1.0 - offset, oy + 0.0))
        m_b = Q2D_Point((ox + 0.0, oy - 1.0 - offset))
        m_r = Q2D_Point((ox + 1.0 + offset, oy + 0.0))

        l_t = Q2D_Line(m_t, Q2D_Vector(DEG(180))) # ref-point is ignored - except at very beginning
        l_l = Q2D_Line(m_l, Q2D_Vector(DEG(270))) # ref-point is ignored
        l_b = Q2D_Line(m_b, Q2D_Vector(DEG(  0))) # ref-point is ignored
        l_r = Q2D_Line(m_r, Q2D_Vector(DEG( 90))) # ref-point is ignored

        path = Q2D_Path(l_t)
        path.append(a_tl, transition=transition, farside=False, co_sense=False)
        path.append(l_l,  transition=transition, farside=False, co_sense=False)
        path.append(a_bl, transition=transition, farside=False, co_sense=True)
        path.append(l_b,  transition=transition, farside=False, co_sense=True)
        path.append(a_br, transition=transition, farside=True,  co_sense=True)
        path.append(l_r,  transition=transition, farside=True,  co_sense=True)
        path.append(a_tr, transition=transition, farside=True,  co_sense=False)
        path.append(l_t,  transition=transition, farside=True,  co_sense=False)
        path.end_point(m_t)

        paths.append(path)

        offset = 0.5
        radius = 0.5
        transition = 0.1

        ox =  2.0
        oy = -2.0

        p_tl = Q2D_Point((ox - 1.0, oy + 1.0))
        p_tr = Q2D_Point((ox + 0.3, oy + 0.8))
        p_bl = Q2D_Point((ox - 1.0, oy - 0.5))
        p_br = Q2D_Point((ox + 1.3, oy - 1.3))

        c_tl = Q2D_Circle(p_tl, radius)
        c_tr = Q2D_Circle(p_tr, 0.7)
        c_bl = Q2D_Circle(p_bl, radius)
        c_br = Q2D_Circle(p_br, 0.3)

        a_tl = Q2D_Arc(p_tl, c_tl, True)  # start-point is ignored
        a_tr = Q2D_Arc(p_tr, c_tr, True)  # start-point is ignored
        a_bl = Q2D_Arc(p_bl, c_bl, False) # start-point is ignored
        a_br = Q2D_Arc(p_br, c_br, True)  # start-point is ignored

        m_t = Q2D_Point((ox + 0.0, oy + 1.0 + offset))
        m_l = Q2D_Point((ox - 1.0 - offset, oy + 0.0))
        m_b = Q2D_Point((ox + 0.0, oy - 0.5 - offset))
        m_r = Q2D_Point((ox + 0.5 + offset, oy + 0.0))

        l_t = Q2D_Line(m_t, Q2D_Vector(DEG(180))) # ref-point is ignored - except at very beginning
        l_l = Q2D_Line(m_l, Q2D_Vector(DEG(270))) # ref-point is ignored
        l_b = Q2D_Line(m_b, Q2D_Vector(DEG(  0))) # ref-point is ignored
        l_r = Q2D_Line(m_r, Q2D_Vector(DEG( 90))) # ref-point is ignored

        path = Q2D_Path(l_t)
        path.append(a_tl, transition=transition, farside=False, co_sense=False)
        path.append(l_l,  transition=transition, farside=False, co_sense=False)
        path.append(a_bl, transition=transition, farside=False, co_sense=True)
        path.append(l_b,  transition=transition, farside=False, co_sense=True)
        path.append(a_br, transition=transition, farside=True,  co_sense=True)
        path.append(l_r,  transition=transition, farside=True,  co_sense=True)
        path.append(a_tr, transition=0.08,       farside=True,  co_sense=False)
        path.append(l_t,  transition=0.08,       farside=True,  co_sense=False)
        path.end_point(m_t)

        paths.append(path)

    elif arc_test == 2: # let's draw a hook
        bCompound = True

        # Fixed Parameters
        r_seat = 0.015 # loading pin has 30mm diameter
        r_hole = 0.008 # supporting pin has 16mm diameter
        y_csep = 0.160 # centre-centre separation is 160mm

        # Adjustable Parameters
        neck_t = 0.010 # thickness of neck
        neck_a = -80.0 # angle of neck (deg)

        r_top  = 0.016 # outer radius at top
        r_main = 0.070 # main body radius

        x_main = 0.03  # coordinates of main body centre
        y_main = 0.02

        r1 = 0.06 # transition radii
        r2 = 0.01
        rb = 0.01

        p_start = Q2D_Point((0.0, -r_seat)) # start/end point of path

        p_seat  = Q2D_Point((0.0, 0.0))     # construction circle-centers
        p_hole  = Q2D_Point((0.0, y_csep))
        p_main  = Q2D_Point((x_main, y_main))

        c_seat = Q2D_Circle(p_seat, r_seat)                 # circle outlining the seat of the hook
        a_seat = Q2D_Arc(p_start, c_seat, clockwise=False)  # define arc anti-clockwise from bottom
        c_top  = Q2D_Circle(p_hole, r_top)                  # circle outlining the top of the hook
        a_top  = Q2D_Arc(None, c_top, clockwise=True)       # define arc clockwise; start irrelevant
        c_main = Q2D_Circle(p_main, r_main)                 # circle outlining the top of the hook
        a_main = Q2D_Arc(None, c_main, clockwise=True)      # define arc clockwise; start irrelevant

        l_neck = Q2D_Line(p_hole, Q2D_Vector(DEG(neck_a)))  # neck center-line

        path = Q2D_Path()

        _, c = path.append(a_seat)
        c.name = "seat-inner"

        t, c = path.append(l_neck.parallel(-neck_t / 2, True), transition=r1, farside=False, co_sense=True)
        t.name = "seat-neck-tr"
        c.name = "neck-left"

        t, c = path.append(a_top, transition=r2, farside=False, co_sense=False)
        t.name = "neck-head-tr-left"
        c.name = "head-outer"

        t, c = path.append(l_neck.parallel( neck_t / 2, False), transition=r2, farside=False, co_sense=False)
        t.name = "neck-head-tr-right"
        c.name = "neck-right"

        t, c = path.append(a_main, transition=r2, farside=False, co_sense=False)
        t.name = "neck-main-tr"
        c.name = "main"

        t, c = path.append(a_seat, transition=rb, farside=False, co_sense=True)
        t.name = "tip"
        c.name = "seat-outer"

        path.end_point(p_start)
        path.name = "hook-outline"

        path.mesh = 0.01
        path["seat-inner"  ].mesh = 0.001
        path["seat-outer"  ].mesh = 0.001
        path["seat-neck-tr"].mesh = 0.002
        path["neck-left"   ].mesh = 0.003
        path["neck-right"  ].mesh = 0.003
        path["head-outer"  ].mesh = 0.002

        # circle outlining the top hole of the hook
        hole = Q2D_Path.circle(Q2D_Circle(p_hole, r_hole))
        hole.name = "hook-hole"
        hole.mesh = 0.001

        paths.append(path)
        paths.append(hole)

    elif arc_test == 3:
        oy = 0.0136

        p_0l = Q2D_Point((0.000, oy - 0.018))
        p_tr = Q2D_Point((0.030, oy + 0.000))
        p_cc = Q2D_Point((0.015, oy - 0.015))

        pc_l = Q2D_Point((0.005, oy + 0.000))
        pc_r = Q2D_Point((0.025, oy + 0.000))

        cl_o = Q2D_Circle(pc_l, 0.020)
        cl_i = Q2D_Circle(pc_l, 0.018)
        cr_o = Q2D_Circle(pc_r, 0.017)
        cr_i = Q2D_Circle(pc_r, 0.015)

        l_l = Q2D_Line(p_0l, Q2D_Vector(DEG(270.0)))
        l_r = Q2D_Line(p_tr, Q2D_Vector(DEG( 90.0)))
        l_c = Q2D_Line(p_cc, Q2D_Vector(DEG( 30.0)))

        al_o = Q2D_Arc(None, cl_o, False)
        al_i = Q2D_Arc(None, cl_i, True)
        ar_o = Q2D_Arc(None, cr_o, False)
        ar_i = Q2D_Arc(None, cr_i, True)

        path = Q2D_Path(l_l)
        path.append(al_o, farside=True)
        path.append(l_c.parallel(-0.001), transition=0.007, co_sense=True, farside=True)
        path.append(ar_o, transition=0.005, co_sense=False, farside=False)
        path.append(l_r, farside=True)
        path.append(ar_i)
        path.append(l_c.parallel(0.001, True), transition=0.007, co_sense=False, farside=False)
        path.append(al_i, transition=0.005, co_sense=True, farside=True)
        path.append(l_l)
        path.end_point(p_0l)

        paths.append(path)

    elif arc_test == 4:
        # Original NACA 2412 coordinates
        NACA_2412 = [
            [1,		0.0013],
            [0.95,	0.0114],
            [0.9,	0.0208],
            [0.8,	0.0375],
            [0.7,	0.0518],
            [0.6,	0.0636],
            [0.5,	0.0724],
            [0.4,	0.078],
            [0.3,	0.0788],
            [0.25,	0.0767],
            [0.2,	0.0726],
            [0.15,	0.0661],
            [0.1,	0.0563],
            [0.075,	0.0496],
            [0.05,	0.0413],
            [0.025,	0.0299],
            [0.0125,	0.0215],
            [0,		0],
            [0.0125,	-0.0165],
            [0.025,	-0.0227],
            [0.05,	-0.0301],
            [0.075,	-0.0346],
            [0.1,	-0.0375],
            [0.15,	-0.041],
            [0.2,	-0.0423],
            [0.25,	-0.0422],
            [0.3,	-0.0412],
            [0.4,	-0.038],
            [0.5,	-0.0334],
            [0.6,	-0.0276],
            [0.7,	-0.0214],
            [0.8,	-0.015],
            #[0.9,	-0.0082], - remove colinear mid-node
            [0.95,	-0.0048],
            [1,		-0.0013]]

        points = []
        for n in NACA_2412:
            points.append((n[0], n[1]))
        path = Q2D_Path.polygon(points)

        paths.append(path)

    elif arc_test == 6:
        XY = Q2D_Frame(DEG( 30.0))

        o = XY.g_pt(0.0, 0.0)
        e = XY.g_pt(1.5, 0.0)

        l1 = Q2D_Line(o, XY.g_vec(DEG(180.0)))
        l2 = Q2D_Line(o, XY.g_vec(DEG(270.0)))

        c = Q2D_Circle(o, 1.5)
        a = Q2D_Arc(None, c, clockwise=True)

        path = Q2D_Path(l2)
        path.append(a)
        path.end_point(e)

        paths.append(path)

    elif arc_test == 7:
        XY = Q2D_Frame(DEG(45.0))
        XY.global_tuple_set_origin((-2.5, 0.0))

        p_tl = XY.g_pt(-1.0,  1.0)
        p_tr = XY.g_pt( 1.0,  1.0)
        p_bl = XY.g_pt(-1.0, -1.0)
        p_br = XY.g_pt( 1.0, -1.0)

        p_tr.mesh = 0.01

        l_t = Q2D_Line(p_tr, XY.g_vec(DEG(180))) # ref-point is ignored - except at very beginning
        l_l = Q2D_Line(p_tl, XY.g_vec(DEG(270))) # ref-point is ignored
        l_b = Q2D_Line(p_bl, XY.g_vec(DEG(  0))) # ref-point is ignored
        l_r = Q2D_Line(p_br, XY.g_vec(DEG( 90))) # ref-point is ignored

        path = Q2D_Path(l_t)
        path.append(l_l,  transition=0.25)
        path.append(l_b,  )
        path.append(l_r,  transition=0.75)
        path.end_point(p_tr)

        paths.append(path)

    else:
        raise RuntimeError("No definition for test path " + str(arc_test))

    return paths, bCompound
