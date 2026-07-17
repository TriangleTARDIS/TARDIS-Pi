#!/bin/bash
#
# TARDIS SFX module.  Sensor Log, calls sensor in a loop.
#
# Copyright (C) 2017-2026 M Thompson.  All Rights Reserved.
#
# Created 06-22-2017 by M Thompson (triangletardis@gmail.com)
# Last modified 07-16-2026
#


cd "$(dirname "$0")"
watch -n 5 "./sensor.sh | tee -a log/sensor.log"
