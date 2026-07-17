#!/usr/bin/python3
"""
TARDIS Console SFX Module.

Copyright (C) 2017-2026 M Thompson.  All Rights Reserved.

Created 06-22-2017 by M Thompson(triangletardis@gmail.com)
Last modified 07-17-2026

"""

__version__ = '4.1.8'

import sys
import curses
import logging.config
import math
import random
import signal
import time
from types import FrameType
from typing import Any, cast
import evdev

from Console.Config import ConsoleConfig
from Console.Terminal import ManagerTerminal
from Console.Sound import ManagerSound
from Console.LED import ManagerLED

# Globals
cfg: ConsoleConfig
log: logging.Logger = logging.root
autoPilot: bool = False
gp: evdev.InputDevice[str]
foundOp: bool = False
terminal: ManagerTerminal | None = None
sound: ManagerSound | None = None
led: ManagerLED | None = None


def shutdown():
    """Shutdow evdev, GPIO, Sound, and Terminal."""
    global gp
    global foundOp
    global piGPIO
    global sound
    global terminal

    if foundOp:
        log.debug('Shutdown evDev')
        gp.ungrab()
        foundOp = False

    if led is not None and led.piGPIO is not None:
        log.debug('Shutdown PIGPIO')
        led.piGPIO.stop()

    if sound is not None:
        log.debug('Shutdown Sound')
        sound.endBgSound()

    if terminal is not None:
        log.debug('Shutdown Curses')
        terminal.shutdown()

    log.debug('Shutdown Finished')


def sig_handler(signum: int, frame: FrameType | None):
    """Signal Handler, exit on any signal."""
    log.critical(f'Signal: {signum} - {frame}')
    sys.exit(1)


def mainLoop(stdscr: curses.window):
    """Main Loop."""
    global gp
    global foundOp
    global terminal
    global sound
    global led

    # Setup Curses TUI
    terminal = ManagerTerminal(cfg=cfg, log=log, stdscr=stdscr, autoPilot=autoPilot)
    terminal.initCurses()
    terminal.refreshWinStatus()

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
    terminal.conPrint('***** Console Enabled *****')

    # Init Sound
    sound = ManagerSound(cfg=cfg, log=log)
    sound.initBgSound()

    # Init GPIO
    led = ManagerLED(cfg=cfg, log=log, sound=sound, terminal=terminal)
    led.initGPIO()
    led.fullBright()

    # Find Input Device and Grab if Primary
    # sound.playSound('runaway_scanning_short.wav', True)
    terminal.conPrint('Locate Registered Operator')

    for fn in evdev.list_devices():  # pyright: ignore[reportUnknownMemberType]
        terminal.debugPrint(f'Device: {fn}')
        device = evdev.InputDevice(fn)
        terminal.debugPrint('Device: ' + device.name + ' [' + device.path + ']')

        if device.name == cfg.devName:
            gp = evdev.InputDevice(device.path)
            foundOp = True
            break

    if not autoPilot and not foundOp:
        raise Exception('Operator Missing!')
    elif not foundOp:
        terminal.conPrint('Operator Missing, Autonomous Control active.')
    else:
        terminal.conPrint('Found Operator! [' + gp.name + ']')
        gp.grab()

    # Init. Loop
    r = 0
    rf = cfg.loopRandMin
    vworp = True
    curses.flushinp()

    # Event Loop
    while vworp:
        time.sleep(cfg.loopSleep)

        #FIXME: Is this needed?
        #if r % 10 == 0:
            #terminal.refreshWinStatus()

        terminal.statusPrint(5, 'Frame -- {} {} <{}>'.format(terminal.spin(r), r, rf if autoPilot else ''), 1)
        ranEvent = False
        event: evdev.InputEvent | None = None

        # Read Keyboard via Curses and Optional Mouse Controller via evdev
        curseKey = stdscr.getch()
        kCode: str | None = None

        if foundOp:
            event = cast(evdev.InputEvent, gp.read_one())  # type: ignore

        # Autopilot Injects Events periodically
        if autoPilot and (r >= rf):
            r = 0
            rf = (random.randint(cfg.loopRandMin, cfg.loopRandMax)) * math.trunc(1 / cfg.loopSleep)
            curseKey = curses.KEY_SRESET
            kCode = random.choice(['UP', 'BTN_MIDDLE', 'BTN_LEFT', 'BTN_RIGHT', 'WHEEL_DOWN', 'u', 'i', 'r'])

        # Handle Event
        if (event is not None and (event.type == evdev.ecodes.EV_KEY or event.type == evdev.ecodes.EV_REL)) or (curseKey != curses.ERR):
            if autoPilot and r == 0:
                terminal.conPrint('Autonomous action...')
            else:
                terminal.conPrint('Manual action...')

                # Handle EVDEV and Curses inputs
                if event is not None:
                    keyevent = evdev.categorize(event)

                    if event.type == evdev.ecodes.EV_KEY and isinstance(keyevent, evdev.events.KeyEvent) and keyevent.keystate == evdev.events.KeyEvent.key_down:
                        # Handle multiple key press
                        kCode = keyevent.keycode[0] if isinstance(keyevent.keycode, tuple) else keyevent.keycode
                    elif event.code == evdev.ecodes.REL_WHEEL:
                        # Convert mouse wheel axis to single press
                        kCode = 'WHEEL_UP' if event.value == 1 else 'WHEEL_DOWN'
                else:
                    kCode = chr(curseKey)

            if kCode is not None:
                r = 0
                terminal.statusPrint(4, f'Key: {kCode}[{curseKey}]')

            # Run Effect
            if kCode == 'BTN_LEFT' or kCode == 'w':
                led.effectPulse('takeoff.wav', cfg.pwm.pwmSleepDefault * 4)
                ranEvent = True
            elif kCode == 'BTN_MIDDLE' or kCode == 'e':
                led.effectPulse('exterior_telephone.wav', cfg.pwm.pwmSleepDefault)
                ranEvent = True
            elif kCode == 'BTN_RIGHT' or kCode == 'r':
                led.effectBlink('lock_chirp.wav')
                ranEvent = True
            elif kCode == 'WHEEL_UP' or kCode == 't':
                led.effectPulseRGB('cloister_bell.wav', 'random')
                ranEvent = True
            elif kCode == 'WHEEL_DOWN' or kCode == 'y':
                led.effectPulseRGB('denied_takeoff.wav', 'sinebow')
                ranEvent = True
            elif kCode == 'u':
                led.effectPulseRGB('mummy.wav', 'mauveAlert')
                ranEvent = True
            elif kCode == 'i':
                led.effectPulseRGB('runaway_scanning.wav', 'flag')
                ranEvent = True
            elif kCode == 'q':
                vworp = False

            # Empty Input Buffer
            if ranEvent:
                terminal.refreshWinStatus()
                curses.flushinp()
                curses.doupdate()

                while foundOp and gp.read_one() is not None:  # type: ignore
                    pass

            led.fullBright()
        # endif

        r += 1
        r %= 4000
    # endWhile

