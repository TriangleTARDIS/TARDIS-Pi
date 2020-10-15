#!/bin/sh
#
# TARDIS SFX module.  Kill Script.
#
# Copyright (C) 2017-2019 Michael Thompson.  All Rights Reserved.
#
# Created 06-22-2017 by Michael Thompson(triangletardis@gmail.com)
# Last modified 05-19-2019
#
# Version 4.0.0
#


clear
cat asset/tardis_ascii_small.txt
echo ">>> TT Type 40, Mark 3 <<<"

# Deactivate Lights
sudo pigpiod
./console.py stop
sleep 1
#raspi-gpio set X op
#raspi-gpio set X dh
echo Stealth Mode...

# Stop sound
killall -q speaker-test
echo Quiet Running...
sleep 5

