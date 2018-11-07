import numpy as np

import Polygon

class View(object):

    def __init__(self, space, receiver, origin, window):
        self._space = space
        self._receiver = receiver
        self._origin = np.copy(origin)
        self._window = window

    def search(self):
        subviews = []
        visibles = []
        for p in self._space.polygons:
            # Immediately discard any non-real surfaces
            if p.material.is_illustrative():
                continue

            # Let's see where we are relative to the polygon
            local_xy, local_z = p.plane.project(self._origin)
            if local_z == 0:
                continue # we're in the plane - ignore

            if (local_z < 0) and p.material.is_reflective():
                continue # we're behind the (reflective) plane - ignore

            # Let's check the polygon relative to our window
            pi, pc, sc = self._window.project_and_compare(self._origin, p)
            if pi or pc or sc:
                visibles.append(p) # although it may be occluded

        return subviews
