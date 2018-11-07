import numpy as np

class Polygon(object):

    def __init__(self, plane, vertex_count, material):
        self.plane = plane
        self.count = vertex_count
        self.verts = np.zeros((vertex_count, 2))
        self.__v3D = np.zeros((vertex_count, 3))
        self.material = material

    def vertices(self):
        for v in range(0, self.count):
            self.__v3D[v,:] = self.plane.coordinate((self.verts[v,0], self.verts[v,1]))

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

    def intersection(self, v1, v2):
        # v1 must be behind us
        # v2 must be on or above us
        xy_1, z_1 = self.plane.project(v1)
        xy_2, z_2 = self.plane.project(v2)
        return v1 - z_1 * (v2 - v1) / (z_2 - z_1)

    def project_and_compare(self, origin, polygon):
        # the projection origin must be (a) behind us, and (b) not in the plane of the specified polygon

        polygon_intersects = False
        polygon_contained  = False
        self_contained     = False

        no_in_front = 0
        no_behind   = 0

        verts, count = polygon.vertices()
        for i in range(0,count):
            local_xy, local_z = self.plane.project(verts[i,:])
            if local_z > 0:
                no_in_front += 1
            elif local_z < 0:
                no_behind += 1

        if (no_in_front > 0) and (no_behind > 0):
            # polygon intersects our plane - need to crop it
            crop_verts = np.zeros((count+1,3))
            crop_count = 0
            xy_0, z_0 = self.plane.project(verts[0,:])
            xy_1, z_1 = xy_0, z_0
            if z_1 >= 0:
                crop_verts[crop_count,:] = verts[0,:]
                crop_count += 1
            for i2 in range(1,count):
                i1 = i2 - 1
                xy_2, z_2 = self.plane.project(verts[i2,:])
                if ((z_1 < 0) and (z_2 > 0)) or ((z_1 > 0) and (z_2 < 0)):
                    crop_verts[crop_count,:] = self.intersection(verts[i1,:], verts[i2,:])
                    crop_count += 1
                if z_2 >= 0:
                    crop_verts[crop_count,:] = verts[i2,:]
                    crop_count += 1
                xy_1, z_1 = xy_2, z_2
            if ((z_1 < 0) and (z_0 > 0)) or ((z_1 > 0) and (z_0 < 0)):
                crop_verts[crop_count,:] = self.intersection(verts[(count-1),:], verts[0,:])
                crop_count += 1
            verts, count = crop_verts[0:crop_count,:], crop_count

        if (no_in_front > 0):
            # project
            proj_verts = np.zeros((count,2))
            for i in range(0,count):
                verts[i,:] = self.intersection(origin, verts[i,:])
                local_xy, local_z = self.plane.project(verts[i,:])
                x, y = local_xy
                proj_verts[i,:] = [x, y]

            # compare - we now have two co-planar convex polygons
            polygon_intersects = True
            polygon_contained  = True

            for s1 in range(0,self.count):
                s2 = s1 + 1
                if s2 == self.count:
                    s2 = 0

                Bi = self.verts[s2,:] - self.verts[s1,:]
                Bj = np.asarray([-Bi[1],Bi[0]]) # points inwards; not a normalised basis vector

                all_outside = True
                for i in range(0,count):
                    dp = np.dot(proj_verts[i,:] - self.verts[s1,:], Bj)
                    if dp > 0:
                        all_outside = False
                    if dp < 0:
                        polygon_contained = False
                if all_outside:
                    polygon_intersects = False
                    polygon_contained = False
                    break

            if polygon_intersects: # or, rather, we don't know yet...
                local_xy, local_z = polygon.plane.project(origin)
                if local_z > 0:
                    sense = -1 # projected polygon will be clockwise
                else:
                    sense = 1

                self_contained = True

                for i1 in range(0,self.count):
                    i2 = i1 + 1
                    if i2 == self.count:
                        i2 = 0

                    Bi = proj_verts[i2,:] - proj_verts[i1,:]
                    Bj = np.asarray([-Bi[1],Bi[0]]) * sense # points inwards; not a normalised basis vector

                    all_outside = True
                    for s in range(0,count):
                        dp = np.dot(self.verts[s,:] - proj_verts[i1,:], Bj)
                        if dp > 0:
                            all_outside = False
                        if dp < 0:
                            self_contained = False
                    if all_outside:
                        polygon_intersects = False
                        self_contained = False
                        break

        return polygon_intersects, polygon_contained, self_contained
