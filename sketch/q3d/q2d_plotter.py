import math

from q2d_path import *

Q2D_Plotter_Print_Info = False
Q2D_Plotter_Construction_Arcs = True

Q2D_Plotter_Path_Color = 'blue' # color for plotting path if using MatPlotLib

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
            color = Q2D_Plotter_Path_Color
        if Q2D_Plotter_Print_Info:
            print('Point: ({x},{y})'.format(x=point.x, y=point.y))
        self._ax.scatter(point.x, point.y, marker=marker, color=color)

    def draw_points(self, points):
        marker = '.'
        color = Q2D_Plotter_Path_Color
        for p in points:
            self._ax.scatter(p[0], p[1], marker=marker, color=color)

    def __draw_ellipse(self, ellipse, construction=True):
        if construction and not Q2D_Plotter_Construction_Arcs:
            return

        x0 = ellipse.center.x
        y0 = ellipse.center.y
        x_axis = 2.0 * ellipse.semi_major
        y_axis = 2.0 * ellipse.semi_minor
        angle = math.degrees(ellipse.rotate)
        if construction:
            ec='green'
            ls='--'
        else:
            ec=Q2D_Plotter_Path_Color
            ls='-'
        if Q2D_Plotter_Print_Info:
            print('Ellipse: Center: ({x},{y}); Axes=({a},{b})'.format(x0, y0, a=x_axis, b=y_axis))
        patch = Q2D_Plotter.__mpatches.Arc((x0, y0), x_axis, y_axis, angle=angle,
                                           edgecolor=ec, linestyle=ls, facecolor=None, fill=False, linewidth=1)
        self._ax.add_patch(patch)
        self.__draw_point(ellipse.center, True)

    def __draw_arc(self, arc):
        self.__draw_ellipse(arc.circle)
        if arc.clockwise:
            p1 = arc.end
            p2 = arc.start
        else:
            p1 = arc.start
            p2 = arc.end
        angle = arc.circle.rotate
        t1 = math.degrees(math.atan2(p1.y - arc.Oy, p1.x - arc.Ox)) - angle
        t2 = math.degrees(math.atan2(p2.y - arc.Oy, p2.x - arc.Ox)) - angle
        if t2 <= t1:
            t2 += 360.0
        x_axis = 2.0 * arc.circle.semi_major
        y_axis = 2.0 * arc.circle.semi_minor
        if Q2D_Plotter_Print_Info:
            print('Arc: Center: ({x},{y}); Axes=({a},{b}); Angles=({s},{e})'.format(x=arc.Ox, y=arc.Oy,
                                                                                    a=x_axis, b=y_axis, s=t1, e=t2))
        patch = Q2D_Plotter.__mpatches.Arc((arc.Ox, arc.Oy), x_axis, y_axis, angle=angle, theta1=t1, theta2=t2,
                                           edgecolor=Q2D_Plotter_Path_Color, facecolor=None, fill=False)
        self._ax.add_patch(patch)
        self.__draw_point(arc.circle.center, True)
        self.__draw_point(arc.start)

    def __draw_line(self, line):
        p1 = line.start
        p2 = line.end
        if Q2D_Plotter_Print_Info:
            print('Line: From: ({x},{y}); To: ({a},{b})'.format(x=p1.x, y=p1.y, a=p2.x, b=p2.y))
        self._ax.plot([p1.x, p2.x], [p1.y, p2.y], '-', color=Q2D_Plotter_Path_Color, linewidth=1)
        self.__draw_point(p1)

    def draw(self, path):
        if path.geom == "Path":
            for item in path.edges:
                if item.geom == "Line":
                    self.__draw_line(item)
                elif item.geom == "Arc":
                    self.__draw_arc(item)

        elif path.geom == "Circle" or path.geom == "Ellipse":
            self.__draw_ellipse(path, False)
