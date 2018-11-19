import numpy as np

from .Material import Material
from .View import View

class Receiver(object):

    def __init__(self, space, origin, poly, material=None):
        self.space = space
        self.sources = None

        if material is not None:
            self.material = material
        else:
            self.material = Material.darkzone()

        poly.props['absorption'] = 0

        self._views = [View(origin, poly)]

    def search(self, iterations, drop_if, show_projections=False):
        self.sources = []

        for it in range(0, iterations):
            resolved = []

            while len(self._views) > 0:
                v = self._views.pop(0)
                resolved += v.search(self.space.polygons) # , self.space) # for adding polygons if necessary

            dropped = 0

            while len(resolved) > 0:
                v = resolved.pop(0)

                material = v.region.target.props['material']

                if material.is_source():
                    if show_projections:
                        v.show_history(self.space)
                    self.sources.append(v.copy())

                if material.is_refractive():
                    tv, rv = v.refract_view()
                    #self.space.cube(rv.region.origin, 0.1, self.material, True)
                    if tv.region.window.props['absorption'] > drop_if:
                        dropped += 1
                    else:
                        self._views.append(tv) # through-view
                    if rv.region.window.props['absorption'] > drop_if:
                        dropped += 1
                    else:
                        self._views.append(rv) # refracted view
                elif material.is_reflective():
                    if v.region.window.props['absorption'] > drop_if:
                        dropped += 1
                    else:
                        self._views.append(v.reflect_view())

            print("Sources (total): " + str(len(self.sources)) + '; views dropped (this iteration): ' + str(dropped))

    def calc(self):
        total = 0

        if self.sources is None:
            print('You need to search() before you can calc()')
            return total

        for s in self.sources:
            dB = s.dB_calc()
            # print('  dB: ' + str(dB))
            total += np.power(10, dB / 10)

        if total > 0:
            total = 10 * np.log10(total)
            print('Total: '+str(total)+' dB')

        return total
