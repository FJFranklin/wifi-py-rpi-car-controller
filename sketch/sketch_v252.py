# target API Version 252
# (*)  V22 creates datum / sketching planes

#  0:  arc-arc test
#  1:  arc-line test
#  2:  hook
#  3:  SpaceClaim: 3D-NURBS
#  4:  conduit (GeometrySequence=0 for circular section)
#  5:  SpaceClaim: ski (*)
#  6:  SpaceClaim: cube (*)
#  7:  SpaceClaim: foil [Parameters needed]
#  8: !SpaceClaim: hook - offset
#  9: !SpaceClaim: hook - mesh w/ dmsh
# 10:  SpaceClaim: foil (G. Snee)
# 11:  SpaceClaim: bonded flexible pipe
# 12:  SpaceClaim: bonded flexible pipe - convert wires to beams
# 13:  SpaceClaim: loading pins
# 14:  SpaceClaim: gyro section (2D)
# 15:  SpaceClaim: gyro segment (3D)
# 16:  SpaceClaim: Carcass (Tang)
arc_test = 16

print_path_info = False
print_plot_info = False
plot_construction_arcs = False
script_report = ""

# ==== Preliminary setup: Are we using SpaceClaim? ==== #

import math

Q2D_Design_Tolerance = 1E-15 # tolerance for numerical errors

if 'DEG' in dir():
    Q2D_SpaceClaim = True

    # SpaceClaim uses IronPython, which integrates with Microsoft's .Net framework
    from System import Array, Double
    from SpaceClaim.Api.V252.Geometry import ControlPoint, Knot, NurbsData, NurbsSurface, Line

    # A parameter used solely for convenience; changing GeometrySequence re-runs the script.
    GeometrySequence = Parameters.GeometrySequence

else:
    Q2D_SpaceClaim = False
    # Okay, we're not using SpaceClaim; let's plot the paths with MatPlotLib instead

    def DEG(a):
        return math.radians(a)

    GeometrySequence = 1

    Q2D_path_color = 'blue' # color for plotting path if using MatPlotLib

# ==== General SpaceClaim convenience functions ==== #

def remove_all_bodies():
    while GetRootPart().Bodies.Count > 0:
        b = GetRootPart().Bodies[0]
        if b.IsLocked:
            s = Selection.Create(b)
            ViewHelper.LockBodies(s, False)
        b.Delete()

def remove_all_curves():
    while GetRootPart().Curves.Count > 0:
        GetRootPart().Curves[0].Delete()

def remove_all_datum_planes():
    while GetRootPart().DatumPlanes.Count > 0:
        GetRootPart().DatumPlanes[0].Delete()

def remove_all_components():
    while GetRootPart().Components.Count > 0:
        b = GetRootPart().Components[0]
        s = BodySelection.Create(b.Content.Bodies[0])
        ViewHelper.LockBodies(s, False)
        b.Delete()

def find_component_by_body_name(name):
    matched = None
    for c in GetRootPart().Components:
        for b in c.Content.Bodies:
            if b.GetName() == name:
                matched = c
                break
        if matched is not None:
            break
    return matched

def create_beam_profile_circular(diameter, name):
    area = math.pi * diameter**2 / 4.0
    J = math.pi * diameter**4 / 32.0
    BeamProfile.CreateCustom(area,0.0,0.0,J/2.0,0.0,J/2,0.0,0.0,J,0.0,name)
    c = find_component_by_body_name('Solid')
    c.Content.Bodies[0].SetName(name + '_body')
    return c

class QSC_Select(object):

    @staticmethod
    def create(name, selection): # create named selection
        if len(selection.Items) == 0:
            print('Cannot name empty selection: ' + name)
            return None
        RenameObject.Execute(selection, name)
        return QSC_Select(name)

    def __init__(self, name):
        self.name = name
        self.selection = None

    def select(self): # get named selection
        success = True
        self.selection = Selection.CreateByNames(self.name)
        if len(self.selection.Items) == 0:
            self.selection = None
            success = False
            print('Named selection failed: ' + self.name)
        return success

    def create_named_selection(self, name):
        if self.select():
            self.selection.CreateAGroup(name)

    def delete(self):
        if self.select():
            Delete.Execute(self.selection)

    def rename(self, name):
        if self.select():
            RenameObject.Execute(self.selection, name)
        self.name = name

    def lock(self):
        if self.select():
            ViewHelper.LockBodies(self.selection, True)

    def unlock(self):
        if self.select():
            ViewHelper.LockBodies(self.selection, False)

    def show(self):
        if self.select():
            ViewHelper.SetObjectVisibility(self.selection, VisibilityType.Show)

    def hide(self):
        if self.select():
            ViewHelper.SetObjectVisibility(self.selection, VisibilityType.Hide)

class QSC_Surface(QSC_Select):
    def __init__(self, name):
        QSC_Select.__init__(self, name)

    def surface_face(self):
        if self.select():
            return self.selection.Items[0].Faces[0]
        return None

    def principal_face(self):
        if self.select():
            return Selection.Create(self.selection.Items[0].Faces[0])
        return None

    def paint(self, rgba):
        if self.select():
            ColorHelper.SetColor(self.selection, Color.FromArgb(*rgba))

class QSC_CurveRef(object):
    @staticmethod
    def face_is_shim(face):
        is_shim = False
        for e in face.Edges:
            edge = QSC_CurveRef(e)
            if not edge.closed:
                if edge.length() < 1E-5:
                    is_shim = True
                    break
        return is_shim

    def __init__(self, curve, axis=None):
        self.curve = curve

        self.sp = curve.Shape.StartPoint
        self.ep = curve.Shape.EndPoint

        self.closed = False
        if curve.Shape.StartPoint.Equals(curve.Shape.EndPoint):
            self.closed = True

        self.axial = False
        if axis is not None:
            if axis.IsCoincident(curve.Shape.Geometry):
                self.axial = True

        self.side = None

    def swap(self):
        tmp = self.sp
        self.sp = self.ep
        self.ep = tmp

    def length(self):
        dx = self.ep.X - self.sp.X
        dy = self.ep.Y - self.sp.Y
        dz = self.ep.Z - self.sp.Z
        return (dx**2 + dy**2 + dz**2)**0.5

    def match_start(self, point, tol=None):
        if tol is not None:
            dx = point.X - self.sp.X
            dy = point.Y - self.sp.Y
            dz = point.Z - self.sp.Z
            dr = (dx**2 + dy**2 + dz**2)**0.5
            if dr < tol:
                return True
        return self.sp.Equals(point)

    def match_end(self, point):
        return self.ep.Equals(point)

    def match_both(self, p1, p2):
        if self.sp.Equals(p1) and self.ep.Equals(p2):
            return True
        return self.sp.Equals(p2) and self.ep.Equals(p1)

    def match_curve_to_start(self, curve):
       return curve.Shape.ContainsPoint(self.sp)

    def match_curve_to_end(self, curve):
       return curve.Shape.ContainsPoint(self.ep)

    def contains_point(self, point):
        return self.curve.Shape.ContainsPoint(point)

    def match_curves(self, c1, c2):
        if c1.Shape.ContainsPoint(self.sp) and c2.Shape.ContainsPoint(self.ep):
            return True
        return c1.Shape.ContainsPoint(self.ep) and c2.Shape.ContainsPoint(self.sp)

    def paint(self, r, g, b):
        if self.side is not None:
            sel = Selection.Create(self.side)
            ColorHelper.SetColor(sel, Color.FromArgb(r, g, b))

class QSC_Body(QSC_Select):

    __counter = 0

    @staticmethod
    def __name():
        name = 'body_' + str(QSC_Body.__counter)
        QSC_Body.__counter += 1
        return name

    def __init__(self, name=None):
        if name is None:
            name = QSC_Body.__name()

        QSC_Select.__init__(self, name)
        self.front = None
        self.back = None
        self.sides = []
        self.axis = None

    def paint(self, c_front, c_back, c_sides_from, c_sides_to=None):
        if self.front is not None and c_front is not None:
            side = Selection.Create(self.front)
            ColorHelper.SetColor(side, Color.FromArgb(*c_front))

        if self.back is not None and c_front is not None:
            side = Selection.Create(self.back)
            ColorHelper.SetColor(side, Color.FromArgb(*c_back))

        if len(self.sides) > 0 and c_sides_from is not None:
            if len(self.sides) == 1:
                side = Selection.Create(self.sides[0])
                ColorHelper.SetColor(side, Color.FromArgb(*c_sides_from))
            elif c_sides_to is None:
                for s in self.sides:
                    side = Selection.Create(self.sides[s])
                    ColorHelper.SetColor(side, Color.FromArgb(*c_sides_from))
            else:
                count = len(self.sides)
                if self.sides[0] == self.sides[count-1]: # first and last are the same
                    count -= 1

                for s in range(0, count):
                    a = int(c_sides_from[0] * (count - 1 - s) / (count - 1)) + int(c_sides_to[0] * s / (count - 1))
                    r = int(c_sides_from[1] * (count - 1 - s) / (count - 1)) + int(c_sides_to[1] * s / (count - 1))
                    g = int(c_sides_from[2] * (count - 1 - s) / (count - 1)) + int(c_sides_to[2] * s / (count - 1))
                    b = int(c_sides_from[3] * (count - 1 - s) / (count - 1)) + int(c_sides_to[3] * s / (count - 1))
                    side = Selection.Create(self.sides[s])
                    ColorHelper.SetColor(side, Color.FromArgb(a, r, g, b))

    def _match_face_to_curves(self, f, curves, axis, ring_check=False):
        match_all = True
        match_none = True
        match_axis = False

        if ring_check:
            ring_count = 0
            for e in f.Edges:
                if e.Shape.StartPoint.Equals(e.Shape.EndPoint):
                    ring_count += 1
            if ring_count > 0:
                match_none = False
            if ring_count < len(f.Edges):
                match_all = False
        else:
            for e in f.Edges:
                #print(".    edge")
                if axis is not None:
                    if axis.IsCoincident(e.Shape.Geometry):
                        match_axis = True
                        self.axis = e
                        print(".        axis matched")
                match = False
                for c in curves:
                    curve = c[0].Shape.Geometry
                    start = c[0].Shape.StartPoint
                    if e.Shape.Geometry.IsCoincident(curve):
                        if e.Shape.ContainsPoint(start):
                            print(".        curve matched (definite)")
                            match = True
                            break
                        else:
                            print(".        possible match?")
                if match:
                    match_none = False
                else:
                    match_all = False

        return match_all, match_none, match_axis

    def match_curves(self, curves, axis=None):
        self.front = None
        self.back = None
        self.sides = []

        if len(curves) < 1:
            print("match_curves: unexpected: no curves")
            return

        if not self.select():
            return
        b = self.selection.Items[0]
        if len(b.Faces) == 0:
            print("match_curves: unexpected: no faces")
            return

        # In general, we expect to have a front, a back (where we started from) and a side for each curve.
        # The curve should be a closed loop; let's start by identifying start and end points, and doing checks
        curve_refs_unconnected = []
        count_axis = 0
        for c in curves:
            if len(c) > 1:
                print("match_curves: unexpected: complex wire group")
            curve_ref = QSC_CurveRef(c[0], axis)
            curve_refs_unconnected.append(curve_ref)
            if curve_ref.closed and len(curves) > 1:
                print("match_curves: unexpected: closed curve in multi-curve list")
            if curve_ref.axial:
                count_axis += 1
        if count_axis > 0:
            print("match_curves: note: {n}/{t} curves on axis of rotation".format(n=count_axis, t=len(curves)))

        if len(b.Faces) == 1:
            if count_axis > 0:
                print("match_curves: note: sphere? one side, no front or back.")
            else:
                print("match_curves: note: donut? one side, no front or back.")
            self.sides.append(b.Faces[0])
            side = Selection.Create(b.Faces[0])
            ColorHelper.SetColor(side, Color.FromArgb(0, 255, 0))
            return

        curve_refs = [curve_refs_unconnected.pop(0)]
        attempts_remaining = len(curve_refs_unconnected)
        while len(curve_refs_unconnected) > 0 and attempts_remaining > 0:
            curve_ref = curve_refs_unconnected.pop(0)
            if curve_refs[-1].match_end(curve_ref.sp):
                curve_refs.append(curve_ref)
                attempts_remaining = len(curve_refs_unconnected)
                continue
            if curve_refs[0].match_start(curve_ref.ep):
                curve_refs.insert(0, curve_ref)
                attempts_remaining = len(curve_refs_unconnected)
                continue
            curve_ref.swap()
            if curve_refs[-1].match_end(curve_ref.sp):
                curve_refs.append(curve_ref)
                attempts_remaining = len(curve_refs_unconnected)
                continue
            if curve_refs[0].match_start(curve_ref.ep):
                curve_refs.insert(0, curve_ref)
                attempts_remaining = len(curve_refs_unconnected)
                continue
            curve_refs_unconnected.append(curve_ref)
            attempts_remaining -= 1
        if len(curve_refs_unconnected) > 0:
            print("match_curves: warning: unable to connect curves")
            while len(curve_refs_unconnected) > 0:
                curve_refs.append(curve_refs_unconnected.pop(0))
        if not curve_refs[0].match_start(curve_refs[-1].ep):
            print("match_curves: warning: curves out of sequence or loop is open")

        # check to see if this is a solid of revolution; if so, the edges should all be circles
        solid_of_revolution = False
        if axis is not None:
            solid_rev = 0
            for f in b.Faces:
                if len(f.Edges) != 2:
                    continue
                face_is_rev = True
                for e in f.Edges:
                    curve_ref = QSC_CurveRef(e, axis)
                    if not curve_ref.closed:
                        face_is_rev = False
                        break
                if face_is_rev:
                    solid_rev += 1
            if solid_rev > 0:
                if solid_rev == len(b.Faces):
                    solid_of_revolution = True
                else:
                    print("match_curves: note: {r}/{n} faces are revolutions".format(r=solid_rev, n=len(b.Faces)))

        if solid_of_revolution:
            if len(b.Faces) != len(curves) - count_axis:
                print("match_curves: note: solid of revolution, but #faces ({n}) != #curves ({c}) - {a}".format(n=len(b.Faces), c=len(curves), a=count_axis))
        else:
            if len(b.Faces) != 2 + len(curves) - count_axis:
                print("match_curves: note: #faces ({n}) != 2 + #curves ({c}) - {a}".format(n=len(b.Faces), c=len(curves), a=count_axis))

        if solid_of_revolution:
            unmatched_faces = []
            for f in b.Faces:
                e1 = f.Edges[0]
                e2 = f.Edges[1]
                matched = False
                for curve_ref in curve_refs:
                    if curve_ref.match_curves(e1, e2):
                        if curve_ref.side is not None:
                            print("match_curves: unexpected: multiple faces matched to curve ref")
                        curve_ref.side = f
                        curve_ref.paint(0, 255, 0)
                        matched = True
                        break
                if not matched:
                    unmatched_faces.append(f)
                    print("match_curves: unexpected: face not matched to curve")
            for f in unmatched_faces:
                e1 = f.Edges[0]
                e2 = f.Edges[1]
                matched = False
                index = -1
                swap = False
                for i, curve_ref in enumerate(curve_refs):
                    if curve_ref.side is None:
                        continue
                    # this curve is claimed, so may mark a boundary
                    if curve_ref.match_curve_to_end(e1):
                        index = i
                        break
                    if curve_ref.match_curve_to_end(e2):
                        index = i
                        swap = True
                        break
                if index == -1:
                    print("match_curves: unexpected: disconnected face")
                    continue
                start = index + 1
                if start == len(curve_refs):
                    start = 0
                if curve_refs[start].side is not None:
                    print("match_curves: unexpected: multiply connected face")
                    continue
                curve_refs[start].side = f
                curve_refs[start].paint(255, 0, 0)
                end = start
                while True:
                    end += 1
                    if end == len(curve_refs):
                        end = 0
                    if curve_refs[end].side is not None:
                        print("match_curves: unexpected: corrupted face sequence")
                        break
                    curve_refs[end].side = f
                    curve_refs[end].paint(0, 0, 255)
                    if swap:
                        if curve_refs[end].match_curve_to_end(e1):
                            print("match_curves: note: face matched to curve sequence")
                            break
                    else:
                        if curve_refs[end].match_curve_to_end(e2):
                            print("match_curves: note: face matched to curve sequence")
                            break
            for curve_ref in curve_refs:
                if curve_ref.side is None:
                    print("match_curves: warning: skipping curve unmatched to face")
                else:
                    self.sides.append(curve_ref.side)
            return

        def search_curve_refs(refs, curve_ref, start_only=False, tol=None):
            matched = False
            for ref in refs:
                if start_only:
                    if ref.match_start(curve_ref.sp, tol):
                        matched = True
                        break
                else:
                    if ref.match_both(curve_ref.sp, curve_ref.ep):
                        matched = True
                        break
            return matched

        def search_curve_refs_for_point(refs, point):
            matched = False
            for ref in refs:
                if ref.contains_point(point):
                    matched = True
                    break
            return matched

        list_f = []
        list_b = []
        list_s = []
        for f in b.Faces:
            count = 0
            back = True
            for e in f.Edges:
                edge = QSC_CurveRef(e)
                #print("sp=({xs}, {ys}, {zs})  ep=({xe}, {ye}, {ze})".format(xs=edge.sp.X, ys=edge.sp.Y, zs=edge.sp.Z, xe=edge.ep.X, ye=edge.ep.Y, ze=edge.ep.Z))
                if search_curve_refs(curve_refs, edge, True):
                    count += 1
                else:
                    back = False
                edge.swap()
                if search_curve_refs(curve_refs, edge, True):
                    count += 1
                else:
                    back = False
            if count == 0:
                list_f.append(f)
            elif back:
                list_b.append(f)
            else:
                list_s.append(f)
        print("#front={f}, #back={b}, #sides={s}".format(f=len(list_f), b=len(list_b), s=len(list_s)))
        if len(list_f) != 1 or len(list_b) != 1:
            tol = 1E-5
            list_f = []
            list_b = []
            list_s = []
            for f in b.Faces:
                count = 0
                back = True
                min_length = None
                for e in f.Edges:
                    edge = QSC_CurveRef(e)
                    length = edge.length()
                    if min_length is None:
                        min_length = length
                    elif length < min_length:
                        min_length = length
                    #print("sp=({xs}, {ys}, {zs})  ep=({xe}, {ye}, {ze})".format(xs=edge.sp.X, ys=edge.sp.Y, zs=edge.sp.Z, xe=edge.ep.X, ye=edge.ep.Y, ze=edge.ep.Z))
                    if search_curve_refs(curve_refs, edge, True, tol):
                        count += 1
                    else:
                        back = False
                    edge.swap()
                    if search_curve_refs(curve_refs, edge, True, tol):
                        count += 1
                    else:
                        back = False
                if count == 0:
                    list_f.append(f)
                elif back:
                    if min_length < tol:
                        print("match_curves: note: dropping shim facet")
                    else:
                        list_b.append(f)
                else:
                    list_s.append(f)
            #print("#front={f}, #back={b}, #sides={s}".format(f=len(list_f), b=len(list_b), s=len(list_s)))
        if len(list_f) == 1:
            self.front = list_f[0]
            side = Selection.Create(self.front)
            ColorHelper.SetColor(side, Color.FromArgb(255, 255, 255))
        if len(list_b) == 1:
            self.back = list_b[0]
            side = Selection.Create(self.front)
            ColorHelper.SetColor(side, Color.FromArgb(0, 0, 0))
        elif len(list_b) > 1:
            print("match_curves: warning: multiple back faces; using first by default")
            self.back = list_b[0]
            for i, f in enumerate(list_b):
                side = Selection.Create(f)
                ColorHelper.SetColor(side, Color.FromArgb(0, int((255.0*i)/(len(list_b)-1)), 255-int((255.0*i)/(len(list_b)-1))))
        for f in list_s:
            self.sides.append(f)
            side = Selection.Create(f)
            ColorHelper.SetColor(side, Color.FromArgb(255, 0, 0))

    @staticmethod
    def faces_connected(face1, face2):
        connected = False
        for e1 in face1.Edges:
            for e2 in face2.Edges:
                if e1.Equals(e2): # in V16 was e1.MidPoint().Point.Equals(e2.MidPoint().Point):
                    connected = True
        return connected

    @staticmethod
    def faces_coincident(face1, face2):
        return face1.Shape.Geometry.IsCoincident(face2.Shape.Geometry)

    def sort_faces(self, ref_front, ref_back=None):
        if self.select():
            self._sort_faces(ref_front, ref_back)

    def _sort_faces(self, ref_front, ref_back, split_face=None):
        self.front = None
        self.back = None
        self.sides = []

        for f in self.selection.Items[0].Faces:
            if QSC_Body.faces_coincident(f, ref_front):
                #print('front matched')
                self.front = f
                continue
            if ref_back is not None:
                if QSC_Body.faces_coincident(f, ref_back):
                    #print('back matched')
                    self.back = f
                    continue
            if not QSC_CurveRef.face_is_shim(f):
                #print('side assigned')
                self.sides.append(f)

        if self.front is not None:
            original_front = True
        else:
            original_front = False

        if self.front is not None and self.back is None and split_face is not None:
            for s in self.sides:
                if QSC_Body.faces_coincident(s, split_face):
                    self.back = s
                    self.sides.remove(s)
                    break
        if self.front is not None and self.back is None:
            #print('searching for the back')
            for s in self.sides:
                if QSC_Body.faces_connected(s, self.front):
                    #print('an actual side')
                    continue
                #print('the back?')
                self.back = s
                self.sides.remove(s)
                break

        if self.front is None and self.back is not None and split_face is not None:
            for s in self.sides:
                if QSC_Body.faces_coincident(s, split_face):
                    self.front = s
                    self.sides.remove(s)
                    break
        if self.front is None and self.back is not None:
            #print('searching for the front')
            for s in self.sides:
                if QSC_Body.faces_connected(s, self.back):
                    #print('an actual side')
                    continue
                #print('the front?')
                self.front = s
                self.sides.remove(s)
                break

        return original_front

    def _reorganise_sides(self, ref_body):
        org_sides = []
        for r in ref_body.sides:
            for s in self.sides:
                if QSC_Body.faces_connected(s, r):
                    #print('matched with ref-body, count={d}'.format(d=count))
                    org_sides.append(s)
                    break
        self.sides = org_sides

    @staticmethod
    def cross_sect_and_match(old_body, surface, split_name, ref_body=None):
        back_body = None
        front_body = None

        if not old_body.select():
            print("cross_sect_and_match: unable to select and split = '" + old_body.name + "'")
            return old_body, None

        #print("cross_sect_and_match: note: split body = '" + old_body.name + "'")
        SplitBody.ByCutter(old_body.selection, surface.principal_face(), False)

        old_front = old_body.front
        old_back  = old_body.back
        old_name  = old_body.name

        split_face = surface.surface_face()
        front_is_front = old_body._sort_faces(old_front, old_back, split_face)
        if front_is_front:
            old_body.rename(split_name)
            front_body = old_body
        else:
            back_body = old_body

        if ref_body is not None and old_body.front is not None and old_body.back is not None:
            if QSC_Body.faces_coincident(old_body.front, ref_body.back) or QSC_Body.faces_coincident(old_body.back, ref_body.front):
                #print('Matching original to reference:')
                old_body._reorganise_sides(ref_body)

        new_body = QSC_Body(old_name + '1')
        if new_body.select():
            new_body._sort_faces(old_front, old_back, split_face)

            if front_is_front:
                back_body = new_body
                new_body.rename(old_name)
            else:
                front_body = new_body
                new_body.rename(split_name)

            if ref_body is not None and new_body.front is not None and new_body.back is not None:
                if QSC_Body.faces_coincident(new_body.front, ref_body.back) or QSC_Body.faces_coincident(new_body.back, ref_body.front):
                    #print('Matching off-cut to reference:')
                    new_body._reorganise_sides(ref_body)

                    if old_body.front is not None and old_body.back is not None:
                        #print('Matching original to off-cut:')
                        old_body._reorganise_sides(new_body)
                else:
                    #print('Matching off-cut to original:')
                    new_body._reorganise_sides(old_body)

        return back_body, front_body

