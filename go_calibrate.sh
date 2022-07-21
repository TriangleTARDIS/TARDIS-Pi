#!/bin/sh
cd ~/TARDIS-Pi
./console_init.sh
lxterminal --geometry=80x30 -e "./calibrate.py"
sleep 2

