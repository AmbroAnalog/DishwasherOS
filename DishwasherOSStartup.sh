#!/bin/bash

export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
cd /home/pi/DishwasherOS

# delete old log file
if [ -f "runlog_old.log" ] ; then
	echo "delete runlog_old.log"
	rm runlog_old.log
fi

# copy the last log file
if test -f "runlog.log";
then
	echo "old logfile found > copying..."
	mv runlog.log runlog_old.log
else
	echo "no old logfile found"
fi

touch runlog.log
echo "Start RUNLOG for DishwasherOS..." >> runlog.log

# check for network
ping -q -c 4 8.8.8.8 > /dev/null
if [ $? -eq 0 ] ; then
	echo "`date`: Connectivity check successful" >> runlog.log
else
	echo "`date`: Connectivity check failed. wait 20s..." >> runlog.log
	sleep 20
fi

echo "`date`: Start Time Sync" >> runlog.log

service ntp stop
response=$(timeout 20 ntpd -gq)
service ntp start

slewTime=$(echo "$response" | grep -m 1 "ntpd: time")

echo "TimeSync == $slewTime" >> runlog.log
if [[ $response == *"ntpd exiting on signal 15"* ]] ; then
	echo "TimeSync failed due to timeout (20s)!" >> runlog.log
fi
echo "" >> runlog.log
echo "starting python script..." >> runlog.log

# execute python DishwasherOS
/usr/local/bin/python3.9 main.py
