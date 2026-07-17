from __future__ import annotations

import asyncio
import math
import random
import sys
from typing import Any

import pygame

from .constants import (
    CAMERA_LERP,
    COLOR_AMBER,
    COLOR_BG,
    COLOR_BLUE,
    COLOR_CYAN,
    COLOR_GREEN,
    COLOR_MAGENTA,
    COLOR_MUTED,
    COLOR_RED,
    COLOR_TEXT,
    FPS,
    MAX_DAMAGE_NUMBERS,
    MAX_ENEMIES,
    MAX_ENEMY_PROJECTILES,
    MAX_MINES,
    MAX_PARTICLES,
    MAX_PICKUPS,
    MAX_PLAYER_PROJECTILES,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    TILE_SIZE,
)
from .achievements import ACHIEVEMENTS, evaluate_achievements
from .assets import SpriteBank
from .effects import DamageNumber, Particle
from .equipment import EQUIPMENT_BY_SLOT, EQUIPMENT_SLOTS
from .enemy import Enemy, create_enemy
from .game_state import RunStats, ScreenState
from .meta_upgrades import META_BY_ID, apply_meta_upgrades
from .progression import (
    RESEARCH_BY_ID,
    apply_research_modifiers,
    available_contracts,
    available_modifiers,
    content_unlocked,
    evaluate_unlocks,
    purchase_research,
)
from .pickup import Pickup
from .player import Player
from .projectile import Projectile
from .save_manager import SaveManager
from .skill_tree import SKILL_BY_ID, refund_skill_tree, unlock_skill_node
from .sound import SoundBank
from .stages import get_stage
from .summon import Mine, MiniTurret
from .tank_data import TANK_BY_ID, configure_player_tank
from .ui import UI
from .upgrades import Upgrade, apply_upgrade, choose_upgrades
from .waves import WaveDirector


LOOT_UNLOCK_SECONDS = 300
XP_PICKUP_CAP = 210
HEALTH_PICKUP_CAP = 34
COIN_PICKUP_CAP = 140
PICKUP_MERGE_RADIUS = {
    "xp": 38.0,
    "coin": 34.0,
}
XP_PICKUP_DRAW_SIZE = 20
SHAKE_CAPS = {
    "normal_hit": 0.0,
    "small_death": 0.0,
    "pickup": 0.0,
    "dash": 0.0,
    "chain": 0.0,
    "player_hit": 2.4,
    "heavy_player_hit": 3.6,
    "large_explosion": 3.2,
    "boss_attack": 1.8,
    "boss_spawn": 2.8,
    "boss_death": 4.6,
    "unique_activation": 3.4,
    "run_end": 3.6,
    "generic": 2.0,
}
SHAKE_SCALE = 0.58

ENEMY_PROJECTILE_SPRITES = {
    "enemy": "enemy_bullet",
    "enemy_artillery_shell": "enemy_projectile_artillery_shell",
    "enemy_poison_glob": "enemy_projectile_poison_glob",
    "enemy_lightning_arc": "enemy_projectile_lightning_arc",
    "enemy_cryo_bolt": "effect_frost_zone",
    "enemy_mine": "effect_mine_hazard",
}


