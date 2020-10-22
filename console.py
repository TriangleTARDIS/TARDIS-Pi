#!/usr/bin/python3
#
# TARDIS SFX module.
#
# Copyright (C) 2017-2020 Michael Thompson.  All Rights Reserved.
#
# Created 06-22-2017 by Michael Thompson(triangletardis@gmail.com)
# Last modified 10-20-2020
#


__version__ = '4.1.1'

import curses
import json
import logging.config
import math
import os
import random
import signal
import sys
import time
from pathlib import Path

import evdev
import munch
import pigpio
import simpleaudio

# Globals
# cfg = None
# autoPilot:bool = False
# pwmSleepDefault:float = None
# piGPIO: pigpio = None
# gp: evdev.InputDevice = None
# winStatus: curses.window = None
# winStatus2: curses.window = None
# winConsole: curses.window = None
# log: logging.Logger = None
cfg = None
autoPilot = False
pwmSleepDefault = None
piGPIO = None
gp = None
winStatus = None
winStatus2 = None
winConsole = None
log = None
pinNames = None
levelIn = None
levelOut = None


#
# Print a string to the console.
#
def conPrint(s):
    log.info(s)

    if winConsole is not None:
        winConsole.addstr(' ' + s + '\n')
        winConsole.box()
        winConsole.noutrefresh()


#
# Print a debug string to the console.
#
def debugPrint(s):
    log.debug(s)

    if cfg.debug:
        conPrint(s)


#
# Print a status string to the console.
#
def statusPrint(line, s, win=0):
    w = winStatus if win == 0 else winStatus2

    if w is not None:
        x, y = w.getmaxyx()
        y = y - 2
        w.addstr(line, 1, s.ljust(y)[:y])
        w.refresh()

    # Really spammy
    if cfg.debug:
        log.debug(s)


#
# Refresh Status Windows.
#
def refreshWinStatus():
    winStatus.clear()
    winStatus.addstr(1, 1, 'Auto: {} '.format(autoPilot))
    winStatus.addstr(2, 1, 'Term: {} '.format(curses.has_colors()))
    winStatus.box()
    winStatus.addstr(0, 1, 'TT40 Console', curses.color_pair(1))
    winStatus.refresh()

    winStatus2.clear()
    winStatus2.addstr(1, 1, 'Load : {}'.format(os.getloadavg()))
    winStatus2.addstr(2, 1, 'Gamma: {:1.2f}'.format(cfg.gamma))
    txt = Path('/sys/class/thermal/thermal_zone0/temp').read_text()
    winStatus2.addstr(3, 1, 'Temp : {:3.1f} F'.format(((float(txt) / 1000) * 9 / 5) + 32))
    winStatus2.box()
    winStatus2.addstr(0, 1, 'Sensors', curses.color_pair(1))
    winStatus2.refresh()


#
# Spinners!
# https://stackoverflow.com/questions/2685435/cooler-ascii-spinners
#
def spin(t, display=0) -> str:
    return cfg.spin[display][t % len(cfg.spin[display])]


#
# Play a wave file.
#
# FIXME: Implement blocking.
#
def playSound(f) -> simpleaudio.PlayObject:
    return simpleaudio.WaveObject.from_wave_file(cfg.dirSound + f).play()


#
# Init GPIO.
#
def initGPIO():
    global piGPIO

    piGPIO = pigpio.pi(host=cfg.hostName)


#
# Reset LEDs to full bright (or dark).
#
def fullBright(lvl=0):
    statusPrint(3, 'Full Bright.')

    for pin in [cfg.bcmPin.R, cfg.bcmPin.G, cfg.bcmPin.B, cfg.bcmPin.W]:
        if pin is not None:
            piGPIO.write(pin, lvl)


#
# Gamma Shift a level.
#
def gammaShift(lvl) -> int:
    return int(pow(float(lvl) / float(cfg.pwm.step), cfg.gamma) * cfg.pwm.step + 0.5)


