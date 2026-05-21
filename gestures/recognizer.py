import math
from config import FIST_THRESHOLD, PINCH_THRESHOLD

class GestureRecognizer:
    def _distance(self, a, b):
        return math.sqrt((a["x"] - b["x"])**2 + (a["y"] - b["y"])**2 + (a["z"] - b["z"])**2)
    
    def is_fist(self, landmarks):
        knuckles = [landmarks[5], landmarks[9], landmarks[13], landmarks[17]]
        tips = [landmarks[8], landmarks[12], landmarks[16], landmarks[20]]
        c = 0
        for i in range(4):
            if self._distance(tips[i], knuckles[i]) < FIST_THRESHOLD:
                c += 1
        return c == 4

    def is_pinch(self, landmarks):
        return self._distance(landmarks[4], landmarks[8]) < PINCH_THRESHOLD

    def is_peace(self, landmarks):
        # Index and middle extended
        index_extended = self._distance(landmarks[8], landmarks[5]) > FIST_THRESHOLD
        middle_extended = self._distance(landmarks[12], landmarks[9]) > FIST_THRESHOLD
        # Ring and pinky curled
        ring_curled = self._distance(landmarks[16], landmarks[13]) < FIST_THRESHOLD
        pinky_curled = self._distance(landmarks[20], landmarks[17]) < FIST_THRESHOLD
        return index_extended and middle_extended and ring_curled and pinky_curled

    def is_l_shape(self, landmarks):
        # Thumb extended: tip (4) far from base (2)
        thumb_extended = self._distance(landmarks[4], landmarks[2]) > FIST_THRESHOLD
        # Index extended: tip (8) far from knuckle (5)
        index_extended = self._distance(landmarks[8], landmarks[5]) > FIST_THRESHOLD
        # Middle, ring, pinky curled
        knuckles = [landmarks[9], landmarks[13], landmarks[17]]
        tips = [landmarks[12], landmarks[16], landmarks[20]]
        others_curled = all(self._distance(tips[i], knuckles[i]) < FIST_THRESHOLD for i in range(3))
        return thumb_extended and index_extended and others_curled

    def recognize(self, hands):
        gestures = []
        if hands["left"] is not None:
            if self.is_fist(hands["left"]):
                gestures.append("left_fist")
        
        if hands["right"] is not None:
            fist = self.is_fist(hands["right"])
            if fist:
                gestures.append("right_fist")
            else:
                if self.is_pinch(hands["right"]):
                    gestures.append("right_pinch")
                elif self.is_peace(hands["right"]):
                    gestures.append("right_peace")
                elif self.is_l_shape(hands["right"]):
                    gestures.append("right_l_shape")
        
        return gestures