import RPi.GPIO as GPIO
import time
# just for testing LED don't mind
led_pin=21 

GPIO.setwarnings(False)

GPIO.setmode(GPIO.BCM)

GPIO.setup(led_pin,GPIO.OUT)

while True:
    user_input=input("on/off")
    if user_input =="on":
        GPIO.output(led_pin,1)
    elif user_input =='off':
        GPIO.output(led_pin,0)
    else:
        GPIO.output(led_pin,0)
        break

GPIO.cleanup()