#!/bin/python
# -*- coding:UTF-8 -*-


import requests
import os
import socket
import time
import datetime
import re
import json
import threading
from Queue import Queue


AppFile = "/script/tomcatHealMoni/conf/app.info"
Webhook = "https://oapi.dingtalk.com/robot/send?access_token=XXXXXX"

#读取配置文件
def text_read(filename):
    try:
        file = open(filename,'r')
    except IOError:
        error = []
        return error
    content = file.readlines()

    for i in range(len(content)):
        content[i] = content[i][:len(content[i])-1]

    file.close()
    return content

def error_send(content,app):

    #获取本机IP
    hostname = socket.gethostname()
    ipaddr = socket.gethostbyname(hostname)

    #获取当前时间
    time_stamp = datetime.datetime.now()
    time = time_stamp.strftime('%Y.%m.%d-%H:%M:%S')

    info = '%s - %s - %s \n\n'%(time,ipaddr,app)

    data = {
            "msgtype": "text",
            "text": {
                    "content": info + content
                     },
            }

   ##调用request.post发送json格式的参数
    headers = {'Content-Type': 'application/json','Connection':'close'}
    result = requests.post(url=webhook, data=json.dumps(data), headers=headers)

def HealthChk(APP,IP,PORT):
    url = "http://%s:%s/moni/"%(IP,PORT)
    print (url,APP)

    try:
        StatusCode = requests.get(url,timeout=10).status_code
    except requests.exceptions.RequestException as e:
        ErrorCont = "Tomcat Health Check Connect Timeout"
        error_send(ErrorCont,APP)
        print(e)
        return

    if StatusCode > 200:
        ErrorCont = "Tomcat Health Check StatusCode ERROR"
        error_send(ErrorCont,APP)
        return
    try:
        response = requests.get(url,timeout=10).text
    except requests.exceptions.RequestException as e:
        ErrorCont = "Tomcat Health Check Connect Timeout"
        error_send(ErrorCont,APP)
        print(e)
        return

    m = re.search('GREEN',response)
    n = re.search('2',response)

    if not (m and n):
        ErrorCont = "Tomcat Health Check Operation ERROR"
        error_send(ErrorCont,APP)

    
class Producer(threading.Thread):
    def __init__(self,t_name,queue):
        threading.Thread.__init__(self,name=t_name)
        self.data=queue
    def run(self):
        for appInfo in text_read(AppFile):
            self.data.put(appInfo)
            time.sleep(1)

class Consumer(threading.Thread):
    def __init__(self,t_name,queue):
        threading.Thread.__init__(self,name=t_name)
        self.data=queue
    def run(self):
        while True:
            try:
                AppInfo = self.data.get(1,5)
                app = AppInfo.split(' ',2)[0]
                ip = AppInfo.split(' ',2)[1]
                port = AppInfo.split(' ',2)[2]
                HealthChk(app,ip,port)
            except:
                break

def main():
    queue = Queue()
    producer = Producer('PRO', queue)
    DoNa_Chk1 = Consumer('Chk1', queue)
    DoNa_Chk2 = Consumer('Chk2', queue)
    DoNa_Chk3 = Consumer('Chk3', queue)
    DoNa_Chk4 = Consumer('Chk4', queue)

    producer.start()
    DoNa_Chk1.start()
    DoNa_Chk2.start()
    DoNa_Chk3.start()
    DoNa_Chk4.start()

    producer.join()
    DoNa_Chk1.join()
    DoNa_Chk2.join()
    DoNa_Chk3.join()
    DoNa_Chk4.join()

if __name__ == '__main__':
    main()

