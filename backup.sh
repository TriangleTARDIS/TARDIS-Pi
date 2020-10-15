#!/bin/bash
now=`date +"%Y%m%d%k%M"`
echo "$now"
cd ..
tar cvf TARDIS-Pi_Backup.tar TARDIS-Pi/

sudo mkdir /mnt/sda1
sudo mount /dev/sda1 /mnt/sda1
mount | grep sda
sudo cp -v TARDIS-Pi_Backup.tar "/mnt/sda1/TARDIS-Pi_Backup_$now.tar"

