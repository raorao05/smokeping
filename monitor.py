#! /usr/bin/python
# encoding:utf8
# send alert msg,run as crontab job each 1 mintue

import sys
import time
import json
import MySQLdb
import requests
from config import db_config,email_list,send_email_config


def getdb():
    conn = MySQLdb.connect(
            host = db_config['host'],
            port = db_config['port'],
            user = db_config['username'],
            passwd = db_config['passwd'],
            db = db_config['database'],
            charset = db_config['charset']
        )
    cursor = conn.cursor(cursorclass=MySQLdb.cursors.DictCursor)
    return [cursor,conn]

def getTimeBetween():
    time1 = time.strftime('%Y-%m-%d %H:%M',time.localtime(time.time() - 60))
    time2 = time.strftime('%Y-%m-%d %H:%M',time.localtime(time.time() - 120))
    time3 = time.strftime('%Y-%m-%d %H:%M',time.localtime(time.time() - 180))
    return [time1,time2,time3]


def getMinData(begin_time,end_time):
    global db
    # begin_time = '2017-06-29 22:40'
    # end_time = '2017-06-29 22:41'
    sql = "SELECT * FROM alert WHERE create_time BETWEEN '%s' AND '%s'"%(begin_time,end_time)
    db[0].execute(sql)
    ret = db[0].fetchall()
    data = {}
    for i in ret:
        target_list = i['target'].split('.')
        target = target_list[1] #yidong/liantong/dianxin
        alertname = i['alertname']
        if not data.get(target):
            data[target] = {
                alertname : []
            }
            #data[target][alertname] = []
        if not data[target].get(alertname):
            data[target][alertname] = []
        data[target][alertname].append(i)
    return data


def sendEmail(msg):
        xsmtpapi = {
                "to": email_list,
                "sub": {
                        "%time%" : '',
                        "%msg%" :  ''
                },
        }
        time_info,msg_info = [],[]
        mytime = time.strftime('%Y-%m-%d %H:%M',time.localtime(time.time()-60))
        for i in range(0,len(email_list)):
                time_info.append(mytime)
                msg_info.append(msg)

        xsmtpapi['sub']['%time%'] = time_info
        xsmtpapi['sub']['%msg%']  = msg_info
        params = {
                "apiUser" : send_email_config["apiUser"],
                "apiKey"  : send_email_config["apiKey"],
                "from"     : send_email_config["from"],
                "templateInvokeName" : send_email_config["templateInvokeName"],
                "xsmtpapi"  : json.dumps(xsmtpapi),
        }
        r = requests.post('http://api.sendcloud.net/apiv2/mail/sendtemplate', data=params)
        ret = 'status:' + str(r.status_code) + ' content:' + str(r.content)
        return ret



if __name__ == '__main__':
    try:
        global db
        db = getdb()
        between = getTimeBetween()
        oneMinBeforeData = getMinData(between[1],between[0])
        msg = ''
        for i in oneMinBeforeData:
            for j in oneMinBeforeData[i]:
                if len(oneMinBeforeData[i][j]) >= 2: #一分钟内同一运营商有两个点超时或者丢包，需要报警
                    msg += "<br>########################<br>"
                    msg += '运营商:%s'%str(i) + "<br>"
                    msg += '故障类型:%s'%str(j) + "<br>"
                    for k in oneMinBeforeData[i][j]:
                        del(k['create_time'])
                        del(k['id'])
                        msg += '报警内容:%s'%json.dumps(k) + "<br>"
                    msg += '########################'
        if msg:
            print sendEmail(msg)
    except Exception,e:
        error_time = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
        err_msg = "time:" +error_time + "\n\r" + str(e) + "\n\r"
        with open('monitor_error.log','a+') as f:
            f.write(err_msg)
