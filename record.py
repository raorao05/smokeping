#! /usr/bin/python
# store the smokeping's alert info

import sys
import MySQLdb
import time
import json
from config import db_config

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


if __name__ == '__main__':
    try:
        alertname = sys.argv[1]
        target = sys.argv[2]
        loss = sys.argv[3] + sys.argv[4]
        rtt = sys.argv[5] + sys.argv[6]
        hostname = sys.argv[7]
        create_time = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))

        db = getdb()
        sql = "INSERT INTO alert (alertname,target,loss,rtt,hostname,create_time) \
                    VALUES ('%s','%s','%s','%s','%s','%s')" \
                          %(alertname,target,loss,rtt,hostname,create_time)
        db[0].execute(sql)
        db[1].commit()
    except Exception,e:
        with open('error.log','a+') as f:
            msg = json.dumps(sys.argv) + "\n\r" + str(e) + "\n\r"
            f.write(msg)
