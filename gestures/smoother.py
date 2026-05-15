from collections import deque

possible = ["left_fist", "right_fist", "right_pinch"]

class GestureSmoother:
    def __init__(self, window_size):
        self._history = deque(maxlen=window_size)

    def update(self, gestures):
        self._history.append(gestures)
        stable = []
        for gesture in possible:
            x = sum(gesture in entry for entry in self._history)
            if x > len(self._history)/2 : stable.append(gesture)
        return stable
    