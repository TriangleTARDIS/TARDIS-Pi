#!/bin/sh
cd ~/TARDIS-Pi
./console_init.sh
lxterminal --geometry=80x30 -e "./console.py auto"
sleep 2

