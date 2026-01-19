import logging
import os
import cv2
import datetime
import pyautogui
import logging
import yaml
from pathlib import Path

def load_config():
    config_path = Path("config.yaml")
    if not config_path.exists():
        # Default fallback if file is missing
        return {}
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)
def setup_logging():
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "automation.log"),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def save_debug_screenshot(image, prefix="debug"):
    debug_dir = Path("detection_screenshots")
    debug_dir.mkdir(exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = debug_dir / f"{prefix}_{timestamp}.png"
    cv2.imwrite(str(filename), image)
    return str(filename)

def release_all_keys():
    """Safety function to un-stick any keys like Alt, Ctrl, or Shift."""
    keys = ['alt', 'ctrl', 'shift', 'win']
    for key in keys:
        try:
            pyautogui.keyUp(key)
        except:
            pass
    logging.getLogger(__name__).info("Safety Reset: All modifier keys released.")