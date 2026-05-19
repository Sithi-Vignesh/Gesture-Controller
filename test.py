import pyautogui
import win32gui
import time

hwnd = win32gui.FindWindow(None, "LDPlayer")
win32gui.SetForegroundWindow(hwnd)
time.sleep(0.5)
pyautogui.keyDown('w')
time.sleep(1)
pyautogui.keyUp('w')