def named_object_select(name):
    s = Selection.CreateByNames(name)
    if len(s.Items) == 0:
        s = None
        print('Named selection failed: ' + name)
    return s

def named_object_delete(name):
    s = named_object_select(name)
    if s is not None:
        Delete.Execute(s)

def named_object_rename(name, new_name):
    s = named_object_select(name)
    if s is not None:
        RenameObject.Execute(s, new_name)

def named_object_lock(name):
    s = named_object_select(name)
    if s is not None:
        ViewHelper.LockBodies(s, True)

def named_object_unlock(name):
    s = named_object_select(name)
    if s is not None:
        ViewHelper.LockBodies(s, False)

def named_object_rotate(name, angle):
    s = named_object_select(name)
    if s is not None:
        frame = Frame.Create(Point.Create(0, 0, 0), Direction.Create(0, -1, 0), Direction.Create(1, 0, 0))
        options = MoveOptions()
        options.CreatePatterns = False
        options.DetachFirst = False
        options.MaintainOrientation = False
        options.MaintainMirrorRelationships = True
        options.MaintainConnectivity = True
        options.MaintainOffsetRelationships = True
        options.Copy = False
        Move.Execute(s, frame, TransformType.RotateY, angle, options)

def named_object_extrude(face_name, body_name, thickness, direction, cut=False):
    s = named_object_select(face_name)
    if s is not None:
        face = Selection.Create(s.Items[0].Faces[0])
        options = ExtrudeFaceOptions()
        options.KeepMirror = True
        options.KeepLayoutSurfaces = False
        options.KeepCompositeFaceRelationships = True
        options.PullSymmetric = False
        options.OffsetMode = OffsetMode.IgnoreRelationships
        options.Copy = False
        options.ForceDoAsExtrude = False
        if cut:
            options.ExtrudeType = ExtrudeType.Cut
        else:
            options.ExtrudeType = ExtrudeType.Add
        result = ExtrudeFaces.Execute(face, direction, thickness, options)
        body = Selection.Create(result.CreatedBodies)
        RenameObject.Execute(body, body_name)

def named_surfaces_loft(surf_1_name, surf_2_name, body_name):
    s1 = named_object_select(surf_1_name)
    s2 = named_object_select(surf_2_name)
    if s1 is not None and s2 is not None:
        selection = Selection.Create(s1.Items[0].Faces[0], s2.Items[0].Faces[0])
        options = LoftOptions()
        options.GeometryCommandOptions = GeometryCommandOptions()
        Loft.Create(selection, None, options)
        named_object_rename('Solid', body_name)

def named_object_revolve_helix(face_name, body_name, origin, direction, pitch, revolutions, righthanded, cut=False):
    s = named_object_select(face_name)
    if s is not None:
        face = Selection.Create(s.Items[0].Faces[0])
        axis = Line.Create(origin, direction)
        taperAngle = 0
        bothSides = False
        options = RevolveFaceOptions()
        if cut:
            options.ExtrudeType = ExtrudeType.Cut
        else:
            options.ExtrudeType = ExtrudeType.Add
        if pitch:
            RevolveFaces.ByHelix(face, axis, direction, revolutions * pitch, pitch, taperAngle, righthanded, bothSides, options)
        else:
            RevolveFaces.Execute(face, axis, 2 * math.pi * revolutions, options)
        named_object_rename('Solid', body_name)

def combine_named_selections(list_of_names, new_name):
    s = Selection.CreateByGroups(Array[str](list_of_names))
    s.CreateAGroup(new_name)

def move_geometries_to_new_component(list_of_names, component_name):
    s = Selection.CreateByGroups(Array[str](list_of_names))
    if s is not None:
        result = ComponentHelper.MoveBodiesToComponent(s)
        result.CreatedComponents[0].SetName(component_name)

def write_parameters(filename, pars):
    with open(filename, 'w') as f:
        for p in pars:
            f.write(p + ' ' + str(opars[p]) + '\n')

def read_parameters(filename):
    par = {}
    with open(filename, 'r') as f:
        for line in f:
            pair = line.split()
            par[pair[0]] = float(pair[1])
    return par

def volume_of_named_solid(name):
    v = 0
    s = named_object_select(name)
    if s is not None:
        v = s.Items[0].MassProperties.Mass
    return v

def area_of_named_surface(name):
    return volume_of_named_solid(name)

def face_area_of_named_solid(name, number):
    a = 0
    s = named_object_select(name)
    if s is not None:
        if number < len(s.Items[0].Faces):
            f = Selection.Create(s.Items[0].Faces[number])
            a = f.Items[0].Area
        else:
            print('Number out of range for faces')
    return a

def shell_face_of_named_solid(name, number, thickness):
    s = named_object_select(name)
    if s is not None:
        if number < len(s.Items[0].Faces):
            f = Selection.Create(s.Items[0].Faces[number])
            Shell.RemoveFaces(f, -thickness)
        else:
            print('Number out of range for faces')

def CoG_of_named_solid(name):
    CoG_X = 0
    CoG_Y = 0
    CoG_Z = 0
    s = named_object_select(name)
    if s is not None:
        frame = s.Items[0].MassProperties.PrincipleAxes
        CoG_X = frame.Origin.X
        CoG_Y = frame.Origin.Y
        CoG_Z = frame.Origin.Z
    return CoG_X, CoG_Y, CoG_Z

def sketch_reset(orientation='XY', origin=(0,0,0)):
    O = Point.Create(*origin)

    if orientation == 'YX':
        B1 = Direction.Create( 0, 1, 0)
        B2 = Direction.Create( 1, 0, 0)
        B3 = Direction.Create( 0, 0,-1)
    elif orientation == 'YZ':
        B1 = Direction.Create( 0, 1, 0)
        B2 = Direction.Create( 0, 0, 1)
        B3 = Direction.Create( 1, 0, 0)
    elif orientation == 'ZY':
        B1 = Direction.Create( 0, 0, 1)
        B2 = Direction.Create( 0, 1, 0)
        B3 = Direction.Create(-1, 0, 0)
    elif orientation == 'XZ':
        B1 = Direction.Create( 1, 0, 0)
        B2 = Direction.Create( 0, 0, 1)
        B3 = Direction.Create( 0,-1, 0)
    elif orientation == 'ZX':
        B1 = Direction.Create( 0, 0, 1)
        B2 = Direction.Create( 1, 0, 0)
        B3 = Direction.Create( 0, 1, 0)
    else: #if orientation == 'XY':
        B1 = Direction.Create( 1, 0, 0)
        B2 = Direction.Create( 0, 1, 0)
        B3 = Direction.Create( 0, 0, 1)

    plane = Plane.Create(Frame.Create(O, B1, B2))
    ViewHelper.SetSketchPlane(plane)
    return plane, B3

# Add a line in the sketch plane
def sketch_line(p1, p2):
    start = Point2D.Create(p1[0], p1[1])
    end   = Point2D.Create(p2[0], p2[1])
    result = SketchLine.Create(start, end)
    return result.CreatedCurve

# Add an arc in the sketch plane
def sketch_arc(p0, p1, p2):
    origin = Point2D.Create(p0[0], p0[1]) # centre of the circle that the arc follows
    start  = Point2D.Create(p1[0], p1[1])
    end    = Point2D.Create(p2[0], p2[1])
    result = SketchArc.Create(origin, start, end)
    return result.CreatedCurve

# Add a rectangle in the sketch plane
def sketch_rect(p0, p1, p2):
    sp0 = Point2D.Create(p0[0], p0[1])
    sp1 = Point2D.Create(p1[0], p1[1])
    sp2 = Point2D.Create(p2[0], p2[1])
    result = SketchRectangle.Create(sp0, sp1, sp2)
    return result.CreatedCurve

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

    @staticmethod
    def from_to(from_point, to_point): # define vector between two points
        return Q2D_Vector.from_to(to_point.x() - from_point.x(), to_point.y() - from_point.y())

class Q2D_Line(Q2D_Object):

    def __init__(self, start, direction):
        Q2D_Object.__init__(self, "Line")
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

class Q2D_Circle(object):

    def __init__(self, center, radius):
        self.name = "Circle"
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

    def poly_points(self, interval):
        points = []
        circumference = 2.0 * math.pi * self.radius

        count = int(math.ceil(circumference / interval))
        for c in range(0, count):
            point = self.point_on_circumference((2.0 * math.pi * c) / count)
            points += [[point.x(), point.y()]]

        return points

