#!/bin/sh
sudo nmap -sP -PR 192.168.64.0/24 | grep -v "Host is"
