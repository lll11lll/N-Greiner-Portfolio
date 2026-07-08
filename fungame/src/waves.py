from __future__ import annotations

import random

import pygame

from .constants import SCREEN_HEIGHT, SCREEN_WIDTH


class WaveDirector:
    def __init__(self) -> None:
        self.spawn_cooldown = 0.35
        self.next_boss_time = 300.0
        self.next_elite_time = 150.0
        self.next_surge_time = 110.0
        self.surge_active_until = 0.0

    def update(self, dt: float, game: object) -> None:
        now = game.stats.time_survived
        self._current_pool = game.stage.enemy_pool
        if self.surge_active_until > 0 and now >= self.surge_active_until:
            self.surge_active_until = 0.0
            game.complete_salvage_surge()
        elif self.surge_active_until <= 0 and now >= self.next_surge_time:
            self.surge_active_until = now + 18.0
            self.next_surge_time = now + 108.0
            game.begin_salvage_surge()
        if now >= self.next_boss_time:
            self.next_boss_time += max(145.0, 180.0 - now * 0.06)
            boss_pool = game.stage.boss_pool or (game.stage.boss,)
            game.spawn_enemy(random.choice(boss_pool), self.spawn_position(game, extra_distance=180), boss_spawn=True)
        if now >= self.next_elite_time:
            self.next_elite_time += 88.0 if now < 300 else 70.0
            elite_pool = [kind for kind in ("brute", "dash_scrapper", "shooter", "repair_node", "cryo_crawler", "poison_spitter", "lightning_node") if kind in self._current_pool]
            if elite_pool:
                elemental = ""
                if game.is_content_unlocked("elemental_elites") and random.random() < 0.48:
                    elemental = random.choice(("Fire", "Cryo", "Lightning", "Poison"))
                game.spawn_enemy(random.choice(elite_pool), self.spawn_position(game, extra_distance=95), elite=True, elemental_affinity=elemental)

        if len(game.enemies) >= game.max_enemies:
            return

        self.spawn_cooldown -= dt
        if self.spawn_cooldown > 0:
            return

        minute = int(now // 60)
        interval = (1.10, 0.86, 0.70, 0.58, 0.46)[min(minute, 4)] if now < 300 else max(0.16, 0.44 - (now - 300) * 0.0007)
        self.spawn_cooldown = interval * random.uniform(0.55, 1.05)
        pack = 1 + int(now // 70)
        if self.surge_active_until > now:
            if getattr(game.player, "surge_stabilizer_active", False):
                self.spawn_cooldown *= 0.84
            else:
                self.spawn_cooldown *= 0.72
                pack += 1
        if random.random() < min(0.68, now / 230):
            pack += 1
        if now > 180 and random.random() < 0.28:
            pack += 1
        if 50 <= now <= 90:
            pack = min(pack, 2)

        for _ in range(min(pack, game.max_enemies - len(game.enemies))):
            game.spawn_enemy(self.choose_enemy_type(now, game), self.spawn_position(game))

    def choose_enemy_type(self, now: float, game: object | None = None) -> str:
        allowed = set(getattr(self, "_current_pool", ("crawler", "runner", "brute", "shooter")))
        choices: list[tuple[str, float]] = [("crawler", 1.0)]
        if now > 10 and "drone_swarm" in allowed:
            choices.append(("drone_swarm", 0.55 + min(0.35, now / 300)))
        if now > 18 and "runner" in allowed:
            choices.append(("runner", 0.55 + min(0.6, now / 260)))
        if now > 26 and "dash_scrapper" in allowed:
            choices.append(("dash_scrapper", 0.36 + min(0.4, now / 330)))
        if now > 42 and "brute" in allowed:
            choices.append(("brute", 0.32 + min(0.45, now / 360)))
        if now > 48 and "medium_bruiser" in allowed:
            choices.append(("medium_bruiser", 0.28 + min(0.34, now / 420)))
        if now > 58 and "shield_carrier" in allowed:
            choices.append(("shield_carrier", 0.24 + min(0.3, now / 460)))
        if (now > 120 or (game is not None and getattr(game, "urban_crossfire_active", False) and now > 42)) and "shooter" in allowed:
            choices.append(("shooter", 0.28 + min(0.42, now / 420)))
        if now > 180 and "mine_layer" in allowed:
            choices.append(("mine_layer", 0.2 + min(0.24, now / 520)))
        if now > 180 and "repair_node" in allowed:
            choices.append(("repair_node", 0.16 + min(0.16, now / 620)))
        if (now > 180 or (game is not None and getattr(game, "urban_crossfire_active", False) and now > 76)) and "artillery_buggy" in allowed:
            choices.append(("artillery_buggy", 0.16 + min(0.22, now / 540)))
        if now > 300 and "fire_mote" in allowed:
            choices.append(("fire_mote", 0.32 + min(0.25, now / 420)))
        if now > 300 and "cryo_crawler" in allowed:
            choices.append(("cryo_crawler", 0.3 + min(0.24, now / 460)))
        if now > 300 and "poison_spitter" in allowed:
            choices.append(("poison_spitter", 0.18 + min(0.2, now / 560)))
        if now > 300 and "lightning_node" in allowed:
            choices.append(("lightning_node", 0.18 + min(0.2, now / 560)))
        if game is not None and getattr(game, "charged_wreckage_active", False) and now > 60 and "lightning_node" in allowed:
            choices.append(("lightning_node", 0.42))
        total = sum(weight for _, weight in choices)
        roll = random.random() * total
        acc = 0.0
        for kind, weight in choices:
            acc += weight
            if roll <= acc:
                return kind
        return "crawler"

    def scaling(self, now: float) -> tuple[float, float]:
        health_mult = 1.0 + now / 135.0 + max(0.0, now - 180.0) / 185.0 + max(0.0, now - 300.0) / 240.0
        speed_mult = 1.0 + min(0.3, now / 650.0)
        return health_mult, speed_mult

    def spawn_position(self, game: object, extra_distance: int = 0) -> pygame.Vector2:
        camera = game.camera
        half_w = SCREEN_WIDTH / 2 + 120 + extra_distance
        half_h = SCREEN_HEIGHT / 2 + 120 + extra_distance
        player_pos = game.player.pos

        for _ in range(32):
            side = random.choice(("left", "right", "top", "bottom"))
            if side == "left":
                x = camera.x - half_w
                y = random.uniform(camera.y - half_h, camera.y + half_h)
            elif side == "right":
                x = camera.x + half_w
                y = random.uniform(camera.y - half_h, camera.y + half_h)
            elif side == "top":
                x = random.uniform(camera.x - half_w, camera.x + half_w)
                y = camera.y - half_h
            else:
                x = random.uniform(camera.x - half_w, camera.x + half_w)
                y = camera.y + half_h

            pos = pygame.Vector2(
                max(40, min(game.arena_width - 40, x)),
                max(40, min(game.arena_height - 40, y)),
            )
            if (pos - player_pos).length_squared() > (470 + extra_distance) ** 2:
                return pos

        return pygame.Vector2(
            random.choice((40, game.arena_width - 40)),
            random.uniform(40, game.arena_height - 40),
        )
