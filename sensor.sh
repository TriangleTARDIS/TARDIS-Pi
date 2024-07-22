#!/bin/bash
#
# TARDIS SFX module.  Single poll of sensor data for sensor_log as CSV.
#
# Copyright (C) 2017-2024 Michael Thompson.  All Rights Reserved.
#
# Created 06-22-2017 by Michael Thompson (triangletardis@gmail.com)
# Last modified 07-20-2024
#
# Version 4.1.6
#


cd "$(dirname "$0")"

#Display Header on STDERR
HEADER="DT,TEMP_SOC,TEMP_CPU,V_CORE,V_SDRAM_IO,V_SDRAM_C,V_SDRAM_P,LOAD_1,LOAD_5,LOAD_10,PROC,MEMFREE,THROTTLE_FLAGS"
echo $HEADER >&2

#
#Get Data
now=`date +"%m/%d/%Y %k:%M:%S"`
#Temps
t1=`vcgencmd measure_temp | sed -e 's/temp=\(.*\).C/\1/'`
t1f=$(echo "scale=1; $t1 * (9/5) + 32" | bc)
t2=$(</sys/class/thermal/thermal_zone0/temp)
t2f=$(echo "scale=1; ($t2/1000) * (9/5) + 32" | bc)
#Voltages
v1=`vcgencmd measure_volts core`
v2=`vcgencmd measure_volts sdram_i`
v3=`vcgencmd measure_volts sdram_c`
v4=`vcgencmd measure_volts sdram_p`
#Load
l1=`awk '{print $1","$2","$3","$4}' /proc/loadavg`
#Memory
m1=`awk '/MemFree/ { printf "%.3f\n", $2/1024 }' /proc/meminfo`
#Throttle Flags
#vt=`vcgencmd get_throttled`
vt=`helper/get_throttled.sh`

#Display Sensor Data on STDOUT
csv=`echo "$now,$t1f,$t2f,$v1,$v2,$v3,$v4,$l1,$m1,$vt" | sed -E 's/(volt|temp)=//g'`
echo "$csv"
