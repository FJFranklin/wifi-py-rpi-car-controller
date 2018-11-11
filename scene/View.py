import numpy as np

from Visible import Visible

class View(object):

    def __init__(self, origin, window, visibles=None):
        self.region = Visible(np.copy(origin), window)
        self.parent = None

        if visibles is not None:
            self._visibles = visibles.copy()
        else:
            self._visibles = None

    def copy(self):
        view = View(self.region.origin, self.region.window, self._visibles)
        view.region.target = self.region.target
        view.parent = self.parent
        return view

    def __search_polygons(self, polygons):
        self._visibles = []

        for p in polygons:
            # Immediately discard any non-real surfaces
            if p.ill_only is not None:
                continue

            # Let's see where we are relative to the polygon
            local_xy, local_z = p.plane.project(self.region.origin)
            if local_z == 0:
                continue # we're in the plane - ignore

            if (local_z < 0) and p.material.is_reflective():
                continue # we're behind the (reflective) plane - ignore

            # Let's check the polygon relative to our window
            pp = self.region.window.project_and_crop(self.region.origin, p)
            if pp is not None:
                poly, proj = pp
                self._visibles.append(Visible(self.region.origin, poly, proj)) # although it may be occluded

    def __refine_visibles(self):
        visibles = []

        for v in self._visibles:
            crop_v = self.region.crop_visible(v)

            if crop_v is not None:
                visibles.append(crop_v) # although it may be occluded

        self._visibles = visibles

    def __remove_occluded(self):
        iv1 = 0
        while (iv1 < len(self._visibles)) and (len(self._visibles) > 1):
            poly1_is_occluded = False

            v1 = self._visibles[iv1]
            for iv2 in range(0, len(self._visibles)):
                if iv1 == iv2:
                    continue
                v2 = self._visibles[iv2]

                # check to see if poly1 is contained within poly2
                is_exterior, is_interior, is_farther = v2.compare_visible(v1)
                if is_interior and is_farther:
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
            self.region = self._visibles[0]
            self._visibles = None
            resolved.append(self)
            return subviews, resolved

        # search for/through poly edges that divide the window, and select the one with the nearest vertice(s)

        v1_best = None # 2D coordinates
        v2_best = None
        d1_best = 0    # distance in 3D space
        d2_best = 0

        for v in self._visibles:
            v1, d1, v2, d2 = self.region.nearest_intersection(v)

            if v1 is None: # no valid edge found
                continue

            if (v1_best is None) or ((d1 < d1_best) or ((d1 == d1_best) and (d2 < d2_best))):
                v1_best = v1
                v2_best = v2
                d1_best = d1
                d2_best = d2

        # split the window in two and refine the set of self._visibles, etc.

        view = self.copy()

        self.region.window = self.region.window.split(v1_best, v2_best)
        self.__refine_visibles()
        subviews.append(self)

        view.region.window = view.region.window.split(v2_best, v1_best)
        view.__refine_visibles()
        subviews.append(view)

        return subviews, resolved

    def search(self, polygons):
        # self._target should be None at this point

        self.__search_polygons(polygons)

        resolved = []
        subviews = [self]

        while len(subviews) > 0:
            subview = subviews.pop(0)
            refined_subviews, refined_resolved = subview.__refine()
            subviews += refined_subviews # __refine() will drop the view as empty; or move itself to resolved
            resolved += refined_resolved # if reduced to a single visible; or it will divide into two subviews

        return resolved

    def reflect_view(self):
        origin = self.region.target.plane.reflect(self.region.origin)

        window = self.region.target

        child = View(origin, window)
        child.parent = self
        return child

    def refract_view(self, scale=0.1):
        center = self.region.target.center()
        origin = self.region.target.plane.reflect(center - self.region.origin) * scale + center

        window = self.region.target
        xy_w, z_w = window.plane.project(origin)
        if z_w > 0:
            window = window.reverse()

        child = View(origin, window)
        child.parent = self
        return child