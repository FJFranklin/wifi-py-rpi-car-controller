import numpy as np

import Polygon

class View(object):

    def __init__(self, space, receiver, origin, window):
        self._space = space
        self._receiver = receiver
        self._origin = np.copy(origin)
        self._window = window
        self._target = None

    def search(self):
        # self._target should be None at this point

        subviews = []
        visibles = []

        for p in self._space.polygons:
            # Immediately discard any non-real surfaces
            if p.ill_only:
                continue

            # Let's see where we are relative to the polygon
            local_xy, local_z = p.plane.project(self._origin)
            if local_z == 0:
                continue # we're in the plane - ignore

            if (local_z < 0) and p.material.is_reflective():
                continue # we're behind the (reflective) plane - ignore

            # Let's check the polygon relative to our window
            pp = self._window.project_and_crop(self._origin, p)
            if pp is not None:
                poly, proj = pp
                poly.ill_only = True
                self._space.add_poly(poly)
                visibles.append(pp) # although it may be occluded

        if len(visibles) == 0: # can't see anything, can't do anything
            return subviews    # it's empty at this point

        if len(visibles) == 1: # can see only one thing; restrict view & return
            poly, proj = visibles[0]
            self._window = poly
            self._target = proj
            subviews.append(self)
            return subviews

        # at this point we have multiple visibles
        # TODO: ...

        return subviews
