from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Any

import pygame

from .projectile import Projectile


ENEMY_TYPES: dict[str, dict[str, Any]] = {
    "crawler": {
        "name": "Scrap Crawler",
        "hp": 26,
        "speed": 74,
        "radius": 14,
        "contact": 11,
        "xp": 6,
        "score": 10,
        "sprite": "crawler",
    },
    "runner": {
        "name": "Spark Runner",
        "hp": 16,
        "speed": 146,
        "radius": 12,
        "contact": 9,
        "xp": 5,
        "score": 14,
        "sprite": "runner",
    },
    "brute": {
        "name": "Shield Brute",
        "hp": 98,
        "speed": 48,
        "radius": 22,
        "contact": 24,
        "xp": 18,
        "score": 38,
        "sprite": "brute",
    },
    "shooter": {
        "name": "Pulse Shooter",
        "hp": 44,
        "speed": 68,
        "radius": 17,
        "contact": 12,
        "xp": 13,
        "score": 28,
        "sprite": "shooter",
        "ranged": True,
    },
    "dash_scrapper": {
        "name": "Dash Scrapper",
        "hp": 32,
        "speed": 92,
        "radius": 15,
        "contact": 16,
        "xp": 9,
        "score": 22,
        "sprite": "enemy_dash_scrapper",
        "behavior": "dash",
    },
    "medium_bruiser": {
        "name": "Medium Bruiser",
        "hp": 150,
        "speed": 50,
        "radius": 24,
        "contact": 25,
        "xp": 22,
        "score": 46,
        "sprite": "enemy_medium_bruiser",
    },
    "shield_carrier": {
        "name": "Shield Carrier",
        "hp": 132,
        "speed": 45,
        "radius": 24,
        "contact": 23,
        "xp": 20,
        "score": 44,
        "sprite": "enemy_shield_carrier",
    },
    "mine_layer": {
        "name": "Mine Layer",
        "hp": 58,
        "speed": 62,
        "radius": 17,
        "contact": 11,
        "xp": 15,
        "score": 34,
        "sprite": "enemy_mine_layer",
        "behavior": "mine_layer",
        "ranged": True,
        "ideal_range": 255,
        "shoot_range": 520,
        "projectile_kind": "enemy_mine",
        "projectile_color": (255, 82, 82),
        "projectile_speed": 42,
        "projectile_damage": 16,
        "projectile_radius": 14,
        "fire_interval": (2.0, 3.0),
    },
    "drone_swarm": {
        "name": "Drone Swarm Unit",
        "hp": 13,
        "speed": 168,
        "radius": 11,
        "contact": 8,
        "xp": 4,
        "score": 12,
        "sprite": "enemy_drone_swarm_unit",
    },
    "artillery_buggy": {
        "name": "Artillery Buggy",
        "hp": 72,
        "speed": 42,
        "radius": 22,
        "contact": 12,
        "xp": 20,
        "score": 48,
        "sprite": "enemy_artillery_buggy",
        "behavior": "artillery",
        "ranged": True,
        "ideal_range": 430,
        "shoot_range": 720,
        "projectile_kind": "enemy_artillery_shell",
        "projectile_color": (255, 189, 69),
        "projectile_speed": 190,
        "projectile_damage": 18,
        "projectile_radius": 10,
        "fire_interval": (1.65, 2.45),
    },
    "repair_node": {
        "name": "Repair Node",
        "hp": 42,
        "speed": 46,
        "radius": 17,
        "contact": 8,
        "xp": 16,
        "score": 42,
        "sprite": "enemy_repair_node",
        "behavior": "support",
    },
    "fire_mote": {
        "name": "Fire Mote",
        "hp": 34,
        "speed": 108,
        "radius": 16,
        "contact": 18,
        "xp": 12,
        "score": 30,
        "sprite": "enemy_fire_mote",
    },
    "cryo_crawler": {
        "name": "Cryo Crawler",
        "hp": 52,
        "speed": 64,
        "radius": 18,
        "contact": 13,
        "xp": 14,
        "score": 32,
        "sprite": "enemy_cryo_crawler",
    },
    "poison_spitter": {
        "name": "Poison Spitter",
        "hp": 48,
        "speed": 66,
        "radius": 18,
        "contact": 10,
        "xp": 16,
        "score": 38,
        "sprite": "enemy_poison_spitter",
        "ranged": True,
        "ideal_range": 300,
        "shoot_range": 560,
        "projectile_kind": "enemy_poison_glob",
        "projectile_color": (109, 255, 128),
        "projectile_speed": 225,
        "projectile_damage": 12,
        "projectile_radius": 8,
        "fire_interval": (1.15, 1.75),
    },
    "lightning_node": {
        "name": "Lightning Node",
        "hp": 54,
        "speed": 58,
        "radius": 18,
        "contact": 13,
        "xp": 17,
        "score": 40,
        "sprite": "enemy_lightning_node",
        "ranged": True,
        "ideal_range": 280,
        "shoot_range": 540,
        "projectile_kind": "enemy_lightning_arc",
        "projectile_color": (55, 235, 255),
        "projectile_speed": 330,
        "projectile_damage": 11,
        "projectile_radius": 7,
        "fire_interval": (0.95, 1.45),
    },
    "boss": {
        "name": "Mini Boss",
        "hp": 680,
        "speed": 42,
        "radius": 36,
        "contact": 34,
        "xp": 95,
        "score": 280,
        "sprite": "boss",
        "boss": True,
    },
    "boss_rift_charger": {
        "name": "Rift Charger",
        "hp": 820,
        "speed": 48,
        "radius": 58,
        "contact": 42,
        "xp": 125,
        "score": 360,
        "sprite": "boss_rift_charger",
        "boss": True,
        "behavior": "boss_dash",
        "projectile_kind": "enemy_lightning_arc",
        "projectile_color": (255, 63, 191),
        "projectile_speed": 315,
        "projectile_damage": 13,
        "projectile_radius": 8,
    },
    "boss_furnace_king": {
        "name": "Furnace King",
        "hp": 900,
        "speed": 34,
        "radius": 60,
        "contact": 39,
        "xp": 135,
        "score": 390,
        "sprite": "boss_furnace_king",
        "boss": True,
        "behavior": "boss_fire",
        "projectile_kind": "enemy_artillery_shell",
        "projectile_color": (255, 189, 69),
        "projectile_speed": 230,
        "projectile_damage": 17,
        "projectile_radius": 10,
    },
    "boss_glacier_engine": {
        "name": "Glacier Engine",
        "hp": 940,
        "speed": 30,
        "radius": 61,
        "contact": 37,
        "xp": 140,
        "score": 400,
        "sprite": "boss_glacier_engine",
        "boss": True,
        "behavior": "boss_cryo",
        "projectile_kind": "enemy_cryo_bolt",
        "projectile_color": (55, 235, 255),
        "projectile_speed": 220,
        "projectile_damage": 14,
        "projectile_radius": 10,
    },
    "boss_toxic_maw": {
        "name": "Toxic Maw",
        "hp": 880,
        "speed": 36,
        "radius": 60,
        "contact": 38,
        "xp": 136,
        "score": 395,
        "sprite": "boss_toxic_maw",
        "boss": True,
        "behavior": "boss_poison",
        "projectile_kind": "enemy_poison_glob",
        "projectile_color": (109, 255, 128),
        "projectile_speed": 230,
        "projectile_damage": 15,
        "projectile_radius": 10,
    },
    "boss_storm_capacitor": {
        "name": "Storm Capacitor",
        "hp": 860,
        "speed": 38,
        "radius": 60,
        "contact": 38,
        "xp": 138,
        "score": 405,
        "sprite": "boss_storm_capacitor",
        "boss": True,
        "behavior": "boss_lightning",
        "projectile_kind": "enemy_lightning_arc",
        "projectile_color": (55, 235, 255),
        "projectile_speed": 350,
        "projectile_damage": 14,
        "projectile_radius": 8,
    },
    "boss_scrap_hive_core": {
        "name": "Scrap Hive Core",
        "hp": 920,
        "speed": 32,
        "radius": 62,
        "contact": 36,
        "xp": 150,
        "score": 420,
        "sprite": "boss_scrap_hive_core",
        "boss": True,
        "behavior": "boss_summoner",
        "projectile_kind": "enemy",
        "projectile_color": (255, 63, 191),
        "projectile_speed": 250,
        "projectile_damage": 12,
        "projectile_radius": 8,
    },
}


