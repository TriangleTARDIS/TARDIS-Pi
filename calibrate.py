#!/usr/bin/python3
#
# TARDIS SFX Calibration Tool.
#
# Copyright (C) 2017-2020 Michael Thompson.  All Rights Reserved.
#
# Created 06-22-2017 by Michael Thompson(triangletardis@gmail.com)
# Last modified 10-21-2020
#


__version__ = '4.1.1'

import colorsys
import curses
import logging.config
import signal
import sys
import threading
import time

from guizero import App, Drawing, Slider

import console


#
# Refresh Status Windows.
#
def refreshWinStatus():
    console.winStatus.clear()
    console.winStatus.box()
    console.winStatus.addstr(0, 1, 'TT40 Calibration', curses.color_pair(1))
    console.winStatus.refresh()

    console.winStatus2.clear()
    console.winStatus2.addstr(1, 1, 'PWM: {Hz} Hz - {step}'.format(**console.cfg.pwm))
    console.winStatus2.addstr(2, 1, 'Mix: {R}, {G}, {B}, {W}'.format(**console.cfg.mix))
    console.winStatus2.addstr(3, 1, 'Min: {R}, {G}, {B}, {W}'.format(**console.cfg.min))
    console.winStatus2.addstr(5, 1, 'UD, LR, / *, -+N')
    console.winStatus2.box()
    console.winStatus2.addstr(0, 1, 'Controls', curses.color_pair(1))
    console.winStatus2.refresh()


#
# Convert RGB value to hex string.
#
def rgb_to_hex(rgb) -> str:
    rgbn = tuple(int(c / console.cfg.pwm.step * 255) for c in rgb)
    return '#%02x%02x%02x' % rgbn


