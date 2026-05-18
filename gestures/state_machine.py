class StateMachine:
    def __init__(self):
        self._active = {}

    def _get_position(self, hands, gesture):
        if gesture == "right_pinch":
            if hands["right"] is None:
                return None
            return (hands["right"][8]["x"], hands["right"][8]["y"])
        elif gesture == "right_fist":
            if hands["right"] is None:
                return None
            return (hands["right"][9]["x"], hands["right"][9]["y"])
        else:
            if hands["left"] is None:
                return None
            return (hands["left"][9]["x"], hands["left"][9]["y"])

    def update(self, stableGestures, hands):
        actions = []

        for gesture in stableGestures:
            pos = self._get_position(hands, gesture)
            if pos is None:
                continue
            if gesture not in self._active:
                self._active[gesture] = {"neutral_x": pos[0], "neutral_y": pos[1]}
            else:
                delta_x = pos[0] - self._active[gesture]["neutral_x"]
                delta_y = pos[1] - self._active[gesture]["neutral_y"]
                actions.append({
                    "action": "drag_hold",
                    "gesture": gesture,
                    "delta_x": delta_x,
                    "delta_y": delta_y
                })

        ended = [g for g in self._active if g not in stableGestures]
        for gesture in ended:
            del self._active[gesture]
            actions.append({"action": "drag_end", "gesture": gesture})

        return actions