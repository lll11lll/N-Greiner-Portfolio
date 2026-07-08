from __future__ import annotations

from dataclasses import dataclass, field

import pygame


@dataclass
class Pickup:
    kind: str
    pos: pygame.Vector2
    amount: int
    radius: float = 10.0
    age: float = 0.0
    vel: pygame.Vector2 = field(default_factory=pygame.Vector2)

    def update(self, dt: float, player_pos: pygame.Vector2, magnet_radius: float) -> bool:
        self.age += dt
        to_player = player_pos - self.pos
        dist_sq = to_player.length_squared()
        if dist_sq < magnet_radius * magnet_radius and dist_sq > 1:
            dist = dist_sq**0.5
            pull = (1.0 - min(1.0, dist / magnet_radius)) * 980.0
            self.vel += to_player / dist * pull * dt
        self.vel *= max(0.0, 1.0 - 5.2 * dt)
        self.pos += self.vel * dt
        return dist_sq < (self.radius + 16) ** 2
