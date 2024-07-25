import RPi.GPIO as GPIO
import time

# Replace 17 with the GPIO pin where your button is connected
BUTTON_PIN = 16

GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

try:
    while True:
        button_state = GPIO.input(BUTTON_PIN)
        print(f"Button State: {button_state}")
        time.sleep(1)

except KeyboardInterrupt:
    pass

finally:
    GPIO.cleanup()
    print("GPIO cleanup complete")
