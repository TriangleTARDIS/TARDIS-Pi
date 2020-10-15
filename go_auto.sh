#!/bin/sh
cd ~pi/TARDIS-Pi
sh console_init.sh
lxterminal --working-directory=~pi/TARDIS-Pi --geometry=80x33 -e "./console.py auto"

