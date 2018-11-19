class Material(object):

    __source = None
    __diffzone = None
    __darkzone = None
    __concrete = None
    __wood = None
    __foliage = None
    __brick = None
    __grass = None
    __glass = None
    __barrier = None

    @staticmethod
    def source():
        if Material.__source is None:
            Material.__source = Material((0,1,0,0.5))
            Material.__source.make_source(0, 10) # pure reflection; amplitude 10dB at 10m
        return Material.__source

    @staticmethod
    def diffzone():
        if Material.__diffzone is None:
            Material.__diffzone = Material((0,0,1,0.1))
            Material.__diffzone.make_refractive((0.75, 0.25))
        return Material.__diffzone

    @staticmethod
    def darkzone():
        if Material.__darkzone is None:
            Material.__darkzone = Material((0,0,0,0.5))
            Material.__darkzone.make_illustrative()
        return Material.__darkzone

    @staticmethod
    def concrete():
        if Material.__concrete is None:
            Material.__concrete = Material((1,1,1,1))
            Material.__concrete.make_reflective(0.1) # very low absorption
        return Material.__concrete

    @staticmethod
    def wood():
        if Material.__wood is None:
            Material.__wood = Material((0.596, 0.412, 0.376, 1))
            Material.__wood.make_reflective(0.5) # medium absorption
        return Material.__wood

    @staticmethod
    def foliage():
        if Material.__foliage is None:
            Material.__foliage = Material((0, 0.5, 0, 0.75))
            Material.__foliage.make_refractive((0.25, 0.25))
        return Material.__foliage

    @staticmethod
    def brick():
        if Material.__brick is None:
            Material.__brick = Material((0.7,0.1,0,1))
            Material.__brick.make_reflective(0.2) # low absorption
        return Material.__brick

    @staticmethod
    def grass():
        if Material.__grass is None:
            Material.__grass = Material((0,0.5,0,1))
            Material.__grass.make_reflective(1) # total absorption
        return Material.__grass

    @staticmethod
    def glass():
        if Material.__glass is None:
            Material.__glass = Material((0,0,1,0.25))
            Material.__glass.make_reflective(0.2) # low absorption
        return Material.__glass

    @staticmethod
    def barrier():
        if Material.__barrier is None:
            Material.__barrier = Material((0.1,0.1,0.1,0.5))
            Material.__barrier.make_reflective(0.9) # high absorption
        return Material.__barrier

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

    def make_source(self, absorption, amplitude): # 1 = total absorption; amplitude reference dB at 10m
        self._source = True
        self._amplitude = amplitude
        self._reflective = True
        self._refractive = False
        self._absorption = absorption
        self._illustrative = False

    def amplitude(self): # amplitude reference dB at 10m
        return self._amplitude

    def is_reflective(self):
        return self._reflective

    def make_reflective(self, absorption): # 1 = total absorption
        self._source = False
        self._amplitude = 0
        self._reflective = True
        self._refractive = False
        self._absorption = absorption
        self._illustrative = False

    def is_refractive(self):
        return self._refractive

    def make_refractive(self, absorption): # where absorption=(transmitted,refracted)
        self._source = False
        self._amplitude = 0
        self._reflective = False
        self._refractive = True
        self._absorption = absorption
        self._illustrative = False

    def is_illustrative(self):
        return self._illustrative

    def make_illustrative(self):
        self._source = False
        self._amplitude = 0
        self._reflective = False
        self._refractive = False
        self._absorption = 0
        self._illustrative = True
