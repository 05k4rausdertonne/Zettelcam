#!/usr/bin/python

from Adafruit_Thermal import *
import picamera
from PIL import Image
import RPi.GPIO as GPIO # Import Raspberry Pi GPIO library


buttonPin = 16
ledPin = 12
buttonState = False
loopCount = 0

GPIO.setwarnings(False) # Ignore warning for now
GPIO.setmode(GPIO.BOARD) # Use physical pin numbering
GPIO.setup(buttonPin, GPIO.IN, pull_up_down=GPIO.PUD_UP) # set button pin to input with a pull-up resistor
GPIO.setup(ledPin, GPIO.OUT)

printer = Adafruit_Thermal("/dev/serial0", 9600, timeout=5)

camera = picamera.PiCamera()
camera.resolution = (512, 384)
# camera.capture("test.png")
# # stream = io.BytesIO()
# # camera.capture(stream, format='png')

# #read the image
# im = Image.open("test.png")

# #rotate image by 90 degrees
# angle = 90
# out = im.rotate(angle, expand=True)
# out.save("test.png")
# # stream.seek(0)
# # image = Image.open(stream)
# # image.save("test.png")
# # image.rotate(90, expand=True)
# # image.save("test2.png")


# printer.printImage(out, True)
# printer.printImage("test.png", True)
# printer.feed(2)

GPIO.output(ledPin, GPIO.HIGH)


while True:
    loopCount += 1
    buttonNow = GPIO.input(buttonPin)
    if buttonState != buttonNow:
        buttonState = buttonNow
        if buttonNow == False:
            GPIO.output(ledPin, GPIO.LOW)
            
            camera.capture("test.png")
            # stream = io.BytesIO()
            # camera.capture(stream, format='png')

            #read the image
            im = Image.open("test.png")

            #rotate image by 90 degrees
            angle = 90
            out = im.rotate(angle, expand=True)
            out.save("test.png")
            
            # printer.printImage(out, True)
            printer.printImage("test.png", True)
            printer.feed(2)

            GPIO.output(ledPin, GPIO.HIGH)
                
