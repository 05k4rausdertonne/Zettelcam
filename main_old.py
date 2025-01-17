#!/usr/bin/python

from Adafruit_Thermal import *
from illumination import *
import picamera as picamera
from PIL import Image, ImageFilter, ImageStat
import RPi.GPIO as GPIO # Import Raspberry Pi GPIO library
import time
from numpy import average
import json
import os
import stat
# import pyudev
from shutil import copytree

buttonPin = 16
ledPin = 12
flashPin = 18
buzzer_pin = 7
buttonState = False
loopCount = 0
imagePath = "/home/pi/zettel_cam/DCIM/"
currentFolder = "100ZTC/"
blendingBias = 0
data = None

GPIO.setwarnings(False) # Ignore warning for now
GPIO.setmode(GPIO.BOARD) # Use physical pin numbering
GPIO.setup(buttonPin, GPIO.IN, pull_up_down=GPIO.PUD_UP) # set button pin to input with a pull-up resistor
GPIO.setup(ledPin, GPIO.OUT)
GPIO.setup(flashPin, GPIO.OUT)
GPIO.setup(buzzer_pin, GPIO.OUT) 
buzz = GPIO.PWM(buzzer_pin, 1500) 

printer = Adafruit_Thermal("/dev/serial0", 9600, timeout=5)
printer.begin(160)
printer.sleep()

camera = picamera.PiCamera()
camera.resolution = (512, 384)

GPIO.output(ledPin, True)
GPIO.output(flashPin, False)

with open("/home/pi/zettel_cam/data.json", "r") as file:

    data = json.load(file)

print(data)

# context = pyudev.Context()
# monitor = pyudev.Monitor.from_netlink(context)

# monitor.filter_by(subsystem='usb')

# def print_device_event(device):
#     print('background event {0.action}: {0.device_path}'.format(device))
    
#     if device.action == "bind":
        
#         print("copy!")
#         copytree("/home/pi/zettelcam/DCIM", "/media/usb0/zettelcam/DCIM", dirs_exist_ok=True)
  
# observer = pyudev.MonitorObserver(monitor, callback=print_device_event, name='monitor-observer')
# observer.daemon
# observer.start()

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

    bwImage = Image.open(imageName).convert("L")
    enhancedImage = custom_bw_enhancement(bwImage)
    blendedImage = dynamicallyBlendImage(bwImage.convert("L"), enhancedImage.convert("L"), brightness(bwImage))
    blendedImage.filter(ImageFilter.EDGE_ENHANCE).save(greyName)

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

playSound([2250, 2750, 1500, 2250], 0.1)

print("ready!")

while True:
    loopCount += 1
    buttonNow = GPIO.input(buttonPin)
    if buttonState != buttonNow:
        buttonState = buttonNow
        if buttonNow == False:
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

    time.sleep(0.01)
                