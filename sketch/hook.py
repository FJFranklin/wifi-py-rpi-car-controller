# -*- indent-tabs-mode: t; tab-width: 4 -*-

# 0:  arc-arc test
# 1:  arc-line test
# 2:  hook
# 3:  SpaceClaim: 3D-NURBS
# 4:  conduit
# 5:  SpaceClaim: ski
# 6:  SpaceClaim: cube
# 7:  SpaceClaim: foil
# 8: !SpaceClaim: mesh
arc_test = 8

print_path_info = False
print_plot_info = False
plot_construction_arcs = False

# ==== Preliminary setup: Are we using SpaceClaim? ==== #

import math

Q2D_Design_Tolerance = 1E-15 # tolerance for numerical errors

if 'DEG' in dir():
	Q2D_SpaceClaim = True

	# SpaceClaim uses IronPython, which integrates with Microsoft's .Net framework
	from System import Array, Double
	from SpaceClaim.Api.V16.Geometry import ControlPoint, Knot, NurbsData, NurbsSurface

	# A parameter used solely for convenience; changing GeometrySequence re-runs the script.
	GeometrySequence = Parameters.GeometrySequence

else:
	Q2D_SpaceClaim = False
	# Okay, we're not using SpaceClaim; let's plot the paths with MatPlotLib instead

	import matplotlib.pyplot as plt
	import matplotlib.patches as mpatches

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

	def principal_face(self):
		if self.select():
			return Selection.Create(self.selection.Items[0].Faces[0])
		return None

	def paint(self, rgba):
		if self.select():
			ColorHelper.SetColor(self.selection, Color.FromArgb(*rgba))

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

	def match_curves(self, curves):
		self.front = None
		self.back = None
		self.sides = []

		if self.select():
			b = self.selection.Items[0]

			for f in b.Faces:
				match_all = True
				match_none = True

				for e in f.Edges:
					match = False
					for c in curves:
						curve = c[0].Shape.Geometry
						if e.Shape.Geometry.IsCoincident(curve):
							match = True
							break
					if match:
						match_none = False
					else:
						match_all = False

				if match_all:
					self.back = f
				elif match_none:
					self.front = f
				else:
					self.sides.append(f)

			order = []
			for c in curves:
				curve = c[0].Shape.Geometry
				
				for f in self.sides:
					matched = False
					for e in f.Edges:
						if e.Shape.Geometry.IsCoincident(curve):
							matched = True
							break
					if matched:
						order.append(f)
						break

			self.sides = order

	@staticmethod
	def faces_connected(face1, face2):
		connected = False
		for e1 in face1.Edges:
			for e2 in face2.Edges:
				if e1.MidPoint().Point.Equals(e2.MidPoint().Point):
					connected = True
		return connected

	@staticmethod
	def faces_coincident(face1, face2):
		return face1.Shape.Geometry.IsCoincident(face2.Shape.Geometry)

	def _sort_faces(self, ref_front, ref_back):
		self.front = None
		self.back = None
		self.sides = []

		for f in self.selection.Items[0].Faces:
			if QSC_Body.faces_coincident(f, ref_front):
				#print('front matched')
				self.front = f
				continue
			if QSC_Body.faces_coincident(f, ref_back):
				#print('back matched')
				self.back = f
				continue
			#print('side assigned')
			self.sides.append(f)

		if self.front is not None and self.back is None:
			#print('searching for the back')
			for s in self.sides:
				if QSC_Body.faces_connected(s, ref_front):
					#print('an actual side')
					continue
				#print('the back?')
				self.back = s
				self.sides.remove(s)
				break

		if self.front is None and self.back is not None:
			#print('searching for the front')
			for s in self.sides:
				if QSC_Body.faces_connected(s, ref_back):
					#print('an actual side')
					continue
				#print('the front?')
				self.front = s
				self.sides.remove(s)
				break

	def _reorganise_sides(self, ref_body):
		org_sides = []
		for r in ref_body.sides:
			for s in self.sides:
				if QSC_Body.faces_connected(s, r):
					#print('matched with ref-body, count={d}'.format(d=count))
					org_sides.append(s)
					break
		self.sides = org_sides

	def cross_sect_and_match(self, surface, split_name, ref_body=None):
		split_body = None

		if self.select():
			SplitBody.Execute(self.selection, surface.principal_face(), False)

			old_front = self.front
			old_back  = self.back

			self._sort_faces(old_front, old_back)

			if ref_body is not None and self.front is not None and self.back is not None:
				if QSC_Body.faces_coincident(self.front, ref_body.back) or QSC_Body.faces_coincident(self.back, ref_body.front):
					#print('Matching original to reference:')
					self._reorganise_sides(ref_body)

			new_body = QSC_Body(self.name + '1')
			if new_body.select():
				new_body._sort_faces(old_front, old_back)

				split_body = new_body
				split_body.rename(split_name)

				if ref_body is not None and split_body.front is not None and split_body.back is not None:
					if QSC_Body.faces_coincident(split_body.front, ref_body.back) or QSC_Body.faces_coincident(split_body.back, ref_body.front):
						#print('Matching off-cut to reference:')
						split_body._reorganise_sides(ref_body)

						if self.front is not None and self.back is not None:
							#print('Matching original to off-cut:')
							self._reorganise_sides(split_body)
					else:
						#print('Matching off-cut to original:')
						split_body._reorganise_sides(self)

		return split_body

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
		body = Selection.Create(result.CreatedBody)
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
		RevolveHelixFaces.Execute(face, axis, direction, revolutions * pitch, pitch, taperAngle, righthanded, bothSides, options)
		named_object_rename('Solid', body_name)

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
		
