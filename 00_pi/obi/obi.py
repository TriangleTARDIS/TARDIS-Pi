#!/usr/bin/python3
#
# TARDIS SFX module.
#
# Copyright (C) 2017-2020 Michael Thompson.  All Rights Reserved.
#
# Created 06-22-2017 by Michael Thompson(triangletardis@gmail.com)
# Last modified 12-18-2020
#


__version__ = '1.0.0'

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

import evdev
import munch
import pigpio
import simpleaudio

from pyobihai import PyObihai

#
# Init.
#
if __name__ == '__main__':
    try:
        p = PyObihai("192.168.2.3", "user", "API_PASSWORD")
        print(p.get_state())
        print(p.get_line_state())
        print(p.get_call_direction())
        print('Safe Exit')
    except BaseException as e:
        print('Emergency Exit.  See log for details.')
        print(sys.exc_info())
        raise
