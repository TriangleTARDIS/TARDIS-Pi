#!/bin/bash
#
# TARDIS SFX module.  TUI - Automatic Mode.
#
# Copyright (C) 2017-2026 M Thompson.  All Rights Reserved.
#
# Created 06-22-2017 by M Thompson (triangletardis@gmail.com)
# Last modified 07-16-2026
#


cd "$(dirname "$0")"
./console_init.sh
if [ -v DISPLAY ];then
   echo "Spawning XTerm..."
   lxterminal --geometry=80x30 -e "./src/console.py auto"
else
   ./src/console.py auto
fi
sleep 2
