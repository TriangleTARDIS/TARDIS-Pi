#!/bin/sh
#
# TARDIS SFX module.  Init Script.
#
# Copyright (C) 2017-2019 Michael Thompson.  All Rights Reserved.
#
# Created 06-22-107 by Michael Thompson(triangletardis@gmail.com)
# Last modified 05-19-2019
#
# Version 4.0.0
#

clear
cat asset/tardis_ascii_small.txt
echo
echo ">>> TT Type 40, Mark 3 <<<"
echo ...
echo ... Online

# Output to Headphone, Adjust Mixer
amixer -q cset numid=3
amixer -q set PCM 100%
amixer -q set Master 100%
echo ... Audio Interface Activated

# Startup and background sound
killall -q aplay
killall -q speaker-test
speaker-test -W ./sound -t wav -w hum_mono.wav -l 0 > /dev/null &

# Activate Lights
sudo killall pigpiod
sudo pigpiod
sleep 1
raspi-gpio set 17 op
raspi-gpio set 17 dh
raspi-gpio set 6 op
raspi-gpio set 6 dl
raspi-gpio set 13 op
raspi-gpio set 13 dl
raspi-gpio set 5 op
raspi-gpio set 5 dl
echo ... Hostile Action Displacement System Activated

# Finish
echo ... Initialization Complete!
