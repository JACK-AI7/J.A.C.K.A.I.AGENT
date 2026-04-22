import os
import re
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from comtypes import CLSCTX_ALL
import screen_brightness_control as sbc

def execute(task=None):
    """
    Adjusts system volume or brightness.
    Task formats:
    - 'volume: [0-100]'
    - 'brightness: [0-100]'
    """
    if not task:
        return "System Ops Error: No task provided."
    
    task = task.lower()
    
    # 1. Volume Control
    if "volume" in task:
        try:
            match = re.search(r'(\d+)', task)
            if not match:
                return "System Ops Error: No volume level specified."
            
            level = int(match.group(1))
            level = max(0, min(100, level))
            
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = interface.QueryInterface(IAudioEndpointVolume)
            
            # Volume range is -65.25 to 0.0 (in decibels)
            # Scalar mapping 0.0 to 1.0 is easier
            volume.SetMasterVolumeLevelScalar(level / 100.0, None)
            return f"System volume set to {level}%."
        except Exception as e:
            return f"Volume Control Error: {e}"

    # 2. Brightness Control
    elif "brightness" in task:
        try:
            match = re.search(r'(\d+)', task)
            if not match:
                return "System Ops Error: No brightness level specified."
            
            level = int(match.group(1))
            level = max(0, min(100, level))
            
            sbc.set_brightness(level)
            return f"System brightness set to {level}%."
        except Exception as e:
            return f"Brightness Control Error: {e}"
            
    else:
        return "System Ops Error: Unknown system operation. Use 'volume' or 'brightness'."
