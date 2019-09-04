#!/bin/bash

IPADD=/script/URL_Moni/conf/IP_List
URL_List=/script/URL_Moni/conf/URL_List
DEST_DATA=/script/URL_Moni/logs/UrlChk
DEST_LOG=/script/URL_Moni/logs/UrlChk.log

ipadd=`cat $IPADD`
UrlList=`cat $URL_List`

function SendMessageToDingding(){
    Webhook="https://oapi.dingtalk.com/robot/send?access_token="
    UA="Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24"

            SourceIP=`curl http://members.3322.org/dyndns/getip`
    res=`curl -XPOST -s -L -H "Content-Type:application/json" -H "charset:utf-8" $Webhook -d "
    {
    \"msgtype\": \"text\",
    \"text\": {
             \"content\": \"$1   $2   $3   $4   $5   $6   $7   $8   $9   $SourceIP\"
             }
    }"`

}


for ip in $ipadd
do
    for url in $UrlList
    do
        curl -w "@/script/URL_Moni/conf/curl-format.conf" -H "Host:$url" http://$ip -o /dev/null -s -L > $DEST_DATA 2>&1
        status=`cat $DEST_DATA|awk '{if($1 == "http_code:") print $2}'`
        if [  -z $status ];then
            status="-"
        fi
        ContentLength=`cat $DEST_DATA|awk '{if($1 == "size_request:") print $2}'`
        if [  -z $ContentLength ];then
            ContentLength="-"
        fi
        time_connect=`cat $DEST_DATA|awk '{if($1 == "time_connect:") print $2*1000}'`
        time_starttransfer=`cat $DEST_DATA|awk '{if($1 == "time_starttransfer:") print $2*1000}'`
        time_total=`cat $DEST_DATA|awk '{if($1 == "time_total:") print $2*1000}'`
        Date=`date +%Y/%m/%d:%H:%M:%S`

        Content="[$Date]  $ip  \'\'$url\'\'  $status  $ContentLength  $time_connect  $time_starttransfer  $time_total"
        echo "[$Date]  $ip  \"$url\"  $status  $ContentLength  $time_connect  $time_starttransfer  $time_total" >> $DEST_LOG
        if [[ $status != 200 ]];then
            message="请求响应超时"        
            #SendMessageToDingding $message $Content
        elif [[ $time_connect > 3 ]];then
            message="请求响应超时"
            #SendMessageToDingding $message $Content
        fi
    done
done
