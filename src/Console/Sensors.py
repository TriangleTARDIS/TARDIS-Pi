"""
TARDIS Console SFX Module - Sensors.

Copyright (C) 2017-2026 M Thompson.  All Rights Reserved.

Created 06-22-2017 by M Thompson (triangletardis@gmail.com)
Last modified 07-16-2026
"""

from pathlib import Path
import subprocess


def getTemperature() -> float:
    """Get CPU Temperature (Pi only)."""
    try:
        txt = Path('/sys/class/thermal/thermal_zone0/temp').read_text()
        return ((float(txt) / 1000) * 9 / 5) + 32
    except Exception:
        return 0.0


def getThrottleStatus() -> str:
    """Get Throttle Status (Pi only)."""
    try:
        VC_STATUS = {
            0: 'Under-volt',
            1: 'ARM freq capped',
            2: 'Throttled',
            3: 'Soft temp limit',
        }
        vctxt = (
            subprocess.run(
                ['vcgencmd', 'get_throttled'],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            )
            .stdout.decode('utf-8')
            .replace('throttled=0x', '')
            .strip()
        )
        vchex = int(vctxt, 16)

        stats: list[str] = []
        for bit, message in VC_STATUS.items():
            if vchex & (1 << bit):
                stats.append(message)

        if stats:
            return '<ALERT> ' + '; '.join(stats)
    except Exception:
        return 'N/A'

    return 'OK'
