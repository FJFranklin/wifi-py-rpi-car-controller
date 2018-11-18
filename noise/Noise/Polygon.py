import numpy as np

from .Basis import Basis

class Polygon(object):

    def __init__(self, plane, vertex_count, props=None):
        self.plane = plane
        self.count = vertex_count
        self.verts = np.zeros((vertex_count, 2))
        self.__v3D = np.zeros((vertex_count, 3))

        if props is None:
            self.props = { }
        else:
            self.props = props.copy()
        # props:
        #   'material'  Material class instance [required]
        #   'offset'    3D vector offset for the polygon when displaying [optional]

    def copy(self):
        poly = Polygon(self.plane, self.count, self.props)
        poly.verts[:,:] = self.verts[:,:]
        return poly

    def reverse(self, FlipY=True):
        poly = Polygon(self.plane.reverse(), self.count, self.props)

        # flip y-axis & reverse order of vertices

        for s in range(0, self.count):
            i = self.count - 1 - s
            vert = self.verts[s,:]
            if FlipY:
                poly.verts[i,:] = [vert[0],-vert[1]]
            else:
                poly.verts[i,:] = [-vert[0],vert[1]]

        return poly

    def vertices(self):
        for v in range(0, self.count):
            self.__v3D[v,:] = self.plane.coordinate((self.verts[v,0], self.verts[v,1]))

            if 'offset' in self.props:
                offset = self.props['offset']
                self.__v3D[v,:] = self.__v3D[v,:] + offset

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
        face_color = self.props['material'].color(ambient, brightness)

        if face_color is None:
            edge_color = (0,0,0,1)
        else:
            edge_color = None

        return face_color, edge_color

    @staticmethod
    def __tidy_2D_poly(verts, count): # ensures a strictly convex polygon and removes points that are nearly indistinguishable
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

            if Basis.separation(verts[i1], verts[i2]) == 0:
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

            if Basis.is_positive(np.dot(v2 - v1, Bj)):
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
            poly = Polygon(self.plane, count, polygon.props)
            poly.verts[:,:] = verts[0:count,:]
        else:
            poly = None

        return poly

    def split(self, v1, v2): # crops self-polygon to the line specified by 2D in-plane coordinates v1 & v2
        verts, count = Polygon.__crop_2D_line(self.verts, self.count, v1, v2)

        if verts is not None:
            poly = Polygon(self.plane, count, self.props)
            poly.verts[:,:] = verts
        else:
            poly = None

        return poly

    def intersections_3D(self, origin, v3D, count):
        i3D = np.copy(v3D)

        xy_o, z_o = self.plane.project(origin)

        for i in range(0, count):
            xy_i, z_i = self.plane.project(v3D[i,:])
            i3D[i,:] = origin - z_o * (v3D[i,:] - origin) / (z_i - z_o)

        return i3D

    @staticmethod
    def __crop_3D_poly(plane, polygon, discard_coplanar=True):
        # crops a polygon above plane

        v3D, count = polygon.vertices()

        crop_verts = np.zeros((count+1,2))
        crop_count = 0

        coplanar = True

        xy_0, z_0 = plane.project(v3D[0,:])
        if z_0:
            coplanar = False
        xy_1, z_1 = xy_0, z_0
        if z_1 >= 0:
            crop_verts[crop_count,:] = polygon.verts[0,:]
            crop_count += 1
        for i2 in range(1,count):
            i1 = i2 - 1
            xy_2, z_2 = plane.project(v3D[i2,:])
            if z_2:
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

        if coplanar and discard_coplanar:
            return None

        crop_verts, crop_count = Polygon.__tidy_2D_poly(crop_verts, crop_count)

        if crop_verts is not None:
            crop_poly = Polygon(polygon.plane, crop_count, polygon.props)
            crop_poly.verts[:,:] = crop_verts
        else:
            crop_poly = None

        return crop_poly

    def crop_3D_poly(self, polygon):
        # crops a polygon above self-plane
        return Polygon.__crop_3D_poly(self.plane, polygon)

    def crop_3D_poly_between(self, planes, above=True):
        # crops self above/below planes
        poly = self
        for p in planes:
            if above:
                plane = p
            else:
                plane = p.reverse()
            poly = Polygon.__crop_3D_poly(plane, poly)
            if poly is None:
                break
        return poly

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

        found_zero = False

        xy_o, z_o = self.plane.project(origin)
        if printing:
            print(xy_o, z_o)
        for i1 in range(0, count):
            xy_i, z_i = self.plane.project(v3D[i1,:])
            if z_i - z_o == 0:
                found_zero = True
                break
            if printing:
                #print(xy_i, z_i, z_o/(z_i-z_o))
                print(origin - z_o * (v3D[i1,:] - origin) / (z_i - z_o))

            if reorientate:
                i2 = count - 1 - i1
            else:
                i2 = i1
            proj_verts[i2,:], z_i = self.plane.project(origin - z_o * (v3D[i1,:] - origin) / (z_i - z_o))
        if found_zero:
            if printing:
                print('Found zero')
            return None
        if printing:
            print(origin)
            print(self.plane.basis.origin)
            print(self.plane.basis.matrix)
            print(polygon.plane.basis.origin)
            print(polygon.plane.basis.matrix)
            print(polygon.verts)
            print(v3D)
            print(reorientate)
            print(proj_verts)
        proj_verts, proj_count = Polygon.__tidy_2D_poly(proj_verts, proj_count)

        if proj_verts is not None:
            proj_poly = Polygon(self.plane, proj_count, polygon.props)
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

        # crop refractive plane according to incidence
        if polygon.props['material'].is_refractive():
            poly_xy, poly_z = polygon.plane.project(origin)
            poly = Polygon.__crop_3D_poly(polygon.plane.jki(origin), polygon, False)
        else:
            poly = polygon
        if poly is None: # cropped away, or lost amidst the tolerances...
            return None

        # crop polygon above self-plane
        poly = self.crop_3D_poly(poly)
        if poly is None: # cropped away, or lost amidst the tolerances...
            return None

        # project polygon onto self-plane
        poly = self.project_3D_poly(origin, poly)
        if poly is None: # lost amidst the tolerances...
            return None

        return self.crop_visible(origin, (poly, polygon))
