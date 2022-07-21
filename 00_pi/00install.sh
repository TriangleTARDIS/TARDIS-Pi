#!/bin/bash
echo "Git Clone..."
git clone https://github.com/TriangleTARDIS/TARDIS-Pi.git ~/TARDIS-Pi/

echo "Python Update..."
pip3 install -r ~/TARDIS-Pi/requirements.txt

echo "RASPI Config..."
sudo env HNAME=tardispi sh ~/TARDIS-Pi/00_pi/raspi-config.txt

echo "Desktop Config..."
cp -rv ~/TARDIS-Pi/00_pi/home/. ~/
sed -i'' "s/~/\/home\/$USER/" ~/Desktop/TARDIS-*.desktop
sed -i'' "s/~/\/home\/$USER/" ~/.config/pcmanfm/LXDE-pi/*.conf

killall pcmanfm
pcmanfm --desktop --profile LXDE-pi --display :0 &

