from flask import Flask,request
from flask import render_template,get_template_attribute
from raspberry_touch import *
from multiprocessing import Process,Queue

app=Flask(__name__)


@app.route("/") # default root
@app.route("/remote")
def start():
    return render_template('layout_web.html')

@app.route("/remote/on")
def on():
    try:
        global process,queue
        queue=Queue() 
        process=Process(target=main,args=(queue,)) 
        process.start()
        return 'on'

    except Exception as ex:
        print("error occured",ex)
        return "On error"
    
@app.route("/remote/off")
def off():
    try:
        queue.put('off') # next page signal
        return "off"
    except Exception as ex:
        print("Error occured",ex)
        return "Off error"

@app.route("/remote/back")
def back():
    try:
        queue.put('back') # next page signal
        return "back"
    except Exception as ex:
        print("Error occured",ex)
        return "back error"

@app.route("/remote/next")
def next():
    try:
        queue.put('next') # next page signal
        return "next"
    except Exception as ex:
        print("Error occured",ex)
        return "next error"

@app.route("/remote/clock/<time>")
def control_clock(time):
    try:
        queue.put(time) # hour min second
        return time
    except Exception as ex:
        print("Error occured",ex)
        return "control error"

@app.route("/remote/clock/<dial>")
def dial_oper(dial):
    try:
        queue.put(dial)
        return dial
    except Exception as ex:
        print("Error occured",ex)
        return "control error"


if __name__=="__main__":
    app.run(host="0.0.0.0",debug=True) 