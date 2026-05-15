import math
from config import FIST_THRESHOLD, PINCH_THRESHOLD

class GestureRecognizer:
    def _distance(self, a, b):
        return math.sqrt((a["x"] - b["x"])**2 + (a["y"] - b["y"])**2 + (a["z"] - b["z"])**2)
    
    def is_fist(self, landmarks):
        knuckles = [landmarks[5], landmarks[9], landmarks[13], landmarks[17]]
        tips = [landmarks[8], landmarks[12], landmarks[16], landmarks[20]]
        c=0
        for i in range(0,4):
            x = self._distance(tips[i], knuckles[i])
            if x < FIST_THRESHOLD:
                c += 1
        return c == 4
    
    def is_pinch(self, landmarks):
        x = self._distance(landmarks[4], landmarks[8])
        return x < PINCH_THRESHOLD
    
    def recognize(self, hands):
        gestures = []
        if hands["left"] is not None:
            x = self.is_fist(hands["left"])
            if x: gestures.append("left_fist")
        
        if hands["right"] is not None:
            x = self.is_fist(hands["right"])
            if x: gestures.append("right_fist")
            if not x:
                y = self.is_pinch(hands["right"])
                if y: gestures.append("right_pinch")
        
        return gestures