#
# PWM Set Duty Cycle (with gamma correction).
#
def setPwmDutyCycle(pinName, lvl, adjust=True) -> int:
    global levelIn
    global levelOut


    pin = cfg.bcmPin[pinName]
    mixl = cfg.mix[pinName]
    minl = cfg.min[pinName]
    levelIn[pinName] = lvl

    if pin is not None and pin > 0:
        lvla = lvl

        if adjust:
            lvla = gammaShift(lvla)
            lvla = lvla * mixl
            # FIXME: Scale to min.

        levelOut[pinName] = round(min(cfg.pwm.step, max(0, lvla)))
        piGPIO.set_PWM_dutycycle(pin, cfg.pwm.step - levelOut[pinName])
        return levelOut[pinName]
    else:
        return levelOut[pinName]


#
# Begin PWM.
#
def beginPWM():
    statusPrint(3, 'Begin PWM.')

    for pin in [cfg.bcmPin.R, cfg.bcmPin.G, cfg.bcmPin.B, cfg.bcmPin.W]:
        if pin is not None:
            piGPIO.set_PWM_frequency(pin, cfg.pwm.Hz)
            piGPIO.set_PWM_range(pin, cfg.pwm.step)


#
# End PWM.
#
def endPWM():
    statusPrint(3, 'End PWM.')

    for pinName in cfg.bcmPin.keys():
        setPwmDutyCycle(pinName, cfg.pwm.step)


#
# RGB Sinebow.
# http://basecase.org/env/on-rainbows
#
def sinebow(h):
    h += 1 / 2
    h *= -1
    r = math.sin(math.pi * h)
    g = math.sin(math.pi * (h + 1 / 3))
    b = math.sin(math.pi * (h + 2 / 3))
    return (int(255 * chan ** 2) for chan in (r, g, b))


#
# RGB Sequence.
# http://basecase.org/env/on-rainbows
#
def nthcolor(n):
    phi = (1 + 5 ** 0.5) / 2
    return sinebow(n * phi)


#
# Pulse Lights / Dematerialise effect.
#
def effectPulse(f, pwmSleep=pwmSleepDefault):
    conPrint('Pulse: ' + f)
    beginPWM()
    play = playSound(f)

    i = 0
    while play.is_playing():
        lvla = int(cfg.pwm.step * 0.5 * ((math.cos((i / cfg.pwm.step) * 2 * math.pi)) + 1))
        statusPrint(4, 'Level: {} {:6g} of {:6g}'.format(spin(i, 1), lvla, cfg.pwm.step))

        for pinName in cfg.bcmPin.keys():
            setPwmDutyCycle(pinName, lvla)

        time.sleep(pwmSleep)
        i = i + 1

    endPWM()
    statusPrint(4, '')
    conPrint('All Stop')


#
# Pulse Lights RGB effect.
#
def effectPulseRGB(f, pwmSleep=pwmSleepDefault, rand=False):
    conPrint('PulseRGB: ' + f)
    play = playSound(f)
    beginPWM()
    setPwmDutyCycle('W', 0)

    i = 0
    while play.is_playing():
        (lR, lG, lB) = nthcolor(i) if rand else sinebow(i / cfg.pwm.step)
        statusPrint(4, 'Level: {} {:6g} - [{:3g}, {:3g}, {:3g}]'.format(spin(i, 1), i, lR, lG, lB))

        setPwmDutyCycle('R', lR)
        setPwmDutyCycle('G', lG)
        setPwmDutyCycle('B', lB)

        time.sleep(pwmSleep)
        i = i + 1

    endPWM()
    statusPrint(4, '')
    conPrint('All Stop')


