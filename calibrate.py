#!/usr/bin/python3
#
# TARDIS SFX Calibration Tool.
#
# Copyright (C) 2017-2020 Michael Thompson.  All Rights Reserved.
#
# Created 06-22-2017 by Michael Thompson(triangletardis@gmail.com)
# Last modified 10-13-2020
#


__version__ = '4.1.0'

import curses
import logging.config
import signal
import sys
import threading
import time

from guizero import App, Drawing

import console


#
# Refresh Status Windows.
#
def refreshWinStatus():
    console.winStatus.clear()
    console.winStatus.addstr(1, 1, 'Gamma: {:1.2f}'.format(console.cfg.gamma))
    console.winStatus.box()
    console.winStatus.addstr(0, 1, 'TT40 Calibration', curses.color_pair(1))
    console.winStatus.refresh()

    console.winStatus2.clear()
    console.winStatus2.addstr(1, 1, 'PWM: {}'.format(console.cfg.pwm))
    console.winStatus2.addstr(3, 1, 'Y,R,G,B,W,X')
    console.winStatus2.addstr(4, 1, 'y,u,i,o,p,[')
    console.winStatus2.box()
    console.winStatus2.addstr(0, 1, 'Controls', curses.color_pair(1))
    console.winStatus2.refresh()


#
# Convert RGB value to hex string.
#
def rgb_to_hex(rgb) -> str:
    return '#%02x%02x%02x' % rgb


#
# Main Loop.
#
def mainLoop(stdscr, appgui):
    #FIXME: def mainLoop(stdscr: curses.window, appgui: App):
    # rgbBox: Drawing
    # rgbRect: Drawing

    # Setup Curses TUI
    curses.resizeterm(33, 80)
    curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_WHITE)

    stdscr.nodelay(True)

    console.winStatus = curses.newwin(6, 40, 0, 0)
    console.winStatus2 = curses.newwin(6, 40, 0, 40)
    refreshWinStatus()

    console.winConsole = curses.newwin(26, 60, 6, 10)
    console.winConsole.scrollok(True)

    # Run System Init
    console.conPrint('***** Console Enabled *****')

    # Init GPIO
    console.initGPIO()
    console.beginPWM()

    # Setup GUI
    rgbBox = Drawing(master=appgui)

    # Init controls
    k = 0
    (r, g, b, w) = (0, 0, 0, 0)
    adjust = True
    vworp = True

    # Event Loop
    while vworp:
        time.sleep(0.1)

        # Keep values within bounds
        console.cfg.gamma = min(5.0, max(0.1, console.cfg.gamma))
        r = min(255, max(0, r))
        g = min(255, max(0, g))
        b = min(255, max(0, b))
        w = min(255, max(0, w))

        # Gamma shift controls
        rl = console.gammaShift(r)
        gl = console.gammaShift(g)
        bl = console.gammaShift(b)
        wl = console.gammaShift(w)

        # Update TUI/GUI
        console.statusPrint(2, 'RGBW : {}, {}, {} - {}'.format(r, g, b, w))
        console.statusPrint(3, 'RGBWx: {}, {}, {} - {}'.format(rl, gl, bl, w))
        console.statusPrint(4, 'Adj  : {}'.format(adjust))

        try:
            rgbBox.clear()
            rgbBox.rectangle(0, 5, 240, 35, rgb_to_hex((r, g, b)))
            rgbBox.rectangle(0, 40, 240, 70, rgb_to_hex((rl, gl, bl)))
            rgbBox.rectangle(0, 75, 240, 105, rgb_to_hex((wl, wl, wl)))
        except:
            vworp = False

        # Setup PWM
        console.setPwmDutyCycle(console.cfg.bcmPin.R, r, adjust)
        console.setPwmDutyCycle(console.cfg.bcmPin.G, g, adjust)
        console.setPwmDutyCycle(console.cfg.bcmPin.B, b, adjust)
        console.setPwmDutyCycle(console.cfg.bcmPin.W, w, adjust)

        k = stdscr.getch()

        if k == ord('y'):
            console.cfg.gamma += 0.1
        elif k == ord('u'):
            r += 1
        elif k == ord('i'):
            g += 1
        elif k == ord('o'):
            b += 1
        elif k == ord('p'):
            w += 1
        elif k == ord('['):
            adjust = not adjust
        elif k == ord('h'):
            console.cfg.gamma -= 0.1
        elif k == ord('j'):
            r -= 1
        elif k == ord('k'):
            g -= 1
        elif k == ord('l'):
            b -= 1
        elif k == ord(';'):
            w -= 1
        elif k == ord('6'):
            console.cfg.gamma = 1
        elif k == ord('7'):
            r += 128 if r < 255 else -256
        elif k == ord('8'):
            g += 128 if g < 255 else -256
        elif k == ord('9'):
            b += 128 if b < 255 else -256
        elif k == ord('0'):
            w += 128 if w < 255 else -256
        elif k == ord('q'):
            vworp = False

        if k != curses.ERR:
            console.conPrint('Key: {}'.format(k))
            refreshWinStatus()
            curses.flushinp()
            curses.doupdate()
        # endIf

    console.endPWM()
    appgui.tk.destroy()
    # endWhile


# End mainLoop


#
# Init.
#
if __name__ == '__main__':
    try:
        # Set XTerm Title
        print('\33]0;TT40_Console\a', end='', flush=True)

        # Handle Break
        signal.signal(signal.SIGINT, console.sig_handler)

        # Config Logging
        logging.config.fileConfig('logging.ini')
        console.log = logging.getLogger()
        console.log.info('Event Zero.')

        # Read General Config
        console.readConfig()

        # Start GUI/TUI Loop
        appgui = App(title='TT40 - Color Test GUI', width=320, height=120, )
        threading.Thread(target=curses.wrapper, args=(mainLoop, appgui), daemon=True).start()
        appgui.display()
        console.shutdown()
        print('Safe Exit')
        console.log.info('Safe Exit')
    except BaseException as e:
        console.shutdown()
        console.log.critical('Emergency Exit, unexpected error.', exc_info=sys.exc_info())
        print('Emergency Exit.  See log for details.')
        print(sys.exc_info())
        raise