@dataclass
class Enemy:
    kind: str
    pos: pygame.Vector2
    max_health: float
    health: float
    speed: float
    radius: float
    contact_damage: float
    xp_value: int
    score_value: int
    sprite_key: str
    ranged: bool = False
    boss: bool = False
    elite: bool = False
    sprite_angle_offset: float = 0.0
    behavior: str = "chase"
    projectile_kind: str = "enemy"
    projectile_color: tuple[int, int, int] = (159, 91, 255)
    projectile_speed: float = 255.0
    projectile_damage: float = 10.0
    projectile_radius: float = 7.0
    ideal_range: float = 330.0
    shoot_range: float = 560.0
    fire_interval: tuple[float, float] = (1.0, 1.55)
    phase: float = field(default_factory=lambda: random.random() * math.tau)
    flash: float = 0.0
    fire_cooldown: float = field(default_factory=lambda: random.uniform(0.35, 1.4))
    radial_cooldown: float = 2.6
    summon_cooldown: float = 4.8
    dash_cooldown: float = field(default_factory=lambda: random.uniform(1.0, 2.2))
    dash_windup: float = 0.0
    dash_time: float = 0.0
    dash_direction: pygame.Vector2 = field(default_factory=pygame.Vector2)
    support_cooldown: float = field(default_factory=lambda: random.uniform(0.7, 1.5))
    contact_cooldown: float = 0.0
    shield_cooldown: float = 0.0
    slow_timer: float = 0.0
    slow_strength: float = 0.0
    poison_timer: float = 0.0
    poison_dps: float = 0.0
    poison_stacks: int = 0
    dot_family: str = ""
    corrosion_timer: float = 0.0
    corrosion_bonus: float = 0.0
    conductive_timer: float = 0.0
    knockback: pygame.Vector2 = field(default_factory=pygame.Vector2)

    def update(self, dt: float, player_pos: pygame.Vector2, game: object) -> None:
        self.flash = max(0.0, self.flash - dt)
        self.contact_cooldown = max(0.0, self.contact_cooldown - dt)
        self.shield_cooldown = max(0.0, self.shield_cooldown - dt)
        self.corrosion_timer = max(0.0, self.corrosion_timer - dt)
        self.conductive_timer = max(0.0, self.conductive_timer - dt)
        if self.poison_timer > 0:
            tick = min(dt, self.poison_timer)
            stacks = self.poison_stacks if self.dot_family == "Poison" else 1
            self.health -= self.poison_dps * stacks * (1.0 + self.corrosion_bonus) * tick
            self.poison_timer = max(0.0, self.poison_timer - dt)
            if self.poison_timer <= 0:
                self.poison_stacks = 0
        self.slow_timer = max(0.0, self.slow_timer - dt)
        to_player = player_pos - self.pos
        dist_sq = to_player.length_squared()
        direction = to_player.normalize() if dist_sq > 1 else pygame.Vector2()

        speed_scale = 1.0 - self.slow_strength if self.slow_timer > 0 else 1.0
        original_speed = self.speed
        self.speed *= max(0.35, speed_scale)
        if self.boss:
            self._update_boss(dt, direction, dist_sq, player_pos, game)
        elif self.behavior == "dash":
            self._update_dash(dt, direction, dist_sq, game)
        elif self.behavior == "mine_layer":
            self._update_mine_layer(dt, direction, dist_sq, player_pos, game)
        elif self.behavior == "support":
            self._update_support(dt, direction, dist_sq, game)
        elif self.ranged:
            self._update_shooter(dt, direction, dist_sq, player_pos, game)
        else:
            self.pos += direction * self.speed * dt
        self.speed = original_speed

        self.pos += self.knockback * dt
        self.knockback *= max(0.0, 1.0 - 8.0 * dt)

    def _update_dash(self, dt: float, direction: pygame.Vector2, dist_sq: float, game: object) -> None:
        if self.dash_time > 0:
            self.pos += self.dash_direction * self.speed * 3.35 * dt
            self.dash_time = max(0.0, self.dash_time - dt)
            return

        if self.dash_windup > 0:
            self.dash_windup = max(0.0, self.dash_windup - dt)
            if random.random() < 0.35:
                game.spawn_hit_particles(self.pos, (255, 63, 191))
            return

        self.pos += direction * self.speed * dt
        self.dash_cooldown -= dt
        if dist_sq < 520**2 and self.dash_cooldown <= 0 and direction.length_squared() > 0:
            self.dash_direction = direction.copy()
            self.dash_windup = 0.26
            self.dash_time = 0.24
            self.dash_cooldown = random.uniform(1.4, 2.35)

    def _update_mine_layer(
        self,
        dt: float,
        direction: pygame.Vector2,
        dist_sq: float,
        player_pos: pygame.Vector2,
        game: object,
    ) -> None:
        dist = dist_sq**0.5
        if dist < 210:
            move = -direction
        elif dist > self.ideal_range + 70:
            move = direction
        else:
            move = pygame.Vector2(-direction.y, direction.x) * math.sin(game.stats.time_survived * 1.7 + self.phase)
        self.pos += move * self.speed * dt

        self.fire_cooldown -= dt
        if dist < self.shoot_range and self.fire_cooldown <= 0:
            self.fire_cooldown = random.uniform(*self.fire_interval)
            self._shoot_at(
                player_pos,
                game,
                speed=self.projectile_speed,
                damage=self.projectile_damage,
                radius=self.projectile_radius,
                ttl=5.0,
            )

    def _update_support(self, dt: float, direction: pygame.Vector2, dist_sq: float, game: object) -> None:
        dist = dist_sq**0.5
        if dist < 240:
            self.pos -= direction * self.speed * 0.55 * dt
        else:
            self.pos += direction * self.speed * 0.35 * dt

        self.support_cooldown -= dt
        if self.support_cooldown > 0:
            return
        self.support_cooldown = random.uniform(1.2, 1.9)
        candidates = [
            enemy
            for enemy in game.enemies
            if enemy is not self
            and enemy.alive
            and not enemy.boss
            and enemy.health < enemy.max_health
            and (enemy.pos - self.pos).length_squared() <= 165**2
        ]
        if not candidates:
            return
        target = min(candidates, key=lambda enemy: enemy.health / max(1.0, enemy.max_health))
        heal = min(target.max_health - target.health, 12.0 + self.max_health * 0.04)
        if heal > 0:
            target.health += heal
            game.spawn_hit_particles(target.pos, (109, 255, 128))

    def _update_shooter(
        self,
        dt: float,
        direction: pygame.Vector2,
        dist_sq: float,
        player_pos: pygame.Vector2,
        game: object,
    ) -> None:
        ideal = self.ideal_range
        dist = dist_sq**0.5
        if dist > ideal + 55:
            move = direction
        elif dist < ideal - 75:
            move = -direction
        else:
            move = pygame.Vector2(-direction.y, direction.x) * math.sin(game.stats.time_survived + self.phase)
        self.pos += move * self.speed * dt

        self.fire_cooldown -= dt
        if dist < self.shoot_range and self.fire_cooldown <= 0:
            self.fire_cooldown = random.uniform(*self.fire_interval)
            self._shoot_at(
                player_pos,
                game,
                speed=self.projectile_speed,
                damage=self.projectile_damage,
                radius=self.projectile_radius,
            )

    def _update_boss(
        self,
        dt: float,
        direction: pygame.Vector2,
        dist_sq: float,
        player_pos: pygame.Vector2,
        game: object,
    ) -> None:
        dist = dist_sq**0.5
        if self.behavior == "boss_dash":
            if self.dash_time > 0:
                self.pos += self.dash_direction * self.speed * 3.0 * dt
                self.dash_time = max(0.0, self.dash_time - dt)
            elif self.dash_windup > 0:
                self.dash_windup = max(0.0, self.dash_windup - dt)
                if random.random() < 0.45:
                    game.spawn_hit_particles(self.pos, (255, 63, 191))
            else:
                self._boss_drift(dt, direction, dist)
                self.dash_cooldown -= dt
                if dist < 680 and self.dash_cooldown <= 0 and direction.length_squared() > 0:
                    self.dash_direction = direction.copy()
                    self.dash_windup = 0.45
                    self.dash_time = 0.34
                    self.dash_cooldown = random.uniform(2.7, 4.1)
        else:
            self._boss_drift(dt, direction, dist)

        self.fire_cooldown -= dt
        self.radial_cooldown -= dt
        self.summon_cooldown -= dt

        if self.fire_cooldown <= 0:
            self.fire_cooldown = 0.95 if self.behavior == "boss_lightning" else 1.15
            offsets = (-6, 6) if self.behavior == "boss_lightning" else (-12, 0, 12)
            for offset in offsets:
                d = direction.rotate(offset)
                game.add_projectile(
                    self._enemy_projectile(
                        d,
                        self.projectile_speed,
                        self.projectile_damage,
                        self.projectile_radius,
                    )
                )

        if self.radial_cooldown <= 0:
            self.radial_cooldown = 2.75 if self.behavior == "boss_fire" else 3.1
            count = 16 if self.behavior in ("boss_fire", "boss_lightning") else 12
            start = random.random() * 30
            for i in range(count):
                angle = math.radians(start + i * (360 / count))
                d = pygame.Vector2(math.cos(angle), math.sin(angle))
                game.add_projectile(
                    self._enemy_projectile(
                        d,
                        max(170, self.projectile_speed * 0.78),
                        max(8, self.projectile_damage * 0.72),
                        self.projectile_radius,
                        ttl=4.0,
                    )
                )
            game.add_screen_shake(5.0, source_type="boss_attack")

        should_summon = self.kind == "boss" or self.behavior == "boss_summoner"
        if should_summon and self.summon_cooldown <= 0 and len(game.enemies) < game.max_enemies:
            self.summon_cooldown = 5.6
            summon_kinds = ("crawler", "runner")
            summon_count = 4
            if self.behavior == "boss_summoner":
                summon_kinds = ("drone_swarm", "drone_swarm", "repair_node")
                summon_count = 5
            for i in range(summon_count):
                angle = math.radians(i * (360 / summon_count) + random.uniform(-16, 16))
                offset = pygame.Vector2(math.cos(angle), math.sin(angle)) * random.randint(58, 90)
                game.spawn_enemy(random.choice(summon_kinds), self.pos + offset, summoned=True)

    def _boss_drift(self, dt: float, direction: pygame.Vector2, dist: float) -> None:
        if dist > 180:
            self.pos += direction * self.speed * dt
        else:
            strafe = pygame.Vector2(-direction.y, direction.x)
            self.pos += strafe * self.speed * 0.75 * dt

    def _shoot_at(
        self,
        player_pos: pygame.Vector2,
        game: object,
        speed: float,
        damage: float,
        radius: float,
        ttl: float = 3.5,
    ) -> None:
        direction = player_pos - self.pos
        if direction.length_squared() == 0:
            direction = pygame.Vector2(1, 0)
        else:
            direction = direction.normalize()
        game.add_projectile(self._enemy_projectile(direction, speed, damage, radius, ttl=ttl))

    def _enemy_projectile(
        self,
        direction: pygame.Vector2,
        speed: float,
        damage: float,
        radius: float,
        ttl: float = 3.5,
    ) -> Projectile:
        if direction.length_squared() == 0:
            direction = pygame.Vector2(1, 0)
        else:
            direction = direction.normalize()
        return Projectile(
            pos=self.pos + direction * (self.radius + 8),
            vel=direction * speed,
            radius=radius,
            damage=damage,
            source="enemy",
            ttl=ttl,
            kind=self.projectile_kind,
            color=self.projectile_color,
        )

    def take_damage(self, amount: float, knockback: pygame.Vector2 | None = None) -> None:
        if self.corrosion_timer > 0:
            amount *= 1.0 + self.corrosion_bonus
        self.health -= amount
        self.flash = 0.08
        if knockback is not None:
            self.knockback += knockback

    def apply_slow(self, duration: float, strength: float) -> None:
        self.slow_timer = max(self.slow_timer, duration)
        self.slow_strength = max(self.slow_strength, min(0.65, strength))

    def apply_poison(self, dps: float, duration: float, family: str = "Poison") -> None:
        same_toxin = family == "Poison" and self.dot_family == "Poison" and self.poison_timer > 0
        if same_toxin:
            self.poison_stacks = min(3, self.poison_stacks + 1)
            self.poison_dps = max(self.poison_dps, dps)
            self.poison_timer = min(6.5, max(self.poison_timer, duration) + 0.18)
        else:
            self.dot_family = family
            self.poison_dps = dps
            self.poison_timer = duration
            self.poison_stacks = 1
        if family == "Poison":
            # Baseline corrosion makes poison useful against durable targets;
            # Corrosion Rounds can still deepen this debuff further. Keeping
            # conductivity here also makes Plague Network spread feed lightning.
            self.apply_corrosion(1, duration=self.poison_timer)
            self.apply_conductive(max(3.6, min(5.0, self.poison_timer)))

    def apply_corrosion(self, level: int, duration: float = 2.2) -> None:
        self.corrosion_bonus = max(self.corrosion_bonus, min(0.32, 0.08 * level))
        self.corrosion_timer = max(self.corrosion_timer, duration)

    def apply_conductive(self, duration: float) -> None:
        self.conductive_timer = max(self.conductive_timer, duration)

    @property
    def name(self) -> str:
        return str(ENEMY_TYPES.get(self.kind, {}).get("name", self.kind))

    @property
    def alive(self) -> bool:
        return self.health > 0


