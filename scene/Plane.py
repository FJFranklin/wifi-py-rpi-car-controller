import numpy as np

class Plane(object):

    def __init__(self, origin, axes):
        self.origin = np.copy(origin)

        self.basis_i = np.copy(axes[0,0:3])
        self.basis_j = np.copy(axes[1,0:3])
        self.basis_k = np.copy(axes[2,0:3])

    def coordinate(self, xy):
        x, y = xy # in-plane coordinates

        return self.origin + x * self.basis_i + y * self.basis_j

    def project(self, xyz):
        pos = xyz - self.origin

        local_x = np.dot(pos, self.basis_i)
        local_y = np.dot(pos, self.basis_j)
        local_z = np.dot(pos, self.basis_k)

        return (local_x, local_y), local_z

    def brightness(self, light_vector):
        b = np.dot(self.basis_k, light_vector)
        if b < 0:
            b = 0
        return b
