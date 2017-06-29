##简介
采用smokeping监控


##原理
smokeping监控到丢包，调用alert.sh,alert.sh在调用record.py把数据记录进mysql<br>

crontab运行monitor.py，每分钟运行一次，读取数据库中当前时间的前一分钟的数据,<br>一旦发现同一个运营商方向具备两个以上节点丢包或者延时过高，即发送告警邮件


