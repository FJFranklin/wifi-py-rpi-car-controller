from operator import itemgetter

import numpy as np

from .Basis import Basis
from .Plane import Plane
from .Polygon import Polygon
from .Receiver import Receiver

class Space(Basis):

    def __init__(self):
        self.polygons = []
        Basis.__init__(self)

    def add_poly(self, polygon, material=None):
        if material is not None:
            polygon.props['material'] = material
        else:
            material = polygon.props['material']
        if material.is_illustrative():
            polygon.props['ill_only'] = True
        self.polygons.append(polygon)

    def __make_poly(self, verts, indices, material):
        plane = Plane.from_points(verts[indices[0],:], verts[indices[1],:], verts[indices[2],:])
        polygon = Polygon(plane, len(indices))

        pi = 0
        for i in indices:
            xy, z = plane.project(verts[i,:])
            polygon.set_vertex(pi, xy)
            pi += 1

        self.add_poly(polygon, material)
        return polygon

    def __add_zone(self, poly, indices, neighbour, zone_width, zone_material):
        angle = np.arccos(np.dot(poly.plane.normal(), neighbour.plane.normal())) * 180 / np.pi
        angle = ((330 - angle) / 2) * np.pi / 180

        v3D, count = poly.vertices()
        v1 = v3D[indices[0], :]
        v2 = v3D[indices[1], :]

        Bk = poly.plane.normal()
        Bi = v2 - v1
        Bj = np.cross(Bk, Bi)

        Bi /= np.linalg.norm(Bi)
        Bj /= np.linalg.norm(Bj)

        offset = zone_width * (Bk * np.sin(angle) + Bj * np.cos(angle))

        v3D = np.zeros((4,3))
        v3D[0,:] = v2
        v3D[1,:] = v2 + offset
        v3D[2,:] = v1 + offset
        v3D[3,:] = v1

        self.__make_poly(v3D, range(0, 4), zone_material)

    def add_prism(self, verts, count, left_plane, right_plane, material, diffraction_zones=None):
        # Diffraction zones: two planes angled relative to neighbouring faces
        # - a material for the zones
        # - a list of zero-or-positive zone sizes corresponding to each of the four categories:
        #   [left, right, base, top/other]
        # e.g., diffraction_zones=(zone_material, [1,1,1,1])

        p_left = Polygon(left_plane, count)
        p_left.verts[:,:] = verts
        p_left.props['face'] = 'left'
        self.add_poly(p_left, material)
        p_right = p_left.reverse(False)
        p_right.plane = right_plane
        p_right.props['face'] = 'right'
        self.add_poly(p_right, material)

        l3D, lc = p_left.vertices()
        r3D, rc = p_right.vertices()

        polygons = []

        for l1 in range(0, count):
            l2 = l1 + 1
            if l2 == count:
                l2 = 0
            r1 = count - 1 - l1
            r2 = count - 1 - l2

            v3D = np.zeros((4,3))
            v3D[0,:] = l3D[l2]
            v3D[1,:] = l3D[l1]
            v3D[2,:] = r3D[r1]
            v3D[3,:] = r3D[r2]

            poly = self.__make_poly(v3D, [0,1,2,3], material)

            # faces go: front, base, back, [top, [top, [...]]] - i.e., 0 or more 'top' faces possible
            if l1 == 0:
                poly.props['face'] = 'front'
            elif l1 == 1:
                poly.props['face'] = 'base'
            elif l1 == 2:
                poly.props['face'] = 'back'
            else:
                poly.props['face'] = 'top'

            polygons.append(poly)

        if diffraction_zones is not None:
            zone_material, zone_dimensions = diffraction_zones
            z_left  = zone_dimensions[0]
            z_right = zone_dimensions[1]
            z_base  = zone_dimensions[2]
            z_other = zone_dimensions[3]

            for l1 in range(0, count):
                l2 = l1 + 1
                if l2 == count:
                    l2 = 0
                r1 = count - 1 - l1
                r2 = count - 1 - l2

                if z_base and z_left and l1 == 1:
                    self.__add_zone(p_left, [l1, l2], polygons[l1], z_left, zone_material)
                    self.__add_zone(polygons[l1], [0, 1], p_left, z_base, zone_material)
                if z_base and z_right and l1 == 1:
                    self.__add_zone(p_right, [r2, r1], polygons[l1], z_right, zone_material)
                    self.__add_zone(polygons[l1], [2, 3], p_right, z_base, zone_material)
                if z_other and z_left and not l1 == 1:
                    self.__add_zone(p_left, [l1, l2], polygons[l1], z_left, zone_material)
                    self.__add_zone(polygons[l1], [0, 1], p_left, z_other, zone_material)
                if z_other and z_right and not l1 == 1:
                    self.__add_zone(p_right, [r2, r1], polygons[l1], z_right, zone_material)
                    self.__add_zone(polygons[l1], [2, 3], p_right, z_other, zone_material)
                if z_base and z_other and l1 < 2:
                    self.__add_zone(polygons[l1], [3, 0], polygons[l2], z_base, zone_material)
                    self.__add_zone(polygons[l2], [1, 2], polygons[l1], z_base, zone_material)
                if z_other and l1 > 1:
                    self.__add_zone(polygons[l1], [3, 0], polygons[l2], z_other, zone_material)
                    self.__add_zone(polygons[l2], [1, 2], polygons[l1], z_other, zone_material)

    def add_box(self, basis, base_wh, heights, material, diffraction_zones=None):
        w, h = base_wh

        if isinstance(w, tuple):
            radius, angles = w
            swing = True
        else:
            radius = 0
            swing = False

        if isinstance(heights, tuple):
            height, roof = heights
            count = 5
        else:
            height = heights
            count = 4

        verts = np.zeros((count, 2))
        verts[0,:] = [-radius-h/2, height]
        verts[1,:] = [-radius-h/2, 0]
        verts[2,:] = [-radius+h/2, 0]
        verts[3,:] = [-radius+h/2, height]

        if count == 5:
            verts[4,:] = [-radius, height + roof]

        if swing:
            count = len(angles)
            if radius > h and count > 1:
                
                for i2 in range(1, count):
                    i1 = i2 - 1
                    a1 = angles[i1] - 90
                    a2 = angles[i2] - 90
                    
                    left_plane  = Plane(basis.jki().rotate_j(a2+180))
                    right_plane = Plane(basis.jki().rotate_j(a1))

                    if diffraction_zones is not None:
                        dz_material, dz_dims = diffraction_zones
                        dz = dz_dims.copy()
                        if i1 > 0:
                            dz[1] = 0
                        if i2 < count - 1:
                            dz[0] = 0
                        zones = (dz_material, dz)
                    else:
                        zones = None

                    self.add_prism(verts, count, left_plane, right_plane, material, zones)
        else:
            left_plane  = Plane(basis.jki([-w/2,0,0]).rotate_j(180))
            right_plane = Plane(basis.jki([ w/2,0,0]))

            self.add_prism(verts, count, left_plane, right_plane, material, diffraction_zones)

    def make_receiver(self, basis, dimension, material):
        verts = np.zeros((4,3))

        verts[0,:] = [-0.5, 0.5, 0]
        verts[1,:] = [ 0,   0.5, 1]
        verts[2,:] = [ 0,  -0.5, 1]
        verts[3,:] = [-0.5,-0.5, 0]
        poly_l = self.__make_poly(basis.rel_to_abs(verts * dimension), [0,1,2,3], material)

        verts[0,:] = [ 0.5, 0.5, 0]
        verts[1,:] = [ 0,   0.5, 1]
        verts[2,:] = [ 0,  -0.5, 1]
        verts[3,:] = [ 0.5,-0.5, 0]
        poly_r = self.__make_poly(basis.rel_to_abs(verts * dimension), [3,2,1,0], material)

        l = Receiver(self, [0,0,dimension/3], poly_l, material)
        r = Receiver(self, [0,0,dimension/3], poly_r, material)

        return l, r
