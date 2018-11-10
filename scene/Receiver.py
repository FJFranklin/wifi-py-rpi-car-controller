import numpy as np

import View

class Receiver(object):

    def __init__(self, space, origin, cube_dimension, material):
        self._origin = np.copy(origin)
        self._space = space
        self._views = []

        polygons = space.cube(self._origin, cube_dimension, material, True)
        for p in polygons:
            self._views.append(View.View(self._origin, p))

    def search(self, show_projections=False):
        resolved = []

        for v in self._views:
            resolved += v.search(self._space.polygons)
        self._views = resolved

        if show_projections:
            for rv in resolved:
                poly = rv.region.window
                poly.ill_only = poly.plane.basis_k # make the polygon illustrative only and offset it
                self._space.add_poly(poly)
