#!/usr/bin/python3
#
# TARDIS SFX Calibration Tool GUI.
#
# Copyright (C) 2017-2026 Michael Thompson.  All Rights Reserved.
#
# Created 06-22-2017 by Michael Thompson(triangletardis@gmail.com)
# Last modified 07-09-2026
#

__version__ = '4.1.8'


import colorsys
import curses
import logging.config
import signal
import sys
import threading
import time
import guizero
from tkinter import Canvas

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
    console.winStatus2.addstr(5, 1, 'UD - Hue, LR - Sat, * - Mode')
    console.winStatus2.box()
    console.winStatus2.addstr(0, 1, 'Controls', curses.color_pair(1))
    console.winStatus2.refresh()


#
# Convert RGB value to hex string.
#
def rgb_to_hex(rgbL: console.RGBWLevel) -> str:
    rgb = tuple((rgbL['R'], rgbL['G'], rgbL['B']))
    rgbn = tuple(int(c / console.cfg.pwm.step * 255) for c in rgb)
    return '#%02x%02x%02x' % rgbn

#
# Main Loop.
#
def mainLoop(stdscr: curses.window, appgui: guizero.App):
    rgbBox: Canvas

    # Setup Curses TUI
    console.initCurses(stdscr)
    refreshWinStatus()

    # Run System Init
    console.conPrint('***** Console Enabled *****')

    # Init GPIO
    console.initGPIO()
    console.beginPWM()

    # Setup GUI
    y = 0

    for col in range(1, 4):
        appgui.tk.columnconfigure(col, weight=1)

    rgbText = guizero.Text(master=appgui, grid=[0, y], text='In\nCorrected\nOut', align='left')
    recHeight = 28
    rgbBox = Canvas(master=appgui.tk, bd=0, highlightthickness=0, bg='black', height=recHeight * 3)
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
        (h, s, v) = (int(sliderHue.value) / 360, int(sliderSat.value) / 100, int(sliderVal.value) / 100)
        (r, g, b) = tuple(int(c * console.cfg.pwm.step) for c in colorsys.hsv_to_rgb(h, s, v))
        w = int(sliderInitW.value / 100 * console.cfg.pwm.step)
        console.levelIn['R'] = r
        console.levelIn['G'] = g
        console.levelIn['B'] = b
        console.levelIn['W'] = w
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
        colorCorrected = console.colorCorrect(console.levelIn, adjustGamma=True, adjustWBalance=True, adjustWMix=True, adjustMin=True)
    
        # Setup PWM
        if (adjustMode == 0):
            console.setPwmRgbw(console.levelIn, adjustGamma=False, adjustWBalance=False, adjustWMix=False, adjustMin=False)
        else:
            console.setPwmRgbw(console.levelIn, adjustGamma=chkGamma.value, adjustWBalance=chkBalance.value, adjustWMix=chkWMix.value, adjustMin=chkMin.value)

        # Update TUI
        refreshWinStatus()
        console.statusPrint(1, 'Gamma: {:1.2f}   Adj Mode: {}'.format(console.cfg.gamma, adjustMode))
        console.statusPrint(2, 'RGBWi: {}'.format(list(str(value) for value in console.levelIn.values())))
        console.statusPrint(3, 'RGBWc: {}'.format(list(str(value) for value in colorCorrected.values())))
        console.statusPrint(4, 'RGBWo: {}'.format(list(str(value) for value in console.levelOut.values())))
        console.statusPrint(5, 'HSV  : {:1.0f}, {:1.0f}, {:1.0f}'.format(h * 360, s * 100, v * 100))

        # Update GUI
        rgbBox.delete('all')
        recPad = 50
        width = max(1, rgbBox.winfo_width())
        rgbBox.create_rectangle(0, 0, width, recHeight, fill=rgb_to_hex(console.levelIn), outline='')
        rgbBox.create_rectangle(recPad, recHeight, width - recPad, recHeight * 2, fill=rgb_to_hex(colorCorrected), outline='')
        rgbBox.create_rectangle(recPad * 2, recHeight * 2, width - recPad * 2, recHeight * 4, fill=rgb_to_hex(console.levelOut), outline='')

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
            console.conPrint('Key: {}'.format(k))

        curses.doupdate()
    # endWhile

    console.endPWM()
    appgui.tk.destroy()

# End mainLoop


#
# Init.
#
if __name__ == '__main__':
    try:
        # Set XTerm Title
        console.setXtermTitle('TT40 --==Calibration==--')

        # Handle Break
        signal.signal(signal.SIGINT, console.sig_handler)

        # Config Logging
        console.configLog()
        console.log.info('Event Zero.')

        # Read General Config
        console.readConfig()

        # Start GUI/TUI Loop
        appgui = guizero.App(title='Aux Control', width=310, height=400, layout='grid')
        threading.Thread(target=curses.wrapper, args=(mainLoop, appgui), daemon=True).start()
        appgui.display()

        # Finished
        console.shutdown()
        print('Final Gamma: {}'.format(console.cfg.gamma))
        print('Final Mix  : {R}, {G}, {B}, {W}'.format(**console.cfg.mix))
        print('Final Min  : {R}, {G}, {B}, {W}'.format(**console.cfg.min))
        print('Safe Exit')
        console.log.info('Safe Exit')
    except BaseException as e:
        console.shutdown()
        console.log.critical('Emergency Exit, unexpected error.', exc_info=sys.exc_info())
        print('Emergency Exit.  See log for details.')
        print(sys.exc_info())
        raise
