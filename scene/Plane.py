import numpy as np

class Plane(object):

    def __init__(self, origin, axes=None):
        self.origin = np.copy(origin)

        if axes is not None:
            self.basis_i = np.copy(axes[0,0:3])
            self.basis_j = np.copy(axes[1,0:3])
            self.basis_k = np.copy(axes[2,0:3])
        else:
            self.basis_i = np.asarray([1,0,0])
            self.basis_j = np.asarray([0,1,0])
            self.basis_k = np.asarray([0,0,1])

    def reverse(self):
        #plane = Plane(self.origin,np.asarray([self.basis_i,self.basis_j,self.basis_k]))
        plane = Plane(self.origin)

        plane.basis_i = np.copy( self.basis_i)
        plane.basis_j = np.copy(-self.basis_j)
        plane.basis_k = np.copy(-self.basis_k)

        return plane

    def jki(self, origin):
        plane = Plane(origin)

        plane.basis_i[:] = self.basis_j
        plane.basis_j[:] = self.basis_k
        plane.basis_k[:] = self.basis_i

        return plane

    def coordinate(self, xy):
        x, y = xy # in-plane coordinates

        return self.origin + x * self.basis_i + y * self.basis_j

    def project(self, xyz):
        pos = xyz - self.origin

        local_x = np.dot(pos, self.basis_i)
        local_y = np.dot(pos, self.basis_j)
        local_z = np.dot(pos, self.basis_k)

        return (local_x, local_y), local_z

    def reflect(self, xyz):
        local_z = np.dot(xyz - self.origin, self.basis_k)
        return xyz - 2 * local_z * self.basis_k

    def brightness(self, light_vector):
        return np.dot(self.basis_k, light_vector)
