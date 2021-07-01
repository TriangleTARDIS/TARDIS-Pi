#!/bin/bash
#Originally from  https://github.com/arpitjindal97/raspbian-recipes/blob/master/wifi-to-eth-route.sh

# Share Wifi with Eth device
#
#
# This script is created to work with Raspbian Stretch
# but it can be used with most of the distributions
# by making few changes.
#
# Make sure you have already installed `dnsmasq`
# Please modify the variables according to your need
# Don't forget to change the name of network interface
# Check them with `ifconfig`

ip_address="192.168.2.1"
netmask="255.255.255.0"
dhcp_range_start="192.168.2.2"
dhcp_range_end="192.168.2.5"
dhcp_time="1h"
eth="eth0"
wlan="wlan0"

echo "Start Network..."
sudo systemctl start network-online.target &> /dev/null

echo "Start IPTables..."
#sudo iptables -F
#sudo iptables -t nat -F
#sudo iptables -t nat -A POSTROUTING -o $wlan -j MASQUERADE
#sudo iptables -A FORWARD -i $wlan -o $eth -m state --state RELATED,ESTABLISHED -j ACCEPT
#sudo iptables -A FORWARD -i $eth -o $wlan -j ACCEPT
sudo iptables-restore < iptables.rules
sudo sh -c "echo 1 > /proc/sys/net/ipv4/ip_forward"

echo "Bring Up Ethernet..."
sudo ifconfig $eth down
sudo ifconfig $eth $ip_address netmask $netmask
# Remove default route created by dhcpcd
#sudo ip route del 0/0 dev $eth &> /dev/null

echo "Restart DNSMasq..."
sudo systemctl stop dnsmasq
sudo rm -rf /etc/dnsmasq.d/* &> /dev/null

echo -e "interface=$eth\n\
bind-interfaces\n\
server=8.8.8.8\n\
domain-needed\n\
bogus-priv\n\
log-dhcp\n
dhcp-range=$dhcp_range_start,$dhcp_range_end,$dhcp_time" > /tmp/custom-dnsmasq.conf

sudo cp /tmp/custom-dnsmasq.conf /etc/dnsmasq.d/custom-dnsmasq.conf
sudo systemctl start dnsmasq

sudo systemctl --no-pager status dnsmasq
cat /var/lib/misc/dnsmasq.leases

echo "Done."
sleep 2

