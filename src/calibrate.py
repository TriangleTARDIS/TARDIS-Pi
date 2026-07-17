#!/usr/bin/python3
"""
TARDIS Console SFX LED Calibration Tool GUI.

Copyright (C) 2017-2026 M Thompson.  All Rights Reserved.

Created 06-22-2017 by M Thompson(triangletardis@gmail.com)
Last modified 07-17-2026
"""

import colorsys
import curses
import signal
import sys
import threading
import time
import guizero
from tkinter import Canvas

from Console.Terminal import ManagerTerminal
from Console.LED import ManagerLED
import console

def refreshWinStatus():
    """Refresh WinStatus Override."""

    if console.terminal is not None:
        console.terminal.winStatus.clear()
        console.terminal.winStatus.box()
        console.terminal.winStatus.addstr(0, 1, 'TT40 Calibration', curses.color_pair(1))
        console.terminal.winStatus.refresh()

        console.terminal.winStatus2.clear()
        console.terminal.winStatus2.addstr(1, 1, 'PWM: {Hz} Hz - {step}'.format(**console.cfg.pwm.model_dump()))
        console.terminal.winStatus2.addstr(2, 1, 'Mix: {R}, {G}, {B}, {W}'.format(**console.cfg.mix.model_dump()))
        console.terminal.winStatus2.addstr(3, 1, 'Min: {R}, {G}, {B}, {W}'.format(**console.cfg.min.model_dump()))
        console.terminal.winStatus2.addstr(5, 1, 'UD - Hue, LR - Sat, * - Mode')
        console.terminal.winStatus2.box()
        console.terminal.winStatus2.addstr(0, 1, 'Controls', curses.color_pair(1))
        console.terminal.winStatus2.refresh()


