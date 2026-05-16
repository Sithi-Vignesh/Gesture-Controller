# gestures/state_machine.pyhiw 

class StateMachine:
    def __init__(self):
        self._state = "IDLE"
        self._gesture = None
        self._x = None
        self._y = None

    def _get_position(self, hands, gesture):
        if gesture == "right_pinch":
            return (hands["right"][8]["x"],hands["right"][8]["y"])
        elif gesture == "right_fist":
            return (hands["right"][9]["x"],hands["right"][9]["y"])
        else:
            return (hands["left"][9]["x"],hands["left"][9]["y"])
    
        
    def update(self, stableGestures, hands):
        if self._state == "IDLE":
            if not stableGestures:
                return None
            else:
                self._gesture = stableGestures[0]
                self._state = "GESTURE_START"
                self._x, self._y = self._get_position(hands, self._gesture)
                return {"action": "drag_start", "x": self._x, "y": self._y}
            
        elif self._state in ("GESTURE_START", "GESTURE_HOLD"):
            if not stableGestures:
                self._state = "IDLE"
                return {"action": "drag_end"}
            else:
                if self._gesture == stableGestures[0]:
                    x2, y2 = self._get_position(hands, self._gesture)
                    x1 = self._x
                    y1 = self._y
                    self._x = x2
                    self._y = y2
                    self._state = "GESTURE_HOLD"
                    return {"action": "drag_hold", "x1": x1, "y1": y1, "x2": x2, "y2": y2}
                
                else:
                    self._state = "IDLE"
                    return {"action": "drag_end"}