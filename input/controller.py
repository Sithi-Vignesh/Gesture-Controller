import pyautogui
import win32gui
from config import MOVE_SENSITIVITY, MAX_DRAG

WINDOW_TITLE = "LDPlayer"

pyautogui.PAUSE = 0

DIRECTION_KEYS = {
    ( 1,  0): ['s'],
    (-1,  0): ['w'],
    ( 0, -1): ['a'],
    ( 0,  1): ['d'],
    ( 1, -1): ['s', 'a'],
    ( 1,  1): ['s', 'd'],
    (-1, -1): ['w', 'a'],
    (-1,  1): ['w', 'd'],
}


class EmulatorController:
    def __init__(self):
        self._hwnd = win32gui.FindWindow(None, WINDOW_TITLE)
        if not self._hwnd:
            raise RuntimeError("LDPlayer window not found")
        win32gui.SetForegroundWindow(self._hwnd)
        self._pressed_keys = set()
        self._drag_origin = {}

    def _press_key(self, key):
        if key not in self._pressed_keys:
            pyautogui.keyDown(key)
            self._pressed_keys.add(key)

    def _release_key(self, key):
        if key in self._pressed_keys:
            pyautogui.keyUp(key)
            self._pressed_keys.discard(key)

    def _release_all_keys(self):
        for key in list(self._pressed_keys):
            self._release_key(key)

    def _get_direction(self, dx, dy):
        sx = 0 if abs(dy) < 0.05 else (1 if dy > 0 else -1)
        sy = 0 if abs(dx) < 0.05 else (1 if dx > 0 else -1)
        return (sx, sy)

    def _window_center(self):
        rect = win32gui.GetWindowRect(self._hwnd)
        cx = (rect[0] + rect[2]) // 2
        cy = (rect[1] + rect[3]) // 2
        return cx, cy

    def _mouse_move(self, gesture, dx, dy):
        if gesture not in self._drag_origin:
            cx, cy = self._window_center()
            pyautogui.moveTo(cx, cy)
            self._drag_origin[gesture] = (cx, cy)
        ox, oy = self._drag_origin[gesture]
        scale = MAX_DRAG * MOVE_SENSITIVITY
        tx = int(ox + dx * scale)
        ty = int(oy + dy * scale)
        pyautogui.moveTo(tx, ty)

    def _right_click_down(self, key):
        if key not in self._pressed_keys:
            pyautogui.keyDown(key)
            self._pressed_keys.add(key)

    def _right_click_up(self, key=None):
        if key:
            self._release_key(key)
        else:
            for k in ['x', 'c']:
                self._release_key(k)

    def send(self, action):
        gesture = action["gesture"]
        act = action["action"]

        if act == "tap":
            if gesture == "right_pinch":
                pyautogui.press('e')
            elif gesture == "right_fist":
                pyautogui.press('f')
            elif gesture == "right_peace":
                pyautogui.press('r')
            elif gesture == "right_l_shape":
                pyautogui.press('q')

        elif act == "drag_hold":
            dx = action["delta_x"]
            dy = action["delta_y"]

            if abs(dx) < 0.005 and abs(dy) < 0.005:
                return

            if gesture == "left_fist":
                direction = self._get_direction(dx, dy)
                keys = DIRECTION_KEYS.get(direction, [])
                for key in list(self._pressed_keys):
                    if key not in keys:
                        self._release_key(key)
                for key in keys:
                    self._press_key(key)

            elif gesture == "right_pinch":
                if gesture not in self._drag_origin:
                    cx, cy = self._window_center()
                    pyautogui.moveTo(cx, cy)
                self._right_click_down('x')
                self._mouse_move(gesture, dx, dy)

            elif gesture == "right_fist":
                if gesture not in self._drag_origin:
                    cx, cy = self._window_center()
                    pyautogui.moveTo(cx, cy)
                self._right_click_down('c')
                self._mouse_move(gesture, dx, dy)

        elif act == "drag_end":
            if gesture == "left_fist":
                self._release_all_keys()
            elif gesture == "right_pinch":
                self._right_click_up('x')
                self._drag_origin.pop(gesture, None)
            elif gesture == "right_fist":
                self._right_click_up('c')
                self._drag_origin.pop(gesture, None)

    def stop(self):
        self._release_all_keys()