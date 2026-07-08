from __future__ import annotations

import math
import random
from array import array

import pygame


class SoundBank:
    def __init__(self, enabled: bool = True) -> None:
        self.enabled = False
        self.sounds: dict[str, pygame.mixer.Sound] = {}
        if not enabled:
            return
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=256)
            self.sounds = {
                "shoot": self._tone(520, 0.045, 0.18),
                "pickup": self._tone(880, 0.06, 0.2),
                "hurt": self._tone(150, 0.09, 0.24),
                "level": self._tone(660, 0.16, 0.22, sweep=420),
                "boom": self._noise(0.18, 0.22),
            }
            self.enabled = True
        except pygame.error:
            self.enabled = False

    def play(self, name: str) -> None:
        if self.enabled and name in self.sounds:
            self.sounds[name].play()

    def _tone(self, freq: float, duration: float, volume: float, sweep: float = 0.0) -> pygame.mixer.Sound:
        rate = pygame.mixer.get_init()[0]
        count = int(rate * duration)
        samples = array("h")
        for i in range(count):
            t = i / rate
            env = 1.0 - i / max(1, count)
            current = freq + sweep * (i / max(1, count))
            value = math.sin(math.tau * current * t) * env * volume
            samples.append(int(value * 32767))
        sound = pygame.mixer.Sound(buffer=samples.tobytes())
        sound.set_volume(volume)
        return sound

    def _noise(self, duration: float, volume: float) -> pygame.mixer.Sound:
        rate = pygame.mixer.get_init()[0]
        count = int(rate * duration)
        samples = array("h")
        last = 0.0
        for i in range(count):
            env = (1.0 - i / max(1, count)) ** 1.8
            last = last * 0.6 + random.uniform(-1.0, 1.0) * 0.4
            samples.append(int(last * env * volume * 32767))
        sound = pygame.mixer.Sound(buffer=samples.tobytes())
        sound.set_volume(volume)
        return sound
