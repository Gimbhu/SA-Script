#!/usr/bin/env python
#-*- coding:utf-8 -*-


##########################################
#Auther:Kammo
#Date:2020/01/12
#Ex:
#每周日定时过滤最近一周每天的baidu爬虫日志
#发送到运营同学的邮箱
##########################################



import datetime
import time
from elasticsearch import Elasticsearch, RequestsHttpConnection, Urllib3HttpConnection
import ssl
import re
import os
import zipfile
import smtplib
import shutil
from smtplib import SMTP_SSL
from email.mime.text import MIMEText
from email.header import Header
from email.mime.multipart import MIMEMultipart


logPath='/tmp/spiderlog/'
dom1Path='/tmp/spiderlog/www.domain1.com'
dom2Path='/tmp/spiderlog/www.domain2.com'

source_dir = '/tmp/spiderlog'
zipname = '/tmp/spiderlog.zip'

#获取当天日期
time_stamp = datetime.datetime.now()
DATE = time_stamp.strftime('%Y.%m.%d')

#创建存放日志目录
if not os.path.exists(logPath):
    os.makedirs(logPath)
if not os.path.exists(dom1Path):
    os.makedirs(dom1Path)
if not os.path.exists(dom2Path):
    os.makedirs(dom2Path)

#连接ES
es = Elasticsearch(
    ['${account}:${password}:9200'],
    connection_class=RequestsHttpConnection,
    use_ssl=True,
    verify_certs=True,
    ca_certs='/etc/elasticsearch/root-ca.pem',
    ssl_version=ssl.PROTOCOL_TLSv1_2,
    ssl_assert_hostname=True,
    retry_on_timeout=True,
    )

#时间转换
def TimeStamp():
    now = datetime.datetime.now()
    Time = now.strftime('%H:%M:%S')
    delta = datetime.timedelta(hours=8,seconds=10)
    Timestamp = now - delta
    return Timestamp.strftime('%H:%M:%S')

#日志查询
def LogQuery(Domain,Date):
    index = "edge_nginx_access_log-%s"%(Date)
    query = {
        'query': {
            'bool': {
                'minimum_should_match': 1,
            'should': [
                {'match_phrase': {'domain': Domain }}
            ], 
           'must': {'match_phrase':{'user_agent.name':'Baiduspider'}}
          }
       },
         'from': 0, 'size': 10000
    }

    res = es.search(index=index,body=query)
    time.sleep(2)

    logFile = '%s%s/%s.log'%(logPath,Domain,Date)

    f= open(logFile,'a+')

    for i in res['hits']['hits']:
        request_path=i['_source']['request_path']
        remote_addr=i['_source']['remote_addr']
        domain=i['_source']['domain']
        try:
            request_param=i['_source']['request_param']
        except:
            request_param=''
        try:
            user_agent=i['_source']['agent']
        except:
            print (i['_source'])
        log='%s %s?%s %s %s\n'%(remote_addr,request_path,request_param,domain,user_agent)
        f.write(log)
        f.flush()

    f.close()


#获取近七天日期
days = []
for i in range(1,8)[::-1]:
    days.append(str((datetime.date.today() - datetime.timedelta(days=i)).strftime('%Y.%m.%d')))
    
DOMAIN = ['www.domain1.com','www.domain2.com']

for d in days:
    for n in DOMAIN:
        LogQuery(n,d)


time.sleep(3)

#打包压缩日志
startdir = source_dir
file_news = zipname   
z = zipfile.ZipFile(file_news, 'w', zipfile.ZIP_DEFLATED)
for dirpath, dirnames, filenames in os.walk(startdir):
    fpath = dirpath.replace(startdir, '')
    fpath = fpath and fpath + os.sep or ''
    for filename in filenames:
        z.write(os.path.join(dirpath, filename), fpath+filename)
z.close()


#发送邮件
def send_mail(mailto_list,sub):
    mail_host=""
    mail_user=""
    mail_pass=""
    att1 = MIMEText(open(zipname, 'rb').read(), 'base64', 'utf-8')
    att1["Content-Type"] = 'application/octet-stream'
    att1["Content-Disposition"] = 'attachment; filename="spiderlog.zip"'
    msg = MIMEMultipart()
    msg['Subject'] = sub
    msg['From'] = mail_user
    msg['To'] = ";".join(mailto_list)
    msg.attach(att1)

    mailreciver_list = mailto_list

    try:
        s = smtplib.SMTP_SSL(mail_host,465)
        s.ehlo()
        s.login(mail_user,mail_pass)
        s.sendmail(mail_user, mailreciver_list, msg.as_string())
        s.close()
        return True
    except Exception:
        return False


#发送邮箱
mailto_list=[""]

sub="百度爬虫日志-%s"%(DATE)

if send_mail(mailto_list,sub):
    shutil.rmtree(source_dir)
    os.remove(zipname)
    print ("发送成功")
else:
    print("发送失败")
