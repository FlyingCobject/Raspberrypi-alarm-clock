from gtts import gTTS
from bs4 import BeautifulSoup
import requests
import os
import RPi.GPIO as GPIO

def alarm_sound():
    GPIO.setwarnings(False) # for lighting the LED

    GPIO.setmode(GPIO.BCM)
    led_pin=21 
    GPIO.setup(led_pin,GPIO.OUT)
    GPIO.output(led_pin,1)

    # touch_screen.class에서 00:00:00 시간 정보 받아와서 음성출력
    # 현재 방온도와 습도 정보 받아와서 음성 출력

    # 웹 크롤링: 현재 용인 날씨 정보를 받아와서 출력

    # 주요 뉴스에 대한 정보 웹 크롤링 해서 출력

    html = requests.get('https://search.naver.com/search.naver?query=날씨') #crawling the weather infomation in NAVER


    soup = BeautifulSoup(html.text, 'html.parser')

    data1 = soup.find('div', {'class': 'weather_box'})
    find_address=data1.find('span',{'class':'btn_select'}).text

    weather_info=""
    weather_info+="현재 위치는 "+find_address+"이고 " # location

    find_currenttemp=data1.find('span',{'class':'todaytemp'}).text
    weather_info+="현재 기온은 "+find_currenttemp+"도 이며 " # temperature

    data2=data1.findAll('dd')

    find_dust=data2[0].find('span',{'class':'num'}).text
    find_ultra_dust=data2[1].find('span',{"class":"num"}).text # micro dust and ozone
    find_dust=(''.join(i for i in find_dust if i.isdigit()))
    find_ultra_dust=(''.join(i for i in find_ultra_dust if i.isdigit()))
    find_ozone=data2[2].find('span',{'class':"num"}).text

    weather_info+="미세먼지는 "+find_dust+"이며 "
    weather_info+="초미세먼지는 "+find_ultra_dust+"이고 "
    weather_info+="오존량은 "+find_ozone+"이에요"

    tts=gTTS( # TTS sound in korean
        text=weather_info,
        lang='ko',slow=False
    )

    tts.save("/mnt/ramdisk/weather.mp3") # save to the ramdisk(you should make a folder and save to them)
    os.system("play /mnt/ramdisk/weather.mp3") # play



    news_info="" # why i use headers?-> Naver blocked when crawling ranking news without header
    news_url='https://news.naver.com/main/ranking/popularDay.nhn?mid=etc&sid1=111'
    headers={
        "User-Agent":'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36'}
    html=requests.get(news_url,headers=headers)
    soup=BeautifulSoup(html.text,'html.parser')

    data1=soup.find('div',{'class','rankingnews_head'})
    find_head=data1.find('h2',{'class','rankingnews_tit'}).text

    news_info+=find_head+"입니다\n" # printing today's ranking news
    #print(news_info)

    data2=soup.findAll('div',{'class','rankingnews_box'})

    find_list=data2[0].findAll('li')
    #print(find_list)
    number=['첫번쨰로','두번째로','세번째로','네번째로','다섯번째로'] # print the 5 ranking news
    number_indx=0
    for element in find_list:
        if number_indx==5:
            break
        find_time=element.find('span').text
        news_info+=number[number_indx]+find_time+'뉴스입니다.\n'
        find_content=element.find('a').text
        news_info+=find_content+'\n'
        number_indx+=1

    print(news_info)

    tts2=gTTS( # tts module
        text=news_info,
        lang='ko',slow=False
    )

    tts2.save("/mnt/ramdisk/news.mp3")
    os.system("play /mnt/ramdisk/news.mp3") # play the news sound

    os.system("play musics/Instrumental.mp3") # play the alarm sound


    GPIO.output(led_pin,0) # turn off the light and clear when alarm sound finish
    GPIO.cleanup()


if __name__=="__main__":
    alarm_sound()