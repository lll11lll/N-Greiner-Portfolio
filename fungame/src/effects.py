from __future__ import annotations

from dataclasses import dataclass

import pygame


@dataclass
class Particle:
    pos: pygame.Vector2
    vel: pygame.Vector2
    color: tuple[int, int, int]
    ttl: float
    size: float
    gravity: float = 0.0

    start_ttl: float = 0.0

    def __post_init__(self) -> None:
        self.start_ttl = self.ttl

    def update(self, dt: float) -> bool:
        self.ttl -= dt
        self.vel.y += self.gravity * dt
        self.pos += self.vel * dt
        return self.ttl > 0

    @property
    def alpha(self) -> int:
        if self.start_ttl <= 0:
            return 0
        return int(255 * max(0.0, min(1.0, self.ttl / self.start_ttl)))


@dataclass
class DamageNumber:
    text: str
    pos: pygame.Vector2
    color: tuple[int, int, int]
    ttl: float = 0.65

    start_ttl: float = 0.65

    def update(self, dt: float) -> bool:
        self.ttl -= dt
        self.pos.y -= 44 * dt
        return self.ttl > 0

    @property
    def alpha(self) -> int:
        return int(255 * max(0.0, self.ttl / self.start_ttl))
