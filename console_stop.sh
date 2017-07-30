#!/bin/sh
#
# TARDIS SFX module.  Kill Script.
#
# Copyright (C) 2017 Michael Thompson.  All Rights Reserved.
#
# Created 06-22-107 by Michael Thompson(triangletardis@gmail.com)
# Last modified 07-11-2017
#
# Version 0.0.1
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
