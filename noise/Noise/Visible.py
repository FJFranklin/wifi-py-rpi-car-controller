import numpy as np

from .Basis import Basis

class Visible(object):

    def __init__(self, origin, window, target=None):
        self.origin = origin
        self.window = window
        self.target = target

    def crop_visible(self, visible):
        cropped_poly = self.window.crop_2D_poly(visible.window)
        if cropped_poly is None: # cropped away, or lost amidst the tolerances...
            return None

        # project polygon back onto original plane
        cropped_proj = visible.target.project_3D_poly(self.origin, cropped_poly)
        if cropped_proj is None:
            print('Projection error')
            return None
        return Visible(self.origin, cropped_poly, cropped_proj)

    def nearest_intersection(self, visible):
        # assumes coincident origins & coplanar windows
        # i.e., self.origin == visible.origin & self.window.plane == visible.window.plane

        v3D, count = visible.target.vertices()

        v1 = None
        v2 = None
        d1 = 0
        d2 = 0

        for i1 in range(0, count):
            i2 = i1 + 1
            if i2 == count:
                i2 = 0

            Bi = visible.window.verts[i2,:] - visible.window.verts[i1,:]
            Bj = np.asarray([-Bi[1],Bi[0]])

            vertex_above = False
            vertex_below = False

            for s in range(0, self.window.count):
                dp = np.dot(self.window.verts[s,:] - visible.window.verts[i1,:], Bj)
                if Basis.is_strictly_positive(dp):
                    vertex_above = True
                if Basis.is_strictly_negative(dp):
                    vertex_below = True
                if vertex_above and vertex_below: # a valid intersecting edge
                    dist_o1 = np.linalg.norm(v3D[i1,:] - self.origin)
                    dist_o2 = np.linalg.norm(v3D[i2,:] - self.origin)
                    if dist_o1 < dist_o2:
                        v_min = visible.window.verts[i1,:]
                        v_max = visible.window.verts[i2,:]
                        d_min = dist_o1
                        d_max = dist_o2
                    else:
                        v_min = visible.window.verts[i2,:]
                        v_max = visible.window.verts[i1,:]
                        d_min = dist_o2
                        d_max = dist_o1
                    if (v1 is None) or ((d_min < d1) or ((d_min == d1) and (d_max < d2))):
                        v1 = v_min
                        v2 = v_max
                        d1 = d_min
                        d2 = d_max
                    break

        return v1, d1, v2, d2

    def compare_visible(self, visible, printing=False):
        # assumes coincident origins & coplanar windows
        # i.e., self.origin == visible.origin & self.window.plane == visible.window.plane

        # is_exterior is True if all points in visible.window are outside self.window
        # is_interior is True if all points in visible.window are within self.window
        # is_farther  is True if any points in visible.target are opposite to the origin than self.target.plane

        is_exterior = False
        is_interior = True
        is_farther  = True
        is_coplanar = True

        for s1 in range(0, self.window.count):
            s2 = s1 + 1
            if s2 == self.window.count:
                s2 = 0

            Bi = self.window.verts[s2,:] - self.window.verts[s1,:]
            Bj = np.asarray([-Bi[1],Bi[0]]) # points inwards; not a normalised basis vector

            all_outside = True
            for i in range(0, visible.window.count):
                dp = np.dot(visible.window.verts[i,:] - self.window.verts[s1,:], Bj)
                if Basis.is_strictly_positive(dp):
                    all_outside = False
                if Basis.is_strictly_negative(dp):
                    is_interior = False
            if all_outside:
                is_exterior = True
                is_interior = False
                break

        v3D, count = visible.target.vertices()

        xy_o, z_o = self.target.plane.project(self.origin)
        for i in range(0, count):
            xy_i, z_i = self.target.plane.project(v3D[i,:])
            zoi = z_o * z_i
            if printing:
                print('vis-cmp: '+str((z_o, z_i, zoi)))
            if Basis.is_strictly_positive(zoi):
                is_farther = False
                is_coplanar = False
            if Basis.is_strictly_negative(zoi):
                is_coplanar = False

        return is_exterior, is_interior, is_farther, is_coplanar
