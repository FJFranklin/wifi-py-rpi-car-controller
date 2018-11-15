import numpy as np

from .Basis import Basis

class Plane(object):

    def __init__(self, basis):
        self.basis = basis

    @staticmethod
    def from_points(P1, P2, P3): # where P1, P2, P3 are absolute coordinates; P1 & P2 determine e_i; P2 & P3 determine e_j; e_k is normal
        Bi = P2 - P1
        Bk = np.cross(Bi, P3 - P2)
        Bj = np.cross(Bk, Bi)

        return Plane(Basis.using(P1, Bi / np.linalg.norm(Bi), Bj / np.linalg.norm(Bj), Bk / np.linalg.norm(Bk)))

    def reverse(self):
        return Plane(self.basis.rotate_i(180))

    def jki(self, new_origin_abs): # new origin specified in absolute coordinates
        basis = self.basis.jki()
        basis.origin = new_origin_abs

        return Plane(basis)

    def coordinate(self, xy):
        x, y = xy # in-plane coordinates
        return self.basis.rel_to_abs([x, y, 0])

    def project(self, xyz):
        pos = self.basis.abs_to_rel(xyz)[0]
        return (pos[0], pos[1]), pos[2]

    def reflect(self, xyz):
        pos = self.basis.abs_to_rel(xyz)
        pos[0,2] = -pos[0,2]
        return self.basis.rel_to_abs(pos)[0]

    def normal(self):
        return self.basis.e_k()

    def brightness(self, light_vector):
        return np.dot(self.normal(), light_vector)