#
# Blink Lights / Door Lock effect.
#
def effectBlink(f):
    conPrint('Lock: ' + f)
    play = playSound(f)
    beginPWM()

    for lvl in [1, 0, 0.25, 1, 0, 0.25, 1]:
        lvl *= cfg.pwm.step
        statusPrint(4, 'Level: {:6g} of {:6g}'.format(lvl, cfg.pwm.step))

        for pin in cfg.bcmPin.values():
            piGPIO.set_PWM_dutycycle(pin, lvl)

        time.sleep(0.1)

    endPWM()
    statusPrint(4, '')
    conPrint('Locked')


#
# Shutdown.
#
def shutdown():
    global piGPIO
    global gp

    try:
        log.debug('Shutdown Curses')
        curses.endwin()
    except:
        pass

    if piGPIO is not None:
        log.debug('Shutdown PIGPIO')
        piGPIO.stop()
        piGPIO = None

    if gp is not None:
        log.debug('Shutdown evDev')
        gp.ungrab()
        gp = None

    log.debug('Shutdown finished')


#
# Signal Handler.
#
def sig_handler(signal, frame):
    shutdown()
    sys.exit(1)


#
# Main Loop.
#
def mainLoop(stdscr):
    # FIXME: def mainLoop(stdscr: curses.window):
    global gp
    global winConsole
    global winStatus
    global winStatus2

    # Setup Curses TUI
    curses.resizeterm(30, 80)
    curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_WHITE)

    stdscr.nodelay(True)
    # for l in range(0, 29):
    #    stdscr.addstr(l, 0, str(l).rjust(80, '*'))
    stdscr.refresh()

    winStatus = curses.newwin(7, 40, 0, 0)
    winStatus2 = curses.newwin(7, 40, 0, 40)
    refreshWinStatus()

    winConsole = curses.newwin(22, 60, 7, 10)
    winConsole.scrollok(True)

    # Run System Init
    # FIXME: This hangs on Pi.
    # with subprocess.Popen(['./console_init.sh'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT) as proc:
    #    next_line = proc.stdout.readline()
    #
    #    while len(next_line) != 0:
    #        winConsole.addstr(str(next_line, 'utf8'))
    #        winConsole.box()
    #        winConsole.refresh()
    #        next_line = proc.stdout.readline()
    conPrint('***** Console Enabled *****')

    # Init GPIO
    initGPIO()
    fullBright()
    refreshWinStatus()

    # Find Input Device
    conPrint('Locate Registered Operator')
    # FIXME: playSound('runaway_scanning.wav', 5, True)
    devices = [evdev.InputDevice(fn) for fn in evdev.list_devices()]

    for device in devices:
        log.debug('Device: ' + device.name + ' [' + device.path + ']')

        if device.name == cfg.devName:
            gp = evdev.InputDevice(device.path)
            break

    if autoPilot and (gp is None):
        gp = evdev.InputDevice('/dev/input/event0')

    # Event Loop
    if not autoPilot and (gp is None):
        raise Exception('Operator Missing!')
    else:
        conPrint('Found Operator! [' + gp.name + ']')
        gp.grab()
        curses.flushinp()

        r = 0
        rf = 10
        vworp = True

        while vworp:
            time.sleep(cfg.loopSleep)
            statusPrint(4, 'Frame: {} {} {}'.format(spin(r), r, rf if autoPilot else ''), 1)
            ranEvent = False
            event = gp.read_one()
            curseKey = stdscr.getch()

            # Autopilot Injects Events periodically
            if autoPilot and (r >= rf):
                r = 0
                rf = (random.randint(10, 60)) * math.trunc(1 / cfg.loopSleep)
                event = evdev.events.InputEvent(0, 0, evdev.ecodes.EV_KEY, evdev.ecodes.KEY_ESC, 1)

            # Handle Event
            if (event is not None and (event.type == evdev.ecodes.EV_KEY or event.type == evdev.ecodes.EV_REL)) or (
                    curseKey != curses.ERR):
                kCode = None

                if autoPilot and r == 0:
                    conPrint('Automatic action')
                    kCode = random.choice(['UP', 'BTN_MIDDLE', 'BTN_LEFT', 'BTN_RIGHT', 'DOWN'])
                else:
                    conPrint('Normal action')

                    # Handle EVDEV and Curses inputs
                    if event is not None:
                        keyevent = evdev.categorize(event)

                        # Handle multiple key press and convert mouse wheel axis to single press
                        if event.type == evdev.ecodes.EV_KEY and keyevent.keystate == evdev.events.KeyEvent.key_down:
                            kCode = keyevent.keycode[0] if type(keyevent.keycode) is list else keyevent.keycode
                        elif event.code == evdev.ecodes.REL_WHEEL:
                            kCode = 'UP' if event.value == 1 else 'DOWN'
                    else:
                        kCode = chr(curseKey)

                if kCode is not None:
                    r = 0
                    statusPrint(4, 'KEY: ' + kCode)

                # Run Effect
                if kCode == 'BTN_LEFT' or kCode == 'w':
                    effectPulse('takeoff.wav', pwmSleepDefault * 2)
                    ranEvent = True
                elif kCode == 'BTN_MIDDLE' or kCode == 'e':
                    effectBlink('lock_chirp.wav')
                    ranEvent = True
                elif kCode == 'BTN_RIGHT' or kCode == 'r':
                    effectPulse('exterior_telephone.wav', pwmSleepDefault)
                    ranEvent = True
                elif kCode == 'UP' or kCode == 't':
                    effectPulseRGB('cloister_bell.wav', pwmSleepDefault * 50, True)
                    ranEvent = True
                elif kCode == 'DOWN' or kCode == 'y':
                    effectPulseRGB('denied_takeoff.wav', pwmSleepDefault * 1.5)
                    ranEvent = True
                elif kCode == 'KEY_Q' or kCode == 'q':
                    vworp = False
                elif kCode is not None:
                    debugPrint('Unused Key: ' + str(kCode))

                # Empty Input Buffer
                if ranEvent:
                    refreshWinStatus()
                    curses.flushinp()
                    curses.doupdate()

                    while gp.read_one() is not None:
                        pass

                fullBright()
            # endif

            r += 1
            r %= 4000
        # endWhile