class Q2D_Arc(Q2D_Object):

    def __init__(self, start, circle, clockwise=False):
        Q2D_Object.__init__(self, "Arc")
        self.start = start
        self.circle = circle
        self.clockwise = clockwise

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
            if print_path_info:
                print('Unable to add line to line - no intersection')
        else:
            if radius > 0:
                if print_path_info:
                    print('Adding line to line with transition')
                p1 = l1.project(pi)
                p2 = l2.project(pi)

                clockwise = d2.cross(d1) > 0
                self.__append(Q2D_Arc(p1, Q2D_Circle(pi, radius), clockwise))

                self.__append(Q2D_Line(p2, d2))
            else:
                if print_path_info:
                    print('Adding line to line without transition')
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
    def __intersect_line(line, circle, sense):
        point = None
        tangent = False

        midpoint = line.project(circle.center)
        cp = Q2D_Point.from_to(circle.center, midpoint)
        cross = cp.cross(line.direction)

        if abs(cp.length - circle.radius) < Q2D_Design_Tolerance:
            if print_path_info:
                print("tangent: error = {e}".format(e=(cp.length - circle.radius)))
            point = midpoint
            tangent = True # check sense
        elif cp.length > circle.radius:
            if print_path_info:
                print("line does not intersect circle; missed by {d}".format(d=(cp.length - circle.radius)))
        else: # cp.length < circle.radius:
            if print_path_info:
                print("line intersects circle")
            dv = line.direction.copy()
            dv.length = (circle.radius**2.0 - cp.length**2.0)**0.5

            if sense:
                point = midpoint.vector_relative(dv)
            else:
                point = midpoint.vector_relative(dv.reverse())

        return point, cross, tangent

    def __append_line_to_arc(self, line, transition, kwargs):
        arc = self.current

        if 'co_sense' in kwargs:
            co_sense = kwargs['co_sense']
        else:
            co_sense = True

        if 'farside' in kwargs:
            farside = kwargs['farside']
        else:
            farside = False

        if not arc.clockwise:
            sense = not co_sense
        else:
            sense = co_sense

        point, cross, tangent = Q2D_Path.__intersect_line(line, arc.circle, sense)
        if transition is None:
            if point is None:
                if print_path_info:
                    print('Unable to add line without transition')
            else:
                if print_path_info:
                    print('Adding line without transition')
                self.__append(Q2D_Line(point, line.direction))
        else:
            if not arc.clockwise:
                offset = -transition
            else:
                offset = transition

            if point is not None:
                if print_path_info:
                    print('point = ({x}, {y}); cross={c}; tangent={t}'.format(x=point.x(), y=point.y(), c=cross, t=tangent))

            if tangent:
                if (cross > 0.0 and not arc.clockwise) or (cross < 0.0 and arc.clockwise):
                    if not co_sense:
                        if print_path_info:
                            print('Co-sense transition should be used here')
                else:
                    if co_sense:
                        if print_path_info:
                            print('Contra-sense transition should be used here')

                if co_sense:
                    if print_path_info:
                        print('Adding (tangent) line (without transition)')
                    self.__append(Q2D_Line(line.project(point), line.direction))
                else:
                    if print_path_info:
                        print('Adding (tangent) line (with counter-sense transition)')
                    o = Q2D_Circle(arc.circle.center, arc.circle.radius + transition)
                    l = line.parallel(offset)
                    p, c, t = Q2D_Path.__intersect_line(l, o, not farside)
                    #print 'point = (', p.x(), p.y(), '); cross =', c, 'tangent =', t
                    self.__append(Q2D_Arc(arc.circle.project(p), Q2D_Circle(p, transition), clockwise=(not arc.clockwise)))
                    self.__append(Q2D_Line(line.project(p), line.direction))
            elif point is None:
                if (cross > 0.0 and not arc.clockwise) or (cross < 0.0 and arc.clockwise):
                    if not co_sense:
                        if print_path_info:
                            print('Co-sense transition should be used here')
                else:
                    if co_sense:
                        if print_path_info:
                            print('Contra-sense transition should be used here')

                if co_sense:
                    if transition > arc.circle.radius:
                        o = Q2D_Circle(arc.circle.center, transition - arc.circle.radius)
                        l = line.parallel(-offset)
                        p, c, t = Q2D_Path.__intersect_line(l, o, not farside)
                        if p is not None:
                            if print_path_info:
                                print('Adding line (with co-sense transition)')
                            #print 'point = (', p.x(), p.y(), '); cross =', c, 'tangent =', t
                            self.__append(Q2D_Arc(arc.circle.project(p, True), Q2D_Circle(p, transition), clockwise=arc.clockwise))
                            self.__append(Q2D_Line(line.project(p), line.direction))
                        else:
                            if print_path_info:
                                print('Unable to add line with specified (co-sense) transition; try increasing the transition radius')
                    else:
                        if print_path_info:
                            print('Unable to add line with specified (co-sense) transition; require transition radius > arc radius')
                else:
                    o = Q2D_Circle(arc.circle.center, arc.circle.radius + transition)
                    if arc.clockwise:
                        l = line.parallel( transition)
                    else:
                        l = line.parallel( transition)
                    p, c, t = Q2D_Path.__intersect_line(l, o, not farside)
                    if p is not None:
                        if print_path_info:
                            print('Adding line (with counter-sense transition)')
                        #print 'point = (', p.x(), p.y(), '); cross =', c, 'tangent =', t
                        self.__append(Q2D_Arc(arc.circle.project(p), Q2D_Circle(p, transition), clockwise=(not arc.clockwise)))
                        self.__append(Q2D_Line(line.project(p), line.direction))
                    else:
                        if print_path_info:
                            print('Unable to add line with specified (counter-sense) transition')
            else: # line intersects circle
                if co_sense:
                    if transition < arc.circle.radius:
                        o = Q2D_Circle(arc.circle.center, arc.circle.radius - transition)
                        l = line.parallel(-offset)
                        p, c, t = Q2D_Path.__intersect_line(l, o, not farside)
                        if p is not None:
                            if print_path_info:
                                print('Adding line (with co-sense transition)')
                            #print 'point = (', p.x(), p.y(), '); cross =', c, 'tangent =', t
                            self.__append(Q2D_Arc(arc.circle.project(p), Q2D_Circle(p, transition), clockwise=arc.clockwise))
                            self.__append(Q2D_Line(line.project(p), line.direction))
                        else:
                            if print_path_info:
                                print('Unable to add line with specified (co-sense) transition; try increasing the transition radius')
                    else:
                        if print_path_info:
                            print('Unable to add line with specified (co-sense) transition; require transition radius > arc radius')
                else:
                    o = Q2D_Circle(arc.circle.center, arc.circle.radius + transition)
                    l = line.parallel(offset)
                    p, c, t = Q2D_Path.__intersect_line(l, o, not farside)
                    if p is not None:
                        if print_path_info:
                            print('Adding (counter-sense) arc (with transition)')
                        #print('point = (', p.x(), p.y(), '); cross =', c, 'tangent =', t)
                        self.__append(Q2D_Arc(arc.circle.project(p), Q2D_Circle(p, transition), clockwise=(not arc.clockwise)))
                        self.__append(Q2D_Line(line.project(p), line.direction))

    def __append_arc_to_line(self, arc, transition, kwargs):
        line = self.current

        if 'co_sense' in kwargs:
            co_sense = kwargs['co_sense']
        else:
            co_sense = True

        if 'farside' in kwargs:
            farside = kwargs['farside']
        else:
            farside = False

        if arc.clockwise:
            sense = not co_sense
        else:
            sense = co_sense

        point, cross, tangent = Q2D_Path.__intersect_line(line, arc.circle, sense)
        if transition is None:
            if point is None:
                if print_path_info:
                    print('Unable to add arc without transition')
            else:
                if print_path_info:
                    print('Adding arc without transition')
                self.__append(Q2D_Arc(point, arc.circle, clockwise=arc.clockwise))
        else:
            if arc.clockwise:
                offset = -transition
            else:
                offset = transition

            if point is not None:
                if print_path_info:
                    print('point = ({x}, {y}); cross={c}; tangent={t}'.format(x=point.x(), y=point.y(), c=cross, t=tangent))

            if tangent:
                if (cross > 0.0 and not arc.clockwise) or (cross < 0.0 and arc.clockwise):
                    if not co_sense:
                        if print_path_info:
                            print('Co-sense transition should be used here')
                else:
                    if co_sense:
                        if print_path_info:
                            print('Contra-sense transition should be used here')

                if co_sense:
                    if print_path_info:
                        print('Adding (tangent) arc (without transition)')
                    self.__append(Q2D_Arc(point, arc.circle, clockwise=arc.clockwise))
                else:
                    if print_path_info:
                        print('Adding (counter-sense tangent) arc (with transition)')
                    o = Q2D_Circle(arc.circle.center, arc.circle.radius + transition)
                    l = line.parallel(-offset)
                    p, c, t = Q2D_Path.__intersect_line(l, o, farside)
                    #print 'point = (', p.x(), p.y(), '); cross =', c, 'tangent =', t
                    self.__append(Q2D_Arc(line.project(p), Q2D_Circle(p, transition), clockwise=(not arc.clockwise)))
                    self.__append(Q2D_Arc(arc.circle.project(p), arc.circle, clockwise=arc.clockwise))
            elif point is None:
                if (cross > 0.0 and not arc.clockwise) or (cross < 0.0 and arc.clockwise):
                    if not co_sense:
                        if print_path_info:
                            print('Co-sense transition should be used here')
                else:
                    if co_sense:
                        if print_path_info:
                            print('Contra-sense transition should be used here')

                if co_sense:
                    if transition > arc.circle.radius:
                        o = Q2D_Circle(arc.circle.center, transition - arc.circle.radius)
                        l = line.parallel(offset)
                        p, c, t = Q2D_Path.__intersect_line(l, o, farside)
                        if p is not None:
                            if print_path_info:
                                print('Adding (co-sense) arc (with transition)')
                            #print 'point = (', p.x(), p.y(), '); cross =', c, 'tangent =', t
                            self.__append(Q2D_Arc(line.project(p), Q2D_Circle(p, transition), clockwise=arc.clockwise))
                            self.__append(Q2D_Arc(arc.circle.project(p, True), arc.circle, clockwise=arc.clockwise))
                        else:
                            if print_path_info:
                                print('Unable to add (co-sense) arc with specified transition; try increasing the transition radius')
                    else:
                        if print_path_info:
                            print('Unable to add (co-sense) arc with specified transition; require transition radius > arc radius')
                else:
                    o = Q2D_Circle(arc.circle.center, arc.circle.radius + transition)
                    l = line.parallel(-offset)
                    p, c, t = Q2D_Path.__intersect_line(l, o, farside)
                    if p is not None:
                        if print_path_info:
                            print('Adding (counter-sense) arc (with transition)')
                        #print('point = (', p.x(), p.y(), '); cross =', c, 'tangent =', t)
                        self.__append(Q2D_Arc(line.project(p), Q2D_Circle(p, transition), clockwise=(not arc.clockwise)))
                        self.__append(Q2D_Arc(arc.circle.project(p), arc.circle, clockwise=arc.clockwise))
                    else:
                        if print_path_info:
                            print('Unable to add (counter-sense) arc with specified transition')
            else: # line intersects circle
                if co_sense:
                    if transition < arc.circle.radius:
                        o = Q2D_Circle(arc.circle.center, arc.circle.radius - transition)
                        l = line.parallel(offset)
                        p, c, t = Q2D_Path.__intersect_line(l, o, farside)
                        if p is not None:
                            if print_path_info:
                                print('Adding (co-sense) arc (with transition)')
                            #print('point = (', p.x(), p.y(), '); cross =', c, 'tangent =', t)
                            self.__append(Q2D_Arc(line.project(p), Q2D_Circle(p, transition), clockwise=arc.clockwise))
                            self.__append(Q2D_Arc(arc.circle.project(p), arc.circle, clockwise=arc.clockwise))
                        else:
                            if print_path_info:
                                print('Unable to add (co-sense) arc with specified transition; try increasing the transition radius')
                    else:
                        if print_path_info:
                            print('Unable to add (co-sense) arc with specified transition; require transition radius > arc radius')
                else:
                    o = Q2D_Circle(arc.circle.center, arc.circle.radius + transition)
                    l = line.parallel(-offset)
                    p, c, t = Q2D_Path.__intersect_line(l, o, farside)
                    if p is not None:
                        if print_path_info:
                            print('Adding (counter-sense) arc (with transition)')
                        #print('point = (', p.x(), p.y(), '); cross =', c, 'tangent =', t)
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
            if print_path_info:
                print("Unable to intersect arcs")
        else:
            if print_path_info:
                print("Adding arc with transition")
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

class Q2D_Plotter(object):

    __plt = None
    __mpatches = None

    @staticmethod
    def __load():
        if Q2D_Plotter.__plt is None:
            import matplotlib.pyplot as plt
            import matplotlib.patches as mpatches

            Q2D_Plotter.__plt = plt
            Q2D_Plotter.__mpatches = mpatches

    @staticmethod
    def show():
        if Q2D_Plotter.__plt is not None:
            Q2D_Plotter.__plt.show()

    def __init__(self, x_range, y_range):
        Q2D_Plotter.__load()

        xsize = 1500
        ysize = 1500
        dpi_osx = 192 # Something very illogical here.
        self._fig = Q2D_Plotter.__plt.figure(figsize=(xsize / dpi_osx, ysize / dpi_osx), dpi=(dpi_osx/2))

        self._ax = self._fig.add_subplot(111)
        self._ax.set_facecolor('white')
        self._ax.set_position([0.07, 0.06, 0.90, 0.90])

        self._ax.set_xlim(x_range)
        self._ax.set_ylim(y_range)

    def __draw_point(self, point, center=False):
        if center:
            marker = '+'
            color = 'green'
        else:
            marker = '.'
            color = Q2D_path_color
        if print_plot_info:
            print('Point: ({x},{y})'.format(x=point.start[0], y=point.start[1]))
        self._ax.scatter(point.start[0], point.start[1], marker=marker, color=color)

    def draw_points(self, points):
        marker = '.'
        color = Q2D_path_color
        for p in points:
            self._ax.scatter(p[0], p[1], marker=marker, color=color)

    def draw_elements(self, nodes, elements):
        for e in elements:
            n1 = nodes[e[0]]
            n2 = nodes[e[1]]
            n3 = nodes[e[2]]
            self._ax.plot([n1[0], n2[0], n3[0], n1[0]], [n1[1], n2[1], n3[1], n1[1]], '-', color=Q2D_path_color, linewidth=0.5)

    def __draw_circle(self, circle, construction=True):
        if construction and not plot_construction_arcs:
            return

        x_axis = 2.0 * circle.radius
        y_axis = 2.0 * circle.radius
        if construction:
            ec='green'
            ls='--'
        else:
            ec=Q2D_path_color
            ls='-'
        if print_plot_info:
            print('Ellipse: Center: ({x},{y}); Axes=({a},{b})'.format(x=circle.center.start[0], y=circle.center.start[1], a=x_axis, b=y_axis))
        patch = Q2D_Plotter.__mpatches.Ellipse(circle.center.start, x_axis, y_axis, edgecolor=ec, linestyle=ls, facecolor=None, fill=False, linewidth=1)
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
        if t2 <= t1:
            t2 += 360.0
        x_axis = 2.0 * arc.circle.radius
        y_axis = 2.0 * arc.circle.radius
        if print_plot_info:
            print('Arc: Center: ({x},{y}); Axes=({a},{b}); Angles=({s},{e})'.format(x=arc.circle.center.start[0], y=arc.circle.center.start[1], a=x_axis, b=y_axis, s=t1, e=t2))
        patch = Q2D_Plotter.__mpatches.Arc(arc.circle.center.start, x_axis, y_axis, theta1=t1, theta2=t2, edgecolor=Q2D_path_color, facecolor=None, fill=False)
        self._ax.add_patch(patch)
        self.__draw_point(arc.circle.center, True)
        self.__draw_point(arc.start)

    def __draw_line(self, line):
        p1 = line.start
        p2 = line.chain
        if p2.name != "Point":
            p2 = p2.start
        if print_plot_info:
            print('Line: From: ({x},{y}); To: ({a},{b})'.format(x=p1.start[0], y=p1.start[1], a=p2.start[0], b=p2.start[1]))
        self._ax.plot([p1.start[0], p2.start[0]], [p1.start[1], p2.start[1]], '-', color=Q2D_path_color, linewidth=1)
        self.__draw_point(p1)

    def draw(self, path):
        if path.name == "Path":
            item = path.chain

            while item is not None:
                if item.name == "Line":
                    self.__draw_line(item)
                elif item.name == "Arc":
                    self.__draw_arc(item)
                else:
                    self.__draw_point(item)
                item = item.chain

        elif path.name == "Circle":
            self.__draw_circle(path, False)

class Q2D_Sketcher(object):

    def __init__(self, plane): # where plane is a SpaceClaim sketch plane - see, e.g., sketch_reset()
        self.plane = plane
        self.curves = []
        self.shapes = []
        self.body = QSC_Body()

    def __draw_circle(self, circle):
        result = SketchCircle.Create(circle.center.point(), circle.radius)
        self.curves.append(result.CreatedCurve)
        self.shapes.append(result.CreatedCurve[0].Shape)

    def __draw_arc(self, arc):
        origin = arc.circle.center.point()
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
        result = SketchArc.Create(origin, p1.point(), p2.point())
        self.curves.append(result.CreatedCurve)
        self.shapes.append(result.CreatedCurve[0].Shape)

    def __draw_line(self, line):
        p1 = line.start
        p2 = line.chain
        if p2.name != "Point":
            p2 = p2.start
        result = SketchLine.Create(p1.point(), p2.point())
        self.curves.append(result.CreatedCurve)
        self.shapes.append(result.CreatedCurve[0].Shape)

    def draw(self, path):
        if path.name == "Path":
            item = path.chain

            while item is not None:
                if item.name == "Line":
                    self.__draw_line(item)
                elif item.name == "Arc":
                    self.__draw_arc(item)
                item = item.chain

        elif path.name == "Circle":
            self.__draw_circle(path)

    def _create_surface(self, name):
        shapes = Array[ITrimmedCurve](self.shapes)
        surface = PlanarBody.Create(self.plane, shapes, None, name)

    def _clear_curves(self):
        for c in self.curves:
            s = Selection.Create(c)
            Delete.Execute(s)

    def create_surface_and_clear(self, name, clear_curves=True):
        self._create_surface(name)
        if clear_curves:
            self._clear_curves()
        return QSC_Surface(name)

    def _match_curves(self, body_name, axis=None):
        self.body.rename(body_name)
        self.body.match_curves(self.curves, axis)

