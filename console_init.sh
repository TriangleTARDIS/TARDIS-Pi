#!/bin/sh
#
# TARDIS SFX module.  Init Script for TUI.
#
# Copyright (C) 2017-2026 Michael Thompson.  All Rights Reserved.
#
# Created 06-22-2017 by Michael Thompson (triangletardis@gmail.com)
# Last modified 07-25-2024
#
# Version 4.1.8
#


cd "$(dirname "$0")"
clear
cat asset/tardis_ascii_small.txt
echo ">>> TT Type 40, Mark 3 <<<"

# Kill any existing consoles
killall console.py 2> /dev/null

# Output to Headphone, Adjust Mixer, Max volume
#amixer -q cset numid=3
#amixer -q set PCM 100%
#amixer -q -c 1 set Headphone 100%
echo Audio Interface Activated...

# Activate gpio daemon
sudo killall pigpiod > /dev/null
sudo pigpiod
sleep 1

# Activate Lights
#raspi-gpio set X op
#raspi-gpio set X dl
echo Hostile Action Displacement System Activated...

# Finish
echo Initialization Complete!
sleep 1
