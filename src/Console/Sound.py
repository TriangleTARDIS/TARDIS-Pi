"""
TARDIS Console SFX Module - Sound.

Copyright (C) 2017-2026 M Thompson.  All Rights Reserved.

Created 06-22-2017 by M Thompson (triangletardis@gmail.com)
Last modified 07-16-2026
"""

import time
import logging
from simpleaudio import WaveObject, PlayObject
from threading import Thread, Event

from Console.Config import ConsoleConfig


class ManagerSound:
    """Console Sound Manager - Background Ambient Sound and FX Sounds."""

    log: logging.Logger
    cfg: ConsoleConfig
    bgSoundThread: Thread | None = None
    bgSoundEnd: Event = Event()

    def __init__(self, log: logging.Logger, cfg: ConsoleConfig):
        self.log = log
        self.cfg = cfg

    def playSound(self, wavFile: str, blocking: bool = False) -> PlayObject:
        """Play a wave file with optional blocking."""
        self.log.debug(f'Playing sound: {wavFile}')
        play = WaveObject.from_wave_file(self.cfg.dirSound + wavFile).play()  # pyright: ignore[reportUnknownMemberType]

        if blocking:
            play.wait_done()

        return play

    def initBgSound(self):
        """Begin Background Ambient Sound."""
        self.bgSoundThread = Thread(target=self._bgSoundLoop, daemon=True)
        self.bgSoundThread.start()

    def endBgSound(self):
        """End Background Ambient Sound."""
        self.bgSoundEnd.set()

        if self.bgSoundThread is not None:
            self.bgSoundThread.join()
            self.bgSoundThread = None

    def _bgSoundLoop(self):
        """Background Ambient Sound Thread Loop."""
        while not self.bgSoundEnd.is_set():
            # FIXME: Adjust Volume via cfg.bgSoundVolume
            play = WaveObject.from_wave_file(self.cfg.dirSound + self.cfg.bgSound).play()  # pyright: ignore[reportUnknownMemberType]

            while play.is_playing():
                if self.bgSoundEnd.is_set():
                    break

                time.sleep(0.05)