class Q2D_Extrusion(Q2D_Sketcher):

    def __init__(self, plane): # where plane is a SpaceClaim sketch plane - see, e.g., sketch_reset()
        Q2D_Sketcher.__init__(self, plane)

    def extrude_and_clear(self, name, direction, thickness):
        self._create_surface(name)
        named_object_extrude(name, name, thickness, direction, False)
        self._match_curves(name)
        self._clear_curves()
        return self.body

class Q2D_Helix(Q2D_Sketcher):

    def __init__(self, helix_radius, helix_pitch, origin, e_axis, e_radial, e_transverse, righthanded=True, incline=True): # where origin is (x,y,z) and e_* are basis vectors as (x,y,z)
        if incline:
            h_adjust = math.atan(helix_pitch / (2.0 * math.pi * helix_radius))
            c = math.cos(h_adjust)
            if righthanded:
                s =  math.sin(h_adjust)
            else:
                s = -math.sin(h_adjust)
        else:
            c = 1.0
            s = 0.0
        h_axis   = Direction.Create(*e_axis)
        h_prof_y = Direction.Create(*e_radial)
        h_prof_x = Direction.Create(c * e_axis[0] + s * e_transverse[0], c * e_axis[1] + s * e_transverse[1], c * e_axis[2] + s * e_transverse[2])
        h_origin = Point.Create(origin[0] + helix_radius * e_radial[0], origin[1] + helix_radius * e_radial[1], origin[2] + helix_radius * e_radial[2])
        h_plane  = Plane.Create(Frame.Create(h_origin, h_prof_x, h_prof_y))
        ViewHelper.SetSketchPlane(h_plane)

        Q2D_Sketcher.__init__(self, h_plane)
        self.origin = Point.Create(*origin)
        self.axis = h_axis
        self.pitch = helix_pitch
        self.radius = helix_radius
        self.righthanded = righthanded
        self.incline_cos = c
        self.incline_sin = s
        self.basis_origin = origin
        self.basis_e_axis = e_axis
        self.basis_e_radial = e_radial
        self.basis_e_transverse = e_transverse
        self.name = None

    def offset_plane(self, angle):
        c = math.cos(angle)
        s = math.sin(angle)
        e_radial     = ( self.basis_e_radial[0] * c + self.basis_e_transverse[0] * s,  self.basis_e_radial[1] * c + self.basis_e_transverse[1] * s,  self.basis_e_radial[2] * c + self.basis_e_transverse[2] * s)
        e_transverse = (-self.basis_e_radial[0] * s + self.basis_e_transverse[0] * c, -self.basis_e_radial[1] * s + self.basis_e_transverse[1] * c, -self.basis_e_radial[2] * s + self.basis_e_transverse[2] * c)

        c = self.incline_cos
        s = self.incline_sin
        prof_y = Direction.Create(*e_radial)
        prof_x = Direction.Create(c * self.basis_e_axis[0] + s * e_transverse[0], c * self.basis_e_axis[1] + s * e_transverse[1], c * self.basis_e_axis[2] + s * e_transverse[2])
        origin = Point.Create(*self.basis_origin)
        plane  = Plane.Create(Frame.Create(origin, prof_x, prof_y))
        return plane

    def split(self, angle, new_body_name, ref_body=None, make_surface_only=False):
        plane = self.offset_plane(angle)
        ViewHelper.SetSketchPlane(plane)
        plotter = Q2D_Sketcher(plane)

        occlusion = Q2D_Path.polygon([(-3.0 * self.pitch, 0.0), (3.0 * self.pitch, 0.0), (3.0 * self.pitch, 2.0 * self.radius), (-3.0 * self.pitch, 2.0 * self.radius)])
        plotter.draw(occlusion)
        surface = plotter.create_surface_and_clear('Helix-Split-Plane')
        if make_surface_only:
            return surface
        back_body, front_body = QSC_Body.cross_sect_and_match(self.body, surface, new_body_name, ref_body)
        self.body = back_body
        surface.delete()
        return front_body

    def revolve_and_clear(self, name, revolutions, cut=False, match=True, clear=True):
        self.name = name
        self._create_surface(name)
        named_object_revolve_helix(name, name, self.origin, self.axis, self.pitch, revolutions, self.righthanded, cut)
        if match:
            self._match_curves(name, Line.Create(self.origin, self.axis))
        if clear:
            self._clear_curves()
        return self.body

class Q3D_NURBS(object): # cubic surface

    @staticmethod
    def default_knots(Ncp):
        k = [Knot(0, 4)]
        for ik in range(1, Ncp - 3):
            k.append(Knot(ik, 1))
        k.append(Knot(Ncp - 3, 4))
        return k

    @staticmethod
    def default_range(Ncp):
        return Ncp - 3

    def __init__(self, Nu, Nv):
        self.Nu = Nu
        self.Nv = Nv
        self.uu = Interval.Create(0, Q3D_NURBS.default_range(Nu))
        self.vv = Interval.Create(0, Q3D_NURBS.default_range(Nv))
        self.ku = Array[Knot](Q3D_NURBS.default_knots(Nu))
        self.kv = Array[Knot](Q3D_NURBS.default_knots(Nv))
        self.cp = Array.CreateInstance(ControlPoint, Nu, Nv) # control points

    def set_control_point(self, u, v, xyz):
        self.cp[u,v] = ControlPoint(Point.Create(xyz[0], xyz[1], xyz[2]), 1)

    def add_controlpoints_to_sketch(self):
        for iv in range(0, self.Nv):
            for iu in range(0, self.Nu):
                SketchPoint.Create(self.cp[iu,iv].Position)

    def add_nurbscurves_to_sketch(self):
        d = NurbsData(4, False, False, self.ku)
        for iv in range(0, self.Nv):
            c = Array.CreateInstance(ControlPoint, self.Nu)
            for iu in range(0, self.Nu):
                c[iu] = self.cp[iu,iv]
            SketchNurbs.Create(NurbsCurve.CreateFromControlPoints(d, c))

        d = NurbsData(4, False, False, self.kv)
        for iu in range(0, self.Nu):
            c = Array.CreateInstance(ControlPoint, self.Nv)
            for iv in range(0, self.Nv):
                c[iv] = self.cp[iu,iv]
            SketchNurbs.Create(NurbsCurve.CreateFromControlPoints(d, c))

    def create_nurbs_surface(self, name):
        named_object_delete(name)

        surf_ud = NurbsData(4, False, False, self.ku)
        surf_vd = NurbsData(4, False, False, self.kv)
        surf_pt = NurbsSurface.Create(surf_ud, surf_vd, self.cp)

        bbox = BoxUV.Create(self.uu, self.vv)
        SurfaceBody.Create(surf_pt, bbox, None, name)

    @staticmethod
    def example(name, Nu, Nv): # points on a unit sphere
        NS = Q3D_NURBS(Nu, Nv)
        for iv in range(0, Nv):
            v = math.pi * (0.5 + float(iv)) / float(Nv)
            for iu in range(0, Nu):
                u = 2.0 * math.pi * (0.5 + float(iu)) / float(Nu)
                xyz = (math.cos(u) * math.sin(v), math.sin(u) * math.sin(v), math.cos(v))
                NS.set_control_point(iu, iv, xyz)

        NS.create_nurbs_surface(name)
        NS.add_nurbscurves_to_sketch()
        NS.add_controlpoints_to_sketch()
        return NS

# Helix starting at (0,radius,0) and winding along z-axis
# Nrotations must be a positive integer
# kappa is the curvature of the helix centreline in the yz-plane
def add_helix_to_sketch(radius, pitch, Nrotations=7, kappa=0):
    Ncps = 1 + 6 * Nrotations
    Narc = 3 * Nrotations
    knots = [Knot(0, 3)]
    for a in range(1, Narc):
        knots.append(Knot(a, 2))
    knots.append(Knot(Narc, 3))
    knarr = Array[Knot](knots)
    d = NurbsData(3, False, False, knarr)
    c = Array.CreateInstance(ControlPoint, Ncps)
    rt3 = 3.0**0.5
    eqp = [(0.0, 1.0), (rt3, 1.0), (rt3/2, -0.5), (0.0, -2.0), (-rt3/2, -0.5), (-rt3, 1.0)]
    cpi = 0
    if kappa > 0:
        theta = 0.0
    else:
        z = 0.0
    for r in range(0, Nrotations):
        for p in range(0, 6):
            x, y = eqp[p]
            x = x * radius
            y = y * radius
            if kappa > 0:
                z = (1.0 / kappa + y) * math.sin(theta)
                y = (1.0 / kappa + y) * math.cos(theta) - 1.0 / kappa
            if p % 2 == 0:
                wt = 1.0
            else:
                wt = 0.5
            c[cpi] = ControlPoint(Point.Create(x, y, z), wt)
            cpi = cpi + 1
            if kappa > 0:
                theta = theta + pitch * kappa / 6.0
            else:
                z = z + pitch / 6.0
    x, y = eqp[0]
    x = x * radius
    y = y * radius
    if kappa > 0:
        z = (1.0 / kappa + y) * math.sin(theta)
        y = (1.0 / kappa + y) * math.cos(theta) - 1.0 / kappa
    c[cpi] = ControlPoint(Point.Create(x, y, z), 1)
    SketchNurbs.Create(NurbsCurve.CreateFromControlPoints(d, c))

# ==== Q2D examples ==== #

if Q2D_SpaceClaim:
    # Let's start afresh:
    remove_all_bodies()
    remove_all_curves()
    remove_all_datum_planes()
    remove_all_components()

if arc_test == 0:
    if Q2D_SpaceClaim:
        plane, normal = sketch_reset()
        plotter = Q2D_Sketcher(plane)
    else:
        plotter = Q2D_Plotter([-4,4], [-3,3])

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

    plotter.draw(path)

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

    plotter.draw(path)

    if Q2D_SpaceClaim:
        print("Attempting to create a surface will fail; however, switching to solid view will let SpaceClaim identify bounded regions...")

elif arc_test == 1:
    if Q2D_SpaceClaim:
        plane, normal = sketch_reset()
        plotter = Q2D_Sketcher(plane)
    else:
        plotter = Q2D_Plotter([-4.0,4.0], [-4.0,4.0])

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

    plotter.draw(path)

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

    plotter.draw(path)

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

    plotter.draw(path)

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

    plotter.draw(path)

    if Q2D_SpaceClaim:
        print("Attempting to create a surface will fail; however, switching to solid view will let SpaceClaim identify bounded regions...")

elif arc_test == 2: # let's draw a hook

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

    # Let's draw the hook
    if Q2D_SpaceClaim:
        plane, normal = sketch_reset()
        plotter = Q2D_Extrusion(plane)
    else:
        plotter = Q2D_Plotter([-0.13,0.13], [-0.07,0.19])

    p_start = Q2D_Point((0.0, -r_seat))	# start/end point of path

    p_seat  = Q2D_Point((0.0, 0.0))		# construction circle-centers
    p_hole  = Q2D_Point((0.0, y_csep))
    p_main  = Q2D_Point((x_main, y_main))

    c_seat = Q2D_Circle(p_seat, r_seat)                 # circle outlining the seat of the hook
    a_seat = Q2D_Arc(p_start, c_seat, clockwise=False)  # define arc anti-clockwise from bottom
    c_top  = Q2D_Circle(p_hole, r_top)                  # circle outlining the top of the hook
    a_top  = Q2D_Arc(None, c_top, clockwise=True)       # define arc clockwise; start irrelevant
    c_main = Q2D_Circle(p_main, r_main)	   	            # circle outlining the top of the hook
    a_main = Q2D_Arc(None, c_main, clockwise=True)      # define arc clockwise; start irrelevant

    l_neck = Q2D_Line(p_hole, Q2D_Vector(DEG(neck_a)))  # neck center-line

    path = Q2D_Path(a_seat)
    path.append(l_neck.parallel(-neck_t / 2, True), transition=r1, farside=False, co_sense=True)
    path.append(a_top, transition=r2, farside=False, co_sense=False)
    path.append(l_neck.parallel( neck_t / 2, False), transition=r2, farside=False, co_sense=False)
    path.append(a_main, transition=r2, farside=False, co_sense=False)
    path.append(a_seat, transition=rb, farside=False, co_sense=True)
    path.end_point(p_start)

    plotter.draw(path)

    plotter.draw(Q2D_Circle(p_hole, r_hole)) # circle outlining the top hole of the hook

    if Q2D_SpaceClaim:
        plotter.extrude_and_clear('Hook', normal, 0.008)
        # The result is a solid hook with 13 faces
        #  10 have  4 edges - the outside faces
        #   1 has   2 edges - the hole
        #   2 have 11 edges - the front and back faces
        # sides actually matches the initial set of curves, so in this particular case:
        #  sides[0] == sides[10] - the seat
        #  sides[1 .. 9]         - clockwise around the hook
        #  sides[11]             - the top hole
        Selection.Create(plotter.body.sides[0]).CreateAGroup('Seat')
        Selection.Create(plotter.body.sides[11]).CreateAGroup('Hole')
        Selection.Create(plotter.body.front).CreateAGroup('Front')
        Selection.Create(plotter.body.back).CreateAGroup('Back')

elif arc_test == 3:
    if Q2D_SpaceClaim:
        Q3D_NURBS.example('sphere', 12, 8)

elif arc_test == 4:
    def make_conduit_profile(P):
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

        if GeometrySequence == 0:
            P.draw(Q2D_Circle(Q2D_Point((0.005,-0.005)), 0.005))
        else:
            P.draw(path)

    if Q2D_SpaceClaim:
        h_radius = 0.05
        h_pitch = 0.02
        h_revs  = 2

        black = (  0.0,   0.0,   0.0,   0.0)
        white = (255.0, 255.0, 255.0, 255.0)
        red   = (255.0, 255.0,   0.0,   0.0)
        green = (255.0,   0.0, 255.0,   0.0)
        blue  = (255.0,   0.0,   0.0, 255.0)

        plotter = Q2D_Helix(h_radius, h_pitch, (0,0,-2.5*h_pitch), (0,0,1), (0,1,0), (1,0,0))
        make_conduit_profile(plotter)
        Conduit_Left = plotter.revolve_and_clear('Conduit-Left', h_revs)

        Selection.Create(Conduit_Left.front).CreateAGroup('Conduit-Left-Front')
        Selection.Create(Conduit_Left.back).CreateAGroup('Conduit-Left-Back')

        Conduit_Left.paint(black, white, red, green)
        Conduit_Left.lock()

        plotter = Q2D_Helix(h_radius, h_pitch, (0,0,-0.5*h_pitch), (0,0,1), (0,1,0), (1,0,0))
        make_conduit_profile(plotter)
        Conduit_Middle = plotter.revolve_and_clear('Conduit-Middle', 1.0)

        Conduit_Middle.paint(black, white, green, blue)
        Conduit_Middle.lock()

        Conduit_Middle_Helix = plotter

        plotter = Q2D_Helix(h_radius, h_pitch, (0,0,0.5*h_pitch), (0,0,1), (0,1,0), (1,0,0))
        make_conduit_profile(plotter)
        Conduit_Right = plotter.revolve_and_clear('Conduit-Right', 2.0)

        Selection.Create(Conduit_Right.front).CreateAGroup('Conduit-Right-Front')
        Selection.Create(Conduit_Right.back).CreateAGroup('Conduit-Right-Back')

        Conduit_Right.paint(black, white, blue, red)
        Conduit_Right.lock()

        Conduit_Left.hide()
        Conduit_Right.hide()
        Conduit_Middle.unlock()

        Conduit_Middle_Right  = Conduit_Middle_Helix.split(DEG(175.0), 'Conduit-Middle-Right',  Conduit_Right)
        Conduit_Middle_Right.lock()
        Conduit_Middle_Right.hide()

        Conduit_Middle_Middle = Conduit_Middle_Helix.split(DEG(185.0), 'Conduit-Middle-Middle', Conduit_Middle_Right)
        Conduit_Middle_Middle.paint(black, white, green, blue)
        Conduit_Middle_Middle.lock()
        Conduit_Middle_Middle.hide()

        Conduit_Middle_Left = Conduit_Middle_Helix.body
        Conduit_Middle_Left.rename('Conduit-Middle-Left')
        Conduit_Middle_Left.lock()
        Conduit_Middle_Left.hide()

        Conduit_Left.show()
        Conduit_Right.show()
        Conduit_Middle_Left.show()
        Conduit_Middle_Middle.show()
        Conduit_Middle_Right.show()

        Selection.Create(Conduit_Middle_Left.front).CreateAGroup('Conduit-Middle-Left-Front')
        Selection.Create(Conduit_Middle_Left.back).CreateAGroup('Conduit-Middle-Left-Back')

        Selection.Create(Conduit_Middle_Middle.front).CreateAGroup('Conduit-Middle-Middle-Front')
        Selection.Create(Conduit_Middle_Middle.back).CreateAGroup('Conduit-Middle-Middle-Back')

        Selection.Create(Conduit_Middle_Right.front).CreateAGroup('Conduit-Middle-Right-Front')
        Selection.Create(Conduit_Middle_Right.back).CreateAGroup('Conduit-Middle-Right-Back')
    else:
        plotter = Q2D_Plotter([-0.01,0.04], [-0.01,0.01])
        make_conduit_profile(plotter)

