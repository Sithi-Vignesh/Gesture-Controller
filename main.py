import cv2
from gestures.detector import HandDetector
from gestures.recognizer import GestureRecognizer
from gestures.smoother import GestureSmoother
import time


detector = HandDetector()
recognizer = GestureRecognizer()
smoother = GestureSmoother(5)

detector.start()

prev_time = 0

connections = [
    (0,1),(1,2),(2,3),(3,4),
    (0,5),(5,6),(6,7),(7,8),
    (0,9),(9,10),(10,11),(11,12),
    (0,13),(13,14),(14,15),(15,16),
    (0,17),(17,18),(18,19),(19,20),
    (5,9),(9,13),(13,17)
]

stableGestures = []

while True:
    hands = detector.read()
    frame = hands["frame"]
    check = hands["ok"]
    if not check: continue
    gestures = recognizer.recognize(hands)

    if (hands["left"] is None and hands["right"] is None):
        stableGestures = []
    else:
        stableGestures = smoother.update(gestures)

    for side in ["left", "right"]:
        if hands[side]:
            for point in hands[side]:
                cx = int(point["x"] * 640)
                cy = int(point["y"] * 480)
                cv2.circle(frame, (cx, cy), 4, (0, 255, 0), -1)

            for start, end in connections:
                x1 = int(hands[side][start]["x"] * 640)
                y1 = int(hands[side][start]["y"] * 480)
                x2 = int(hands[side][end]["x"] * 640)
                y2 = int(hands[side][end]["y"] * 480)
                cv2.line(frame, (x1, y1), (x2, y2), (255, 255, 255), 2)

    cv2.rectangle(frame, (10, 10), (300, 60), (0, 0, 0), -1)

    curr_time = time.time()
    fps = int(1 / (curr_time - prev_time)) if (curr_time - prev_time) > 0 else 0
    prev_time = curr_time

    text = ", ".join(stableGestures) if stableGestures else "None"
    cv2.putText(frame, f"Gestures: {text} | FPS: {fps}", (15, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

    cv2.imshow("Gesture Controller", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

detector.stop()
cv2.destroyAllWindows()