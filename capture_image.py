#!/usr/bin/env python3
import cv2
from datetime import datetime
from pathlib import Path
import logging

# Configuration
IMAGE_DIR = Path.home() / "logs" / "plant-water" / "images"
LOG_FILE = IMAGE_DIR / "camera.log"

IMAGE_DIR.mkdir(parents=True, exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()  # Also print to console
    ]
)

def capture_image():
    """Capture single image from webcam"""
    try:
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            logging.error("Could not open webcam (device 0)")
            return None
        
        # Let camera warm up
        for _ in range(5):
            cap.read()
        
        # Capture frame
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            logging.error("Could not read frame from webcam")
            return None
        
        # Save with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = IMAGE_DIR / f"plant_{timestamp}.jpg"
        cv2.imwrite(str(filename), frame)
        
        logging.info(f"Captured image: {filename.name} (size: {frame.shape})")
        return filename
        
    except Exception as e:
        logging.error(f"Unexpected error during image capture: {e}", exc_info=True)
        return None

if __name__ == "__main__":
    result = capture_image()
    if result is None:
        logging.error("Image capture failed")
        exit(1)
