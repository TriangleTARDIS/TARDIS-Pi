#!/usr/bin/python3
#
# TARDIS SFX module - Sound Manager.
#
# Copyright (C) 2017-2026 Michael Thompson.  All Rights Reserved.
#
# Created 06-22-2017 by Michael Thompson(triangletardis@gmail.com)
# Last modified 07-14-2026
#

import simpleaudio
import threading
import time


#
# Sound Manager — encapsulates all audio playback and background ambient sound.
#
class SoundManager:
    def __init__(self, cfg):
        self._cfg = cfg
        self._bgSoundThread: threading.Thread = None
        self._bgSoundEnd: threading.Event = None

    #
    # Play a wave file with optional blocking.
    #
    def playSound(self, f: str, blocking: bool = False) -> simpleaudio.PlayObject:
        play = simpleaudio.WaveObject.from_wave_file(self._cfg.dirSound + f).play()

        if blocking:
            play.wait_done()

        return play

    #
    # Begin Background Ambient Sound.
    #
    def initBgSound(self):
        self._bgSoundEnd = threading.Event()
        self._bgSoundThread = threading.Thread(target=self._bgSoundLoop, daemon=True)
        self._bgSoundThread.start()

    #
    # End Background Ambient Sound.
    #
    def endBgSound(self):
        if self._bgSoundEnd is not None:
            self._bgSoundEnd.set()

        if self._bgSoundThread is not None:
            self._bgSoundThread.join()
            self._bgSoundThread = None

    #
    # Background Ambient Sound Thread Loop.
    #
    def _bgSoundLoop(self):
        while not self._bgSoundEnd.is_set():
            #FIXME: Adjust Volume via self._cfg.bgSoundVolume
            play = simpleaudio.WaveObject.from_wave_file(self._cfg.dirSound + self._cfg.bgSound).play()

            while play.is_playing():
                if self._bgSoundEnd.is_set():
                    break
                time.sleep(0.05)