class Q2D_Plotter(object):

	def __init__(self, x_range, y_range):
		xsize = 1500
		ysize = 1500
		dpi_osx = 192 # Something very illogical here.
		self._fig = plt.figure(figsize=(xsize / dpi_osx, ysize / dpi_osx), dpi=(dpi_osx/2))

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
		patch = mpatches.Ellipse(circle.center.start, x_axis, y_axis, edgecolor=ec, linestyle=ls, facecolor=None, fill=False, linewidth=1)
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
		patch = mpatches.Arc(arc.circle.center.start, x_axis, y_axis, theta1=t1, theta2=t2, edgecolor=Q2D_path_color, facecolor=None, fill=False)
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

	def create_surface_and_clear(self, name):
		self._create_surface(name)
		self._clear_curves()
		return QSC_Surface(name)

	def _match_curves(self, body_name):
		self.body.rename(body_name)
		self.body.match_curves(self.curves)

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
			h_adjust = math.atan(h_pitch / (2.0 * math.pi * helix_radius))
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
		h_origin = Point.Create(origin[0] + h_radius * e_radial[0], origin[1] + h_radius * e_radial[1], origin[2] + h_radius * e_radial[2])
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
            
	def split(self, angle, new_body_name, ref_body=None):
		plane = self.offset_plane(angle)
		ViewHelper.SetSketchPlane(plane)
		plotter = Q2D_Sketcher(plane)

		occlusion = Q2D_Path.polygon([(-3.0 * self.pitch, 0.0), (3.0 * self.pitch, 0.0), (3.0 * self.pitch, 2.0 * self.radius), (-3.0 * self.pitch, 2.0 * self.radius)])
		plotter.draw(occlusion)
		surface = plotter.create_surface_and_clear('Helix-Split-Plane')

		split_body = self.body.cross_sect_and_match(surface, new_body_name, ref_body)
		surface.delete()

		return split_body

	def revolve_and_clear(self, name, revolutions, cut=False, match=True, clear=True):
		self.name = name
		self._create_surface(name)
		named_object_revolve_helix(name, name, self.origin, self.axis, self.pitch, revolutions, self.righthanded, cut)
		if match:
			self._match_curves(name)
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
		h_pitch  = 0.02

		black = (  0.0,   0.0,   0.0,   0.0)
		white = (255.0, 255.0, 255.0, 255.0)
		red   = (255.0, 255.0,   0.0,   0.0)
		green = (255.0,   0.0, 255.0,   0.0)
		blue  = (255.0,   0.0,   0.0, 255.0)

		plotter = Q2D_Helix(h_radius, h_pitch, (0,0,-2.5*h_pitch), (0,0,1), (0,1,0), (1,0,0))
		make_conduit_profile(plotter)
		Conduit_Left = plotter.revolve_and_clear('Conduit-Left', 2.0)

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

		Conduit_Middle.rename('Conduit-Middle-Left')
		Conduit_Middle.lock()
		Conduit_Middle.hide()

		Selection.Create(Conduit_Middle_Helix.body.front).CreateAGroup('Conduit-Middle-Left-Front')
		Selection.Create(Conduit_Middle_Helix.body.back).CreateAGroup('Conduit-Middle-Left-Back')

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
		SplitBody.Execute(surface.selection, splitter.principal_face(), False)

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

elif arc_test == 8: # let's draw a hook

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

	Q2D_path_color = 'red'
	for i in range(-3,4,6):
		inset = 0.001 * i
		plotter.draw(path.offset_path(inset))

if Q2D_SpaceClaim:
	# Finally, switch to solid-modelling mode
	ViewHelper.SetViewMode(InteractionMode.Solid)
else:
	plt.show()
