"""
TARDIS Console SFX Module - Configuration.

Copyright (C) 2017-2026 M Thompson.  All Rights Reserved.

Created 06-22-2017 by M Thompson (triangletardis@gmail.com)
Last modified 07-16-2026
"""

from typing import Dict, List
from pydantic import BaseModel, model_validator


class PwmConfig(BaseModel):
    Hz: int
    step: int
    pwmSleepDefault: float = 0.0

    @model_validator(mode='after')
    def calcSleep(self) -> 'PwmConfig':
        self.pwmSleepDefault = 1 / self.step
        return self


class RGBWIntConfig(BaseModel):
    R: int
    G: int
    B: int
    W: int


class RGBWFloatConfig(BaseModel):
    R: float
    G: float
    B: float
    W: float


class EffectConfig(BaseModel):
    slow: int
    pattern: str
    fade: bool


class i2cConfig(BaseModel):
    bus: int
    address: str


class ConsoleConfig(BaseModel):
    __description__: str
    __version__: str
    debug: bool
    hostName: str
    autoPilot: bool
    devName: str
    i2cLCD: i2cConfig
    dirSound: str
    bgSound: str
    bgSoundVolume: float
    spin: List[str]
    loopSleep: float
    loopRandMin: int
    loopRandMax: int
    pwm: PwmConfig
    fadeStep: int
    bcmPin: RGBWIntConfig
    gamma: float
    mix: RGBWFloatConfig
    min: RGBWIntConfig
    patterns: Dict[str, List[str]]
    effects: Dict[str, EffectConfig]
