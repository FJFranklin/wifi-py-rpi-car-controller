import numpy as np

import View

class Receiver(object):

    def __init__(self, space, origin, cube_dimension, material):
        self._origin = np.copy(origin)
        self._space = space
        self._views = []

        polygons = space.cube(self._origin, cube_dimension, material, False)
        for p in polygons:
            self._views.append(View.View(space, self, self._origin, p))

    def search(self):
        subviews = []
        for v in self._views:
            subviews += v.search()
        self._views = subviews
