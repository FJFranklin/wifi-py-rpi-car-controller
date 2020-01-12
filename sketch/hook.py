# -*- indent-tabs-mode: t; tab-width: 4 -*-

arc_test = 2 # 0: arc-arc test; 1: arc-line test; 2: hook

Q2D_Design_Tolerance = 1E-15 # tolerance for numerical errors

if 'DEG' in dir():
	Q2D_SpaceClaim = True
else:
	Q2D_SpaceClaim = False
	# Okay, we're not using SpaceClaim; let's plot the paths with MatPlotLib instead

	import math

	import matplotlib.pyplot as plt
	import matplotlib.patches as mpatches

	def DEG(a):
		return math.radians(a)

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

	def x(self):
		return self.start[0]

	def y(self):
		return self.start[1]

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

class Q2D_Path(object):

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
		if pi is not None:
			if radius > 0:
				p1 = l1.project(pi)
				p2 = l2.project(pi)

				clockwise = d2.cross(d1) > 0
				self.__append(Q2D_Arc(p1, Q2D_Circle(pi, radius), clockwise))

				self.__append(Q2D_Line(p2, d2))
			else:
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
			print("tangent: error =", cp.length - circle.radius)
			point = midpoint
			tangent = True # check sense
		elif cp.length > circle.radius:
			print("line does not intersect circle; missed by", cp.length - circle.radius)
		else: # cp.length < circle.radius:
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
			offset = -transition
		else:
			sense = co_sense
			offset = transition

		point, cross, tangent = Q2D_Path.__intersect_line(line, arc.circle, sense)
		if transition is None:
			if point is None:
				print('Unable to add line without transition')
			else:
				print('Adding line without transition')
				self.__append(Q2D_Line(point, line.direction))
		else:
			if point is not None:
				print('point = (', point.x(), point.y(), '); cross =', cross, 'tangent =', tangent)

			if tangent:
				if (cross > 0.0 and not arc.clockwise) or (cross < 0.0 and arc.clockwise):
					if not co_sense:
						print('Co-sense transition should be used here')
				else:
					if co_sense:
						print('Contra-sense transition should be used here')

				if co_sense:
					print('Adding (tangent) line (without transition)')
					self.__append(Q2D_Line(line.project(point), line.direction))
				else:
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
						print('Co-sense transition should be used here')
				else:
					if co_sense:
						print('Contra-sense transition should be used here')

				if co_sense:
					if transition > arc.circle.radius:
						o = Q2D_Circle(arc.circle.center, transition - arc.circle.radius)
						l = line.parallel(-offset)
						p, c, t = Q2D_Path.__intersect_line(l, o, not farside)
						if p is not None:
							print('Adding line (with co-sense transition)')
							#print 'point = (', p.x(), p.y(), '); cross =', c, 'tangent =', t
							self.__append(Q2D_Arc(arc.circle.project(p, True), Q2D_Circle(p, transition), clockwise=arc.clockwise))
							self.__append(Q2D_Line(line.project(p), line.direction))
						else:
							print('Unable to add line with specified (co-sense) transition; try increasing the transition radius')
					else:
						print('Unable to add line with specified (co-sense) transition; require transition radius > arc radius')
				else:
					o = Q2D_Circle(arc.circle.center, arc.circle.radius + transition)
					if arc.clockwise:
						l = line.parallel( transition)
					else:
						l = line.parallel( transition)
					p, c, t = Q2D_Path.__intersect_line(l, o, not farside)
					if p is not None:
						print('Adding line (with counter-sense transition)')
						#print 'point = (', p.x(), p.y(), '); cross =', c, 'tangent =', t
						self.__append(Q2D_Arc(arc.circle.project(p), Q2D_Circle(p, transition), clockwise=(not arc.clockwise)))
						self.__append(Q2D_Line(line.project(p), line.direction))
					else:
						print('Unable to add line with specified (counter-sense) transition')
			else: # line intersects circle
				if co_sense:
					if transition < arc.circle.radius:
						o = Q2D_Circle(arc.circle.center, arc.circle.radius - transition)
						l = line.parallel(-offset)
						p, c, t = Q2D_Path.__intersect_line(l, o, not farside)
						if p is not None:
							print('Adding line (with co-sense transition)')
							#print 'point = (', p.x(), p.y(), '); cross =', c, 'tangent =', t
							self.__append(Q2D_Arc(arc.circle.project(p), Q2D_Circle(p, transition), clockwise=arc.clockwise))
							self.__append(Q2D_Line(line.project(p), line.direction))
						else:
							print('Unable to add line with specified (co-sense) transition; try increasing the transition radius')
					else:
						print('Unable to add line with specified (co-sense) transition; require transition radius > arc radius')
				else:
					o = Q2D_Circle(arc.circle.center, arc.circle.radius + transition)
					l = line.parallel(offset)
					p, c, t = Q2D_Path.__intersect_line(l, o, not farside)
					if p is not None:
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
			offset = -transition
		else:
			sense = co_sense
			offset = transition

		point, cross, tangent = Q2D_Path.__intersect_line(line, arc.circle, sense)
		if transition is None:
			if point is None:
				print('Unable to add arc without transition')
			else:
				print('Adding arc without transition')
				self.__append(Q2D_Arc(point, arc.circle))
		else:
			if point is not None:
				print('point = (', point.x(), point.y(), '); cross =', cross, 'tangent =', tangent)

			if tangent:
				if (cross > 0.0 and not arc.clockwise) or (cross < 0.0 and arc.clockwise):
					if not co_sense:
						print('Co-sense transition should be used here')
				else:
					if co_sense:
						print('Contra-sense transition should be used here')

				if co_sense:
					print('Adding (tangent) arc (without transition)')
					self.__append(Q2D_Arc(point, arc.circle, clockwise=arc.clockwise))
				else:
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
						print('Co-sense transition should be used here')
				else:
					if co_sense:
						print('Contra-sense transition should be used here')

				if co_sense:
					if transition > arc.circle.radius:
						o = Q2D_Circle(arc.circle.center, transition - arc.circle.radius)
						l = line.parallel(offset)
						p, c, t = Q2D_Path.__intersect_line(l, o, farside)
						if p is not None:
							print('Adding (co-sense) arc (with transition)')
							#print 'point = (', p.x(), p.y(), '); cross =', c, 'tangent =', t
							self.__append(Q2D_Arc(line.project(p), Q2D_Circle(p, transition), clockwise=arc.clockwise))
							self.__append(Q2D_Arc(arc.circle.project(p, True), arc.circle, clockwise=arc.clockwise))
						else:
							print('Unable to add (co-sense) arc with specified transition; try increasing the transition radius')
					else:
						print('Unable to add (co-sense) arc with specified transition; require transition radius > arc radius')
				else:
					o = Q2D_Circle(arc.circle.center, arc.circle.radius + transition)
					l = line.parallel(-offset)
					p, c, t = Q2D_Path.__intersect_line(l, o, farside)
					if p is not None:
						print('Adding (counter-sense) arc (with transition)')
						#print('point = (', p.x(), p.y(), '); cross =', c, 'tangent =', t)
						self.__append(Q2D_Arc(line.project(p), Q2D_Circle(p, transition), clockwise=(not arc.clockwise)))
						self.__append(Q2D_Arc(arc.circle.project(p), arc.circle, clockwise=arc.clockwise))
					else:
						print('Unable to add (counter-sense) arc with specified transition')
			else: # line intersects circle
				if co_sense:
					if transition < arc.circle.radius:
						o = Q2D_Circle(arc.circle.center, arc.circle.radius - transition)
						l = line.parallel(offset)
						p, c, t = Q2D_Path.__intersect_line(l, o, farside)
						if p is not None:
							print('Adding (co-sense) arc (with transition)')
							#print('point = (', p.x(), p.y(), '); cross =', c, 'tangent =', t)
							self.__append(Q2D_Arc(line.project(p), Q2D_Circle(p, transition), clockwise=arc.clockwise))
							self.__append(Q2D_Arc(arc.circle.project(p), arc.circle, clockwise=arc.clockwise))
						else:
							print('Unable to add (co-sense) arc with specified transition; try increasing the transition radius')
					else:
						print('Unable to add (co-sense) arc with specified transition; require transition radius > arc radius')
				else:
					o = Q2D_Circle(arc.circle.center, arc.circle.radius + transition)
					l = line.parallel(-offset)
					p, c, t = Q2D_Path.__intersect_line(l, o, farside)
					if p is not None:
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
			print("Unable to intersect arcs")
		else:
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

	def show(self):
		plt.show()

	def __draw_point(self, point, center=False):
		if center:
			marker = '+'
			color = 'green'
		else:
			marker = '.'
			color = 'blue'
		self._ax.scatter(point.start[0], point.start[1], marker=marker, color=color)

	def __draw_circle(self, circle, construction=True):
		x_axis = 2.0 * circle.radius
		y_axis = 2.0 * circle.radius
		if construction:
			ec='green'
			ls='--'
		else:
			ec='blue'
			ls='-'
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
		patch = mpatches.Arc(arc.circle.center.start, x_axis, y_axis, theta1=t1, theta2=t2, edgecolor='blue', facecolor=None, fill=False)
		self._ax.add_patch(patch)
		self.__draw_point(arc.circle.center, True)
		self.__draw_point(arc.start)

	def __draw_line(self, line):
		p1 = line.start
		p2 = line.chain
		if p2.name != "Point":
			p2 = p2.start
		self._ax.plot([p1.start[0], p2.start[0]], [p1.start[1], p2.start[1]], '-', color='blue', linewidth=1)
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

