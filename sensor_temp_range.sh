#!/bin/sh
#
# TARDIS SFX module.  Sensor Log, Query Historical Temperature Range.
#
# Copyright (C) 2017-2026 M Thompson.  All Rights Reserved.
#
# Created 06-22-2017 by M Thompson (triangletardis@gmail.com)
# Last modified 07-16-2026
#


cd "$(dirname "$0")"
cat log/sensor*.log | cut -d , -f 2 | grep -v "TEMP_SOC" | sort | uniq -c