elif arc_test == 5:
    midoff = 0.001
    min_t  = 0.005
    skin_t = 0.001

    def ski_top(zoff=0.0):
        pts = []
        pts.append((-0.65,0.005,0.03))
        pts.append((-0.62,0.040,0.00))
        pts.append((-0.61,0.040,0.00))
        pts.append((-0.60,0.040,0.00))
        pts.append((-0.40,0.040,0.00))
        pts.append((-0.20,0.030,0.01))
        pts.append(( 0.00,0.030,0.01))
        pts.append(( 0.20,0.030,0.01))
        pts.append(( 0.40,0.040,0.00))
        pts.append(( 0.60,0.040,0.00))
        Nu = len(pts)
        Nv = 4
        NS = Q3D_NURBS(Nu, Nv)
        for iu in range(0, Nu):
            p = pts[iu]
            x = p[0]
            y = p[1]
            z = p[2] + min_t / 2.0 + zoff
            NS.set_control_point(iu, 0, (x, y, z))
            NS.set_control_point(iu, 1, (x, midoff, z))
            NS.set_control_point(iu, 2, (x, -midoff, z))
            NS.set_control_point(iu, 3, (x, -y, z))

        name = 'ski-top'
        NS.create_nurbs_surface(name)
        #NS.add_nurbscurves_to_sketch()
        #NS.add_controlpoints_to_sketch()

    def ski_bottom(zoff=0.0):
        pts = []
        pts.append((-0.65,0.005,0.03))
        pts.append((-0.62,0.040,0.00))
        pts.append((-0.61,0.040,0.00))
        pts.append((-0.60,0.040,0.00))
        pts.append((-0.40,0.040,0.00))
        pts.append((-0.20,0.030,0.005))
        pts.append(( 0.00,0.030,0.005))
        pts.append(( 0.20,0.030,0.005))
        pts.append(( 0.40,0.040,0.00))
        pts.append(( 0.60,0.040,0.00))
        Nu = len(pts)
        Nv = 4
        NS = Q3D_NURBS(Nu, Nv)
        for iu in range(0, Nu):
            p = pts[iu]
            x = p[0]
            y = p[1]
            z = p[2] - min_t / 2.0 + zoff
            NS.set_control_point(iu, 0, (x, y, z))
            NS.set_control_point(iu, 1, (x, midoff, z))
            NS.set_control_point(iu, 2, (x, -midoff, z))
            NS.set_control_point(iu, 3, (x, -y, z))

        name = 'ski-bottom'
        NS.create_nurbs_surface(name)
        #NS.add_nurbscurves_to_sketch()
        #NS.add_controlpoints_to_sketch()

    ski_top()
    ski_bottom()
    named_surfaces_loft('ski-top', 'ski-bottom', 'ski-core')

    Core = QSC_Select('ski-core')
    Core.lock()

    def surf_split(surf_name, new_surf_name, xoff):
        origin = Point.Create(xoff, 0.0, 0.0)
        prof_x = Direction.Create(0.0, 1.0, 0.0)
        prof_y = Direction.Create(0.0, 0.0, 1.0)
        plane  = Plane.Create(Frame.Create(origin, prof_x, prof_y))
        ViewHelper.SetSketchPlane(plane)

        plotter = Q2D_Sketcher(plane)
        occlusion = Q2D_Path.polygon([(-0.1, -0.1), (0.1, -0.1), (0.1, 0.1), (-0.1, 0.1)])
        plotter.draw(occlusion)
        plotter.create_surface_and_clear('split-plane')
        splitter = QSC_Surface('split-plane')

        surface = QSC_Surface(surf_name)
        surface.select()
        SplitBody.ByCutter(surface.selection, splitter.principal_face(), False)

        splitter.delete()

        new_surf = QSC_Surface(surf_name + '1')
        new_surf.rename(new_surf_name)

    ski_top()
    Top = QSC_Surface('ski-top')

    surf_split('ski-top', 'ski-top-front', -0.15)
    TopFront = QSC_Surface('ski-top-front')
    TopFront.lock()

    surf_split('ski-top', 'ski-top-foot', 0.15)
    TopFoot = QSC_Surface('ski-top-foot')
    TopFoot.lock()

    Top.rename('ski-top-back')
    Top.lock()

    ski_bottom()
    Bottom = QSC_Surface('ski-bottom')

    surf_split('ski-bottom', 'ski-bottom-tip', -0.6)
    Tip = QSC_Surface('ski-bottom-tip')
    Tip.lock()

    surf_split('ski-bottom', 'ski-bottom-far-front', -0.5)
    FarFront = QSC_Surface('ski-bottom-far-front')
    FarFront.lock()

    surf_split('ski-bottom', 'ski-bottom-near-front', -0.15)
    NearFront = QSC_Surface('ski-bottom-near-front')
    NearFront.lock()

    surf_split('ski-bottom', 'ski-bottom-foot',  0.15)
    Foot = QSC_Surface('ski-bottom-foot')
    Foot.lock()

    surf_split('ski-bottom', 'ski-bottom-near-back', 0.5)
    NearBack = QSC_Surface('ski-bottom-near-back')
    NearBack.lock()

    Bottom.rename('ski-bottom-far-back')
    Bottom.lock()

    TopFoot.create_named_selection('Ski Top Foot')
    FarFront.create_named_selection('Ski Bottom Front')
    Bottom.create_named_selection('Ski Bottom Back')

elif arc_test == 6:
    black = (  0.0,   0.0,   0.0,   0.0)
    white = (255.0, 255.0, 255.0, 255.0)
    red   = (255.0, 255.0,   0.0,   0.0)
    green = (255.0,   0.0, 255.0,   0.0)
    blue  = (255.0,   0.0,   0.0, 255.0)

    plane, normal = sketch_reset('XY', (0.0,0.0,-1.0))
    plotter = Q2D_Extrusion(plane)
    square = Q2D_Path.polygon([(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)])
    plotter.draw(square)
    Ref = plotter.extrude_and_clear('Ref', normal, 1.0)
    Ref.paint(black, white, blue, red)
    Ref.lock()

    plane, normal = sketch_reset('XY', (0.0,0.0,0.0))
    plotter = Q2D_Extrusion(plane)
    square = Q2D_Path.polygon([(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)])
    plotter.draw(square)
    Cube = plotter.extrude_and_clear('Cube', normal, 1.0)
    Cube.paint(black, white, blue, red)

    plane, normal = sketch_reset('XY', (0.0,0.0,0.5))
    splitter = Q2D_Sketcher(plane)
    outline = Q2D_Path.polygon([(-1.0,-1.0), (2.0,-1.0), (2.0,2.0), (-1.0,2.0)])
    splitter.draw(outline)
    split_plane = splitter.create_surface_and_clear('split-plane')

    Offcut = Cube.cross_sect_and_match(split_plane, 'Offcut', Ref)
    Offcut.paint(black, white, blue, red)
    Cube.paint(black, white, blue, red)
    split_plane.delete()

elif arc_test == 7:
    def rotate(x, y, theta):
        s = math.sin(theta)
        c = math.cos(theta)
        return x * c - y * s, y * c + x * s

    ftheta = DEG(Parameters.foil_theta)
    fdepth = Parameters.foil_depth
    foil_w = Parameters.foil_width
    foil_h = Parameters.foil_height
    foil_l = Parameters.foil_left
    foil_r = Parameters.foil_right
    foil_d = Parameters.foil_down
    foil_u = Parameters.foil_up

    pt_l  = (-foil_w / 2.0,  foil_h * (foil_l - 0.5))
    pt_dl = (-foil_w / 2.0, -foil_h / 2.0)
    pt_d  = ( foil_w * (foil_d - 0.5), -foil_h / 2.0)
    pt_dr = ( foil_w / 2.0, -foil_h / 2.0)
    pt_r  = ( foil_w / 2.0,  foil_h * (foil_r - 0.5))
    pt_ur = ( foil_w / 2.0,  foil_h / 2.0)
    pt_u  = ( foil_w * (foil_u - 0.5),  foil_h / 2.0)
    pt_ul = (-foil_w / 2.0,  foil_h / 2.0)

    pts = [pt_l, pt_dl, pt_d, pt_dr, pt_r, pt_ur, pt_u, pt_ul]

    wt_dl = math.sqrt(1.0 / Parameters.wt_down_left)
    wt_dr = math.sqrt(1.0 / Parameters.wt_down_right)
    wt_ul = math.sqrt(1.0 / Parameters.wt_up_left)
    wt_ur = math.sqrt(1.0 / Parameters.wt_up_right)

    wt = [1.0, wt_dl, 1.0, wt_dr, 1.0, wt_ur, 1.0, wt_ul]

    Narc = 4
    Ncps = 1 + 2 * Narc
    knots = [Knot(0, 3)]
    for a in range(1, Narc):
        knots.append(Knot(a, 2))
    knots.append(Knot(Narc, 3))
    knarr = Array[Knot](knots)
    d = NurbsData(3, False, False, knarr)
    c = Array.CreateInstance(ControlPoint, Ncps)
    cpi = 0
    z = 0.0
    for p in range(0, 2 * Narc):
        x, y = pts[p]
        if ftheta:
            x, y = rotate(x, y, ftheta)
        c[cpi] = ControlPoint(Point.Create(x, y, z), wt[p])
        cpi = cpi + 1
    x, y = pts[0]
    if ftheta:
        x, y = rotate(x, y, ftheta)
    c[cpi] = ControlPoint(Point.Create(x, y, z), wt[0])
    plane, normal = sketch_reset()
    sn = SketchNurbs.Create(NurbsCurve.CreateFromControlPoints(d, c))
    shapes = Array[ITrimmedCurve]([sn.CreatedCurve[0].Shape])
    surface = PlanarBody.Create(plane, shapes, None, 'foil')
    s = Selection.Create(sn.CreatedCurve)
    Delete.Execute(s)
    named_object_extrude('foil', 'Foil', fdepth, normal)

elif arc_test == 8 or arc_test == 9: # let's draw a hook

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

    # Let's draw the hook
    p_start = Q2D_Point((0.0, -r_seat))	# start/end point of path

    p_seat  = Q2D_Point((0.0, 0.0))		# construction circle-centers
    p_hole  = Q2D_Point((0.0, y_csep))
    p_main  = Q2D_Point((x_main, y_main))

    c_seat = Q2D_Circle(p_seat, r_seat)                 # circle outlining the seat of the hook
    a_seat = Q2D_Arc(p_start, c_seat, clockwise=False)  # define arc anti-clockwise from bottom
    c_top  = Q2D_Circle(p_hole, r_top)                  # circle outlining the top of the hook
    a_top  = Q2D_Arc(None, c_top, clockwise=True)       # define arc clockwise; start irrelevant
    c_main = Q2D_Circle(p_main, r_main)	   	            # circle outlining the top of the hook
    a_main = Q2D_Arc(None, c_main, clockwise=True)      # define arc clockwise; start irrelevant

    l_neck = Q2D_Line(p_hole, Q2D_Vector(DEG(neck_a)))  # neck center-line

    path = Q2D_Path(a_seat)
    path.append(l_neck.parallel(-neck_t / 2, True), transition=r1, farside=False, co_sense=True)
    path.append(a_top, transition=r2, farside=False, co_sense=False)
    path.append(l_neck.parallel( neck_t / 2, False), transition=r2, farside=False, co_sense=False)
    path.append(a_main, transition=r2, farside=False, co_sense=False)
    path.append(a_seat, transition=rb, farside=False, co_sense=True)
    path.end_point(p_start)

    hole = Q2D_Circle(p_hole, r_hole)

    if arc_test == 8: # offset path
        plotter = Q2D_Plotter([-0.13,0.13], [-0.07,0.19])
        plotter.draw(path)
        plotter.draw(hole) # circle outlining the top hole of the hook

        Q2D_path_color = 'red'
        for i in range(-3,4,6):
            inset = 0.001 * i
            plotter.draw(path.offset_path(inset))

    if arc_test == 9:
        ppts = path.poly_points(0.003, 0.005)
        ppts.reverse()
        #plotter.draw_points(ppts)

        hpts = hole.poly_points(0.002)

        import dmsh
        poly = dmsh.Difference(dmsh.Polygon(ppts), dmsh.Polygon(hpts))
        #poly = dmsh.Polygon(ppts)

        def edge_size(x):
            dseat = (x[0]**2 + x[1]**2)**0.5
            dhole = (x[0]**2 + (x[1]-y_csep)**2)**0.5
            return 0.005 - 0.001 * (dhole < 0.07) - 0.001 * (dhole < 0.02) - 0.002 * (dseat < 0.02)

        print("Generating mesh...")
        nodes, elements = dmsh.generate(poly, edge_size, show=False, tol=1) # high tolerance to take the default mesh
        #nodes, elements = dmsh.generate(poly, 0.005, show=False, tol=5E-4)

        boundary = []
        for n1 in nodes:
            matched = False
            for n2 in ppts:
                if n1[0] == n2[0] and n1[1] == n2[1]:
                    matched = True
                    break
            if not matched:
                for n2 in hpts:
                    if n1[0] == n2[0] and n1[1] == n2[1]:
                        matched = True
                        break
            if matched:
                boundary.append(True)
            else:
                boundary.append(False)

        def node_is_left(nn, n0, n1):
            vn = nn - n0
            vt = n1 - n0
            return vn[0] * vt[1] - vn[1] * vt[0] < 0

        def element_contains_node(N, n, e):
            contains = False
            nn = N[n]
            n0 = N[e[0]]
            n1 = N[e[1]]
            n2 = N[e[2]]
            if node_is_left(nn, n0, n1) and node_is_left(nn, n1, n2) and node_is_left(nn, n2, n0):
                contains = True
                print("Violation @ Node #{n}".format(n=n))
            return contains

        def violation(nn, n0, n1):
            vn = nn - n0
            vt = n1 - n0
            x = vt[0]
            y = vt[1]
            l = (x**2 + y**2)**0.5
            vt[0] = -y / l
            vt[1] =  x / l
            vdot = vn[0] * vt[0] + vn[1] * vt[1]
            if abs(vdot) < l * 1E-2:
                #print("vdot={v}".format(v=vdot))
                if vdot < 0:
                    vdot = l * -1E-2
                else:
                    vdot = l *  1E-2
            return vt * vdot

        def verify(P, N, E, B):
            adjustments = []
            for e1 in E:
                for e2 in E:
                    if e1 is not e2:
                        if e1[0] in e2 and e1[1] in e2:
                            if element_contains_node(N, e1[2], e2):
                                N[e1[2]] -= 2.0 * violation(N[e1[2]], N[e1[0]], N[e1[1]])
                                if P is not None:
                                    P.draw_points([N[e1[2]]])
                                adjustments.append((e1[2], -1.01 * violation(N[e1[2]], N[e1[0]], N[e1[1]])))
                        elif e1[1] in e2 and e1[2] in e2:
                            if element_contains_node(N, e1[0], e2):
                                N[e1[0]] -= 2.0 * violation(N[e1[0]], N[e1[1]], N[e1[2]])
                                if P is not None:
                                    P.draw_points([N[e1[0]]])
                                adjustments.append((e1[0], -1.01 * violation(N[e1[0]], N[e1[1]], N[e1[2]])))
                        elif e1[2] in e2 and e1[0] in e2:
                            if element_contains_node(N, e1[1], e2):
                                N[e1[1]] -= 2.0 * violation(N[e1[1]], N[e1[2]], N[e1[0]])
                                if P is not None:
                                    P.draw_points([N[e1[1]]])
                                adjustments.append((e1[1], -1.01 * violation(N[e1[1]], N[e1[2]], N[e1[0]])))

            for e1 in E:
                if not node_is_left(N[e1[0]], N[e1[1]], N[e1[2]]):
                    if B[e1[0]] and B[e1[1]] and not B[e1[2]]:
                        # move e1[2]
                        N[e1[2]] -= 2.0 * violation(N[e1[2]], N[e1[0]], N[e1[1]])
                        if P is not None:
                            P.draw_points([N[e1[2]]])
                        adjustments.append((e1[2], -1.01 * violation(N[e1[2]], N[e1[0]], N[e1[1]])))
                    if B[e1[1]] and B[e1[2]] and not B[e1[0]]:
                        # move e1[0]
                        N[e1[0]] -= 2.0 * violation(N[e1[0]], N[e1[1]], N[e1[2]])
                        if P is not None:
                            P.draw_points([N[e1[0]]])
                        adjustments.append((e1[0], -1.01 * violation(N[e1[0]], N[e1[1]], N[e1[2]])))
                    if B[e1[2]] and B[e1[0]] and not B[e1[1]]:
                        # move e1[1]
                        N[e1[1]] -= 2.0 * violation(N[e1[1]], N[e1[2]], N[e1[0]])
                        if P is not None:
                            P.draw_points([N[e1[1]]])
                        adjustments.append((e1[1], -1.01 * violation(N[e1[1]], N[e1[2]], N[e1[0]])))

            return adjustments

        print("Verifying mesh...")
        while True:
            plotter = None
            Q2D_path_color = 'red'
            adjustments = verify(plotter, nodes, elements, boundary)
            if len(adjustments) == 0:
                break
            print(adjustments)
            print("Re-verifying mesh...")

        enable_Optimesh = True
        if enable_Optimesh:
            print("Optimising mesh...")
            import optimesh
            #nodes, elements = optimesh.cpt.fixed_point_uniform(nodes, elements, 1.0e-10, 100, verbose=True)
            #nodes, elements = optimesh.odt.fixed_point_uniform(nodes, elements, 1.0e-10, 100, verbose=True)
            #nodes, elements = optimesh.cvt.quasi_newton_uniform_full(nodes, elements, 1.0e-10, 100, verbose=True)
            nodes, elements = optimesh.cpt.linear_solve_density_preserving(nodes, elements, 1.0e-10, 100, verbose=True)

        plotter = Q2D_Plotter([-0.13,0.13], [-0.07,0.19])
        Q2D_path_color = 'blue'
        plotter.draw(path)
        plotter.draw(hole) # circle outlining the top hole of the hook

        Q2D_path_color = 'grey'
        plotter.draw_elements(nodes, elements)