if arc_test == 0:
	plotter = Q2D_Plotter([-8,0], [-2,6])

	point = Q2D_Point((-2.0, -1.5))
	arc_1 = Q2D_Arc(point, Q2D_Circle(Q2D_Point((-2.0, -1.0)), 0.5), clockwise=True)
	arc_2 = Q2D_Arc(point, Q2D_Circle(Q2D_Point((-3.0,  4.0)), 0.5), clockwise=True)
	arc_3 = Q2D_Arc(point, Q2D_Circle(Q2D_Point((-3.25, 1.0)), 0.5), clockwise=False)
	path = Q2D_Path(arc_1)
	path.append(arc_2, transition=4.5, farside=True,  co_sense=False)
	path.append(arc_3, transition=2.5, farside=False, co_sense=True)
	path.append(arc_1, transition=3.5, farside=False, co_sense=False)
	path.end_point(point)

	plotter.draw(path)
	plotter.show()

elif arc_test == 1:
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
	path.append(a_tr, transition=0.08,	   farside=True,  co_sense=False)
	path.append(l_t,  transition=0.08,	   farside=True,  co_sense=False)
	path.end_point(m_t)

	plotter.draw(path)

	plotter.show()

else: # let's draw a hook

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
	if not Q2D_SpaceClaim:
		plotter = Q2D_Plotter([-0.13,0.13], [-0.07,0.19])

	p_start = Q2D_Point((0.0, -r_seat))	# start/end point of path

	p_seat  = Q2D_Point((0.0, 0.0))		# construction circle-centers
	p_hole  = Q2D_Point((0.0, y_csep))
	p_main  = Q2D_Point((x_main, y_main))

	c_seat = Q2D_Circle(p_seat, r_seat)					# circle outlining the seat of the hook
	a_seat = Q2D_Arc(p_start, c_seat, clockwise=False)	# define arc anti-clockwise from bottom
	c_top  = Q2D_Circle(p_hole, r_top)					# circle outlining the top of the hook
	a_top  = Q2D_Arc(None, c_top, clockwise=True)		# define arc clockwise; start irrelevant
	c_main = Q2D_Circle(p_main, r_main)					# circle outlining the top of the hook
	a_main = Q2D_Arc(None, c_main, clockwise=True)		# define arc clockwise; start irrelevant

	l_neck = Q2D_Line(p_hole, Q2D_Vector(DEG(neck_a)))	# neck center-line

	path = Q2D_Path(a_seat)
	path.append(l_neck.parallel(-neck_t / 2, True), transition=r1, farside=False, co_sense=True)
	path.append(a_top, transition=r2, farside=False, co_sense=False)
	path.append(l_neck.parallel( neck_t / 2, False), transition=r2, farside=False, co_sense=False)
	path.append(a_main, transition=r2, farside=False, co_sense=False)
	path.append(a_seat, transition=rb, farside=False, co_sense=True)
	path.end_point(p_start)

	plotter.draw(path)

	plotter.draw(Q2D_Circle(p_hole, r_hole)) # circle outlining the top hole of the hook

	if not Q2D_SpaceClaim:
		plotter.show()
