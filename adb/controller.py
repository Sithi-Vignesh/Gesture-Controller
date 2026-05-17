import subprocess
import config
import threading


def _send_swipe(cmd):
    subprocess.run(cmd)

class ADBController:
    def __init__(self, phone_width, phone_height):
        self.phone_width = phone_width
        self.phone_height = phone_height
        self._thread = None
    
    def send(self,action):
        if action["action"] == "drag_hold":
            x1 = action["x1"]*self.phone_width
            y1 = action["y1"]*self.phone_height
            x2 = action["x2"]*self.phone_width
            y2 = action["y2"]*self.phone_height
            
            if self._thread is None or not self._thread.is_alive():
                swipe = str(int(x1)), str(int(y1)), str(int(x2)), str(int(y2)), str(config.ADB_SWIPE_DURATION)
                self._thread = threading.Thread(target=_send_swipe, args=([config.ADB_PATH, "shell", "input", "swipe"] + list(swipe),))
                self._thread.daemon = True
                self._thread.start()
