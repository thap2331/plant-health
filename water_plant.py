import serial
import RPi.GPIO as GPIO
import time
from pathlib import Path
import csv
from datetime import datetime

RELAY_PIN = 27
DRY_THRESHOLD = 490
WATERING_DURATION = 3
COOLDOWN_MINUTES = 30

LAST_WATERED_FILE = Path.home() / "last_watered.txt"
LOG_FILE = Path.home() / "moisture_log.csv"

# Initialize CSV with headers if it doesn't exist
if not LOG_FILE.exists():
    with open(LOG_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'moisture_reading', 'is_dry', 'watered', 'cooldown_active'])

GPIO.setmode(GPIO.BCM)
GPIO.setup(RELAY_PIN, GPIO.OUT, initial=GPIO.LOW)

ser = serial.Serial('/dev/ttyACM0', 9600, timeout=2)
time.sleep(2)

def get_last_watered():
    if LAST_WATERED_FILE.exists():
        return float(LAST_WATERED_FILE.read_text().strip())
    return 0

def set_last_watered():
    LAST_WATERED_FILE.write_text(str(time.time()))

def log_reading(moisture, is_dry, watered, cooldown_active):
    with open(LOG_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.now().isoformat(),
            moisture,
            is_dry,
            watered,
            cooldown_active
        ])

try:
    print("Starting moisture monitor...")
    while True:
        line = ser.readline().decode().strip()
        if line:
            try:
                value = int(line)
                is_dry = value > DRY_THRESHOLD
                watered = False
                cooldown_active = False
                
                print(f"Moisture: {value}", end="")
                
                if is_dry:
                    last = get_last_watered()
                    elapsed_min = (time.time() - last) / 60
                    
                    if elapsed_min < COOLDOWN_MINUTES:
                        cooldown_active = True
                        print(f" → Dry but watered {elapsed_min:.1f}m ago, skipping")
                    else:
                        print(f" → Dry, watering for {WATERING_DURATION}s")
                        GPIO.output(RELAY_PIN, GPIO.HIGH)
                        time.sleep(WATERING_DURATION)
                        GPIO.output(RELAY_PIN, GPIO.LOW)
                        set_last_watered()
                        watered = True
                        print("   Watering complete")
                else:
                    print(" → Soil OK")
                
                log_reading(value, is_dry, watered, cooldown_active)
                    
            except ValueError:
                print(f"Bad reading: {line}")
        
        time.sleep(60)
        
except KeyboardInterrupt:
    print("\nShutting down gracefully")
    GPIO.cleanup()
    ser.close()