elif arc_test == 10:
    def offset_rotate_scale(x, y, theta, scale, offset=0.25):
        s = math.sin(theta)
        c = math.cos(theta)
        return scale * ((x - offset) * c - y * s), scale * (y * c + (x - offset) * s)

    # Original NACA 2412 coordinates
    NACA_2412 = [
        [1,			0.0013],
        [0.95,		0.0114],
        [0.9,		0.0208],
        [0.8,		0.0375],
        [0.7,		0.0518],
        [0.6,		0.0636],
        [0.5,		0.0724],
        [0.4,		0.078],
        [0.3,		0.0788],
        [0.25,		0.0767],
        [0.2,		0.0726],
        [0.15,		0.0661],
        [0.1,		0.0563],
        [0.075,		0.0496],
        [0.05,		0.0413],
        [0.025,		0.0299],
        [0.0125,	0.0215],
        [0,			0],
        [0.0125,	-0.0165],
        [0.025,		-0.0227],
        [0.05,		-0.0301],
        [0.075,		-0.0346],
        [0.1,		-0.0375],
        [0.15,		-0.041],
        [0.2,		-0.0423],
        [0.25,		-0.0422],
        [0.3,		-0.0412],
        [0.4,		-0.038],
        [0.5,		-0.0334],
        [0.6,		-0.0276],
        [0.7,		-0.0214],
        [0.8,		-0.015],
        #[0.9,		-0.0082], - remove colinear mid-node
        [0.95,		-0.0048],
        [1,			-0.0013]]

    def create_section(name, chord, twist, radius):
        points = []
        for n in NACA_2412:
            x, y = offset_rotate_scale(n[0], n[1], twist, chord)
            points.append((x, y))
        path = Q2D_Path.polygon(points)

        plane, pnorm = sketch_reset(orientation='XY', origin=(0, 0, radius))
        sketcher = Q2D_Sketcher(plane)
        sketcher.draw(path)

        surface = sketcher.create_surface_and_clear(name)
        surface.select()
        return surface.selection.Items[0].Faces[0]

    # Section	Chord	Twist	Distance from root
    section_parameters = [
        ['Section-14',	0.585279772,	6.916907674,	1.417854122],
        ['Section-17',	0.525625145,	6.579225954,	1.629666612],
        ['Section-20',	0.475588448,	6.102231593,	1.841479102],
        ['Section-23',	0.433424998,	5.557618775,	2.053291592],
        ['Section-26',	0.397623563,	4.98856372,		2.265104082],
        ['Section-29',	0.366962721,	4.41783243,		2.476916571],
        ['Section-32',	0.340478389,	3.854632702,	2.688729061],
        ['Section-35',	0.317413899,	3.29861338,		2.900541551],
        ['Section-38',	0.297173955,	2.740829294,	3.112354041],
        ['Section-41',	0.279287339,	2.160488016,	3.324166531],
        ['Section-44',	0.263378122,	1.51141408,		3.53597902],
        ['Section-47',	0.249143853,	0.664895367,	3.74779151],
        ['Section-50',	0.236339101,	0.0,			3.959604]]

    faces = []
    for sp in section_parameters:
        face = create_section(sp[0], sp[1], DEG(sp[2]), sp[3])
        faces.append(face)

    selection = Selection.Create(faces)
    options = LoftOptions()
    options.GeometryCommandOptions = GeometryCommandOptions()
    result = Loft.Create(selection, None, options)
    named_object_rename('Solid', 'Foil')

    sp = section_parameters[0]
    front = create_section(sp[0], sp[1], DEG(sp[2]), sp[3])

    sp = section_parameters[len(section_parameters)-1]
    back = create_section(sp[0], sp[1], DEG(sp[2]), sp[3])

    black = (  0.0,   0.0,   0.0,   0.0)
    white = (255.0, 255.0, 255.0, 255.0)
    red   = (255.0, 255.0,   0.0,   0.0)
    green = (255.0,   0.0, 255.0,   0.0)
    blue  = (255.0,   0.0,   0.0, 255.0)

    foil = QSC_Body('Foil')
    foil.sort_faces(front, back)
    foil.paint(white, black, red, blue)
    foil.lock()
    foil.hide()
    named_object_delete('Section-14')
    named_object_delete('Section-50')

    faces = []
    for sp in section_parameters:
        face = create_section(sp[0], sp[1], DEG(sp[2]), sp[3])
        faces.append(face)

    selection = Selection.Create(faces)
    options = LoftOptions()
    options.GeometryCommandOptions = GeometryCommandOptions()
    result = Loft.Create(selection, None, options)
    named_object_rename('Solid', 'Skin')

elif arc_test == 11 or arc_test == 12:
    black = (  0.0,   0.0,   0.0,   0.0)
    white = (255.0, 255.0, 255.0, 255.0)
    red   = (255.0, 255.0,   0.0,   0.0)
    green = (255.0,   0.0, 255.0,   0.0)
    blue  = (255.0,   0.0,   0.0, 255.0)

    pipe_ID =  MM(Parameters.pipe_inner)    #  40
    pipe_OD =  MM(Parameters.pipe_outer)    #  60
    wire_D  =  MM(Parameters.wire_diameter) #   2
    wire_A  = DEG(Parameters.wire_angle)    #  55
    wire_N  = int(Parameters.wire_count)     #  40
    pipe_L  =  MM(Parameters.pipe_length)   # 100

    def draw_ellipse(name, pipe_diameter, offset_angle):
        DirMajor = Direction.Create(math.sin(offset_angle), -math.cos(offset_angle), 0)
        DirMinor = Direction.Create(math.cos(offset_angle),  math.sin(offset_angle), 0)
        xc = math.cos(offset_angle) * pipe_diameter / 2.0
        yc = math.sin(offset_angle) * pipe_diameter / 2.0
        origin = Point.Create(xc, yc, 0)
        plane = Plane.Create(Frame.Create(origin, DirMajor, DirMinor))
        ViewHelper.SetSketchPlane(plane)
        center = Point2D.Create(0, 0)
        dir_major = -DirectionUV.DirU
        dir_minor = -DirectionUV.DirV
        axis_major = wire_D / (2.0 * math.cos(wire_A))
        axis_minor = wire_D /  2.0
        result = SketchEllipse.Create(center, dir_major, dir_minor, axis_major, axis_minor)
        shapes =  Array[ITrimmedCurve]([result.CreatedCurve[0].Shape])
        PlanarBody.Create(plane, shapes, None, name)
        ViewHelper.SetViewMode(InteractionMode.Solid)
        surface = QSC_Surface('Surface')
        #remove_all_datum_planes()
        return surface

    origin = Point.Create(0, 0, 0)
    DirAxis = Direction.Create(0, 0, 1)

    diameter_inner = (pipe_ID + pipe_OD) / 2.0 - wire_D * 1.5
    pitch_inner = math.pi * diameter_inner / math.tan(wire_A)
    revolutions_inner = pipe_L / pitch_inner
    diameter_outer = (pipe_ID + pipe_OD) / 2.0 + wire_D * 1.5
    pitch_outer = math.pi * diameter_outer / math.tan(wire_A)
    revolutions_outer = pipe_L / pitch_outer

    if True:
        plane, normal = sketch_reset()
        plotter = Q2D_Extrusion(plane)

        pipe_center  = Q2D_Point((0.0, 0.0))

        plotter.draw(Q2D_Circle(pipe_center, pipe_OD / 2.0))
        plotter.draw(Q2D_Circle(pipe_center, pipe_ID / 2.0))

        Pipe = plotter.extrude_and_clear('Pipe', normal, pipe_L / 2.0)
        Pipe.paint(black, white, red, green)

    ViewHelper.SetViewMode(InteractionMode.Solid)

    for n in range(0, wire_N):
        name =  'wire_'+str(n)
        angle = DEG(n * 360.0 / wire_N)
        surface = draw_ellipse(name + '_section', diameter_inner, angle)
        named_object_revolve_helix(name + '_section', name, origin, DirAxis, pitch_inner, revolutions_inner, True, True)

    for n in range(0, wire_N):
        name =  'wire_'+str(n)
        angle = DEG(n * 360.0 / wire_N)
        surface = draw_ellipse(name + '_section', diameter_outer, angle)
        named_object_revolve_helix(name + '_section', name, origin, DirAxis, pitch_outer, revolutions_outer, False, True)

    Pipe.lock()
    Pipe.hide()

    Wires_Inner = []
    for n in range(0, wire_N):
        name =  'wire_i_'+str(n)
        angle = DEG(n * 360.0 / wire_N)
        surface = draw_ellipse(name + '_section', diameter_inner, angle)
        surface.select()
        section_face = surface.selection.Items[0].Faces[0]
        named_object_revolve_helix(name + '_section', name, origin, DirAxis, pitch_inner, revolutions_inner, True)
        wire = QSC_Body(name)
        wire.sort_faces(section_face)
        surface.delete()
        wire.paint(black, white, red)
        wire.lock()
        wire.hide()
        Wires_Inner.append(wire)

    Wires_Outer = []
    for n in range(0, wire_N):
        name =  'wire_o_'+str(n)
        angle = DEG(n * 360.0 / wire_N)
        surface = draw_ellipse(name + '_section', diameter_outer, angle)
        surface.select()
        section_face = surface.selection.Items[0].Faces[0]
        named_object_revolve_helix(name + '_section', name, origin, DirAxis, pitch_outer, revolutions_outer, False)
        wire = QSC_Body(name)
        wire.sort_faces(section_face)
        surface.delete()
        wire.paint(black, white, blue)
        wire.lock()
        wire.hide()
        Wires_Outer.append(wire)

    Pipe.show()

    for w in Wires_Inner:
        w.show()
    for w in Wires_Outer:
        w.show()

    if arc_test == 12:
        wire_profile = create_beam_profile_circular(wire_D, 'wire_profile')
        cs = ComponentSelection.Create(wire_profile)

        for w in Wires_Inner:
            w.select()
            result = Beam.ExtractProfile(w.selection)
            cb = result.CreatedBeams
            cb[0].SetName(w.name + '_beam')
            s = Selection.Create(cb[0])
            Beam.SetProfile(s, cs)
        for w in Wires_Outer:
            w.select()
            result = Beam.ExtractProfile(w.selection)
            cb = result.CreatedBeams
            cb[0].SetName(w.name + '_beam')
            s = Selection.Create(cb[0])
            Beam.SetProfile(s, cs)

elif arc_test == 13:
    def xy_sketch_reset(orientation='up', origin=(0,0,0)):
        O = Point.Create(*origin)

        if orientation == 'down':
            B1 = Direction.Create(-1,  0, 0)
            B2 = Direction.Create( 0, -1, 0)
            B3 = Direction.Create( 0,  0, 1)
        else: #if orientation == 'up':
            B1 = Direction.Create( 1, 0, 0)
            B2 = Direction.Create( 0, 1, 0)
            B3 = Direction.Create( 0, 0, 1)

        plane = Plane.Create(Frame.Create(O, B1, B2))
        ViewHelper.SetSketchPlane(plane)
        return plane, B3

    plane, normal = xy_sketch_reset('down', (0, 0.0, -0.008))
    plotter = Q2D_Extrusion(plane)
    ear = Q2D_Path.polygon([(-0.003, -0.01), (0.003, -0.01), (0.003, 0.01), (-0.003, 0.01)])
    plotter.draw(ear)
    plotter.extrude_and_clear('pin lower flange rear ear', normal, 0.004)

    plane, normal = xy_sketch_reset('down', (0, 0.0, -0.004))
    plotter = Q2D_Extrusion(plane)
    center  = Q2D_Point((0.0, 0.0))
    plotter.draw(Q2D_Circle(center, 0.02))
    plotter.extrude_and_clear('pin lower flange rear', normal, 0.004)

    plane, normal = xy_sketch_reset('down', (0, 0.0, 0.008))
    plotter = Q2D_Extrusion(plane)
    center  = Q2D_Point((0.0, 0.0))
    plotter.draw(Q2D_Circle(center, 0.02))
    plotter.extrude_and_clear('pin lower flange front', normal, 0.004)

    plane, normal = xy_sketch_reset('down', (0, 0.0, 0.012))
    plotter = Q2D_Extrusion(plane)
    ear = Q2D_Path.polygon([(-0.003, -0.01), (0.003, -0.01), (0.003, 0.01), (-0.003, 0.01)])
    plotter.draw(ear)
    plotter.extrude_and_clear('pin lower flange front ear', normal, 0.004)

    plane, normal = xy_sketch_reset('down', (0, 0.0, 0.0))
    plotter = Q2D_Extrusion(plane)
    pflat = Q2D_Point((0.0, -0.002))
    pcirc = Q2D_Point((0.0,  0.0))
    l = Q2D_Line(pflat, Q2D_Vector(0.0))
    c = Q2D_Circle(pcirc, 0.015)
    a = Q2D_Arc(None, c, False)
    path = Q2D_Path(l)
    path.append(a, farside=True, transition=0.002)
    path.append(l, farside=True, transition=0.002)
    path.end_point(pflat)
    plotter.draw(path)
    plotter.extrude_and_clear('pin lower', normal, 0.008)

    plane, normal = xy_sketch_reset('up', (0, 0.16, -0.008))
    plotter = Q2D_Extrusion(plane)
    ear = Q2D_Path.polygon([(-0.003, -0.01), (0.003, -0.01), (0.003, 0.01), (-0.003, 0.01)])
    plotter.draw(ear)
    plotter.extrude_and_clear('pin upper flange rear ear', normal, 0.004)

    plane, normal = xy_sketch_reset('up', (0, 0.16, -0.004))
    plotter = Q2D_Extrusion(plane)
    center  = Q2D_Point((0.0, 0.0))
    plotter.draw(Q2D_Circle(center, 0.015))
    plotter.extrude_and_clear('pin upper flange rear', normal, 0.004)

    plane, normal = xy_sketch_reset('up', (0, 0.16, 0.008))
    plotter = Q2D_Extrusion(plane)
    center  = Q2D_Point((0.0, 0.0))
    plotter.draw(Q2D_Circle(center, 0.015))
    plotter.extrude_and_clear('pin upper flange front', normal, 0.004)

    plane, normal = xy_sketch_reset('up', (0, 0.16, 0.012))
    plotter = Q2D_Extrusion(plane)
    ear = Q2D_Path.polygon([(-0.003, -0.01), (0.003, -0.01), (0.003, 0.01), (-0.003, 0.01)])
    plotter.draw(ear)
    plotter.extrude_and_clear('pin upper flange front ear', normal, 0.004)

    plane, normal = xy_sketch_reset('up', (0, 0.16, 0.0))
    plotter = Q2D_Extrusion(plane)
    pflat = Q2D_Point((0.0, -0.002))
    pcirc = Q2D_Point((0.0,  0.0))
    l = Q2D_Line(pflat, Q2D_Vector(0.0))
    c = Q2D_Circle(pcirc, 0.008)
    a = Q2D_Arc(None, c, False)
    path = Q2D_Path(l)
    path.append(a, farside=True, transition=0.002)
    path.append(l, farside=True, transition=0.002)
    path.end_point(pflat)
    plotter.draw(path)
    plotter.extrude_and_clear('pin upper', normal, 0.008)

