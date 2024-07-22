#!/bin/sh
#
# TARDIS SFX module.  Sensor Log, Query Historical Temperature Range.
#
# Copyright (C) 2017-2024 Michael Thompson.  All Rights Reserved.
#
# Created 06-22-2017 by Michael Thompson (triangletardis@gmail.com)
# Last modified 07-20-2024
#
# Version 4.1.6
#


cd "$(dirname "$0")"
cat log/sensor*.log | cut -d , -f 2 | grep -v "TEMP_SOC" | sort | uniq -c
