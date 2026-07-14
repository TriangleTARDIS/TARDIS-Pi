#!/usr/bin/python3
#
# TARDIS SFX module.
#
# Copyright (C) 2017-2026 Michael Thompson.  All Rights Reserved.
#
# Created 06-22-2017 by Michael Thompson(triangletardis@gmail.com)
# Last modified 07-09-2026
#


__version__ = '4.1.8'

import curses
import json
import logging.config
import math
import os
import random
import signal
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import TypedDict

import evdev
import munch
import pigpio
import subprocess

from console_sound import SoundManager

#Types
class RGBWLevel(TypedDict, total=True):
    R: int = 0
    G: int = 0
    B: int = 0
    W: int = 0

# Consts
XTERM_COLOR_BLUE1 = 21
XTERM_COLOR_GREY58 = 246

# Globals
cfg = None
autoPilot: bool = False
pwmSleepDefault: float = None
piGPIO: pigpio = None
gp: evdev.InputDevice = None
colorHeaderInfo: int = None
colorHeaderSensor: int = None
colorConsole: int = None
winStatus: curses.window = None
winStatus2: curses.window = None
winConsole: curses.window = None
log: logging.Logger = None
pinNames: list[str] = None
levelIn: RGBWLevel = None
levelOut: RGBWLevel = None
sound: SoundManager = None


#
# Print a string to the console.
#
def conPrint(s):
    log.info(s)

    if winConsole is not None:
        winConsole.bkgd(' ', colorConsole)
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
# Get CPU Temperature (Pi only).
#     
def getTemperature() -> float:
    try:
        txt = Path('/sys/class/thermal/thermal_zone0/temp').read_text()
        return ((float(txt) / 1000) * 9 / 5) + 32
    except Exception:
        return 0.0