elif arc_test == 14:
    ZoneList = []

    def shrink_1000():
        names = []
        for Z in ZoneList:
            Z.unlock()
            names.append(Z.name)
        BS = BodySelection.CreateByNames(Array[str](names))
        point = Point.Create(MM(0), MM(0), MM(0))
        frame =  Frame.Create(point, Direction.DirX, Direction.DirY)
        vector = Vector.Create(0.001, 0.001, 1.0)
        preserveHoles = False
        result = Scale.Execute(BS, frame, vector, preserveHoles)

    def make_mmpoly(name, polypoints):
        mmpoints = []
        for xy in polypoints:
            mmpoints.append((MM(xy[0]),MM(xy[1])))
        plane, normal = sketch_reset()
        plotter = Q2D_Sketcher(plane)
        rect = Q2D_Path.polygon(mmpoints)
        plotter.draw(rect)
        plotter.create_surface_and_clear(name)
        S = QSC_Surface(name)
        S.create_named_selection(name)
        ZoneList.append(S)
        return S

    def make_mmrect(name, x_off, y_off, width, height):
        BL = (MM(x_off),MM(y_off))
        TL = (MM(x_off),MM(y_off+height))
        TR = (MM(x_off+width),MM(y_off+height))
        BR = (MM(x_off+width),MM(y_off))
        return make_mmpoly(name, [BL,TL,TR,BR])

    def nearest_quarter(value):
        return int(4.0 * value + 0.5) / 4.0

    def adjust_up(value, layer_id):
        for lid, factor in [('T',0.25),('Q',0.5),('H',1.0),('1',2.0),('2',4.0),('4',8)]:
            if layer_id == lid:
                break
            dv = abs(value / (2 * factor) - int(value / (2 * factor)))
            if dv > 0.49 and dv < 0.51:
                value += 3 * factor
            else:
                value += 2 * factor
        return value

    def adjust_down(value, layer_id):
        for lid, factor in [('T',0.25),('Q',0.5),('H',1.0),('1',2.0),('2',4.0),('4',8)]:
            if layer_id == lid:
                break
            dv = abs(value / (2 * factor) - int(value / (2 * factor)))
            if dv > 0.49 and dv < 0.51:
                value -= 3 * factor
            else:
                value -= 2 * factor
        return value

    def reflector_locations(wavelength, count=1, a1=0, a2=0, an=0):
        x1 = nearest_quarter(21 * wavelength / 8.0 + a1)
        x2 = nearest_quarter(22 * wavelength / 8.0 + a2)
        RL = [(x1,x2)]
        for c in range(1,count):
            x1 = nearest_quarter((10 + 2 * c) * wavelength / 4.0 + an)
            x2 = nearest_quarter((11 + 2 * c) * wavelength / 4.0 + an)
            RL.append((x1,x2))
        ZW = int(wavelength * (1.0 + int(adjust_up(x2, '4') / wavelength)))
        return RL, ZW

    def add_electrode(pts, midpoint, ref_height, width, height):
        x1 = nearest_quarter(midpoint-width/2)
        x2 = nearest_quarter(midpoint+width/2)
        pts.append((x1,ref_height))
        pts.append((x1,ref_height-height))
        pts.append((x2,ref_height-height))
        pts.append((x2,ref_height))
        global script_report
        script_report += "Electrode: {s} - {e}, height {d}\n".format(s=x1, e=x2, d=height)

    def add_reflectors(pts, refls, ref_height, height, layer_id, nudge_symmetric, nudge): # layer_id = 'T','Q','H','1','2','4'
        yo = ref_height + adjust_up(0, layer_id)
        yh = ref_height + adjust_up(height, layer_id)
        if layer_id == '2' or layer_id == '4':
            r1 = refls[ 0][0]
            r2 = refls[-1][1]
            x1 = adjust_down(r1, layer_id)
            x2 = adjust_up(r2, layer_id)
            if nudge_symmetric:
                x1_t = x1 - nudge
                x2_t = x2 + nudge
            else:
                x1_t = x1
                x2_t = x2
            x1_b = x1 + nudge
            x2_b = x2 - nudge
            pts.append((x1_t,yo))
            pts.append((x1_b,yh))
            pts.append((x2_b,yh))
            pts.append((x2_t,yo))
        if layer_id == 'T' or layer_id == 'Q' or layer_id == 'H' or layer_id == '1':
            for r1, r2 in refls:
                x1 = adjust_down(r1, layer_id)
                x2 = adjust_up(r2, layer_id)
                if nudge_symmetric:
                    x1_t = x1 - nudge
                    x2_t = x2 + nudge
                else:
                    x1_t = x1
                    x2_t = x2
                x1_b = x1 + nudge
                x2_b = x2 - nudge
                pts.append((x1_t,yo))
                pts.append((x1_b,yh))
                pts.append((x2_b,yh))
                pts.append((x2_t,yo))
                if layer_id == 'T':
                    global script_report
                    script_report += "Reflector: {a},{b} - {c},{d}, depth {e}\n".format(a=x1_t, b=x1_b, c=x2_b, d=x2_t, e=height)

    def core_path(ref_height, layer_id, nudge_symmetric=True, nudge=0.0):
        yo = ref_height + adjust_up(0, layer_id)
        pts = [(0,yo)]
        if layer_id == 'T':
            DD_a1 =  42.4
            DD_a3 = 122.0
            DDw   =  10.0
            DDh   =   0.5
            add_electrode(pts, DD_a1, ref_height, DDw, DDh)
            add_electrode(pts, DD_a3, ref_height, DDw, DDh)
        add_reflectors(pts, reflectors, ref_height, Reflh, layer_id, nudge_symmetric, nudge)
        pts.append((ZoneW,yo))
        return pts

    YO    = 10.0      # Vertical offset of the gyro
    WaveL = 75.8      # Raleigh wavelength
    Reflh = 6.0       # Depth of reflectors
    ZoneH = Parameters.Core_Depth     # Core simulation depth

    refl_adjust_a1 = Parameters.Reflector_a1    # adjust leading edge of first reflector
    refl_adjust_a2 = Parameters.Reflector_a2    # adjust trailing edge of first reflector
    refl_adjust_an = Parameters.Reflector_an    # adjust edges of all reflectors (except first)
    refl_count_max = Parameters.Reflector_max   # maximum number of reflectors, determines ZoneW
    refl_count     = Parameters.Reflector_count # requested number of reflectors
    refl_nudge     = Parameters.Reflector_nudge # nudge reflector points out at top, in at bottom
    if Parameters.Reflector_sym > 0:            # if zero, don't nudge reflector points out at top, only at bottom
        refl_nudge_sym = True
        refl_incline = math.degrees(math.atan2(2 * refl_nudge, Reflh))
    else:
        refl_nudge_sym = False
        refl_incline = math.degrees(math.atan2(refl_nudge, Reflh))
    _, ZoneW = reflector_locations(WaveL, int(refl_count_max), 0, 0, 0)
    reflectors, _ = reflector_locations(WaveL, int(refl_count), refl_adjust_a1, refl_adjust_a2, refl_adjust_an)

    script_report += "Vertical offset: {a}\n".format(a=YO)
    script_report += "Raleigh Wavelength: {a}\n".format(a=WaveL)
    script_report += "Core simulation depth: {a}\n".format(a=ZoneH)
    script_report += "Core simulation width: {a}\n".format(a=ZoneW)
    script_report += "Reflector adjustments: 1st lead = {a}, 1st trail = {b}, rest = {c}\n".format(a=refl_adjust_a1, b=refl_adjust_a2, c=refl_adjust_an)
    script_report += "Reflector count: {a} / {b}\n".format(a=refl_count, b=refl_count_max)
    if refl_nudge_sym:
        script_report += "Reflector nudge (symmetric): {a} (incline to vertical: {b} degrees)\n".format(a=refl_nudge, b=refl_incline)
    else:
        script_report += "Reflector nudge (asymmetric): {a} (incline to vertical: {b} degrees)\n".format(a=refl_nudge, b=refl_incline)
    script_report += "Absorber size: {a}\n".format(a=Parameters.Absorber)

    Top  = core_path(YO, 'T', refl_nudge_sym, refl_nudge)
    CP_Q = core_path(YO, 'Q', refl_nudge_sym, refl_nudge)
    CP_H = core_path(YO, 'H', refl_nudge_sym, refl_nudge)
    CP_1 = core_path(YO, '1', refl_nudge_sym, refl_nudge)
    CP_2 = core_path(YO, '2')
    CP_4 = core_path(YO, '4')

    Bottom = [(0,YO+ZoneH),(ZoneW,YO+ZoneH)]

    def activate_edges(surface, edge_list):
        surface.select()
        Selection.Create(surface.selection.Items[0].Edges[edge_list]).SetActive()
    def name_edges(surface, edge_list, name):
        surface.select()
        Selection.Create(surface.selection.Items[0].Edges[edge_list]).CreateAGroup(name)

    def make_core_zone_and_name_edges(top_vertices, bottom_vertices, zone_name, zone_prefix, name_top=True):
        NEdge_top = len(top_vertices) - 1
        NEdge_bottom = len(bottom_vertices) - 1
        zone = make_mmpoly(zone_name, top_vertices + bottom_vertices)
        name_edges(zone, 1+NEdge_top+NEdge_bottom, zone_prefix + '-inside')
        if name_top:
            if NEdge_top > 1:
                name_edges(zone, slice(1+NEdge_bottom,1+NEdge_bottom+NEdge_top), zone_prefix + '-top')
            else:
                name_edges(zone, 1+NEdge_bottom, zone_prefix + '-top')
        name_edges(zone, NEdge_bottom, zone_prefix + '-outside')
        if NEdge_bottom > 1:
            name_edges(zone, slice(0,NEdge_bottom), zone_prefix + '-bottom')
        else:
            name_edges(zone, 0, zone_prefix + '-bottom')
        return zone

    Bottom.reverse()
    CZ8 = make_core_zone_and_name_edges(CP_4, Bottom, 'CoreZone8', 'CZ8')
    CZ8.lock()

    CP_4.reverse()
    CZ4 = make_core_zone_and_name_edges(CP_2, CP_4, 'CoreZone4', 'CZ4')
    CZ4.lock()

    CP_2.reverse()
    CZ2 = make_core_zone_and_name_edges(CP_1, CP_2, 'CoreZone2', 'CZ2')
    CZ2.lock()

    CP_1.reverse()
    CZ1 = make_core_zone_and_name_edges(CP_H, CP_1, 'CoreZone1', 'CZ1')
    CZ1.lock()

    CP_H.reverse()
    CZH = make_core_zone_and_name_edges(CP_Q, CP_H, 'CoreZoneH', 'CZH')
    CZH.lock()

    CP_Q.reverse()
    CZQ = make_core_zone_and_name_edges(Top, CP_Q, 'CoreZoneQ', 'CZQ', False)
    name_edges(CZQ, len(Top)+len(CP_Q)-4, 'A1-electrode')
    name_edges(CZQ, len(Top)+len(CP_Q)-8, 'A3-electrode')
    #ep = CZQ.principal_face().Items[0].Edges[0].Shape.EndPoint
    #sp = SketchPoint.Create(ep).CreatedCurves[0]
    #Selection.Create(sp).CreateAGroup('Center')
    CZQ.lock()

    # Absorber Paths
    def absz_path(width):
        YT = YO
        YB = YO + width
        XL = ZoneW
        XR = ZoneW + width
        return [(XR,YT),(XR,YB),(XL,YB)]

    AZ_I = [(ZoneW,YO)]
    absorber_size = Parameters.Absorber
    AZ8R = ZoneW + absorber_size
    AZ8B = YO + ZoneH + absorber_size
    AZ_O = [(AZ8R,YO),(AZ8R,AZ8B),(0,AZ8B),(0,YO+ZoneH),(ZoneW,YO+ZoneH)]

    AZPQ = absz_path( 0.5)
    AZPH = absz_path( 2.0)
    AZP1 = absz_path( 4.0)
    AZP2 = absz_path( 8.0)
    AZP4 = absz_path(16.0)

    AZQ = make_mmpoly('AbsZoneQ', AZ_I + AZPQ)
    name_edges(AZQ, 3, 'AbsZoneQ-inner')
    name_edges(AZQ, slice(0,2), 'AbsZoneQ-bottom')
    AZQ.lock()

    AZPQ.reverse()
    AZH = make_mmpoly('AbsZoneH', AZPH + AZPQ)
    name_edges(AZH, 2, 'AbsZoneH-inner')
    name_edges(AZH, slice(3,5), 'AbsZoneH-bottom')
    name_edges(AZH, slice(0,2), 'AbsZoneH-top')
    AZH.lock()

    AZPH.reverse()
    AZ1 = make_mmpoly('AbsZone1', AZP1 + AZPH)
    name_edges(AZ1, 2, 'AbsZone1-inner')
    name_edges(AZ1, slice(3,5), 'AbsZone1-bottom')
    name_edges(AZ1, slice(0,2), 'AbsZone1-top')
    AZ1.lock()

    AZP1.reverse()
    AZ2 = make_mmpoly('AbsZone2', AZP2 + AZP1)
    name_edges(AZ2, 2, 'AbsZone2-inner')
    name_edges(AZ2, slice(3,5), 'AbsZone2-bottom')
    name_edges(AZ2, slice(0,2), 'AbsZone2-top')
    AZ2.lock()

    AZP2.reverse()
    AZ4 = make_mmpoly('AbsZone4', AZP4 + AZP2)
    name_edges(AZ4, 2, 'AbsZone4-inner')
    name_edges(AZ4, slice(3,5), 'AbsZone4-bottom')
    name_edges(AZ4, slice(0,2), 'AbsZone4-top')
    AZ4.lock()

    AZP4.reverse()
    AZ8 = make_mmpoly('AbsZone8', AZ_O + AZP4)
    name_edges(AZ8, 4, 'AbsZone8B-inner')
    name_edges(AZ8, 5, 'AbsZone8B-bottom')
    name_edges(AZ8, 3, 'AbsZone8B-top')
    name_edges(AZ8, 2, 'AbsZone8S-inner')
    name_edges(AZ8, 6, 'AbsZone8S-outer')
    name_edges(AZ8, slice(0,2), 'AbsZone8S-top')
    AZ8.lock()

    shrink_1000()

    combine_named_selections(['CoreZoneQ','CoreZoneH','CoreZone1','CoreZone2','CoreZone4','CoreZone8'], 'CoreZones')
    combine_named_selections(['AbsZoneQ','AbsZoneH','AbsZone1','AbsZone2','AbsZone4','AbsZone8'], 'AbsZones')
    combine_named_selections(['CoreZones','AbsZones'], 'AllZones')

    move_geometries_to_new_component(['AllZones'], 'Gyro')

    s = named_object_select('Gyro')
    ComponentShareTopology.SetComponentShareTopology(s, ShareTopologyType.Share)

