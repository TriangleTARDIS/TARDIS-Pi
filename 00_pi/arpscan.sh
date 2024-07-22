#!/bin/sh
sudo nmap -sP -PR 192.168.2.0/24 | grep -v "Host is"
ping obi200
