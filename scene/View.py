import numpy as np

class View(object):

    def __init__(self, space, receiver, origin, window):
        self._space = space
        self._receiver = receiver
        self._origin = np.copy(origin)
        self._window = window

    def search(self):
        subviews = []
        # TODO
        return subviews