#
# Get Throttle Status (Pi only).
#
def getThrottleStatus() -> str:
    try:
        vctxt = subprocess.run(['vcgencmd', 'get_throttled'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL).stdout.decode('utf-8').replace('throttled=', '')
        return vctxt
    except Exception:
        return 'N/A'

#
# Refresh Status Windows.
#
def refreshWinStatus():
    winStatus.clear()
    statusPrint(1, 'Autonomous: {} '.format(autoPilot))
    statusPrint(2, 'Dest.     : {} '.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    winStatus.box()
    winStatus.addstr(0, 1, 'TT40 Console', colorHeaderInfo)
    winStatus.refresh()

    winStatus2.clear()
    statusPrint(1, 'Load  : {}'.format(os.getloadavg()), 1)
    statusPrint(2, 'Gamma : {:1.2f}'.format(cfg.gamma), 1)
    statusPrint(3, 'Temp  : {:3.1f} F'.format(getTemperature()), 1)
    statusPrint(4, 'Status: {}'.format(getThrottleStatus()), 1)
    winStatus2.box()
    winStatus2.addstr(0, 1, 'Sensors', colorHeaderSensor)
    winStatus2.refresh()


#
# Spinners!
# https://stackoverflow.com/questions/2685435/cooler-ascii-spinners
#
def spin(t, display=0) -> str:
    if not curses.has_colors():
       display = display + 2
    return cfg.spin[display][t % len(cfg.spin[display])]


#
# Init GPIO.
#
def initGPIO():
    global piGPIO

    piGPIO = pigpio.pi(host=cfg.hostName)


#
# Reset LEDs to full bright (or dark).
#
def fullBright(lvl=1):
    statusPrint(3, f'Full Bright: {lvl}')

    for n in cfg.bcmPin.keys():
        pin = cfg.bcmPin[n]

        if pin is not None and pin > 0:
            levelIn[n] = cfg.pwm.step * lvl
            levelOut[n] = levelIn[n]
            piGPIO.write(pin, 1 - lvl)

    statusPrint(4, 'Level: [{R:3g}, {G:3g}, {B:3g}, {W:3g}]'.format(**levelIn))


#
# Gamma Shift a level.
#
def gammaShift(lvl) -> float:
    return pow(float(lvl) / float(cfg.pwm.step), cfg.gamma) * cfg.pwm.step


#
# Correct Colors to get to LED RGBW values.
#   Optional - Gamma Correction.
#   Optional - White Balance - Adjust RGB for calibrated levels due to human eye sensitivity.
#   Optional - Mix White channel with lowest RGB channel.
#   Optional - Scale for minimum forward voltage for each LED channel.
#   Safely clamp each channel to between 0 and pwm.step.
#
def colorCorrect(colorOrig:RGBWLevel, adjustGamma: bool = True, adjustWBalance: bool = True, adjustWMix: bool = True, adjustMin: bool = True) -> RGBWLevel:
    colorCorrected: RGBWLevel = colorOrig.copy()

    for k in colorOrig.keys():
        if k != 'W':
            # Gamma
            if adjustGamma:
                colorCorrected[k] = gammaShift(colorCorrected[k])

            # White Balance - Color Mix
            if adjustWBalance:
                colorCorrected[k] = colorCorrected[k] * cfg.mix[k]

    # Mix White
    if adjustWMix and cfg.mix.W > 0:
        rgb = {k: v for k, v in colorCorrected.items() if k != 'W'}
        minrgb = min(rgb, key=rgb.get)
        colorCorrected['W'] = rgb[minrgb] * cfg.mix.W
        colorCorrected[minrgb] = colorCorrected[minrgb] * (1 - cfg.mix.W)

    for k in colorCorrected.keys():
        # Scale for Minimum Forward Voltage
        if adjustMin:
            minl = cfg.min[k]
            maxl = cfg.pwm.step
            colorCorrected[k] = minl + ((colorCorrected[k] / maxl) * (maxl - minl))

        # Clamp
        colorCorrected[k] = int(min(cfg.pwm.step, max(0, colorCorrected[k])))

    return colorCorrected


#
# Set PWM Duty Cycle for RGBW channels (with optional color corrections).
#
def setPwmRgbw(colors, adjustGamma: bool = True, adjustWBalance: bool = True, adjustWMix: bool = True, adjustMin: bool = True):
    global levelIn
    global levelOut

    levelIn = colors

    if adjustGamma or adjustWBalance or adjustWMix or adjustMin:
        levelOut = colorCorrect(levelIn, adjustGamma=adjustGamma, adjustWBalance=adjustWBalance, adjustWMix=adjustWMix, adjustMin=adjustMin)
    else:
        levelOut = levelIn

    for pinName in cfg.bcmPin.keys():
        pin = cfg.bcmPin[pinName]

        if pin is not None and pin > 0:
            # Set duty cycle (inverted)
            levelOut[pinName] = levelOut[pinName]
            piGPIO.set_PWM_dutycycle(pin, cfg.pwm.step - levelOut[pinName])

    return levelOut


#
# Begin PWM.
#
def beginPWM():
    statusPrint(2, '--- Scanning ---')
    statusPrint(3, 'Begin PWM.')

    for pin in cfg.bcmPin.values():
        if pin is not None and pin > 0:
            piGPIO.set_PWM_frequency(pin, cfg.pwm.Hz)
            piGPIO.set_PWM_range(pin, cfg.pwm.step)


#
# End PWM.
#
def endPWM():
    statusPrint(3, 'End PWM.')
    levelIn = {'R': cfg.pwm.step, 'G': cfg.pwm.step, 'B': cfg.pwm.step, 'W': cfg.pwm.step}
    setPwmRgbw(levelIn)


#
# RGB Sinebow.
# http://basecase.org/env/on-rainbows
#
def sinebow(h) -> RGBWLevel:
    h += 1 / 2
    h *= -1
    r = math.sin(math.pi * h)
    g = math.sin(math.pi * (h + 1 / 3))
    b = math.sin(math.pi * (h + 2 / 3))
    w = 0
    return {'R': int(255 * r ** 2), 'G': int(255 * g ** 2), 'B': int(255 * b ** 2), 'W': w}


#
# RGB Sequence.
# http://basecase.org/env/on-rainbows
#
def nthcolor(n) -> RGBWLevel:
    phi = (1 + 5 ** 0.5) / 2
    return sinebow(n * phi)


#
# Convert RGB Hex string to RGBW Tuple.
# White will always be zero.
#
def hexToRGB(h) -> RGBWLevel:
    r, g, b = tuple(c for c in bytes.fromhex(h[1:]))
    return {'R': r, 'G': g, 'B': b, 'W': 0}


#
# Return RGB used to color fade from one color to the next in pattern.
#
def colorFade(p, i) -> RGBWLevel:
    j = int(i / cfg.fadeStep % len(p))
    s = i % cfg.fadeStep
    c1 = hexToRGB(p[j])
    c2 = hexToRGB(p[(j + 1) % len(p)])
    (r, g, b) = (int((c2[c] - c1[c]) / cfg.fadeStep * s) + c1[c] for c in range(3))
    w = 0
    return {'R': r, 'G': g, 'B': b, 'W': w}


#
# Return RGB used for the named effect.
#
def colorPattern(effect, i) -> RGBWLevel:
    name = effect.pattern
    fade = effect.fade

    if name == 'sinebow':
        return sinebow(i / cfg.pwm.step)
    elif name == 'random':
        return nthcolor(i)
    else:
        p = cfg.patterns[name]
        return colorFade(p, i) if fade else hexToRGB(p[i % len(p)])


#
# Check Curses for Escape Key press.
#
def shouldStopEffect(stdscr=None) -> bool:
    if stdscr is None:
        return False

    key = stdscr.getch()
    return key != curses.ERR and key == 27 


#
# Pulse Lights RGB effect.
#
def effectPulseRGB(snd, name='sinebow', stdscr=None):
    conPrint('Effect - PulseRGB: {} - {}'.format(name, snd))
    beginPWM()
    play = sound.playSound(snd)

    effect = cfg.effects[name]
    slow = effect.slow / cfg.fadeStep if effect.fade else effect.slow
    pwmSleep = pwmSleepDefault * slow
    i = 0

    while play.is_playing():
        if shouldStopEffect(stdscr):
            conPrint('>>> Effect stopped!')
            play.stop()
            return

        levelIn = colorPattern(effect, i)
        statusPrint(4, 'LevelI: {} {:3g} - [{R:3g}, {G:3g}, {B:3g}, {W:3g}]'.format(spin(i, 1), i, **levelIn))
        setPwmRgbw(levelIn)
        statusPrint(5, 'LevelO: {} {:3g} - [{R:3g}, {G:3g}, {B:3g}, {W:3g}]'.format(spin(i, 1), i, **levelOut))

        time.sleep(pwmSleep)
        i = i + 1

    endPWM()
    conPrint('All Stop')


#
# Pulse Lights / Dematerialise effect.
#
def effectPulse(f, pwmSleep=pwmSleepDefault, stdscr=None):
    conPrint('Effect - Pulse: ' + f)
    beginPWM()
    play = sound.playSound(f)

    i = 0
    while play.is_playing():
        if shouldStopEffect(stdscr):
            conPrint('>>> Effect stopped!')
            play.stop()
            return

        lvl = int(cfg.pwm.step * 0.5 * ((math.cos((i / cfg.pwm.step) * 2 * math.pi)) + 1))
        levelIn = {'R': lvl, 'G': lvl, 'B': lvl, 'W': lvl}
        statusPrint(4, 'Level : {} {:6g} of {:6g}'.format(spin(i, 1), lvl, cfg.pwm.step))
        setPwmRgbw(levelIn, adjustWBalance=False, adjustWMix= False)
        statusPrint(5, 'LevelO: {} {:3g} - [{R:3g}, {G:3g}, {B:3g}, {W:3g}]'.format(spin(i, 1), i, **levelOut))

        time.sleep(pwmSleep)
        i = i + 1

    endPWM()
    conPrint('All Stop')


#
# Blink Lights / Door Lock effect.
#
def effectBlink(snd, stdscr=None):
    conPrint('Effect - Blink: ' + snd)
    beginPWM()
    play = sound.playSound(snd)

    for lvl in [1, 0, 0.25, 1, 0, 0.25, 1]:
        if shouldStopEffect(stdscr):
            conPrint('>>> Effect stopped!')
            play.stop()
            return

        lvl *= cfg.pwm.step
        levelIn = {'R': lvl, 'G': lvl, 'B': lvl, 'W': lvl}
        statusPrint(4, 'Level: {:6g} of {:6g}'.format(lvl, cfg.pwm.step))
        setPwmRgbw(levelIn, adjustWBalance=False, adjustWMix= False)
        statusPrint(5, 'LevelO: [{R:3g}, {G:3g}, {B:3g}, {W:3g}]'.format( **levelOut))

        time.sleep(0.1)

    endPWM()
    conPrint('Locked')


#
# Shutdown.
#
def shutdown():
    global piGPIO
    global gp


    try:
       if sound is not None:
           log.debug('Shutdown Background Sound')
           sound.endBgSound()
    except:
        pass

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
# Signal Handler, exit on any signal.
#
def sig_handler(signal, frame):
    log.critical(f'Signal: {signal} - {frame}')
    sys.exit(1)


#
# Setup Curses TUI.
# Initialize colors and three panes.
#
def initCurses(stdscr: curses.window):
    global colorHeaderInfo
    global colorHeaderSensor
    global colorConsole
    global winConsole
    global winStatus
    global winStatus2


    log.debug(f'Console: {curses.termname()} - Colors: {curses.COLORS} - ChangeColor: {curses.can_change_color()}')
    curses.curs_set(0)
    curses.resizeterm(30, 80)

    # Mono 
    colorHeaderInfo = curses.A_REVERSE
    colorHeaderSensor = curses.A_BOLD
    colorConsole = curses.A_REVERSE
    
    if (curses.has_colors()):
        curses.start_color()
        curses.use_default_colors()

        if (curses.COLORS == 8):
            # XTerm ANSI
            curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_BLACK)
            curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
        elif (curses.COLORS > 255):
            # XTerm 256 (probably...)
            curses.init_pair(1, XTERM_COLOR_BLUE1, curses.COLOR_BLACK)
            curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
            curses.init_pair(3, curses.COLOR_BLACK, XTERM_COLOR_GREY58)
            colorConsole = curses.color_pair(3)

        colorHeaderInfo = curses.color_pair(1) | curses.A_BOLD
        colorHeaderSensor = curses.color_pair(2)

    stdscr.nodelay(True)
    stdscr.refresh()
    stdscr.leaveok(True)

    winStatus = curses.newwin(7, 40, 0, 0)
    winStatus2 = curses.newwin(7, 40, 0, 40)
    refreshWinStatus()

    winConsole = curses.newwin(22, 60, 7, 10)
    winConsole.scrollok(True)


#
# Main Loop.
#
def mainLoop(stdscr: curses.window):
    global colorHeaderInfo
    global colorHeaderSensor
    global colorConsole
    global gp
    global winConsole
    global winStatus
    global winStatus2
    global sound


    # Setup Curses TUI
    initCurses(stdscr)

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

    # Init GPIO/Sound
    initGPIO()
    fullBright()
    sound = SoundManager(cfg)
    sound.initBgSound()

    # Find Input Device
    conPrint('Locate Registered Operator')
    #sound.playSound('runaway_scanning_short.wav', True)
    devices = [evdev.InputDevice(fn) for fn in evdev.list_devices()]

    for device in devices:
        debugPrint('Device: ' + device.name + ' [' + device.path + ']')

        if device.name == cfg.devName:
            gp = evdev.InputDevice(device.path)
            break

    # if autoPilot and (gp is None):
    #    gp = evdev.InputDevice('/dev/input/event0')

    if not autoPilot and (gp is None):
        raise Exception('Operator Missing!')

    if gp is None:
        conPrint('Operator Missing, Autonomous Control active.')
    else:
        conPrint('Found Operator! [' + gp.name + ']')
        gp.grab()

    r = 0
    rf = cfg.loopRandMin
    vworp = True
    curses.flushinp()

    # Event Loop
    while vworp:
        time.sleep(cfg.loopSleep)

        if (r % 10 == 0):
            refreshWinStatus()

        statusPrint(5, 'Frame -- {} {} <{}>'.format(spin(r), r, rf if autoPilot else ''), 1)
        ranEvent = False
        event = gp.read_one() if gp is not None else None
        curseKey = stdscr.getch()

        # Autopilot Injects Events periodically
        if autoPilot and (r >= rf):
            r = 0
            rf = (random.randint(cfg.loopRandMin, cfg.loopRandMax)) * math.trunc(1 / cfg.loopSleep)
            event = evdev.events.InputEvent(0, 0, evdev.ecodes.EV_KEY, evdev.ecodes.KEY_ESC, 1)

        # Handle Event
        if (event is not None and (event.type == evdev.ecodes.EV_KEY or event.type == evdev.ecodes.EV_REL)) or (
                curseKey != curses.ERR):
            kCode = None

            if autoPilot and r == 0:
                conPrint('Autonomous action')
                kCode = random.choice(['UP', 'BTN_MIDDLE', 'BTN_LEFT', 'BTN_RIGHT', 'DOWN', 'u', 'i', 'r'])
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
                statusPrint(4, 'Key: ' + kCode)

            # Run Effect
            if kCode == 'BTN_LEFT' or kCode == 'w':
                effectPulse('takeoff.wav', pwmSleepDefault * 2, stdscr)
                ranEvent = True
            elif kCode == 'BTN_MIDDLE' or kCode == 'e':
                effectPulse('exterior_telephone.wav', pwmSleepDefault, stdscr)
                ranEvent = True
            elif kCode == 'BTN_RIGHT' or kCode == 'r':
                effectBlink('lock_chirp.wav', stdscr)
                ranEvent = True
            elif kCode == 'UP' or kCode == 't':
                effectPulseRGB('cloister_bell.wav', 'random', stdscr)
                ranEvent = True
            elif kCode == 'DOWN' or kCode == 'y':
                effectPulseRGB('denied_takeoff.wav', 'sinebow', stdscr)
                ranEvent = True
            elif kCode == 'u':
                # Test Effect
                effectPulseRGB('mummy.wav', 'mauveAlert', stdscr)
                ranEvent = True
            elif kCode == 'i':
                # Test Effect
                effectPulseRGB('runaway_scanning.wav', 'flag', stdscr)
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

                while gp is not None and gp.read_one() is not None:
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

    with open('console_config.json', encoding='utf-8') as f:
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
# Set XTerm Title Bar Message.
#
def setXtermTitle(title):
    print('\33]0;' + title + '\a', end='', flush=True)


#
# Configure Logging.
#
def configLog():
    global log

    logging.config.fileConfig('logging.ini')
    log = logging.getLogger()


#
# Init.
#
if __name__ == '__main__':
    try:
        stopMode = False

        # Set XTerm Title
        setXtermTitle('TT40 Console - Initializing...')

        # Handle Break
        signal.signal(signal.SIGINT, sig_handler)

        # Config Logging
        configLog()
        log.info('Event Zero.')

        # Read General Config
        readConfig()

        if len(sys.argv) > 1:
            autoPilot = sys.argv[1] == "auto"
            stopMode = sys.argv[1] == "stop"

        if stopMode:
            # Kill the lights
            setXtermTitle(f'TT40 Console - Stop Mode')
            initGPIO()
            fullBright(0)
            log.info('Stop Mode')
        else:
            # Start TUI Loop
            setXtermTitle(f'TT40 Console - Auto: {autoPilot}')
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
