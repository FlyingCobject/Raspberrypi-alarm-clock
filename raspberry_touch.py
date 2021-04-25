'''
Sehyun Choi at Dankook University(Software) Email:Sehyun523@naver.com
you should be allowed to use this code

Basic: Touch Scrreen using tkinter(plan to use touch screen monitor)
Purpose: touch screen for Raspberry pi control,GPIO, lots of UI test

'''
from tkinter import * # python 3
from PIL import Image,ImageTk
import math # convert float to int for Font value
import datetime # clock information
#import calendar # day of week information
#import vlc # for alarm clock and streaming music
import time # use in sub thread
import threading,_thread # Raspberry pi gets slower when too much burden
import os #display set up(for ssh), command using in python 
from queue import Queue # thread:for backround processing(related to flask web server)
from rpi_backlight import Backlight # raspberry pi 7 inch touchscreen backlight control
#import subprocess #for vlc loop setting(resource is wasted..)
import board # GPIO.board
import adafruit_dht # dht 11 sensor
import Adafruit_BMP.BMP085 as BMP085 # BMP180 sensor
#from temp_cal import Temperature
from alarm_class import Alarm # alarm node class
from multiprocessing import Process,Queue
from weather_broadcast import alarm_sound

''' # not support mp3 function(if you request, i can add)
playlist=['musics/BTS Dynamite Lyrics.mp3',
'musics/Don Diablo  On My Mind Official Music Video.mp3',
'musics/Pitbull ft Flo Rida LunchMoney Lewis  Greenlight Official Lyric Video.mp3',
'musics/Pitbull ft NeYo  Time Of Our Lives Official Lyric Video.mp3',
'musics/RetroVision  Puzzle NCS Release.mp3'] # mp3 lists
'''

img_widget=list()  #widget list(for effectively controlling)
text_widget=list()
shape_widget=list()
after_func=dict()

nameOfAfter=['digital_clock','analog_clock','dht_check','tmp_alarm','goto_menu'] # after_func list(tkinter uses after)



def rel_mov(window,canvas,obj,mode,levelX,levelY,centerX=False,centerY=False):# move widget relatively(according to monitor size)
    coords=canvas.bbox(obj) 

    if(mode==-1): #item anchor should be 'nw'
        canvas.move(obj,-coords[0],-coords[1]) 
        return

    if (levelX and levelY)<1 or (levelX and levelY)>7:
        print("1<=level<=7")
        return
    
    xOffset=(window.winfo_screenwidth()*0.25*levelX/2)-((coords[2]-
    coords[0])/2) # Offset of X

    yOffset=(window.winfo_screenheight()*0.25*levelY/2)-((coords[3]
    -coords[1])/2)# Offset of Y

    if mode ==1:# move just x
        yOffset=0
    if mode ==2:# move just y
        xOffset=0
    
    if mode <0 or mode>3:
        print("mode should be in 1~3")
        return
    if centerX == True:
        xOffset=window.winfo_screenwidth()/2
    if centerY == True:
        yOffset=window.winfo_screenheight()/2
    canvas.move(obj,xOffset,yOffset) #move by offsets


def list_clear(canvas,catagory,func_det=0): # remove widget all by one function(includes canceling after function set)
    if catagory=="img":
        if not img_widget:
            pass
        else:
            for e in img_widget:
                canvas.delete(e)
            img_widget.clear()
    elif catagory=='text':
        if not text_widget:
            pass
        else:
            for e in text_widget:
                canvas.delete(e)
            text_widget.clear()
    elif catagory=='shape':
        if not shape_widget:
            pass
        else:
            for e in shape_widget:
                canvas.delete(e)
            shape_widget.clear()
    elif catagory=='func':
        if func_det not in after_func or after_func[func_det]==0:
            pass
        else:
            canvas.after_cancel(after_func[func_det])
            after_func[func_det]=0

def after_all(canvas): # remove all kind of widgets and after function
    for i in nameOfAfter:
        list_clear(canvas,'func',i)
    list_clear(canvas,'text')
    list_clear(canvas,'shape')
    list_clear(canvas,'img')
    print('text_widget:',end=''); print(text_widget,end=''); print()
    print('img_widget:',end=''); print(img_widget,end=''); print()
    print("shape_widget",end=''); print(shape_widget,end=''); print()
    print("after_function:",end='');print(after_func,end=''); print()
    return
            

