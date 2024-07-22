#!/bin/sh
#
# TARDIS SFX module.  GUI - LED Calibration.
#
# Copyright (C) 2017-2020 Michael Thompson.  All Rights Reserved.
#
# Created 06-22-2017 by Michael Thompson (triangletardis@gmail.com)
# Last modified 07-20-2024
#
# Version 4.1.6
#


cd "$(dirname "$0")"

# Activate gpio daemon
sudo killall pigpiod > /dev/null
sudo pigpiod
sleep 1

lxterminal --geometry=80x30 -e "./calibrate.py"
sleep 2
