import cv2
import time
import threading
from typing import Callable, Optional

from gestures.detector import HandDetector
from gestures.recognizer import GestureRecognizer
from gestures.smoother import GestureSmoother
from gestures.state_machine import StateMachine
from input.controller import EmulatorController


# ─── Display config ───────────────────────────────────────────────────────────

DISPLAY_WIDTH  = 1280
DISPLAY_HEIGHT = 720

CONNECTIONS = [
    (0,1),(1,2),(2,3),(3,4),
    (0,5),(5,6),(6,7),(7,8),
    (0,9),(9,10),(10,11),(11,12),
    (0,13),(13,14),(14,15),(15,16),
    (0,17),(17,18),(18,19),(19,20),
    (5,9),(9,13),(13,17)
]


# ─── Named exceptions ─────────────────────────────────────────────────────────

class LDPlayerNotFoundError(Exception):
    pass

class CameraNotFoundError(Exception):
    pass


# ─── Pipeline ─────────────────────────────────────────────────────────────────

class GesturePipeline:

    def __init__(self):
        self.on_frame: Optional[Callable] = None

        self._detector   = None
        self._recognizer = None
        self._smoother   = None
        self._sm         = None
        self._controller = None

        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    # ── public API ────────────────────────────────────────────────────────────

    def start(self):
        """Initialize all components and start the loop.
        Raises LDPlayerNotFoundError or CameraNotFoundError on failure.
        """
        # controller init — catches LDPlayer missing
        try:
            self._controller = EmulatorController()
        except RuntimeError:
            raise LDPlayerNotFoundError(
                "LDPlayer window not found.\n"
                "Please open LDPlayer 9 and launch Brawl Stars, then try again."
            )

        # detector init — catches camera missing
        self._detector = HandDetector()
        try:
            self._detector.start()
        except Exception:
            raise CameraNotFoundError(
                "Could not access webcam.\n"
                "Please check your camera is connected and not in use by another app."
            )

        self._recognizer = GestureRecognizer()
        self._smoother   = GestureSmoother(3)
        self._sm         = StateMachine()

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join()
            self._thread = None
        if self._detector:
            self._detector.stop()
            self._detector = None
        if self._controller:
            self._controller.stop()
            self._controller = None

    # ── private loop ──────────────────────────────────────────────────────────

    def _loop(self):
        prev_time      = 0
        stableGestures = []

        while not self._stop_event.is_set():
            hands = self._detector.read()
            frame = hands["frame"]
            if not hands["ok"]:
                continue

            frame = cv2.resize(frame, (DISPLAY_WIDTH, DISPLAY_HEIGHT))

            gestures = self._recognizer.recognize(hands)

            if hands["left"] is None and hands["right"] is None:
                stableGestures = []
            else:
                stableGestures = self._smoother.update(gestures)

            actions = self._sm.update(stableGestures, hands)
            for action in actions:
                t1 = time.time()
                self._controller.send(action)
                t2 = time.time()
                print(f"{action['action']} | {action['gesture']} | {(t2-t1)*1000:.1f}ms")

            # ── draw landmarks ────────────────────────────────────────────────
            dot_color  = {"left": (0, 255, 0),    "right": (0, 255, 0)}
            line_color = {"left": (255, 255, 255), "right": (255, 255, 255)}

            if "left_fist"     in stableGestures: dot_color["left"]  = line_color["left"]  = (255, 0, 0)
            if "right_fist"    in stableGestures: dot_color["right"] = line_color["right"] = (0, 255, 255)
            if "right_pinch"   in stableGestures: dot_color["right"] = line_color["right"] = (0, 0, 255)
            if "right_peace"   in stableGestures: dot_color["right"] = line_color["right"] = (255, 0, 255)
            if "right_l_shape" in stableGestures: dot_color["right"] = line_color["right"] = (0, 255, 0)

            for side in ["left", "right"]:
                if hands[side]:
                    for point in hands[side]:
                        cx = int(point["x"] * DISPLAY_WIDTH)
                        cy = int(point["y"] * DISPLAY_HEIGHT)
                        cv2.circle(frame, (cx, cy), 4, dot_color[side], -1)
                    for s, e in CONNECTIONS:
                        x1 = int(hands[side][s]["x"] * DISPLAY_WIDTH)
                        y1 = int(hands[side][s]["y"] * DISPLAY_HEIGHT)
                        x2 = int(hands[side][e]["x"] * DISPLAY_WIDTH)
                        y2 = int(hands[side][e]["y"] * DISPLAY_HEIGHT)
                        cv2.line(frame, (x1, y1), (x2, y2), line_color[side], 2)

            # ── FPS + gesture overlay ─────────────────────────────────────────
            curr_time = time.time()
            fps       = int(1 / (curr_time - prev_time)) if (curr_time - prev_time) > 0 else 0
            prev_time = curr_time
            text      = ", ".join(stableGestures) if stableGestures else "None"

            cv2.rectangle(frame, (10, 10), (300, 60), (0, 0, 0), -1)
            cv2.putText(
                frame, f"Gestures: {text} | FPS: {fps}",
                (15, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1
            )

            # ── deliver frame ─────────────────────────────────────────────────
            if self.on_frame:
                self.on_frame(frame)