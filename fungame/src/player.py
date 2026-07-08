from __future__ import annotations

import math
import random
from collections import defaultdict
from dataclasses import dataclass, field

import pygame

from .constants import (
    PLAYER_MAX_HEALTH,
    PLAYER_RADIUS,
    COLOR_CYAN,
    COLOR_GREEN,
    COLOR_RED,
    COLOR_AMBER,
)
from .projectile import Projectile


@dataclass
class Player:
    pos: pygame.Vector2
    vel: pygame.Vector2 = field(default_factory=pygame.Vector2)
    radius: float = PLAYER_RADIUS
    max_health: float = PLAYER_MAX_HEALTH
    health: float = PLAYER_MAX_HEALTH
    level: int = 1
    xp: int = 0
    xp_to_next: int = 28
    tank_id: str = "starter"
    tank_name: str = "Starter Tank"

    speed: float = 220.0
    fire_rate: float = 3.2
    bullet_damage: float = 16.0
    bullet_speed: float = 620.0
    bullet_size: float = 5.0
    bullet_pierce: int = 0
    multi_shot: int = 1
    magnet_radius: float = 115.0
    bullet_range: float = 760.0
    explosion_radius: float = 0.0

    split_level: int = 0
    side_cannon_level: int = 0
    side_cannon_rate: float = 0.75
    shield_drone_level: int = 0
    lightning_level: int = 0
    lightning_every: int = 6
    crit_chance: float = 0.0
    ricochet: int = 0
    slow_chance: float = 0.0
    slow_duration: float = 0.0
    poison_dps: float = 0.0
    poison_duration: float = 0.0
    armor: float = 0.0
    regen_per_second: float = 0.0
    time_since_damage: float = 0.0
    passive_regen_rate: float = 1.0
    ability_cooldown_reduction: float = 0.0
    handling_response: float = 13.5
    ram_damage_mult: float = 1.0
    ram_knockback_mult: float = 1.0
    contact_damage_reduction: float = 0.0
    track_dash_mult: float = 1.0
    gear_chest_bonus: float = 0.0
    contract_blueprint_bonus_chance: float = 0.0
    status_duration_mult: float = 1.0
    Strength: int = 0
    Dexterity: int = 0
    Vitality: int = 0
    Tech: int = 0
    Focus: int = 0
    Luck: int = 0
    active_skills: list = field(default_factory=list)
    equipped_effects: set[str] = field(default_factory=set)
    luck: float = 0.0
    run_coin_bonus: float = 1.0
    run_xp_bonus: float = 1.0
    boss_damage_bonus: float = 0.0
    turret_damage_mult: float = 1.0
    turret_range_bonus: float = 0.0
    dash_cooldown_duration: float = 1.6
    magnet_pulse_level: int = 0
    magnet_pulse_timer: float = 0.0
    overclock_level: int = 0
    overclock_timer: float = 0.0
    emergency_shield_level: int = 0
    emergency_shield_cooldown: float = 0.0
    mine_layer_level: int = 0
    overpressure_level: int = 0
    serrated_bonus: float = 0.0
    volatile_chance: float = 0.0
    burn_chance: float = 0.0
    burn_dps: float = 0.0
    corrosion_level: int = 0
    kinetic_barrier_level: int = 0
    kinetic_barrier_charge: float = 0.0
    kinetic_barrier_shield: float = 0.0
    last_stand_level: int = 0
    bloodless_harvest: bool = False
    salvage_pct: float = 0.0
    drone_swarm_level: int = 0
    drone_swarm_kills: int = 0
    repair_drone_level: int = 0
    ability_power_mult: float = 1.0
    cursor_minefield_level: int = 0
    firestorm_catalyst_level: int = 0
    scrapstorm_fragment_level: int = 0
    hyperdrive_level: int = 0
    wildfire_level: int = 0
    molten_payload_level: int = 0
    ash_collector_level: int = 0
    frostbite_level: int = 0
    shatter_freeze_level: int = 0
    ice_barrier_level: int = 0
    arc_rounds_level: int = 0
    capacitor_link_level: int = 0
    storm_battery_level: int = 0
    plague_burst_level: int = 0
    acid_pool_level: int = 0
    venom_engine_level: int = 0
    family_passives_unlocked: set[str] = field(default_factory=set)
    last_passive_unlocks: list[object] = field(default_factory=list)
    last_evolution_unlocks: list[object] = field(default_factory=list)
    content_unlocks: set[str] = field(default_factory=set)
    conductive_wildfire_level: int = 0
    toxic_frostbite_level: int = 0
    storm_shatter_level: int = 0
    salvage_momentum_level: int = 0
    blueprint_echo_level: int = 0
    relay_overcharge_level: int = 0
    split_fireball_level: int = 0
    chilling_ring_level: int = 0
    corrosive_burst_level: int = 0
    arc_echo_level: int = 0
    contract_momentum_timer: float = 0.0
    relay_charge: float = 0.0
    relay_next_shot_boost: float = 0.0
    fire_patch_radius_bonus: float = 0.0
    frost_nova_radius_bonus: float = 0.0
    acid_puddle_duration_bonus: float = 0.0
    arc_surge_chain_bonus: int = 0
    engineer_turret_duration_bonus: float = 0.0
    engineer_turret_rate_bonus: float = 0.0
    contract_coin_bonus: int = 0
    blueprint_analysis_active: bool = False
    surge_stabilizer_active: bool = False
    chest_calibration_active: bool = False
    boss_salvage_tools_active: bool = False
    evolution_stabilizer_active: bool = False
    fusion_resonance_active: bool = False
    fireball_splitter_active: bool = False
    frost_shockwave_active: bool = False
    acid_mist_active: bool = False
    chain_echo_active: bool = False
    relay_tools_active: bool = False
    poison_tick_speed_bonus: float = 0.0
    sniper_pierce_damage_bonus: float = 0.0
    travel_damage_bonus: float = 0.0
    fire_duration_bonus: float = 0.0
    poison_duration_bonus: float = 0.0
    cryo_duration_bonus: float = 0.0
    damage_invuln_bonus: float = 0.0
    crit_damage_bonus: float = 0.0
    explosion_falloff_bonus: float = 0.0
    kinetic_charge_mult: float = 1.0
    lightning_chain_range: float = 175.0
    lightning_hit_counter: int = 0
    economy_pulse_timer: float = 0.0
    defense_pulse_cooldown: float = 0.0
    ice_barrier_cooldown: float = 0.0
    inferno_core_cooldown: float = 0.0
    plague_network_cooldown: float = 0.0
    absolute_zero_cooldown: float = 0.0
    storm_grid_cooldown: float = 0.0
    storm_grid_pulse_counter: int = 0

    cooldown: float = 0.0
    side_cooldown: float = 0.0
    invuln: float = 0.0
    hurt_flash: float = 0.0
    dash_cooldown: float = 0.0
    pending_dash: bool = False
    shot_counter: int = 0
    engineer_deploy_timer: float = 0.0
    engineer_deploy_interval: float = 0.0
    engineer_turret_cap: int = 0
    engineer_turret_cooldown: float = 0.55

    aim_dir: pygame.Vector2 = field(default_factory=lambda: pygame.Vector2(1, 0))
    upgrade_counts: defaultdict[str, int] = field(default_factory=lambda: defaultdict(int))
    evolutions: set[str] = field(default_factory=set)

    def has_family_passive(self, family: str, threshold: int) -> bool:
        return f"{family}:{threshold}" in self.family_passives_unlocked

    def request_dash(self) -> None:
        self.pending_dash = True

    def update(self, dt: float, keys: pygame.key.ScancodeWrapper, mouse_world: pygame.Vector2, game: object) -> None:
        move = pygame.Vector2(
            int(keys[pygame.K_d]) - int(keys[pygame.K_a]),
            int(keys[pygame.K_s]) - int(keys[pygame.K_w]),
        )
        moving = move.length_squared() > 0
        if moving:
            move = move.normalize()

        desired = move * self.speed
        self.vel = self.vel.lerp(desired, min(1.0, self.handling_response * dt))

        aim = mouse_world - self.pos
        if aim.length_squared() > 12:
            self.aim_dir = aim.normalize()

        self._update_timers(dt)
        self._update_branch_defenses(dt, moving)
        if self.regen_per_second > 0 and self.time_since_damage >= 2.5 and self.health > 0:
            self.heal(self.regen_per_second * dt)
        if self.repair_drone_level > 0 and self.health > 0:
            self.heal(0.4 * self.repair_drone_level * dt)
        if self.time_since_damage >= 5.0 and self.health > 0:
            self.heal(max(0.0, self.passive_regen_rate) * dt)

        # Mouse events cast tank specials; this loop only advances their cooldowns.
        for skill in self.active_skills:
            if skill["cooldown"] > 0:
                skill["cooldown"] = max(0.0, skill["cooldown"] - dt)

        if self.pending_dash:
            self._dash(move, game)
        self.pending_dash = False

        self.pos += self.vel * dt
        self.pos.x = max(self.radius, min(game.arena_width - self.radius, self.pos.x))
        self.pos.y = max(self.radius, min(game.arena_height - self.radius, self.pos.y))

        self.cooldown -= dt
        if self.cooldown <= 0:
            self._fire_volley(game)
            self.cooldown += max(0.035, 1.0 / self.effective_fire_rate)

        if self.side_cannon_level > 0:
            self.side_cooldown -= dt
            if self.side_cooldown <= 0:
                self._fire_side_cannons(game)
                self.side_cooldown += self.side_cannon_rate

        if self.tank_id == "engineer":
            self._update_engineer_deploy(dt, game)

        if self.magnet_pulse_level > 0:
            self.magnet_pulse_timer -= dt
            if self.magnet_pulse_timer <= 0:
                game.trigger_magnet_pulse(220 + self.magnet_pulse_level * 85)
                self.magnet_pulse_timer = max(3.2, 8.0 - self.magnet_pulse_level * 0.8)
        if self.has_family_passive("Economy", 4):
            self.economy_pulse_timer -= dt
            if self.economy_pulse_timer <= 0:
                game.trigger_magnet_pulse(190)
                self.economy_pulse_timer = 6.5

    def _update_branch_defenses(self, dt: float, moving: bool) -> None:
        if self.kinetic_barrier_level <= 0:
            return
        if moving:
            self.kinetic_barrier_charge += dt * self.kinetic_charge_mult
            max_shield = 10.0 + self.kinetic_barrier_level * 9.0
            if self.kinetic_barrier_charge >= 2.8 and self.kinetic_barrier_shield < max_shield:
                self.kinetic_barrier_shield = min(max_shield, self.kinetic_barrier_shield + 7.0)
                self.kinetic_barrier_charge = 0.0
        else:
            self.kinetic_barrier_charge = max(0.0, self.kinetic_barrier_charge - dt * 1.5)

    def _maybe_drop_cursor_mines(self, game: object, mouse_world: pygame.Vector2) -> None:
        if self.cursor_minefield_level <= 0:
            return
        count = min(3, 1 + self.cursor_minefield_level)
        for _ in range(count):
            offset = pygame.Vector2(random.uniform(-34, 34), random.uniform(-34, 34))
            game.add_mine(mouse_world + offset, self.cursor_minefield_level)

    def _update_timers(self, dt: float) -> None:
        self.invuln = max(0.0, self.invuln - dt)
        self.hurt_flash = max(0.0, self.hurt_flash - dt)
        self.dash_cooldown = max(0.0, self.dash_cooldown - dt)
        self.overclock_timer = max(0.0, self.overclock_timer - dt)
        self.emergency_shield_cooldown = max(0.0, self.emergency_shield_cooldown - dt)
        self.defense_pulse_cooldown = max(0.0, self.defense_pulse_cooldown - dt)
        self.ice_barrier_cooldown = max(0.0, self.ice_barrier_cooldown - dt)
        self.inferno_core_cooldown = max(0.0, self.inferno_core_cooldown - dt)
        self.plague_network_cooldown = max(0.0, self.plague_network_cooldown - dt)
        self.absolute_zero_cooldown = max(0.0, self.absolute_zero_cooldown - dt)
        self.storm_grid_cooldown = max(0.0, self.storm_grid_cooldown - dt)
        self.contract_momentum_timer = max(0.0, self.contract_momentum_timer - dt)
        self.time_since_damage += dt

    def _dash(self, move: pygame.Vector2, game: object) -> None:
        if self.dash_cooldown > 0:
            return
        direction = move if move.length_squared() > 0 else self.aim_dir
        self.vel += direction * 620 * self.track_dash_mult
        self.invuln = max(self.invuln, 0.18)
        self.dash_cooldown = self.dash_cooldown_duration
        game.add_screen_shake(4.0, source_type="dash")
        game.spawn_dash_particles(self.pos, -direction)

    def _fire_volley(self, game: object) -> None:
        count = max(1, self.multi_shot)
        spread = min(46.0, 8.5 * (count - 1))
        base_angle = math.atan2(self.aim_dir.y, self.aim_dir.x)
        start = -spread * 0.5
        self.shot_counter += 1
        chain = self.lightning_level if self.lightning_level and self.shot_counter % self.lightning_every == 0 else 0
        arc_interval = max(4, 9 - self.arc_rounds_level - self.storm_battery_level)
        if self.arc_rounds_level > 0 and self.shot_counter % arc_interval == 0:
            chain = max(chain, 1)
        if chain > 0 and self.has_family_passive("Lightning", 6):
            chain += 1

        for i in range(count):
            angle_offset = start + (spread / max(1, count - 1)) * i if count > 1 else 0
            angle = base_angle + math.radians(angle_offset)
            direction = pygame.Vector2(math.cos(angle), math.sin(angle))
            game.add_projectile(self._make_projectile(direction, game, chain=chain))
        rocket_trail = "rocket_core" in self.evolutions or "scrapstorm_detonator" in self.evolutions
        game.spawn_muzzle_particles(self.pos + self.aim_dir * 22, self.aim_dir, rocket_trail)
        if self.mine_layer_level > 0 and game.random_chance(0.05 + self.mine_layer_level * 0.035):
            game.add_mine(self.pos - self.aim_dir * 34, self.mine_layer_level)

    def _update_engineer_deploy(self, dt: float, game: object) -> None:
        if self.engineer_turret_cap <= 0:
            return
        self.engineer_deploy_timer -= dt
        if self.engineer_deploy_timer > 0:
            return
        if len(game.summons) >= self.engineer_turret_cap:
            self.engineer_deploy_timer = 0.6
            return
        drop_dir = self.aim_dir.rotate(180 + 35 * (len(game.summons) % 2 * 2 - 1))
        pos = self.pos + drop_dir * 42
        game.add_mini_turret(pos, self.engineer_turret_cooldown)
        self.engineer_deploy_timer = self.engineer_deploy_interval

    def _fire_side_cannons(self, game: object) -> None:
        perp = pygame.Vector2(-self.aim_dir.y, self.aim_dir.x)
        dirs = [perp, -perp]
        if "twin_turret_form" in self.evolutions:
            dirs.extend([self.aim_dir.rotate(24), self.aim_dir.rotate(-24)])
        for direction in dirs:
            projectile = self._make_projectile(direction, game, damage_scale=0.65, side=True)
            game.add_projectile(projectile)

    def _make_projectile(
        self,
        direction: pygame.Vector2,
        game: object,
        damage_scale: float = 1.0,
        chain: int = 0,
        side: bool = False,
    ) -> Projectile:
        speed = self.bullet_speed
        damage = self.bullet_damage * damage_scale
        radius = self.bullet_size
        kind = "slug"
        explosion = self.explosion_radius
        pierce = self.bullet_pierce

        if self.tank_id == "sniper" and not side:
            kind = "sniper"
            damage *= 1.05
            speed *= 1.04
            if pierce > 0:
                damage *= 1.0 + self.sniper_pierce_damage_bonus
        elif self.tank_id == "engineer" and not side:
            kind = "engineer"
        elif self.tank_id == "flame_caster" and not side:
            kind = "fireball"
            explosion += 12

        if not side and self.contract_momentum_timer > 0:
            damage *= 1.0 + 0.08 * self.salvage_momentum_level
        if not side and self.relay_next_shot_boost > 0:
            damage *= 1.0 + self.relay_next_shot_boost
            chain += 1
            self.relay_next_shot_boost = 0.0

        if "minigun_mode" in self.evolutions and not side:
            kind = "minigun"
            radius = max(4.0, radius - 1.0)
            speed *= 1.08
        if ("rocket_core" in self.evolutions or "scrapstorm_detonator" in self.evolutions) and not side:
            kind = "rocket"
            speed *= 0.88
            radius += 2.0
            explosion += 18

        crit = False
        if not side and self.crit_chance > 0 and game.random_chance(self.crit_chance):
            crit = True
            damage *= 1.85 + self.crit_damage_bonus

        split = self.split_level if not side else 0
        bounces = self.ricochet if not side else 0
        slow_chance = self.slow_chance
        slow_duration = self.slow_duration + self.cryo_duration_bonus
        poison_dps = self.poison_dps
        poison_duration = self.poison_duration
        dot_family = "Poison" if poison_dps > 0 else ""
        freeze_burst_radius = 0.0
        if not side and "bullets_explode" in self.equipped_effects and self.shot_counter % 5 == 0:
            explosion += 54
        if not side and self.tank_id == "sniper" and "sniper_freeze" in self.equipped_effects:
            slow_chance += 0.24
            slow_duration += 0.85
        if not side and self.tank_id == "twin_shot" and "ricochet_double" in self.equipped_effects:
            bounces += 1
        if not side and kind in ("fireball", "rocket") and "impact_split" in self.equipped_effects:
            split += 2
        if crit and "crit_burn" in self.equipped_effects:
            poison_dps += max(4.0, damage * 0.07)
            poison_duration = max(poison_duration, 2.4)
            dot_family = "Fire"
        if not side and self.burn_chance > 0 and game.random_chance(self.burn_chance):
            poison_dps += self.burn_dps
            poison_duration = max(poison_duration, 2.6 + self.fire_duration_bonus)
            dot_family = "Fire"
        elif poison_dps > 0:
            poison_duration += self.poison_duration_bonus
        if not side and self.molten_payload_level > 0 and explosion > 0:
            poison_dps += max(2.5, self.burn_dps * (0.35 + self.molten_payload_level * 0.08))
            poison_duration = max(poison_duration, 1.4 + self.fire_duration_bonus)
            dot_family = "Fire"
        if not side and self.has_family_passive("Fire", 6) and self.shot_counter % 5 == 0:
            explosion += 18
            poison_dps += max(3.0, self.burn_dps * 0.5)
            poison_duration = max(poison_duration, 1.8 + self.fire_duration_bonus)
            dot_family = "Fire"
        if not side and self.has_family_passive("Cryo", 6) and self.shot_counter % 7 == 0:
            slow_chance = 1.0
            slow_duration = max(slow_duration, 1.35 + self.cryo_duration_bonus)
            freeze_burst_radius = 78

        knockback = 75 + radius * 9
        if not side and self.overpressure_level > 0 and self.shot_counter % 6 == 0:
            damage *= 1.0 + self.overpressure_level * 0.18
            radius += 2.0 + self.overpressure_level
            speed *= 0.94
            knockback += 90 + self.overpressure_level * 28
        if not side and self.has_family_passive("Projectile", 6) and self.shot_counter % 8 == 0:
            pierce += 1
        slow_duration *= self.status_duration_mult
        poison_duration *= self.status_duration_mult

        return Projectile(
            pos=self.pos + direction * 22,
            vel=direction * speed,
            radius=radius,
            damage=damage,
            source="player",
            ttl=self.bullet_range / max(1.0, speed),
            pierce=pierce,
            kind=kind,
            explosion_radius=explosion,
            split=split,
            chain=chain,
            knockback=knockback,
            bounces=bounces,
            crit=crit,
            slow_chance=slow_chance,
            slow_duration=slow_duration,
            poison_dps=poison_dps,
            poison_duration=poison_duration,
            dot_family=dot_family,
            freeze_burst_radius=freeze_burst_radius,
            serrated_bonus=self.serrated_bonus if not side else 0.0,
            volatile_chance=self.volatile_chance if not side else 0.0,
            corrosion_level=self.corrosion_level if not side else 0,
        )

    def take_damage(self, amount: float) -> bool:
        if self.invuln > 0:
            return False
        has_unique_shield = "low_hp_shield" in self.equipped_effects
        if (self.emergency_shield_level > 0 or has_unique_shield) and self.health / self.max_health < 0.32 and self.emergency_shield_cooldown <= 0:
            self.invuln = 1.0 + self.emergency_shield_level * 0.35 + (0.55 if has_unique_shield else 0.0)
            self.emergency_shield_cooldown = 18.0 if self.has_family_passive("Defense", 6) else 28.0
            self.hurt_flash = 0.2
            return False
        damage = amount * max(0.45, 1.0 - self.armor) * max(0.55, 1.0 - self.contact_damage_reduction)
        if self.kinetic_barrier_shield > 0:
            absorbed = min(self.kinetic_barrier_shield, damage)
            self.kinetic_barrier_shield -= absorbed
            damage -= absorbed
        self.health -= damage
        self.invuln = 0.24 + self.damage_invuln_bonus
        self.hurt_flash = 0.16
        self.time_since_damage = 0.0
        return True

    def heal(self, amount: float) -> None:
        self.health = min(self.max_health, self.health + amount)

    def gain_xp(self, amount: int) -> None:
        self.xp += amount

    def can_level(self) -> bool:
        return self.xp >= self.xp_to_next

    def level_up_heal_amount(self) -> float:
        return min(15.0, max(3.0, self.max_health * 0.05))

    def commit_level_up(self) -> float:
        self.xp -= self.xp_to_next
        self.level += 1
        self.xp_to_next = int(28 + self.level * 11 + self.level**1.35 * 4)
        before = self.health
        self.heal(self.level_up_heal_amount())
        return self.health - before

    def shield_positions(self, now: float) -> list[pygame.Vector2]:
        positions: list[pygame.Vector2] = []
        count = self.shield_drone_level
        if count <= 0:
            return positions
        radius = 42 + count * 5
        for i in range(count):
            angle = now * 2.7 + i * (math.tau / count)
            positions.append(self.pos + pygame.Vector2(math.cos(angle), math.sin(angle)) * radius)
        return positions

    def cast_burst_barrage(self, game: object, mouse_world: pygame.Vector2) -> bool:
        direction = (mouse_world - self.pos)
        if direction.length_squared() > 0:
            direction = direction.normalize()
        else:
            direction = self.aim_dir
        base_angle = math.atan2(direction.y, direction.x)
        ability_damage = self.bullet_damage * 0.8 * (1.0 + self.Focus * 0.04) * self.ability_power_mult
        for i in range(8):
            angle = base_angle + math.radians(random.uniform(-15, 15))
            dir_vec = pygame.Vector2(math.cos(angle), math.sin(angle))
            game.add_projectile(Projectile(
                pos=self.pos + dir_vec * 22,
                vel=dir_vec * self.bullet_speed * 1.1,
                radius=self.bullet_size * 0.8,
                damage=ability_damage,
                source="player",
                ttl=self.bullet_range / (self.bullet_speed * 1.1),
                pierce=0,
                kind="ability_bullet",
                color=COLOR_CYAN
            ))
        game.spawn_muzzle_particles(self.pos + direction * 22, direction)
        game.add_message("BURST BARRAGE!", COLOR_CYAN)
        game.sounds.play("shoot")
        return True

    def cast_piercing_laser(self, game: object, mouse_world: pygame.Vector2) -> bool:
        direction = (mouse_world - self.pos)
        if direction.length_squared() > 0:
            direction = direction.normalize()
        else:
            direction = self.aim_dir
        ability_damage = self.bullet_damage * 3.5 * (1.0 + self.Focus * 0.04) * self.ability_power_mult
        game.add_projectile(Projectile(
            pos=self.pos + direction * 22,
            vel=direction * 1800.0,
            radius=self.bullet_size * 2.5,
            damage=ability_damage,
            source="player",
            ttl=1.5,
            pierce=99,
            kind="laser",
            color=COLOR_CYAN
        ))
        game.spawn_muzzle_particles(self.pos + direction * 22, direction)
        game.add_message("PIERCING LASER!", COLOR_CYAN)
        game.sounds.play("shoot")
        return True

    def cast_deploy_sentry(self, game: object, mouse_world: pygame.Vector2) -> bool:
        pos = pygame.Vector2(mouse_world)
        game.add_mini_turret(pos, self.engineer_turret_cooldown)
        game.add_message("SENTRY DEPLOYED!", COLOR_GREEN)
        return True

    def cast_fireball(self, game: object, mouse_world: pygame.Vector2) -> bool:
        direction = (mouse_world - self.pos)
        if direction.length_squared() > 0:
            direction = direction.normalize()
        else:
            direction = self.aim_dir
        ability_damage = self.bullet_damage * 2.0 * (1.0 + self.Focus * 0.04) * self.ability_power_mult
        split = max(self.firestorm_catalyst_level, self.split_fireball_level * 2)
        if self.fireball_splitter_active:
            split = max(split, 2)
        poison_dps = self.burn_dps if self.firestorm_catalyst_level > 0 else 0.0
        if self.fire_patch_radius_bonus > 0:
            poison_dps = max(poison_dps, self.burn_dps, 5.0)
        game.add_projectile(Projectile(
            pos=self.pos + direction * 22,
            vel=direction * 480.0,
            radius=self.bullet_size * 2.0,
            damage=ability_damage,
            source="player",
            ttl=2.0,
            pierce=0,
            kind="fireball",
            explosion_radius=72 + self.Focus * 4 + self.fire_patch_radius_bonus,
            color=COLOR_RED,
            split=split,
            poison_dps=poison_dps,
            poison_duration=2.4 + self.fire_duration_bonus if poison_dps > 0 else 0.0,
            dot_family="Fire" if poison_dps > 0 else "",
        ))
        game.add_message("FIREBALL!", COLOR_RED)
        return True

    def cast_frost_nova(self, game: object, mouse_world: pygame.Vector2) -> bool:
        target = pygame.Vector2(mouse_world)
        target.x = max(80, min(game.arena_width - 80, target.x))
        target.y = max(80, min(game.arena_height - 80, target.y))
        game._freeze_burst(target, 138 + self.Focus * 5 + self.frost_nova_radius_bonus, 1.6 + self.cryo_duration_bonus)
        if self.frost_shockwave_active or self.chilling_ring_level > 0:
            ring_level = max(1, self.chilling_ring_level)
            game.add_lingering_zone(target, "Cryo", 88 + ring_level * 16, 1.8 + ring_level * 0.35, 0.0)
        game.spawn_hit_particles(target, COLOR_CYAN)
        game.add_screen_shake(5.0, source_type="unique_activation")
        game.add_message("FROST NOVA!", COLOR_CYAN)
        return True

    def cast_acid_glob(self, game: object, mouse_world: pygame.Vector2) -> bool:
        direction = mouse_world - self.pos
        direction = direction.normalize() if direction.length_squared() else self.aim_dir
        game.add_projectile(Projectile(
            pos=self.pos + direction * 24,
            vel=direction * 430,
            radius=11,
            damage=self.bullet_damage * 1.25 * self.ability_power_mult,
            source="player",
            ttl=1.35,
            pierce=0,
            kind="acid_glob",
            color=COLOR_GREEN,
            explosion_radius=92,
            poison_dps=max(11.0, self.poison_dps * 1.75) * (1.0 + self.poison_tick_speed_bonus),
            poison_duration=4.2 + self.poison_duration_bonus + self.acid_puddle_duration_bonus,
            dot_family="Poison",
        ))
        game.add_message("ACID GLOB!", COLOR_GREEN)
        return True

    def cast_arc_surge(self, game: object, mouse_world: pygame.Vector2) -> bool:
        target = pygame.Vector2(mouse_world)
        target.x = max(70, min(game.arena_width - 70, target.x))
        target.y = max(70, min(game.arena_height - 70, target.y))
        candidates = [enemy for enemy in game.enemies if enemy.alive and (enemy.pos - target).length_squared() <= 175 ** 2]
        if not candidates:
            candidates = [enemy for enemy in game.enemies if enemy.alive]
        if not candidates:
            return False
        first = min(candidates, key=lambda enemy: (enemy.pos - target).length_squared())
        damage = self.bullet_damage * 3.0 * self.ability_power_mult
        first.take_damage(damage, (first.pos - self.pos).normalize() * 180 if first.pos != self.pos else pygame.Vector2())
        from .effects import DamageNumber
        game.damage_numbers.append(DamageNumber(str(int(damage)), first.pos.copy(), COLOR_CYAN))
        game._chain_lightning(first, 4 + self.arc_surge_chain_bonus, damage * 0.62)
        echo_level = self.arc_echo_level + (1 if self.chain_echo_active else 0)
        if echo_level > 0 and game.random_chance(0.18 + echo_level * 0.12):
            game._chain_lightning(first, 1 + echo_level, damage * 0.24)
            game.add_message("ARC ECHO", COLOR_BLUE)
        game.spawn_hit_particles(first.pos, COLOR_CYAN)
        game.add_screen_shake(6.0, source_type="unique_activation")
        game.add_message("ARC SURGE!", COLOR_CYAN)
        return True

    def activate_special(self, game: object, mouse_world: pygame.Vector2) -> bool:
        if self.health <= 0:
            return False
        cooldown_reduction = min(0.6, self.Focus * 0.03 + self.ability_cooldown_reduction)
        for skill in self.active_skills:
            if skill["cooldown"] > 0:
                continue
            method = getattr(self, skill["cast_fn_name"], None)
            if method and method(game, mouse_world):
                skill["cooldown"] = skill["max_cooldown"] * (1.0 - cooldown_reduction)
                self._maybe_drop_cursor_mines(game, mouse_world)
                if hasattr(game, "stats"):
                    game.stats.abilities_cast += 1
                if hasattr(game, "record_ability_use"):
                    game.record_ability_use()
                return True
        return False

    def cast_bullet_fan(self, game: object, mouse_world: pygame.Vector2) -> bool:
        direction = (mouse_world - self.pos)
        if direction.length_squared() > 0:
            direction = direction.normalize()
        else:
            direction = self.aim_dir
        base_angle = math.atan2(direction.y, direction.x)
        ability_damage = self.bullet_damage * 0.9 * (1.0 + self.Focus * 0.04) * self.ability_power_mult
        for i in range(10):
            angle = base_angle + math.radians(-30 + i * 6)
            dir_vec = pygame.Vector2(math.cos(angle), math.sin(angle))
            game.add_projectile(Projectile(
                pos=self.pos + dir_vec * 22,
                vel=dir_vec * self.bullet_speed * 0.95,
                radius=self.bullet_size * 0.9,
                damage=ability_damage,
                source="player",
                ttl=self.bullet_range / (self.bullet_speed * 0.95),
                pierce=0,
                kind="ability_bullet",
                color=COLOR_AMBER
            ))
        game.spawn_muzzle_particles(self.pos + direction * 22, direction)
        game.add_message("BULLET FAN!", COLOR_AMBER)
        game.sounds.play("shoot")
        return True

    @property
    def alive(self) -> bool:
        return self.health > 0

    @property
    def effective_fire_rate(self) -> float:
        multiplier = 1.0
        if self.overclock_timer > 0:
            multiplier += 0.35 + self.overclock_level * 0.12
        if self.last_stand_level > 0 and self.health / max(1.0, self.max_health) <= 0.35:
            multiplier += 0.16 * self.last_stand_level
        if self.contract_momentum_timer > 0:
            multiplier += 0.06 * self.salvage_momentum_level
        raw = self.fire_rate * multiplier
        if raw > 8.0:
            raw = 8.0 + (raw - 8.0) * 0.45
        return min(raw, 14.0)

    @property
    def effective_magnet_radius(self) -> float:
        radius = self.magnet_radius
        if self.last_stand_level > 0 and self.health / max(1.0, self.max_health) <= 0.35:
            radius += 35 * self.last_stand_level
        if self.hyperdrive_level > 0 and self.vel.length_squared() > (self.speed * 0.35) ** 2:
            radius += 70
        return radius

    @property
    def sprite_key(self) -> str:
        if "minigun_mode" in self.evolutions or "railgun_core" in self.evolutions:
            return "evolution_projectile"
        if self.tank_id == "flame_caster" and "inferno_core" in self.evolutions:
            return "evolution_fire"
        if self.tank_id == "poison" and "plague_network" in self.evolutions:
            return "evolution_poison"
        if self.tank_id == "cryo" and "absolute_zero" in self.evolutions:
            return "evolution_cryo"
        if self.tank_id == "lightning" and "storm_grid" in self.evolutions:
            return "evolution_lightning"
        if "rocket_core" in self.evolutions or "scrapstorm_detonator" in self.evolutions:
            return "player_rocket"
        if "twin_turret_form" in self.evolutions:
            return "player_twin"
        if self.tank_id == "sniper":
            return "player_sniper"
        if self.tank_id == "engineer":
            return "player_engineer"
        if self.tank_id == "twin_shot":
            return "player_twin"
        if self.tank_id == "flame_caster":
            return "player_flame"
        if self.tank_id == "cryo":
            return "player_cryo"
        if self.tank_id == "poison":
            return "player_poison"
        if self.tank_id == "lightning":
            return "player_lightning"
        return "player"

    @property
    def turret_key(self) -> str:
        if "rocket_core" in self.evolutions or "scrapstorm_detonator" in self.evolutions:
            return "turret_rocket"
        if "twin_turret_form" in self.evolutions:
            return "turret_twin"
        if "minigun_mode" in self.evolutions:
            return "turret_minigun"
        if self.tank_id == "sniper":
            return "turret_sniper"
        if self.tank_id == "engineer":
            return "turret_engineer"
        if self.tank_id == "twin_shot":
            return "turret_twin"
        if self.tank_id == "flame_caster":
            return "turret_rocket"
        return "turret_starter"

    skill_points: int = 0

    def allocate_node(self, node_id: str) -> bool:
        return True

    def refund_node(self) -> None:
        pass
