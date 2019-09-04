#!/bin/python
# -*- coding:UTF-8 -*-

import threading,time
from Queue import Queue
import os
import datetime
import re
import time
import requests
import json

IPADD = "/script/URL_Moni/conf/IP_List"
URL_List= "/script/URL_Moni/conf/URL_List"
DEST_DATA= "/script/URL_Moni/logs/UrlChk"
DEST_LOG= "/script/URL_Moni/logs/UrlChk.log"
IPADDHK = "/script/URL_Moni/conf/IPList_HK"
UrlFormat = "/script/URL_Moni/conf/CurlFormat.conf"
Webhook = "https://oapi.dingtalk.com/robot/send?access_token="

ipadd = open(IPADD,'r')
Url_List = open(URL_List,'r')
ChkLog = open(DEST_LOG,'a+')
ipAddhk = open(IPADDHK,'r+')

IPAdd = []
UrlList = []
IPAddHK = []

for i in ipadd:
    IPAdd.append(i.strip('\n'))

for u in Url_List:
    UrlList.append(u.strip('\n'))

for h in ipAddhk:
    IPAddHK.append(h.strip('\n'))

SourceIP = os.popen('curl -s http://members.3322.org/dyndns/getip').read().split()[0]


def error_push(Content,ErrorTag):

    #获取当前时间
    time_stamp = datetime.datetime.now()
    time = time_stamp.strftime('%Y.%m.%d-%H:%M:%S')

    info = '%s  %s'%(ErrorTag,Content)
    #print (info)

    data = {
            "msgtype": "text",
            "text": {
                    "content": info
                     },
            }

   ## 调用request.post发送json格式的参数
    headers = {'Content-Type': 'application/json'}

    try:
        result = requests.post(url=Webhook, data=json.dumps(data), headers=headers)
    except:
        print (data)

    

def URLChk(url,IPAdd,UrlFormat):
    for ip in IPAdd:
        HOST = url.split('/')[0]
        IPURL = url.replace(HOST,ip)
        command = 'curl --insecure -w "@%s" -A "url_monitor" -H Host:%s https://%s -o /dev/null -s -L -k'%(UrlFormat,HOST,IPURL)
        status = os.popen(command).read().split()
        value = dict(zip(status[0::2], status[1::2]))
        StatusCode = int(value['http_code:'])
        RequestSize = int(value['size_request:'])
        TimeConnect = float(value['time_connect:']) * 1000
        TimeStarttransfer = float(value['time_starttransfer:']) * 1000
        Time_Total = float(value['time_total:']) * 1000
        time_stamp = datetime.datetime.now()
        date = time_stamp.strftime('%Y/%m/%d:%H:%M:%S')
        LogConent = '[%s]  %s  "%s"  %s  %s  %.0f  %.0f  %.0f  %s'%(date,ip,url,StatusCode,RequestSize,TimeConnect,TimeStarttransfer,Time_Total,SourceIP)

        ChkLog.write('%s\n'%LogConent)
        ChkLog.flush()
        
        if TimeConnect > 3000:
            message = "请求响应超时"
            #error_push(LogConent,message)
            time.sleep(1)
        if status > 200 or status == 0:
            message = "请求状态异常"
            #error_push(LogConent,message)
            time.sleep(1)



class Producer(threading.Thread):
    def __init__(self,t_name,queue):
        threading.Thread.__init__(self,name=t_name)
        self.data=queue
    def run(self):
        for url in UrlList:
            self.data.put(url)
            time.sleep(1)

class Hstong(threading.Thread):
    def __init__(self,t_name,queue):
        threading.Thread.__init__(self,name=t_name)
        self.data=queue
    def run(self):
        while True:
            try:
                url_Hst = self.data.get(1,5)
                if re.search('hstong.com',url_Hst):
                    URLChk(url_Hst,IPAdd,UrlFormat)
                elif re.search('valuable.com|vbkr.com',url_Hst):
                    URLChk(url_Hst,IPAddHK,UrlFormat)
            except:
                break


def main():
    queue = Queue()
    producer = Producer('PRO', queue)
    DoNa_Hst1 = Hstong('HST1', queue)
    DoNa_Hst2 = Hstong('HST2', queue)
    DoNa_Hst3 = Hstong('HST3', queue)
    DoNa_Hst4 = Hstong('HST4', queue)

    producer.start()
    DoNa_Hst1.start()
    DoNa_Hst2.start()
    DoNa_Hst3.start()
    DoNa_Hst4.start()

    producer.join()
    DoNa_Hst1.join()
    DoNa_Hst2.join()
    DoNa_Hst3.join()
    DoNa_Hst4.join()

    ipadd.close()
    Url_List.close()
    ChkLog.close()
    ipAddhk.close()

if __name__ == '__main__':
    main()
