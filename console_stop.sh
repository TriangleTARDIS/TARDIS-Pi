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
echo
echo ... TT Type 40, Mark 3 ...
echo ...
echo ... Stealth Mode!

# Deactivate Lights
sudo killall pigpiod
sleep 1
raspi-gpio set 17 op
raspi-gpio set 17 dl
raspi-gpio set 6 op
raspi-gpio set 6 dh
raspi-gpio set 13 op
raspi-gpio set 13 dh
raspi-gpio set 5 op
raspi-gpio set 5 dh

# Stop sound
killall -q aplay
killall -q speaker-test
