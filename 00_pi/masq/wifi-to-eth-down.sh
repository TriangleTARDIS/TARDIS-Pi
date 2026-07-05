#!/bin/bash

eth="eth0"

#sudo iptables-restore < iptables.rules
sudo ifconfig $eth down
sudo systemctl stop dnsmasq
sudo rm -rf /etc/dnsmasq.d/* &> /dev/null