# End mainLoop


#
# Read Config.
#
def readConfig():
    global cfg
    global pwmSleepDefault
    global pinNames
    global levelIn
    global levelOut

    with open('console_config.json') as f:
        cfg = munch.munchify(json.load(f))

    pwmSleepDefault = 1 / cfg.pwm.step
    pinNames = list(cfg.bcmPin.keys())
    levelIn = dict.fromkeys(cfg.bcmPin.keys())
    levelOut = dict.fromkeys(cfg.bcmPin.keys())

    log.info(cfg)
    log.debug("Debug: %s", cfg.debug)
    log.debug("Names: %s", pinNames)
    log.debug("Pins : %s", cfg.bcmPin)
    log.debug("PWM Sleep: %s", pwmSleepDefault)


#
# Init.
#
if __name__ == '__main__':
    try:
        stopMode = False

        # Set XTerm Title
        print('\33]0;TT40_Console\a', end='', flush=True)

        # Handle Break
        signal.signal(signal.SIGINT, sig_handler)

        # Config Logging
        logging.config.fileConfig('logging.ini')
        log = logging.getLogger()
        log.info('Event Zero.')

        # Read General Config
        readConfig()

        if len(sys.argv) > 1:
            autoPilot = sys.argv[1] == "auto"
            stopMode = sys.argv[1] == "stop"

        if stopMode:
            # Kill the lights
            initGPIO()
            fullBright(1)
            log.info('Stop Mode')
        else:
            # Start TUI Loop
            curses.wrapper(mainLoop)
            shutdown()

        print('Safe Exit')
        log.info('Safe Exit')
    except BaseException as e:
        shutdown()
        log.critical('Emergency Exit, unexpected error.', exc_info=sys.exc_info())
        print('Emergency Exit.  See log for details.')
        print(sys.exc_info())
        raise
