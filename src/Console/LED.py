"""
TARDIS Console SFX Module - LED.

Copyright (C) 2017-2026 M Thompson.  All Rights Reserved.

Created 06-22-2017 by M Thompson (triangletardis@gmail.com)
Last modified 07-16-2026
"""

import logging
import copy
import math
import time
from typing import Any
import pigpio
from dataclasses import dataclass

from Console.Config import ConsoleConfig, EffectConfig
from Console.Terminal import ManagerTerminal
from Console.Sound import ManagerSound


@dataclass
class LevelRGBW:
    """RGB/White Level Struct, default to None More Black"""

    R: int = 0
    G: int = 0
    B: int = 0
    W: int = 0

    @staticmethod
    def keys():
        return {f.name for f in LevelRGBW.__dataclass_fields__.values()}

    @staticmethod
    def keysNoWhite():
        return {f.name for f in LevelRGBW.__dataclass_fields__.values() if f.name != 'W'}

    @staticmethod
    def __len__():
        return len(LevelRGBW.keys())

    def __getitem__(self, key: str):
        return getattr(self, key)

    def __setitem__(self, key: str, value: int):
        setattr(self, key, value)

    def __iter__(self):
        return iter(self.keys())

    def __str__(self):
        return f'[{self.R:3g}, {self.G:3g}, {self.B:3g}, {self.W:3g}]'

    def dict(self):
        return {f.name: getattr(self, f.name) for f in self.__dataclass_fields__.values()}


