import cv2
from core.pipeline import GesturePipeline


def main():
    pipeline = GesturePipeline()

    def on_frame(frame):
        cv2.imshow("Gesture Controller", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            pipeline.stop()

    pipeline.on_frame = on_frame
    pipeline.start()

    try:
        pipeline._thread.join()
    except KeyboardInterrupt:
        pipeline.stop()
    finally:
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()