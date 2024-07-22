#!/bin/bash
#
# TARDIS SFX module.  Sensor Log, calls sensor in a loop.
#
# Copyright (C) 2017-2024 Michael Thompson.  All Rights Reserved.
#
# Created 06-22-2017 by Michael Thompson (triangletardis@gmail.com)
# Last modified 07-20-2024
#
# Version 4.1.6
#


cd "$(dirname "$0")"
watch -n 5 "./sensor.sh | tee -a log/sensor.log"
