#!/usr/bin/env python3
import cv2
import numpy as np
from datetime import datetime
from pathlib import Path
import logging
import json

# Configuration
IMAGE_DIR = Path.home() / "logs" / "plant-water" / "images"
HEALTH_DIR = Path.home() / "logs" / "plant-water" / "health"
HEALTH_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = HEALTH_DIR / "health.log"
HEALTH_LOG = HEALTH_DIR / "health_log.json"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

def analyze_plant_health(image_path):
    """
    Analyze plant health based on leaf color
    Returns health score 0-100 (100 = healthy green, 0 = dead/brown)
    """
    try:
        img = cv2.imread(str(image_path))
        if img is None:
            logging.error(f"Could not load image: {image_path}")
            return None
        
        # Convert to HSV for better color detection
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        # Define color ranges
        # Green (healthy): Hue 35-85, Sat 40-255, Val 40-255
        green_lower = np.array([35, 40, 40])
        green_upper = np.array([85, 255, 255])
        green_mask = cv2.inRange(hsv, green_lower, green_upper)
        
        # Yellow (stressed): Hue 20-35, Sat 40-255, Val 40-255
        yellow_lower = np.array([20, 40, 40])
        yellow_upper = np.array([35, 255, 255])
        yellow_mask = cv2.inRange(hsv, yellow_lower, yellow_upper)
        
        # Brown (dead): Hue 10-20, Sat 40-255, Val 20-100
        brown_lower = np.array([10, 40, 20])
        brown_upper = np.array([20, 255, 100])
        brown_mask = cv2.inRange(hsv, brown_lower, brown_upper)
        
        # Count pixels
        green_pixels = np.sum(green_mask > 0)
        yellow_pixels = np.sum(yellow_mask > 0)
        brown_pixels = np.sum(brown_mask > 0)
        total_plant_pixels = green_pixels + yellow_pixels + brown_pixels
        
        if total_plant_pixels == 0:
            logging.warning("No plant detected in image")
            return None
        
        # Calculate health score
        green_ratio = green_pixels / total_plant_pixels
        yellow_ratio = yellow_pixels / total_plant_pixels
        brown_ratio = brown_pixels / total_plant_pixels
        
        # Health score: 100% green = 100, 100% brown = 0
        health_score = (green_ratio * 100) + (yellow_ratio * 50) + (brown_ratio * 0)
        
        result = {
            'timestamp': datetime.now().isoformat(),
            'image': image_path.name,
            'health_score': round(health_score, 2),
            'green_percent': round(green_ratio * 100, 2),
            'yellow_percent': round(yellow_ratio * 100, 2),
            'brown_percent': round(brown_ratio * 100, 2),
            'total_plant_pixels': int(total_plant_pixels)
        }
        
        logging.info(f"Health analysis: score={result['health_score']}, "
                    f"green={result['green_percent']}%, "
                    f"yellow={result['yellow_percent']}%, "
                    f"brown={result['brown_percent']}%")
        
        return result
        
    except Exception as e:
        logging.error(f"Error analyzing image: {e}", exc_info=True)
        return None

def save_health_log(result):
    """Append health analysis to JSON log"""
    logs = []
    if HEALTH_LOG.exists():
        with open(HEALTH_LOG, 'r') as f:
            logs = json.load(f)
    
    logs.append(result)
    
    with open(HEALTH_LOG, 'w') as f:
        json.dump(logs, f, indent=2)

if __name__ == "__main__":
    # Get most recent image
    images = sorted(IMAGE_DIR.glob("plant_*.jpg"))
    if not images:
        logging.error("No images found")
        exit(1)
    
    latest_image = images[-1]
    logging.info(f"Analyzing: {latest_image.name}")
    
    result = analyze_plant_health(latest_image)
    if result:
        save_health_log(result)
        print(f"\n✓ Health Score: {result['health_score']}/100")
        print(f"  Green: {result['green_percent']}%")
        print(f"  Yellow: {result['yellow_percent']}%")
        print(f"  Brown: {result['brown_percent']}%")
    else:
        logging.error("Health analysis failed")
        exit(1)
