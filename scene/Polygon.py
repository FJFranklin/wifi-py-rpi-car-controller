import numpy as np

class Polygon(object):

    def __init__(self, plane, vertex_count, props):
        self.plane = plane
        self.props = props
        self.count = vertex_count
        self.verts = np.zeros((vertex_count, 2))
        self.__v3D = np.zeros((vertex_count, 3))

    def vertices(self):
        for v in range(0, self.count):
            self.__v3D[v,:] = self.plane.coordinate((self.verts[v,0], self.verts[v,1]))

        return self.__v3D, self.count

    def set_vertex(self, index, xy):
        x, y = xy
        self.verts[index,:] = [x, y]

    def get_colors(self, light_vector, ambient): # vector points to light source
        brightness = self.plane.brightness(light_vector)

        r = 1 # default to white
        g = 1
        b = 1
        if self.props is not None:
            color = self.props['color']
            if color is not None:
                r, g, b = color
        r = r * ambient + (1 - ambient) * brightness
        g = g * ambient + (1 - ambient) * brightness
        b = b * ambient + (1 - ambient) * brightness

        a = 1 # transparency?

        face_color = (r, g, b, a)
        edge_color = None # TODO: refractive surfaces as edges only?

        return face_color, edge_color
