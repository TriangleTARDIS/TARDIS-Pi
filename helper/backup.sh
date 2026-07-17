#!/bin/bash
#
# TARDIS SFX module.  Backup Script.
#
# Copyright (C) 2017-2026 M Thompson.  All Rights Reserved.
#
# Created 06-22-2017 by M Thompson (triangletardis@gmail.com)
# Last modified 07-16-2026
#


now=`date +"%Y%m%d%k%M" | sed "s/ /0/g"`
fn=TARDIS-Pi_Backup_$now.tgz
echo "Backup to $fn ..."
cd ..
tar --exclude=.git --exclude=00_junk --exclude=*env* --exclude=__pycache__ -cvf $fn TARDIS-Pi
echo
echo "Copy $fn to external storage."
