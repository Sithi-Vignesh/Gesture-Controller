import subprocess
import json
import os
import config
import sys

def get_tap():
    process = subprocess.Popen([config.ADB_PATH,"shell","getevent","-l","/dev/input/event4"], stdout=subprocess.PIPE)
    x = None
    y = None
    for line in process.stdout:
        line = line.decode().strip()
        parts = line.split()
        if len(parts) >= 3:
            if parts[1] == "ABS_MT_POSITION_X":
                x = int(parts[2], 16)
            elif parts[1] == "ABS_MT_POSITION_Y":
                y = int(parts[2], 16)

        if len(parts) >= 2 and parts[1] == "SYN_REPORT" and x is not None and y is not None:
            try:
                process.kill()
            except:
                pass
            return (x, y)
        
def calibrate():
    print("Place finger on Movement Joystick and tap")
    x1, y1 = get_tap()
    print(f"Movement captured: ({x1}, {y1})")
    
    print("Place finger on Attack button and tap")
    x2, y2 = get_tap()
    print(f"Attack captured: ({x2}, {y2})")
    
    print("Place finger on Super button and tap")
    x3, y3 = get_tap()
    print(f"Super captured: ({x3}, {y3})")

    profile = {
        "movement": {"x": x1, "y": y1},
        "attack": {"x": x2, "y": y2},
        "super": {"x": x3, "y": y3}
    }

    with open("data/profiles/profile.json", "w") as f:
        json.dump(profile, f)
    print("Calibration done!")


if __name__ == "__main__":
    calibrate()