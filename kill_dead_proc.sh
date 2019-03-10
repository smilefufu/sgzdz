#!/bin/bash

ps -eo pid,etime,cmd | grep levelup_robot.py | grep -v grep | awk '{if(length($2)==5){split($2, a, ":"); if(int(a[1])>9){print $1}  }else{print $1}}' | xargs kill -9

