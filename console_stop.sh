#!/bin/sh
#
# TARDIS SFX module.  Kill Script.
#
# Copyright (C) 2017-2024 Michael Thompson.  All Rights Reserved.
#
# Created 06-22-2017 by Michael Thompson (triangletardis@gmail.com)
# Last modified 07-20-2024
#
# Version 4.1.6
#


cd "$(dirname "$0")"
clear
cat asset/tardis_ascii_small.txt
echo ">>> TT Type 40, Mark 3 <<<"

# Stop sound
killall -q speaker-test
echo Quiet Running...

# Activate gpio daemon
sudo killall pigpiod > /dev/null
sudo pigpiod
sleep 1

# Deactivate Lights
./console.py stop
#raspi-gpio set X op
#raspi-gpio set X dh
echo Stealth Mode...

sleep 5
