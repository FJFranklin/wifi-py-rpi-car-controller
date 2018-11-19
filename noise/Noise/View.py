import numpy as np

from .Plane import Plane
from .Polygon import Polygon
from .Visible import Visible

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
        if self.region.target is not None:
            view.region.target = self.region.target.copy()
        else:
            view.region.target = None
        view.parent = self.parent
        return view

    def __search_polygons(self, polygons, space):
        self._visibles = []

        for p in polygons:
            # Immediately discard any non-real surfaces
            if 'ill_only' in p.props:
                continue

            # Let's see where we are relative to the polygon
            local_xy, local_z = p.plane.project(self.region.origin)
            if local_z == 0:
                continue # we're in the plane - ignore

            if (local_z < 0) and p.props['material'].is_reflective():
                continue # we're behind the (reflective) plane - ignore

            # Let's check the polygon relative to our window
            pp = self.region.window.project_and_crop(self.region.origin, p)
            if pp is not None:
                poly, proj = pp
                if poly is None:
                    print('Error: No window')
                if proj is None:
                    print('Error: No target')
                if space is not None:
                    proj.props['offset'] = proj.plane.normal()
                    proj.props['ill_only'] = True
                    space.add_poly(proj)
                self._visibles.append(Visible(self.region.origin, poly, proj)) # although it may be occluded

    def __refine_visibles(self):
        visibles = []

        for v in self._visibles:
            crop_v = self.region.crop_visible(v)

            if crop_v is not None:
                visibles.append(crop_v) # although it may be occluded

        self._visibles = visibles

    def __remove_occluded(self, printing=False):
        iv1 = 0
        while (iv1 < len(self._visibles) - 1) and (len(self._visibles) > 1):
            poly1_is_occluded = False
            poly2_deleted = False

            v1 = self._visibles[iv1]

            for iv2 in range(iv1+1, len(self._visibles)):
                v2 = self._visibles[iv2]

                # check to see if poly1 is contained within poly2
                v1_exterior, v1_interior, v1_farther, v1_coplanar = v2.compare_visible(v1, printing)
                if printing:
                    print('Exterior: '+str(v1_exterior)+', Interior: '+str(v1_interior)+', Farther: '+str(v1_farther)+', Coplanar: '+str(v1_coplanar))
                if v1_interior and v1_farther:
                    poly1_is_occluded = True
                    break
                if v1_interior and v1_coplanar:
                    print('Error: interior-coplanar polygons?')

                # check to see if poly2 is contained within poly1
                v2_exterior, v2_interior, v2_farther, v2_coplanar = v1.compare_visible(v2, printing)
                if printing:
                    print('Exterior: '+str(v2_exterior)+', Interior: '+str(v2_interior)+', Farther: '+str(v2_farther)+', Coplanar: '+str(v2_coplanar))
                if v2_interior and v2_farther:
                    del self._visibles[iv2]
                    poly2_deleted = True
                    break
                if v2_interior and v2_coplanar:
                    print('Error: interior-coplanar polygons?')
                if v1_interior and v2_interior:
                    print('Error: intersecting polygons? removing one...')
                    print(v1.target.vertices())
                    print(v2.target.vertices())
                    del self._visibles[iv2]
                    poly2_deleted = True
                    break

            if poly1_is_occluded:
                del self._visibles[iv1]
            elif not poly2_deleted:
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

        if v1_best is None: # no valid edge found
            print('View:')
            print(self.region.window.verts)
            print('Visibles:')
            for v in self._visibles:
                print(v.window.verts)
            print('Occlusions:')
            self.__remove_occluded(True) # remove any obviously occluded polygons
            print('* * * Removing View - Critical Error * * *')
            return subviews, resolved

        # split the window in two and refine the set of self._visibles, etc.

        view = self.copy()

        self.region.window = self.region.window.split(v1_best, v2_best)
        if self.region.window is None:
            print('Warning: Split failed (self)')
        else:
            self.__refine_visibles()
            subviews.append(self)

        view.region.window = view.region.window.split(v2_best, v1_best)
        if view.region.window is None:
            print('Warning: Split failed (view)')
        else:
            view.__refine_visibles()
            subviews.append(view)

        return subviews, resolved

    def search(self, polygons, space=None):
        # self._target should be None at this point

        self.__search_polygons(polygons, space)

        resolved = []
        subviews = [self]

        while len(subviews) > 0:
            subview = subviews.pop(0)
            refined_subviews, refined_resolved = subview.__refine()
            subviews += refined_subviews # __refine() will drop the view as empty; or move itself to resolved
            resolved += refined_resolved # if reduced to a single visible; or it will divide into two subviews

        return resolved

    def reflect_view(self):
        material = self.region.target.props['material']
        absorption = material.absorption()

        abs_prior = self.region.window.props['absorption']
        abs_new = 1 - (1 - absorption) * (1 - abs_prior)
        
        window = self.region.target.copy()
        window.props['absorption'] = abs_new

        origin = window.plane.reflect(self.region.origin)

        child = View(origin, window)
        child.parent = self
        return child

    def refract_view(self):
        material = self.region.target.props['material']
        abs_transmitted, abs_refracted = material.absorption()

        abs_prior = self.region.window.props['absorption']
        abs_new_t = 1 - (1 - abs_transmitted) * (1 - abs_prior)
        abs_new_r = 1 - (1 - abs_refracted) * (1 - abs_prior)
        
        window = self.region.target.copy()
        window.props['absorption'] = abs_new_r

        xy_w, z_w = window.plane.project(self.region.origin)
        if z_w > 0:
            window = window.reverse()

        center = window.center()
        origin = center - np.linalg.norm(self.region.origin - center) * window.plane.normal()

        # rotate origin until directly behind the window's center
        child = View(origin, window)
        child.parent = self

        window = window.copy()
        window.props['absorption'] = abs_new_t

        # let's also treat the refractive surface as transparent
        through = View(self.region.origin, window)
        through.parent = self

        return through, child

    def show_history(self, space):
        props = self.region.target.props

        i3D, count = self.region.target.vertices()

        v = self
        while v:
            v3D = i3D
            i3D = v.region.window.intersections_3D(v.region.origin, v3D, count)

            for i2 in range(1, count):
                i1 = i2 - 1

                plane = Plane.from_points(v.region.origin, v3D[i1,:], v3D[i2,:])

                poly = Polygon(plane, 4, props)

                poly.verts[0,:], z_0 = plane.project(v3D[i1,:])
                poly.verts[1,:], z_1 = plane.project(v3D[i2,:])
                poly.verts[2,:], z_2 = plane.project(i3D[i2,:])
                poly.verts[3,:], z_3 = plane.project(i3D[i1,:])

                poly.props['ill_only'] = True
                space.add_poly(poly)

            v = v.parent

    def dB_calc(self):
        material = self.region.target.props['material']

        amplitude = material.amplitude() # reference: dB at 10m, based on 1m2 visible source
        dist_ref = 10 # reference distance = 10m

        absorption = self.region.window.props['absorption'] # very unscientific scaling (??) # FIXME
        if 1 - absorption < 1E-6:
            return 0
        surf_loss  = 10 * np.log10(1 - absorption)

        # distance:
        distance = 0
        center = self.region.target.center()
        i3D = np.asarray([center])
        count = 1

        area_scale = None

        v = self
        while v:
            v3D = i3D
            i3D = v.region.window.intersections_3D(v.region.origin, v3D, count)

            distance += np.linalg.norm(v3D[0,:] - i3D[0,:])

            if area_scale is None:
                incidence_vector = (i3D[0,:] - v3D[0,:]) / np.linalg.norm(v3D[0,:] - i3D[0,:])
                area_scale = np.dot(incidence_vector, v.region.target.plane.normal())

            v = v.parent

        area = self.region.target.area()
        area_loss = 10 * np.log10(area * area_scale)

        attenuation = 10 # [dB/km] Note: very humidity- & frequency-dependent # FIXME
        h2o_loss = -attenuation * distance / 1000 # this is loss through attenuation, not distance effect

        # distance effect
        dist_loss = -20 * np.abs(np.log10(dist_ref / distance))

        #print(str(amplitude)+' (amp) ' +
        #      str(area_loss)+' (area) '+
        #      str(surf_loss)+' (surf) '+
        #      str( h2o_loss)+' (H2O) ' +
        #      str(dist_loss)+' (dist) [dist='+str(distance)+'; area='+str(area)+']')

        return amplitude + area_loss + surf_loss + h2o_loss + dist_loss
