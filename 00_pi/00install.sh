#!/bin/bash
git clone https://github.com/TriangleTARDIS/TARDIS-Pi.git ~/TARDIS-Pi/
pip3 install -r ~/TARDIS-Pi/requirements.txt

sudo env HNAME=tardispi sh ~/TARDIS-Pi/00_pi/raspi-config.txt

cp -rv ~/TARDIS-Pi/00_pi/home/. ~/
sed -i'' "s/~/\/home\/$USER/" ~/Desktop/TARDIS-*.desktop
sed -i'' "s/~/\/home\/$USER/" ~/.config/pcmanfm/LXDE-pi/*.conf
