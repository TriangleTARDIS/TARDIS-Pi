t1=`vcgencmd measure_temp`
t2=$(</sys/class/thermal/thermal_zone0/temp)
v1=`vcgencmd measure_volts core`
v2=`vcgencmd measure_volts sdram_i`
v3=`vcgencmd measure_volts sdram_c`
v4=`vcgencmd measure_volts sdram_p`
now=`date +"%m/%d/%Y %k:%M:%S"`
csv=`echo "$now,$t1,$((t2/1000)),$v1,$v2,$v3,$v4" | sed -e 's/[volt=|temp=]//g'`
echo "$csv"

