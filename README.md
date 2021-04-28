# Raspberrypi-alarm-clock
An alarm clock program written in python and javascript that uses official 7inch touchscreen and sensors.

youtube link :https://www.youtube.com/watch?v=oix73klMY2o

## Basic info
I use this program for setting alarm and control the near IOT object. This program is simply divided by GUI, background process, web server(of course i will include database later). This smart alarm clock serve as a multi functional interface so I included digital,analog clock and home sensing system. and Users can control this program using remote control by their smartphone(I am still considering efficient method for data communication instead of Queue transfer and I will update 
and revise CSS and html for various types of resolutions. It only support iphone 12). And i am still thiking what design
would be motivating for waking users up in the morning.
## Demo images
<img src="https://user-images.githubusercontent.com/83174153/116087746-247b2c00-a6dc-11eb-8267-775c8b33302c.jpg" width="90%" height="90%">
<p>
<img src="https://user-images.githubusercontent.com/83174153/116086320-a79b8280-a6da-11eb-86b9-49ceacdf8c1b.jpg" width="45%">
<img src="https://user-images.githubusercontent.com/83174153/116087638-06153080-a6dc-11eb-805f-36bcdd3b4f0c.jpg" width="45%">
</p>
<p>
<img src="https://user-images.githubusercontent.com/83174153/116087679-1200f280-a6dc-11eb-87e6-5d6b2056dd6f.jpg" width="45%">
<img src="https://user-images.githubusercontent.com/83174153/116087720-1b8a5a80-a6dc-11eb-89c1-fd3dc8609748.jpg" width="45%">
</p>
images show that it provide various UI to sense many types of information in the house and it light up the neopixel when alarm rings and make an announcement of today's weather and recent news and turn on the music.

## References
Thanks to the lots of ideas to make this beautiful and good working alarm clock
* Retro Arcade Clock-Arduino https://www.youtube.com/watch?v=e5DrPF1A_Pg
* Raspberry pi:Alarm Clock Project https://www.youtube.com/watch?v=-Or5jmBqsNE&t=44s
* For trial and error Stack Overflow (of course)
## Goals
The main goal is to offer users a quality sleep and wake up system. So i considered a good 
design for sleeping and remote-controlling system using web server(Flask module). and there's a 
back light controlling module. when Alarm rings, the alarm automatically turn the volume to announce 
today's news and weathers and calming sound.

Of course this is a form of IOT project so i will update to control another sensors or devices
and dark-mode in GUI. Any ideas for update are welcome.
## Hardware
* Raspberry pi 4B(another board is okay if 7inch touch screen supports)
* SD card(for installing OS)
* Keyboard,monitor(initial setting)
* Raspberry pi heatsink
* breadboard,Jumper line
* Speaker(3.5mm or bluetooth)
* 5V 1 channel relay(input voltage is 12V because I used 12V for led)
* Male and Female 12V DC power jack Adapter Connector(link:https://www.amazon.com/gp/product/B01ER6QWAY/ref=ppx_yo_dt_b_asin_title_o00_s00?ie=UTF8&psc=1)
* LED Strip Lights that uses DC Adapter(link:https://www.amazon.com/gp/product/B07RFFJ7YL/ref=ppx_yo_dt_b_asin_title_o00_s00?ie=UTF8&psc=1)
* Official Raspberrypi 7inch touch scrreen(make sure that is supports your board)
* 7inch touch screen case(neccesary)
* 220V->110V Transformers(I used 110V led strip and here is korea so i used this)
* Adafruit dht11 sensor
* Adafruit BMP180 sensor
## Dependencies
* pip3 --version (make sure that python3 is pre-installed)
* sudo pip3 install PIL
* rpi-backlight library(link:https://github.com/linusg/rpi-backlight)
* sudo pip3 install tkinter
* adafruit_dht library (link:https://github.com/adafruit/DHT-sensor-library)
* adafruit_BMP180 library (link:https://github.com/adafruit/Adafruit_Python_BMP)
* sudo pip3 install gtts
* sudo pip3 install bs4
* sudo pip3 install requests
* (optional) sudo pip3 install flask (only if you want remote control)
## What about Raspberry pi alarm clock?
Raspberry pi touch alarm clock offers several functions
### GUI
1. digital clock
2. analog clock
3. alarm setting:hour,minute,second,dayofweek
4. check alarm list( thread using so program can control multiple of alarm)
5. temperature,humidity,pressure check
### background
1. Alarm thread
2. (optional)flask web server ( go into the raspberry pi IP address and you can control by remote controlling)
3. alarm wake up system(LED control,web crawling and gtts sound all of thesese is formed of multiprocess)
4. dht_sensor checking (multiprocess)
## ETC
I wrote comments shortly in the program and if you have trouble using or understanding the code, email me at sehyunisworking0708@gmail.com(of course i will serve
as a military so for a while i will not be able to confirm)
And i had been struggling to communicate with flask server and i turned on and off the GUI alarm clock by using multiprocess module in the flask because 
I am not good at programming about communication so if you have any comments on that let me know
I checked all but there might have some copyright issue if you let me know by email above i will delete them as soon as possible
## Notice
I will keep update this part

you should make ramdisk for weather_broadcast.py because i made the ramdisk folder /mnt/ramdisk
