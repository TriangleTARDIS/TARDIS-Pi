#!/bin/sh
#
# TARDIS SFX module.  Kill Script.
#
# Copyright (C) 2017-2019 Michael Thompson.  All Rights Reserved.
#
# Created 06-22-2017 by Michael Thompson(triangletardis@gmail.com)
# Last modified 01-11-2019
#
# Version 3.0.1
#


clear
cat asset/tardis_ascii_small.txt
echo
echo ... TT Type 40, Mark 3 ...
echo ...
echo ... Stealth Mode!

# Deactivate Lights
raspi-gpio set 17 op
raspi-gpio set 17 dl

# Stop sound
killall -q aplay
killall -q speaker-test