#
# LED Manager — encapsulates GPIO, PWM, color correction, patterns, and effects.
#
class ManagerLED:
    """Console LED Manager - LED Color Control/Patterns with correction via GPIO PWM."""

    cfg: ConsoleConfig
    log: logging.Logger
    sound: ManagerSound | None
    terminal: ManagerTerminal | None
    piGPIO: Any | None
    levelIn: LevelRGBW
    levelOut: LevelRGBW

    def __init__(self, cfg: ConsoleConfig, log: logging.Logger, sound: ManagerSound | None, terminal: ManagerTerminal | None):
        self.cfg = cfg
        self.log = log
        self.sound = sound
        self.terminal = terminal
        self.levelIn = LevelRGBW()
        self.levelOut = LevelRGBW()

    @staticmethod
    def sinebow(n: float) -> LevelRGBW:
        """RGB Sinebow.
        http://basecase.org/env/on-rainbows"""
        n += 1 / 2
        n *= -1
        r = math.sin(math.pi * n)
        g = math.sin(math.pi * (n + 1 / 3))
        b = math.sin(math.pi * (n + 2 / 3))
        w = 0
        return LevelRGBW(R=int(255 * r**2), G=int(255 * g**2), B=int(255 * b**2), W=w)

    @staticmethod
    def random(n: float) -> LevelRGBW:
        """RGB nthcolor Sequence (Random Phi).
        http://basecase.org/env/on-rainbows"""
        phi = (1 + 5**0.5) / 2
        return ManagerLED.sinebow(n * phi)

    @staticmethod
    def gammaShift(lvl: int, pwmStep: int, gamma: float) -> int:
        """Gamma Shift a PWM level."""
        return int(pow(float(lvl) / float(pwmStep), gamma) * pwmStep)

    @staticmethod
    def rgbToHex(rgbL: LevelRGBW, pwmStep: int) -> str:
        """Convert RGB value to hex string (ignore white)."""
        rgb = tuple((rgbL['R'], rgbL['G'], rgbL['B']))
        rgbn = tuple(int(c / pwmStep * 255) for c in rgb)
        return '#%02x%02x%02x' % rgbn

    @staticmethod
    def hexToRGB(hexStr: str) -> LevelRGBW:
        """Convert RGB Hex string to RGBW Level (zero white)."""
        r, g, b = tuple(c for c in bytes.fromhex(hexStr[1:]))
        return LevelRGBW(R=r, G=g, B=b, W=0)

    @staticmethod
    def colorFade(pattern: list[str], n: int, fadeStep: int) -> LevelRGBW:
        """Return RGBW (zero white) used to color fade from one color to the next in pattern."""
        j = int(n / fadeStep % len(pattern))
        s = n % fadeStep
        c1 = ManagerLED.hexToRGB(pattern[j])
        c2 = ManagerLED.hexToRGB(pattern[(j + 1) % len(pattern)])
        (r, g, b) = (int((c2[k] - c1[k]) / fadeStep * s) + c1[k] for k in LevelRGBW.keysNoWhite())
        return LevelRGBW(R=r, G=g, B=b, W=0)

    def initGPIO(self):
        """Init GPIO (over network)."""
        self.piGPIO = pigpio.pi(host=self.cfg.hostName)  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]

    def fullBright(self, lvl: int = 1):
        """Reset LEDs to full bright (or dark)."""
        self.log.debug(f'Full Bright: {lvl}')

        for n, pin in self.cfg.bcmPin.model_dump().items():
            if pin is not None and pin > 0:
                self.levelIn[n] = self.cfg.pwm.step * lvl
                self.levelOut[n] = self.levelIn[n]

                if self.piGPIO is not None:
                    self.piGPIO.write(pin, 1 - lvl)

    def colorCorrect(self, colorOrig: LevelRGBW, adjustGamma: bool = True, adjustWBalance: bool = True, adjustWMix: bool = True, adjustMin: bool = True) -> LevelRGBW:
        """Correct Colors to get to LED RGBW values.

        Optional - Gamma Correction.
        Optional - White Balance - Adjust RGB for calibrated levels due to human eye sensitivity.
        Optional - Mix White channel in place of lowest RGB channel.
        Optional - Scale for minimum forward voltage for each LED channel.
        Safely clamp each channel to between 0 and pwm.step."""
        colorCorrected: LevelRGBW = copy.copy(colorOrig)

        for k in colorCorrected.keys():
            if k != 'W':
                # Gamma
                if adjustGamma:
                    colorCorrected[k] = ManagerLED.gammaShift(colorCorrected[k], self.cfg.pwm.step, self.cfg.gamma)

                # White Balance - Color Mix
                if adjustWBalance:
                    colorCorrected[k] = colorCorrected[k] * self.cfg.mix.model_dump()[k]

        if adjustWMix and self.cfg.mix.model_dump()['W'] > 0:
            # Mix White
            rgbCopy = {k: colorCorrected[k] for k in LevelRGBW.keysNoWhite()}
            minRgbKey = min(rgbCopy, key=lambda k: rgbCopy[k])
            colorCorrected['W'] = rgbCopy[minRgbKey] * self.cfg.mix.model_dump()['W']
            colorCorrected[minRgbKey] = rgbCopy[minRgbKey] * (1 - self.cfg.mix.model_dump()['W'])

        for k in colorCorrected.keys():
            # Scale for Minimum Forward Voltage
            if adjustMin:
                minl = self.cfg.min.model_dump()[k]
                maxl = self.cfg.pwm.step
                colorCorrected[k] = minl + ((colorCorrected[k] / maxl) * (maxl - minl))

            # Clamp
            colorCorrected[k] = int(min(self.cfg.pwm.step, max(0, colorCorrected[k])))

        return colorCorrected

    def colorPattern(self, effect: EffectConfig, n: int) -> LevelRGBW:
        """Return RGBW (zero white) used for the Nth step of the named effect/pattern."""
        name = effect.pattern
        fade = effect.fade

        if name == 'sinebow':
            return self.sinebow(n / self.cfg.pwm.step)

        if name == 'random':
            return self.random(n)

        p: list[str] = self.cfg.patterns[name]
        return ManagerLED.colorFade(p, n, self.cfg.fadeStep) if fade else ManagerLED.hexToRGB(p[n % len(p)])

    def beginPWM(self):
        """Begin PWM."""
        if self.terminal is not None:
            self.terminal.statusPrint(2, '--- Scanning ---')
            self.terminal.statusPrint(3, 'Begin PWM.')

        for pin in self.cfg.bcmPin.model_dump().values():
            if pin is not None and pin > 0:
                if self.piGPIO is not None:
                    self.piGPIO.set_PWM_frequency(pin, self.cfg.pwm.Hz)
                    self.piGPIO.set_PWM_range(pin, self.cfg.pwm.step)

    def endPWM(self):
        """End PWM."""
        if self.terminal is not None:
            self.terminal.statusPrint(2, '--- Complete ---')
            self.terminal.statusPrint(3, 'End PWM.')

        self.levelIn = LevelRGBW(R=self.cfg.pwm.step, G=self.cfg.pwm.step, B=self.cfg.pwm.step, W=self.cfg.pwm.step)
        self.levelOut = self.levelIn
        self.setPwmRgbw(self.levelIn)

    def setPwmRgbw(
        self,
        colors: LevelRGBW,
        adjustGamma: bool = True,
        adjustWBalance: bool = True,
        adjustWMix: bool = True,
        adjustMin: bool = True,
    ) -> LevelRGBW:
        """Set PWM Duty Cycle for RGBW channels (with optional color corrections)."""
        self.levelIn = colors
        self.levelOut = self.levelIn

        if adjustGamma or adjustWBalance or adjustWMix or adjustMin:
            self.levelOut = self.colorCorrect(
                self.levelIn,
                adjustGamma=adjustGamma,
                adjustWBalance=adjustWBalance,
                adjustWMix=adjustWMix,
                adjustMin=adjustMin,
            )

        for pinName, pin in self.cfg.bcmPin.model_dump().items():
            if pin is not None and pin > 0:
                # Set duty cycle (inverted)
                self.levelOut[pinName] = self.levelOut[pinName]
                if self.piGPIO is not None:
                    self.piGPIO.set_PWM_dutycycle(pin, self.cfg.pwm.step - self.levelOut[pinName])

        return self.levelOut

    def effectPulseRGB(self, snd: str, name: str = 'sinebow'):
        """Pulse Lights RGB effect."""
        if self.sound is not None and self.terminal is not None:
            self.terminal.conPrint('Effect - PulseRGB: {} - {}'.format(name, snd))
            self.beginPWM()
            play = self.sound.playSound(snd)

            effect = self.cfg.effects[name]
            slow = effect.slow / self.cfg.fadeStep if effect.fade else effect.slow
            pwmSleep = self.cfg.pwm.pwmSleepDefault * slow
            i = 0

            while play.is_playing():
                if self.terminal.shouldStopEffect():
                    self.terminal.conPrint('>>> Effect stopped!')
                    play.stop()
                    return

                self.levelIn = self.colorPattern(effect, i)
                self.terminal.statusPrint(
                    4,
                    'LevelI: {} {:3g} - [{R:3g}, {G:3g}, {B:3g}, {W:3g}]'.format(self.terminal.spin(i, 1), i, **self.levelIn),
                )
                self.setPwmRgbw(self.levelIn)
                self.terminal.statusPrint(
                    5,
                    'LevelO: {} {:3g} - [{R:3g}, {G:3g}, {B:3g}, {W:3g}]'.format(self.terminal.spin(i, 1), i, **self.levelOut),
                )

                time.sleep(pwmSleep)
                i = i + 1

            self.endPWM()
            self.terminal.conPrint('All Stop')

    def effectPulse(self, snd: str, pwmSleep: float | None = None):
        """Pulse Lights / Dematerialise effect."""
        if pwmSleep is None:
            pwmSleep = self.cfg.pwm.pwmSleepDefault

        if self.sound is not None and self.terminal is not None:
            self.terminal.conPrint('Effect - Pulse: ' + snd)
            self.beginPWM()
            play = self.sound.playSound(snd)

            i = 0
            while play.is_playing():
                if self.terminal.shouldStopEffect():
                    self.terminal.conPrint('>>> Effect stopped!')
                    play.stop()
                    return

                lvl = int(self.cfg.pwm.step * 0.5 * ((math.cos((i / self.cfg.pwm.step) * 2 * math.pi)) + 1))
                self.levelIn = LevelRGBW(R=lvl, G=lvl, B=lvl, W=lvl)
                self.terminal.statusPrint(4, 'Level : {} {:6g} of {:6g}'.format(self.terminal.spin(i, 1), lvl, self.cfg.pwm.step))
                self.setPwmRgbw(self.levelIn, adjustWBalance=False, adjustWMix=False)
                self.terminal.statusPrint(
                    5,
                    'LevelO: {} {:3g} - [{R:3g}, {G:3g}, {B:3g}, {W:3g}]'.format(self.terminal.spin(i, 1), i, **self.levelOut),
                )

                time.sleep(pwmSleep)
                i = i + 1

            self.endPWM()
            self.terminal.conPrint('All Stop')

    def effectBlink(self, snd: str):
        """Blink Lights / Door Lock effect."""
        if self.sound is not None and self.terminal is not None:
            self.terminal.conPrint('Effect - Blink: ' + snd)
            self.beginPWM()
            play = self.sound.playSound(snd)

            for lvl in [1.0, 0.0, 0.25, 1.0, 0.0, 0.25, 1.0]:
                if self.terminal.shouldStopEffect():
                    self.terminal.conPrint('>>> Effect stopped!')
                    play.stop()
                    return

                lvl *= self.cfg.pwm.step
                flatLvl = int(lvl)
                self.levelIn = LevelRGBW(R=flatLvl, G=flatLvl, B=flatLvl, W=flatLvl)
                self.terminal.statusPrint(4, f'Level: {lvl:6g} of {self.cfg.pwm.step:6g}')
                self.setPwmRgbw(self.levelIn, adjustWBalance=False, adjustWMix=False)
                self.terminal.statusPrint(5, f'LevelO: {self.levelOut}')

                time.sleep(0.1)

            self.endPWM()
            self.terminal.conPrint('Locked')
