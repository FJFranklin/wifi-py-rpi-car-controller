import numpy as np

class Polygon(object):

    def __init__(self, plane, vertex_count, material):
        self.plane = plane
        self.count = vertex_count
        self.verts = np.zeros((vertex_count, 2))
        self.__v3D = np.zeros((vertex_count, 3))
        self.material = material
        self.ill_only = None # if not None, then for illustration only; otherwise it's an offset

    def vertices(self):
        for v in range(0, self.count):
            self.__v3D[v,:] = self.plane.coordinate((self.verts[v,0], self.verts[v,1]))
            if self.ill_only is not None:
                self.__v3D[v,:] = self.__v3D[v,:] + self.ill_only

        return self.__v3D, self.count

    def set_vertex(self, index, xy):
        x, y = xy
        self.verts[index,:] = [x, y]

    def square(self, dimension):
        d = dimension / 2
        self.verts[0,:] = [ d, d]
        self.verts[1,:] = [-d, d]
        self.verts[2,:] = [-d,-d]
        self.verts[3,:] = [ d,-d]

    def get_colors(self, light_vector, ambient): # vector points to light source
        brightness = self.plane.brightness(light_vector)
        face_color = self.material.color(ambient, brightness)

        if face_color is None:
            edge_color = (0,0,0,1)
        else:
            edge_color = None

        return face_color, edge_color

    @staticmethod
    def __crop_2D_line(verts, count, v1, v2): # crops an anticlockwise polygon to the interior, assuming v1 & v2 are consecutive vertices of an anticlockwise polygon
        Bi = v2 - v1
        Bj = np.asarray([-Bi[1],Bi[0]])

        crop_verts = np.zeros((count+1,2))
        crop_count = 0

        dj_0 = np.dot(verts[0,:] - v1, Bj) # -ve for exterior points
        if dj_0 >= 0:
            crop_verts[crop_count,:] = verts[0,:]
            crop_count += 1
        dj_1 = dj_0
        for i2 in range(1, count):
            i1 = i2 - 1
            dj_2 = np.dot(verts[i2,:] - v1, Bj) # -ve for exterior points
            if ((dj_1 < 0) and (dj_2 > 0)) or ((dj_1 > 0) and (dj_2 < 0)):
                crop_verts[crop_count,:] = verts[i1,:] - dj_1 * (verts[i2,:] - verts[i1,:]) / (dj_2 - dj_1)
                crop_count += 1
            if dj_2 >= 0:
                crop_verts[crop_count,:] = verts[i2,:]
                crop_count += 1
            dj_1 = dj_2
        if ((dj_1 < 0) and (dj_0 > 0)) or ((dj_1 > 0) and (dj_0 < 0)):
            i1 = count - 1
            i2 = 0
            crop_verts[crop_count,:] = verts[i1,:] - dj_1 * (verts[i2,:] - verts[i1,:]) / (dj_0 - dj_1)
            crop_count += 1

        if crop_count > 2:
            verts = crop_verts[0:crop_count,:]
            count = crop_count
        else:
            verts = None
            count = 0
        return verts, count

    def crop_2D_poly(self, polygon): # crops a polygon to the interior of self - assumes self.plane == polygon.plane
        verts = polygon.verts
        count = polygon.count

        for s1 in range(0, self.count):
            s2 = s1 + 1
            if s2 == self.count:
                s2 = 0
            verts, count = self.__crop_2D_line(verts, count, self.verts[s1,:], self.verts[s2,:])
            if verts is None:
                break

        if count > 2:
            poly = Polygon(self.plane, count, polygon.material)
            poly.verts[:,:] = verts[0:count,:]
        else:
            poly = None

        return poly

    def crop_3D_poly(self, polygon):
        # crops a polygon above self-plane
        # TODO: tolerances.. merge near-points

        v3D, count = polygon.vertices()

        crop_verts = np.zeros((count+1,2))
        crop_count = 0

        xy_0, z_0 = self.plane.project(v3D[0,:])
        xy_1, z_1 = xy_0, z_0
        if z_1 >= 0:
            crop_verts[crop_count,:] = polygon.verts[0,:]
            crop_count += 1
        for i2 in range(1,count):
            i1 = i2 - 1
            xy_2, z_2 = self.plane.project(v3D[i2,:])
            if ((z_1 < 0) and (z_2 > 0)) or ((z_1 > 0) and (z_2 < 0)):
                crop_verts[crop_count,:] = polygon.verts[i1,:] - z_1 * (polygon.verts[i2,:] - polygon.verts[i1,:]) / (z_2 - z_1)
                crop_count += 1
            if z_2 >= 0:
                crop_verts[crop_count,:] = polygon.verts[i2,:]
                crop_count += 1
            xy_1, z_1 = xy_2, z_2
        if ((z_1 < 0) and (z_0 > 0)) or ((z_1 > 0) and (z_0 < 0)):
            i1 = count - 1
            i2 = 0
            crop_verts[crop_count,:] = polygon.verts[i1,:] - z_1 * (polygon.verts[i2,:] - polygon.verts[i1,:]) / (z_0 - z_1)
            crop_count += 1

        if crop_count > 2:
            crop_poly = Polygon(polygon.plane, crop_count, polygon.material)
            crop_poly.verts[:,:] = crop_verts[0:crop_count,:]
        else:
            crop_poly = None

        return crop_poly

    def project_3D_poly(self, origin, polygon):
        # assumes the polygon is above self-plane
        # TODO: tolerances.. merge near-points

        local_xy, local_z = polygon.plane.project(origin)
        if local_z > 0:
            reorientate = True # projected polygon will be clockwise
        elif local_z < 0:
            reorientate = False
        else:
            return None # projection will be a line

        v3D, count = polygon.vertices()

        proj_verts = np.zeros((count,2))
        proj_count = count

        xy_o, z_o = self.plane.project(origin)
        for i1 in range(0, count):
            xy_i, z_i = self.plane.project(v3D[i1,:])

            if reorientate:
                i2 = count - 1 - i1
            else:
                i2 = i1
            proj_verts[i2,:], z_i = self.plane.project(origin - z_o * (v3D[i1,:] - origin) / (z_i - z_o))

        if proj_count > 2:
            proj_poly = Polygon(self.plane, proj_count, polygon.material)
            proj_poly.verts[:,:] = proj_verts[0:proj_count,:]
        else:
            proj_poly = None

        return proj_poly

    def project_and_crop(self, origin, polygon):
        # the projection origin must be behind us

        # crop polygon above self-plane
        crop_poly = self.crop_3D_poly(polygon)
        if crop_poly is None: # cropped away, or lost amidst the tolerances...
            return None

        # project polygon onto self-plane
        proj_poly = self.project_3D_poly(origin, crop_poly)
        if proj_poly is None: # lost amidst the tolerances...
            return None

        window_poly = self.crop_2D_poly(proj_poly)
        if window_poly is None: # cropped away, or lost amidst the tolerances...
            return None

        # project polygon back onto original plane
        proj = polygon.project_3D_poly(origin, window_poly)

        return (window_poly, proj)

    def compare_2D_poly(self, polygon):
        # assumes polygon is coplanar and shares same coordinate system, i.e., self.plane == polygon.plane
        # is_exterior is True if all points in polygon are outside self
        # is_interior is True if all points in polygon are within self

        is_exterior = False
        is_interior = True

        for s1 in range(0, self.count):
            s2 = s1 + 1
            if s2 == self.count:
                s2 = 0

            Bi = self.verts[s2,:] - self.verts[s1,:]
            Bj = np.asarray([-Bi[1],Bi[0]]) # points inwards; not a normalised basis vector

            all_outside = True
            for i in range(0, polygon.count):
                dp = np.dot(polygon.verts[i,:] - self.verts[s1,:], Bj)
                if dp > 0:
                    all_outside = False
                if dp < 0:
                    is_interior = False
            if all_outside:
                is_exterior = True
                is_interior = False
                break

        return is_exterior, is_interior
