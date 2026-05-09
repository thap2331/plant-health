import spidev
import RPi.GPIO as GPIO
import time
import logging
from pathlib import Path
import csv
from datetime import datetime

# --- Config ---
RELAY_PIN      = 17
SPI_BUS        = 0
SPI_DEVICE     = 0
SPI_SPEED      = 1350000
SENSOR_CHANNEL = 0

DRY_VAL        = 618   # raw value in dry soil
WET_VAL        = 364   # raw value in water
DRY_THRESHOLD  = 40    # % — trigger relay below this
RELAY_ON_SECS  = 5
COOLDOWN_MINUTES = 300

LOG_DIR = Path.home() / "logs" / "plant-water" / "water"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LAST_WATERED_FILE = Path.home() / "last_watered.txt"
LOG_FILE     = LOG_DIR / "water_plant.log"
MOISTURE_CSV = LOG_DIR / "moisture_log.csv"

# --- Logging ---
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def log(msg):
    logging.info(msg)
    print(msg)

# --- CSV ---
if not MOISTURE_CSV.exists():
    with open(MOISTURE_CSV, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'raw', 'moisture_pct', 'is_dry', 'watered', 'cooldown_active'])

# --- GPIO ---
GPIO.setmode(GPIO.BCM)
GPIO.setup(RELAY_PIN, GPIO.OUT)
GPIO.output(RELAY_PIN, GPIO.LOW)   # LOW = relay OFF (active-HIGH)

# --- SPI / MCP3008 ---
spi = spidev.SpiDev()
spi.open(SPI_BUS, SPI_DEVICE)
spi.max_speed_hz = SPI_SPEED

def read_mcp3008(channel):
    assert 0 <= channel <= 7
    r = spi.xfer2([1, (8 + channel) << 4, 0])
    return ((r[1] & 3) << 8) + r[2]

def to_percent(raw):
    pct = (DRY_VAL - raw) / (DRY_VAL - WET_VAL) * 100
    return max(0, min(100, round(pct, 1)))

def get_last_watered():
    if LAST_WATERED_FILE.exists():
        return float(LAST_WATERED_FILE.read_text().strip())
    return 0

def set_last_watered():
    LAST_WATERED_FILE.write_text(str(time.time()))

def log_csv(raw, moisture, is_dry, watered, cooldown_active):
    with open(MOISTURE_CSV, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([datetime.now().isoformat(), raw, moisture, is_dry, watered, cooldown_active])

# --- Main ---
try:
    raw = read_mcp3008(SENSOR_CHANNEL)
    moisture = to_percent(raw)
    is_dry = moisture < DRY_THRESHOLD
    watered = False
    cooldown_active = False

    log(f"Moisture: {moisture}% (raw: {raw})")

    if is_dry:
        last = get_last_watered()
        elapsed_min = (time.time() - last) / 60
        if elapsed_min < COOLDOWN_MINUTES:
            cooldown_active = True
            log(f"Below threshold ({DRY_THRESHOLD}%) but watered {elapsed_min:.1f}m ago, skipping")
        else:
            log(f"Below threshold ({DRY_THRESHOLD}%) — relay ON for {RELAY_ON_SECS}s")
            GPIO.output(RELAY_PIN, GPIO.HIGH)
            time.sleep(RELAY_ON_SECS)
            GPIO.output(RELAY_PIN, GPIO.LOW)
            set_last_watered()
            watered = True
            log("Relay OFF — watering complete")
    else:
        log("Moisture OK — relay stayed off")

    log_csv(raw, moisture, is_dry, watered, cooldown_active)

finally:
    GPIO.output(RELAY_PIN, GPIO.LOW)   # safety: ensure relay is off on exit
    GPIO.cleanup()
    spi.close()
