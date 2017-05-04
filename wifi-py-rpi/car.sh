#!/bin/bash

# This runs the car.py program, after checking that it's not
# already running, and shuts down the operating system on exit.
# If the Raspberry Pi is setup to login automatically, then
# as soon as the RPi boots and logs in user pi, you can run
# this script automatically from the ~/.profile login script.

# Of course, anyone at all concerned about system security
# would never do it this way...

pid_file="car.pid"
res=""

if [ -f $pid_file ]; then
   pid=$(<$pid_file)
   res=`ps x -p $pid | grep car.py | grep -v grep`
   if [ -z "$res" ]; then
      rm $pid_file
   fi
fi

if [ -z "$res" ]; then
   echo "Starting car.py"
   python car.py &
   pid=$!
   echo $pid > $pid_file
   wait $pid
   exit_value=$?
   rm $pid_file
   if [ $exit_value -eq 0 ]; then
       echo "exit okay: shutting down..."
       sudo shutdown -h now
   else
       echo "exit not okay: exit without shutdown"
   fi
fi
