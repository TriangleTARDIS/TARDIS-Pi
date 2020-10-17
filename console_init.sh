#!/bin/sh
#
# TARDIS SFX module.  Init Script.
#
# Copyright (C) 2017-2020 Michael Thompson.  All Rights Reserved.
#
# Created 06-22-2017 by Michael Thompson(triangletardis@gmail.com)
# Last modified 10-14-2020
#
# Version 4.1.0
#


clear
cat asset/tardis_ascii_small.txt
echo ">>> TT Type 40, Mark 3 <<<"

# Output to Headphone, Adjust Mixer, 
#amixer -q cset numid=3
#amixer -q set PCM 100%
#amixer -q -c 1 set Headphone 100%
echo Audio Interface Activated...

# Startup background sound
killall -q speaker-test
nohup speaker-test -W ./sound -t wav -w hum_mono.wav -l 0 > /dev/null &

# Activate gpio daemon
sudo pigpiod
sleep 1
#raspi-gpio set X op
#raspi-gpio set X dl
echo Hostile Action Displacement System Activated...

# Finish
echo Initialization Complete!
sleep 1

