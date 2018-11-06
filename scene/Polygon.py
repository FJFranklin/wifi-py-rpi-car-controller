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
