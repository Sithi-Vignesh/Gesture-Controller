import win32gui
import pyautogui
import time

hwnd = win32gui.FindWindow(None, "LDPlayer")
rect = win32gui.GetWindowRect(hwnd)
print(f"Window: {rect}")

try:
    while True:
        mx, my = pyautogui.position()
        rx = mx - rect[0]
        ry = my - rect[1]
        print(f"\rRelative: {rx}, {ry}   ", end="")
        time.sleep(0.1)
except KeyboardInterrupt:
    print(f"\nFinal relative: {rx}, {ry}")