elif arc_test == 15:
    axis = Line.Create(Point.Origin, Direction.DirY)

    sector_angle = 60.0

    ZoneList = []

    def shrink_1000():
        names = []
        for Z in ZoneList:
            Z.unlock()
            names.append(Z.name)
        BS = BodySelection.CreateByNames(Array[str](names))
        point = Point.Create(MM(0), MM(0), MM(0))
        frame =  Frame.Create(point, Direction.DirX, Direction.DirY)
        vector = Vector.Create(0.001, 0.001, 0.001)
        preserveHoles = False
        result = Scale.Execute(BS, frame, vector, preserveHoles)

    def make_mmpoly(name, polypoints, offset=0.0, sweep=None):
        mmpoints = []
        for xy in polypoints:
            mmpoints.append((MM(xy[1]),MM(xy[0]))) # swap x & y
        if offset == 0.0:
            e_x = (1.0, 0.0, 0.0)
            e_y = (0.0, 1.0, 0.0)
            e_z = (0.0, 0.0, 1.0)
        else:
            e_x = (math.cos(math.radians(offset)), math.sin(math.radians(offset)), 0.0)
            e_y = (-math.sin(math.radians(offset)), math.cos(math.radians(offset)), 0.0)
            e_z = (0.0, 0.0, 1.0)
        plotter = Q2D_Helix(0.0, 0.0, (0.0, 0.0, 0.0), e_z, e_x, e_y, True, False)
        rect = Q2D_Path.polygon(mmpoints)
        plotter.draw(rect)
        if sweep is None:
            sweep = sector_angle
        B = plotter.revolve_and_clear(name, sweep / 360.0)
        B.create_named_selection(name)
        ZoneList.append(B)
        return B

    def make_mmrect(name, x_off, y_off, width, height, offset=0.0, sweep=None):
        BL = (x_off,y_off)
        TL = (x_off,y_off+height)
        TR = (x_off+width,y_off+height)
        BR = (x_off+width,y_off)
        return make_mmpoly(name, [BL,TL,TR,BR], offset, sweep)

    def nearest_quarter(value):
        return int(4.0 * value + 0.5) / 4.0

    def adjust_up(value, layer_id):
        for lid, factor in [('T',0.25),('Q',0.5),('H',1.0),('1',2.0),('2',4.0),('4',8)]:
            if layer_id == lid:
                break
            dv = abs(value / (2 * factor) - int(value / (2 * factor)))
            if dv > 0.49 and dv < 0.51:
                value += 3 * factor
            else:
                value += 2 * factor
        return value

    def adjust_down(value, layer_id):
        for lid, factor in [('T',0.25),('Q',0.5),('H',1.0),('1',2.0),('2',4.0),('4',8)]:
            if layer_id == lid:
                break
            dv = abs(value / (2 * factor) - int(value / (2 * factor)))
            if dv > 0.49 and dv < 0.51:
                value -= 3 * factor
            else:
                value -= 2 * factor
        return value

    def reflector_locations(wavelength, count=1):
        x1 = nearest_quarter(21 * wavelength / 8.0)
        x2 = nearest_quarter(22 * wavelength / 8.0)
        RL = [(x1,x2)]
        for c in range(1,count):
            x1 = nearest_quarter((10 + 2 * c) * wavelength / 4.0)
            x2 = nearest_quarter((11 + 2 * c) * wavelength / 4.0)
            RL.append((x1,x2))
        ZW = int(wavelength * (1.0 + int(adjust_up(x2, '4') / wavelength)))
        return RL, ZW

    def add_electrode(midpoint, ref_height, width, height, offset, sweep, name):
        x1 = nearest_quarter(midpoint-width/2)
        x2 = nearest_quarter(midpoint+width/2)
        zone = make_mmrect('Electrode-' + name, x1, ref_height-height, x2 - x1, height, offset, sweep)
        name_edges(zone, 1, name + '-bottom')
        name_edges(zone, 3, name + '-top')
        zone.lock()
        return zone

    def add_electrodes(ref_height):
        DD_a1 =  42.4
        DD_a3 = 122.0
        DDw   =  10.0
        DDh   =   0.5
        sweep = sector_angle / 6.0
        offset_1 = sector_angle / 6.0
        offset_2 = sector_angle / 1.5
        E_A1_1 = add_electrode(DD_a1, ref_height, DDw, DDh, offset_1, sweep, 'A1-1')
        E_A1_2 = add_electrode(DD_a1, ref_height, DDw, DDh, offset_2, sweep, 'A1-2')
        E_A3_1 = add_electrode(DD_a3, ref_height, DDw, DDh, offset_1, sweep, 'A3-1')
        E_A3_2 = add_electrode(DD_a3, ref_height, DDw, DDh, offset_2, sweep, 'A3-2')
        return E_A1_1, E_A1_2, E_A3_1, E_A3_2

    def add_reflectors(pts, refls, ref_height, height, layer_id): # layer_id = 'T','Q','H','1','2','4'
        yo = ref_height + adjust_up(0, layer_id)
        yh = ref_height + adjust_up(height, layer_id)
        if layer_id == '2' or layer_id == '4':
            r1 = refls[ 0][0]
            r2 = refls[-1][1]
            x1 = adjust_down(r1, layer_id)
            x2 = adjust_up(r2, layer_id)
            pts.append((x1,yo))
            pts.append((x1,yh))
            pts.append((x2,yh))
            pts.append((x2,yo))
        if layer_id == 'T' or layer_id == 'Q' or layer_id == 'H' or layer_id == '1':
            for r1, r2 in refls:
                x1 = adjust_down(r1, layer_id)
                x2 = adjust_up(r2, layer_id)
                pts.append((x1,yo))
                pts.append((x1,yh))
                pts.append((x2,yh))
                pts.append((x2,yo))

    def core_path(ref_height, layer_id):
        yo = ref_height + adjust_up(0, layer_id)
        pts = [(0,yo)]
        add_reflectors(pts, reflectors, ref_height, Reflh, layer_id)
        pts.append((ZoneW,yo))
        return pts

    YO    = 10.0      # Vertical offset of the gyro
    WaveL = 75.8      # Raleigh wavelength
    Reflh = 6.0       # Depth of reflectors
    ZoneH = 192.0     # Core simulation depth

    reflectors, ZoneW = reflector_locations(WaveL, 4)

    Top  = core_path(YO, 'T')
    CP_Q = core_path(YO, 'Q')
    CP_H = core_path(YO, 'H')
    CP_1 = core_path(YO, '1')
    CP_2 = core_path(YO, '2')
    CP_4 = core_path(YO, '4')

    Bottom = [(0,YO+ZoneH),(ZoneW,YO+ZoneH)]

    def activate_edges(body, edge_list):
        body.select()
        Selection.Create(body.selection.Items[0].Edges[edge_list]).SetActive()
    def name_edges(body, edge_list, name):
        Selection.Create(body.sides[edge_list]).CreateAGroup(name)
    def name_front_back_axis(body, name):
        if body.axis is not None:
            Selection.Create(body.axis).CreateAGroup(name + '-axis')
        Selection.Create(body.front).CreateAGroup(name + '-front')
        Selection.Create(body.back).CreateAGroup(name + '-back')

    def make_core_zone_and_name_edges(top_vertices, bottom_vertices, zone_name, zone_prefix, name_top=True):
        NEdge_top = len(top_vertices) - 1
        NEdge_bottom = len(bottom_vertices) - 1
        zone = make_mmpoly(zone_name, top_vertices + bottom_vertices)
        name_front_back_axis(zone, zone_prefix)
        if name_top:
            if NEdge_top > 1:
                name_edges(zone, slice(0,0+NEdge_top), zone_prefix + '-top')
            else:
                name_edges(zone, 0, zone_prefix + '-top')
        name_edges(zone, 0+NEdge_top, zone_prefix + '-outside')
        if NEdge_bottom > 1:
            name_edges(zone, slice(1+NEdge_top,1+NEdge_top+NEdge_bottom), zone_prefix + '-bottom')
        else:
            name_edges(zone, 1+NEdge_top, zone_prefix + '-bottom')
        return zone

    Bottom.reverse()
    CZ8 = make_core_zone_and_name_edges(CP_4, Bottom, 'CoreZone8', 'CZ8')
    CZ8.lock()

    CP_4.reverse()
    CZ4 = make_core_zone_and_name_edges(CP_2, CP_4, 'CoreZone4', 'CZ4')
    CZ4.lock()

    CP_2.reverse()
    CZ2 = make_core_zone_and_name_edges(CP_1, CP_2, 'CoreZone2', 'CZ2')
    CZ2.lock()

    CP_1.reverse()
    CZ1 = make_core_zone_and_name_edges(CP_H, CP_1, 'CoreZone1', 'CZ1')
    CZ1.lock()

    CP_H.reverse()
    CZH = make_core_zone_and_name_edges(CP_Q, CP_H, 'CoreZoneH', 'CZH')
    CZH.lock()

    CP_Q.reverse()
    CZQ = make_core_zone_and_name_edges(Top, CP_Q, 'CoreZoneQ', 'CZQ')
    CZQ.lock()

    E_A1_1, E_A1_2, E_A3_1, E_A3_2 = add_electrodes(YO)

    # Absorber Paths
    def absz_path(width):
        YT = YO
        YB = YO + width
        XL = ZoneW
        XR = ZoneW + width
        return [(XR,YT),(XR,YB),(XL,YB)]

    AZ_I = [(ZoneW,YO)]
    AZ8R = ZoneW + 32.0
    AZ8B = YO + ZoneH + 32.0
    AZ_O = [(AZ8R,YO),(AZ8R,AZ8B),(0,AZ8B),(0,YO+ZoneH),(ZoneW,YO+ZoneH)]

    AZPQ = absz_path( 0.5)
    AZPH = absz_path( 2.0)
    AZP1 = absz_path( 4.0)
    AZP2 = absz_path( 8.0)
    AZP4 = absz_path(16.0)

    AZQ = make_mmpoly('AbsZoneQ', AZ_I + AZPQ)
    name_front_back_axis(AZQ, 'AbsZoneQ')
    name_edges(AZQ, 3, 'AbsZoneQ-inner')
    name_edges(AZQ, slice(1,3), 'AbsZoneQ-bottom')
    AZQ.lock()

    AZPQ.reverse()
    AZH = make_mmpoly('AbsZoneH', AZPH + AZPQ)
    name_front_back_axis(AZH, 'AbsZoneH')
    name_edges(AZH, slice(0,2), 'AbsZoneH-bottom')
    name_edges(AZH, 2, 'AbsZoneH-inner')
    name_edges(AZH, slice(3,5), 'AbsZoneH-top')
    AZH.lock()

    AZPH.reverse()
    AZ1 = make_mmpoly('AbsZone1', AZP1 + AZPH)
    name_front_back_axis(AZ1, 'AbsZone1')
    name_edges(AZ1, slice(0,2), 'AbsZone1-bottom')
    name_edges(AZ1, 2, 'AbsZone1-inner')
    name_edges(AZ1, slice(3,5), 'AbsZone1-top')
    AZ1.lock()

    AZP1.reverse()
    AZ2 = make_mmpoly('AbsZone2', AZP2 + AZP1)
    name_front_back_axis(AZ2, 'AbsZone2')
    name_edges(AZ2, slice(0,2), 'AbsZone2-bottom')
    name_edges(AZ2, 2, 'AbsZone2-inner')
    name_edges(AZ2, slice(3,5), 'AbsZone2-top')
    AZ2.lock()

    AZP2.reverse()
    AZ4 = make_mmpoly('AbsZone4', AZP4 + AZP2)
    name_front_back_axis(AZ4, 'AbsZone4')
    name_edges(AZ4, slice(0,2), 'AbsZone4-bottom')
    name_edges(AZ4, 2, 'AbsZone4-inner')
    name_edges(AZ4, slice(3,5), 'AbsZone4-top')
    AZ4.lock()

    AZP4.reverse()
    AZ8 = make_mmpoly('AbsZone8', AZ_O + AZP4)
    name_front_back_axis(AZ8, 'AbsZone8')
    name_edges(AZ8, 1, 'AbsZone8B-bottom')
    name_edges(AZ8, 2, 'AbsZone8B-top')
    name_edges(AZ8, 3, 'AbsZone8S-inner')
    name_edges(AZ8, 0, 'AbsZone8S-outer')
    name_edges(AZ8, slice(4,6), 'AbsZone8S-top')
    AZ8.lock()

    shrink_1000()

elif arc_test == 16:
    # Buckling collapse study for the carcass layer of flexible pipes using a strain energy equivalence method
    # Ocean Engineering, 111, 209-217, 2016
    # https://doi.org/10.1016/j.oceaneng.2015.10.057
    # Minggang Tang and Qingzhen Lu and Jun Yan and Qianjin Yue

    pitch = 0.01488 # expected pitch

    ID = 0.153   # carcass internal diameter
    rt = 0.0009  # ribbon thickness
    L1 = 0.0262  # end-to-end length
    L2 = 0.01036 # length upper-outer face
    L3 = 0.00896 # length lower-inner face
    L4 = 0.00590 # length lower-outer face
    L5 = 0.00180 # length mid-section
    L6 = 0.0001  # length upper-inner face; must be > 0
    L7 = 0.00177 # containment separation
    R1 = 0.00418 # insertion inner radius

    fr = Parameters.FilletRadius # 1mm makes L5=1.77mm
    cl = 0.0001      # specify an arbitrary clearance
    ro = rt + L7 / 2 # outer radius of end-loops

    def midsep(c1, r1, c2, r2):
        x1, y1 = c1
        x2, y2 = c2
        cc_sep = ((x2 - x1)**2 + (y2 - y1)**2)**0.5
        cc_theta = math.atan2(y2 - y1, x1 - x2)
        dtheta = math.asin((r1 + r2) / cc_sep)
        theta = cc_theta + dtheta
        dx = r1 * math.sin(theta)
        dy = r1 * math.cos(theta)
        tangent = cc_sep * math.cos(dtheta)
        return (x1 - dx, y1 - dy), theta, tangent

    def tang_carcass_profile(offset=0.0):
        ox = offset

        p_r0 = Q2D_Point((ox + L1 - ro, 0.0))
        p_r1 = Q2D_Point((ox + L1 - ro, rt))
        p_r2 = Q2D_Point((ox + L1 - ro, ro))
        p_r3 = Q2D_Point((ox + L1 - ro - L4, L7 + rt))
        p_r4 = Q2D_Point((ox + L1 - ro - L4, L7 + rt * 2))

        p_l0 = Q2D_Point((ox + ro, rt + cl + 0.0))
        p_l1 = Q2D_Point((ox + ro, rt + cl + rt))
        p_l2 = Q2D_Point((ox + ro, rt + cl + ro))
        p_l3 = Q2D_Point((ox + ro, rt + cl + L7 + rt))
        p_l4 = Q2D_Point((ox + ro, rt + cl + L7 + rt * 2))

        p_f0 = Q2D_Point((ox + ro + L6, rt + cl + rt + fr))
        p_f1 = Q2D_Point((ox + ro + L2, rt + cl + L7 + rt - fr))
        p_f2 = Q2D_Point((ox + L1 - ro - L3, rt + fr))

        ta = math.radians(28) # somewhat arbitrary transition angle for final curve
        ts = rt + fr + R1     # centre-centre separation
        p_ta = Q2D_Point((ox + ro + L6 + ts * math.sin(ta), rt + cl + rt + fr - ts * math.cos(ta)))

        p1, theta1, l1 = midsep((ox + L1 - ro - L3, rt + fr), fr,      (ox + ro + L2, rt + cl + L7 + rt - fr), fr + rt)
        p2, theta2, l2 = midsep((ox + L1 - ro - L3, rt + fr), fr + rt, (ox + ro + L2, rt + cl + L7 + rt - fr), fr)
        p_m1 = Q2D_Point(p1)
        p_m2 = Q2D_Point(p2)
        theta = (theta1 + theta2) / 2
        print("C5 estimate: {a:.2f}mm and {b:.2f}mm (official = {o:.2f}mm)".format(a=l1*1000, b=l2*1000, o=L5*1000))

        c_lli = Q2D_Circle(p_l2, ro - rt)
        c_llo = Q2D_Circle(p_l2, ro)
        c_rli = Q2D_Circle(p_r2, ro - rt)
        c_rlo = Q2D_Circle(p_r2, ro)
        c_f0i = Q2D_Circle(p_f0, fr)
        c_f0o = Q2D_Circle(p_f0, fr + rt)
        c_tai = Q2D_Circle(p_ta, R1)
        c_tao = Q2D_Circle(p_ta, R1 + rt)

        l_r4d = Q2D_Line(p_r4, Q2D_Vector(DEG(270)))
        l_r3r = Q2D_Line(p_r3, Q2D_Vector(DEG(  0)))
        l_r1l = Q2D_Line(p_r1, Q2D_Vector(DEG(180)))
        l_m1u = Q2D_Line(p_m1, Q2D_Vector(math.pi - theta))
        l_l4l = Q2D_Line(p_l4, Q2D_Vector(DEG(180)))
        l_l0r = Q2D_Line(p_l0, Q2D_Vector(DEG(  0)))
        l_tau = Q2D_Line(p_ta, Q2D_Vector(math.pi / 2 - ta))
        l_l1l = Q2D_Line(p_l1, Q2D_Vector(DEG(180)))
        l_l3r = Q2D_Line(p_l3, Q2D_Vector(DEG(  0)))
        l_m2d = Q2D_Line(p_m2, Q2D_Vector(2 * math.pi - theta))
        l_r0r = Q2D_Line(p_r0, Q2D_Vector(DEG(  0)))
        l_r4l = Q2D_Line(p_r4, Q2D_Vector(DEG(180)))

        path = Q2D_Path(l_r4d)
        path.append(l_r3r)
        path.append(Q2D_Arc(None, c_rli, True))
        path.append(l_r1l)
        path.append(l_m1u, transition=fr)
        path.append(l_l4l, transition=(fr+rt))
        path.append(Q2D_Arc(None, c_llo, False))
        path.append(l_l0r)
        path.append(Q2D_Arc(None, c_tai, True), transition=(fr+rt), co_sense=False)
        path.append(l_tau)
        path.append(Q2D_Arc(None, c_tao, False))
        path.append(l_l1l, transition=fr, co_sense=False)
        path.append(Q2D_Arc(None, c_lli, True))
        path.append(l_l3r)
        path.append(l_m2d, transition=fr)
        path.append(l_r0r, transition=(fr+rt))
        path.append(Q2D_Arc(None, c_rlo, False))
        path.append(l_r4l)
        path.end_point(p_r4)

        return path

    black = (  0.0,   0.0,   0.0,   0.0)
    white = (255.0, 255.0, 255.0, 255.0)
    red   = (255.0, 255.0,   0.0,   0.0)
    green = (255.0,   0.0, 255.0,   0.0)
    blue  = (255.0,   0.0,   0.0, 255.0)

    path = tang_carcass_profile()
    revs = 1.0

    plotter = Q2D_Helix(ID / 2, pitch, (0,0,0), (0,0,1), (0,1,0), (1,0,0))
    plotter.draw(path)
    Carcass = plotter.revolve_and_clear('Carcass', revs)
    Carcass.paint(black, white, blue, red)
    Carcass.lock()

if Q2D_SpaceClaim:
    # Finally, switch to solid-modelling mode
    remove_all_datum_planes()
    ViewHelper.SetViewMode(InteractionMode.Solid)
else:
    Q2D_Plotter.show()
