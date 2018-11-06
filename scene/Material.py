class Material(object):

    def __init__(self, color=None):
        self._color = color      # 4-color (r, g, b, a) or None
        self._source = False
        self._reflective = False
        self._refractive = False
        self._absorption = 0     # 1 = total absorption
        self._illustrative = False

    def absorption(self):        # 1 = total absorption
        return self._absorption

    def color(self, ambient, brightness):
        c = self._color

        if (self._reflective and not self._source) or self._refractive or self._illustrative:
            if self._color is not None:
                if brightness < 0:
                    if self._reflective:
                        brightness = 0
                    else:
                        brightness = -brightness
                r, g, b, a = self._color
                r = r * ambient + (1 - ambient) * brightness
                g = g * ambient + (1 - ambient) * brightness
                b = b * ambient + (1 - ambient) * brightness
                c = (r, g, b, a)

        return c

    def set_color(self, color):  # 4-color (r, g, b, a) or None
        self._color = color

    def is_source(self):
        return self._source

    def make_source(self, absorption):     # 1 = total absorption
        self._source = True
        self._reflective = True
        self._refractive = False
        self._absorption = absorption
        self._illustrative = False

    def is_reflective(self):
        return self._reflective

    def make_reflective(self, absorption): # 1 = total absorption
        self._source = False
        self._reflective = True
        self._refractive = False
        self._absorption = absorption
        self._illustrative = False

    def is_refractive(self):
        return self._refractive

    def make_refractive(self):
        self._source = False
        self._reflective = False
        self._refractive = True
        self._absorption = 0
        self._illustrative = False

    def is_illustrative(self):
        return self._illustrative

    def make_illustrative(self):
        self._source = False
        self._reflective = False
        self._refractive = False
        self._absorption = 0
        self._illustrative = True
