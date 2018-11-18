import numpy as np

from .View import View

class Receiver(object):

    def __init__(self, space, origin, poly, material):
        self.space = space
        self.material = material

        poly.props['absorbed'] = 0

        self._views = [View(origin, poly)]

    def search(self, iterations, show_projections=False):
        sources = []

        for it in range(0, iterations):
            resolved = []

            while len(self._views) > 0:
                v = self._views.pop(0)
                resolved += v.search(self.space.polygons) # , self.space) # for adding polygons if necessary

            while len(resolved) > 0:
                v = resolved.pop(0)

                material = v.region.target.props['material']

                if material.is_source():
                    if show_projections:
                        v.show_history(self.space)
                    sources.append(v.copy())

                if material.is_refractive():
                    tv, rv = v.refract_view()
                    #self.space.cube(rv.region.origin, 0.1, self.material, True)
                    self._views.append(tv) # through-view
                    self._views.append(rv) # refracted view
                elif material.is_reflective():
                    self._views.append(v.reflect_view())

            print("Sources total: " + str(len(sources)))