class Game:
    def __init__(
        self,
        screen: pygame.Surface,
        smoke: bool = False,
        debug_unlock_loot: bool = False,
        debug_performance: bool = False,
    ) -> None:
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.smoke = smoke
        self.debug_performance = debug_performance
        self.assets = SpriteBank()
        self.ui = UI()
        self.sounds = SoundBank(enabled=not smoke and sys.platform != "emscripten")
        self.save_manager = SaveManager()
        self.save_data = self.save_manager.load()
        if evaluate_unlocks(self.save_data):
            self.save_manager.save(self.save_data)
        if debug_unlock_loot:
            self.save_data["loot_unlocked"] = True
            self.save_manager.save(self.save_data)
            print("Debug: meta loot unlocked for this save.")
        self.max_enemies = MAX_ENEMIES
        self.state = ScreenState.MENU
        self.running = True
        self.garage_tab = "tanks"
        self.research_category = "All"
        self.progression_tab = "achievements"
        self.achievement_page = 0
        self.menu_particles: list[Particle] = []
        self.reset_run()

    def reset_run(self) -> None:
        self.stage = get_stage(self.save_data.get("selected_stage"))
        self.arena_width = self.stage.width
        self.arena_height = self.stage.height
        center = pygame.Vector2(self.arena_width / 2, self.arena_height / 2)
        self.player = Player(center)
        self.selected_tank_id = self.save_data.get("selected_tank", "starter")
        if self.selected_tank_id not in TANK_BY_ID:
            self.selected_tank_id = "starter"
            self.save_data["selected_tank"] = "starter"
        configure_player_tank(self.player, self.selected_tank_id)
        self.player.content_unlocks = set(self.save_data.get("unlocks_completed", []))
        self.xp_multiplier, self.coin_multiplier = apply_meta_upgrades(self.player, self.save_data)
        apply_research_modifiers(self.player, self.save_data)
        self.stage_enemy_speed_multiplier = 1.0
        self.explosion_damage_multiplier = 1.0
        self.charged_wreckage_active = False
        self.urban_crossfire_active = False
        self.stage_pickup_density_bonus = 0.0
        if self.stage.id == "scrap_outskirts":
            self.player.magnet_radius += 20
        elif self.stage.id == "desert_wrecks":
            self.stage_enemy_speed_multiplier = 1.12
        elif self.stage.id == "frozen_base":
            self.player.cryo_duration_bonus += 0.35
        elif self.stage.id == "shattered_metro":
            self.urban_crossfire_active = True
            self.stage_pickup_density_bonus = 0.16
        elif self.stage.id == "overgrowth_basin":
            self.player.speed *= 0.96
            self.player.magnet_radius += 18
            self.stage_pickup_density_bonus = 0.24
        self.active_contract = random.choice(available_contracts(self.stage, self.save_data))
        self.active_modifier = random.choice(available_modifiers(self.stage, self.save_data))
        if self.active_modifier.id == "volatile_scrap":
            self.stage_enemy_speed_multiplier *= 1.12
            self.explosion_damage_multiplier = 1.22
        elif self.active_modifier.id == "charged_wreckage":
            self.charged_wreckage_active = True
        self.contract_progress = 0
        self.contract_completed = False
        self.contract_failed = False
        self.contract_relay_pos = center + pygame.Vector2(180, -105)
        self.contract_blueprint_analysis_available = True
        self.run_elemental_evolution_families: set[str] = set()
        self.anomaly_route_available = False
        self._last_survival_progress_second = -1
        self.camera = center.copy()
        self.enemies: list[Enemy] = []
        self.projectiles: list[Projectile] = []
        self.summons: list[MiniTurret] = []
        self.mines: list[Mine] = []
        self.lingering_zones: list[dict[str, Any]] = []
        self.pickups: list[Pickup] = []
        self.particles: list[Particle] = []
        self.menu_particles: list[Particle] = []
        self.damage_numbers: list[DamageNumber] = []
        self.messages: list[tuple[str, float, tuple[int, int, int]]] = []
        self.passive_popups: list[tuple[object, float]] = []
        self.level_choices: list[Upgrade] = []
        self.stats = RunStats()
        self.stats.tank_used = self.selected_tank_id
        self.director = WaveDirector()
        self.map_decor = self._build_map_decor()
        self.run_finalized = False
        self.run_loot_unlocked = bool(self.save_data.get("loot_unlocked", False))
        self.loot_unlock_message_shown = self.run_loot_unlocked
        self.next_survival_coin_time = 45.0
        self.shake = 0.0
        self.shake_offset = pygame.Vector2()
        self.frame_count = 0
        self.elemental_death_procs_this_frame = 0

    def start_run(self) -> None:
        self.reset_run()
        self.state = ScreenState.PLAYING
        for _ in range(8):
            self.spawn_enemy("crawler", self.director.spawn_position(self))
        self.add_message("SURVIVE THE SCRAP WAVE", COLOR_CYAN)
        self.add_message(f"CONTRACT: {self.active_contract.name.upper()}", COLOR_AMBER, ttl=3.0)
        self.add_message(self.active_modifier.name.upper(), COLOR_CYAN, ttl=3.0)

    def is_meta_loot_unlocked(self) -> bool:
        return bool(
            self.run_loot_unlocked
            or self.save_data.get("loot_unlocked", False)
            or self.save_data.get("stats", {}).get("best_time", 0) >= LOOT_UNLOCK_SECONDS
            or self.stats.time_survived >= LOOT_UNLOCK_SECONDS
        )

    def _check_meta_loot_unlock(self) -> None:
        if self.run_loot_unlocked or self.stats.time_survived < LOOT_UNLOCK_SECONDS:
            return
        self.run_loot_unlocked = True
        self.save_data["loot_unlocked"] = True
        self.save_manager.save(self.save_data)
        if not self.loot_unlock_message_shown:
            self.loot_unlock_message_shown = True
            self.add_message("META LOOT SYSTEM ONLINE", COLOR_MAGENTA, ttl=3.4)
            self.add_screen_shake(10, source_type="unique_activation")

    def is_content_unlocked(self, unlock_id: str) -> bool:
        return content_unlocked(self.save_data, unlock_id)

    def _refresh_unlocks(self, announce: bool = True) -> list[object]:
        newly_unlocked = evaluate_unlocks(self.save_data)
        if newly_unlocked:
            self.player.content_unlocks.update(unlock.id for unlock in newly_unlocked)
            if announce:
                for unlock in newly_unlocked:
                    self.add_message(f"UNLOCKED: {unlock.name.upper()}", COLOR_GREEN, ttl=3.6)
        return newly_unlocked

    def _open_unlocks_screen(self) -> None:
        self.state = ScreenState.ACHIEVEMENTS
        self.progression_tab = "unlocks"

    def _acknowledge_unlocks(self) -> None:
        if self.save_data.get("unlocks_new"):
            self.save_data["unlocks_new"] = []
            self.save_manager.save(self.save_data)

    def _sync_survival_progress(self) -> None:
        second = int(self.stats.time_survived)
        if second <= self._last_survival_progress_second:
            return
        self._last_survival_progress_second = second
        changed = False
        if second > int(self.save_data.get("best_survival_time", 0)):
            self.save_data["best_survival_time"] = second
            changed = True
        stage_times = self.save_data.setdefault("stage_best_times", {})
        if second > int(stage_times.get(self.stage.id, 0)):
            stage_times[self.stage.id] = second
            changed = True
        if changed:
            self._refresh_unlocks()
            self.save_manager.save(self.save_data)

    def _record_contract_completion(self) -> None:
        self.save_data["lifetime_contracts_completed"] = int(self.save_data.get("lifetime_contracts_completed", 0)) + 1
        self.save_data["lifetime_stage_contracts_completed"] = int(self.save_data.get("lifetime_stage_contracts_completed", 0)) + 1
        stage_counts = self.save_data.setdefault("stage_contract_counts", {})
        stage_counts[self.stage.id] = int(stage_counts.get(self.stage.id, 0)) + 1
        completed_stages = set(self.save_data.get("stage_contracts_completed", []))
        completed_stages.add(self.stage.id)
        self.save_data["stage_contracts_completed"] = sorted(completed_stages)
        self._refresh_unlocks()

    def _record_enemy_milestone(self, enemy: Enemy) -> None:
        changed = False
        if enemy.elite:
            self.stats.elites_defeated += 1
            self.save_data["lifetime_elites_defeated"] = int(self.save_data.get("lifetime_elites_defeated", 0)) + 1
            changed = True
        if enemy.boss:
            self.save_data["lifetime_bosses_defeated"] = int(self.save_data.get("lifetime_bosses_defeated", 0)) + 1
            changed = True
        if changed:
            self._refresh_unlocks()
            self.save_manager.save(self.save_data)

    def record_ability_use(self) -> None:
        self.save_data["lifetime_ability_uses"] = int(self.save_data.get("lifetime_ability_uses", 0)) + 1
        self._refresh_unlocks()
        self.save_manager.save(self.save_data)

    def _record_elemental_evolutions(self, evolutions: list[object]) -> None:
        families = {getattr(evolution, "family", "") for evolution in evolutions}
        elemental = families & {"Fire", "Cryo", "Lightning", "Poison"}
        if not elemental:
            return
        new_families = elemental - self.run_elemental_evolution_families
        if not new_families:
            return
        self.run_elemental_evolution_families.update(new_families)
        permanent = set(self.save_data.get("elemental_evolution_families", []))
        actually_new = new_families - permanent
        if actually_new:
            permanent.update(actually_new)
            self.save_data["elemental_evolution_families"] = sorted(permanent)
            self.save_data["lifetime_evolutions_triggered"] = int(self.save_data.get("lifetime_evolutions_triggered", 0)) + len(actually_new)
            self._refresh_unlocks()
            self.save_manager.save(self.save_data)

    def _record_surge_completion(self) -> None:
        self.stats.salvage_surges_completed += 1
        self.save_data["lifetime_salvage_surges_survived"] = int(self.save_data.get("lifetime_salvage_surges_survived", 0)) + 1
        self._refresh_unlocks()
        self.save_manager.save(self.save_data)

    def buy_research(self, project_id: str) -> None:
        purchased, detail = purchase_research(self.save_data, project_id)
        if not purchased:
            self.add_message(detail.upper(), COLOR_RED)
            return
        self.save_manager.save(self.save_data)
        self.add_message(f"RESEARCH COMPLETED: {detail.upper()}", COLOR_GREEN, ttl=3.0)

    def _update_contract_relay(self, dt: float) -> None:
        if self.player.relay_overcharge_level <= 0:
            return
        near_relay = (self.player.pos - self.contract_relay_pos).length_squared() <= 145**2
        if near_relay:
            self.player.relay_charge = min(1.0, self.player.relay_charge + dt * (0.28 + self.player.relay_overcharge_level * 0.08))
        else:
            self.player.relay_charge = max(0.0, self.player.relay_charge - dt * 0.11)
        if self.player.relay_charge >= 1.0 and self.player.relay_next_shot_boost <= 0:
            self.player.relay_charge = 0.0
            self.player.relay_next_shot_boost = 0.28 + self.player.relay_overcharge_level * 0.12
            self.add_message("RELAY SHOT CHARGED", COLOR_CYAN, ttl=1.1)

    def _build_map_decor(self) -> list[tuple[pygame.Vector2, str, int]]:
        seed = sum(ord(ch) for ch in self.stage.id)
        rng = random.Random(seed)
        decor: list[tuple[pygame.Vector2, str, int]] = []
        center = pygame.Vector2(self.arena_width / 2, self.arena_height / 2)
        for i in range(150):
            pos = pygame.Vector2(rng.uniform(80, self.arena_width - 80), rng.uniform(80, self.arena_height - 80))
            if (pos - center).length_squared() < 260**2:
                continue
            tx = int(pos.x // TILE_SIZE)
            ty = int(pos.y // TILE_SIZE)
            terrain_index = self._terrain_tile_index(tx, ty)
            if self.stage.tileset == "city" and terrain_index in (0, 1, 2, 6, 7):
                continue
            if self.stage.tileset == "jungle" and terrain_index in (3, 4, 8) and rng.random() < 0.72:
                continue
            if i % 5 == 0:
                kind = "obstacle"
            elif i % 5 == 1:
                kind = "debris"
            else:
                kind = "decor"
            decor.append((pos, kind, i))
        landmark_positions = self._landmark_positions()
        for index, (x_ratio, y_ratio) in enumerate(landmark_positions):
            decor.append((pygame.Vector2(self.arena_width * x_ratio, self.arena_height * y_ratio), "landmark", index))
        return decor

    def _landmark_positions(self) -> tuple[tuple[float, float], ...]:
        if self.stage.tileset == "city":
            return (
                (0.25, 0.21), (0.74, 0.22), (0.28, 0.40), (0.72, 0.40),
                (0.27, 0.63), (0.73, 0.64), (0.18, 0.83), (0.83, 0.81),
            )
        if self.stage.tileset == "jungle":
            return (
                (0.23, 0.20), (0.76, 0.23), (0.30, 0.42), (0.72, 0.45),
                (0.26, 0.65), (0.76, 0.63), (0.18, 0.82), (0.84, 0.80),
            )
        return (
            (0.38, 0.39), (0.62, 0.39), (0.38, 0.61), (0.62, 0.61),
            (0.17, 0.18), (0.82, 0.20), (0.16, 0.79), (0.84, 0.78),
        )

    def run(self, max_frames: int | None = None, auto_start: bool = False) -> bool:
        if auto_start:
            self.start_run()
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            if self.smoke:
                dt = 1.0 / FPS
            dt = min(dt, 0.05)

            if not self._handle_events():
                return True
            self.update(dt)
            self.draw()
            pygame.display.flip()

            self.frame_count += 1
            if max_frames is not None and self.frame_count >= max_frames:
                return self._smoke_assertions()
        return True

    async def run_async(self, max_frames: int | None = None, auto_start: bool = False) -> bool:
        if auto_start:
            self.start_run()
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            if self.smoke:
                dt = 1.0 / FPS
            dt = min(dt, 0.05)

            if not self._handle_events():
                return True
            self.update(dt)
            self.draw()
            pygame.display.flip()
            if self.frame_count == 0:
                import platform

                if hasattr(platform, "window"):
                    platform.window.eval(
                        'window.parent.postMessage("scrapstorm:ready", window.location.origin);'
                    )
            await asyncio.sleep(0)

            self.frame_count += 1
            if max_frames is not None and self.frame_count >= max_frames:
                return self._smoke_assertions()
        return True

    def _handle_events(self) -> bool:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.state == ScreenState.PLAYING:
                        self.state = ScreenState.PAUSED
                    elif self.state == ScreenState.PAUSED:
                        self.state = ScreenState.PLAYING
                    elif self.state in (ScreenState.TANK_SELECT, ScreenState.SHOP, ScreenState.UNLOCKS, ScreenState.RESEARCH, ScreenState.ACHIEVEMENTS, ScreenState.STAGE_SELECT):
                        self.state = ScreenState.MENU
                elif event.key == pygame.K_SPACE:
                    if self.state == ScreenState.MENU:
                        self.start_run()
                    elif self.state == ScreenState.PLAYING:
                        self.player.request_dash()
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER) and self.state == ScreenState.MENU:
                    self.start_run()
                elif event.key == pygame.K_r and self.state == ScreenState.GAME_OVER:
                    self.start_run()
                elif self.state == ScreenState.LEVEL_UP and event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                    self.select_upgrade(event.key - pygame.K_1)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.state == ScreenState.MENU:
                    buttons = self.ui.menu_button_rects()
                    if buttons["play"].collidepoint(event.pos):
                        self.start_run()
                    elif buttons["tanks"].collidepoint(event.pos):
                        self.state = ScreenState.TANK_SELECT
                    elif buttons["shop"].collidepoint(event.pos):
                        self.state = ScreenState.SHOP
                    elif buttons["achievements"].collidepoint(event.pos):
                        self.state = ScreenState.ACHIEVEMENTS
                        self.progression_tab = "achievements"
                    elif buttons["stages"].collidepoint(event.pos):
                        self.state = ScreenState.STAGE_SELECT
                    elif buttons["quit"].collidepoint(event.pos):
                        self.running = False
                elif self.state == ScreenState.TANK_SELECT:
                    if self.ui.back_rect().collidepoint(event.pos):
                        self.state = ScreenState.MENU
                    else:
                        tabs = self.ui.garage_tab_rects()
                        if tabs["tanks"].collidepoint(event.pos):
                            self.garage_tab = "tanks"
                        elif tabs["research"].collidepoint(event.pos):
                            self.garage_tab = "research"
                        elif tabs["gear"].collidepoint(event.pos):
                            self.garage_tab = "gear"
                        elif tabs["skill_tree"].collidepoint(event.pos):
                            self.garage_tab = "skill_tree"
                        else:
                            tab = getattr(self, "garage_tab", "tanks")
                            if tab == "tanks":
                                for tank_id, rect in self.ui.tank_card_rects().items():
                                    if rect.collidepoint(event.pos):
                                        self.choose_or_buy_tank(tank_id)
                                        break
                            elif tab == "research":
                                for category, rect in self.ui.research_filter_rects().items():
                                    if rect.collidepoint(event.pos):
                                        self.research_category = category
                                        break
                                else:
                                    for project_id, rect in self.ui.research_card_rects(self.research_category).items():
                                        if rect.collidepoint(event.pos):
                                            self.buy_research(project_id)
                                            break
                            elif tab == "gear":
                                self.handle_garage_clicks(event.pos)
                            elif tab == "skill_tree":
                                self.handle_skill_tree_clicks(event.pos)
                elif self.state == ScreenState.SHOP:
                    if self.ui.back_rect().collidepoint(event.pos):
                        self.state = ScreenState.MENU
                    else:
                        for upgrade_id, rect in self.ui.shop_row_rects().items():
                            if rect.collidepoint(event.pos):
                                self.buy_meta_upgrade(upgrade_id)
                                break
                elif self.state == ScreenState.UNLOCKS:
                    if self.ui.back_rect().collidepoint(event.pos):
                        self._acknowledge_unlocks()
                        self.state = ScreenState.MENU
                elif self.state == ScreenState.RESEARCH:
                    if self.ui.back_rect().collidepoint(event.pos):
                        self.state = ScreenState.MENU
                    else:
                        for project_id, rect in self.ui.research_card_rects().items():
                            if rect.collidepoint(event.pos):
                                self.buy_research(project_id)
                                break
                elif self.state == ScreenState.ACHIEVEMENTS:
                    if self.ui.back_rect().collidepoint(event.pos):
                        self.state = ScreenState.MENU
                    else:
                        for tab, rect in self.ui.progression_tab_rects().items():
                            if rect.collidepoint(event.pos):
                                self.progression_tab = tab
                                break
                        else:
                            if self.progression_tab == "achievements":
                                pages = self.ui.achievement_page_rects()
                                page_count = max(1, (len(ACHIEVEMENTS) + 11) // 12)
                                if pages["previous"].collidepoint(event.pos):
                                    self.achievement_page = max(0, self.achievement_page - 1)
                                elif pages["next"].collidepoint(event.pos):
                                    self.achievement_page = min(page_count - 1, self.achievement_page + 1)
                elif self.state == ScreenState.STAGE_SELECT:
                    if self.ui.back_rect().collidepoint(event.pos):
                        self.state = ScreenState.MENU
                    else:
                        for stage_id, rect in self.ui.stage_card_rects().items():
                            if rect.collidepoint(event.pos):
                                self.select_stage(stage_id)
                                break
                elif self.state == ScreenState.GAME_OVER:
                    if self.ui.game_over_restart_rect().collidepoint(event.pos):
                        self.start_run()
                    elif self.ui.game_over_menu_rect().collidepoint(event.pos):
                        self.state = ScreenState.MENU
                elif self.state == ScreenState.LEVEL_UP:
                    for idx, rect in enumerate(self.ui.level_card_rects(len(self.level_choices))):
                        if rect.collidepoint(event.pos):
                            self.select_upgrade(idx)
                            break
                elif self.state == ScreenState.PAUSED:
                    buttons = self.ui.pause_button_rects()
                    if buttons["resume"].collidepoint(event.pos):
                        self.state = ScreenState.PLAYING
                    elif buttons["menu"].collidepoint(event.pos):
                        self.abandon_run_to_menu()
                    elif buttons["quit"].collidepoint(event.pos):
                        self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3 and self.state == ScreenState.PLAYING:
                self.player.activate_special(self, self.screen_to_world(pygame.Vector2(event.pos)))
        return True

    def update(self, dt: float) -> None:
        self._update_shake(dt)
        self._update_transient_lists(dt)
        menu_states = (ScreenState.MENU, ScreenState.TANK_SELECT, ScreenState.SHOP, ScreenState.UNLOCKS, ScreenState.RESEARCH, ScreenState.ACHIEVEMENTS, ScreenState.STAGE_SELECT)
        if self.state in menu_states:
            self.menu_particles = [p for p in self.menu_particles if p.update(dt)]
            is_initially_empty = len(self.menu_particles) == 0
            while len(self.menu_particles) < 80:
                y_pos = random.uniform(0, SCREEN_HEIGHT) if is_initially_empty else random.uniform(SCREEN_HEIGHT, SCREEN_HEIGHT + 20)
                p = Particle(
                    pos=pygame.Vector2(random.uniform(0, SCREEN_WIDTH), y_pos),
                    vel=pygame.Vector2(random.uniform(-10, 10), random.uniform(-65, -130)),
                    color=random.choice((COLOR_CYAN, COLOR_MAGENTA, COLOR_AMBER, COLOR_GREEN)),
                    ttl=random.uniform(8.0, 15.0),
                    size=random.uniform(2, 5),
                )
                self.menu_particles.append(p)
        if self.state != ScreenState.PLAYING:
            return

        self.elemental_death_procs_this_frame = 0
        self.stats.time_survived += dt
        self._sync_survival_progress()
        self._update_contract_relay(dt)
        self._update_contract_timer()
        self._check_meta_loot_unlock()
        self.max_enemies = min(240, MAX_ENEMIES + int(self.stats.time_survived // 35) * 7)
        keys = pygame.key.get_pressed()
        mouse_world = self._smoke_target() if self.smoke else self.screen_to_world(pygame.Vector2(pygame.mouse.get_pos()))

        self.player.update(dt, keys, mouse_world, self)
        self.stats.min_health_pct = min(self.stats.min_health_pct, self.player.health / max(1.0, self.player.max_health))
        self.director.update(dt, self)
        for enemy in self.enemies:
            enemy.update(dt, self.player.pos, self)
            enemy.pos.x = max(enemy.radius, min(self.arena_width - enemy.radius, enemy.pos.x))
            enemy.pos.y = max(enemy.radius, min(self.arena_height - enemy.radius, enemy.pos.y))

        self._update_projectiles(dt)
        self._update_lingering_zones(dt)

        self.summons = [summon for summon in self.summons if summon.update(dt, self)]
        self.mines = [mine for mine in self.mines if mine.update(dt, self)]
        self._award_survival_coins()
        self._update_pickups(dt)
        self._handle_collisions()
        self._remove_dead_entities()
        self._update_camera(dt)

        if not self.player.alive:
            self.finish_run()
            self.state = ScreenState.GAME_OVER
            self.add_screen_shake(12, source_type="run_end")
            self.add_message("RUN TERMINATED", COLOR_RED)
        elif self.player.can_level():
            self._open_level_up()

    def _update_camera(self, dt: float) -> None:
        target = self.player.pos
        self.camera = self.camera.lerp(target, min(1.0, CAMERA_LERP * dt))

    def _update_shake(self, dt: float) -> None:
        if self.shake > 0:
            self.shake = max(0.0, self.shake - 36.0 * dt)
            amount = self.shake * 0.7
            self.shake_offset = pygame.Vector2(random.uniform(-amount, amount), random.uniform(-amount, amount))
        else:
            self.shake_offset.update(0, 0)

    def _update_transient_lists(self, dt: float) -> None:
        self.particles = [p for p in self.particles if p.update(dt)]
        self.damage_numbers = [n for n in self.damage_numbers if n.update(dt)][-MAX_DAMAGE_NUMBERS:]
        self.messages = [(text, ttl - dt, color) for text, ttl, color in self.messages if ttl > dt]
        self.passive_popups = [(passive, ttl - dt) for passive, ttl in self.passive_popups if ttl > dt]

    def _update_pickups(self, dt: float) -> None:
        kept: list[Pickup] = []
        magnet_radius = getattr(self.player, "effective_magnet_radius", self.player.magnet_radius)
        crowded_late = self.stats.time_survived >= 420 and len(self.pickups) >= 120
        for pickup in self.pickups:
            if crowded_late and pickup.kind in ("xp", "coin"):
                to_player = self.player.pos - pickup.pos
                if to_player.length_squared() > magnet_radius * magnet_radius and to_player.length_squared() < 620**2:
                    pickup.vel += to_player.normalize() * 85 * dt
            collected = pickup.update(dt, self.player.pos, magnet_radius)
            if collected:
                self._collect_pickup(pickup)
            else:
                kept.append(pickup)
        self.pickups = kept
        self._enforce_pickup_caps()

    def _collect_pickup(self, pickup: Pickup) -> None:
        if pickup.kind == "xp":
            self._advance_contract("xp", pickup.amount)
            self.player.gain_xp(max(1, int(round(pickup.amount * self.xp_multiplier * self.player.run_xp_bonus))))
            self.spawn_pickup_particles(pickup.pos, COLOR_CYAN)
            self.sounds.play("pickup")
        elif pickup.kind == "health":
            if getattr(self.player, "bloodless_harvest", False) and self.player.health >= self.player.max_health - 0.5:
                shield_cap = 22.0
                shield_gain = min(pickup.amount * 0.5, max(0.0, shield_cap - self.player.kinetic_barrier_shield))
                self.player.kinetic_barrier_shield += shield_gain
                if shield_gain < pickup.amount * 0.5:
                    self._award_run_coins(max(1, int(pickup.amount // 14)))
                self.spawn_pickup_particles(pickup.pos, COLOR_BLUE if shield_gain else COLOR_AMBER)
            else:
                self.player.heal(pickup.amount)
                self.spawn_pickup_particles(pickup.pos, COLOR_GREEN)
            self.sounds.play("pickup")
        elif pickup.kind == "coin":
            self._award_run_coins(pickup.amount)
            self.spawn_pickup_particles(pickup.pos, COLOR_AMBER)
            self.sounds.play("pickup")
        elif pickup.kind == "chest":
            self.spawn_pickup_particles(pickup.pos, COLOR_AMBER)
            self.sounds.play("pickup")
            self._open_loot_chest(quality=max(1, pickup.amount))

    def _handle_collisions(self) -> None:
        for projectile in self.projectiles:
            if projectile.source == "player" and projectile.alive:
                self._handle_player_projectile(projectile)
            elif projectile.source == "enemy" and projectile.alive:
                if (projectile.pos - self.player.pos).length_squared() <= (projectile.radius + self.player.radius) ** 2:
                    projectile.ttl = 0
                    if self.player.take_damage(projectile.damage):
                        self.sounds.play("hurt")
                        self.add_screen_shake(6, source_type="player_hit")
                        self.spawn_hurt_particles(self.player.pos)
                        self._after_player_damage()

        for enemy in self.enemies:
            delta = enemy.pos - self.player.pos
            min_dist = enemy.radius + self.player.radius
            dist_sq = delta.length_squared()
            if dist_sq <= min_dist**2:
                distance = dist_sq**0.5
                direction = delta.normalize() if distance > 0 else pygame.Vector2(1, 0)
                overlap = max(0.0, min_dist - distance)
                enemy.pos += direction * min(overlap + 2.0, 38.0)
                enemy.knockback += direction * (130 if enemy.boss else 220) * self.player.ram_knockback_mult
                if enemy.contact_cooldown <= 0:
                    enemy.contact_cooldown = 0.42
                    impact_damage = self._enemy_impact_damage(enemy)
                    enemy.take_damage(impact_damage, direction * (140 if enemy.boss else 260) * self.player.ram_knockback_mult)
                    self.spawn_hit_particles(enemy.pos, COLOR_AMBER)
                    if self.player.take_damage(enemy.contact_damage):
                        self.sounds.play("hurt")
                        self.add_screen_shake(5, source_type="player_hit")
                        self.spawn_hurt_particles(self.player.pos)
                        self._after_player_damage()

        self._handle_shield_drones()

    def _enemy_impact_damage(self, enemy: Enemy) -> float:
        base = (10.0 + self.player.bullet_damage * 0.45) * self.player.ram_damage_mult
        if enemy.boss:
            return max(6.0, base * 0.3)
        if enemy.max_health <= 30:
            return max(base, enemy.max_health + 1.0)
        if enemy.max_health <= 55:
            return max(base, enemy.max_health * 0.5)
        return max(base, enemy.max_health * 0.18)

    def _after_player_damage(self) -> None:
        if self.player.has_family_passive("Defense", 4) and self.player.defense_pulse_cooldown <= 0:
            self.player.defense_pulse_cooldown = 5.2
            self._knockback_pulse(self.player.pos, 155, 220)
            self.spawn_hit_particles(self.player.pos, COLOR_BLUE)
        if self.player.ice_barrier_level > 0 and self.player.ice_barrier_cooldown <= 0:
            self.player.ice_barrier_cooldown = max(4.2, 7.2 - self.player.ice_barrier_level)
            self._freeze_burst(self.player.pos, 130 + self.player.ice_barrier_level * 24, 1.0 + self.player.ice_barrier_level * 0.2)
            self.add_message("ICE BARRIER", COLOR_CYAN, ttl=1.2)

    def _knockback_pulse(self, pos: pygame.Vector2, radius: float, force: float) -> None:
        radius_sq = radius * radius
        for enemy in self.enemies:
            if not enemy.alive:
                continue
            delta = enemy.pos - pos
            if delta.length_squared() > radius_sq:
                continue
            direction = delta.normalize() if delta.length_squared() else pygame.Vector2(1, 0)
            enemy.knockback += direction * force

    def _freeze_burst(self, pos: pygame.Vector2, radius: float, duration: float) -> None:
        radius_sq = radius * radius
        for enemy in self.enemies:
            if enemy.alive and (enemy.pos - pos).length_squared() <= radius_sq:
                strength = 0.28 if enemy.boss else 0.42
                enemy.apply_slow(duration, strength)
                self.spawn_hit_particles(enemy.pos, COLOR_CYAN)

    def _handle_player_projectile(self, projectile: Projectile) -> None:
        for enemy in self.enemies:
            if not enemy.alive or id(enemy) in projectile.hits:
                continue
            if (projectile.pos - enemy.pos).length_squared() > (projectile.radius + enemy.radius) ** 2:
                continue

            direction = projectile.direction
            damage = projectile.damage * (1.0 + self.player.boss_damage_bonus if enemy.boss else 1.0)
            if projectile.distance_traveled >= 280 and getattr(self.player, "travel_damage_bonus", 0.0) > 0:
                damage *= 1.0 + self.player.travel_damage_bonus
            if enemy.slow_timer > 0 and (self.player.frostbite_level > 0 or self.player.has_family_passive("Cryo", 4)):
                damage *= 1.0 + min(0.24, 0.06 * self.player.frostbite_level + (0.08 if self.player.has_family_passive("Cryo", 4) else 0.0))
                if "absolute_zero" in self.player.evolutions:
                    damage *= 1.09 if enemy.boss else 1.18
            if enemy.poison_timer > 0 and enemy.dot_family == "Poison" and self.player.has_family_passive("Poison", 4):
                damage *= 1.08
            if projectile.serrated_bonus > 0 and projectile.hits:
                damage *= 1.0 + min(0.75, projectile.serrated_bonus)
            if projectile.corrosion_level > 0:
                enemy.apply_corrosion(projectile.corrosion_level)
            combo_triggered = False
            if projectile.dot_family == "Fire" and enemy.slow_timer > 0:
                damage *= 1.18
                combo_triggered = True
            if projectile.dot_family == "Fire" and enemy.conductive_timer > 0 and self.player.conductive_wildfire_level > 0:
                damage *= 1.0 + self.player.conductive_wildfire_level * 0.12
                combo_triggered = True
            if projectile.dot_family == "Poison":
                enemy.apply_conductive(3.6)
                if enemy.slow_timer > 0 and self.player.toxic_frostbite_level > 0:
                    damage *= 1.0 + self.player.toxic_frostbite_level * 0.11
                    combo_triggered = True
            if projectile.chain > 0 and enemy.conductive_timer > 0:
                damage *= 1.2
                projectile.chain += 1
                combo_triggered = True
            if combo_triggered:
                self.stats.elemental_combos += 1
            enemy.take_damage(damage, direction * projectile.knockback)
            killed_by_hit = enemy.health <= 0
            if projectile.slow_chance > 0 and self.random_chance(projectile.slow_chance):
                enemy.apply_slow(projectile.slow_duration, 0.35)
                self.spawn_hit_particles(enemy.pos, COLOR_CYAN)
            if projectile.freeze_burst_radius > 0:
                self._freeze_burst(enemy.pos, projectile.freeze_burst_radius, projectile.slow_duration)
            if projectile.poison_dps > 0:
                enemy.apply_poison(projectile.poison_dps, projectile.poison_duration, projectile.dot_family or "Poison")
            if projectile.kind == "turret" and "drone_lifesteal" in self.player.equipped_effects:
                self.player.heal(max(0.4, damage * 0.025))
            projectile.hits.add(id(enemy))
            self.spawn_hit_particles(projectile.pos, projectile.color)
            number_color = COLOR_AMBER if projectile.crit else COLOR_TEXT
            label = f"{int(damage)}!" if projectile.crit else str(int(damage))
            self.damage_numbers.append(DamageNumber(label, enemy.pos.copy(), number_color))

            if projectile.explosion_radius > 0:
                self._explode(projectile.pos, projectile.explosion_radius, damage * 0.65)
                if projectile.kind == "acid_glob":
                    self._spread_dot(
                        projectile.pos,
                        "Poison",
                        radius=projectile.explosion_radius,
                        dps=projectile.poison_dps,
                        duration=projectile.poison_duration,
                        limit=12,
                    )
                    if self.player.acid_mist_active or self.player.corrosive_burst_level > 0:
                        mist_radius = 76 + self.player.corrosive_burst_level * 14
                        self.add_lingering_zone(projectile.pos, "Poison", mist_radius, 2.4 + self.player.corrosive_burst_level * 0.4, projectile.poison_dps * 0.42)
                    if self.player.corrosive_burst_level > 0:
                        self._explode(projectile.pos, 28 + self.player.corrosive_burst_level * 8, damage * 0.18)
                if projectile.kind == "fireball" and projectile.poison_dps > 0:
                    self._spread_dot(
                        projectile.pos,
                        "Fire",
                        radius=projectile.explosion_radius,
                        dps=projectile.poison_dps,
                        duration=projectile.poison_duration,
                        limit=10,
                    )
                if "scrapstorm_detonator" in self.player.evolutions and projectile.kind not in ("split", "scrap_fragment"):
                    self._spawn_scrapstorm_fragments(projectile, damage)
            if projectile.chain > 0:
                self._chain_lightning(enemy, projectile.chain, damage * 0.48)
                if enemy.slow_timer > 0 and self.player.storm_shatter_level > 0:
                    self._explode(enemy.pos, 24 + self.player.storm_shatter_level * 8, damage * (0.16 + self.player.storm_shatter_level * 0.05))
            if self.player.has_family_passive("Lightning", 4):
                self.player.lightning_hit_counter += 1
                hit_threshold = max(5, 10 - self.player.arc_rounds_level - self.player.storm_battery_level)
                if self.player.lightning_hit_counter >= hit_threshold:
                    self.player.lightning_hit_counter = 0
                    bonus_chain = 2 if self.player.has_family_passive("Lightning", 6) else 1
                    self._chain_lightning(enemy, bonus_chain, damage * 0.34)
            if projectile.split > 0 and projectile.kind != "split":
                self._split_projectile(projectile)
            if killed_by_hit and projectile.volatile_chance > 0 and self.random_chance(projectile.volatile_chance):
                self._explode(enemy.pos, 42 + self.player.upgrade_counts["volatile_payload"] * 7, damage * 0.45)
            if killed_by_hit and projectile.crit and self.player.has_family_passive("Critical", 6):
                self.player.gain_xp(1)

            if projectile.pierce > 0:
                projectile.pierce -= 1
            else:
                projectile.ttl = 0
                break

    def _handle_shield_drones(self) -> None:
        if self.player.shield_drone_level <= 0:
            return
        drone_positions = self.player.shield_positions(self.stats.time_survived)
        for enemy in self.enemies:
            if not enemy.alive or enemy.shield_cooldown > 0:
                continue
            for pos in drone_positions:
                if (pos - enemy.pos).length_squared() <= (enemy.radius + 13) ** 2:
                    enemy.shield_cooldown = 0.22
                    direction = (enemy.pos - self.player.pos)
                    direction = direction.normalize() if direction.length_squared() else pygame.Vector2(1, 0)
                    damage = 18 + self.player.shield_drone_level * 7
                    enemy.take_damage(damage, direction * 180)
                    self.spawn_hit_particles(pos, COLOR_GREEN)
                    break

    def _explode(self, pos: pygame.Vector2, radius: float, damage: float) -> None:
        damage *= self.explosion_damage_multiplier
        self.add_screen_shake(min(10, 3 + radius * 0.08), source_type="large_explosion")
        self.spawn_explosion_particles(pos, radius)
        radius_sq = radius * radius
        for enemy in self.enemies:
            dist_sq = (enemy.pos - pos).length_squared()
            if enemy.alive and dist_sq <= radius_sq:
                max_falloff = max(0.52, 0.7 - getattr(self.player, "explosion_falloff_bonus", 0.0))
                falloff = 1.0 - min(max_falloff, (dist_sq**0.5) / max(1.0, radius))
                direction = enemy.pos - pos
                direction = direction.normalize() if direction.length_squared() else pygame.Vector2(1, 0)
                enemy.take_damage(damage * falloff, direction * (120 + radius))

    def _spawn_scrapstorm_fragments(self, projectile: Projectile, damage: float) -> None:
        base = projectile.direction
        for angle in (-55, -22, 22, 55):
            direction = base.rotate(angle)
            self.add_projectile(
                Projectile(
                    pos=projectile.pos.copy() + direction * 9,
                    vel=direction * max(360, projectile.vel.length() * 0.62),
                    radius=max(3, projectile.radius * 0.55),
                    damage=damage * 0.24,
                    source="player",
                    ttl=0.34,
                    pierce=0,
                    kind="scrap_fragment",
                    color=COLOR_AMBER,
                )
            )

    def _chain_lightning(self, first_enemy: Enemy, chain: int, damage: float) -> None:
        current = first_enemy
        hit_ids = {id(first_enemy)}
        chain_range = getattr(self.player, "lightning_chain_range", 175.0)
        storm_grid = "storm_grid" in self.player.evolutions
        max_arcs = 7 if storm_grid else 4
        arc_budget = chain + (1 if storm_grid else 0) + (1 if first_enemy.conductive_timer > 0 else 0)
        hits = 0
        while hits < min(max_arcs, arc_budget):
            hop_range = chain_range * (1.4 if current.conductive_timer > 0 else 1.0)
            candidates = [
                enemy
                for enemy in self.enemies
                if enemy.alive and id(enemy) not in hit_ids and (enemy.pos - current.pos).length_squared() < hop_range**2
            ]
            if not candidates:
                break
            target = min(candidates, key=lambda enemy: (enemy.pos - current.pos).length_squared())
            arc_damage = damage * (1.2 if target.conductive_timer > 0 else 1.0)
            if self.charged_wreckage_active:
                arc_damage *= 1.14
            target.take_damage(arc_damage, (target.pos - current.pos).normalize() * 90 if target.pos != current.pos else None)
            self.spawn_lightning_particles(current.pos, target.pos)
            if target.slow_timer > 0 and self.player.storm_shatter_level > 0:
                self._explode(target.pos, 22 + self.player.storm_shatter_level * 8, arc_damage * 0.24)
            hit_ids.add(id(target))
            if target.conductive_timer > 0:
                arc_budget = min(max_arcs, arc_budget + 1)
            current = target
            hits += 1
        if storm_grid and hits > 0:
            self.player.storm_grid_pulse_counter += 1
            if self.player.storm_grid_pulse_counter >= 4 and self.player.storm_grid_cooldown <= 0:
                self.player.storm_grid_pulse_counter = 0
                self.player.storm_grid_cooldown = 1.15
                self._storm_grid_pulse(current.pos, max(5.0, damage * 0.62))

    def _storm_grid_pulse(self, pos: pygame.Vector2, damage: float) -> None:
        radius = 150
        radius_sq = radius * radius
        candidates = [
            enemy
            for enemy in self.enemies
            if enemy.alive and (enemy.pos - pos).length_squared() <= radius_sq
        ]
        candidates.sort(key=lambda enemy: (enemy.pos - pos).length_squared())
        for target in candidates[:6]:
            direction = target.pos - pos
            knockback = direction.normalize() * 70 if direction.length_squared() else None
            target.take_damage(damage * (0.55 if target.boss else 1.0), knockback)
            self.spawn_lightning_particles(pos, target.pos)
        self.spawn_hit_particles(pos, COLOR_BLUE)

    def _split_projectile(self, projectile: Projectile) -> None:
        branches = min(4, 1 + projectile.split)
        base = projectile.direction
        angles = [-34, 34] if branches <= 2 else [-42, -18, 18, 42]
        for angle in angles[:branches]:
            direction = base.rotate(angle)
            self.add_projectile(
                Projectile(
                    pos=projectile.pos.copy() + direction * 8,
                    vel=direction * projectile.vel.length() * 0.82,
                    radius=max(3, projectile.radius * 0.72),
                    damage=projectile.damage * 0.48,
                    source="player",
                    ttl=0.42,
                    pierce=0,
                    kind="split",
                    explosion_radius=0,
                    split=0,
                    color=COLOR_MAGENTA,
                )
            )

    def _remove_dead_entities(self) -> None:
        for enemy in list(self.enemies):
            if enemy.alive:
                continue
            self._kill_enemy(enemy)
        self.enemies = [enemy for enemy in self.enemies if enemy.alive]
        self.projectiles = [
            projectile
            for projectile in self.projectiles
            if projectile.alive
            and -80 < projectile.pos.x < self.arena_width + 80
            and -80 < projectile.pos.y < self.arena_height + 80
        ]
        player_bullets = [p for p in self.projectiles if p.source == "player"]
        enemy_bullets = [p for p in self.projectiles if p.source == "enemy"]
        self.projectiles = player_bullets[-MAX_PLAYER_PROJECTILES:] + enemy_bullets[-MAX_ENEMY_PROJECTILES:]

    def _kill_enemy(self, enemy: Enemy) -> None:
        self._handle_elemental_death(enemy)
        enemy.health = -999
        self.stats.defeated += 1
        self.stats.score += enemy.score_value
        self._advance_contract("kills", 1)
        if enemy.elite:
            self._advance_contract("elites", 1)
        if enemy.kind == "fire_mote":
            self.spawn_explosion_particles(enemy.pos, 34)
            if (enemy.pos - self.player.pos).length_squared() <= 54**2 and self.player.take_damage(7):
                self.sounds.play("hurt")
                self.add_screen_shake(5, source_type="player_hit")
                self.spawn_hurt_particles(self.player.pos)
                self._after_player_damage()
        self._maybe_spawn_swarm_drone(enemy)
        self._maybe_drop_coin(enemy)
        if enemy.boss:
            self.stats.bosses_defeated += 1
            self._award_run_coins(8 + int(self.stats.time_survived // 180))
            self.add_screen_shake(14, source_type="boss_death")
            self.add_message("BOSS SCRAPPED", COLOR_AMBER)
        elif enemy.elite:
            self._award_run_coins(2)
            self.add_message("ELITE SCRAPPED +2 COINS", COLOR_MAGENTA)
        self._record_enemy_milestone(enemy)
        if enemy.boss and self.is_content_unlocked("anomaly_routes"):
            self.anomaly_route_available = True
            self.add_message("ANOMALY ROUTE SIGNAL DETECTED", COLOR_CYAN, ttl=3.0)
        self.sounds.play("boom")
        self.spawn_death_particles(enemy.pos, boss=enemy.boss)
        for _ in range(random.randint(3, 6)):
            vel = pygame.Vector2(random.uniform(-40, 40), random.uniform(-40, 40))
            color = random.choice(((90, 95, 110), (120, 130, 145), COLOR_MUTED))
            self._add_particle(enemy.pos.copy(), vel, color, random.uniform(1.5, 3.5), random.uniform(4, 8))
        self._drop_pickups(enemy)

    def _handle_elemental_death(self, enemy: Enemy) -> None:
        if self.elemental_death_procs_this_frame >= 8:
            return
        if enemy.dot_family == "Fire":
            if (
                "inferno_core" in self.player.evolutions
                and self.player.inferno_core_cooldown <= 0
                and self.elemental_death_procs_this_frame < 8
            ):
                self.player.inferno_core_cooldown = 0.18
                self.elemental_death_procs_this_frame += 1
                burst_damage = max(5.0, self.player.burn_dps * 0.75 + self.player.bullet_damage * 0.14)
                self._explode(enemy.pos, 48, burst_damage)
                self._spread_dot(
                    enemy.pos,
                    "Fire",
                    radius=128,
                    dps=max(4.0, self.player.burn_dps * 0.55),
                    duration=1.55 + self.player.fire_duration_bonus,
                    limit=3,
                )
            if (
                (self.player.wildfire_level > 0 or self.player.has_family_passive("Fire", 4))
                and self.elemental_death_procs_this_frame < 8
            ):
                chance = min(0.5, 0.18 + self.player.wildfire_level * 0.08 + (0.08 if self.player.has_family_passive("Fire", 4) else 0.0))
                if self.random_chance(chance):
                    self.elemental_death_procs_this_frame += 1
                    self._spread_dot(enemy.pos, "Fire", radius=145, dps=max(4.0, self.player.burn_dps * 0.65), duration=1.8 + self.player.fire_duration_bonus, limit=4)
            if (
                self.player.has_family_passive("Fire", 6)
                and self.elemental_death_procs_this_frame < 8
                and self.random_chance(0.35)
            ):
                self.elemental_death_procs_this_frame += 1
                self._explode(enemy.pos, 38, max(4.0, self.player.burn_dps * 0.55))
            if self.player.ash_collector_level > 0 and self.random_chance(0.08 + self.player.ash_collector_level * 0.05):
                pickup = Pickup("coin", enemy.pos.copy(), 1, radius=10)
                pickup.vel = pygame.Vector2(random.uniform(-80, 80), random.uniform(-80, 80))
                self._add_pickup(pickup)
        elif enemy.dot_family == "Poison":
            if (
                "plague_network" in self.player.evolutions
                and self.player.plague_network_cooldown <= 0
                and self.elemental_death_procs_this_frame < 8
            ):
                self.player.plague_network_cooldown = 0.3
                self.elemental_death_procs_this_frame += 1
                dps = max(5.5, self.player.poison_dps * 0.84)
                self._spread_dot(
                    enemy.pos,
                    "Poison",
                    radius=210,
                    dps=dps,
                    duration=3.2 + self.player.poison_duration_bonus,
                    limit=6,
                )
                self.spawn_hit_particles(enemy.pos, COLOR_GREEN)
            if (
                (self.player.plague_burst_level > 0 or self.player.has_family_passive("Poison", 6))
                and self.elemental_death_procs_this_frame < 8
            ):
                chance = min(0.64, 0.18 + self.player.plague_burst_level * 0.09 + (0.12 if self.player.has_family_passive("Poison", 6) else 0.0))
                if self.random_chance(chance):
                    self.elemental_death_procs_this_frame += 1
                    dps = max(3.8, self.player.poison_dps * (0.62 + self.player.acid_pool_level * 0.14))
                    self._spread_dot(enemy.pos, "Poison", radius=155 + self.player.acid_pool_level * 14, dps=dps, duration=2.7 + self.player.poison_duration_bonus, limit=4)
        if (
            enemy.slow_timer > 0
            and "absolute_zero" in self.player.evolutions
            and self.player.absolute_zero_cooldown <= 0
            and self.elemental_death_procs_this_frame < 8
        ):
            self.player.absolute_zero_cooldown = 0.22
            self.elemental_death_procs_this_frame += 1
            self._explode(enemy.pos, 42, max(6.0, self.player.bullet_damage * 0.28))
            self.spawn_hit_particles(enemy.pos, COLOR_CYAN)
        if (
            enemy.slow_timer > 0
            and self.player.shatter_freeze_level > 0
            and self.elemental_death_procs_this_frame < 8
            and self.random_chance(0.18 + self.player.shatter_freeze_level * 0.08)
        ):
            self.elemental_death_procs_this_frame += 1
            self._explode(enemy.pos, 34 + self.player.shatter_freeze_level * 8, max(5.0, self.player.bullet_damage * 0.22))
            self.spawn_hit_particles(enemy.pos, COLOR_CYAN)
        if (
            self.player.has_family_passive("Explosion", 6)
            and self.elemental_death_procs_this_frame < 8
            and not enemy.boss
            and self.random_chance(0.12)
        ):
            self.elemental_death_procs_this_frame += 1
            self._explode(enemy.pos, 28, max(4.0, self.player.bullet_damage * 0.18))

    def _spread_dot(
        self,
        pos: pygame.Vector2,
        family: str,
        *,
        radius: float,
        dps: float,
        duration: float,
        limit: int,
    ) -> None:
        color = COLOR_RED if family == "Fire" else COLOR_GREEN
        candidates = [
            enemy
            for enemy in self.enemies
            if enemy.alive and (enemy.pos - pos).length_squared() <= radius * radius
        ]
        candidates.sort(key=lambda target: (target.pos - pos).length_squared())
        for target in candidates[:limit]:
            target_dps = dps
            target_duration = duration
            if family == "Poison" and target.boss and "plague_network" in self.player.evolutions:
                target_dps *= 0.55
                target_duration = max(target_duration, 2.8)
            target.apply_poison(target_dps, target_duration, family)
            self.spawn_hit_particles(target.pos, color)

    def _maybe_spawn_swarm_drone(self, enemy: Enemy) -> None:
        level = getattr(self.player, "drone_swarm_level", 0)
        network_passive = self.player.has_family_passive("Summon", 6)
        if (level <= 0 and not network_passive) or enemy.boss:
            return
        effective_level = level + (1 if network_passive else 0)
        self.player.drone_swarm_kills += 1
        threshold = max(3, 7 - effective_level * 2)
        if self.player.drone_swarm_kills < threshold:
            return
        cap = 2 + effective_level * 2 + (2 if "drone_network" in self.player.evolutions else 0)
        self.player.drone_swarm_kills = 0
        if len(self.summons) >= cap:
            return
        offset = pygame.Vector2(random.uniform(-36, 36), random.uniform(-36, 36))
        self.add_mini_turret(enemy.pos + offset, max(0.24, self.player.engineer_turret_cooldown * 0.82))

    def _drop_pickups(self, enemy: Enemy) -> None:
        amount = enemy.xp_value
        if enemy.boss:
            chunks = 8
        elif amount >= 16:
            chunks = 3
        else:
            chunks = 1
        for i in range(chunks):
            value = max(1, amount // chunks)
            pickup = Pickup("xp", enemy.pos + pygame.Vector2(random.uniform(-12, 12), random.uniform(-12, 12)), value)
            pickup.vel = pygame.Vector2(random.uniform(-120, 120), random.uniform(-120, 120))
            self._add_pickup(pickup)
        if self.stage_pickup_density_bonus > 0 and random.random() < self.stage_pickup_density_bonus:
            bonus = Pickup("xp", enemy.pos + pygame.Vector2(random.uniform(-22, 22), random.uniform(-22, 22)), 1)
            bonus.vel = pygame.Vector2(random.uniform(-85, 85), random.uniform(-85, 85))
            self._add_pickup(bonus)
        hardy_kinds = {"brute", "medium_bruiser", "shield_carrier"}
        health_chance = 1.0 if enemy.boss else (0.42 if enemy.elite else (0.12 if enemy.kind in hardy_kinds else 0.045))
        health_chance += self.player.luck * 0.18
        if random.random() < health_chance:
            self._add_pickup(Pickup("health", enemy.pos.copy(), 18 if not enemy.boss else 40, radius=12))

        # Chest drop
        chest_chance = 0.006 + self.player.luck * 0.015
        chest_quality = 1
        if enemy.boss:
            chest_chance = 1.0
            chest_quality = 3
        elif getattr(enemy, "elemental_elite", False):
            chest_chance = 0.72 + self.player.luck * 0.05
            chest_quality = 2
        elif enemy.elite:
            chest_chance = 0.5 + self.player.luck * 0.05
            chest_quality = 2
        elif enemy.kind in hardy_kinds:
            chest_chance = 0.16 + self.player.luck * 0.06
            chest_quality = 2
        elif enemy.kind in ("shooter", "artillery_buggy", "poison_spitter", "lightning_node"):
            chest_chance += 0.025
        if "rare_chests" in self.player.equipped_effects:
            chest_chance += 0.04
        if self.player.has_family_passive("Economy", 6):
            chest_chance += 0.025
            if random.random() < 0.18:
                chest_quality += 1
            
        if random.random() < chest_chance:
            chest_pickup = Pickup("chest", enemy.pos.copy(), chest_quality, radius=14)
            chest_pickup.vel = pygame.Vector2(random.uniform(-60, 60), random.uniform(-60, 60))
            self._add_pickup(chest_pickup)

    def _maybe_drop_coin(self, enemy: Enemy) -> None:
        if enemy.boss:
            return
        chances = {
            "crawler": 0.025,
            "runner": 0.032,
            "brute": 0.12,
            "shooter": 0.09,
            "dash_scrapper": 0.045,
            "medium_bruiser": 0.12,
            "shield_carrier": 0.1,
            "mine_layer": 0.075,
            "drone_swarm": 0.018,
            "artillery_buggy": 0.105,
            "repair_node": 0.08,
            "fire_mote": 0.055,
            "cryo_crawler": 0.06,
            "poison_spitter": 0.08,
            "lightning_node": 0.08,
        }
        chance = chances.get(enemy.kind, 0.02) + self.player.luck * 0.08
        if random.random() < chance:
            pickup = Pickup("coin", enemy.pos.copy(), 1, radius=10)
            pickup.vel = pygame.Vector2(random.uniform(-95, 95), random.uniform(-95, 95))
            self._add_pickup(pickup)

    def _add_pickup(self, pickup: Pickup) -> None:
        if pickup.kind in PICKUP_MERGE_RADIUS:
            merge_radius_sq = PICKUP_MERGE_RADIUS[pickup.kind] ** 2
            nearest = None
            nearest_dist = merge_radius_sq
            for existing in self.pickups:
                if existing.kind != pickup.kind:
                    continue
                dist = (existing.pos - pickup.pos).length_squared()
                if dist <= nearest_dist:
                    nearest = existing
                    nearest_dist = dist
            if nearest is not None:
                total = nearest.amount + pickup.amount
                nearest.pos = nearest.pos.lerp(pickup.pos, pickup.amount / max(1, total))
                nearest.amount = total
                nearest.radius = min(18.0, max(nearest.radius, 10.0 + total * 0.08))
                nearest.vel = (nearest.vel + pickup.vel) * 0.45
                return
        self.pickups.append(pickup)
        self._enforce_pickup_caps()

    def _enforce_pickup_caps(self) -> None:
        for kind, cap in (("xp", XP_PICKUP_CAP), ("health", HEALTH_PICKUP_CAP), ("coin", COIN_PICKUP_CAP)):
            matching = [pickup for pickup in self.pickups if pickup.kind == kind]
            while len(matching) > cap:
                oldest = max(matching, key=lambda pickup: pickup.age)
                targets = [pickup for pickup in matching if pickup is not oldest]
                if targets:
                    target = min(targets, key=lambda pickup: (pickup.pos - oldest.pos).length_squared())
                    target.amount += oldest.amount
                    target.radius = min(18.0, max(target.radius, 10.0 + target.amount * 0.08))
                    target.pos = target.pos.lerp(oldest.pos, 0.25)
                self.pickups.remove(oldest)
                matching.remove(oldest)
        while len(self.pickups) > MAX_PICKUPS:
            mergeable = [pickup for pickup in self.pickups if pickup.kind in PICKUP_MERGE_RADIUS]
            if not mergeable:
                break
            oldest = max(mergeable, key=lambda pickup: pickup.age)
            targets = [pickup for pickup in mergeable if pickup is not oldest and pickup.kind == oldest.kind]
            if not targets:
                break
            target = min(targets, key=lambda pickup: (pickup.pos - oldest.pos).length_squared())
            target.amount += oldest.amount
            target.radius = min(18.0, max(target.radius, 10.0 + target.amount * 0.08))
            target.pos = target.pos.lerp(oldest.pos, 0.25)
            self.pickups.remove(oldest)

    def _award_survival_coins(self) -> None:
        while self.stats.time_survived >= self.next_survival_coin_time:
            base = 1 + int(self.stats.time_survived // 240)
            self._award_run_coins(base)
            self.add_message(f"+{base} SURVIVAL COIN", COLOR_AMBER, ttl=1.25)
            self.next_survival_coin_time += 45.0

    def _award_run_coins(self, base_amount: int) -> None:
        if base_amount <= 0:
            return
        raw = base_amount * self.coin_multiplier * self.player.run_coin_bonus
        amount = int(raw)
        if random.random() < raw - amount:
            amount += 1
        self.stats.run_coins += max(1, amount)

    def finish_run(self) -> None:
        if self.run_finalized:
            return
        self.run_finalized = True
        self.stats.banked_coins = self.stats.run_coins
        self.save_data["coins"] = int(self.save_data.get("coins", 0)) + self.stats.run_coins
        stats = self.save_data.setdefault("stats", {})
        stats["total_kills"] = int(stats.get("total_kills", 0)) + self.stats.defeated
        stats["total_bosses"] = int(stats.get("total_bosses", 0)) + self.stats.bosses_defeated
        stats["total_coins_earned"] = int(stats.get("total_coins_earned", 0)) + self.stats.run_coins
        stats["total_chests_opened"] = int(stats.get("total_chests_opened", 0)) + self.stats.chests_opened
        stats["total_gear_found"] = int(stats.get("total_gear_found", 0)) + self.stats.gear_found
        stats["total_unique_gear_found"] = int(stats.get("total_unique_gear_found", 0)) + self.stats.unique_gear_found
        stats["total_abilities_cast"] = int(stats.get("total_abilities_cast", 0)) + self.stats.abilities_cast
        stats["best_time"] = max(int(stats.get("best_time", 0)), int(self.stats.time_survived))
        stats["best_level"] = max(int(stats.get("best_level", 1)), self.player.level)
        stats["best_run_bosses"] = max(int(stats.get("best_run_bosses", 0)), self.stats.bosses_defeated)
        if self.stats.min_health_pct >= 0.25:
            stats["clean_run_time"] = max(int(stats.get("clean_run_time", 0)), int(self.stats.time_survived))
        tank_key = f"{self.stats.tank_used}_best_time"
        if tank_key in stats:
            stats[tank_key] = max(int(stats.get(tank_key, 0)), int(self.stats.time_survived))
        stats["unlocked_tank_count"] = len(set(self.save_data.get("unlocked_tanks", [])))
        if self.stats.time_survived >= LOOT_UNLOCK_SECONDS:
            self.save_data["loot_unlocked"] = True
        for achievement in evaluate_achievements(self.save_data):
            self.add_message(f"ACHIEVEMENT: {achievement.name.upper()}", COLOR_AMBER, ttl=3.4)
        self.save_manager.save(self.save_data)

    def abandon_run_to_menu(self) -> None:
        self.run_finalized = True
        self.reset_run()
        self.state = ScreenState.MENU
        self.add_message("RUN ABANDONED", COLOR_AMBER)

    def _open_level_up(self) -> None:
        healed = self.player.commit_level_up()
        self._convert_salvage_xp()
        if self.player.has_family_passive("Ability", 6):
            self.player.overclock_timer = max(self.player.overclock_timer, 4.0 + self.player.overclock_level)
        self.level_choices = choose_upgrades(self.player, tank_id=self.selected_tank_id)
        self.state = ScreenState.LEVEL_UP
        self.add_message(f"LEVEL {self.player.level}", COLOR_AMBER)
        if healed > 0:
            self.add_message(f"+{math.ceil(healed)} HP", COLOR_GREEN, ttl=1.35)
            self.damage_numbers.append(DamageNumber(f"+{math.ceil(healed)} HP", self.player.pos.copy(), COLOR_GREEN, ttl=0.9, start_ttl=0.9))
            self.spawn_heal_particles(self.player.pos)
        self.sounds.play("level")

    def _convert_salvage_xp(self) -> None:
        salvage_pct = getattr(self.player, "salvage_pct", 0.0)
        if salvage_pct <= 0 or self.player.xp <= 0:
            return
        converted_xp = int(self.player.xp * min(0.35, salvage_pct))
        if converted_xp <= 0:
            return
        self.player.xp -= converted_xp
        coins = max(1, converted_xp // 8)
        self._award_run_coins(coins)
        self.add_message(f"SALVAGE +{coins} COINS", COLOR_AMBER, ttl=1.5)

    def select_upgrade(self, idx: int) -> None:
        if idx < 0 or idx >= len(self.level_choices):
            return
        upgrade = self.level_choices[idx]
        evolution_messages = apply_upgrade(self.player, upgrade)
        evolution_unlocks = list(getattr(self.player, "last_evolution_unlocks", []))
        self._record_elemental_evolutions(evolution_unlocks)
        passive_unlocks = list(getattr(self.player, "last_passive_unlocks", []))
        self.add_message(upgrade.name.upper(), COLOR_CYAN)
        for message in evolution_messages:
            self.add_message(message, COLOR_AMBER, ttl=3.2)
            self.add_screen_shake(12, source_type="unique_activation")
            self.spawn_evolution_particles(self.player.pos)
        if upgrade.rarity == "evolution":
            self._queue_evolution_popup(upgrade)
        for evolution in evolution_unlocks:
            self._queue_evolution_popup(evolution)
        for passive in passive_unlocks:
            self._queue_passive_popup(passive)
        self.level_choices = []
        if self.player.can_level():
            self._open_level_up()
        else:
            self.state = ScreenState.PLAYING

    def _queue_passive_popup(self, passive: object) -> None:
        self.passive_popups.append((passive, 2.9))
        self.passive_popups = self.passive_popups[-3:]
        name = getattr(passive, "name", "Passive")
        family = getattr(passive, "family", "Build")
        self.add_message(f"{family.upper()} PASSIVE: {name.upper()}", COLOR_AMBER, ttl=2.4)

    def _queue_evolution_popup(self, evolution: object) -> None:
        self.passive_popups.append((evolution, 4.0))
        self.passive_popups = self.passive_popups[-3:]

    def choose_or_buy_tank(self, tank_id: str) -> None:
        tank = TANK_BY_ID.get(tank_id)
        if tank is None:
            return
        unlocked = set(self.save_data.get("unlocked_tanks", []))
        if tank_id in unlocked:
            self.save_data["selected_tank"] = tank_id
            self.selected_tank_id = tank_id
            self.save_manager.save(self.save_data)
            self.add_message(f"{tank.name.upper()} SELECTED", COLOR_CYAN)
            return
        coins = int(self.save_data.get("coins", 0))
        if coins >= tank.cost:
            self.save_data["coins"] = coins - tank.cost
            self.save_data.setdefault("unlocked_tanks", []).append(tank_id)
            self.save_data["unlocked_tanks"] = sorted(set(self.save_data["unlocked_tanks"]))
            self.save_data["selected_tank"] = tank_id
            self.selected_tank_id = tank_id
            self.save_data.setdefault("stats", {})["unlocked_tank_count"] = len(set(self.save_data["unlocked_tanks"]))
            for achievement in evaluate_achievements(self.save_data):
                self.add_message(f"ACHIEVEMENT: {achievement.name.upper()}", COLOR_AMBER, ttl=3.4)
            self.save_manager.save(self.save_data)
            self.add_message(f"{tank.name.upper()} UNLOCKED", COLOR_AMBER)
        else:
            self.add_message("NOT ENOUGH COINS", COLOR_RED)

    def buy_meta_upgrade(self, upgrade_id: str) -> None:
        upgrade = META_BY_ID.get(upgrade_id)
        if upgrade is None:
            return
        levels = self.save_data.setdefault("universal_upgrades", {})
        level = int(levels.get(upgrade_id, 0))
        cost = upgrade.cost_for_level(level)
        if cost is None:
            self.add_message("UPGRADE MAXED", COLOR_GREEN)
            return
        coins = int(self.save_data.get("coins", 0))
        if coins < cost:
            self.add_message("NOT ENOUGH COINS", COLOR_RED)
            return
        self.save_data["coins"] = coins - cost
        levels[upgrade_id] = level + 1
        stats = self.save_data.setdefault("stats", {})
        stats["upgrades_purchased"] = int(stats.get("upgrades_purchased", 0)) + 1
        for achievement in evaluate_achievements(self.save_data):
            self.add_message(f"ACHIEVEMENT: {achievement.name.upper()}", COLOR_AMBER, ttl=3.4)
        self.save_manager.save(self.save_data)
        self.add_message(f"{upgrade.name.upper()} +1", COLOR_AMBER)

    def select_stage(self, stage_id: str) -> None:
        stage = get_stage(stage_id)
        self.save_data["selected_stage"] = stage.id
        self.stage = stage
        self.save_manager.save(self.save_data)
        self.add_message(f"{stage.name.upper()} SELECTED", COLOR_CYAN)

    def handle_garage_clicks(self, pos: tuple[int, int]) -> None:
        equipped_gear = self.save_data.setdefault("equipped_gear", {"weapon": None, "armor": None, "trinket": None, "tracks": None})
        slot_rects = self.ui.equipment_slot_rects()
        
        # Unequip slots
        for slot, rect in slot_rects.items():
            if rect.collidepoint(pos):
                if equipped_gear.get(slot) is not None:
                    equipped_gear[slot] = None
                    apply_meta_upgrades(self.player, self.save_data)
                    self.save_manager.save(self.save_data)
                    self.add_message(f"UNEQUIPPED {slot.upper()}", COLOR_AMBER)
                return
                
        # Inventory slots
        inventory = self.save_data.setdefault("gear_inventory", [])

        for idx, rect in enumerate(self.ui.equipment_inventory_rects()):
            if rect.collidepoint(pos):
                if idx < len(inventory):
                    item = inventory[idx]
                    slot = item["type"]
                    equipped_gear[slot] = item["id"]
                    apply_meta_upgrades(self.player, self.save_data)
                    self.save_manager.save(self.save_data)
                    self.add_message(f"EQUIPPED {item['name'].upper()}", COLOR_GREEN)
                return

    def handle_skill_tree_clicks(self, pos: tuple[int, int]) -> None:
        selected_tank = self.save_data.get("selected_tank", "starter")
        for node_id, rect in self.ui.skill_tree_node_rects().items():
            if rect.collidepoint(pos):
                purchased, detail = unlock_skill_node(self.save_data, selected_tank, node_id)
                if purchased:
                    configure_player_tank(self.player, selected_tank)
                    apply_meta_upgrades(self.player, self.save_data)
                    self.save_manager.save(self.save_data)
                    self.add_message(f"SKILL LEARNED: {detail.upper()}", COLOR_GREEN)
                else:
                    self.add_message(detail.upper(), COLOR_RED)
                return
        if self.ui.skill_tree_refund_rect().collidepoint(pos):
            if refund_skill_tree(self.save_data, selected_tank):
                configure_player_tank(self.player, selected_tank)
                apply_meta_upgrades(self.player, self.save_data)
                self.save_manager.save(self.save_data)
                self.add_message("SKILL TREE REFUNDED", COLOR_AMBER)

    def _generate_random_gear_item(self, quality: int = 1, allow_unique: bool = False, boss_salvage: bool = False) -> dict[str, Any]:
        item_types = list(EQUIPMENT_SLOTS)
        item_type = random.choice(item_types)
        template = random.choice(EQUIPMENT_BY_SLOT[item_type])
        base_name = template.name
        
        quality = max(1, min(3, quality))
        luck_modifier = 1.0 + (self.player.Luck * 0.03) + (quality - 1) * 0.32
        if "rare_chests" in self.player.equipped_effects:
            luck_modifier += 0.25
            
        weights = [
            520 / luck_modifier,
            265,
            155 * luck_modifier,
            72 * luck_modifier,
            25 * luck_modifier,
            6 * luck_modifier
        ]
        if quality >= 3:
            weights[0] *= 0.18
            weights[1] *= 0.55
            weights[3] *= 1.45
            weights[4] *= 1.8
            weights[5] *= 2.3
        if boss_salvage:
            weights[2] *= 1.25
            weights[3] *= 1.4
            weights[4] *= 1.65
            weights[5] *= 1.8
        if not allow_unique:
            weights[5] = 0
        
        rarities = ["Common", "Uncommon", "Rare", "Epic", "Legendary", "Unique"]
        rarity = random.choices(rarities, weights=weights)[0]
        
        unique_effects = [
            "bullets_explode",
            "turret_lightning",
            "crit_burn",
            "impact_split",
            "sniper_freeze",
            "drone_lifesteal",
            "ricochet_double",
            "rare_chests",
            "low_hp_shield"
        ]
        
        effect = template.effect
        if rarity == "Unique":
            effect = random.choice(unique_effects)
            unique_names = {
                "bullets_explode": "Blastcore Array",
                "turret_lightning": "Tesla Coil",
                "crit_burn": "Igniter Valve",
                "impact_split": "Fission Core",
                "sniper_freeze": "Cryo Lens",
                "drone_lifesteal": "Siphon Drone",
                "ricochet_double": "Reflector Rib",
                "rare_chests": "Treasure Finder",
                "low_hp_shield": "Emergency Capacitor"
            }
            base_name = unique_names.get(effect, "Prototype Module")
        
        stats_pool = ["Strength", "Dexterity", "Vitality", "Tech", "Focus", "Luck"]
        stats_dict = dict(template.stats)
        
        num_stats = {
            "Common": 1,
            "Uncommon": 2,
            "Rare": 3,
            "Epic": 4,
            "Legendary": 5,
            "Unique": 2
        }[rarity]
        
        selected_stats = random.sample(stats_pool, min(num_stats, len(stats_pool)))
        for stat in selected_stats:
            val = {
                "Common": random.choice([1, 2]),
                "Uncommon": random.choice([2, 3]),
                "Rare": random.choice([3, 4, 5]),
                "Epic": random.choice([5, 6, 7]),
                "Legendary": random.choice([8, 9, 10, 12]),
                "Unique": random.choice([4, 5, 6])
            }[rarity]
            stats_dict[stat] = stats_dict.get(stat, 0) + val
            
        import uuid
        item_id = str(uuid.uuid4())[:8]
        
        return {
            "id": item_id,
            "name": base_name,
            "type": item_type,
            "rarity": rarity,
            "stats": stats_dict,
            "effect": effect,
            "template_id": template.id,
            "art_key": template.art_key,
        }

    def _generate_boss_relic(self) -> dict[str, Any]:
        import uuid

        relics = (
            ("Furnace Crown", "weapon", {"Strength": 5, "Focus": 4}),
            ("Glacier Governor", "armor", {"Vitality": 5, "Tech": 3}),
            ("Storm Reliquary", "trinket", {"Dexterity": 4, "Luck": 3}),
        )
        name, item_type, stats = random.choice(relics)
        return {
            "id": str(uuid.uuid4())[:8],
            "name": f"Boss Relic: {name}",
            "type": item_type,
            "rarity": "Rare",
            "stats": stats,
            "effect": "boss_relic_damage",
        }

    def _open_loot_chest(self, quality: int = 1) -> None:
        quality = max(1, min(3, quality))
        boss_chest = quality >= 3
        if self.player.chest_calibration_active and self.random_chance(0.16):
            quality = min(3, quality + 1)
        self.stats.chests_opened += 1
        self.save_data["lifetime_chests_opened"] = int(self.save_data.get("lifetime_chests_opened", 0)) + 1
        self._refresh_unlocks()
        is_unlocked = self.is_meta_loot_unlocked()
        
        if not is_unlocked:
            gold_amount = random.randint(8 + quality * 3, 18 + quality * 8)
            self._award_run_coins(gold_amount)
            self.add_message(f"CHEST: +{gold_amount} COINS (Meta loot locked)", COLOR_AMBER, ttl=2.0)
            self.sounds.play("pickup")
        else:
            roll = random.random()
            gear_chance = min(0.94, 0.54 + (quality - 1) * 0.16 + self.player.luck * 0.04 + self.player.gear_chest_bonus)
            if roll < gear_chance:
                relic_drop = boss_chest and self.is_content_unlocked("relic_prototypes") and self.random_chance(0.32)
                item = (
                    self._generate_boss_relic()
                    if relic_drop
                    else self._generate_random_gear_item(
                        quality=quality,
                        allow_unique=boss_chest and self.is_content_unlocked("relic_prototypes"),
                        boss_salvage=boss_chest and self.player.boss_salvage_tools_active,
                    )
                )
                inventory = self.save_data.setdefault("gear_inventory", [])
                if len(inventory) < 15:
                    inventory.append(item)
                    self.stats.gear_found += 1
                    if item["rarity"] == "Unique":
                        self.stats.unique_gear_found += 1
                    rarity_color = {
                        "Common": (200, 200, 200),
                        "Uncommon": (50, 220, 50),
                        "Rare": (50, 200, 255),
                        "Epic": (180, 50, 255),
                        "Legendary": (255, 180, 0),
                        "Unique": (255, 0, 255)
                    }.get(item["rarity"], COLOR_AMBER)
                    self.add_message(f"FOUND: {item['name'].upper()} ({item['rarity']})!", rarity_color, ttl=3.0)
                    self.save_manager.save(self.save_data)
                else:
                    gold_amount = random.randint(25, 45)
                    self._award_run_coins(gold_amount)
                    self.add_message(f"INVENTORY FULL! CONVERTED: +{gold_amount} COINS", COLOR_RED, ttl=2.5)
            else:
                gold_amount = random.randint(14 + quality * 4, 28 + quality * 9)
                self._award_run_coins(gold_amount)
                self.add_message(f"CHEST: +{gold_amount} COINS", COLOR_AMBER, ttl=2.0)
        for achievement in evaluate_achievements(self.save_data):
            self.add_message(f"ACHIEVEMENT: {achievement.name.upper()}", COLOR_AMBER, ttl=3.4)
        self.save_manager.save(self.save_data)

    def random_chance(self, chance: float) -> bool:
        return random.random() < max(0.0, min(1.0, chance))

    def spawn_enemy(
        self,
        kind: str,
        pos: pygame.Vector2,
        summoned: bool = False,
        boss_spawn: bool = False,
        elite: bool = False,
        elemental_affinity: str = "",
    ) -> None:
        if len(self.enemies) >= self.max_enemies and not (boss_spawn or elite):
            return
        health_mult, speed_mult = self.director.scaling(self.stats.time_survived)
        if summoned:
            health_mult *= 0.85
        enemy = create_enemy(kind, pos, health_mult, speed_mult * self.stage_enemy_speed_multiplier, elite=elite)
        if elemental_affinity:
            enemy.elemental_elite = True
            enemy.elemental_affinity = elemental_affinity
            enemy.max_health *= 1.14
            enemy.health *= 1.14
        if boss_spawn:
            if self.active_contract.id == "elite_hunt" and not self.contract_completed:
                self.contract_failed = True
                self.add_message("ELITE HUNT EXPIRED", COLOR_RED, ttl=2.8)
            self.add_message(f"{enemy.name.upper()} INBOUND", COLOR_RED, ttl=2.8)
            self.add_screen_shake(9, source_type="boss_spawn")
        elif elite:
            label = f"{elemental_affinity.upper()} ELITE SIGNAL" if elemental_affinity else "ELITE SIGNAL DETECTED"
            self.add_message(label, COLOR_MAGENTA, ttl=2.4)
            self.add_screen_shake(5, source_type="unique_activation")
        self.enemies.append(enemy)

    def add_projectile(self, projectile: Projectile) -> None:
        self.projectiles.append(projectile)

    def _update_contract_timer(self) -> None:
        if self.active_contract.kind == "time":
            relay_speed = 1.16 if self.player.relay_tools_active else 1.0
            self._advance_contract("time", int(self.stats.time_survived * relay_speed))

    def _advance_contract(self, kind: str, amount: int) -> None:
        if self.contract_completed or self.contract_failed or kind != self.active_contract.kind:
            return
        if kind == "time":
            self.contract_progress = max(self.contract_progress, amount)
        else:
            self.contract_progress += amount
        if self.player.salvage_momentum_level > 0:
            self.player.contract_momentum_timer = max(self.player.contract_momentum_timer, 2.4 + self.player.salvage_momentum_level * 0.45)
        if self.contract_progress < self.active_contract.goal:
            return
        self.contract_progress = self.active_contract.goal
        self.contract_completed = True
        self.stats.contracts_completed += 1
        blueprint_reward = 1
        if self.player.blueprint_analysis_active and self.contract_blueprint_analysis_available:
            self.contract_blueprint_analysis_available = False
            if self.random_chance(0.32):
                blueprint_reward += 1
                self.add_message("BLUEPRINT ANALYSIS: +1 FRAGMENT", COLOR_GREEN, ttl=2.5)
        if self.player.contract_blueprint_bonus_chance > 0 and self.random_chance(self.player.contract_blueprint_bonus_chance):
            blueprint_reward += 1
            self.add_message("FORTUNE CIRCUIT: +1 FRAGMENT", COLOR_GREEN, ttl=2.5)
        self.save_data["blueprint_fragments"] = int(self.save_data.get("blueprint_fragments", 0)) + blueprint_reward
        self._record_contract_completion()
        self.save_manager.save(self.save_data)
        self._award_run_coins(5 + self.player.contract_coin_bonus)
        chest = Pickup("chest", self.player.pos + pygame.Vector2(26, 0), 2, radius=14)
        chest.vel = pygame.Vector2(70, -80)
        self._add_pickup(chest)
        if self.player.blueprint_echo_level > 0:
            echo_xp = 4 + self.player.blueprint_echo_level * 3
            self.player.gain_xp(echo_xp)
            self.add_message(f"BLUEPRINT ECHO: +{echo_xp} XP", COLOR_CYAN, ttl=1.8)
        self.add_screen_shake(8, source_type="unique_activation")
        self.add_message(f"CONTRACT COMPLETE: +{blueprint_reward} BLUEPRINT", COLOR_AMBER, ttl=3.2)

    def begin_salvage_surge(self) -> None:
        self.add_message("SALVAGE SURGE: HOLD THE LINE", COLOR_MAGENTA, ttl=2.4)

    def complete_salvage_surge(self) -> None:
        self._record_surge_completion()
        self._advance_contract("surge", 1)
        self._award_run_coins(2)
        chest = Pickup("chest", self.player.pos + pygame.Vector2(-30, 0), 1, radius=14)
        chest.vel = pygame.Vector2(-60, -75)
        self._add_pickup(chest)
        self.add_message("SURGE CLEARED: +2 COINS", COLOR_AMBER, ttl=2.4)

    def add_mini_turret(self, pos: pygame.Vector2, cooldown: float) -> None:
        pos.x = max(34, min(self.arena_width - 34, pos.x))
        pos.y = max(34, min(self.arena_height - 34, pos.y))
        turret = MiniTurret(
            pygame.Vector2(pos),
            ttl=9.0 + self.player.engineer_turret_duration_bonus,
            fire_rate=max(1.1, 1.0 / max(0.18, cooldown)) * (1.0 + self.player.engineer_turret_rate_bonus),
            damage=max(6.0, self.player.bullet_damage * 0.58) * self.player.turret_damage_mult,
            bullet_speed=self.player.bullet_speed * 0.84,
            range_bonus=self.player.turret_range_bonus,
        )
        self.summons.append(turret)
        self.spawn_evolution_particles(turret.pos)

    def add_mine(self, pos: pygame.Vector2, level: int) -> None:
        pos.x = max(24, min(self.arena_width - 24, pos.x))
        pos.y = max(24, min(self.arena_height - 24, pos.y))
        self.mines.append(Mine(pygame.Vector2(pos), damage=42 + level * 22, radius=17 + level * 3))
        self.mines = self.mines[-MAX_MINES:]

    def explode_mine(self, mine: Mine) -> None:
        self._explode(mine.pos, 58 + mine.radius, mine.damage)
        self.spawn_explosion_particles(mine.pos, 56)
        self.add_screen_shake(7, source_type="large_explosion")

    def trigger_magnet_pulse(self, radius: float) -> None:
        radius_sq = radius * radius
        for pickup in self.pickups:
            to_player = self.player.pos - pickup.pos
            if to_player.length_squared() <= radius_sq and to_player.length_squared() > 1:
                pickup.vel += to_player.normalize() * 520
        self.spawn_pickup_particles(self.player.pos, COLOR_MAGENTA)

    def add_lingering_zone(self, pos: pygame.Vector2, family: str, radius: float, ttl: float, dps: float) -> None:
        self.lingering_zones.append({
            "pos": pygame.Vector2(pos),
            "family": family,
            "radius": float(radius),
            "ttl": float(ttl),
            "max_ttl": float(ttl),
            "dps": float(dps),
        })
        self.lingering_zones = self.lingering_zones[-8:]

    def _update_lingering_zones(self, dt: float) -> None:
        active: list[dict[str, Any]] = []
        for zone in self.lingering_zones:
            zone["ttl"] -= dt
            if zone["ttl"] <= 0:
                continue
            radius_sq = zone["radius"] ** 2
            for enemy in self.enemies:
                if not enemy.alive or (enemy.pos - zone["pos"]).length_squared() > radius_sq:
                    continue
                if zone["family"] == "Cryo":
                    enemy.apply_slow(0.28, 0.32)
                elif zone["family"] == "Poison":
                    tick_scale = 1.0 + self.player.poison_tick_speed_bonus
                    enemy.apply_poison(max(3.0, zone["dps"] * tick_scale), 0.42, "Poison")
            active.append(zone)
        self.lingering_zones = active

    def trigger_ability_variant(self, mouse_world: pygame.Vector2, level: int) -> None:
        """A lightweight chassis-specific echo unlocked by Variant Protocol."""
        target = pygame.Vector2(mouse_world)
        target.x = max(60, min(self.arena_width - 60, target.x))
        target.y = max(60, min(self.arena_height - 60, target.y))
        strength = max(1, level)
        if self.player.tank_id == "flame_caster":
            self._explode(target, 34 + strength * 12, self.player.bullet_damage * (0.42 + strength * 0.08))
        elif self.player.tank_id == "cryo":
            self._freeze_burst(target, 58 + strength * 12, 0.72 + strength * 0.12)
        elif self.player.tank_id == "poison":
            self._spread_dot(target, "Poison", 72 + strength * 12, max(4.0, self.player.poison_dps * 0.48), 1.5 + strength * 0.3, 5)
        elif self.player.tank_id == "lightning" and self.enemies:
            first = min(self.enemies, key=lambda enemy: (enemy.pos - target).length_squared())
            self._chain_lightning(first, 1 + strength, self.player.bullet_damage * 0.5)
        else:
            for angle in (-18, 18):
                direction = self.player.aim_dir.rotate(angle)
                self.add_projectile(self.player._make_projectile(direction, self, damage_scale=0.45, chain=0, side=True))
        self.spawn_hit_particles(target, COLOR_MAGENTA)
        self.add_message("ABILITY VARIANT ECHO", COLOR_MAGENTA, ttl=1.1)

    def _update_projectiles(self, dt: float) -> None:
        for projectile in self.projectiles:
            projectile.update(dt)
            if projectile.source != "player" or projectile.bounces <= 0:
                continue
            bounced = False
            if projectile.pos.x < projectile.radius:
                projectile.pos.x = projectile.radius
                projectile.vel.x = abs(projectile.vel.x)
                bounced = True
            elif projectile.pos.x > self.arena_width - projectile.radius:
                projectile.pos.x = self.arena_width - projectile.radius
                projectile.vel.x = -abs(projectile.vel.x)
                bounced = True
            if projectile.pos.y < projectile.radius:
                projectile.pos.y = projectile.radius
                projectile.vel.y = abs(projectile.vel.y)
                bounced = True
            elif projectile.pos.y > self.arena_height - projectile.radius:
                projectile.pos.y = self.arena_height - projectile.radius
                projectile.vel.y = -abs(projectile.vel.y)
                bounced = True
            if bounced:
                projectile.bounces -= 1
                projectile.hits.clear()
                self.spawn_hit_particles(projectile.pos, COLOR_CYAN)

    def add_screen_shake(self, amount: float, duration: float | None = None, source_type: str = "generic") -> None:
        del duration
        cap = SHAKE_CAPS.get(source_type, SHAKE_CAPS["generic"])
        if cap <= 0:
            return
        self.shake = max(self.shake, min(amount, cap) * SHAKE_SCALE)

    def add_message(self, text: str, color: tuple[int, int, int], ttl: float = 2.0) -> None:
        self.messages.append((text, ttl, color))
        self.messages = self.messages[-5:]

    def spawn_muzzle_particles(self, pos: pygame.Vector2, direction: pygame.Vector2, rocket: bool = False) -> None:
        color = COLOR_AMBER if rocket else COLOR_CYAN
        self.sounds.play("shoot")
        for _ in range(5 if not rocket else 9):
            vel = direction.rotate(random.uniform(-34, 34)) * random.uniform(60, 210)
            self._add_particle(pos.copy(), vel, color, random.uniform(0.08, 0.18), random.uniform(2, 4))

    def spawn_hit_particles(self, pos: pygame.Vector2, color: tuple[int, int, int]) -> None:
        for _ in range(6):
            vel = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1))
            if vel.length_squared():
                vel = vel.normalize() * random.uniform(55, 170)
            self._add_particle(pos.copy(), vel, color, random.uniform(0.12, 0.26), random.uniform(2, 5))

    def spawn_hurt_particles(self, pos: pygame.Vector2) -> None:
        for _ in range(13):
            vel = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1))
            if vel.length_squared():
                vel = vel.normalize() * random.uniform(80, 230)
            self._add_particle(pos.copy(), vel, COLOR_RED, random.uniform(0.18, 0.38), random.uniform(3, 6))

    def spawn_heal_particles(self, pos: pygame.Vector2) -> None:
        for _ in range(12):
            vel = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 0))
            if vel.length_squared():
                vel = vel.normalize() * random.uniform(45, 135)
            self._add_particle(pos.copy(), vel, COLOR_GREEN, random.uniform(0.22, 0.46), random.uniform(2, 5))

    def spawn_death_particles(self, pos: pygame.Vector2, boss: bool = False) -> None:
        count = 44 if boss else 15
        for _ in range(count):
            vel = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1))
            if vel.length_squared():
                vel = vel.normalize() * random.uniform(80, 330 if boss else 210)
            color = random.choice((COLOR_AMBER, COLOR_MAGENTA, COLOR_CYAN, COLOR_RED))
            self._add_particle(pos.copy(), vel, color, random.uniform(0.25, 0.62), random.uniform(3, 7 if boss else 5))

    def spawn_explosion_particles(self, pos: pygame.Vector2, radius: float) -> None:
        for _ in range(min(38, int(radius * 0.55))):
            angle = random.random() * math.tau
            vel = pygame.Vector2(math.cos(angle), math.sin(angle)) * random.uniform(80, 310)
            self._add_particle(pos.copy(), vel, random.choice((COLOR_AMBER, COLOR_RED, COLOR_MAGENTA)), 0.35, random.uniform(3, 7))

    def spawn_lightning_particles(self, start: pygame.Vector2, end: pygame.Vector2) -> None:
        steps = 6
        for i in range(steps):
            pos = start.lerp(end, i / max(1, steps - 1))
            pos += pygame.Vector2(random.uniform(-8, 8), random.uniform(-8, 8))
            self._add_particle(pos, pygame.Vector2(), COLOR_CYAN, 0.13, 4)

    def spawn_pickup_particles(self, pos: pygame.Vector2, color: tuple[int, int, int]) -> None:
        for _ in range(4):
            vel = pygame.Vector2(random.uniform(-60, 60), random.uniform(-60, 60))
            self._add_particle(pos.copy(), vel, color, 0.2, 3)

    def spawn_dash_particles(self, pos: pygame.Vector2, direction: pygame.Vector2) -> None:
        for _ in range(16):
            vel = direction.rotate(random.uniform(-45, 45)) * random.uniform(120, 360)
            self._add_particle(pos.copy(), vel, COLOR_CYAN, 0.22, 4)

    def spawn_evolution_particles(self, pos: pygame.Vector2) -> None:
        for i in range(60):
            angle = i * math.tau / 60
            vel = pygame.Vector2(math.cos(angle), math.sin(angle)) * random.uniform(100, 260)
            self._add_particle(pos.copy(), vel, random.choice((COLOR_CYAN, COLOR_AMBER, COLOR_MAGENTA)), 0.55, 5)

    def _add_particle(
        self,
        pos: pygame.Vector2,
        vel: pygame.Vector2,
        color: tuple[int, int, int],
        ttl: float,
        size: float,
    ) -> None:
        if len(self.particles) >= MAX_PARTICLES:
            self.particles.pop(0)
        self.particles.append(Particle(pos, vel, color, ttl, size))

    def draw(self) -> None:
        self.screen.fill(COLOR_BG)
        menu_states = (ScreenState.MENU, ScreenState.TANK_SELECT, ScreenState.SHOP, ScreenState.UNLOCKS, ScreenState.RESEARCH, ScreenState.ACHIEVEMENTS, ScreenState.STAGE_SELECT)
        if self.state in menu_states:
            for p in self.menu_particles:
                size = max(1, int(p.size))
                color = (*p.color, p.alpha)
                pygame.draw.rect(self.screen, color, pygame.Rect(int(p.pos.x), int(p.pos.y), size, size))
            if self.state == ScreenState.MENU:
                self.ui.draw_menu(self.screen, self)
            elif self.state == ScreenState.TANK_SELECT:
                self.ui.draw_tank_select(self.screen, self)
            elif self.state == ScreenState.SHOP:
                self.ui.draw_shop(self.screen, self)
            elif self.state == ScreenState.UNLOCKS:
                self.ui.draw_unlocks(self.screen, self)
            elif self.state == ScreenState.RESEARCH:
                self.ui.draw_research(self.screen, self)
            elif self.state == ScreenState.ACHIEVEMENTS:
                self.ui.draw_achievements(self.screen, self)
            elif self.state == ScreenState.STAGE_SELECT:
                self.ui.draw_stage_select(self.screen, self)
            self._draw_messages()
        else:
            self._draw_world()
            self.ui.draw_hud(self.screen, self)
            self._draw_messages()
            if self.state == ScreenState.PAUSED:
                self.ui.draw_pause(self.screen, self)
            elif self.state == ScreenState.LEVEL_UP:
                self.ui.draw_level_up(self.screen, self, self.level_choices)
            elif self.state == ScreenState.GAME_OVER:
                self.ui.draw_game_over(self.screen, self)
            if self.state != ScreenState.PAUSED:
                self.ui.draw_passive_popups(self.screen, self)

    def _draw_world(self) -> None:
        self._draw_background()
        self._draw_map_decor()
        self._draw_contract_relay()
        self._draw_lingering_zones()
        for pickup in self.pickups:
            self._draw_pickup(pickup)
        for mine in self.mines:
            self._draw_mine(mine)
        for projectile in self.projectiles:
            self._draw_projectile(projectile)
        for summon in self.summons:
            self._draw_summon(summon)
        for enemy in self.enemies:
            self._draw_enemy(enemy)
        self._draw_player()
        self._draw_particles()
        self._draw_damage_numbers()

    @staticmethod
    def _terrain_noise(tx: int, ty: int, salt: int = 0) -> int:
        value = (tx * 0x45D9F3B + ty * 0x119DE1F3 + salt * 0x27D4EB2D) & 0xFFFFFFFF
        value ^= value >> 16
        value = (value * 0x45D9F3B) & 0xFFFFFFFF
        return value ^ (value >> 16)

    def _city_terrain_index(self, tx: int, ty: int) -> int:
        columns = max(1, self.arena_width // TILE_SIZE)
        rows = max(1, self.arena_height // TILE_SIZE)
        avenue_x = columns // 2
        plaza_y = rows // 2
        avenue_distance = abs(tx - avenue_x)
        plaza_distance = abs(ty - plaza_y)

        # A single broad avenue gives City a readable combat lane.  The lane
        # markings stay on the vertical road, where their source-art direction
        # remains correct; the crossing becomes a concrete civic plaza instead
        # of another conflicting road stripe.
        if avenue_distance <= 2:
            if avenue_distance == 0 and plaza_distance == 0:
                return 6
            if avenue_distance == 0 and abs(ty - plaza_y) % 5 == 0:
                return 7
            road_noise = self._terrain_noise(tx, ty // 2, 3) % 13
            return 2 if road_noise == 0 else (0 if road_noise < 7 else 1)
        if avenue_distance == 3:
            return 5

        # The plaza cuts across the avenue as a calm concrete landmark rather
        # than a second set of repeated lane markings.
        if plaza_distance <= 3 and 10 < tx < columns - 10:
            if plaza_distance == 3:
                return 5
            return 3 if self._terrain_noise(tx // 2, ty, 7) % 3 else 4

        # A short maintenance route and construction pocket break up the
        # districts without turning the whole arena into a tiled grid.
        service_y = max(8, rows // 4)
        if abs(ty - service_y) <= 1 and 8 < tx < avenue_x - 8:
            return 9 if ty == service_y else 5
        construction_x = int(columns * 0.77)
        construction_y = int(rows * 0.34)
        if ((tx - construction_x) / 5.5) ** 2 + ((ty - construction_y) / 3.5) ** 2 < 1:
            return 8 if self._terrain_noise(tx, ty, 11) % 4 else 4

        district_noise = self._terrain_noise(tx // 5, ty // 5, 17) % 12
        if district_noise == 0:
            return 2
        return 3 if district_noise < 8 else 4

    def _jungle_terrain_index(self, tx: int, ty: int) -> int:
        columns = max(1, self.arena_width // TILE_SIZE)
        rows = max(1, self.arena_height // TILE_SIZE)
        trail_x = columns * 0.50 + math.sin(ty * 0.17) * 3.4 + math.sin(ty * 0.055) * 1.6
        trail_distance = abs(tx - trail_x)
        plaza_x = abs(tx - columns * 0.50)
        plaza_y = abs(ty - rows * 0.49)
        in_ruin_plaza = plaza_x <= 5.5 and plaza_y <= 4.0 and plaza_x + plaza_y * 0.55 <= 7.0

        # A winding root trail and a small ruin clearing establish a deliberate
        # route through the basin instead of repeating every floor variant.
        if in_ruin_plaza:
            return 4
        if trail_distance <= 0.65:
            return 8
        if trail_distance <= 1.7:
            return 3

        wetlands = (
            (columns * 0.23, rows * 0.62, 9.5, 6.0),
            (columns * 0.76, rows * 0.30, 8.0, 5.0),
        )
        for center_x, center_y, radius_x, radius_y in wetlands:
            depth = ((tx - center_x) / radius_x) ** 2 + ((ty - center_y) / radius_y) ** 2
            if depth < 1:
                return 7 if depth > 0.72 and self._terrain_noise(tx, ty, 23) % 5 == 0 else 6

        moss_patches = (
            (columns * 0.28, rows * 0.25, 8.5, 5.0),
            (columns * 0.72, rows * 0.73, 10.0, 5.5),
        )
        for center_x, center_y, radius_x, radius_y in moss_patches:
            if ((tx - center_x) / radius_x) ** 2 + ((ty - center_y) / radius_y) ** 2 < 1:
                return 2

        canopy_noise = self._terrain_noise(tx // 4, ty // 4, 29) % 14
        if canopy_noise == 0:
            return 5
        if canopy_noise < 3:
            return 2
        return 0 if canopy_noise < 10 else 1

    def _terrain_tile_index(self, tx: int, ty: int) -> int:
        if self.stage.tileset == "city":
            return self._city_terrain_index(tx, ty)
        if self.stage.tileset == "jungle":
            return self._jungle_terrain_index(tx, ty)
        return tx * 17 + ty * 9

    def _draw_background(self) -> None:
        start_x = int((self.camera.x - SCREEN_WIDTH / 2) // TILE_SIZE) - 1
        end_x = int((self.camera.x + SCREEN_WIDTH / 2) // TILE_SIZE) + 2
        start_y = int((self.camera.y - SCREEN_HEIGHT / 2) // TILE_SIZE) - 1
        end_y = int((self.camera.y + SCREEN_HEIGHT / 2) // TILE_SIZE) + 2
        floor_base = {
            "scrap": (29, 32, 38),
            "desert": (182, 135, 73),
            "frozen": (84, 145, 171),
            "city": (45, 48, 68),
            "jungle": (39, 78, 52),
        }[self.stage.tileset]
        for tx in range(start_x, end_x):
            for ty in range(start_y, end_y):
                world = pygame.Vector2(tx * TILE_SIZE, ty * TILE_SIZE)
                screen = self.world_to_screen(world)
                floor_tiles = self.assets.tilesets[self.stage.tileset]["floor"]
                tile = floor_tiles[self._terrain_tile_index(tx, ty) % len(floor_tiles)]
                pygame.draw.rect(self.screen, floor_base, pygame.Rect(int(screen.x), int(screen.y), TILE_SIZE, TILE_SIZE))
                self.screen.blit(tile, (int(screen.x), int(screen.y)))

        arena = pygame.Rect(0, 0, self.arena_width, self.arena_height)
        top_left = self.world_to_screen(pygame.Vector2(arena.topleft))
        rect = pygame.Rect(int(top_left.x), int(top_left.y), self.arena_width, self.arena_height)
        pygame.draw.rect(self.screen, (0, 0, 0), rect, 16)
        border_color = {"scrap": COLOR_MAGENTA, "desert": COLOR_AMBER, "frozen": COLOR_CYAN, "city": COLOR_MAGENTA, "jungle": COLOR_GREEN}[self.stage.tileset]
        pygame.draw.rect(self.screen, border_color, rect, 3)

    def _draw_map_decor(self) -> None:
        decor_tiles = self.assets.tilesets[self.stage.tileset]["decor"]
        obstacle_tiles = self.assets.tilesets[self.stage.tileset]["obstacle"]
        for pos, kind, idx in self.map_decor:
            screen = self.world_to_screen(pos)
            if -160 <= screen.x <= SCREEN_WIDTH + 160 and -160 <= screen.y <= SCREEN_HEIGHT + 160:
                if kind == "landmark":
                    landmarks = self.assets.landmarks.get(self.stage.id, [])
                    if not landmarks:
                        continue
                    image = landmarks[idx % len(landmarks)]
                else:
                    tiles = decor_tiles if kind in ("decor", "debris") else obstacle_tiles
                    image = tiles[idx % len(tiles)]
                self.screen.blit(image, image.get_rect(center=(int(screen.x), int(screen.y))))

    def _draw_contract_relay(self) -> None:
        if self.player.relay_overcharge_level <= 0:
            return
        pos = self.world_to_screen(self.contract_relay_pos)
        radius = 15 + int(4 * math.sin(self.stats.time_survived * 4))
        pygame.draw.circle(self.screen, (8, 22, 30), (int(pos.x), int(pos.y)), 34)
        pygame.draw.circle(self.screen, COLOR_CYAN, (int(pos.x), int(pos.y)), 30, 2)
        pygame.draw.circle(self.screen, COLOR_MAGENTA if self.player.relay_next_shot_boost > 0 else COLOR_CYAN, (int(pos.x), int(pos.y)), max(7, radius))
        if (self.player.pos - self.contract_relay_pos).length_squared() <= 145**2:
            pygame.draw.arc(self.screen, COLOR_AMBER, pygame.Rect(int(pos.x - 25), int(pos.y - 25), 50, 50), -math.pi / 2, -math.pi / 2 + math.tau * self.player.relay_charge, 3)

    def _draw_lingering_zones(self) -> None:
        colors = {"Cryo": COLOR_CYAN, "Poison": COLOR_GREEN}
        for zone in self.lingering_zones:
            pos = self.world_to_screen(zone["pos"])
            radius = int(zone["radius"])
            overlay = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
            color = colors.get(zone["family"], COLOR_MAGENTA)
            alpha = int(52 * max(0.15, zone["ttl"] / max(0.1, zone["max_ttl"])))
            pygame.draw.circle(overlay, (*color, alpha), (radius + 2, radius + 2), radius)
            pygame.draw.circle(overlay, (*color, min(210, alpha + 90)), (radius + 2, radius + 2), radius, 2)
            self.screen.blit(overlay, (int(pos.x - radius - 2), int(pos.y - radius - 2)))

    def _draw_pickup(self, pickup: Pickup) -> None:
        key = pickup.kind
        if key == "chest":
            key = "chest_boss" if pickup.amount >= 3 else "chest_basic"
        key = key if key in self.assets.sprites else "xp"
        bob = math.sin(pickup.age * 8) * 2
        image = self.assets.sprites[key]
        # Generated source art is intentionally high resolution for clean UI reuse;
        # XP drops must remain visually aligned with their 10px world pickup radius.
        if pickup.kind == "xp":
            image = pygame.transform.scale(image, (XP_PICKUP_DRAW_SIZE, XP_PICKUP_DRAW_SIZE))
        pos = self.world_to_screen(pickup.pos + pygame.Vector2(0, bob))
        self.screen.blit(image, image.get_rect(center=(int(pos.x), int(pos.y))))

    def _draw_projectile(self, projectile: Projectile) -> None:
        if projectile.source == "enemy":
            key = ENEMY_PROJECTILE_SPRITES.get(projectile.kind, "enemy_bullet")
            if key not in self.assets.sprites:
                key = "enemy_bullet"
            base_radius = 14.0 if key.startswith("effect_") else 8.0
            scale = max(0.45, min(1.1, projectile.radius / base_radius))
            image = self.assets.scaled_rotated(key, projectile.direction, scale)
        else:
            key = "bullet"
            if projectile.kind == "rocket":
                key = "bullet_rocket"
            elif projectile.kind == "sniper":
                key = "sniper_bullet"
            elif projectile.kind == "turret":
                key = "turret_bullet"
            scale = max(0.75, projectile.radius / 5.0)
            image = self.assets.scaled_rotated(key, projectile.direction, scale)
        pos = self.world_to_screen(projectile.pos)
        self.screen.blit(image, image.get_rect(center=(int(pos.x), int(pos.y))))

    def _draw_summon(self, summon: MiniTurret) -> None:
        image = self.assets.sprites["mini_turret"]
        pos = self.world_to_screen(summon.pos)
        self.screen.blit(image, image.get_rect(center=(int(pos.x), int(pos.y))))
        pct = max(0.0, min(1.0, summon.ttl / 9.0))
        rect = pygame.Rect(int(pos.x - 14), int(pos.y + 17), 28, 4)
        pygame.draw.rect(self.screen, (0, 0, 0), rect.inflate(2, 2))
        fill = rect.copy()
        fill.width = int(rect.width * pct)
        pygame.draw.rect(self.screen, COLOR_GREEN, fill)

    def _draw_mine(self, mine: Mine) -> None:
        image = self.assets.sprites["mine"]
        pos = self.world_to_screen(mine.pos)
        self.screen.blit(image, image.get_rect(center=(int(pos.x), int(pos.y))))
        if mine.armed <= 0:
            pygame.draw.circle(self.screen, COLOR_RED, (int(pos.x), int(pos.y)), int(mine.radius), 1)

    def _draw_enemy(self, enemy: Enemy) -> None:
        direction = self.player.pos - enemy.pos
        image = self.assets.scaled_rotated(
            enemy.sprite_key,
            direction,
            1.2 if enemy.elite else 1.0,
            base_angle=enemy.sprite_angle_offset,
        )
        if enemy.flash > 0:
            image = image.copy()
            image.fill((135, 135, 135, 0), special_flags=pygame.BLEND_RGBA_ADD)
        pos = self.world_to_screen(enemy.pos)
        self.screen.blit(image, image.get_rect(center=(int(pos.x), int(pos.y))))
        if enemy.elite:
            pygame.draw.circle(self.screen, COLOR_MAGENTA, (int(pos.x), int(pos.y)), int(enemy.radius + 8), 2)
        if getattr(enemy, "elemental_elite", False):
            affinity_colors = {"Fire": COLOR_RED, "Cryo": COLOR_CYAN, "Lightning": COLOR_BLUE, "Poison": COLOR_GREEN}
            color = affinity_colors.get(getattr(enemy, "elemental_affinity", ""), COLOR_MAGENTA)
            pygame.draw.circle(self.screen, color, (int(pos.x), int(pos.y)), int(enemy.radius + 13), 2)

        if enemy.boss or enemy.elite or enemy.health < enemy.max_health:
            bar_w = 46 if not enemy.boss else 86
            rect = pygame.Rect(int(pos.x - bar_w / 2), int(pos.y - enemy.radius - 15), bar_w, 5)
            pygame.draw.rect(self.screen, (0, 0, 0), rect.inflate(2, 2))
            pygame.draw.rect(self.screen, COLOR_RED, rect)
            fill = rect.copy()
            fill.width = int(rect.width * max(0, enemy.health / enemy.max_health))
            pygame.draw.rect(self.screen, COLOR_GREEN if not enemy.boss else COLOR_AMBER, fill)

    def _draw_player(self) -> None:
        for pos in self.player.shield_positions(self.stats.time_survived):
            image = self.assets.sprites["shield"]
            screen = self.world_to_screen(pos)
            self.screen.blit(image, image.get_rect(center=(int(screen.x), int(screen.y))))

        pos = self.world_to_screen(self.player.pos)
        body_key = self.player.sprite_key
        # The generated player tanks are full AI sprites, not split mechanical parts.
        # Their source art has different default facings, so compensate before rotating toward aim.
        tank_def = TANK_BY_ID.get(self.player.tank_id)
        base_angle = tank_def.aim_angle_offset if tank_def is not None else 90.0
        scale = 1.38 if self.player.tank_id != "sniper" else 1.85
        body = self.assets.scaled_rotated(body_key, self.player.aim_dir, scale, base_angle=base_angle)
        if self.player.hurt_flash > 0:
            body = body.copy()
            body.fill((175, 175, 175, 0), special_flags=pygame.BLEND_RGBA_ADD)
        self.screen.blit(body, body.get_rect(center=(int(pos.x), int(pos.y))))

    def _draw_particles(self) -> None:
        for particle in self.particles:
            pos = self.world_to_screen(particle.pos)
            size = max(1, int(particle.size))
            color = (*particle.color, particle.alpha)
            pygame.draw.rect(self.screen, color, pygame.Rect(int(pos.x), int(pos.y), size, size))

    def _draw_damage_numbers(self) -> None:
        for number in self.damage_numbers[-MAX_DAMAGE_NUMBERS:]:
            pos = self.world_to_screen(number.pos)
            image = self.ui.font_sm.render(number.text, False, number.color)
            image.set_alpha(number.alpha)
            self.screen.blit(image, image.get_rect(center=(int(pos.x), int(pos.y))))

    def _draw_messages(self) -> None:
        y = 96
        for text, ttl, color in self.messages[-4:]:
            alpha = int(255 * min(1.0, ttl / 0.35))
            image = self.ui.font.render(text, False, color)
            image.set_alpha(alpha)
            shadow = self.ui.font.render(text, False, (0, 0, 0))
            shadow.set_alpha(alpha)
            rect = image.get_rect(center=(SCREEN_WIDTH // 2, y))
            self.screen.blit(shadow, rect.move(2, 2))
            self.screen.blit(image, rect)
            y += 27

    def world_to_screen(self, pos: pygame.Vector2) -> pygame.Vector2:
        return pos - self.camera + pygame.Vector2(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2) + self.shake_offset

    def screen_to_world(self, pos: pygame.Vector2) -> pygame.Vector2:
        return pos - pygame.Vector2(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2) + self.camera - self.shake_offset

    def _smoke_target(self) -> pygame.Vector2:
        if self.enemies:
            return min(self.enemies, key=lambda enemy: (enemy.pos - self.player.pos).length_squared()).pos
        return self.player.pos + pygame.Vector2(1, 0)

    def _smoke_assertions(self) -> bool:
        base_ok = self.player.alive and self.stats.time_survived > 1.0 and bool(self.projectiles or self.stats.defeated)
        from .e2e_tests import run_e2e_tests
        e2e_ok = run_e2e_tests(self)
        return base_ok and e2e_ok
