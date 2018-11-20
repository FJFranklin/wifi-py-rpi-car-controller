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
        totals = { }
        total = 0

        if self.sources is None:
            print('You need to search() before you can calc()')
            return totals

        for s in self.sources:
            label = s.region.target.props['material'].label()

            if label in totals:
                l_tot = totals[label]
            else:
                l_tot = 0

            dB = s.dB_calc()
            dB_pow = np.power(10, dB / 10)
            # print('  dB: ' + str(dB))
            total += dB_pow
            l_tot += dB_pow

            totals[label] = l_tot

        if total > 0:
            total = 10 * np.log10(total)
            print('Total: '+str(total)+' dB')

            for t in totals:
                subtotal = 10 * np.log10(totals[t])
                print(' - '+t+': '+str(subtotal)+' dB')
                if subtotal < 0:
                    print('* * * Error: Negative Sound Level * * *')
                    subtotal = 0
                totals[t] = subtotal

            totals['total'] = total

        return totals
