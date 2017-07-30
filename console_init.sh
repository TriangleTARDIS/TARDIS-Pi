#!/bin/sh
#
# TARDIS SFX module.  Init Script.
#
# Copyright (C) 2017 Michael Thompson.  All Rights Reserved.
#
# Created 06-22-107 by Michael Thompson(triangletardis@gmail.com)
# Last modified 07-12-2017
#
# Version 0.0.4
#

clear
cat asset/tardis_ascii_small.txt
echo
echo ">>> TT Type 40, Mark 3 <<<"
echo ...
echo ... Online

# Output to Headphone, Adjust Mixer
#alsamixer
amixer -q cset numid=3
amixer -q set PCM 100%
echo ... Audio Interface Activated

# Startup sound
aplay -d 5 -q -N sound/door_open_close.wav
speaker-test -W ./sound -t wav -w hum_mono.wav -l 0 > /dev/null &

# Activate Bluetooth
bluetoothctl << EOF
power on
exit
EOF
echo ... Communications Activated

# Activate Lights
raspi-gpio set 17 op
raspi-gpio set 17 dh
echo ... Hostile Action Displacement System Activated

# Finish
echo ... Initialization Complete!
