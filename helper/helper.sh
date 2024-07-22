#!/bin/sh
cd "$(dirname "$0")"
lsusb > zusb.txt
v4l2-ctl --list-devices | grep -v /dev/ > zv4l.txt
w > zsys.txt
free >> zsys.txt

cat z*.txt
../sensor.sh