def mainLoop(stdscr: curses.window, appgui: guizero.App):
    """Main Loop."""
    rgbBox: Canvas

    # Setup Curses TUI
    console.terminal = ManagerTerminal(cfg=console.cfg, log=console.log, stdscr=stdscr, autoPilot=False)
    console.terminal.initCurses()
    refreshWinStatus()

    # Run System Init
    console.terminal.conPrint('***** Console Enabled *****')

    # Init GPIO
    console.led = ManagerLED(console.cfg, console.log, None, console.terminal)
    console.led.initGPIO()
    console.led.beginPWM()

    # Setup GUI
    y = 0

    for col in range(1, 4):
        appgui.tk.columnconfigure(col, weight=1)  # pyright: ignore[reportUnknownMemberType]

    guizero.Text(master=appgui, grid=[0, y], text='In\nCorrected\nOut', align='left')
    recHeight = 28
    rgbBox = Canvas(master=appgui.tk, bd=0, highlightthickness=0, bg='black', height=recHeight * 3)  # pyright: ignore[reportUnknownArgumentType]
    rgbBox.grid(column=1, row=y, columnspan=3, sticky='ew')
    y += 1

    guizero.Text(master=appgui, grid=[0, y], text='HSV', align='left')
    sliderHue = guizero.Slider(master=appgui, grid=[1, y], end=360)
    sliderSat = guizero.Slider(master=appgui, grid=[2, y], end=100)
    sliderVal = guizero.Slider(master=appgui, grid=[3, y], end=100)
    y += 1

    guizero.Text(master=appgui, grid=[0, y], text='InitW', align='left')
    sliderInitW = guizero.Slider(master=appgui, grid=[1, y, 3, 1], end=100)
    y += 1

    guizero.Text(master=appgui, grid=[0, y], text='Gamma', align='left')
    sliderGamma = guizero.Slider(master=appgui, grid=[1, y, 3, 1], start=0, end=50)
    y += 1

    guizero.Text(master=appgui, grid=[0, y], text='Rx')
    sliderRMix = guizero.Slider(master=appgui, grid=[1, y], end=100)
    sliderRMin = guizero.Slider(master=appgui, grid=[3, y], end=10)
    y += 1

    guizero.Text(master=appgui, grid=[0, y], text='Gx')
    sliderGMix = guizero.Slider(master=appgui, grid=[1, y], end=100)
    sliderGMin = guizero.Slider(master=appgui, grid=[3, y], end=10)
    y += 1

    guizero.Text(master=appgui, grid=[0, y], text='Bx')
    sliderBMix = guizero.Slider(master=appgui, grid=[1, y], end=100)
    sliderBMin = guizero.Slider(master=appgui, grid=[3, y], end=10)
    y += 1

    guizero.Text(master=appgui, grid=[0, y], text='Wx')
    sliderWMix = guizero.Slider(master=appgui, grid=[1, y], end=100)
    sliderWMin = guizero.Slider(master=appgui, grid=[3, y], end=10)
    y += 1

    chkGamma = guizero.CheckBox(master=appgui, grid=[0, y], text='GamAdj', align='left')
    chkBalance = guizero.CheckBox(master=appgui, grid=[1, y], text='W.Bal', align='left')
    chkWMix = guizero.CheckBox(master=appgui, grid=[2, y], text='W.Mix', align='left')
    chkMin = guizero.CheckBox(master=appgui, grid=[3, y], text='MinFwd', align='left')
    y += 1

    # Init controls
    sliderHue.value = 30
    sliderSat.value = 80
    sliderVal.value = 90
    sliderInitW.value = 0
    sliderRMix.value = int(console.cfg.mix.R * 100)
    sliderRMin.value = int(console.cfg.min.R)
    sliderGMix.value = int(console.cfg.mix.G * 100)
    sliderGMin.value = int(console.cfg.min.G)
    sliderBMix.value = int(console.cfg.mix.B * 100)
    sliderBMin.value = int(console.cfg.min.B)
    sliderWMix.value = int(console.cfg.mix.W * 100)
    sliderWMin.value = int(console.cfg.min.W)
    sliderGamma.value = console.cfg.gamma * 10
    chkGamma.value = True
    chkBalance.value = True
    chkWMix.value = True
    chkMin.value = True
    adjustMode = 1
    vworp = True
    curses.flushinp()

    # Event Loop
    while vworp:
        time.sleep(console.cfg.loopSleep)

        # Pull values from sliders
        (h, s, v) = (
            int(sliderHue.value) / 360,
            int(sliderSat.value) / 100,
            int(sliderVal.value) / 100,
        )
        (r, g, b) = tuple(int(c * console.cfg.pwm.step) for c in colorsys.hsv_to_rgb(h, s, v))
        w = int(sliderInitW.value / 100 * console.cfg.pwm.step)
        console.led.levelIn['R'] = r
        console.led.levelIn['G'] = g
        console.led.levelIn['B'] = b
        console.led.levelIn['W'] = w
        console.cfg.gamma = float(sliderGamma.value) / 10
        console.cfg.mix.R = float(sliderRMix.value) / 100
        console.cfg.mix.G = float(sliderGMix.value) / 100
        console.cfg.mix.B = float(sliderBMix.value) / 100
        console.cfg.mix.W = float(sliderWMix.value) / 100
        console.cfg.min.R = int(sliderRMin.value)
        console.cfg.min.G = int(sliderGMin.value)
        console.cfg.min.B = int(sliderBMin.value)
        console.cfg.min.W = int(sliderWMin.value)

        # Keep values within bounds
        adjustMode = adjustMode % 2

        # Mode 0: No adjustment (raw output)
        # Mode 1: Console Handles Adjustment
        colorCorrected = console.led.colorCorrect(
            console.led.levelIn,
            adjustGamma=True,
            adjustWBalance=True,
            adjustWMix=True,
            adjustMin=True,
        )

        # Setup PWM
        if adjustMode == 0:
            console.led.setPwmRgbw(
                console.led.levelIn,
                adjustGamma=False,
                adjustWBalance=False,
                adjustWMix=False,
                adjustMin=False,
            )
        else:
            console.led.setPwmRgbw(
                console.led.levelIn,
                adjustGamma=chkGamma.value,
                adjustWBalance=chkBalance.value,
                adjustWMix=chkWMix.value,
                adjustMin=chkMin.value,
            )

        # Update TUI
        console.terminal.statusPrint(1, 'Gamma: {:1.2f}   Adj Mode: {}'.format(console.cfg.gamma, adjustMode))
        console.terminal.statusPrint(2, f'RGBWi: {console.led.levelIn}')
        console.terminal.statusPrint(3, f'RGBWc: {colorCorrected}')
        console.terminal.statusPrint(4, f'RGBWo: {console.led.levelOut}')
        console.terminal.statusPrint(5, 'HSV  : {:1.0f}, {:1.0f}, {:1.0f}'.format(h * 360, s * 100, v * 100))

        # Update GUI
        #rgbBox.delete('all')
        recPad = 50
        width = max(1, rgbBox.winfo_width())
        rgbBox.create_rectangle(
            0,
            0,
            width,
            recHeight,
            fill=ManagerLED.rgbToHex(console.led.levelIn, console.cfg.pwm.step),
            outline='',
        )
        rgbBox.create_rectangle(
            recPad,
            recHeight,
            width - recPad,
            recHeight * 2,
            fill=ManagerLED.rgbToHex(colorCorrected, console.cfg.pwm.step),
            outline='',
        )
        rgbBox.create_rectangle(
            recPad * 2,
            recHeight * 2,
            width - recPad * 2,
            recHeight * 4,
            fill=ManagerLED.rgbToHex(console.led.levelOut, console.cfg.pwm.step),
            outline='',
        )

        # Handle Event
        k = stdscr.getch()

        if k == ord('q'):
            vworp = False
        elif k == ord('*'):
            adjustMode += 1
        elif k == curses.KEY_UP:
            sliderHue.value += 30
        elif k == curses.KEY_DOWN:
            sliderHue.value -= 30
        elif k == curses.KEY_RIGHT:
            sliderSat.value += 5
        elif k == curses.KEY_LEFT:
            sliderSat.value -= 5

        if k != curses.ERR:
            console.terminal.conPrint('Key: {}'.format(k))

        curses.doupdate()
    # endWhile

    appgui.tk.destroy()  # pyright: ignore[reportUnknownMemberType]
# End mainLoop


#
# Init.
#
if __name__ == '__main__':
    try:
        # Handle Break
        signal.signal(signal.SIGINT, console.sig_handler)

        # Set XTerm Title
        console.setXtermTitle('TT40 --==Calibration==--')

        # Config Logging
        console.configLog()
        console.log.info('Event Zero.')

        # Read General Config
        console.cfg = console.readConfig()

        # Start GUI/TUI Loop
        appgui = guizero.App(title='Aux Control', width=310, height=400, layout='grid')
        threading.Thread(target=curses.wrapper, args=(mainLoop, appgui), daemon=True).start()
        appgui.display()

        # Finished
        curses.endwin()
        console.shutdown()
        print('Final Gamma: {}'.format(console.cfg.gamma))
        print('Final Mix  : {R}, {G}, {B}, {W}'.format(**console.cfg.mix.model_dump()))
        print('Final Min  : {R}, {G}, {B}, {W}'.format(**console.cfg.min.model_dump()))
        print('Safe Exit')
        console.log.info('Safe Exit')
    except BaseException:
        console.shutdown()
        console.log.exception('Emergency Exit.')
        print('Emergency Exit.  See log for details.')
        raise
