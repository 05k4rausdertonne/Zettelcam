#!/usr/bin/python

from Adafruit_Thermal import *
# from illumination import *
import picamera
from PIL import Image, ImageFilter, ImageStat
import RPi.GPIO as GPIO # Import Raspberry Pi GPIO library
import time
import numpy as np
from numpy import average
import json
import os
import stat
from shutil import copytree
import subprocess
from illumination_using_wgif import illuminate

shutterButtonPin = 16
optionButtonPin = 22
ledPin = 12
flashPin = 18
buzzer_pin = 7
shutterButtonState = True
optionButtonState = True
optionButtonLast = float('inf')
shutdownHoldTime = 5
imagePath = "/home/pi/zettel_cam/DCIM/"
currentFolder = "100ZTC/"
blendingBias = 0
data = None

GPIO.setwarnings(False) # Ignore warning for now
GPIO.setmode(GPIO.BOARD) # Use physical pin numbering
GPIO.setup(shutterButtonPin, GPIO.IN, pull_up_down=GPIO.PUD_UP) # set button pin to input with a pull-up resistor
GPIO.setup(optionButtonPin, GPIO.IN, pull_up_down=GPIO.PUD_UP) # set button pin to input with a pull-up resistor
GPIO.setup(ledPin, GPIO.OUT)
GPIO.setup(flashPin, GPIO.OUT)
GPIO.setup(buzzer_pin, GPIO.OUT) 
buzz = GPIO.PWM(buzzer_pin, 1500) 

printer = Adafruit_Thermal("/dev/serial0", 9600, timeout=5)
printer.begin(160)
printer.sleep()

camera = picamera.PiCamera()
camera.resolution = (1024, 768)

GPIO.output(ledPin, True)
GPIO.output(flashPin, False)

with open("/home/pi/zettel_cam/data.json", "r") as file:

    data = json.load(file)

print(data)

def playSound(notes, speed):
    for i in notes:
        buzz.start(30) 
        buzz.ChangeFrequency(i) 
        time.sleep(speed)
        buzz.stop()
        time.sleep(speed/2)

def brightness( img ):
    stat = ImageStat.Stat(img)
    brightness = average(stat.rms)
    print(brightness)
    return brightness

def dynamicallyBlendImage(ogImage, enhancedImage, brightness):
    return Image.blend(enhancedImage, ogImage, (brightness-blendingBias)/100)

def takePicture():
    imageName = imagePath + data["current_folder"] + "ZTCO" + str(data["picture_count"]).zfill(4) + ".jpeg"
    greyName = imagePath + data["current_folder"] + "ZTCG" + str(data["picture_count"]).zfill(4) + ".jpeg"
            
    GPIO.output(flashPin, True)
    camera.capture(imageName, quality = 100)
    GPIO.output(flashPin, False)
    
    playSound([2250, 1500], 0.1)
    
    print("picture taken.\nprocessing...")

    #rotate image by 90 degrees
    angle = 90
    Image.open(imageName).rotate(angle, expand=True).save(imageName)

    bwImage = Image.open(imageName).convert("L").resize((384, 512))
    enhancedImage = Image.fromarray(illuminate(np.reshape(bwImage.getdata(), (bwImage.size[1], bwImage.size[0]))))
    # enhancedImage = custom_bw_enhancement(bwImage)
    # blendedImage = dynamicallyBlendImage(bwImage, enhancedImage, brightness(bwImage))
    enhancedImage.filter(ImageFilter.EDGE_ENHANCE).save(greyName)

    return greyName

def printPicture(imageName):
    printer.wake()
    printer.printImage(imageName, True)
    printer.feed(2)
    printer.sleep()

def createNewFolder(data):
    data["picture_count"] = 0
    data["folder_count"] += 1
    data["current_folder"] = str(data["folder_count"]) + "ZTC/"

    folder_path = imagePath + data["current_folder"]
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        os.chmod(folder_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)  # Set read/write/execute permissions


    return data

def shutdown_raspberry_pi():
    try:
        subprocess.run(['sudo', 'shutdown', '-h', 'now'])
    except Exception as e:
        print(f"Error: {e}")

playSound([2250, 2750, 1500, 2250], 0.1)

print("ready!")

try:
    while True:
        shutterButtonNow = GPIO.input(shutterButtonPin)
        optionButtonNow = GPIO.input(optionButtonPin)    
        if shutterButtonState != shutterButtonNow:
            shutterButtonState = shutterButtonNow
            if shutterButtonNow == False:
                print("taking picture")
                GPIO.output(ledPin, False)            
                
                imageName = takePicture()

                printPicture(imageName)

                data["picture_count"] += 1

                if data["picture_count"] > 9999:
                    createNewFolder(data)

                with open("/home/pi/zettel_cam/data.json", 'w') as file:
                    json.dump(data, file, indent=4)

                GPIO.output(ledPin, True)
                print("ready!")
                print(data)

        if time.time() - optionButtonLast > shutdownHoldTime:
            playSound([2750, 2250, 1500, 1000], 0.1)
            print("shutting down")
            shutdown_raspberry_pi()

        if optionButtonState != optionButtonNow:
            optionButtonState = optionButtonNow
            if optionButtonNow == False:
                optionButtonLast = time.time()
            if optionButtonNow == True:
                playSound([2250], 0.1)
                print("doing stuff...")
                optionButtonLast = float('inf')

        

        time.sleep(0.01)

except KeyboardInterrupt:
    pass

finally:
    camera.close()
    GPIO.cleanup()
    print("GPIO cleanup complete")