class TouchScreen:
    def __init__(self,frame,queue_remote): 
        self.frame=frame # making window
        width=self.frame.winfo_screenwidth()
        height=self.frame.winfo_screenheight()
        self.frame.geometry("%dx%d+0+0" % (width,height))

        self.frame.attributes("-fullscreen",True) #full screen
        self.frame.bind("<Escape>",exit) #ESC -> exit

        self.canvas=Canvas(self.frame) #making canvas
        self.canvas.pack(fill=BOTH,expand=1)

        self.channel=0 #remote control
        self.arrow_true=True # arrow switch

        #calculate relative size for Font to adapt any size of monitor
        self.rel_screen_width=self.frame.winfo_screenwidth()/1536 # relative width size of other monitor
        self.rel_screen_height=self.frame.winfo_screenheight()/864 # relative height
        self.rel_screen_value=(self.rel_screen_width+self.rel_screen_height)/2 # relative value

        self.Xcent=self.frame.winfo_screenwidth()/2 # center of Screen
        self.Ycent=self.frame.winfo_screenheight()/2-50

        self.queue=queue_remote # queue setting
        
        self.lgt_level=0 # light configure

        #self.music_select=0 # music play related variable
        #self.player=0

        self.time_state=False # False-> standard time / True -> Am Pm time

        self.oper_time=0; self.hour=0; self.min=0; self.sec=0; # background real-time

        self.listOfDay=list() # Day of week list(Canvas object)
        #self.weekend_list=['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'] # Day of Week lists
        self.dayOfWeek=list() # Day of week list(Text)- i made this because i can't refer to the canvas object from another function


        self.q=Queue() # for alarm node communication
        self.alarm_num=0 # number of alarm clock
        self.alarm_list=dict() # list of alarm object
        
        self.temp_on=False
        self.dhtDevice=adafruit_dht.DHT11(board.D18) # dht-11 sensor
        self.BMPDevice=BMP085.BMP085() # BMP180 sensor

        self.tempq=Queue()
        
        self.set_background('images/background.png') #setting background


    def set_background(self,img):
        img=Image.open(img)#resize and convert background for tk
        resized_image=img.resize((self.frame.winfo_screenwidth(),self.frame.winfo_screenheight()))
        self.imgTk=ImageTk.PhotoImage(resized_image) #imgTk should be member
        self.canvas.create_image(0,0,image=self.imgTk,anchor='nw') #background image
        
        img_exit=Image.open('images/exit.png') # exit button
        resized_exit=img_exit.resize((math.ceil(150*self.rel_screen_width),math.ceil(150*self.rel_screen_height)))
        self.exit_Tk=ImageTk.PhotoImage(resized_exit)
        exit_btn=self.canvas.create_image(0,0,image=self.exit_Tk,anchor='nw')
        rel_mov(self.frame,self.canvas,exit_btn,3,1,7)
        self.canvas.tag_bind(exit_btn,'<Button-1>',exit)
        #ini_widget.append(exit_btn)

        width=self.frame.winfo_screenwidth()
        height=self.frame.winfo_screenheight()

        #clear_initial('<button-1>',self.canvas)
        root3=1.732
        x0=width/13
        y0=height/2
        points=[x0,y0-25,x0,y0+25,x0-(50*root3/2),y0]
        self.go_back=self.canvas.create_polygon(points, fill='black')

        x1=12*width/13
        y1=height/2
        points=[x1,y1-25,x1,y1+25,x1+(50*root3/2),y1]
        self.go_next=self.canvas.create_polygon(points,fill='black')

        self.canvas.tag_bind(self.go_back,'<Button-1>',lambda event:self.menu_switch(event,'back'))
        self.canvas.tag_bind(self.go_next,'<Button-1>',lambda event:self.menu_switch(event,'next'))

        self.digital_clock()

        t=threading.Thread(target=self.check_queue,args=(self.queue,)) #queue check(background processing)
        t.setDaemon(True)
        t.start()
    

    def hide_arrow(self,event): # hide the arrow widgets
        if self.arrow_true==True:
            self.canvas.itemconfig(self.go_back,state='hidden')
            self.canvas.itemconfig(self.go_next,state='hidden')
        else:
            self.canvas.itemconfig(self.go_back,state='normal')
            self.canvas.itemconfig(self.go_next,state='normal')
        
        self.arrow_true=not(self.arrow_true)


    def check_queue(self,queue): # background processing function(to communicate with flask process)
        print("queue thread is executing")

        while True:
            try:
                temp=queue.get_nowait()
                if (temp=='off'):
                    print('off button has pressed!')
                    _thread.interrupt_main()
                elif (temp=='back'):
                    print("back button has pressed!")
                    self.menu_switch('<Button-1>','back')
                elif (temp=='next'):
                    print("next button has pressed!")
                    self.menu_switch('<Button-1>','next')
                elif (temp=='H' or temp=='M' or temp=='S'):
                    if self.channel==2:
                        if temp=='H':
                            temp='hour'
                        elif temp=='M':
                            temp='min'
                        else:
                            temp='sec'
                        self.oper_dial('<Button-1>',temp)
                else: #0~9,set
                    if self.channel==2:
                        self.oper_dial('<Button-1>',temp)
            except: # if queue is empty
                print("[remote]:queue is empty")
            finally:
                time.sleep(1) # check every second


    def set_bright(self,event): #setting brightness function
        bck_light=Backlight()
        lgt_level=self.lgt_level % 5

        bck_light.brightness=lgt_level*25 # 0/25/50/75/100

        self.lgt_level+=1

    '''
    def music_play(self,event): # streaming music function(select music)
        if (self.player!=0):
            self.player.stop()

        self.music_select%=len(playlist)   
        self.player=vlc.MediaPlayer(playlist[self.music_select])
        self.player.play() # maybe using another thread so it should be stopped when next button
        self.music_select+=1
    

    def play_stop(self,event): # play and pause music function
        if (self.player!=0):
            self.player.pause()
        else:
            print("select music what you want")
    '''
    
    def menu_switch(self,event,string):
        if string == 'back': #switch the menu
            self.channel-=1
            
        else:
            self.channel+=1
        
        if (self.channel==-1):
            self.channel=3

        if (self.channel==4):
            self.channel=0
        
        if (self.channel==0):
            self.cancel_temp()
            self.temp_on=False
            self.digital_clock()

        if (self.channel==1):
            self.analog_clock() 
        
        if (self.channel==2):
            self.cancel_temp()
            self.temp_on=False
            self.alarm_clock()
        
        if (self.channel==3):
            self.temp_humid()


    def digital_clock(self):
        after_all(self.canvas)
        self.hide_arrow("<button-1>")
        
        now=datetime.datetime.now() # calculate current time
        date_str=now.strftime("%Y:%m:%d")+" "+datetime.datetime.today().strftime('%A') # date and dayofweek
        time_str=now.strftime("%H:%M:%S")

        self.time_Tk=self.canvas.create_text(0,0,text="00:00:00",font=("Helvetica",
        math.ceil(-250*self.rel_screen_value)),fill='white',anchor='nw')
        self.date_Tk=self.canvas.create_text(0,0,text="2021:00:00",font=("Terminal",
        math.ceil(-60*self.rel_screen_value)),fill='white',anchor='nw') # GUI
        rel_mov(self.frame,self.canvas,self.time_Tk,3,4,2)
        rel_mov(self.frame,self.canvas,self.date_Tk,3,5,3)
        self.canvas.move(self.date_Tk,0,30)
        text_widget.append(self.time_Tk)
        text_widget.append(self.date_Tk)
        self.canvas.tag_bind(self.time_Tk,'<Button-1>',lambda event:self.clock_call_back(event,'change'))
        self.canvas.tag_bind(self.date_Tk,"<Button-1>",self.hide_arrow)

        self.alarm_text=self.canvas.create_text(0,0,text="Next alarm:None",font=("Roman",
        math.ceil(-70*self.rel_screen_value)),fill='white',anchor='nw')
        rel_mov(self.frame,self.canvas,self.alarm_text,3,4,5)
        text_widget.append(self.alarm_text)


        if len(self.alarm_list)==0:
            self.canvas.itemconfig(self.alarm_text,text='Next alarm:None') # Next alarm text
        else:
            tmp_alarm_list=list(self.alarm_list.keys())
            tmp_data=self.alarm_list[tmp_alarm_list[0]]
            #data[0]:hour / data[1]:min / data[2]:sec / data[3]:dayofweek list
            clock_str=" %02d:%02d:%02d   " % (tmp_data[0],tmp_data[1],tmp_data[2])
            day_str=" "
            day_str_result=day_str.join(i[0:3] for i in tmp_data[3])
            tmp_alarm_text="Next alarm:"+clock_str+day_str_result
            self.canvas.itemconfig(self.alarm_text,text=tmp_alarm_text)        

        self.canvas.itemconfig(self.date_Tk,text=date_str)
        self.canvas.itemconfig(self.time_Tk,text=time_str)

        self.clock_call_back('<Button-1>')
    

    def clock_call_back(self,event,AmPm=None): # digital clock background
        now=datetime.datetime.now() 
        date_str=now.strftime("%Y:%m:%d")+" "+datetime.datetime.today().strftime('%A')
        
        if AmPm =='change':
            self.time_state= not(self.time_state)
         
        if self.time_state == False:
            time_str=now.strftime("%H:%M:%S")
            self.canvas.itemconfig(self.time_Tk,font=("Helvetica",math.ceil(-250*self.rel_screen_value)))

        else:
            tmp_time="  " # tmp_time comes PM or AM
            hour_part=int(now.strftime("%H"))
            if hour_part == 0:
                hour_part=12
                tmp_time='PM'
            elif 1<=hour_part<=12:
                tmp_time='AM'
            elif 13<=hour_part<=23:
                hour_part-=12
                tmp_time='PM'
            
            min_part=now.strftime("%M")
            sec_part=now.strftime("%S")

            time_str=str(hour_part)+":"+min_part+":"+sec_part+" "+tmp_time
            self.canvas.itemconfig(self.time_Tk,font=("Helvetica",math.ceil(-200*self.rel_screen_value)))
        
        self.canvas.itemconfig(self.date_Tk,text=date_str)
        self.canvas.itemconfig(self.time_Tk,text=time_str)

        self.after_id=self.canvas.after(1000,lambda:self.clock_call_back('<Button-1>')) # call function every one sec
        after_func['digital_clock']=self.after_id


    def analog_clock(self): #analog function
        after_all(self.canvas)

        self.arrow_true=False
        if self.canvas.itemcget(self.go_back,'state')=='normal' and self.canvas.itemcget(self.go_next,'state')=='normal':
            self.canvas.itemconfigure(self.go_back,state='hidden')
            self.canvas.itemconfigure(self.go_next,state='hidden')
        
        python_black="#000000"
     
        centerY=self.Ycent+50
        
        x1,y1=(self.Xcent-1,centerY-1) #draw all kind of shapes (circle, tips,numbers,,,, to draw analog clock)
        x2,y2=(self.Xcent+1,centerY+1)
        cent_dot=self.canvas.create_oval(x1,y1,x2,y2,fill=python_black) # of course you need to use trigonometric function
        shape_widget.append(cent_dot)

        x3,y3=self.Xcent-230,centerY-230
        x4,y4=self.Xcent+230,centerY+230
        clock_circle=self.canvas.create_oval(x3,y3,x4,y4,width=3,fill=python_black) # circle plate
        shape_widget.append(clock_circle)
        self.canvas.tag_bind(clock_circle,'<Button-1>',self.hide_arrow)

        self.PI=3.141592
        num_text=[str(x) for x in range(12)]

        for i in range(12):# numbers
            tmpx,tmpy=(180*math.sin(i*self.PI/6)+self.Xcent,-180*math.cos(i*self.PI/6)+centerY)
            clock_digit=self.canvas.create_text(tmpx,tmpy,text=num_text[i],font=("Helvetica",30),fill='white')
            shape_widget.append(clock_digit)


        for i in range(60): # white border lines
            if i%5 == 0:
                borderx,bordery=(210*math.sin(i*self.PI/30)+self.Xcent,-210*math.cos(i*self.PI/30)+centerY)
                borderxp,borderyp=(230*math.sin(i*self.PI/30)+self.Xcent,-230*math.cos(i*self.PI/30)+centerY)
                line_border=5
            else:
                borderx,bordery=(220*math.sin(i*self.PI/30)+self.Xcent,-220*math.cos(i*self.PI/30)+centerY)
                borderxp,borderyp=(230*math.sin(i*self.PI/30)+self.Xcent,-230*math.cos(i*self.PI/30)+centerY)
                line_border=2
            borders=self.canvas.create_line(borderx,bordery,borderxp,borderyp,fill='white',width=line_border)
            shape_widget.append(borders)

        # represent
        #central:250,250        #tips
        self.htip=self.canvas.create_line(self.Xcent,centerY,self.Xcent+130,self.Xcent,width=3,fill='red')#radius:70
        self.mtip=self.canvas.create_line(self.Xcent,centerY,self.Xcent,centerY-170,width=3,fill='white')#radius:100
        self.stip=self.canvas.create_line(self.Xcent,centerY,self.Xcent,centerY-200,width=3,fill='gray')#radius:130
        shape_widget.append(self.htip)
        shape_widget.append(self.mtip)
        shape_widget.append(self.stip)
        self.clock_mov(centerY)


    def clock_mov(self,Ycenter): # analog clock background
        sec=datetime.datetime.now().second
        mins=datetime.datetime.now().minute
        hr=datetime.datetime.now().hour
        if(hr>12):
            hr=hr%12
        #print(hr,mins,sec)
        self.canvas.coords(self.stip,self.Xcent,Ycenter,200*math.sin(sec*self.PI/30)+self.Xcent,-200*math.cos(sec*self.PI/30)+Ycenter)
        self.canvas.coords(self.mtip,self.Xcent,Ycenter,170*math.sin(mins*self.PI/30)+self.Xcent,-170*math.cos(mins*self.PI/30)+Ycenter)
        self.canvas.coords(self.htip,self.Xcent,Ycenter,130*math.sin(hr*self.PI/6+mins*(self.PI/6)/60)+self.Xcent,-130*math.cos(hr*self.PI/6+mins*(self.PI/6)/60)+Ycenter)
        self.analog_clck_after=self.canvas.after(1000,lambda:self.clock_mov(Ycenter))
        after_func['analog_clock']=self.analog_clck_after


    def alarm_clock(self,event=None): # alarm clock function
        after_all(self.canvas)
        if self.canvas.itemcget(self.go_back,'state')=='hidden' and self.canvas.itemcget(self.go_next,'state')=='hidden':
            self.canvas.itemconfigure(self.go_back,state='normal')
            self.canvas.itemconfigure(self.go_next,state='normal')

        self.hour=0 ; self.min=0;self.sec=0

        self.hour_id=self.canvas.create_text(0,0,text='Hour:00',font=('Helvetica',
        math.ceil(50*self.rel_screen_value)),fill='white',anchor='nw') #Hour
        self.min_id=self.canvas.create_text(0,0,text='Minute:00',font=('Helvetica',
        math.ceil(50*self.rel_screen_value)),fill='white',anchor='nw') #Minute
        self.sec_id=self.canvas.create_text(0,0,text='Second:00',font=('Helvetica',
        math.ceil(50*self.rel_screen_value)),fill='white',anchor='nw') #Second
        
        self.select_day=self.canvas.create_text(0,0,text='DayOfWeek',font=('Helvetica',
        math.ceil(30*self.rel_screen_value)),fill='white',anchor='nw') # day of week
        rel_mov(self.frame,self.canvas,self.select_day,3,1,1)
        text_widget.append(self.select_day)
        self.canvas.tag_bind(self.select_day,'<Button-1>',self.set_dayofweek)

        self.show_alarms=self.canvas.create_text(0,0,text='Alarm list',font=('Helvetica',
        math.ceil(30*self.rel_screen_value)),fill='white',anchor='nw') # day of week
        rel_mov(self.frame,self.canvas,self.show_alarms,3,1,2)
        text_widget.append(self.show_alarms)
        self.canvas.tag_bind(self.show_alarms,'<Button-1>',self.print_alarms)

        self.dial_list=list() # the list of number pads (1~9,0,'set','<-')
        x_inter=15 ; y_inter=15 # interval
        x_size=50 ; y_size=50 # size of X,Y
        oval_border=3; #dial_font=30 # oval_border,font
        oval_color='black'
        text_color='white'
    
        x_crd=self.Xcent-(x_size/2)-x_inter-x_size
        y_crd=self.Ycent+(y_size/2)

        x_crd_p=x_crd+x_size
        y_crd_p=y_crd+y_size

        for i in range(0,3): # number pad(1~9)
            for j in range(1,4):
                dial_tmp=self.canvas.create_oval(x_crd,y_crd,x_crd_p,y_crd_p,outline='black',width=oval_border,fill=oval_color)
                shape_widget.append(dial_tmp)
                dial_tmp_txt=self.canvas.create_text((x_crd+x_crd_p)/2,(y_crd+y_crd_p)/2,font=("Roman",30),text=str(j+i*3),fill=text_color)
                text_widget.append(dial_tmp_txt)
                self.dial_list.append(dial_tmp_txt)
                x_crd+=x_size+x_inter ; x_crd_p=x_crd+x_size ; y_crd_p=y_crd+y_size
            
            y_crd+=y_size+y_inter; x_crd=x_crd-3*(x_size+x_inter)
            x_crd_p=x_crd+x_size; y_crd_p=y_crd+y_size
        
        x_crd+=x_size+x_inter; #number pad (0)
        x_crd_p=x_crd+x_size ; y_crd_p=y_crd+y_size
        dial_tmp=self.canvas.create_oval(x_crd,y_crd,x_crd_p,y_crd_p,outline='black',width=oval_border,fill=oval_color)
        shape_widget.append(dial_tmp)
        dial_tmp_txt=self.canvas.create_text((x_crd+x_crd_p)/2,(y_crd+y_crd_p)/2,font=("Roman",30),text='0',fill=text_color)
        text_widget.append(dial_tmp_txt)
        self.dial_list.append(dial_tmp_txt)

        x_crd+=x_size+x_inter # number pad ('set')
        x_crd_p=x_crd+x_size ; y_crd_p=y_crd+y_size
        set_clk=self.canvas.create_oval(x_crd,y_crd,x_crd_p,y_crd_p,outline='black',width=oval_border,fill=oval_color)
        shape_widget.append(set_clk)
        set_clk_txt=self.canvas.create_text((x_crd+x_crd_p)/2,(y_crd+y_crd_p)/2,font=('Roman',20),text='set',fill=text_color)
        text_widget.append(set_clk_txt)
        self.dial_list.append(set_clk_txt)
        
        #self.canvas.coords(self.hour_id,0,0) # hour_id coords, text, font change
        rel_mov(self.frame,self.canvas,self.hour_id,3,3,1)
        self.canvas.itemconfig(self.hour_id,text="%02d:" % 0)
        self.canvas.itemconfig(self.hour_id,font=("Helvetica",80))

        #self.canvas.coords(self.min_id,0,0) # same change to min_id
        rel_mov(self.frame,self.canvas,self.min_id,3,5,1)
        self.canvas.itemconfig(self.min_id,text="%02d:" % 0)
        self.canvas.itemconfig(self.min_id,font=("Helvetica",80))

        #self.canvas.coords(self.sec_id,0,0) # same change to sec_id
        rel_mov(self.frame,self.canvas,self.sec_id,3,7,1)
        self.canvas.itemconfig(self.sec_id,text="%02d" % 0)
        self.canvas.itemconfig(self.sec_id,font=("Helvetica",80))
        
        text_widget.append(self.hour_id)
        text_widget.append(self.min_id)
        text_widget.append(self.sec_id)

        self.canvas.tag_bind(self.hour_id,'<Button-1>',lambda event:self.oper_dial(event,'hour')) # binding to the oper_dial
        self.canvas.tag_bind(self.min_id,'<Button-1>',lambda event:self.oper_dial(event,'min'))
        self.canvas.tag_bind(self.sec_id,'<Button-1>',lambda event:self.oper_dial(event,'sec'))


        self.Ten_digitOfclk={'hour':True,'min':True,'sec':True}

        #self.dial_list: 1~9 0 set '<-'
        
        # can't use for loop(it should be stated one by one)
        self.canvas.tag_bind(self.dial_list[0],'<Button-1>',lambda event:self.oper_dial(event,'1'))
        self.canvas.tag_bind(self.dial_list[1],'<Button-1>',lambda event:self.oper_dial(event,'2'))
        self.canvas.tag_bind(self.dial_list[2],'<Button-1>',lambda event:self.oper_dial(event,'3'))
        self.canvas.tag_bind(self.dial_list[3],'<Button-1>',lambda event:self.oper_dial(event,'4'))
        self.canvas.tag_bind(self.dial_list[4],'<Button-1>',lambda event:self.oper_dial(event,'5'))
        self.canvas.tag_bind(self.dial_list[5],'<Button-1>',lambda event:self.oper_dial(event,'6'))
        self.canvas.tag_bind(self.dial_list[6],'<Button-1>',lambda event:self.oper_dial(event,'7'))
        self.canvas.tag_bind(self.dial_list[7],'<Button-1>',lambda event:self.oper_dial(event,'8'))
        self.canvas.tag_bind(self.dial_list[8],'<Button-1>',lambda event:self.oper_dial(event,'9'))
        self.canvas.tag_bind(self.dial_list[9],'<Button-1>',lambda event:self.oper_dial(event,'0'))

        self.canvas.tag_bind(self.dial_list[10],'<Button-1>',lambda event:self.oper_dial(event,'set'))
        #self.canvas.tag_bind(self.dial_list[11],'<Button-1>',lambda event:self.oper_dial(event,'cancel'))

        
    def oper_dial(self,event,string): # change the color or hour,min,sec_id and if color is black and press dial, alarm changes
        num_list=[x for x in range(10)]
        num_list=[str(x) for x in num_list]
        #print(num_list)

        if string =='hour':
            if self.canvas.itemcget(self.hour_id,'fill') == 'white':
                self.canvas.itemconfig(self.hour_id,fill='black')
            else:
                self.canvas.itemconfig(self.hour_id,fill='white')
            
            self.canvas.itemconfig(self.min_id,fill='white')
            self.canvas.itemconfig(self.sec_id,fill='white')
        
        elif string=='min':
            if self.canvas.itemcget(self.min_id,'fill') == 'white':
                self.canvas.itemconfig(self.min_id,fill='black')
            else:
                self.canvas.itemconfig(self.min_id,fill='white')
            
            self.canvas.itemconfig(self.hour_id,fill='white')
            self.canvas.itemconfig(self.sec_id,fill='white')
        
        elif string=='sec':
            if self.canvas.itemcget(self.sec_id,'fill') == 'white':
                self.canvas.itemconfig(self.sec_id,fill='black')
            else:
                self.canvas.itemconfig(self.sec_id,fill='white')
            
            self.canvas.itemconfig(self.min_id,fill='white')
            self.canvas.itemconfig(self.hour_id,fill='white')
        
        elif string in num_list:

            txt_list=[self.hour_id,self.min_id,self.sec_id] # list of hour,minute,second
            result_txt=None #selected time standard
            result_indx=None # selected index of txt_list
            for i in range(0,len(txt_list)):
                if self.canvas.itemcget(txt_list[i],'fill') == 'black':
                    result_txt=txt_list[i]
                    result_indx=i # assign selected time standard

            if result_txt==None: # if all element's color is white(not setted)
                return
            
            selected_clk=self.canvas.itemcget(result_txt,'text')
            num_clk=int(''.join(i for i in selected_clk if i.isdigit())) # current clock value
            
            if result_indx==0: #hour control
                if self.Ten_digitOfclk['hour']==True:
                    result_clk='%02d'%(num_clk-((num_clk//10)*10)+10*int(string))
                else:
                    result_clk='%02d'%(num_clk-(num_clk%10)+int(string))
                
                if int(result_clk)>23:
                    self.Ten_digitOfclk['hour']=not(self.Ten_digitOfclk['hour'])
                    result_clk='%02d'%(num_clk)
                
                self.canvas.itemconfig(result_txt,text=result_clk+":")
                self.hour=int(result_clk)
                self.Ten_digitOfclk['hour']=not(self.Ten_digitOfclk['hour']) # reverse the ten digit's of each clock
            elif result_indx==1: #minute control
                if self.Ten_digitOfclk['min']==True:
                    result_clk='%02d'%(num_clk-((num_clk//10)*10)+10*int(string))
                else:
                    result_clk='%02d'%(num_clk-(num_clk%10)+int(string))
                
                if int(result_clk)>59:
                    self.Ten_digitOfclk['min']=not(self.Ten_digitOfclk['min'])
                    result_clk='%02d'%(num_clk)
                    
                self.canvas.itemconfig(result_txt,text=result_clk+":")
                self.min=int(result_clk)
                self.Ten_digitOfclk['min']=not(self.Ten_digitOfclk['min'])
            else: #second control
                if self.Ten_digitOfclk['sec']==True:
                    result_clk='%02d'%(num_clk-((num_clk//10)*10)+10*int(string))
                else:
                    result_clk='%02d'%(num_clk-(num_clk%10)+int(string))
                
                if int(result_clk)>59:
                    result_clk='%02d'%(num_clk)
                    self.Ten_digitOfclk['sec']=not(self.Ten_digitOfclk['sec'])
                    
                self.canvas.itemconfig(result_txt,text=result_clk)
                self.sec=int(result_clk)
                self.Ten_digitOfclk['sec']=not(self.Ten_digitOfclk['sec'])
            print(self.hour,self.min,self.sec)
        
        elif string =='set': # if you press set button -> the alarm will be setted
            after_all(self.canvas)
            self.alarm_num+=1
            alarm_str="%02d:%02d:%02d setted" % (self.hour,self.min,self.sec)
            #print(alarm_str)
            set_pop_up=self.canvas.create_text(0,0,text=alarm_str,fill='white',font=("Helvetica",50))
            self.canvas.coords(set_pop_up,self.Xcent,self.Ycent)
            self.canvas.tag_bind(set_pop_up,'<Button-1>',self.alarm_clock)
            text_widget.append(set_pop_up)


            #added: put the day of week information too
            local_dayOfweek=list() # why i use this: the sub thread refer to the global list when i use self.dayOfWeek
            if len(self.dayOfWeek)==0: #it means self.dayOfWeek is also empty list
                local_dayOfweek.append(datetime.datetime.today().strftime('%A'))
            else:
                for i in self.dayOfWeek:
                    local_dayOfweek.append(i)

            data=[self.hour,self.min,self.sec,local_dayOfweek]
            alarm_name="alarm"+str(self.alarm_num)

            alarm_thread=Alarm(name=alarm_name,args=(data,self.q)) # Alarm object(which contains thread)
            alarm_thread.setDaemon(True)
            alarm_thread.start()

            self.alarm_list[alarm_name]=data # dictionary of alarm_name:alarm_data

            self.alarm_name_list=list(self.alarm_list.keys()) # list of alarm_list's keys
            print(self.alarm_list)

            self.check_alarm() # the GUI also process the checking for the signal by alarm class when the alarm rings

    def check_alarm(self):
        try:
            signal=self.q.get_nowait() # check the signal
            if signal[-4:]=='exit':
                self.q.put(signal)
            elif signal[-4:]=='5min':
                self.q.put(signal)
            else:
                pass

            for e in self.alarm_name_list: # alarm_list contains various alarm set (you can set many alarms at the same time)
                if signal==e:
                    after_all(self.canvas)

                    if self.canvas.itemcget(self.go_back,'state')=='normal' and self.canvas.itemcget(self.go_next,'state')=='normal':
                        self.canvas.itemconfigure(self.go_back,state='hidden')
                        self.canvas.itemconfigure(self.go_next,state='hidden')

                    alarm_img=Image.open('images/alarm.png') # alarm image
                    resized_alarm=alarm_img.resize((math.ceil(300*self.rel_screen_width),math.ceil(300*self.rel_screen_height)))
                    self.alarm_img_Tk=ImageTk.PhotoImage(resized_alarm)
                    alarm_draw=self.canvas.create_image(0,0,image=self.alarm_img_Tk,anchor='nw')
                    rel_mov(self.frame,self.canvas,alarm_draw,3,4,2)
                    img_widget.append(alarm_draw)

                    pop_alarm=self.alarm_list[e] # alert that alarm is ringing
                    pop_alarm_time="%02d:%02d:%02d"%(pop_alarm[0],pop_alarm[1],pop_alarm[2])
                    pop_alarm_dayOfWeek=pop_alarm[3]
                    clock_info=self.canvas.create_text(0,0,text=pop_alarm_time,font=("Helvetica",
                    math.ceil(-100*self.rel_screen_value)),fill='white',anchor='nw') # GUI
                    date_info=self.canvas.create_text(0,0,text=pop_alarm_dayOfWeek,font=("Helvetica",
                    math.ceil(-50*self.rel_screen_value)),fill='white',anchor='nw')
                    rel_mov(self.frame,self.canvas,clock_info,3,4,4)
                    rel_mov(self.frame,self.canvas,date_info,3,4,5)
                    text_widget.append(clock_info)
                    text_widget.append(date_info)

                    #later_btn=self.canvas.create_oval(self.Xcent-50,self.Ycent-50,self.Xcent+50,self.Ycent+50,outline='black',width=3,fill='black')
                    later_text=self.canvas.create_text(0,0,text="later",font=("Helvetica",math.ceil(-80*self.rel_screen_value)),fill='white')
                    rel_mov(self.frame,self.canvas,later_text,3,3,7)
                    text_widget.append(later_text)

                    cancel_text=self.canvas.create_text(0,0,text="cancel",font=("Helvetica",math.ceil(-80*self.rel_screen_value)),fill='white')
                    rel_mov(self.frame,self.canvas,cancel_text,3,6,7)
                    text_widget.append(cancel_text)


                    self.canvas.tag_bind(later_text,'<Button-1>',lambda evt:self.deal_user_alarm_input(evt,'5min',signal))
                    self.canvas.tag_bind(cancel_text,'<Button-1>',lambda evt:self.deal_user_alarm_input(evt,'cancel',signal))

        except:
            print("[Main_Thread]:checking alarm_signal")
        finally:
            if len(self.alarm_list)!=0:
                self.alarm_check=self.canvas.after(1000,self.check_alarm)
                after_func['alarm_clock']=self.alarm_check # it is not appended to the nameOfAfter list(not working in after_all)
    
    def deal_user_alarm_input(self,event,string,msg): # deal with the signal when alarm rings
        after_all(self.canvas)
        list_clear(self.canvas,'func','alarm_clock')
        if string=='5min':
            self.alarm_clock()
            self.check_alarm() # it keeps checking
            print(msg+"5min")
            self.q.put(msg+"5min")
        else: # cancel
            self.alarm_clock()
            self.q.put(msg+"exit")
            del self.alarm_list[msg]
            process=Process(target=alarm_sound)
            process.daemon=True
            process.start()


    def set_dayofweek(self,event): # set the Day of week function
        if self.canvas.itemcget(self.go_back,'state')=='normal' and self.canvas.itemcget(self.go_next,'state')=='normal':
            self.canvas.itemconfigure(self.go_back,state='hidden')
            self.canvas.itemconfigure(self.go_next,state='hidden')

        after_all(self.canvas)

        weekend_list=['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
        self.listOfDay.clear()
        self.dayOfWeek.clear()

        position=1
        #self.listOfDay=list() # the list about day of weeks for alarm
        for day in weekend_list:
            tmp=self.canvas.create_text(0,0,text=day,font=("Helvetica",
            math.ceil(-50*self.rel_screen_value)),fill='white',anchor='nw')
            rel_mov(self.frame,self.canvas,tmp,3,4,position)
            text_widget.append(tmp)
            self.listOfDay.append(tmp)
            self.dayOfWeek.append(day)
            position+=1

        # tag_bind can't use for loop because the parameter is treated as a variable so last item only binded
        self.canvas.tag_bind(self.listOfDay[0],'<Button-1>',lambda event:self.assign_dayofweek(event,self.listOfDay[0]))
        self.canvas.tag_bind(self.listOfDay[1],'<Button-1>',lambda event:self.assign_dayofweek(event,self.listOfDay[1]))
        self.canvas.tag_bind(self.listOfDay[2],'<Button-1>',lambda event:self.assign_dayofweek(event,self.listOfDay[2]))
        self.canvas.tag_bind(self.listOfDay[3],'<Button-1>',lambda event:self.assign_dayofweek(event,self.listOfDay[3]))
        self.canvas.tag_bind(self.listOfDay[4],'<Button-1>',lambda event:self.assign_dayofweek(event,self.listOfDay[4]))
        self.canvas.tag_bind(self.listOfDay[5],'<Button-1>',lambda event:self.assign_dayofweek(event,self.listOfDay[5]))
        self.canvas.tag_bind(self.listOfDay[6],'<Button-1>',lambda event:self.assign_dayofweek(event,self.listOfDay[6]))
        # These are tag binded for assign_day of week method

        self.set_dayOfWeek=self.canvas.create_text(0,0,text="set",font=("Helvetica",
        math.ceil(-50*self.rel_screen_value)),fill='white',anchor='nw') # text for setting days of week
        rel_mov(self.frame,self.canvas,self.set_dayOfWeek,3,5,3)
        text_widget.append(self.set_dayOfWeek)
        self.canvas.tag_bind(self.set_dayOfWeek,'<Button-1>',self.oper_dayOfWeek) # click and perform oper_day of week method


    def assign_dayofweek(self,event,day):
        color=self.canvas.itemcget(day, "fill") # white color: not setted for alarm / black color: setted for alarm
        if color == 'white':
            self.canvas.itemconfig(day,fill='black')
        elif color == 'black':
            self.canvas.itemconfig(day,fill='white')


    def oper_dayOfWeek(self,event):
        tmp_list=list() # temp list stores the index of the day of week which is going to be erased in self.listofday

        for day_count in range(0,len(self.listOfDay)): # remove the member whose color is not black(not set for alarm)
            if (self.canvas.itemcget(self.listOfDay[day_count],"fill")=="white"):
                tmp_list.append(day_count)
        #print(tmp_list)
        
        erase=0 # variable for erasing each element of which color is white
        for e in tmp_list:
            e-=erase # erase is accumulated if you erase element one by one
            self.canvas.delete(self.listOfDay[e])
            del self.listOfDay[e]
            del self.dayOfWeek[e]
            erase+=1
            
        position=1 # rearrange the days of week whose color is black
        for day in self.listOfDay:
            self.canvas.coords(day,0,0) # initialize the position
            rel_mov(self.frame,self.canvas,day,3,4,position) # reposition
            position+=1
        
        self.canvas.itemconfig(self.set_dayOfWeek,text='completed')
        alarm_clock_aft=self.canvas.after(3000,self.alarm_clock)
        after_func['tmp_alarm']=alarm_clock_aft
    
    def print_alarms(self,event): # printing alarm set function
        after_all(self.canvas)
        element_number=len(self.alarm_list)
        if element_number==0:
            alarm_0=self.canvas.create_text(self.Xcent,self.Ycent,text="Alarm is not setted",font=("Helvetica",50),fill='white')
            text_widget.append(alarm_0)
            self.canvas.tag_bind(alarm_0,'<Button-1>',self.alarm_clock)
        else:
            position=1
            alarm_list_keys=list(self.alarm_list.keys())
            bind_alarm_text=list() # just for temporary self variable
            for i in range(len(alarm_list_keys)):
                order_index=str(i+1)            
                real_index=alarm_list_keys[i]
                data_list=self.alarm_list[real_index]
                result="%02d:%02d:%02d" % (data_list[0],data_list[1],data_list[2])
                day_str=" "
                day_str_result=day_str.join(i[0:3] for i in data_list[3])
            
                alarm_x=self.canvas.create_text(0,0,text="Alarm{0} {1}".format(order_index,result),font=("Helvectica",math.ceil(-50*self.rel_screen_value)),fill='white',anchor='nw')
                rel_mov(self.frame,self.canvas,alarm_x,3,2,position)
                text_widget.append(alarm_x)
                bind_alarm_text.append(alarm_x)

                alarm_x_day=self.canvas.create_text(0,0,text=day_str_result,font=("Helvectica",math.ceil(-50*self.rel_screen_value)),fill='white',anchor='nw')
                rel_mov(self.frame,self.canvas,alarm_x_day,3,4,position)
                text_widget.append(alarm_x_day)

                position+=1
        
        try:
            self.canvas.tag_bind(bind_alarm_text[0],"<Button-1>",lambda event:self.cancel_alarm(event,alarm_list_keys[0]))
            self.canvas.tag_bind(bind_alarm_text[1],"<Button-1>",lambda event:self.cancel_alarm(event,alarm_list_keys[1]))
            self.canvas.tag_bind(bind_alarm_text[2],"<Button-1>",lambda event:self.cancel_alarm(event,alarm_list_keys[2]))
            self.canvas.tag_bind(bind_alarm_text[3],"<Button-1>",lambda event:self.cancel_alarm(event,alarm_list_keys[3]))
            self.canvas.tag_bind(bind_alarm_text[4],"<Button-1>",lambda event:self.cancel_alarm(event,alarm_list_keys[4]))
            self.canvas.tag_bind(bind_alarm_text[5],"<Button-1>",lambda event:self.cancel_alarm(event,alarm_list_keys[5]))
            self.canvas.tag_bind(bind_alarm_text[6],"<Button-1>",lambda event:self.cancel_alarm(event,alarm_list_keys[6]))
            self.canvas.tag_bind(bind_alarm_text[7],"<Button-1>",lambda event:self.cancel_alarm(event,alarm_list_keys[7]))
            self.canvas.tag_bind(bind_alarm_text[8],"<Button-1>",lambda event:self.cancel_alarm(event,alarm_list_keys[8]))
            self.canvas.tag_bind(bind_alarm_text[9],"<Button-1>",lambda event:self.cancel_alarm(event,alarm_list_keys[9]))
        except:
            pass

        go_back=self.canvas.create_text(0,0,text='Go back',font=("Helvectica",math.ceil(-50*self.rel_screen_value)),fill='white',anchor='nw')
        rel_mov(self.frame,self.canvas,go_back,3,4,7)  # go back button-> then go to alarm set menu
        text_widget.append(go_back)
        self.canvas.tag_bind(go_back,'<Button-1>',self.alarm_clock)

    def cancel_alarm(self,event,indx): # canceling the alarm -> if you press the alarm list's element you can cancel
        print(indx+"exit")
        self.q.put(indx+"exit")
        del self.alarm_list[indx]
        self.print_alarms("<Button-1>")

    ''' Not supported ( using python-vlc module)
    def alarm_sound(self): # alarm buzzing function
        if (self.player!=0):
            self.player.stop()
        
        sound='musics/alarm_sound.mp3'
        self.player=vlc.MediaPlayer(sound)
        self.player.play()
    '''
    def temp_humid(self): # showing temperature and humidity pressure etc..
        after_all(self.canvas)

        self.arrow_true=False
        if self.canvas.itemcget(self.go_back,'state')=='normal' and self.canvas.itemcget(self.go_next,'state')=='normal':
            self.canvas.itemconfigure(self.go_back,state='hidden')
            self.canvas.itemconfigure(self.go_next,state='hidden')

        self.control_temp=False # it is only used in this method and background temp method

        self.temperature=self.canvas.create_text(0,0,text="0°C",font=("Helvetica",math.ceil(180*self.rel_screen_value)),fill="White",anchor="nw")
        rel_mov(self.frame,self.canvas,self.temperature,3,2,2) #alarm sign
        text_widget.append(self.temperature)
        #self.canvas.tag_bind(self.temperature,'<Button-1>',lambda event:self.back_temp_humid(event,'change_temp'))

        home_img=Image.open('images/home_black.png') # exit button
        resized_home=home_img.resize((math.ceil(350*self.rel_screen_width),math.ceil(350*self.rel_screen_height)))
        self.home_img_Tk=ImageTk.PhotoImage(resized_home)
        home_pic=self.canvas.create_image(0,0,image=self.home_img_Tk,anchor='nw')
        rel_mov(self.frame,self.canvas,home_pic,3,2,5)
        self.canvas.move(home_pic,30,0)
        img_widget.append(home_pic)
        self.canvas.tag_bind(home_pic,'<Button-1>',self.hide_arrow)

        ''' # if you want the temperature of this standard you can use
        self.temp_F=self.canvas.create_text(0,0,text="0°F",font=("Helvetica",math.ceil(45*self.rel_screen_value)),fill="White",anchor="nw")
        rel_mov(self.frame,self.canvas,self.temp_F,3,4,2) #alarm sign
        text_widget.append(self.temp_F)
        '''
        
        self.humidity=self.canvas.create_text(0,0,text="humidity:"+"--"+"%",font=("Helvetica",math.ceil(40*self.rel_screen_value)),fill="White",anchor="nw")
        rel_mov(self.frame,self.canvas,self.humidity,3,5,3) #humidity
        text_widget.append(self.humidity)
        
        self.pressure=self.canvas.create_text(0,0,text='pressure:'+"--"+"Pa", # pressure
        font=("Helvetica",math.ceil(37*self.rel_screen_value)),fill="White",anchor="nw")
        rel_mov(self.frame,self.canvas,self.pressure,3,5,4)
        text_widget.append(self.pressure)

        self.altitude=self.canvas.create_text(0,0,text='altitude:'+"--"+"m", # altitude
        font=("Helvetica",math.ceil(35*self.rel_screen_value)),fill="White",anchor="nw")
        rel_mov(self.frame,self.canvas,self.altitude,3,5,5)
        text_widget.append(self.altitude)

        
        self.sealevel_Pressure=self.canvas.create_text(0,0,text='sea level Pressure:'+"--"+"Pa", # pressure from sea level
        font=("Helvetica",math.ceil(30*self.rel_screen_value)),fill="White",anchor="nw")
        rel_mov(self.frame,self.canvas,self.sealevel_Pressure,3,5,6)
        text_widget.append(self.sealevel_Pressure)

        img_bright=Image.open('images/brightness.png') # setting brightness button
        resized_bright=img_bright.resize((math.ceil(100*self.rel_screen_width),math.ceil(100*self.rel_screen_height)))
        self.bright_Tk=ImageTk.PhotoImage(resized_bright)
        bright_btn=self.canvas.create_image(0,0,image=self.bright_Tk,anchor='nw')
        rel_mov(self.frame,self.canvas,bright_btn,3,3,3)
        self.canvas.tag_bind(bright_btn,'<Button-1>',self.set_bright)
        self.canvas.move(bright_btn,0,30)
        img_widget.append(bright_btn)

        process=Process(target=self.back_temp_humid,args=(self.tempq,)) # background processing
        process.daemon=True 
        process.start()

        self.temp_on=True # this is the indicator that background processing is now on
        self.receive_temp() # GUI also check the information and apply to the widget

    def receive_temp(self):
        try:
            response=self.tempq.get_nowait()
            if response=='back_exit':
                self.tempq.put(response)
                time.sleep(0.3)
            self.canvas.itemconfig(self.temperature,text=("{:.0f}°C".format(response[0]))) #itemconfig the widget
            self.canvas.itemconfig(self.humidity,text=("humidity:{:.0f}%".format(response[1])))
            self.canvas.itemconfig(self.pressure,text=("pressure:{0:.0f}Pa".format(response[2])))
            self.canvas.itemconfig(self.altitude,text=("altitude:{0:0.2f}m".format(response[3])))
            self.canvas.itemconfig(self.sealevel_Pressure,text=("sea level pressure:{0:.0f}Pa".format(response[4])))
            
        except:
            print("[receive_temp]:checking temp...")

        temp_id=self.canvas.after(1000,self.receive_temp) # operated by one second
        after_func['dht_check']=temp_id


    def back_temp_humid(self,queue): # we can't assign again this DHT sensor object so i declared in the self variable
        #dhtDevice=adafruit_dht.DHT11(board.D18) # dht-11 sensor  
        #BMPDevice=BMP085.BMP085() # BMP180 sensor
        while True:
            try:
                signal=queue.get_nowait()
                if signal != 'back_exit': # dealing with wrong signal
                    queue.put(signal)
                    time.sleep(1)
                else:
                    print("exit the back_temp")
                    break
            except:
                try:
                    info_list=list()
                    temperature_c = self.dhtDevice.temperature
                    #temperature_f = temperature_c * (9 / 5) + 32
                    humidity = self.dhtDevice.humidity

                    pressure=self.BMPDevice.read_pressure() # sensing the information
                    altitude=self.BMPDevice.read_altitude()
                    sealevel_pressure=self.BMPDevice.read_sealevel_pressure()

                    info_list.append(temperature_c)
                    info_list.append(humidity)
                    info_list.append(pressure)
                    info_list.append(altitude)
                    info_list.append(sealevel_pressure)
                    
                    print("Temp:{:.1f}C Humidity: {}% ".format(temperature_c,humidity))

                    queue.put(info_list) # and put to the queue
                    time.sleep(0.5)
                    
                except RuntimeError as error:
                    print(error.args[0])
                    print("Runtime error has occured!")
                    
                except Exception as error:
                    #dhtDevice.exit()
                    print("Exception error has occured")
                    raise error
                finally:
                    time.sleep(2) # call by 2 seconds


    def cancel_temp(self): # cancelling the background process whenever user skip the page
        if self.temp_on==True:
            try:
                signal=self.tempq.get_nowait()
                self.tempq.put(signal)
                time.sleep(0.5)
                self.tempq.put('back_exit')
            except:
                self.tempq.put('back_exit')
        else:
            print("back temp is not setted")
            pass

def main(queue):
    if os.environ.get('DISPLAY','') == '': #display setting(only for ssh connection used by visual studio )
        print('no display found. Using :0.0')
        os.environ.__setitem__('DISPLAY', ':0.0')
        os.system("export display=:0.0")
        os.system("xhost +")

    root=Tk() 
    touch_screen=TouchScreen(root,queue) # why i use queue?-> only for flask(remote control)
    mainloop()    


if __name__=="__main__":
    print("it is executed in terminal")
    queue=Queue() #Empty queue
    main(queue)



















# Unused code
'''
    def display_menu_text(self):
        #list_clear(self.canvas,'text')
        #list_clear(self.canvas,'img')
        after_all(self.canvas)
        #list_clear(self.canvas,'func','dht_check')

        def_pix=70 # pixel for default text
        self.default_text=self.canvas.create_text(0,0,text="Alarm clock menu",font=("Helvetica",math.ceil(def_pix*self.rel_screen_value))
        ,fill="white",anchor="nw") # menu text
        rel_mov(self.frame,self.canvas,self.default_text,3,4,1) # move to center(considered resolution)
        text_widget.append(self.default_text)

'''
'''
        select_img=Image.open('select.png') #select button
        resized_sel=select_img.resize((math.ceil(150*self.rel_screen_width),math.ceil(110*self.rel_screen_height)))
        self.sel_Tk=ImageTk.PhotoImage(resized_sel)
        self.select_btn=self.canvas.create_image(0,0,image=self.sel_Tk,anchor='nw')
        rel_mov(self.frame,self.canvas,self.select_btn,3,6,5)
        self.canvas.tag_bind(self.select_btn,'<Button-1>',lambda event:self.bg_alarm_clock(event,"select"))
        self.canvas.tag_bind(self.select_btn,'<Double-Button-1>',self.alarm_clear)
        img_widget.append(self.select_btn)

        up_img=Image.open('up.png') #up button
        resized_up=up_img.resize((math.ceil(100*self.rel_screen_width),math.ceil(100*self.rel_screen_height)))
        self.up_Tk=ImageTk.PhotoImage(resized_up)
        self.up_btn=self.canvas.create_image(0,0,image=self.up_Tk,anchor='nw')
        rel_mov(self.frame,self.canvas,self.up_btn,3,7,5)
        self.canvas.tag_bind(self.up_btn,'<Button-1>',lambda event:self.bg_alarm_clock(event,"up"))
        img_widget.append(self.up_btn)

        down_img=Image.open('down.png') #down button
        resized_down=down_img.resize((math.ceil(100*self.rel_screen_width),math.ceil(100*self.rel_screen_height)))
        self.down_Tk=ImageTk.PhotoImage(resized_down)
        self.down_btn=self.canvas.create_image(0,0,image=self.down_Tk,anchor='nw')
        rel_mov(self.frame,self.canvas,self.down_btn,3,7,7)
        self.canvas.tag_bind(self.down_btn,'<Button-1>',lambda event:self.bg_alarm_clock(event,"down"))
        img_widget.append(self.down_btn)


        ok_img=Image.open('ok.png') #ok button
        resized_ok=ok_img.resize((math.ceil(100*self.rel_screen_width),math.ceil(100*self.rel_screen_height)))
        self.ok_Tk=ImageTk.PhotoImage(resized_ok)
        self.ok_btn=self.canvas.create_image(0,0,image=self.ok_Tk,anchor='nw')
        rel_mov(self.frame,self.canvas,self.ok_btn,3,6,7)
        self.canvas.tag_bind(self.ok_btn,'<Button-1>',lambda event:self.bg_alarm_clock(event,"ok"))
        img_widget.append(self.ok_btn)
'''
'''
    def bg_alarm_clock(self,event,string):
        if (string=="select"):
            self.oper_time=(self.oper_time+1)%3 # oper_time:0,1,2
            
        if (string=="up"):
            if (self.oper_time==0):
                self.hour=(self.hour+1)%24 #hour:0~23
                temp=("Hour:%02d" % (self.hour))
                self.canvas.itemconfig(self.hour_id,text=temp)
            elif (self.oper_time==1):
                self.min=(self.min+1)%60 #min:0~59
                temp=("Minute:%02d" % (self.min))
                self.canvas.itemconfig(self.min_id,text=temp)
            else:
                self.sec=(self.sec+1)%60 #sec:0~59
                temp=("Second:%02d" % (self.sec))
                self.canvas.itemconfig(self.sec_id,text=temp)
        
        if (string=="down"):
            if (self.oper_time==0):
                self.hour=(self.hour-1+24)%24 #hour:0~23
                temp=("Hour:%02d" % (self.hour))
                self.canvas.itemconfig(self.hour_id,text=temp)
            elif (self.oper_time==1):
                self.min=(self.min-1+60)%60 #min:0~59
                temp=("Minute:%02d" % (self.min))
                self.canvas.itemconfig(self.min_id,text=temp)
            else:
                self.sec=(self.sec-1+60)%60 #sec:0~59
                temp=("Second:%02d" % (self.sec))
                self.canvas.itemconfig(self.sec_id,text=temp)

        if (string=="ok"):
            self.if_alarm=True

            list_clear(self.canvas,'img')
            list_clear(self.canvas,'text')
            list_clear(self.canvas,'func','alarm_clock')

            self.alarm_sign=self.canvas.create_text(0,0,text="Wait...",font=("Helvetica",math.ceil(70*self.rel_screen_value)),fill="White",anchor="nw")
            rel_mov(self.frame,self.canvas,self.alarm_sign,3,4,1) #alarm sign
            text_widget.append(self.alarm_sign)
            self.canvas.tag_bind(self.alarm_sign,'<Button-1>',lambda event:clear_initial(event,self.canvas))

            self.check_alarm() # function that checks alarm
'''    
'''
    def check_alarm(self): # comparing current time and setup time
        if (datetime.datetime.now().hour==self.hour) and (datetime.datetime.now().minute==self.min) and (datetime.datetime.now().second==self.sec):

            after_all(self.canvas)

            self.oper_time=0;self.hour=0;self.min=0;self.sec=0

            self.alarm_sign=self.canvas.create_text(0,0,text="alarm ring!",font=("Helvetica",math.ceil(70*self.rel_screen_value)),fill="White",anchor="nw")
            rel_mov(self.frame,self.canvas,self.alarm_sign,3,4,1) #alarm sign
            text_widget.append(self.alarm_sign)

            self.alarm_sound() # alarm sound

            return #escape function
             
        print(datetime.datetime.now().strftime("Time:%H:%M:%S"))
        self.check_after=self.canvas.after(1000,self.check_alarm)
        after_func['alarm_clock']=self.check_after
'''
'''
def clear_initial(event,canvas): # next button,music,bright related widget clear
    global ini_ctrl
    if (ini_ctrl):
        for i in ini_widget:
            canvas.itemconfigure(i,state='hidden')
    else:
        for i in ini_widget:
            canvas.itemconfigure(i,state='normal')
    
    ini_ctrl=not(ini_ctrl)
'''
'''

        img_btn=Image.open('button.png') # menu button
        resized_btn=img_btn.resize((math.ceil(200*self.rel_screen_width),math.ceil(200*self.rel_screen_height)))
        self.btn_Tk=ImageTk.PhotoImage(resized_btn)
        menu_btn=self.canvas.create_image(0,0,image=self.btn_Tk,anchor='nw')
        rel_mov(self.frame,self.canvas,menu_btn,3,4,7)
        self.canvas.tag_bind(menu_btn,'<Button-1>',self.btn_click)
        ini_widget.append(menu_btn)

        img_exit=Image.open('exit.png') # exit button
        resized_exit=img_exit.resize((math.ceil(150*self.rel_screen_width),math.ceil(150*self.rel_screen_height)))
        self.exit_Tk=ImageTk.PhotoImage(resized_exit)
        exit_btn=self.canvas.create_image(0,0,image=self.exit_Tk,anchor='nw')
        rel_mov(self.frame,self.canvas,exit_btn,3,1,7)
        self.canvas.tag_bind(exit_btn,'<Button-1>',exit)
        ini_widget.append(exit_btn)

        img_bright=Image.open('brightness.png') # setting brightness button
        resized_bright=img_bright.resize((math.ceil(100*self.rel_screen_width),math.ceil(100*self.rel_screen_height)))
        self.bright_Tk=ImageTk.PhotoImage(resized_bright)
        bright_btn=self.canvas.create_image(0,0,image=self.bright_Tk,anchor='nw')
        rel_mov(self.frame,self.canvas,bright_btn,3,7,1)
        self.canvas.tag_bind(bright_btn,'<Button-1>',self.set_bright)
        ini_widget.append(bright_btn)

        img_music_slt=Image.open('music_select.png') # choosing music button
        resized_music=img_music_slt.resize((math.ceil(100*self.rel_screen_width),math.ceil(100*self.rel_screen_height)))
        self.music_Tk=ImageTk.PhotoImage(resized_music)
        music_btn=self.canvas.create_image(0,0,image=self.music_Tk,anchor='nw')
        rel_mov(self.frame,self.canvas,music_btn,3,1,4)
        self.canvas.tag_bind(music_btn,'<Button-1>',self.music_play)
        ini_widget.append(music_btn)

        img_play_pause=Image.open('pause.png') # play and pause music button
        resized_play_pause=img_play_pause.resize((math.ceil(100*self.rel_screen_width),math.ceil(100*self.rel_screen_height)))
        self.play_pause_Tk=ImageTk.PhotoImage(resized_play_pause)
        play_pause_btn=self.canvas.create_image(0,0,image=self.play_pause_Tk,anchor='nw')
        rel_mov(self.frame,self.canvas,play_pause_btn,3,1,5)
        self.canvas.tag_bind(play_pause_btn,'<Button-1>',self.play_stop)
        ini_widget.append(play_pause_btn)
'''
'''
        x_crd+=x_size+x_inter ; y_crd-=2*(y_size+y_inter) #number pad ('<-')
        x_crd_p=x_crd+x_size ; y_crd_p=y_crd+y_size
        modi_clk=self.canvas.create_oval(x_crd,y_crd,x_crd_p,y_crd_p,outline='black',width=oval_border,fill=oval_color)
        shape_widget.append(modi_clk)
        modi_clk_txt=self.canvas.create_text((x_crd+x_crd_p)/2,(y_crd+y_crd_p)/2,font=('Roman',20),text='<-',fill=text_color)
        text_widget.append(modi_clk_txt)
        self.dial_list.append(modi_clk_txt)
'''