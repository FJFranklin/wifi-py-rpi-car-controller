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
                visibles.append(pp) # although it may be occluded

        if len(visibles) == 0: # can't see anything, can't do anything
            return subviews    # it's empty at this point

        iv1 = 0
        while (iv1 < len(visibles)) and (len(visibles) > 1):
            poly1_is_occluded = False

            poly1, proj1 = visibles[iv1]
            for iv2 in range(0, len(visibles)):
                if iv1 == iv2:
                    continue
                poly2, proj2 = visibles[iv2]

                # check to see if poly1 is contained within poly2
                is_exterior, is_interior = poly2.compare_2D_poly(poly1)
                if is_interior:
                    v3D, count = proj1.vertices()
                    xy_o, z_o = proj2.plane.project(self._origin)
                    xy_1, z_1 = proj2.plane.project(v3D[0,:])
                    if z_o * z_1 < 0:
                        poly1_is_occluded = True
                        break

            if poly1_is_occluded:
                del visibles[iv1]
            else:
                iv1 += 1

        for pp in visibles:
            poly, proj = pp
            poly.ill_only = True
            self._space.add_poly(poly)

        if len(visibles) == 1: # can see only one thing; restrict view & return
            poly, proj = visibles[0]
            self._window = poly
            self._target = proj
            subviews.append(self)
            return subviews

        # TODO: new method refine():
        # - search for/through poly edges that divide the window, and select the one with the nearest vertice(s)
        # - split the window in two and refine the set of visibles, etc.

        return subviews