# End mainLoop


def readConfig() -> ConsoleConfig:
    """Read Config from JSON file."""
    global cfg

    with open('console_config.json', encoding='utf-8') as f:
        cfg = ConsoleConfig.model_validate_json(f.read())

    log.info(cfg)
    log.debug('Debug: %s', cfg.debug)
    log.debug('Names: %s', list(cfg.bcmPin.model_dump().keys()))
    log.debug('Pins : %s', cfg.bcmPin)
    log.debug('PWM Sleep: %s', cfg.pwm.pwmSleepDefault)

    return cfg


def setXtermTitle(title: str):
    """Set the XTerm title bar message."""
    print('\33]0;' + title + '\a', end='', flush=True)


def configLog():
    """Configure Logging."""
    global log

    logging.config.fileConfig('logging.ini')
    log = logging.getLogger()


#
# Init.
#
if __name__ == '__main__':
    try:
        stopMode = False

        # Handle Break
        signal.signal(signal.SIGINT, sig_handler)

        # Set XTerm Title
        setXtermTitle('TT40 Console - Initializing...')

        # Config Logging
        configLog()
        log.info('Event Zero.')

        # Read General Config
        cfg = readConfig()

        # Determine Mode
        if len(sys.argv) > 1:
            autoPilot = sys.argv[1] == 'auto'
            stopMode = sys.argv[1] == 'stop'

        if stopMode:
            # Kill the lights
            setXtermTitle('TT40 Console - Stop Mode')
            log.info('Stop Mode')
            led = ManagerLED(cfg, log, None, None)
            led.initGPIO()
            led.fullBright(0)
        else:
            # Start TUI Loop
            setXtermTitle(f'TT40 Console - Auto: {autoPilot}')
            log.info('Normal Mode')
            curses.wrapper(mainLoop)

        # Finished
        shutdown()
        log.info('Safe Exit.')
    except BaseException:
        shutdown()
        log.exception('Emergency Exit.')
        print('Emergency Exit.  See log for details.')
        raise
