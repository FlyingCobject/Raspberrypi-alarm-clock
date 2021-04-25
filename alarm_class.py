import threading
import time
import queue
import datetime

class Alarm(threading.Thread): # alarm class
    def __init__(self,args,name=""):
        threading.Thread.__init__(self)
        self.name=name
        self.data=args[0] # data list [hour,minute,second,dayOfWeek]
        self.queue=args[1] #queue

        self.hour=self.data[0] ; self.min=self.data[1] ; self.sec=self.data[2]
        self.dayOfWeek=self.data[3]
        #print(self.dayOfWeek)
    
    def run(self):
        'start()시 실제로 실행되는 부분'
        print("[{}] thread start: {}".format(threading.current_thread().getName(),self.data))
    
        while True:
            try:
                exit_sig=self.queue.get_nowait() # receive exit signal
                if exit_sig == self.name+"exit":
                    print(self.name,end='')
                    print("exits...",end='')
                    break
                else:
                    print("[{0}] wrong signal:{1}".format(threading.current_thread().getName(),exit_sig))
                    self.queue.put(exit_sig) #deal with the wrong signal
                    time.sleep(3)
            except:
                now=datetime.datetime.now()
                today=datetime.datetime.today().strftime("%A")
                if now.hour==self.hour and now.minute==self.min and now.second == self.sec: # background processing
                    if today not in self.dayOfWeek:
                        print("Not today")
                        time.sleep(0.1)
                        continue
                    time.sleep(2) # because another clock can put the value in the queue at the exact time
                    print("[{}]alarm ring".format(threading.current_thread().getName()))
                    self.queue.put(self.name) # input the name to the main thread
                    time.sleep(3)
                    while True: # send the signal to the GUI and wait for the signal
                        response=self.queue.get(block=True)
                        print("[{0}:{1}]".format(threading.current_thread().getName(),response))
                        if response==self.name+"exit":
                            print("[{}] terminates".format(self.name))
                            exit()
                        elif response==self.name+"5min": # this signal is for 5 minute longer button in GUI
                            self.min+=5
                            if self.min>=60:
                                self.hour+=1
                                self.min=self.min-60
                            break
                        else: # another thread's queue signal
                            time.sleep(1)
                            self.queue.put(response) # if alarmxmin alarmxexit -> re put
                else:
                    print("[{}]".format(threading.current_thread().getName()),end='')
                    print(now.strftime("%H:%M:%S "),end='')
                    print(self.name,self.hour,self.min,self.sec,self.dayOfWeek)
                    print()
                    time.sleep(1)
                    #print(self.dayOfWeek)
                    continue

        print("{} is end".format(threading.current_thread().getName())) # indicate the alarm is over

def main():
    # main is just for simple test don't mind
    q=queue.Queue() # 1개의 쓰레드와 통신
    data1=[20,45,10,['Monday','Wednesday','Saturday','Sunday']] # 시간 정보
    alarm_name1='alarm1' # 쓰레드 이름

    data2=[20,45,11,['Thursday','Sunday']]
    alarm_name2='alarm2'

    '''
    alarm_name3='alarm3'
    data3=[1,38,2,'Friday']
    '''
    alarm_thread1=Alarm(name=alarm_name1,args=(data1,q))
    alarm_thread1.setDaemon(True)
    alarm_thread1.start()

    alarm_thread2=Alarm(name=alarm_name2,args=(data2,q))
    alarm_thread2.setDaemon(True)
    alarm_thread2.start()
    
    '''
    alarm_thread3=Alarm(name=alarm_name3,args=(data3,q))
    alarm_thread3.setDaemon(True)
    alarm_thread3.start()
    '''
    
    alarm_list=dict()
    alarm_list[alarm_name1]=data1
    alarm_list[alarm_name2]=data2
    #alarm_list[alarm_name3]=True

    key_list=list(alarm_list.keys())

    print("[Main Thread] started")


    while True:
        try:
            signal=q.get_nowait()
            for e in key_list:
                if signal == e:
                    time.sleep(0.1)
                    q.put(signal+"5min")
                    #del alarm_list[signal]
            if len(alarm_list)==0:
                break
        except: #Empty 예외
            print("[Main_Thread]:checking...")
        finally:
            time.sleep(1)
    
    print("[Main_Thread] finshed")

    
if __name__=='__main__':
    main()