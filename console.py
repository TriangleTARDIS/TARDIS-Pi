#!/usr/bin/python
#
# TARDIS SFX module.
#
# Copyright (C) 2017-2020 Michael Thompson.  All Rights Reserved.
#
# Created 06-22-2017 by Michael Thompson(triangletardis@gmail.com)
# Last modified 02-07-2020
#
# Version 4.0.2
#


from __future__ import division
__version__ = "4.0.2"


import sys
import os
import signal
import time
from datetime import datetime
import wave
import math
import contextlib
import evdev
import random
import pigpio


# Globals
#devName = "Compx 2.4G Receiver"
devName = "Logitech USB Receiver"
dirSound = "sound/"
#pwmHz = 120
pwmHz = 1200
#pwmStep is min 25
pwmStep = 255
pwmSleepDefault = 1 / pwmStep
debug = True
autoPilot = False
bcmPinR = 5
bcmPinG = 6
bcmPinB = 13
bcmPinW = 19
piGPIO = None
gp = None


#
# Print a string to the console.
#
def conPrint(s):
   now  = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
   print(now + " ... \033[94m" + s + "\033[0m")


#
# Print a debug string to the console.
#
def debugPrint(s):
   if (debug):
      now  = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
      sys.stderr.write(now + " > \033[31;5m" + s + "\033[0m\n")


#
# Get length of a wave file.
#
def lenSound(f):
   debugPrint("Sound: " + f)
   with contextlib.closing(wave.open(dirSound + f, "r")) as w:
      len = w.getnframes() / float(w.getframerate())

   debugPrint(" -- " + str(len) + " Seconds")
   return len


#
# Play a wave file.
#
def playSound(f, secs=0, blk=False):
   debugPrint("Play: " + f)
   c = "aplay -q -N "

   if secs ==0 :
      c = c + (dirSound + f)
   else:
      c = c + "-d %s %s" % (secs, dirSound + f)

   if not blk:
      c = c + " &"

   debugPrint(c)
   os.system(c)


#
# Init GPIO.
#
def initGPIO():
   global piGPIO

   piGPIO = pigpio.pi()
   piGPIO.set_mode(bcmPinR, pigpio.OUTPUT)
   piGPIO.set_mode(bcmPinG, pigpio.OUTPUT)
   piGPIO.set_mode(bcmPinB, pigpio.OUTPUT)
   piGPIO.set_mode(bcmPinW, pigpio.OUTPUT)


#
# Reset LEDs.
#
def resetRGB():
   debugPrint("Reset RGB.")
   piGPIO.write(bcmPinR, 0)
   piGPIO.write(bcmPinG, 0)
   piGPIO.write(bcmPinB, 0)
   piGPIO.write(bcmPinW, 0)


#
# Begin PWM.
#
def beginPWM():
   conPrint("Begin PWM.")
   resetRGB()
   piGPIO.set_PWM_frequency(bcmPinR, pwmHz)
   piGPIO.set_PWM_range(bcmPinR, pwmStep)
   piGPIO.set_PWM_frequency(bcmPinG, pwmHz)
   piGPIO.set_PWM_range(bcmPinG, pwmStep)
   piGPIO.set_PWM_frequency(bcmPinB, pwmHz)
   piGPIO.set_PWM_range(bcmPinB, pwmStep)
   piGPIO.set_PWM_frequency(bcmPinW, pwmHz)
   piGPIO.set_PWM_range(bcmPinW, pwmStep)


#
# RGB Sinebow.
# http://basecase.org/env/on-rainbows
#
def sinebow(h):
  h += 1/2
  h *= -1
  r = math.sin(math.pi * h)
  g = math.sin(math.pi * (h + 1/3))
  b = math.sin(math.pi * (h + 2/3))

  return (int(255*chan**2) for chan in (r, g, b))

def nthcolor(n):
  phi = (1+5**0.5)/2
  return sinebow(n * phi)


#
# End PWM.
#
def endPWM():
   conPrint("End PWM.")
   piGPIO.set_PWM_dutycycle(bcmPinR, 0)
   piGPIO.set_PWM_dutycycle(bcmPinG, 0)
   piGPIO.set_PWM_dutycycle(bcmPinB, 0)
   piGPIO.set_PWM_dutycycle(bcmPinW, 0)
   resetRGB()


#
# Pulse Lights / Dematerialise effect.
#
def effectPulse(f, pwmSleep=pwmSleepDefault):
   conPrint("Pulse: " + f)
   len = lenSound(f)
   playSound(f)
   beginPWM()

   try:
      r = int(len / pwmSleep)
      debugPrint("T: " + str(r))

      for i in range(0,  r):
         l = int(pwmStep * 0.5 * ((math.cos((i / pwmStep) * 2 * math.pi)) + 1))
         debugPrint("Level: " + str(l))
         piGPIO.set_PWM_dutycycle(bcmPinR, pwmStep - l)
         piGPIO.set_PWM_dutycycle(bcmPinG, pwmStep - l)
         piGPIO.set_PWM_dutycycle(bcmPinB, pwmStep - l)
         piGPIO.set_PWM_dutycycle(bcmPinW, pwmStep - l)
         time.sleep(pwmSleep)

      #Possibly wait out sound rounding error?
      #time.sleep(0.5)

   except Exception as e:
       print("Failed")
       print(e)

   conPrint("All Stop")
   endPWM()


