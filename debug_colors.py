#!/usr/bin/env python3
import cv2
import numpy as np
from pathlib import Path

IMAGE_DIR = Path.home() / "plant-health" / "images"
OUTPUT_DIR = Path.home() / "plant-health" / "debug"
OUTPUT_DIR.mkdir(exist_ok=True)

# Get latest image
images = sorted(IMAGE_DIR.glob("plant_*.jpg"))
img_path = images[-1]

img = cv2.imread(str(img_path))
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# Same ranges as analyzer
green_mask = cv2.inRange(hsv, np.array([35, 40, 40]), np.array([85, 255, 255]))
yellow_mask = cv2.inRange(hsv, np.array([20, 40, 40]), np.array([35, 255, 255]))
brown_mask = cv2.inRange(hsv, np.array([10, 40, 20]), np.array([20, 255, 100]))

# Save visualizations
cv2.imwrite(str(OUTPUT_DIR / "1_original.jpg"), img)
cv2.imwrite(str(OUTPUT_DIR / "2_green_mask.jpg"), green_mask)
cv2.imwrite(str(OUTPUT_DIR / "3_yellow_mask.jpg"), yellow_mask)
cv2.imwrite(str(OUTPUT_DIR / "4_brown_mask.jpg"), brown_mask)

print("✓ Debug images saved to debug/")
print("  SCP them to see what's being detected")
