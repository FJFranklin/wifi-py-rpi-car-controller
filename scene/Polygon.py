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

    def get_colors(self, light_vector, ambient): # vector points to light source
        brightness = self.plane.brightness(light_vector)
        face_color = self.material.color(ambient, brightness)

        edge_color = None # TODO: ??

        return face_color, edge_color
