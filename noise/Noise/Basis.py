import numpy as np

class Basis(object):

    __resolution = 1E-9
    __eqdecimals = 9 # how many decimals to round off to for relative coordinates

    def __init__(self, basis=None, transform=None):
        if basis is not None:
            self.origin = basis.origin.copy()
            if transform is not None:
                self.matrix = np.asmatrix(transform) * basis.matrix
            else:
                self.matrix = basis.matrix.copy()
        else:
            self.origin = np.matrix([[0,0,0]])
            self.matrix = np.matrix([[1,0,0],[0,1,0],[0,0,1]])

    @staticmethod
    def using(origin_abs, ei, ej, ek):
        basis = Basis()

        basis.origin = np.matrix(origin_abs)
        basis.matrix = np.matrix([ei, ej, ek])

        return basis

    @staticmethod
    def set_resolution(decimals):
        Basis.__eqdecimals = decimals
        Basis.__resolution = 10**(-decimals)

    @staticmethod
    def is_positive(value):
        return value > -Basis.__resolution

    @staticmethod
    def is_negative(value):
        return value < Basis.__resolution

    @staticmethod
    def is_strictly_positive(value):
        return value > Basis.__resolution

    @staticmethod
    def is_strictly_negative(value):
        return value < -Basis.__resolution

    def rel_to_abs(self, coord_rel):
        return np.asarray(self.origin + np.asmatrix(coord_rel) * self.matrix)

    def abs_to_rel(self, coord_abs):
        mat_abs = (np.asmatrix(coord_abs) - self.origin) * self.matrix.getT()

        if Basis.__eqdecimals > 0:
            mat_abs = np.around(mat_abs, decimals=Basis.__eqdecimals)

        return np.asarray(mat_abs)

    def e_i(self):
        return np.asarray(self.matrix[0,:])[0]

    def e_j(self):
        return np.asarray(self.matrix[1,:])[0]

    def e_k(self):
        return np.asarray(self.matrix[2,:])[0]

    @staticmethod
    def separation(coord_1, coord_2): # distance between two points; can be abs or rel, so long as the bases are the same
        dp = np.linalg.norm(coord_2 - coord_1)

        if Basis.__resolution > 0:
            if dp < 2 * Basis.__resolution:
                dp = 0

        return dp

    def offset(self, offset_origin_rel):
        basis = Basis(self)
        basis.origin = self.rel_to_abs(offset_origin_rel)

        return basis

    def jki(self, offset_origin_rel=None):
        basis = Basis(self, [[0,1,0],[0,0,1],[1,0,0]])

        if offset_origin_rel is not None:
            basis.origin = self.rel_to_abs(offset_origin_rel)

        return basis

    def rotate_i(self, angle, offset_origin_rel=None): # angle [degrees] anti-clockwise rotation of self about self.i; optionally offset the origin
        if angle == 90:
            basis = Basis(self, [[1,0,0],[0,0,1],[0,-1,0]])
        elif angle == 180:
            basis = Basis(self, [[1,0,0],[0,-1,0],[0,0,-1]])
        elif angle == 270:
            basis = Basis(self, [[1,0,0],[0,0,-1],[0,1,0]])
        elif angle:
            sin_theta = np.sin(angle * np.pi / 180)
            cos_theta = np.cos(angle * np.pi / 180)

            basis = Basis(self, [[1,0,0],[0,cos_theta,sin_theta],[0,-sin_theta,cos_theta]])

        if offset_origin_rel is not None:
            basis.origin = self.rel_to_abs(offset_origin_rel)

        return basis

    def rotate_j(self, angle, offset_origin_rel=None): # angle [degrees] anti-clockwise rotation of self about self.j; optionally offset the origin
        if angle == 90:
            basis = Basis(self, [[0,0,-1],[0,1,0],[1,0,0]])
        elif angle == 180:
            basis = Basis(self, [[-1,0,0],[0,1,0],[0,0,-1]])
        elif angle == 270:
            basis = Basis(self, [[0,0,1],[0,1,0],[-1,0,0]])
        elif angle:
            sin_theta = np.sin(angle * np.pi / 180)
            cos_theta = np.cos(angle * np.pi / 180)

            basis = Basis(self, [[cos_theta,0,-sin_theta],[0,1,0],[sin_theta,0,cos_theta]])

        if offset_origin_rel is not None:
            basis.origin = self.rel_to_abs(offset_origin_rel)

        return basis

    def rotate_k(self, angle, offset_origin_rel=None): # angle [degrees] anti-clockwise rotation of self about self.k; optionally offset the origin
        if angle == 90:
            basis = Basis(self, [[0,1,0],[-1,0,0],[0,0,1]])
        elif angle == 180:
            basis = Basis(self, [[-1,0,0],[0,-1,0],[0,0,1]])
        elif angle == 270:
            basis = Basis(self, [[0,-1,0],[1,0,0],[0,0,1]])
        elif angle:
            sin_theta = np.sin(angle * np.pi / 180)
            cos_theta = np.cos(angle * np.pi / 180)

            basis = Basis(self, [[cos_theta,sin_theta,0],[-sin_theta,cos_theta,0],[0,0,1]])

        if offset_origin_rel is not None:
            basis.origin = self.rel_to_abs(offset_origin_rel)

        return basis
