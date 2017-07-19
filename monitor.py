#! /usr/bin/python
# encoding:utf8
# send alert msg,run as crontab job each 1 mintue

import sys
import copy
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
    #begin_time = '2017-07-19 07:32'
    #end_time = '2017-07-19 07:33'
    sql = "SELECT * FROM alert WHERE create_time BETWEEN '%s' AND '%s'"%(begin_time,end_time)
    db[0].execute(sql)
    ret = db[0].fetchall()
    data = {}
    for i in ret:
        target_list = i['target'].split('.')
        target = target_list[0] #yidong/liantong/dianxin
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


def sendEmail(msg,email):
        xsmtpapi = {
                "to": email,
                "sub": {
                        "%time%" : '',
                        "%msg%" :  ''
                },
        }
        time_info,msg_info = [],[]
        mytime = time.strftime('%Y-%m-%d %H:%M',time.localtime(time.time()-60))
        for i in range(0,len(email)):
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
        msg_admin = msg_guest = ''

        #给内部人员发的告警信
        for i in oneMinBeforeData:
            for j in oneMinBeforeData[i]:
                if len(oneMinBeforeData[i][j]) >= 2: #一分钟内同一运营商有两个点超时或者丢包，需要报警
                    msg_admin += "<br>########################<br>"
                    msg_admin += '运营商:%s'%str(i) + "<br>"
                    msg_admin += '故障类型:%s'%str(j) + "<br>"
                    for k in oneMinBeforeData[i][j]:
                        del(k['create_time'])
                        del(k['id'])
                        msg_admin += '报警内容:%s'%json.dumps(k) + "<br>"
                    msg_admin += '########################'

        #给外部人发的告警信
        for i in oneMinBeforeData:
            for j in oneMinBeforeData[i]:
                new_data = copy.deepcopy(oneMinBeforeData[i][j])
                if len(oneMinBeforeData[i][j]) >= 2: #一分钟内同一运营商有两个点超时或者丢包，需要报警
                    for k in oneMinBeforeData[i][j]:
                        target = k['target'].split('.')[1] # dianxin-nanchong-2
                        if target.find('dianxin-nanchong') or target.find('dianxin-foshan'):
                            new_data.remove(k)

                    if len(new_data) >= 2:
                        msg_guest += "<br>########################<br>"
                        msg_guest += '运营商:%s'%str(i) + "<br>"
                        msg_guest += '故障类型:%s'%str(j) + "<br>"
                        for k in new_data:
                            del(k['create_time'])
                            del(k['id'])
                            msg_guest += '报警内容:%s'%json.dumps(k) + "<br>"
                        msg_guest += '########################'

        if msg_admin:
            if not msg_guest:
                msg_admin += '<br>注：本次只是内部告警，未发送到斗鱼'
            else:
                msg_admin += '<br>注：本次告警，斗鱼也会收到'
            email = email_list['admin']
            print sendEmail(msg_admin,email)

        if msg_guest:
            email = email_list['guest']
            print sendEmail(msg_guest,email)
    except Exception,e:
        error_time = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
        err_msg = "time:" +error_time + "\n\r" + str(e) + "\n\r"
        with open('monitor_error.log','a+') as f:
            f.write(err_msg)
