from __future__ import annotations

from dataclasses import dataclass

import pygame

from .projectile import Projectile


@dataclass
class MiniTurret:
    pos: pygame.Vector2
    ttl: float = 9.0
    cooldown: float = 0.15
    fire_rate: float = 1.45
    range: float = 360.0
    damage: float = 8.0
    bullet_speed: float = 500.0
    radius: float = 12.0
    range_bonus: float = 0.0

    def update(self, dt: float, game: object) -> bool:
        self.ttl -= dt
        self.cooldown -= dt
        if self.cooldown <= 0:
            target = self._find_target(game)
            if target is not None:
                direction = target.pos - self.pos
                if direction.length_squared() > 0:
                    direction = direction.normalize()
                    chain = 1 if "turret_lightning" in getattr(game.player, "equipped_effects", set()) else 0
                    if getattr(game.player, "capacitor_link_level", 0) > 0:
                        chain = max(chain, 1)
                    if chain and "Lightning:6" in getattr(game.player, "family_passives_unlocked", set()):
                        chain += 1
                    game.add_projectile(
                        Projectile(
                            pos=self.pos + direction * 12,
                            vel=direction * self.bullet_speed,
                            radius=4,
                            damage=self.damage,
                            source="player",
                            ttl=self.range / self.bullet_speed,
                            pierce=0,
                            kind="turret",
                            color=(109, 255, 128),
                            chain=chain,
                            knockback=35,
                        )
                    )
                    game.spawn_muzzle_particles(self.pos + direction * 12, direction)
            self.cooldown += 1.0 / self.fire_rate
        return self.ttl > 0

    def _find_target(self, game: object) -> object | None:
        candidates = [
            enemy
            for enemy in game.enemies
            if enemy.alive and (enemy.pos - self.pos).length_squared() <= (self.range + self.range_bonus) ** 2
        ]
        if not candidates:
            return None
        prefer_elites = getattr(game.player, "upgrade_counts", {}).get("targeting_ai", 0) > 0 or "drone_network" in getattr(
            game.player, "evolutions", set()
        )
        if prefer_elites:
            return min(candidates, key=lambda enemy: (0 if enemy.boss or enemy.kind in ("brute", "shooter") else 1, (enemy.pos - self.pos).length_squared()))
        return min(candidates, key=lambda enemy: (enemy.pos - self.pos).length_squared())


@dataclass
class Mine:
    pos: pygame.Vector2
    radius: float = 18.0
    damage: float = 45.0
    ttl: float = 18.0
    armed: float = 0.35

    def update(self, dt: float, game: object) -> bool:
        self.ttl -= dt
        self.armed = max(0.0, self.armed - dt)
        if self.armed > 0:
            return self.ttl > 0
        for enemy in game.enemies:
            if enemy.alive and (enemy.pos - self.pos).length_squared() <= (enemy.radius + self.radius) ** 2:
                game.explode_mine(self)
                return False
        return self.ttl > 0
