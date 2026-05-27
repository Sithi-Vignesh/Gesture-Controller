import os
import sys

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


#Camera
CAMERA_INDEX = 0
CAMERA_WIDTH = 1920
CAMERA_HEIGHT = 1080
FPS_TARGET = 30

#MediaPipe
MAX_HANDS = 2
DETECTION_CONFIDENCE = 0.5
TRACKING_CONFIDENCE = 0.3

#Gesture Thresholds
FIST_THRESHOLD = 0.1
PINCH_THRESHOLD = 0.05

#INPUT
MOVE_SENSITIVITY = 3
MAX_DRAG = 700
