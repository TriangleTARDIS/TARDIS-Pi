# TARDIS Pi Install


## Configuration (2026)

### First Boot
   - Download and run [Raspberry Pi Imager](https://www.raspberrypi.com/software/)
      - RPI 4 Trixie 32 bit
      - Hostname - tardispi
      - Localisation - Capital City / TZ
      - User   
      - Wifi - Initial AP association
      - SSH - Enable
      - Raspberry Pi Connect

### Second Boot
   - git clone https://github.com/TriangleTARDIS/TARDIS-Pi.git
   - sh ~/TARDIS-Pi/00_pi/00install.sh
   - Setup a screensaver
   - Run Calibration to verify LEDs
   - ~~Optional - Append panel_config.txt to /boot for small panel (800x480)~~
   - Reboot
   - NOTE: TigerVNC is required to support the WayVNC protocol in 2026
