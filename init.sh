amixer cset numid=3

bluetoothctl << EOF
remove FF:FF:DE:AD:BE:EF
power off
exit
EOF

sleep 5

bluetoothctl << EOF
power on
scan on
pair FF:FF:DE:AD:BE:EF
trust FF:FF:DE:AD:BE:EF
connect FF:FF:DE:AD:BE:EF
exit
EOF

sleep 5

bluetoothctl << EOF
info FF:FF:DE:AD:BE:EF
exit
EOF

