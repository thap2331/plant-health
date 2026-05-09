import spidev
import RPi.GPIO as GPIO
import time
from pathlib import Path
import csv
from datetime import datetime

RELAY_PIN = 27
DRY_THRESHOLD = 560
WATERING_DURATION = 3
COOLDOWN_MINUTES = 300
LAST_WATERED_FILE = Path.home() / "last_watered.txt"
LOG_FILE = Path.home() / "moisture_log.csv"

if not LOG_FILE.exists():
    with open(LOG_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'moisture_reading', 'is_dry', 'watered', 'cooldown_active'])

spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 1350000

def read_moisture():
    r = spi.xfer2([1, (8 + 0) << 4, 0])
    return ((r[1] & 3) << 8) + r[2]

GPIO.setmode(GPIO.BCM)
GPIO.setup(RELAY_PIN, GPIO.OUT, initial=GPIO.HIGH)

def get_last_watered():
    if LAST_WATERED_FILE.exists():
        return float(LAST_WATERED_FILE.read_text().strip())
    return 0

def set_last_watered():
    LAST_WATERED_FILE.write_text(str(time.time()))

def log_reading(moisture, is_dry, watered, cooldown_active):
    with open(LOG_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([datetime.now().isoformat(), moisture, is_dry, watered, cooldown_active])

try:
    value = read_moisture()
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
            GPIO.output(RELAY_PIN, GPIO.LOW)
            time.sleep(WATERING_DURATION)
            GPIO.output(RELAY_PIN, GPIO.HIGH)
            set_last_watered()
            watered = True
            print(" Watering complete")
    else:
        print(" → Soil OK")

    log_reading(value, is_dry, watered, cooldown_active)

finally:
    GPIO.cleanup()
    spi.close()
