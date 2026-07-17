#!/bin/bash
#
# TARDIS SFX module.  GUI - LED Calibration.
#
# Copyright (C) 2017-2026 M Thompson.  All Rights Reserved.
#
# Created 06-22-2017 by M Thompson (triangletardis@gmail.com)
# Last modified 07-16-2026
#


cd "$(dirname "$0")"
./console_init.sh
if [ -v DISPLAY ];then
   ./src/calibrate.py
else
   echo "XTERM REQUIRED!"
fi
sleep 5
