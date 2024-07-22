#!/bin/sh
#
# TARDIS SFX module.  TUI - Automatic Mode.
#
# Copyright (C) 2017-2024 Michael Thompson.  All Rights Reserved.
#
# Created 06-22-2017 by Michael Thompson (triangletardis@gmail.com)
# Last modified 07-20-2024
#
# Version 4.1.6
#


cd "$(dirname "$0")"
./console_init.sh
lxterminal --geometry=80x30 -e "./console.py auto"
sleep 2
