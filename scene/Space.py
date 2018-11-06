import Plane
import Polygon

import numpy as np

class Space(object):

    def __init__(self):
        self.polygons = []
        self.__axes = np.zeros((3, 3))

    def vertical_plane(self, origin, facing_angle): # compass direction, degrees
        angle = (90 - facing_angle) * np.pi / 180
        sin_a = np.sin(angle)
        cos_a = np.cos(angle)

        self.__axes[0,:] = [-sin_a, cos_a, 0]
        self.__axes[1,:] = [     0,     0, 1] # face y-axis is vertical (scene-z)
        self.__axes[2,:] = [ cos_a, sin_a, 0] # face z-axis is the normal

        return Plane.Plane(origin, self.__axes)

    def horizontal_plane(self, origin, facing_up): # boolean: True for facing up
        if facing_up:
            self.__axes[0,:] = [  1,  0,  0 ]
            self.__axes[1,:] = [  0,  1,  0 ]
            self.__axes[2,:] = [  0,  0,  1 ]
        else:
            self.__axes[0,:] = [  1,  0,  0 ]
            self.__axes[1,:] = [  0, -1,  0 ] # both y- & z-axes get reflected
            self.__axes[2,:] = [  0,  0, -1 ]

        return Plane.Plane(origin, self.__axes)

    def plane_from_points(self, P1, P2, P3):
        Bi = P2 - P1
        Bk = np.cross(Bi, P3 - P2)
        Bj = np.cross(Bk, Bi)

        self.__axes[0,:] = Bi / np.linalg.norm(Bi)
        self.__axes[1,:] = Bj / np.linalg.norm(Bj)
        self.__axes[2,:] = Bk / np.linalg.norm(Bk)

        return Plane.Plane(P1, self.__axes)

    def __add_poly(self, polygon):
        self.polygons.append(polygon)

    def __make_poly(self, verts, indices, props):
        plane = self.plane_from_points(verts[indices[0],:], verts[indices[1],:], verts[indices[2],:])
        polygon = Polygon.Polygon(plane, len(indices), props)
        pi = 0
        for i in indices:
            xy, z = plane.project(verts[i,:])
            polygon.set_vertex(pi, xy)
            pi += 1
        self.__add_poly(polygon)

    def add_box(self, base_center, base_wh, height, facing_angle=0, props=None):
        angle = -facing_angle * np.pi / 180
        sin_a = np.sin(angle)
        cos_a = np.cos(angle)

        w, h = base_wh

        verts = np.zeros((8,3))
        verts[0,0:2] = [( w / 2) * cos_a - ( h / 2) * sin_a, ( w / 2) * sin_a + ( h / 2) * cos_a]
        verts[1,0:2] = [(-w / 2) * cos_a - ( h / 2) * sin_a, (-w / 2) * sin_a + ( h / 2) * cos_a]
        verts[2,0:2] = [(-w / 2) * cos_a - (-h / 2) * sin_a, (-w / 2) * sin_a + (-h / 2) * cos_a]
        verts[3,0:2] = [( w / 2) * cos_a - (-h / 2) * sin_a, ( w / 2) * sin_a + (-h / 2) * cos_a]
        verts[4:8,0:2] = verts[0:4,0:2]
        verts[4:8,2] = height
        verts += base_center
        
        # Base
        self.__make_poly(verts, [0,3,2,1], props)
        # Roof
        self.__make_poly(verts, [4,5,6,7], props)
        # Front
        self.__make_poly(verts, [0,1,5,4], props)
        # Right
        self.__make_poly(verts, [1,2,6,5], props)
        # Back
        self.__make_poly(verts, [2,3,7,6], props)
        # Left
        self.__make_poly(verts, [3,0,4,7], props)
