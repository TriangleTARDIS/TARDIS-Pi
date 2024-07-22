#!/bin/bash
# Original: http://www.tunnelsup.com/raspberry-pi-phoning-home-using-a-reverse-remote-ssh-tunnel
createTunnel() {
  /usr/bin/ssh -N -f -R 9040:localhost:22 -p 9091 tardispi@citadel
  if [[ $? -eq 0 ]]; then
    echo Tunnel to jumpbox created successfully  - on localhost use port 9040
  else
    echo An error occurred creating a tunnel to jumpbox. RC was $?
  fi
}
/bin/pidof ssh
if [[ $? -ne 0 ]]; then
  echo Creating new tunnel connection
  createTunnel
fi
