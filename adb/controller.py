import subprocess
import config
import threading
import time

MAX_DRAG = 200
SENSITIVITY = 3.0
DEV = "/dev/input/event4"

class ADBController:
    GESTURE_MAP = {"left_fist": "movement", "right_fist": "super", "right_pinch": "attack"}

    def __init__(self, phone_width, phone_height, profile):
        self.phone_width = phone_width
        self.phone_height = phone_height
        self.profile = profile
        self._lock = threading.Lock()
        self._active = {}
        self._last_sent = {}
        self._shell = subprocess.Popen(
            [config.ADB_PATH, "shell"],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    def _write(self, cmd):
        with self._lock:
            try:
                self._shell.stdin.write((cmd + "\n").encode())
                self._shell.stdin.flush()
            except:
                pass

    def _se(self, type_, code, value):
        return f"sendevent {DEV} {type_} {code} {value}"

    def _finger_down(self, x, y):
        cmds = [
            self._se(3, 58, 16),
            self._se(3, 53, x),
            self._se(3, 54, y),
            self._se(3, 57, 0),
            self._se(0, 2, 0),
            self._se(1, 330, 1),
            self._se(0, 0, 0),
        ]
        self._write(" && ".join(cmds))

    def _finger_move(self, x, y):
        cmds = [
            self._se(3, 58, 16),
            self._se(3, 53, x),
            self._se(3, 54, y),
            self._se(3, 57, 0),
            self._se(0, 2, 0),
            self._se(0, 0, 0),
        ]
        self._write(" && ".join(cmds))

    def _finger_up(self):
        cmds = [
            self._se(3, 57, -1),
            self._se(0, 2, 0),
            self._se(1, 330, 0),
            self._se(0, 0, 0),
        ]
        self._write(" && ".join(cmds))

    def send(self, action):
        gesture = action["gesture"]
        key = self.GESTURE_MAP[gesture]
        x1 = self.profile[key]["x"]
        y1 = self.profile[key]["y"]

        if action["action"] == "drag_hold":
            now = time.time()
            if gesture in self._last_sent and now - self._last_sent[gesture] < 0.1:
                return
            self._last_sent[gesture] = now

            dx = action["delta_x"] * self.phone_width * SENSITIVITY
            dy = action["delta_y"] * self.phone_height * SENSITIVITY
            dx = max(-MAX_DRAG, min(MAX_DRAG, dx))
            dy = max(-MAX_DRAG, min(MAX_DRAG, dy))
            x2 = int(x1 + dx)
            y2 = int(y1 + dy)

            if gesture not in self._active:
                self._active[gesture] = True
                self._finger_down(x1, y1)
            else:
                self._finger_move(x2, y2)

        elif action["action"] == "drag_end":
            if gesture in self._active:
                del self._active[gesture]
                self._last_sent.pop(gesture, None)
                self._finger_up()

    def stop(self):
        self._finger_up()
        time.sleep(0.1)
        try:
            self._shell.stdin.close()
            self._shell.terminate()
        except:
            pass