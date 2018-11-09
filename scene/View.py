import numpy as np

import Polygon

class View(object):

    def __init__(self, space, receiver, origin, window):
        self._space = space
        self._receiver = receiver
        self._origin = np.copy(origin)
        self._window = window
        self._target = None
        self._visibles = None

    def __search_space(self):
        self._visibles = []

        for p in self._space.polygons:
            # Immediately discard any non-real surfaces
            if p.ill_only is not None:
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
                self._visibles.append(pp) # although it may be occluded

    def __remove_occluded(self):
        iv1 = 0
        while (iv1 < len(self._visibles)) and (len(self._visibles) > 1):
            poly1_is_occluded = False

            poly1, proj1 = self._visibles[iv1]
            for iv2 in range(0, len(self._visibles)):
                if iv1 == iv2:
                    continue
                poly2, proj2 = self._visibles[iv2]

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
                del self._visibles[iv1]
            else:
                iv1 += 1

    def __refine(self):
        subviews = []
        resolved = []

        if len(self._visibles) == 0: # can't see anything
            return subviews, resolved

        self.__remove_occluded() # remove any obviously occluded polygons

        if len(self._visibles) == 1: # can see only one thing; restrict view & return
            poly, proj = self._visibles[0]
            self._window = poly
            self._target = proj
            resolved.append(self)
            return subviews, resolved

        # TODO:
        # - search for/through poly edges that divide the window, and select the one with the nearest vertice(s)
        # - split the window in two and refine the set of self._visibles, etc.

        return subviews, resolved

    def search(self):
        # self._target should be None at this point

        self.__search_space()

        resolved = []
        subviews = [self]

        while len(subviews) > 0:
            subview = subviews.pop(0)
            refined_subviews, refined_resolved = subview.__refine()
            subviews += refined_subviews # __refine() will drop the view as empty; or move itself to resolved
            resolved += refined_resolved # if reduced to a single visible; or it will divide into two subviews

        for rv in resolved:
            poly, proj = rv._visibles[0]       # each resolved view should have one and only one visible
            poly.ill_only = poly.plane.basis_k # offset the polygon and make it illustrative only
            self._space.add_poly(poly)

        return resolved
