#!/bin/bash
#
# TARDIS SFX module.  Backup Script.
#
# Copyright (C) 2017-2024 Michael Thompson.  All Rights Reserved.
#
# Created 06-22-2017 by Michael Thompson (triangletardis@gmail.com)
# Last modified 07-20-2024
#
# Version 4.1.6
#


now=`date +"%Y%m%d%k%M" | sed "s/ /0/g"`
fn=TARDIS-Pi_Backup_$now.tgz
echo "Backup to $fn ..."
cd ..
tar --exclude=.git --exclude=00_junk -zcf $fn TARDIS-Pi/
echo
echo "Copy $fn to external storage."
