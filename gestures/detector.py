import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

from config import (
    CAMERA_INDEX, CAMERA_WIDTH, CAMERA_HEIGHT,FPS_TARGET, MAX_HANDS, DETECTION_CONFIDENCE, TRACKING_CONFIDENCE
)

class HandDetector:
    def __init__(self):
        self._cap = cv2.VideoCapture(CAMERA_INDEX) #private variables
        base_options = mp_python.BaseOptions(
            model_asset_path="assets/hand_landmarker.task"
        )
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            num_hands=MAX_HANDS,
            min_hand_detection_confidence=DETECTION_CONFIDENCE,
            min_hand_presence_confidence=TRACKING_CONFIDENCE
        )
        self._hands = vision.HandLandmarker.create_from_options(options)

    def start(self):
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
        self._cap.set(cv2.CAP_PROP_FPS, FPS_TARGET)
        if not self._cap.isOpened():
            raise RuntimeError("Cannot open camera. Check if another app is using it.")
        
    def stop(self):
        self._cap.release()
        self._hands.close()


    def read(self):
        success, frame = self._cap.read()
        if not success:
            return {"left": None, "right": None, "frame": None, "ok": False}
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        results = self._hands.detect(mp_image)

        if not results.hand_landmarks:
            return {"left": None, "right": None, "frame": frame, "ok": True}
        
        result = {"left": None, "right": None, "frame": frame, "ok": True}

        for hand_landmarks, handedness in zip(results.hand_landmarks, results.handedness):
            label = "left" if handedness[0].category_name.lower() == "left" else "right"
            landmarks = [{"x": lm.x, "y": lm.y, "z": lm.z} for lm in hand_landmarks]
            result[label] = landmarks

        return result
    