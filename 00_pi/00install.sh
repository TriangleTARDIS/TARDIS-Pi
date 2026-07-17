#!/bin/bash
echo "Python Update..."
pip3 install --break-system-packages --user -r ~/TARDIS-Pi/requirements.txt


#echo "RASPI Config..."
#sudo sh ~/TARDIS-Pi/00_pi/raspi-config.txt


echo "Setup VNC..."
sudo sh -c "echo \"Authentication=VncAuth\" > /root/.vnc/config.d/vncserver-x11"
sudo sh -c "echo \"Encryption=AlwaysOff\" >> /root/.vnc/config.d/vncserver-x11"
echo "\n\nEnter vnc password"
sudo vncpasswd -service
sudo systemctl restart wayvnc


#echo "Setup XRDP..."
#sudo apt-get install xrdp


echo "Install extras..."
sudo apt-get install pigpio
sudo apt-get install xscreensaver dnsmasq minicom wireguard
#sudo apt-get install ffmpeg audacity youtube-dl python-dev


echo "Setup Samba..."
sudo apt-get install samba
if ! sudo pdbedit -L | grep -q "^$USER:"; then
    sudo smbpasswd -a $USER
else
    echo "User $USER already exists."
fi
sudo sed -i '/\[homes\]/,/^\[/ { s/^ *read only = .*/   read only = no/ }' "/etc/samba/smb.conf"
sudo systemctl restart smbd


echo "Setup Serial TTY..."
sudo cp ~/TARDIS-Pi/00_pi/issue /etc/
sudo cp ~/TARDIS-Pi/00_pi/motd /etc/
sudo systemctl enable --now ~/TARDIS-Pi/00_pi/serial-getty@ttyUSB0.service


echo "Desktop Config..."
cp -rv ~/TARDIS-Pi/00_pi/home/. ~/
sed -i'' "s/~/\/home\/$USER/" ~/Desktop/TARDIS-*.desktop
sed -i'' "s/~/\/home\/$USER/" ~/.config/pcmanfm/LXDE-pi/*.conf

killall pcmanfm
pcmanfm --desktop --profile LXDE-pi --display :0 &
