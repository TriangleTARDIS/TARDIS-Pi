"""
TARDIS Console SFX Module - Terminal.

Copyright (C) 2017-2026 M Thompson.  All Rights Reserved.

Created 06-22-2017 by M Thompson (triangletardis@gmail.com)
Last modified 07-16-2026
"""

from datetime import datetime
import logging
import curses
import os

from Console.Config import ConsoleConfig
from Console import Sensors


class ManagerTerminal:
    # Consts
    XTERM_COLOR_BLUE1 = 21
    XTERM_COLOR_GREY58 = 246

    log: logging.Logger
    cfg: ConsoleConfig
    stdscr: curses.window
    colorHeaderInfo: int = curses.A_REVERSE
    colorHeaderSensor: int = curses.A_BOLD
    colorConsole: int = curses.A_REVERSE
    winConsole: curses.window
    winStatus: curses.window
    winStatus2: curses.window
    autoPilot: bool = False

    def __init__(self, log: logging.Logger, cfg: ConsoleConfig, stdscr: curses.window, autoPilot: bool):
        self.log = log
        self.cfg = cfg
        self.stdscr = stdscr
        self.autoPilot = autoPilot

    def initCurses(self):
        """Setup Curses TUI.
        Initialize colors and three panes."""

        self.log.debug(f'Console: {curses.termname()} - Colors: {curses.COLORS} - ChangeColor: {curses.can_change_color()}')

        curses.curs_set(0)
        curses.resizeterm(30, 80)

        # Initialize Colors by Terminal Type
        # Mono (defaults above)
        if curses.has_colors():
            curses.start_color()
            curses.use_default_colors()

            if curses.COLORS == 8:
                # XTerm ANSI
                curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_BLACK)
                curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
            elif curses.COLORS > 255:
                # XTerm 256 (probably...)
                curses.init_pair(1, ManagerTerminal.XTERM_COLOR_BLUE1, curses.COLOR_BLACK)
                curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
                curses.init_pair(3, curses.COLOR_BLACK, ManagerTerminal.XTERM_COLOR_GREY58)
                self.colorConsole = curses.color_pair(3)

            self.colorHeaderInfo = curses.color_pair(1) | curses.A_BOLD
            self.colorHeaderSensor = curses.color_pair(2)

        self.stdscr.nodelay(True)
        self.stdscr.refresh()
        self.stdscr.leaveok(True)

        self.winStatus = curses.newwin(7, 40, 0, 0)
        self.winStatus.box()
        self.winStatus2 = curses.newwin(7, 40, 0, 40)
        self.winStatus2.box()

        self.winConsole = curses.newwin(22, 60, 7, 10)
        self.winConsole.scrollok(True)

    def shutdown(self):
        curses.curs_set(1)
        # FIXME: Looks like maybe wrapper is handling this?
        # curses.endwin()
        pass

    def shouldStopEffect(self) -> bool:
        """Check Curses for Backspace Key press.
        Originally tried Escape Key but there is a fun delay due to ESC codes.
        https://stackoverflow.com/questions/27372068/why-does-the-escape-key-have-a-delay-in-python-curses"""
        key = self.stdscr.getch()
        return key != curses.ERR and key == curses.KEY_BACKSPACE

    def lcdPrint(self, s: str):
        """Print a string to the LCD."""

        pass

    def conPrint(self, s: str):
        """Print a string to the console and log it."""
        self.log.info(s)

        self.winConsole.bkgd(' ', self.colorConsole)
        self.winConsole.addstr(' ' + s + '\n')
        self.winConsole.box()
        self.winConsole.noutrefresh()

    def debugPrint(self, s: str):
        """Print a debug string to the console."""
        self.log.debug(s)

        if self.cfg.debug:
            self.conPrint(s)

    def statusPrint(self, line: int, s: str, win: int = 0):
        """Print a status string to the console."""
        w = self.winStatus if win == 0 else self.winStatus2
        _, y = w.getmaxyx()
        y = y - 2
        w.addstr(line, 1, s.ljust(y)[:y])
        w.refresh()

        # Really spammy
        if self.cfg.debug:
            self.log.debug(s)

    def refreshWinStatus(self):
        """Refresh Status Windows."""
        self.winStatus.clear()
        self.statusPrint(1, 'Autonomous: {} '.format(self.autoPilot))
        self.statusPrint(2, 'Dest.     : {} '.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        self.winStatus.box()
        self.winStatus.addstr(0, 1, 'TT40 Console', self.colorHeaderInfo)
        self.winStatus.refresh()

        self.winStatus2.clear()
        self.statusPrint(1, 'Load  : {}'.format([f"{x:.2f}" for x in os.getloadavg()]), 1)
        self.statusPrint(2, 'Gamma : {:1.2f}'.format(self.cfg.gamma), 1)
        self.statusPrint(3, 'Temp  : {:3.1f} F'.format(Sensors.getTemperature()), 1)
        self.statusPrint(4, 'Status: {}'.format(Sensors.getThrottleStatus()), 1)
        self.winStatus2.box()
        self.winStatus2.addstr(0, 1, 'Sensors', self.colorHeaderSensor)
        self.winStatus2.refresh()

    def spin(self, t: int, display: int = 0) -> str:
        """Spinners!
        https://stackoverflow.com/questions/2685435/cooler-ascii-spinners"""
        if not curses.has_colors():
            display = display + 2
        return self.cfg.spin[display][t % len(self.cfg.spin[display])]
