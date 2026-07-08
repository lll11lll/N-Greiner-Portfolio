from __future__ import annotations

from dataclasses import dataclass, field

import pygame


@dataclass
class Projectile:
    pos: pygame.Vector2
    vel: pygame.Vector2
    radius: float
    damage: float
    source: str
    ttl: float
    pierce: int = 0
    kind: str = "slug"
    color: tuple[int, int, int] = (55, 235, 255)
    explosion_radius: float = 0.0
    split: int = 0
    chain: int = 0
    knockback: float = 0.0
    bounces: int = 0
    crit: bool = False
    slow_chance: float = 0.0
    slow_duration: float = 0.0
    poison_dps: float = 0.0
    poison_duration: float = 0.0
    dot_family: str = ""
    freeze_burst_radius: float = 0.0
    serrated_bonus: float = 0.0
    volatile_chance: float = 0.0
    corrosion_level: int = 0
    distance_traveled: float = 0.0
    hits: set[int] = field(default_factory=set)

    def update(self, dt: float) -> None:
        step = self.vel * dt
        self.pos += step
        self.distance_traveled += step.length()
        self.ttl -= dt

    @property
    def alive(self) -> bool:
        return self.ttl > 0 and self.damage > 0

    @property
    def direction(self) -> pygame.Vector2:
        if self.vel.length_squared() == 0:
            return pygame.Vector2(1, 0)
        return self.vel.normalize()
