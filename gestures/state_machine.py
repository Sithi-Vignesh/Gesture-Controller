from config import TAP_THRESHOLD, RELEASE_THRESHOLD, MIN_DRAG_DISPLACEMENT


class StateMachine:
    def __init__(self):
        self._active = {}
        self._release_counter = {}

    def _get_position(self, hands, gesture):
        if gesture == "right_pinch":
            if hands["right"] is None:
                return None
            return (hands["right"][8]["x"], hands["right"][8]["y"])
        elif gesture == "right_fist":
            if hands["right"] is None:
                return None
            return (hands["right"][9]["x"], hands["right"][9]["y"])
        elif gesture == "right_peace":
            if hands["right"] is None:
                return None
            return (hands["right"][9]["x"], hands["right"][9]["y"])
        elif gesture == "right_l_shape":
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

            self._release_counter.pop(gesture, None)

            if gesture not in self._active:
                self._active[gesture] = {
                    "neutral_x": pos[0],
                    "neutral_y": pos[1],
                    "frames": 1,
                    "is_drag": False
                }
            else:
                self._active[gesture]["frames"] += 1
                frames = self._active[gesture]["frames"]

                if frames > TAP_THRESHOLD:
                    delta_x = pos[0] - self._active[gesture]["neutral_x"]
                    delta_y = pos[1] - self._active[gesture]["neutral_y"]
                    displacement = (delta_x**2 + delta_y**2) ** 0.5

                    if displacement >= MIN_DRAG_DISPLACEMENT:
                        self._active[gesture]["is_drag"] = True
                        actions.append({
                            "action": "drag_hold",
                            "gesture": gesture,
                            "delta_x": delta_x,
                            "delta_y": delta_y
                        })

        for gesture in list(self._active.keys()):
            if gesture not in stableGestures:
                self._release_counter[gesture] = self._release_counter.get(gesture, 0) + 1

                if self._release_counter[gesture] >= RELEASE_THRESHOLD:
                    was_drag = self._active[gesture]["is_drag"]

                    if was_drag:
                        actions.append({"action": "drag_end", "gesture": gesture})
                    else:
                        actions.append({"action": "tap", "gesture": gesture})

                    del self._active[gesture]
                    del self._release_counter[gesture]

        return actions