#
# Pulse Lights RGB effect.
#
def effectPulseRGB(f, pwmSleep=pwmSleepDefault):
   conPrint("PulseRGB: " + f)
   len = lenSound(f)
   playSound(f)
   beginPWM()

   try:
      r = int(len / pwmSleep)
      debugPrint("T: " + str(r))
      lf = 2*math.pi/100;

      for i in range(0,  r):
         l = int(pwmStep * 0.5 * ((math.cos((i / pwmStep) * 2 * math.pi)) + 1))
         l = pwmStep;
         (lR, lG, lB) = sinebow(i/pwmStep);
         #(lR, lG, lB) = nthcolor(i);
         debugPrint("Level: " + str(i) + " : " + str(lR) + "-" + str(lG) + "-" + str(lB))
         piGPIO.set_PWM_dutycycle(bcmPinR, pwmStep - lR)
         piGPIO.set_PWM_dutycycle(bcmPinG, pwmStep - lG)
         piGPIO.set_PWM_dutycycle(bcmPinB, pwmStep - lB)
         piGPIO.set_PWM_dutycycle(bcmPinW, pwmStep)
         time.sleep(pwmSleep)

      #Possibly wait out sound rounding error?
      #time.sleep(0.5)

   except Exception as e:
       print("Failed")
       print(e)

   conPrint("All Stop")
   endPWM()


#
# Blink Lights / Door Lock effect.
#
def effectBlink(f):
   conPrint("Lock: " + f)
   len = lenSound(f)
   playSound(f)
   beginPWM()

   try:
      for l in [pwmStep, 0, pwmStep * 0.25, pwmStep, 0, pwmStep * 0.25, pwmStep]:
         debugPrint("Level: " + str(l))
         piGPIO.set_PWM_dutycycle(bcmPinR, pwmStep - l)
         piGPIO.set_PWM_dutycycle(bcmPinG, pwmStep - l)
         piGPIO.set_PWM_dutycycle(bcmPinB, pwmStep - l)
         piGPIO.set_PWM_dutycycle(bcmPinW, pwmStep - l)
         time.sleep(0.1)

   except Exception as e:
       print("Failed")
       print(e)

   conPrint("Locked")
   endPWM()


#
# Signal Handler.
#
def sig_handler(signal, frame):
   conPrint("Emergency Exit")
   if piGPIO != None:
      piGPIO.stop()

   if gp != None:
      gp.ungrab()

   sys.exit(1)


#
# Main
#
def mainLoop():
   global gp

   signal.signal(signal.SIGINT, sig_handler)
   autoPilot = len(sys.argv) > 1
   os.system("./console_init.sh")
   conPrint("***** Console Enabled *****")

   #Init GPIO
   initGPIO()
   resetRGB()

   #Find Input Device
   conPrint("Locate Registered Operator")
   #playSound("runaway_scanning.wav", 5, True)
   devices = [evdev.InputDevice(fn) for fn in evdev.list_devices()]
   gp = None

   for device in devices:
      conPrint("Device: " + device.name + " [" + device.fn + "]")

      if (device.name == devName):
        gp = evdev.InputDevice(device.fn)
        break

   if autoPilot and (gp is None):
      gp = evdev.InputDevice("/dev/input/event0")

   #Event Loop
   if not autoPilot and (gp is None):
      conPrint("Operator Missing!")
   else:
      conPrint("Found Operator!  [" + gp.name + "] (Autopilot: " + str(autoPilot) + ")")
      gp.grab()
      r = 0
      rf = 0

      while True:
        time.sleep(0.01)
        ranEvent = False
        event = gp.read_one()

        #Autopilot Injects Events periodically
        if autoPilot:
           if (r >= rf):
            r = 0
            rf = (random.randint(10,60)) * 100
            conPrint("Next Wait: " + str(rf))
            event = evdev.events.InputEvent(0, 0, evdev.ecodes.EV_KEY, evdev.ecodes.KEY_ESC, 1)

        #Handle Event
        if (event != None) and (event.type == evdev.ecodes.EV_KEY or event.type == evdev.ecodes.EV_REL):
          keyevent = evdev.categorize(event)
          kCode = None
          debugPrint("EVENT: " + str(keyevent))

          if (autoPilot and r == 0):
            conPrint("Automatic action")
            kCode = random.choice(["UP", "BTN_MIDDLE", "BTN_LEFT", "BTN_RIGHT", "DOWN"])
          else:
            #Handle multiple key press and convert mouse wheel axis to single press
            if event.type == evdev.ecodes.EV_KEY and keyevent.keystate == evdev.events.KeyEvent.key_down:
               kCode = keyevent.keycode[0] if type(keyevent.keycode) is list else keyevent.keycode
            elif event.code == evdev.ecodes.REL_WHEEL:
               kCode = "UP" if event.value == 1 else "DOWN"

          if kCode != None:
            r = 0
            debugPrint("KEY: " + kCode)

          #Run Effect
          if kCode == "BTN_LEFT":
            effectPulse("takeoff.wav", pwmSleepDefault * 2)
            ranEvent = True
          elif kCode == "BTN_MIDDLE":
            effectBlink("lock_chirp.wav")
            ranEvent = True
          elif kCode == "BTN_RIGHT":
            #effectPulse("exterior_telephone.wav", pwmSleepDefault * 0.5)
            effectPulseRGB("exterior_telephone.wav", pwmSleepDefault * 3)
            ranEvent = True
          elif kCode == "UP":
            effectPulse("cloister_bell.wav", pwmSleepDefault * 3)
            ranEvent = True
          elif kCode == "DOWN":
            effectPulse("denied_takeoff.wav", pwmSleepDefault * 1.5)
            ranEvent = True
          elif kCode != None:
            debugPrint("Unused Key: " + str(kCode))

          #Empty Input Buffer
          if ranEvent:
            while gp.read_one() != None:
               pass

          resetRGB()
        #endif

        r += 1
      #endWhile

   # Finish
   resetRGB()
   piGPIO.stop()
   conPrint("Safe Exit")

   if gp != None:
      gp.ungrab()


#
# Init.
#
if __name__ == "__main__":
   mainLoop()
