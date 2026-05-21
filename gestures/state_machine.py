TAP_THRESHOLD = 4


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

        # Handle active and new gestures
        for gesture in stableGestures:
            pos = self._get_position(hands, gesture)
            if pos is None:
                continue

            # Reset release counter since gesture is present
            self._release_counter.pop(gesture, None)

            if gesture not in self._active:
                # First frame — register neutral position, start frame count
                self._active[gesture] = {
                    "neutral_x": pos[0],
                    "neutral_y": pos[1],
                    "frames": 1
                }
            else:
                self._active[gesture]["frames"] += 1
                frames = self._active[gesture]["frames"]

                if frames > TAP_THRESHOLD:
                    # It's a drag
                    delta_x = pos[0] - self._active[gesture]["neutral_x"]
                    delta_y = pos[1] - self._active[gesture]["neutral_y"]
                    actions.append({
                        "action": "drag_hold",
                        "gesture": gesture,
                        "delta_x": delta_x,
                        "delta_y": delta_y
                    })

        # Handle gestures not seen this frame
        for gesture in list(self._active.keys()):
            if gesture not in stableGestures:
                self._release_counter[gesture] = self._release_counter.get(gesture, 0) + 1

                if self._release_counter[gesture] >= TAP_THRESHOLD:
                    # Confirmed release
                    frames_held = self._active[gesture]["frames"]
                    if frames_held <= TAP_THRESHOLD:
                        actions.append({"action": "tap", "gesture": gesture})
                    else:
                        actions.append({"action": "drag_end", "gesture": gesture})

                    del self._active[gesture]
                    del self._release_counter[gesture]

        return actions