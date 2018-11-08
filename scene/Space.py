from operator import itemgetter

import Plane
import Polygon
import Receiver

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

    def add_poly(self, polygon):
        if polygon.material.is_illustrative():
            polygon.ill_only = True
        self.polygons.append(polygon)

    def __make_poly(self, verts, indices, material):
        plane = self.plane_from_points(verts[indices[0],:], verts[indices[1],:], verts[indices[2],:])
        polygon = Polygon.Polygon(plane, len(indices), material)
        pi = 0
        for i in indices:
            xy, z = plane.project(verts[i,:])
            polygon.set_vertex(pi, xy)
            pi += 1
        self.add_poly(polygon)
        return polygon

    def __make_zone(self, polygon, vert1, vert2, zone_material, zone_width):
        Bk = polygon.plane.basis_k
        Bi = vert2 - vert1
        Bj = np.cross(Bk, Bi)

        Bi /= np.linalg.norm(Bi)
        Bj /= np.linalg.norm(Bj)

        offset = zone_width * (Bk * np.sqrt(3) - Bj) / 2

        verts = np.zeros((4,3))
        verts[0,:] = vert1
        verts[1,:] = vert2
        verts[2,:] = vert2 + offset
        verts[3,:] = vert1 + offset

        self.__make_poly(verts, range(0, 4), zone_material)

    def __make_zones(self, polygon, verts, indices, zone_material, zone_widths):
        for i1 in range(0, polygon.count):
            if zone_widths[i1] > 0:
                i2 = i1 + 1
                if i2 == polygon.count:
                    i2 = 0
                self.__make_zone(polygon, verts[indices[i1],:], verts[indices[i2],:], zone_material, zone_widths[i1])

    def add_box(self, base_center, base_wh, height, facing_angle, material, diffraction_zones=None):
        # Diffraction zones: two planes 30 degrees apart, at 30 degrees to closest walls
        #                    effective change of origin, halving distance?
        # - a list of zero-or-positive zone sizes corresponding to each of the 12 box edges
        # - a material for the zones
        # e.g., diffraction_zones=(material, [0,0,0,0,3,3,3,3,1,1,1,1])

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
        
        p_base  = self.__make_poly(verts, [0,3,2,1], material)
        p_roof  = self.__make_poly(verts, [4,5,6,7], material)
        p_front = self.__make_poly(verts, [0,1,5,4], material)
        p_right = self.__make_poly(verts, [1,2,6,5], material)
        p_back  = self.__make_poly(verts, [2,3,7,6], material)
        p_left  = self.__make_poly(verts, [3,0,4,7], material)

        if diffraction_zones is not None:
            zone_material, edge_list = diffraction_zones

            self.__make_zones(p_base,  verts, [0,3,2,1], zone_material, itemgetter(3, 2, 1, 0)(edge_list))
            self.__make_zones(p_roof,  verts, [4,5,6,7], zone_material, itemgetter(8, 9,10,11)(edge_list))
            self.__make_zones(p_front, verts, [0,1,5,4], zone_material, itemgetter(0, 4, 8, 5)(edge_list))
            self.__make_zones(p_right, verts, [1,2,6,5], zone_material, itemgetter(1, 5, 9, 6)(edge_list))
            self.__make_zones(p_back,  verts, [2,3,7,6], zone_material, itemgetter(2, 6,10, 7)(edge_list))
            self.__make_zones(p_left,  verts, [3,0,4,7], zone_material, itemgetter(3, 7,11, 4)(edge_list))

    def cube(self, center, cube_dimension, material, add_to_scene=True):
        polygons = []

        origin = np.asarray(center)

        plane = self.horizontal_plane(origin + [0,0,cube_dimension/2], True)
        polygons.append(Polygon.Polygon(plane, 4, material))

        plane = self.horizontal_plane(origin - [0,0,cube_dimension/2], False)
        polygons.append(Polygon.Polygon(plane, 4, material))

        plane = self.vertical_plane(origin + [0,cube_dimension/2,0],   0)
        polygons.append(Polygon.Polygon(plane, 4, material))

        plane = self.vertical_plane(origin + [cube_dimension/2,0,0],  90)
        polygons.append(Polygon.Polygon(plane, 4, material))

        plane = self.vertical_plane(origin - [0,cube_dimension/2,0], 180)
        polygons.append(Polygon.Polygon(plane, 4, material))

        plane = self.vertical_plane(origin - [cube_dimension/2,0,0], 270)
        polygons.append(Polygon.Polygon(plane, 4, material))

        for p in polygons:
            p.square(cube_dimension)
            if add_to_scene:
                self.add_poly(p)

        return polygons

    def make_receiver(self, origin, cube_dimension, material):
        return Receiver.Receiver(self, origin, cube_dimension, material)
