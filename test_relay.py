import RPi.GPIO as GPIO
import time

RELAY_PIN = 17

GPIO.setmode(GPIO.BCM)
GPIO.setup(RELAY_PIN, GPIO.OUT, initial=GPIO.LOW)  # Start LOW (relay OFF)

print("Testing relay control...")
print("Relay should be OFF now (no click yet)\n")
time.sleep(2)

print("1. Setting HIGH (relay should click ON, LED lights up)")
GPIO.output(RELAY_PIN, GPIO.HIGH)
time.sleep(2)

print("2. Setting LOW (relay should click OFF, LED goes dark)")
GPIO.output(RELAY_PIN, GPIO.LOW)
time.sleep(2)

print("3. Setting HIGH again (relay should click ON)")
GPIO.output(RELAY_PIN, GPIO.HIGH)
time.sleep(1)

print("4. Final LOW (relay should click OFF)")
GPIO.output(RELAY_PIN, GPIO.LOW)

GPIO.cleanup()
print("\nTest complete. Relay should be OFF now.")