#
# Main Loop.
#
def mainLoop(stdscr, appgui):
    # FIXME: def mainLoop(stdscr: curses.window, appgui: App):
    # rgbBox: Drawing
    # rgbRect: Drawing

    # Setup Curses TUI
    curses.resizeterm(30, 80)
    curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_WHITE)

    stdscr.nodelay(True)
    stdscr.refresh()

    console.winStatus = curses.newwin(7, 40, 0, 0)
    console.winStatus2 = curses.newwin(7, 40, 0, 40)
    refreshWinStatus()

    console.winConsole = curses.newwin(22, 60, 7, 10)
    console.winConsole.scrollok(True)

    # Run System Init
    console.conPrint('***** Console Enabled *****')

    # Init GPIO
    console.initGPIO()
    console.beginPWM()

    # Setup GUI
    m1 = 20
    m2 = 10
    rgbBox = Drawing(master=appgui, width=appgui.width, height=m2 * 4, align='top')
    sliderHue = Slider(master=appgui, width=appgui.width, end=360)
    sliderSat = Slider(master=appgui, width=appgui.width, end=100)
    sliderVal = Slider(master=appgui, width=appgui.width, end=100)
    sliderGamma = Slider(master=appgui, width=appgui.width, start=1, end=50)
    sliderRx = Slider(master=appgui, width=appgui.width / 2, end=100)
    sliderGx = Slider(master=appgui, width=appgui.width / 2, end=100)
    sliderBx = Slider(master=appgui, width=appgui.width / 2, end=100)
    sliderWx = Slider(master=appgui, width=appgui.width / 2, end=100)

    # Init controls
    (r, g, b, w) = (0, 0, 0, 0)
    sliderHue.value = 30
    sliderSat.value = 100
    sliderVal.value = 100
    sliderRx.value = int(console.cfg.mix.R * 100)
    sliderGx.value = int(console.cfg.mix.G * 100)
    sliderBx.value = int(console.cfg.mix.B * 100)
    sliderWx.value = int(console.cfg.mix.W * 100)
    sliderGamma.value = console.cfg.gamma * 10
    adjust = 1
    vworp = True
    curses.flushinp()

    # Event Loop
    while vworp:
        #time.sleep(console.cfg.loopSleep / 25)

        # Pull values from sliders
        (h, s, v) = (int(sliderHue.value) / 360, int(sliderSat.value) / 100, int(sliderVal.value) / 100)
        (r, g, b) = tuple(int(c * console.cfg.pwm.step) for c in colorsys.hsv_to_rgb(h, s, v))
        console.cfg.gamma = float(sliderGamma.value) / 10
        mixR = float(sliderRx.value) / 100
        mixG = float(sliderGx.value) / 100
        mixB = float(sliderBx.value) / 100
        mixW = float(sliderWx.value) / 100

        # Keep values within bounds
        adjust = adjust % 3

        # Gamma shift controls
        (rl, gl, bl, wl) = (r, g, b, w)

        if adjust == 1:
            (rl, gl, bl, wl) = (r, g, b, w)
            rl = console.gammaShift(rl)
            gl = console.gammaShift(gl)
            bl = console.gammaShift(bl)

            rl = round(rl * mixR)
            gl = round(gl * mixG)
            bl = round(bl * mixB)

            # White Blend, gamma shift??
            # https://blog.athrunen.dev/experimenting-with-efficiently-combining-rgb-and-true-white/
            if mixW > 0:
                rgbl = [rl,gl,bl]
                index = rgbl.index(min(rgbl))
                wl = round(rgbl[index] * mixW);
                rgbl[index] = round(rgbl[index] * (1 - mixW));
                [rl, gl, bl] = rgbl

        # Setup PWM
        rl2 = console.setPwmDutyCycle('R', rl, adjust == 2)
        gl2 = console.setPwmDutyCycle('G', gl, adjust == 2)
        bl2 = console.setPwmDutyCycle('B', bl, adjust == 2)
        wl2 = console.setPwmDutyCycle('W', wl, adjust == 2)

        # Update TUI/GUI
        console.statusPrint(1, 'Gamma: {:1.2f}   Adj Mode: {}'.format(console.cfg.gamma, adjust))
        console.statusPrint(2, 'RGBW : {}, {}, {}, {}'.format(r, g, b, w))
        console.statusPrint(3, 'RGBWi: {}'.format(list(str(value) for value in console.levelIn.values())))
        console.statusPrint(4, 'RGBWo: {}, {}, {}, {}'.format(rl2, gl2, bl2, wl2))
        console.statusPrint(5, 'HSV  : {:1.0f}, {:1.0f}, {:1.0f}'.format(h * 360, s * 100, v * 100))

        try:
            rgbBox.clear()
            rgbBox.rectangle(0, 0, appgui.width, m2, rgb_to_hex((r, g, b)))
            rgbBox.rectangle(m1, m2, appgui.width - m1, m2 * 2, rgb_to_hex((rl, gl, bl)))
            rgbBox.rectangle(m1 * 2, m2 * 2, appgui.width - m1 * 2, m2 * 4, rgb_to_hex((rl2, gl2, bl2)))
            rgbBox.rectangle(0, m2 * 3, appgui.width, m2 * 4, rgb_to_hex((wl, wl, wl)))
        except BaseException as e:
            console.log.critical('GUI setup failed.', exc_info=sys.exc_info())
            raise

        k = stdscr.getch()

        if k == ord('q'):
            # Save final adjustments to print to console
            console.cfg.mix.R = mixR
            console.cfg.mix.G = mixG
            console.cfg.mix.B = mixB
            console.cfg.mix.W = mixW
            vworp = False
        elif k == ord('*'):
            adjust += 1
        elif k == ord('/'):
            adjust = (adjust % 2) + 1
        elif k == curses.KEY_UP:
            sliderHue.value += 30
        elif k == curses.KEY_DOWN:
            sliderHue.value -= 30
        elif k == curses.KEY_RIGHT:
            sliderSat.value += 5
        elif k == curses.KEY_LEFT:
            sliderSat.value -= 5
        # Up
        elif k == ord('-'):
            w += 1
        # Down
        elif k == 10:
            w -= 1
        # Middle
        elif k == ord('+'):
            w += 64 if w < console.cfg.pwm.step else -w

        if k != curses.ERR:
            console.conPrint('Key: {}'.format(k))
            refreshWinStatus()
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
        appgui = App(title='TT40 - Calibration ', width=240, height=380)
        threading.Thread(target=curses.wrapper, args=(mainLoop, appgui), daemon=True).start()
        appgui.display()
        console.shutdown()
        print('Final Gamma: {}'.format(console.cfg.gamma))
        print('Final Mix  : {R}, {G}, {B}, {W}'.format(**console.cfg.mix))
        print('Safe Exit')
        console.log.info('Safe Exit')
    except BaseException as e:
        console.shutdown()
        console.log.critical('Emergency Exit, unexpected error.', exc_info=sys.exc_info())
        print('Emergency Exit.  See log for details.')
        print(sys.exc_info())
        raise
