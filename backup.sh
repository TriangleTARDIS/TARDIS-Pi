#!/bin/bash
now=`date +"%Y%m%d%k%M"`
echo "$now"
sleep 1
cd ..
tar cvf TARDIS.tar TARDIS-Pi/
mount /dev/sda1 /media/pi/USB10
mount | grep sd
cp -v TARDIS.tar "/media/pi/USB10/TARDIS_$now.tar"

