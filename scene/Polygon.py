import numpy as np

class Polygon(object):

    def __init__(self, plane, vertex_count, material):
        self.plane = plane
        self.count = vertex_count
        self.verts = np.zeros((vertex_count, 2))
        self.__v3D = np.zeros((vertex_count, 3))
        self.material = material
        self.ill_only = None # if not None, then for illustration only; otherwise it's an offset

    def reverse(self):
        poly = Polygon(self.plane.reverse(), self.count, self.material)

        # flip y-axis & reverse order of vertices

        for s in range(0, self.count):
            i = self.count - 1 - s
            vert = self.verts[s,:]
            poly.verts[i,:] = [vert[0],-vert[1]]

        return poly

    def vertices(self):
        for v in range(0, self.count):
            self.__v3D[v,:] = self.plane.coordinate((self.verts[v,0], self.verts[v,1]))
            if self.ill_only is not None:
                self.__v3D[v,:] = self.__v3D[v,:] + self.ill_only

        return self.__v3D, self.count

    def center(self):
        return self.plane.coordinate(np.mean(self.verts, axis=0))

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
    def __tidy_2D_poly(verts, count): # ensures a strictly convex polygon and removes points that are nearly indistinguishable
        tolerance = 1E-9

        if count < 3:
            verts = None
            count = 0
            return verts, count

        # remove vertices that are too close to their next neighbour

        i1 = 0
        while i1 < count:
            if i1 == count - 1:
                i2 = 0
            else:
                i2 = i1 + 1

            v1 = verts[i1]
            v2 = verts[i2]

            if np.linalg.norm(v2 - v1) < tolerance:
                if count < 4:
                    verts = None
                    count = 0
                else:
                    if i1 < count - 1:
                        verts[i1:(count-1),:] = verts[i2:count,:]
                    count -= 1
            else:
                i1 += 1

        # ensure strict convexity, aggressively

        i2 = 0
        while i2 < count:
            if i2 == 0:
                i1 = count - 1
            else:
                i1 = i2 - 1
            if i2 == count - 1:
                i3 = 0
            else:
                i3 = i2 + 1

            v1 = verts[i1]
            v2 = verts[i2]
            v3 = verts[i3]

            Bi = v3 - v1
            Bj = np.asarray([-Bi[1],Bi[0]])
            Bj /= np.linalg.norm(Bj) # normalise the inward-pointing vector

            if np.dot(v2 - v1, Bj) > -tolerance:
                if count < 4:
                    verts = None
                    count = 0
                else:
                    if i2 < count - 1:
                        verts[i2:(count-1),:] = verts[i3:count,:]
                    count -= 1
            else:
                i2 += 1

        if verts is not None:
            verts = verts[0:count,:]
        return verts, count

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

        return Polygon.__tidy_2D_poly(crop_verts, crop_count)

    def crop_2D_poly(self, polygon): # crops a polygon to the interior of self - assumes self.plane == polygon.plane
        verts = polygon.verts
        count = polygon.count

        for s1 in range(0, self.count):
            s2 = s1 + 1
            if s2 == self.count:
                s2 = 0
            verts, count = Polygon.__crop_2D_line(verts, count, self.verts[s1,:], self.verts[s2,:])
            if verts is None:
                break

        if count > 2:
            poly = Polygon(self.plane, count, polygon.material)
            poly.verts[:,:] = verts[0:count,:]
        else:
            poly = None

        return poly

    def split(self, v1, v2): # crops self-polygon to the line specified by 2D in-plane coordinates v1 & v2
        verts, count = Polygon.__crop_2D_line(self.verts, self.count, v1, v2)

        if verts is not None:
            poly = Polygon(self.plane, count, self.material)
            poly.verts[:,:] = verts
        else:
            poly = None

        return poly

    def crop_3D_poly(self, polygon):
        # crops a polygon above self-plane

        tolerance = 1E-9

        v3D, count = polygon.vertices()

        crop_verts = np.zeros((count+1,2))
        crop_count = 0

        coplanar = True

        xy_0, z_0 = self.plane.project(v3D[0,:])
        if (z_0 < -tolerance) or (z_0 > tolerance):
            coplanar = False
        xy_1, z_1 = xy_0, z_0
        if z_1 >= 0:
            crop_verts[crop_count,:] = polygon.verts[0,:]
            crop_count += 1
        for i2 in range(1,count):
            i1 = i2 - 1
            xy_2, z_2 = self.plane.project(v3D[i2,:])
            if (z_2 < -tolerance) or (z_2 > tolerance):
                coplanar = False
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

        if coplanar:
            return None

        crop_verts, crop_count = self.__tidy_2D_poly(crop_verts, crop_count)

        if crop_verts is not None:
            crop_poly = Polygon(polygon.plane, crop_count, polygon.material)
            crop_poly.verts[:,:] = crop_verts
        else:
            crop_poly = None

        return crop_poly

    def project_3D_poly(self, origin, polygon, printing=False):
        self_xy, self_z = self.plane.project(origin)
        poly_xy, poly_z = polygon.plane.project(origin)

        if self_z * poly_z < 0:
            reorientate = True # projected polygon will be clockwise
        elif self_z * poly_z > 0:
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

        if printing:
            print(proj_verts)
        proj_verts, proj_count = self.__tidy_2D_poly(proj_verts, proj_count)

        if proj_verts is not None:
            proj_poly = Polygon(self.plane, proj_count, polygon.material)
            proj_poly.verts[:,:] = proj_verts
        else:
            proj_poly = None

        return proj_poly

    def crop_visible(self, origin, pp):
        poly, proj = pp

        cropped_poly = self.crop_2D_poly(poly)
        if cropped_poly is None: # cropped away, or lost amidst the tolerances...
            return None

        # project polygon back onto original plane
        cropped_proj = proj.project_3D_poly(origin, cropped_poly)

        if cropped_proj is None:
            print("Oops!")
            print(cropped_poly.verts)
            cropped_proj = proj.project_3D_poly(origin, cropped_poly, True)

        return (cropped_poly, cropped_proj)

    def project_and_crop(self, origin, polygon):
        # the projection origin must be behind us

        # crop polygon above self-plane
        poly = self.crop_3D_poly(polygon)
        if poly is None: # cropped away, or lost amidst the tolerances...
            return None

        # project polygon onto self-plane
        poly = self.project_3D_poly(origin, poly)
        if poly is None: # lost amidst the tolerances...
            return None

        return self.crop_visible(origin, (poly, polygon))