def create_enemy(kind: str, pos: pygame.Vector2, health_mult: float = 1.0, speed_mult: float = 1.0, elite: bool = False) -> Enemy:
    data = ENEMY_TYPES[kind]
    elite_health = 2.15 if elite else 1.0
    max_health = float(data["hp"]) * health_mult * elite_health
    fire_interval = tuple(data.get("fire_interval", (1.0, 1.55)))
    return Enemy(
        kind=kind,
        pos=pygame.Vector2(pos),
        max_health=max_health,
        health=max_health,
        speed=float(data["speed"]) * speed_mult * (1.08 if elite else 1.0),
        radius=float(data["radius"]) * (1.2 if elite else 1.0),
        contact_damage=float(data["contact"]) * (1.25 if elite else 1.0),
        xp_value=int(data["xp"]) * (3 if elite else 1),
        score_value=int(data["score"]) * (3 if elite else 1),
        sprite_key=str(data["sprite"]),
        ranged=bool(data.get("ranged", False)),
        boss=bool(data.get("boss", False)),
        elite=elite,
        # Source enemy sheets are drawn facing up; the dash unit is the only
        # diagonal exception. Keeping this metadata in one place avoids per-draw hacks.
        sprite_angle_offset=float(data.get("sprite_angle_offset", 45.0 if kind == "dash_scrapper" else 90.0)),
        behavior=str(data.get("behavior", "chase")),
        projectile_kind=str(data.get("projectile_kind", "enemy")),
        projectile_color=tuple(data.get("projectile_color", (159, 91, 255))),
        projectile_speed=float(data.get("projectile_speed", 255)),
        projectile_damage=float(data.get("projectile_damage", 10)),
        projectile_radius=float(data.get("projectile_radius", 7)),
        ideal_range=float(data.get("ideal_range", 330)),
        shoot_range=float(data.get("shoot_range", 560)),
        fire_interval=(float(fire_interval[0]), float(fire_interval[1])),
        fire_cooldown=random.uniform(float(fire_interval[0]), float(fire_interval[1])),
    )
