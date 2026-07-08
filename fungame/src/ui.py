from __future__ import annotations

import math
from typing import Sequence

import pygame

from .constants import (
    COLOR_AMBER,
    COLOR_BG,
    COLOR_BLUE,
    COLOR_CYAN,
    COLOR_GREEN,
    COLOR_LINE,
    COLOR_MAGENTA,
    COLOR_MUTED,
    COLOR_PANEL,
    COLOR_PANEL_DARK,
    COLOR_PURPLE,
    COLOR_RED,
    COLOR_TEXT,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)
from .achievements import ACHIEVEMENTS, progress_for
from .equipment import EQUIPMENT_SLOTS, item_description
from .meta_upgrades import META_UPGRADES
from .progression import RESEARCH_CATEGORIES, RESEARCH_PROJECTS, ResearchProject, UNLOCKS, research_status, unlock_progress
from .skill_tree import NODES_BY_BRANCH, SKILL_BRANCHES, SKILL_BY_ID, available_skill_points, allocations, node_status, total_skill_points
from .stages import STAGES
from .tank_data import TANKS, TANK_BY_ID
from .upgrades import (
    UPGRADE_BY_ID,
    Upgrade,
    evolution_names,
    family_label,
    family_progress_text,
    get_active_evolutions,
    get_active_passives,
    stack_text,
    tier_text,
    unlock_hint_text,
    upgrade_family,
)


def format_time(seconds: float) -> str:
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"


def get_gear_assets(item: dict) -> tuple[str, str]:
    rarity = item.get("rarity", "Common").lower()
    frame_key = f"loot_frame_{rarity}"
    
    name = item.get("name", "").lower()
    item_type = item.get("type", "weapon").lower()
    effect = item.get("effect")
    
    art_key = item.get("art_key")
    if isinstance(art_key, str) and art_key:
        icon_key = art_key
    elif rarity == "unique" or effect is not None:
        icon_key = "loot_unique_boss_core"
    elif item_type == "weapon":
        if "sniper" in name:
            icon_key = "loot_weapon_sniper_core"
        else:
            icon_key = "loot_weapon_scrap_cannon"
    elif item_type == "armor":
        if "regen" in name:
            icon_key = "loot_armor_regen_core"
        else:
            icon_key = "loot_armor_plated_shell"
    elif item_type == "tracks":
        icon_key = "equipment_tracks_reinforced_treads"
    else:  # trinket
        if "magnet" in name:
            icon_key = "loot_trinket_xp_magnet"
        else:
            icon_key = "loot_trinket_lucky_coin"
            
    return icon_key, frame_key


def get_achievement_icon_key(ach_id: str) -> str:
    if ach_id in ("survive_5",):
        return "achievement_survive_5min"
    if ach_id in ("survive_10", "survive_15", "survive_20", "survive_30"):
        return "achievement_survive_10min"
    if ach_id in ("first_boss", "boss_triplet", "boss_ten", "boss_25"):
        return "achievement_first_boss"
    if ach_id in ("kills_500", "kills_5000", "kills_10000", "kills_25000"):
        return "achievement_kill_500"
    if ach_id in ("coins_100", "coins_1000", "coins_5000", "coins_20000"):
        return "achievement_coin_1000"
    if ach_id in ("starter_clear", "sniper_clear", "engineer_clear", "twin_shot_clear", "flame_caster_clear", "all_tanks"):
        return "achievement_tank_mastery"
    if ach_id in ("shopper_5", "upgrades_20", "first_chest", "chests_25", "chests_100"):
        return "achievement_chest_opener"
    if ach_id in ("first_gear", "gear_20", "gear_100", "first_unique", "unique_5"):
        return "achievement_legendary_loot"
    return "ach_unlocked"


class UI:
    def __init__(self) -> None:
        self.font_sm = pygame.font.SysFont("consolas", 16, bold=True)
        self.font = pygame.font.SysFont("consolas", 20, bold=True)
        self.font_lg = pygame.font.SysFont("consolas", 34, bold=True)
        self.font_xl = pygame.font.SysFont("consolas", 56, bold=True)

    def text(
        self,
        surface: pygame.Surface,
        value: str,
        pos: tuple[int, int],
        font: pygame.font.Font | None = None,
        color: tuple[int, int, int] = COLOR_TEXT,
        center: bool = False,
    ) -> pygame.Rect:
        font = font or self.font
        shadow = font.render(value, False, (0, 0, 0))
        image = font.render(value, False, color)
        rect = image.get_rect()
        if center:
            rect.center = pos
        else:
            rect.topleft = pos
        surface.blit(shadow, rect.move(2, 2))
        surface.blit(image, rect)
        return rect

    def _blit_pixel_fit(self, surface: pygame.Surface, image: pygame.Surface, bounds: pygame.Rect) -> None:
        """Nearest-neighbor scale while preserving the source sprite's aspect ratio."""
        width, height = image.get_size()
        if width <= 0 or height <= 0:
            return
        scale = min(bounds.width / width, bounds.height / height)
        target = (max(1, round(width * scale)), max(1, round(height * scale)))
        scaled = pygame.transform.scale(image, target)
        surface.blit(scaled, scaled.get_rect(center=bounds.center))

    def draw_bar(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        value: float,
        max_value: float,
        color: tuple[int, int, int],
        back: tuple[int, int, int] = COLOR_PANEL_DARK,
    ) -> None:
        pygame.draw.rect(surface, (0, 0, 0), rect.inflate(4, 4))
        pygame.draw.rect(surface, back, rect)
        pct = 0.0 if max_value <= 0 else max(0.0, min(1.0, value / max_value))
        fill = rect.copy()
        fill.width = int(rect.width * pct)
        pygame.draw.rect(surface, color, fill)
        pygame.draw.rect(surface, COLOR_LINE, rect, 2)

    def draw_hud(self, surface: pygame.Surface, game: object) -> None:
        player = game.player
        self.draw_bar(surface, pygame.Rect(18, 16, 286, 21), player.health, player.max_health, COLOR_GREEN)
        self.text(surface, f"HP {math.ceil(max(0, player.health))}/{int(player.max_health)}", (26, 17), self.font_sm)
        self.draw_bar(surface, pygame.Rect(18, 44, 286, 16), player.xp, player.xp_to_next, COLOR_CYAN)
        self.text(surface, f"LV {player.level}", (316, 16), self.font)
        self.text(surface, format_time(game.stats.time_survived), (SCREEN_WIDTH // 2, 16), self.font_lg, COLOR_CYAN, center=True)
        self.text(surface, f"COINS {game.stats.run_coins}", (SCREEN_WIDTH - 178, 16), self.font, COLOR_AMBER)
        self.text(surface, f"WEAPON {evolution_names(player.evolutions)}", (18, 68), self.font_sm, COLOR_AMBER)
        self.text(surface, player.tank_name.upper(), (SCREEN_WIDTH - 210, 44), self.font_sm, COLOR_MUTED)
        contract = getattr(game, "active_contract", game.stage)
        progress = min(getattr(game, "contract_progress", 0), contract.goal)
        status = "COMPLETE" if getattr(game, "contract_completed", False) else ("FAILED" if getattr(game, "contract_failed", False) else f"{progress}/{contract.goal}")
        self.text(surface, f"CONTRACT {contract.name.upper()}: {status}", (18, 90), self.font_sm, COLOR_CYAN)
        if getattr(game, "anomaly_route_available", False):
            self.text(surface, "ANOMALY ROUTE SIGNAL", (18, 108), self.font_sm, COLOR_MAGENTA)
        if getattr(game.director, "surge_active_until", 0.0) > game.stats.time_survived:
            remaining = game.director.surge_active_until - game.stats.time_survived
            self.text(surface, f"SALVAGE SURGE {remaining:0.0f}s", (SCREEN_WIDTH - 210, 68), self.font_sm, COLOR_MAGENTA)

        x = 18
        y = SCREEN_HEIGHT - 43
        shown = 0
        for upgrade_id, count in sorted(player.upgrade_counts.items()):
            if count <= 0:
                continue
            upgrade_def = UPGRADE_BY_ID.get(upgrade_id)
            icon_key = upgrade_id if upgrade_id in game.assets.icons else (upgrade_def.icon if upgrade_def else upgrade_id)
            icon = game.assets.icons.get(icon_key)
            if icon is None:
                continue
            slot = pygame.Rect(x - 1, y - 1, 30, 30)
            pygame.draw.rect(surface, (0, 0, 0), slot.inflate(2, 2))
            pygame.draw.rect(surface, COLOR_PANEL, slot)
            self._blit_pixel_fit(surface, icon, slot.inflate(-6, -6))
            self.text(surface, str(count), (x + 19, y + 15), self.font_sm, COLOR_TEXT)
            x += 36
            shown += 1
            if shown >= 16:
                break

        if getattr(game, "debug_performance", False):
            perf = f"FPS {game.clock.get_fps():04.1f}  E {len(game.enemies)}  P {len(game.projectiles)}  XP {len(game.pickups)}"
            self.text(surface, perf, (SCREEN_WIDTH - 360, 68), self.font_sm, COLOR_CYAN)

        # Draw active skills CD HUD
        if player.active_skills:
            box_sz = 44
            gap = 10
            total_w = len(player.active_skills) * box_sz + (len(player.active_skills) - 1) * gap
            start_x = SCREEN_WIDTH // 2 - total_w // 2
            hud_y = SCREEN_HEIGHT - 56
            for idx, skill in enumerate(player.active_skills):
                bx = start_x + idx * (box_sz + gap)
                rect = pygame.Rect(bx, hud_y, box_sz, box_sz)
                
                # Draw box
                self._panel(surface, rect, color=COLOR_CYAN)
                
                # Draw icon if matching
                icon_key = {
                    "Burst Barrage": "rapid_fire",
                    "Piercing Laser": "pierce",
                    "Deploy Sentry": "turret_support",
                    "Bullet Fan": "multi_shot",
                    "Fireball": "ability_fireball",
                    "Frost Nova": "ability_frost_nova",
                    "Acid Glob": "ability_acid_glob",
                    "Arc Surge": "ability_arc_surge",
                }.get(skill["name"], "rapid_fire")
                icon = game.assets.icons.get(icon_key, game.assets.icons.get("rapid_fire"))
                if icon:
                    self._blit_pixel_fit(surface, icon, rect.inflate(-12, -12))
                    
                # Hotkey indicator
                self.text(surface, "RMB", (rect.x + 3, rect.y + 2), self.font_sm, COLOR_AMBER)
                
                # Cooldown overlay
                if skill["cooldown"] > 0:
                    reduction = min(0.6, player.Focus * 0.03 + getattr(player, "ability_cooldown_reduction", 0.0))
                    cooldown_pct = skill["cooldown"] / (skill["max_cooldown"] * (1.0 - reduction))
                    overlay = pygame.Surface((box_sz - 4, box_sz - 4), pygame.SRCALPHA)
                    overlay.fill((0, 0, 0, 190))
                    h = int((box_sz - 4) * cooldown_pct)
                    pygame.draw.rect(overlay, (0, 0, 0, 0), (0, 0, box_sz - 4, box_sz - 4 - h))
                    surface.blit(overlay, (rect.x + 2, rect.y + 2))
                    
                    # CD Text
                    self.text(surface, f"{skill['cooldown']:.1f}", (rect.centerx, rect.centery), self.font_sm, COLOR_RED, center=True)

        if player.health / player.max_health < 0.28:
            alpha = int(80 + math.sin(game.stats.time_survived * 9) * 42)
            pulse = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            pygame.draw.rect(pulse, (255, 48, 72, alpha), pulse.get_rect(), 8)
            surface.blit(pulse, (0, 0))

    def menu_button_rects(self) -> dict[str, pygame.Rect]:
        x = SCREEN_WIDTH // 2 - 135
        y = SCREEN_HEIGHT // 2 + 18
        h = 40
        gap = 9
        return {
            "play": pygame.Rect(x, y, 270, h),
            "tanks": pygame.Rect(x, y + (h + gap), 270, h),
            "shop": pygame.Rect(x, y + (h + gap) * 2, 270, h),
            "achievements": pygame.Rect(x, y + (h + gap) * 3, 270, h),
            "stages": pygame.Rect(x, y + (h + gap) * 4, 270, h),
            "quit": pygame.Rect(x, y + (h + gap) * 5, 270, h),
        }

    def menu_start_rect(self) -> pygame.Rect:
        return self.menu_button_rects()["play"]

    def game_over_restart_rect(self) -> pygame.Rect:
        return pygame.Rect(SCREEN_WIDTH // 2 - 250, SCREEN_HEIGHT // 2 + 146, 220, 48)

    def game_over_menu_rect(self) -> pygame.Rect:
        return pygame.Rect(SCREEN_WIDTH // 2 + 30, SCREEN_HEIGHT // 2 + 146, 220, 48)

    def pause_button_rects(self) -> dict[str, pygame.Rect]:
        x = SCREEN_WIDTH // 2 - 355
        y = SCREEN_HEIGHT // 2 + 10
        h = 42
        gap = 12
        return {
            "resume": pygame.Rect(x, y, 300, h),
            "menu": pygame.Rect(x, y + h + gap, 300, h),
            "quit": pygame.Rect(x, y + (h + gap) * 2, 300, h),
        }

    def restart_rect(self) -> pygame.Rect:
        return self.game_over_restart_rect()

    def back_rect(self) -> pygame.Rect:
        return pygame.Rect(28, 30, 140, 42)

    def tank_card_rects(self) -> dict[str, pygame.Rect]:
        columns = 4
        card_w = 272
        card_h = 254
        gap_x = 22
        gap_y = 18
        start = SCREEN_WIDTH // 2 - (card_w * columns + gap_x * (columns - 1)) // 2
        return {
            tank.id: pygame.Rect(
                start + (idx % columns) * (card_w + gap_x),
                138 + (idx // columns) * (card_h + gap_y),
                card_w,
                card_h,
            )
            for idx, tank in enumerate(TANKS)
        }

    def garage_tab_rects(self) -> dict[str, pygame.Rect]:
        width = 190
        gap = 14
        total = width * 4 + gap * 3
        left = SCREEN_WIDTH // 2 - total // 2
        return {
            "tanks": pygame.Rect(left, 74, width, 40),
            "research": pygame.Rect(left + (width + gap), 74, width, 40),
            "gear": pygame.Rect(left + (width + gap) * 2, 74, width, 40),
            "skill_tree": pygame.Rect(left + (width + gap) * 3, 74, width, 40),
        }

    def shop_row_rects(self) -> dict[str, pygame.Rect]:
        rects: dict[str, pygame.Rect] = {}
        left = 74
        top = 142
        row_w = 558
        row_h = 76
        gap_x = 18
        gap_y = 13
        for idx, upgrade in enumerate(META_UPGRADES):
            col = idx % 2
            row = idx // 2
            rects[upgrade.id] = pygame.Rect(left + col * (row_w + gap_x), top + row * (row_h + gap_y), row_w, row_h)
        return rects

    def progression_tab_rects(self) -> dict[str, pygame.Rect]:
        return {
            "achievements": pygame.Rect(SCREEN_WIDTH // 2 - 220, 82, 205, 38),
            "unlocks": pygame.Rect(SCREEN_WIDTH // 2 + 15, 82, 205, 38),
        }

    def research_filter_rects(self) -> dict[str, pygame.Rect]:
        width = 180
        gap = 10
        total = len(RESEARCH_CATEGORIES) * width + (len(RESEARCH_CATEGORIES) - 1) * gap
        left = SCREEN_WIDTH // 2 - total // 2
        return {category: pygame.Rect(left + index * (width + gap), 132, width, 30) for index, category in enumerate(RESEARCH_CATEGORIES)}

    def unlock_tile_rects(self) -> dict[str, pygame.Rect]:
        left = 42
        top = 160
        tile_w = 184
        tile_h = 124
        gap = 12
        columns = 3
        return {
            unlock.id: pygame.Rect(left + (index % columns) * (tile_w + gap), top + (index // columns) * (tile_h + gap), tile_w, tile_h)
            for index, unlock in enumerate(UNLOCKS)
        }

    def research_card_rects(self, category: str = "All") -> dict[str, pygame.Rect]:
        projects = [project for project in RESEARCH_PROJECTS if category == "All" or project.category == category]
        left = 42
        top = 184
        card_w = 378
        card_h = 78
        gap_x = 29
        gap_y = 8
        columns = 3
        return {
            project.id: pygame.Rect(left + (index % columns) * (card_w + gap_x), top + (index // columns) * (card_h + gap_y), card_w, card_h)
            for index, project in enumerate(projects)
        }

    def stage_card_rects(self) -> dict[str, pygame.Rect]:
        card_w = 350
        card_h = 246
        gap_x = 28
        gap_y = 20
        columns = 3
        start = SCREEN_WIDTH // 2 - (card_w * columns + gap_x * (columns - 1)) // 2
        return {
            stage.id: pygame.Rect(start + (idx % columns) * (card_w + gap_x), 150 + (idx // columns) * (card_h + gap_y), card_w, card_h)
            for idx, stage in enumerate(STAGES)
        }

    def level_card_rects(self, count: int) -> list[pygame.Rect]:
        card_w = 300
        gap = 24
        total = count * card_w + (count - 1) * gap
        start = SCREEN_WIDTH // 2 - total // 2
        return [pygame.Rect(start + i * (card_w + gap), 228, card_w, 300) for i in range(count)]

    def achievement_tile_rects(self, page: int = 0) -> dict[str, pygame.Rect]:
        left = 42
        top = 160
        tile_w = 184
        tile_h = 106
        gap = 12
        cols = 3
        start = max(0, page) * 12
        visible = ACHIEVEMENTS[start : start + 12]
        return {
            achievement.id: pygame.Rect(
                left + (idx % cols) * (tile_w + gap),
                top + (idx // cols) * (tile_h + gap),
                tile_w,
                tile_h,
            )
            for idx, achievement in enumerate(visible)
        }

    def achievement_page_rects(self) -> dict[str, pygame.Rect]:
        return {
            "previous": pygame.Rect(42, 640, 140, 32),
            "next": pygame.Rect(478, 640, 140, 32),
        }

    def draw_menu(self, surface: pygame.Surface, game: object) -> None:
        self._dark_overlay(surface, 185)
        self._draw_menu_scene(surface, game)
        
        logo = game.assets.menu.get("logo")
        if logo:
            logo_scaled = pygame.transform.smoothscale(logo, (512, 160))
            surface.blit(logo_scaled, logo_scaled.get_rect(center=(SCREEN_WIDTH // 2, 120)))
        else:
            logo_y = 80
            for offset in (4, 2, 0):
                color = (0, 150, 180) if offset > 0 else COLOR_CYAN
                self.text(surface, "SCRAPSTORM", (SCREEN_WIDTH // 2 + offset, logo_y + offset), self.font_xl, color, center=True)
            
            logo_y2 = 140
            for offset in (4, 2, 0):
                color = (180, 0, 120) if offset > 0 else COLOR_MAGENTA
                self.text(surface, "O V E R D R I V E", (SCREEN_WIDTH // 2 + offset, logo_y2 + offset), self.font_xl, color, center=True)
            
        # self.text(surface, "NEON TANK ROGUELITE", (SCREEN_WIDTH // 2, 196), self.font, COLOR_AMBER, center=True)
        selected_tank = TANK_BY_ID.get(game.save_data.get("selected_tank", "starter"), TANK_BY_ID["starter"])
        loot_status = "META LOOT ONLINE" if game.save_data.get("loot_unlocked", False) else "META LOOT LOCKED"
        self.text(
            surface,
            f"Coins: {game.save_data.get('coins', 0)}  |  Blueprints: {game.save_data.get('blueprint_fragments', 0)}  |  {loot_status}",
            (SCREEN_WIDTH // 2, 224),
            self.font,
            COLOR_AMBER,
            center=True,
        )
        # self.text(
        #     surface,
        #     "WASD move  |  Mouse aim  |  Auto-fire  |  Q skill  |  Space dash",
        #     (SCREEN_WIDTH // 2, 266),
        #     self.font,
        #     COLOR_TEXT,
        #     center=True,
        # )
        labels = {
            "play": ("START RUN", COLOR_CYAN),
            "tanks": ("TANK SELECT", COLOR_GREEN),
            "shop": ("UPGRADE SHOP", COLOR_AMBER),
            "achievements": ("ACHIEVEMENTS" + ("  NEW" if game.save_data.get("unlocks_new") else ""), COLOR_MAGENTA),
            "stages": ("STAGES", COLOR_CYAN),
            "quit": ("QUIT", COLOR_RED),
        }
        for key, rect in self.menu_button_rects().items():
            label, color = labels[key]
            self._button(surface, rect, label, color)
        sprite = game.assets.sprites[selected_tank.sprite_key]
        scaled = pygame.transform.scale(sprite, (82, 82))
        tank_rect = scaled.get_rect(center=(SCREEN_WIDTH // 2, 328))
        pygame.draw.circle(surface, (6, 8, 13), tank_rect.center, 52)
        pygame.draw.circle(surface, COLOR_LINE, tank_rect.center, 52, 2)
        pygame.draw.circle(surface, COLOR_CYAN, tank_rect.center, 42, 1)
        surface.blit(scaled, tank_rect)

    def _draw_menu_scene(self, surface: pygame.Surface, game: object) -> None:
        now = pygame.time.get_ticks() / 1000.0
        horizon = 332
        background = game.assets.menu.get("background")
        if background:
            bg = pygame.transform.smoothscale(background, (SCREEN_WIDTH, SCREEN_HEIGHT)).copy()
            bg.set_alpha(170)
            surface.blit(bg, (0, 0))


    def draw_tank_select(self, surface: pygame.Surface, game: object) -> None:
        self._dark_overlay(surface, 230)
        self._button(surface, self.back_rect(), "BACK", COLOR_MUTED)
        
        # Tabs at the top
        tab = getattr(game, "garage_tab", "tanks")
        tabs = self.garage_tab_rects()
        
        t_color = COLOR_CYAN if tab == "tanks" else COLOR_MUTED
        r_color = COLOR_CYAN if tab == "research" else COLOR_MUTED
        g_color = COLOR_CYAN if tab == "gear" else COLOR_MUTED
        
        self._button(surface, tabs["tanks"], "TANKS", t_color)
        self._button(surface, tabs["research"], "RESEARCH", r_color)
        self._button(surface, tabs["gear"], "EQUIPMENT & STATS", g_color)
        self._button(surface, tabs["skill_tree"], "SKILL TREE", COLOR_GREEN if tab == "skill_tree" else COLOR_MUTED)

        if tab == "research":
            self._draw_research_panel(surface, game)
            return
        if tab == "skill_tree":
            self.draw_skill_tree(surface, game)
            return
        
        if tab == "tanks":
            self.text(surface, "GARAGE", (SCREEN_WIDTH // 2, 38), self.font_lg, COLOR_CYAN, center=True)
            unlocked = set(game.save_data.get("unlocked_tanks", []))
            selected = game.save_data.get("selected_tank", "starter")
            for tank in TANKS:
                rect = self.tank_card_rects()[tank.id]
                color = COLOR_CYAN if tank.id == selected else COLOR_LINE
                self._panel(surface, rect, color=color)
                
                # Highlight if hovered
                mouse = pygame.mouse.get_pos()
                hovered = rect.collidepoint(mouse)
                if hovered:
                    pygame.draw.rect(surface, COLOR_AMBER, rect, 2)
                    
                sprite = game.assets.sprites[tank.sprite_key]
                preview_size = 76
                surface.blit(
                    pygame.transform.scale(sprite, (preview_size, preview_size)),
                    (rect.centerx - preview_size // 2, rect.y + 12),
                )
                
                # Title
                self.text(surface, tank.name, (rect.centerx, rect.y + 96), self.font, COLOR_CYAN, center=True)
                
                # Description
                desc_rect = pygame.Rect(rect.x + 12, rect.y + 118, rect.width - 24, 52)
                self._draw_multiline_text(surface, tank.description, desc_rect, self.font_sm, COLOR_TEXT)
                
                # Strengths
                strengths = self._fit_text("Pros: " + tank.strengths, self.font_sm, rect.width - 24)
                self.text(surface, strengths, (rect.x + 12, rect.y + 182), self.font_sm, COLOR_MUTED)
                
                # Status
                if tank.id == selected:
                    status = "SELECTED"
                    status_color = COLOR_GREEN
                elif tank.id in unlocked:
                    status = "SELECT"
                    status_color = COLOR_AMBER
                else:
                    status = f"BUY: {tank.cost}"
                    status_color = COLOR_RED if game.save_data.get("coins", 0) < tank.cost else COLOR_AMBER
                self._button(surface, pygame.Rect(rect.x + 20, rect.bottom - 48, rect.width - 40, 32), status, status_color)
                
        elif tab == "gear":
            self._draw_equipment_panel(surface, game)
            return
            self.text(surface, "EQUIPMENT & STATS", (SCREEN_WIDTH // 2, 38), self.font_lg, COLOR_CYAN, center=True)
            selected_tank = game.save_data.get("selected_tank", "starter")
            
            # --- LEFT COLUMN: STATS & TANK SPECIALIZATION TREE ---
            left_rect = pygame.Rect(54, 142, 532, 520)
            self._panel(surface, left_rect, color=COLOR_LINE)
            
            # Header
            self.text(surface, f"{TANK_BY_ID[selected_tank].name.upper()} STATS", (left_rect.x + 24, left_rect.y + 20), self.font, COLOR_CYAN)
            
            # Draw player stats (Strength, Dexterity, Vitality, Tech, Focus, Luck)
            from src.player import Player
            from src.meta_upgrades import apply_meta_upgrades
            from src.tank_data import configure_player_tank
            temp_player = Player(pygame.Vector2(0, 0))
            configure_player_tank(temp_player, selected_tank)
            apply_meta_upgrades(temp_player, game.save_data)
            
            stats_list = [
                ("Strength (DMG)", temp_player.Strength, COLOR_RED),
                ("Dexterity (SPD)", temp_player.Dexterity, COLOR_AMBER),
                ("Vitality (HP)", temp_player.Vitality, COLOR_GREEN),
                ("Tech (SUMMON)", temp_player.Tech, COLOR_BLUE),
                ("Focus (SKILLS)", temp_player.Focus, COLOR_PURPLE),
                ("Luck (CRIT/Loot)", temp_player.Luck, COLOR_CYAN)
            ]
            
            y_offset = left_rect.y + 54
            for label, val, color in stats_list:
                self.text(surface, label, (left_rect.x + 24, y_offset), self.font_sm, COLOR_TEXT)
                self.text(surface, str(val), (left_rect.x + 220, y_offset), self.font_sm, color)
                y_offset += 24
                
            # Spec Tree Scaffolding
            tree_y = left_rect.y + 210
            pygame.draw.line(surface, COLOR_LINE, (left_rect.x + 20, tree_y), (left_rect.right - 20, tree_y), 2)
            
            # Skill points calculation
            best_time = game.save_data.get("stats", {}).get(f"{selected_tank}_best_time", 0)
            total_points = int(best_time // 120)
            allocated_nodes = game.save_data.setdefault("tank_skill_trees", {}).setdefault(selected_tank, [])
            available_points = max(0, total_points - len(allocated_nodes))
            
            self.text(surface, "SPECIALIZATION TREE", (left_rect.x + 24, tree_y + 14), self.font, COLOR_AMBER)
            self.text(surface, f"Points: {available_points} available (Best: {format_time(best_time)})", (left_rect.x + 24, tree_y + 40), self.font_sm, COLOR_MUTED)
            self.text(surface, "(Earn 1 point per 2 mins survived)", (left_rect.x + 24, tree_y + 58), self.font_sm, COLOR_MUTED)
            
            # Draw 4 spec nodes
            nodes = [
                ("node_offense", "Offense (+2 Str)", pygame.Rect(left_rect.x + 24, tree_y + 88, 220, 36)),
                ("node_defense", "Defense (+2 Vit)", pygame.Rect(left_rect.x + 276, tree_y + 88, 220, 36)),
                ("node_specialty", "Specialty (+2 Focus)", pygame.Rect(left_rect.x + 24, tree_y + 138, 220, 36)),
                ("node_overclock", "Overclock (+2 Dex)", pygame.Rect(left_rect.x + 276, tree_y + 138, 220, 36))
            ]
            
            for node_id, node_label, rect in nodes:
                is_allocated = node_id in allocated_nodes
                node_color = COLOR_GREEN if is_allocated else (COLOR_CYAN if available_points > 0 else COLOR_MUTED)
                self._button(surface, rect, node_label, node_color)
                # If hovered, highlight
                if rect.collidepoint(pygame.mouse.get_pos()):
                    pygame.draw.rect(surface, COLOR_AMBER, rect, 2)
            
            # Refund button
            refund_rect = pygame.Rect(left_rect.x + 24, tree_y + 196, 472, 34)
            self._button(surface, refund_rect, "REFUND ALL POINTS", COLOR_RED if allocated_nodes else COLOR_MUTED)
            
            # --- RIGHT COLUMN: SLOTS & INVENTORY ---
            right_rect = pygame.Rect(640, 142, 582, 520)
            self._panel(surface, right_rect, color=COLOR_LINE)
            
            self.text(surface, "EQUIPPED SLOTS", (right_rect.x + 24, right_rect.y + 20), self.font, COLOR_CYAN)
            
            # Draw equipped slots: Weapon, Armor, Trinket
            equipped_gear = game.save_data.setdefault("equipped_gear", {"weapon": None, "armor": None, "trinket": None})
            inventory = game.save_data.setdefault("gear_inventory", [])
            inv_by_id = {item["id"]: item for item in inventory}
            
            slot_rects = {
                "weapon": pygame.Rect(right_rect.x + 24, right_rect.y + 54, 160, 50),
                "armor": pygame.Rect(right_rect.x + 204, right_rect.y + 54, 160, 50),
                "trinket": pygame.Rect(right_rect.x + 384, right_rect.y + 54, 160, 50)
            }
            
            mouse = pygame.mouse.get_pos()
            hovered_item = None
            
            for slot, s_rect in slot_rects.items():
                item_id = equipped_gear.get(slot)
                item = inv_by_id.get(item_id) if item_id else None
                s_color = COLOR_CYAN if item else COLOR_LINE
                self._panel(surface, s_rect, color=s_color)
                
                # Check hover
                if s_rect.collidepoint(mouse):
                    pygame.draw.rect(surface, COLOR_AMBER, s_rect, 2)
                    if item:
                        hovered_item = item
                
                # Draw label
                if item:
                    rarity_colors = {
                        "Common": COLOR_TEXT, "Uncommon": COLOR_GREEN,
                        "Rare": COLOR_CYAN, "Epic": COLOR_PURPLE,
                        "Legendary": COLOR_AMBER, "Unique": COLOR_MAGENTA
                    }
                    icon_key, frame_key = get_gear_assets(item)
                    frame_img = game.assets.icons.get(frame_key)
                    icon_img = game.assets.icons.get(icon_key)
                    
                    icon_rect = pygame.Rect(s_rect.x + 6, s_rect.y + 4, 42, 42)
                    if frame_img:
                        surface.blit(pygame.transform.scale(frame_img, (42, 42)), icon_rect)
                    if icon_img:
                        surface.blit(pygame.transform.scale(icon_img, (42, 42)), icon_rect)
                        
                    text_x = s_rect.x + 54
                    self.text(surface, self._fit_text(item["name"], self.font_sm, s_rect.width - 60), (text_x, s_rect.y + 8), self.font_sm, rarity_colors.get(item["rarity"], COLOR_TEXT))
                    self.text(surface, slot.upper(), (text_x, s_rect.y + 28), self.font_sm, COLOR_MUTED)
                else:
                    self.text(surface, f"[{slot.upper()}]", (s_rect.centerx, s_rect.centery), self.font_sm, COLOR_MUTED, center=True)
            
            # Inventory divider
            inv_y = right_rect.y + 124
            pygame.draw.line(surface, COLOR_LINE, (right_rect.x + 20, inv_y), (right_rect.right - 20, inv_y), 2)
            
            self.text(surface, "GEAR INVENTORY", (right_rect.x + 24, inv_y + 14), self.font, COLOR_AMBER)
            
            # Draw inventory slots grid (5 columns x 3 rows)
            left_inv = right_rect.x + 24
            top_inv = inv_y + 42
            slot_w = 100
            slot_h = 50
            gap_x = 8
            gap_y = 8
            
            for idx in range(15):
                col = idx % 5
                row = idx // 5
                rect = pygame.Rect(left_inv + col * (slot_w + gap_x), top_inv + row * (slot_h + gap_y), slot_w, slot_h)
                
                # Check item in inventory
                item = inventory[idx] if idx < len(inventory) else None
                color = COLOR_CYAN if item else COLOR_LINE
                self._panel(surface, rect, color=color)
                
                if item:
                    # Hover check
                    if rect.collidepoint(mouse):
                        pygame.draw.rect(surface, COLOR_AMBER, rect, 2)
                        hovered_item = item
                        
                    rarity_colors = {
                        "Common": COLOR_TEXT, "Uncommon": COLOR_GREEN,
                        "Rare": COLOR_CYAN, "Epic": COLOR_PURPLE,
                        "Legendary": COLOR_AMBER, "Unique": COLOR_MAGENTA
                    }
                    icon_key, frame_key = get_gear_assets(item)
                    frame_img = game.assets.icons.get(frame_key)
                    icon_img = game.assets.icons.get(icon_key)
                    
                    icon_rect = pygame.Rect(rect.x + 4, rect.y + 4, 42, 42)
                    if frame_img:
                        surface.blit(pygame.transform.scale(frame_img, (42, 42)), icon_rect)
                    if icon_img:
                        surface.blit(pygame.transform.scale(icon_img, (42, 42)), icon_rect)
                        
                    text_x = rect.x + 50
                    self.text(surface, self._fit_text(item["name"], self.font_sm, rect.width - 54), (text_x, rect.y + 6), self.font_sm, rarity_colors.get(item["rarity"], COLOR_TEXT))
                    self.text(surface, item["type"].upper(), (text_x, rect.y + 26), self.font_sm, COLOR_MUTED)
                else:
                    self.text(surface, "-", (rect.centerx, rect.centery), self.font_sm, COLOR_MUTED, center=True)
            
            # Hover Item Detail Panel
            detail_y = top_inv + 3 * (slot_h + gap_y) + 12
            detail_rect = pygame.Rect(right_rect.x + 24, detail_y, 532, 110)
            self._panel(surface, detail_rect, color=COLOR_CYAN)
            
            if hovered_item:
                rarity_colors = {
                    "Common": COLOR_TEXT, "Uncommon": COLOR_GREEN,
                    "Rare": COLOR_CYAN, "Epic": COLOR_PURPLE,
                    "Legendary": COLOR_AMBER, "Unique": COLOR_MAGENTA
                }
                icon_key, frame_key = get_gear_assets(hovered_item)
                frame_img = game.assets.icons.get(frame_key)
                icon_img = game.assets.icons.get(icon_key)
                
                large_rect = pygame.Rect(detail_rect.x + 16, detail_rect.y + 16, 78, 78)
                if frame_img:
                    surface.blit(pygame.transform.scale(frame_img, (78, 78)), large_rect)
                if icon_img:
                    surface.blit(pygame.transform.scale(icon_img, (78, 78)), large_rect)
                
                text_start_x = detail_rect.x + 110
                self.text(surface, f"{hovered_item['name']} ({hovered_item['rarity']})", (text_start_x, detail_rect.y + 12), self.font, rarity_colors.get(hovered_item["rarity"], COLOR_TEXT))
                self.text(surface, hovered_item["type"].upper(), (detail_rect.right - 120, detail_rect.y + 12), self.font_sm, COLOR_MUTED)
                
                # Display stats
                stats_str = ", ".join(f"+{v} {k}" for k, v in hovered_item.get("stats", {}).items())
                self.text(surface, f"Stats: {stats_str}" if stats_str else "Stats: None", (text_start_x, detail_rect.y + 44), self.font_sm, COLOR_TEXT)
                
                # Unique effect
                effect = hovered_item.get("effect")
                if effect:
                    eff_desc = {
                        "bullets_explode": "Every 5th shot explodes on impact",
                        "turret_lightning": "Summoned turrets gain chain lightning",
                        "crit_burn": "Crits apply damage over time (burn)",
                        "impact_split": "Fireballs split on impact",
                        "sniper_freeze": "Sniper bullets slow/freeze targets",
                        "drone_lifesteal": "Drones heal you on hit",
                        "ricochet_double": "Twin-shot bullets ricochet",
                        "rare_chests": "Higher chance for rare chest drops",
                        "low_hp_shield": "Low health grants temporary shield"
                    }.get(effect, effect.replace("_", " "))
                    self.text(surface, f"Effect: {eff_desc}", (text_start_x, detail_rect.y + 74), self.font_sm, COLOR_AMBER)
                else:
                    self.text(surface, "Click to equip or unequip", (text_start_x, detail_rect.y + 74), self.font_sm, COLOR_MUTED)
            else:
                self.text(surface, "HOVER OVER GEAR TO VIEW STATS & EFFECTS", (detail_rect.centerx, detail_rect.centery), self.font_sm, COLOR_MUTED, center=True)

    def equipment_slot_rects(self) -> dict[str, pygame.Rect]:
        right_rect = pygame.Rect(620, 142, 600, 520)
        return {
            "weapon": pygame.Rect(right_rect.x + 20, right_rect.y + 54, 130, 58),
            "armor": pygame.Rect(right_rect.x + 164, right_rect.y + 54, 130, 58),
            "trinket": pygame.Rect(right_rect.x + 308, right_rect.y + 54, 130, 58),
            "tracks": pygame.Rect(right_rect.x + 452, right_rect.y + 54, 130, 58),
        }

    def equipment_inventory_rects(self) -> list[pygame.Rect]:
        right_rect = pygame.Rect(620, 142, 600, 520)
        left = right_rect.x + 20
        top = right_rect.y + 172
        return [
            pygame.Rect(left + (index % 5) * 112, top + (index // 5) * 58, 104, 50)
            for index in range(15)
        ]

    def _draw_equipment_panel(self, surface: pygame.Surface, game: object) -> None:
        self.text(surface, "EQUIPMENT & STATS", (SCREEN_WIDTH // 2, 38), self.font_lg, COLOR_CYAN, center=True)
        selected_tank = game.save_data.get("selected_tank", "starter")
        from src.player import Player
        from src.meta_upgrades import apply_meta_upgrades
        from src.tank_data import configure_player_tank

        preview = Player(pygame.Vector2(0, 0))
        configure_player_tank(preview, selected_tank)
        apply_meta_upgrades(preview, game.save_data)

        left_rect = pygame.Rect(54, 142, 532, 520)
        self._panel(surface, left_rect, color=COLOR_LINE)
        self.text(surface, f"{TANK_BY_ID[selected_tank].name.upper()} LOADOUT", (left_rect.x + 22, left_rect.y + 18), self.font, COLOR_CYAN)
        self.text(surface, "CORE STATS", (left_rect.x + 22, left_rect.y + 58), self.font_sm, COLOR_AMBER)
        core_stats = (
            ("Strength", preview.Strength, COLOR_RED),
            ("Dexterity", preview.Dexterity, COLOR_AMBER),
            ("Vitality", preview.Vitality, COLOR_GREEN),
            ("Tech", preview.Tech, COLOR_BLUE),
            ("Focus", preview.Focus, COLOR_PURPLE),
            ("Luck", preview.Luck, COLOR_CYAN),
        )
        for index, (label, value, color) in enumerate(core_stats):
            col, row = index % 2, index // 2
            rect = pygame.Rect(left_rect.x + 22 + col * 248, left_rect.y + 82 + row * 42, 232, 34)
            self._panel(surface, rect, color)
            self.text(surface, label.upper(), (rect.x + 10, rect.y + 9), self.font_sm, COLOR_TEXT)
            self.text(surface, str(value), (rect.right - 12, rect.y + 9), self.font, color, center=False)

        derived_top = left_rect.y + 232
        pygame.draw.line(surface, COLOR_LINE, (left_rect.x + 20, derived_top - 12), (left_rect.right - 20, derived_top - 12), 2)
        self.text(surface, "DERIVED COMBAT", (left_rect.x + 22, derived_top), self.font_sm, COLOR_AMBER)
        derived = (
            ("Damage", f"{preview.bullet_damage:.0f}"),
            ("Fire Rate", f"{preview.effective_fire_rate:.1f}/s"),
            ("Hull", f"{preview.max_health:.0f}"),
            ("Speed", f"{preview.speed:.0f}"),
            ("Crit", f"{preview.crit_chance * 100:.0f}%"),
            ("Cooldown", f"-{preview.ability_cooldown_reduction * 100:.0f}%"),
            ("Ability", f"x{preview.ability_power_mult:.2f}"),
            ("Pickup", f"{preview.effective_magnet_radius:.0f}"),
        )
        for index, (label, value) in enumerate(derived):
            col, row = index % 2, index // 2
            self.text(surface, label, (left_rect.x + 28 + col * 248, derived_top + 30 + row * 38), self.font_sm, COLOR_MUTED)
            self.text(surface, value, (left_rect.x + 176 + col * 248, derived_top + 30 + row * 38), self.font_sm, COLOR_CYAN)
        self.text(surface, self._fit_text("Tracks affect movement response, rams, dashes, pickup routing, and stability.", self.font_sm, left_rect.width - 44), (left_rect.x + 22, left_rect.bottom - 42), self.font_sm, COLOR_GREEN)
        self.text(surface, self._fit_text("Open SKILL TREE to invest the selected tank's earned survival points.", self.font_sm, left_rect.width - 44), (left_rect.x + 22, left_rect.bottom - 22), self.font_sm, COLOR_MUTED)

        right_rect = pygame.Rect(620, 142, 600, 520)
        self._panel(surface, right_rect, color=COLOR_LINE)
        self.text(surface, "EQUIPPED SLOTS", (right_rect.x + 20, right_rect.y + 20), self.font, COLOR_CYAN)
        equipped = game.save_data.setdefault("equipped_gear", {slot: None for slot in EQUIPMENT_SLOTS})
        inventory = game.save_data.setdefault("gear_inventory", [])
        by_id = {item["id"]: item for item in inventory}
        mouse = pygame.mouse.get_pos()
        hovered: dict | None = None
        rarity_colors = {"Common": COLOR_TEXT, "Uncommon": COLOR_GREEN, "Rare": COLOR_CYAN, "Epic": COLOR_PURPLE, "Legendary": COLOR_AMBER, "Unique": COLOR_MAGENTA}
        for slot, rect in self.equipment_slot_rects().items():
            item = by_id.get(equipped.get(slot))
            self._panel(surface, rect, COLOR_CYAN if item else COLOR_LINE)
            if rect.collidepoint(mouse):
                pygame.draw.rect(surface, COLOR_AMBER, rect, 2)
                hovered = item or hovered
            if item:
                icon_key, frame_key = get_gear_assets(item)
                frame, icon = game.assets.icons.get(frame_key), game.assets.icons.get(icon_key)
                icon_rect = pygame.Rect(rect.x + 5, rect.y + 7, 44, 44)
                if frame:
                    surface.blit(pygame.transform.scale(frame, icon_rect.size), icon_rect)
                if icon:
                    surface.blit(pygame.transform.scale(icon, icon_rect.size), icon_rect)
                self.text(surface, self._fit_text(item["name"], self.font_sm, 70), (rect.x + 54, rect.y + 9), self.font_sm, rarity_colors.get(item["rarity"], COLOR_TEXT))
                self.text(surface, slot.upper(), (rect.x + 54, rect.y + 31), self.font_sm, COLOR_MUTED)
            else:
                self.text(surface, slot.upper(), (rect.centerx, rect.y + 14), self.font_sm, COLOR_MUTED, center=True)
                self.text(surface, "EMPTY", (rect.centerx, rect.y + 34), self.font_sm, COLOR_MUTED, center=True)

        self.text(surface, "GEAR INVENTORY — CLICK AN ITEM TO EQUIP", (right_rect.x + 20, right_rect.y + 142), self.font_sm, COLOR_AMBER)
        for index, rect in enumerate(self.equipment_inventory_rects()):
            item = inventory[index] if index < len(inventory) else None
            self._panel(surface, rect, COLOR_CYAN if item else COLOR_LINE)
            if item:
                if rect.collidepoint(mouse):
                    pygame.draw.rect(surface, COLOR_AMBER, rect, 2)
                    hovered = item
                icon_key, frame_key = get_gear_assets(item)
                frame, icon = game.assets.icons.get(frame_key), game.assets.icons.get(icon_key)
                icon_rect = pygame.Rect(rect.x + 4, rect.y + 5, 40, 40)
                if frame:
                    surface.blit(pygame.transform.scale(frame, icon_rect.size), icon_rect)
                if icon:
                    surface.blit(pygame.transform.scale(icon, icon_rect.size), icon_rect)
                self.text(surface, self._fit_text(item["name"], self.font_sm, 52), (rect.x + 48, rect.y + 7), self.font_sm, rarity_colors.get(item["rarity"], COLOR_TEXT))
                self.text(surface, item["type"].upper(), (rect.x + 48, rect.y + 27), self.font_sm, COLOR_MUTED)
            else:
                self.text(surface, "—", rect.center, self.font, COLOR_MUTED, center=True)

        detail = pygame.Rect(right_rect.x + 20, right_rect.y + 360, right_rect.width - 40, 140)
        self._panel(surface, detail, COLOR_CYAN)
        if hovered:
            icon_key, frame_key = get_gear_assets(hovered)
            frame, icon = game.assets.icons.get(frame_key), game.assets.icons.get(icon_key)
            icon_rect = pygame.Rect(detail.x + 14, detail.y + 18, 78, 78)
            if frame:
                surface.blit(pygame.transform.scale(frame, icon_rect.size), icon_rect)
            if icon:
                surface.blit(pygame.transform.scale(icon, icon_rect.size), icon_rect)
            text_x = detail.x + 108
            self.text(surface, self._fit_text(f"{hovered['name']} — {hovered['rarity']}", self.font, detail.width - 124), (text_x, detail.y + 16), self.font, rarity_colors.get(hovered["rarity"], COLOR_TEXT))
            self.text(surface, hovered["type"].upper(), (text_x, detail.y + 40), self.font_sm, COLOR_AMBER)
            stat_text = ", ".join(f"+{value} {stat}" for stat, value in hovered.get("stats", {}).items()) or "No direct stats"
            self.text(surface, self._fit_text(stat_text, self.font_sm, detail.width - 124), (text_x, detail.y + 62), self.font_sm, COLOR_TEXT)
            self._draw_multiline_text(surface, item_description(hovered), pygame.Rect(text_x, detail.y + 84, detail.width - 124, 38), self.font_sm, COLOR_MUTED)
        else:
            self.text(surface, "HOVER EQUIPMENT FOR STATS, EFFECT, AND LOADOUT ROLE", detail.center, self.font_sm, COLOR_MUTED, center=True)

    def skill_tree_node_rects(self) -> dict[str, pygame.Rect]:
        rects: dict[str, pygame.Rect] = {}
        panel_width, panel_height, gap_x, gap_y = 370, 230, 20, 18
        left, top = 65, 142
        for branch_index, branch in enumerate(SKILL_BRANCHES):
            panel_x = left + (branch_index % 3) * (panel_width + gap_x)
            panel_y = top + (branch_index // 3) * (panel_height + gap_y)
            for node_index, node in enumerate(NODES_BY_BRANCH[branch]):
                rects[node.id] = pygame.Rect(panel_x + 16, panel_y + 74 + node_index * 46, panel_width - 32, 36)
        return rects

    def skill_tree_refund_rect(self) -> pygame.Rect:
        return pygame.Rect(SCREEN_WIDTH // 2 - 150, 650, 300, 34)

    def draw_skill_tree(self, surface: pygame.Surface, game: object) -> None:
        selected_tank = game.save_data.get("selected_tank", "starter")
        points = available_skill_points(game.save_data, selected_tank)
        total = total_skill_points(game.save_data, selected_tank)
        learned = set(allocations(game.save_data, selected_tank))
        self.text(surface, "SKILL TREE", (SCREEN_WIDTH // 2, 30), self.font_lg, COLOR_GREEN, center=True)
        self.text(surface, f"{TANK_BY_ID[selected_tank].name.upper()}  •  {points} AVAILABLE / {total} EARNED  •  1 POINT PER 2 MINUTES SURVIVED", (SCREEN_WIDTH // 2, 52), self.font_sm, COLOR_MUTED, center=True)
        panel_width, panel_height, gap_x, gap_y = 370, 230, 20, 18
        left, top = 65, 142
        mouse = pygame.mouse.get_pos()
        hovered = None
        branch_colors = {"Strength": COLOR_RED, "Dexterity": COLOR_AMBER, "Vitality": COLOR_GREEN, "Tech": COLOR_BLUE, "Focus": COLOR_PURPLE, "Luck": COLOR_CYAN}
        rects = self.skill_tree_node_rects()
        for branch_index, branch in enumerate(SKILL_BRANCHES):
            panel = pygame.Rect(left + (branch_index % 3) * (panel_width + gap_x), top + (branch_index // 3) * (panel_height + gap_y), panel_width, panel_height)
            color = branch_colors[branch]
            self._panel(surface, panel, color)
            icon = game.assets.icons.get(f"skill_{branch.lower()}")
            if icon:
                self._blit_pixel_fit(surface, icon, pygame.Rect(panel.x + 16, panel.y + 13, 42, 42))
            self.text(surface, branch.upper(), (panel.x + 70, panel.y + 18), self.font, color)
            self.text(surface, {"Strength": "Damage • rams • impact", "Dexterity": "Handling • fire rate • cooldown", "Vitality": "Hull • repair • defense", "Tech": "Turrets • contracts • gadgets", "Focus": "Abilities • crit • status", "Luck": "Loot • chests • Blueprint"}[branch], (panel.x + 70, panel.y + 40), self.font_sm, COLOR_MUTED)
            previous_center = None
            for node in NODES_BY_BRANCH[branch]:
                rect = rects[node.id]
                if previous_center is not None:
                    pygame.draw.line(surface, color, previous_center, rect.midtop, 2)
                state = node_status(game.save_data, selected_tank, node)
                node_color = COLOR_GREEN if state == "Completed" else (color if state == "Available" else COLOR_LINE)
                self._button(surface, rect, node.name.upper(), node_color)
                if rect.collidepoint(mouse):
                    pygame.draw.rect(surface, COLOR_AMBER, rect, 2)
                    hovered = node
                previous_center = rect.midbottom
        self._button(surface, self.skill_tree_refund_rect(), "REFUND SELECTED TANK TREE", COLOR_RED if learned else COLOR_MUTED)
        if hovered is not None:
            self._draw_skill_tree_tooltip(surface, game, selected_tank, hovered, mouse)

    def _draw_skill_tree_tooltip(self, surface: pygame.Surface, game: object, tank_id: str, node: object, mouse: tuple[int, int]) -> None:
        width, height = 390, 154
        x = min(SCREEN_WIDTH - width - 14, max(14, mouse[0] + 16))
        y = min(SCREEN_HEIGHT - height - 14, max(122, mouse[1] + 16))
        rect = pygame.Rect(x, y, width, height)
        state = node_status(game.save_data, tank_id, node)
        color = COLOR_GREEN if state == "Completed" else (COLOR_CYAN if state == "Available" else COLOR_RED)
        self._panel(surface, rect, color)
        icon = game.assets.icons.get(node.icon)
        if icon:
            self._blit_pixel_fit(surface, icon, pygame.Rect(rect.x + 14, rect.y + 14, 54, 54))
        self.text(surface, node.name.upper(), (rect.x + 82, rect.y + 16), self.font, COLOR_TEXT)
        self.text(surface, node.branch.upper(), (rect.x + 82, rect.y + 40), self.font_sm, COLOR_AMBER)
        self._draw_multiline_text(surface, node.description, pygame.Rect(rect.x + 14, rect.y + 78, rect.width - 28, 32), self.font_sm, COLOR_TEXT)
        prerequisite = SKILL_BY_ID[node.prerequisite].name if node.prerequisite else "None"
        self.text(surface, f"Cost: {node.cost} point  •  Rank: {1 if state == 'Completed' else 0}/1", (rect.x + 14, rect.y + 116), self.font_sm, COLOR_CYAN)
        self.text(surface, self._fit_text(f"Prerequisite: {prerequisite}  •  {state.upper()}", self.font_sm, rect.width - 28), (rect.x + 14, rect.y + 136), self.font_sm, color)

    def draw_shop(self, surface: pygame.Surface, game: object) -> None:
        self._dark_overlay(surface, 232)
        self._button(surface, self.back_rect(), "BACK", COLOR_MUTED)
        self.text(surface, "UPGRADE SHOP", (SCREEN_WIDTH // 2, 58), self.font_xl, COLOR_AMBER, center=True)
        self.text(surface, f"Persistent coins: {game.save_data.get('coins', 0)}", (SCREEN_WIDTH // 2, 108), self.font, COLOR_CYAN, center=True)
        levels = game.save_data.get("universal_upgrades", {})
        for upgrade in META_UPGRADES:
            rect = self.shop_row_rects()[upgrade.id]
            level = int(levels.get(upgrade.id, 0))
            cost = upgrade.cost_for_level(level)
            self._draw_shop_row(surface, game, rect, upgrade, level, cost)

    def draw_unlocks(self, surface: pygame.Surface, game: object) -> None:
        game.progression_tab = "unlocks"
        self.draw_achievements(surface, game)

    def draw_research(self, surface: pygame.Surface, game: object) -> None:
        self._dark_overlay(surface, 232)
        self._button(surface, self.back_rect(), "BACK", COLOR_MUTED)
        self._draw_research_panel(surface, game)

    def _draw_research_panel(self, surface: pygame.Surface, game: object) -> None:
        category = getattr(game, "research_category", "All")
        self.text(surface, "RESEARCH LAB", (SCREEN_WIDTH // 2, 28), self.font_lg, COLOR_CYAN, center=True)
        self.text(surface, f"BLUEPRINT FRAGMENTS: {game.save_data.get('blueprint_fragments', 0)}", (1000, 38), self.font, COLOR_AMBER, center=False)
        for label, rect in self.research_filter_rects().items():
            color = COLOR_CYAN if label == category else COLOR_MUTED
            self._button(surface, rect, label.upper(), color)

        hovered: ResearchProject | None = None
        mouse = pygame.mouse.get_pos()
        cards = self.research_card_rects(category)
        for project in RESEARCH_PROJECTS:
            rect = cards.get(project.id)
            if rect is None:
                continue
            state = research_status(game.save_data, project)
            border = COLOR_GREEN if state == "Completed" else (COLOR_CYAN if state == "Available" else COLOR_LINE)
            self._panel(surface, rect, border)
            icon = game.assets.icons.get(project.icon)
            if icon:
                self._blit_pixel_fit(surface, icon, pygame.Rect(rect.x + 10, rect.y + 11, 54, 54))
            text_x = rect.x + 76
            self.text(surface, self._fit_text(project.name.upper(), self.font_sm, rect.width - 92), (text_x, rect.y + 12), self.font_sm, COLOR_TEXT)
            self.text(surface, self._fit_text(project.category.upper(), self.font_sm, rect.width - 92), (text_x, rect.y + 32), self.font_sm, COLOR_MUTED)
            state_color = COLOR_GREEN if state == "Completed" else (COLOR_AMBER if state == "Available" else COLOR_RED)
            label = "COMPLETED" if state == "Completed" else ("LOCKED" if state == "Locked" else f"{project.fragment_cost} BP")
            self.text(surface, label, (text_x, rect.y + 54), self.font_sm, state_color)
            if rect.collidepoint(mouse):
                hovered = project
                pygame.draw.rect(surface, COLOR_AMBER, rect, 2)
        if hovered is not None:
            self._draw_research_tooltip(surface, game, hovered, mouse)

    def _draw_research_tooltip(self, surface: pygame.Surface, game: object, project: object, mouse: tuple[int, int]) -> None:
        width, height = 360, 158
        x = min(SCREEN_WIDTH - width - 16, max(16, mouse[0] + 18))
        y = min(SCREEN_HEIGHT - height - 16, max(144, mouse[1] + 18))
        rect = pygame.Rect(x, y, width, height)
        state = research_status(game.save_data, project)
        color = COLOR_GREEN if state == "Completed" else (COLOR_CYAN if state == "Available" else COLOR_RED)
        self._panel(surface, rect, color)
        icon = game.assets.icons.get(project.icon)
        if icon:
            self._blit_pixel_fit(surface, icon, pygame.Rect(rect.x + 14, rect.y + 16, 62, 62))
        text_x = rect.x + 88
        self.text(surface, self._fit_text(project.name.upper(), self.font, rect.width - 104), (text_x, rect.y + 16), self.font, COLOR_TEXT)
        self.text(surface, project.category.upper(), (text_x, rect.y + 39), self.font_sm, COLOR_AMBER)
        self.text(surface, f"Cost: {project.fragment_cost} Blueprint Fragments", (text_x, rect.y + 59), self.font_sm, COLOR_CYAN)
        self._draw_multiline_text(surface, project.description, pygame.Rect(rect.x + 14, rect.y + 88, rect.width - 28, 32), self.font_sm, COLOR_TEXT)
        requirement = project.requirement or "Requirement: None"
        self.text(surface, self._fit_text(f"Requirement: {requirement}", self.font_sm, rect.width - 28), (rect.x + 14, rect.y + 122), self.font_sm, COLOR_MUTED)
        self.text(surface, f"Status: {state.upper()}", (rect.x + 14, rect.y + 140), self.font_sm, color)

    def draw_achievements(self, surface: pygame.Surface, game: object) -> None:
        self._dark_overlay(surface, 232)
        self._button(surface, self.back_rect(), "BACK", COLOR_MUTED)
        tab = getattr(game, "progression_tab", "achievements")
        tabs = self.progression_tab_rects()
        self._button(surface, tabs["achievements"], "ACHIEVEMENTS", COLOR_MAGENTA if tab == "achievements" else COLOR_MUTED)
        self._button(surface, tabs["unlocks"], "UNLOCKS", COLOR_GREEN if tab == "unlocks" else COLOR_MUTED)
        title = "ACHIEVEMENTS" if tab == "achievements" else "UNLOCKS"
        subtitle = "Milestone tracking and passive rewards." if tab == "achievements" else "New content earned automatically for future runs."
        self.text(surface, title, (SCREEN_WIDTH // 2, 36), self.font_lg, COLOR_MAGENTA if tab == "achievements" else COLOR_GREEN, center=True)
        self.text(surface, subtitle, (SCREEN_WIDTH // 2, 136), self.font_sm, COLOR_MUTED, center=True)

        mouse = pygame.mouse.get_pos()
        detail_rect = pygame.Rect(650, 160, 570, 440)
        hovered: object | None = None
        if tab == "achievements":
            page_count = max(1, (len(ACHIEVEMENTS) + 11) // 12)
            page = min(max(0, int(getattr(game, "achievement_page", 0))), page_count - 1)
            visible_achievements = ACHIEVEMENTS[page * 12 : (page + 1) * 12]
            unlocked = set(game.save_data.get("achievements", []))
            for achievement in visible_achievements:
                rect = self.achievement_tile_rects(page)[achievement.id]
                is_complete = achievement.id in unlocked
                self._panel(surface, rect, COLOR_GREEN if is_complete else COLOR_LINE)
                icon = game.assets.icons.get(get_achievement_icon_key(achievement.id) if is_complete else "ach_locked", game.assets.icons.get("ach_unlocked"))
                if icon:
                    self._blit_pixel_fit(surface, icon, pygame.Rect(rect.centerx - 22, rect.y + 7, 44, 44))
                self._draw_multiline_text(surface, achievement.name, pygame.Rect(rect.x + 8, rect.y + 60, rect.width - 16, 36), self.font_sm, COLOR_TEXT, center=True)
                if rect.collidepoint(mouse):
                    hovered = achievement
                    pygame.draw.rect(surface, COLOR_AMBER, rect, 2)
            page_rects = self.achievement_page_rects()
            self._button(surface, page_rects["previous"], "PREVIOUS", COLOR_CYAN if page > 0 else COLOR_MUTED)
            self.text(surface, f"PAGE {page + 1}/{page_count}", (330, 656), self.font_sm, COLOR_TEXT, center=True)
            self._button(surface, page_rects["next"], "NEXT", COLOR_CYAN if page < page_count - 1 else COLOR_MUTED)
            self._draw_achievement_tooltip(surface, game, hovered, detail_rect)
        else:
            completed = set(game.save_data.get("unlocks_completed", []))
            recent = set(game.save_data.get("unlocks_new", []))
            for unlock in UNLOCKS:
                rect = self.unlock_tile_rects()[unlock.id]
                is_complete = unlock.id in completed
                self._panel(surface, rect, COLOR_GREEN if is_complete else COLOR_LINE)
                icon = game.assets.icons.get(unlock.icon, game.assets.icons.get("ach_locked"))
                if icon:
                    self._blit_pixel_fit(surface, icon, pygame.Rect(rect.centerx - 25, rect.y + 8, 50, 50))
                self._draw_multiline_text(surface, unlock.name, pygame.Rect(rect.x + 8, rect.y + 64, rect.width - 16, 42), self.font_sm, COLOR_TEXT, center=True)
                if unlock.id in recent:
                    self.text(surface, "NEW", (rect.right - 4, rect.y + 4), self.font_sm, COLOR_GREEN, center=True)
                if rect.collidepoint(mouse):
                    hovered = unlock
                    pygame.draw.rect(surface, COLOR_AMBER, rect, 2)
            self._draw_unlock_tooltip(surface, game, hovered, detail_rect)

    def _draw_achievement_tooltip(self, surface: pygame.Surface, game: object, achievement: object | None, rect: pygame.Rect) -> None:
        self._panel(surface, rect, COLOR_MAGENTA)
        if achievement is None:
            self.text(surface, "HOVER A CARD", rect.center, self.font, COLOR_MUTED, center=True)
            return
        completed = achievement.id in set(game.save_data.get("achievements", []))
        current, target = progress_for(achievement, game.save_data)
        icon = game.assets.icons.get(get_achievement_icon_key(achievement.id), game.assets.icons.get("ach_unlocked"))
        if icon:
            self._blit_pixel_fit(surface, icon, pygame.Rect(rect.x + 24, rect.y + 24, 76, 76))
        self.text(surface, self._fit_text(achievement.name.upper(), self.font_lg, rect.width - 136), (rect.x + 120, rect.y + 28), self.font_lg, COLOR_CYAN)
        self.text(surface, "CATEGORY: ACHIEVEMENT", (rect.x + 120, rect.y + 64), self.font_sm, COLOR_AMBER)
        self._draw_multiline_text(surface, f"Requirement: {achievement.description}", pygame.Rect(rect.x + 24, rect.y + 124, rect.width - 48, 48), self.font, COLOR_TEXT)
        self.draw_bar(surface, pygame.Rect(rect.x + 24, rect.y + 188, rect.width - 48, 18), current, target, COLOR_GREEN if completed else COLOR_CYAN)
        self.text(surface, f"Progress: {current}/{target}", (rect.x + 24, rect.y + 214), self.font_sm, COLOR_TEXT)
        self.text(surface, f"Reward: {self._reward_text(achievement.reward, achievement.reward_value)}", (rect.x + 24, rect.y + 256), self.font, COLOR_AMBER)
        state = "COMPLETED" if completed else "LOCKED"
        self.text(surface, f"Status: {state}", (rect.x + 24, rect.y + 300), self.font, COLOR_GREEN if completed else COLOR_RED)

    def _draw_unlock_tooltip(self, surface: pygame.Surface, game: object, unlock: object | None, rect: pygame.Rect) -> None:
        self._panel(surface, rect, COLOR_GREEN)
        if unlock is None:
            accent = game.assets.icons.get("progression_tooltip_accent", game.assets.icons.get("unlock_relic_prototypes"))
            if accent:
                self._blit_pixel_fit(surface, accent, pygame.Rect(rect.centerx - 48, rect.y + 86, 96, 96))
            self.text(surface, "HOVER AN UNLOCK CARD", (rect.centerx, rect.y + 230), self.font, COLOR_MUTED, center=True)
            return
        completed = unlock.id in set(game.save_data.get("unlocks_completed", []))
        current = min(unlock_progress(game.save_data, unlock), unlock.target)
        icon = game.assets.icons.get(unlock.icon, game.assets.icons.get("ach_locked"))
        if icon:
            self._blit_pixel_fit(surface, icon, pygame.Rect(rect.x + 24, rect.y + 24, 76, 76))
        self.text(surface, self._fit_text(unlock.name.upper(), self.font_lg, rect.width - 136), (rect.x + 120, rect.y + 28), self.font_lg, COLOR_CYAN)
        self.text(surface, f"CATEGORY: {unlock.category.upper()}", (rect.x + 120, rect.y + 64), self.font_sm, COLOR_AMBER)
        self._draw_multiline_text(surface, f"Requirement: {unlock.requirement}", pygame.Rect(rect.x + 24, rect.y + 124, rect.width - 48, 42), self.font, COLOR_TEXT)
        self.draw_bar(surface, pygame.Rect(rect.x + 24, rect.y + 188, rect.width - 48, 18), current, unlock.target, COLOR_GREEN if completed else COLOR_CYAN)
        self.text(surface, f"Progress: {current}/{unlock.target}", (rect.x + 24, rect.y + 214), self.font_sm, COLOR_TEXT)
        self._draw_multiline_text(surface, f"Reward: {unlock.reward}", pygame.Rect(rect.x + 24, rect.y + 252, rect.width - 48, 46), self.font, COLOR_AMBER)
        self.text(surface, f"Status: {'UNLOCKED' if completed else 'LOCKED'}", (rect.x + 24, rect.y + 320), self.font, COLOR_GREEN if completed else COLOR_RED)

    def draw_stage_select(self, surface: pygame.Surface, game: object) -> None:
        self._dark_overlay(surface, 230)
        self._button(surface, self.back_rect(), "BACK", COLOR_MUTED)
        self.text(surface, "STAGE PREVIEW", (SCREEN_WIDTH // 2, 64), self.font_xl, COLOR_CYAN, center=True)
        self.text(surface, "Choose a salvage zone, contract identity, and battlefield modifier for your next run", (SCREEN_WIDTH // 2, 122), self.font, COLOR_MUTED, center=True)
        selected = game.save_data.get("selected_stage")
        for stage in STAGES:
            rect = self.stage_card_rects()[stage.id]
            self._panel(surface, rect, color=COLOR_AMBER if stage.id == selected else COLOR_LINE)
            tiles = game.assets.tilesets[stage.tileset]["floor"]
            floor_base = {
                "scrap": (29, 32, 38),
                "desert": (182, 135, 73),
                "frozen": (84, 145, 171),
                "city": (45, 48, 68),
                "jungle": (39, 78, 52),
            }[stage.tileset]
            for x in range(3):
                for y in range(2):
                    tile_rect = pygame.Rect(rect.x + 18 + x * 46, rect.y + 16 + y * 46, 46, 46)
                    pygame.draw.rect(surface, floor_base, tile_rect)
                    surface.blit(pygame.transform.scale(tiles[(x + y) % len(tiles)], (46, 46)), tile_rect)
            landmarks = game.assets.landmarks.get(stage.id, [])
            if landmarks:
                self._blit_pixel_fit(surface, landmarks[0], pygame.Rect(rect.right - 104, rect.y + 14, 82, 72))
            self.text(surface, stage.name, (rect.x + 18, rect.y + 112), self.font, COLOR_CYAN)
            self._draw_multiline_text(surface, stage.description, pygame.Rect(rect.x + 18, rect.y + 138, rect.width - 36, 36), self.font_sm, COLOR_TEXT)
            contract = f"Contract: {stage.contract_name} ({stage.contract_goal})"
            self.text(surface, self._fit_text(contract, self.font_sm, rect.width - 36), (rect.x + 18, rect.y + 178), self.font_sm, COLOR_AMBER)
            self.text(surface, self._fit_text(stage.modifier_name, self.font_sm, rect.width - 36), (rect.x + 18, rect.y + 198), self.font_sm, COLOR_CYAN)
            status = "SELECTED" if stage.id == selected else "CLICK TO SELECT"
            self.text(surface, status, (rect.centerx, rect.bottom - 16), self.font_sm, COLOR_AMBER if stage.id == selected else COLOR_GREEN, center=True)

    def draw_pause(self, surface: pygame.Surface, game: object) -> None:
        self._dark_overlay(surface, 175)
        panel = pygame.Rect(SCREEN_WIDTH // 2 - 420, SCREEN_HEIGHT // 2 - 220, 840, 440)
        self._panel(surface, panel)
        self.text(surface, "PAUSED", (panel.centerx, panel.y + 42), self.font_xl, COLOR_CYAN, center=True)
        labels = {
            "resume": ("RESUME", COLOR_CYAN),
            "menu": ("ABANDON RUN", COLOR_AMBER),
            "quit": ("QUIT GAME", COLOR_RED),
        }
        for key, rect in self.pause_button_rects().items():
            label, color = labels[key]
            self._button(surface, rect, label, color)

        summary_x = SCREEN_WIDTH // 2 - 40
        summary_y = panel.y + 100
        pygame.draw.line(surface, COLOR_LINE, (summary_x - 28, panel.y + 84), (summary_x - 28, panel.bottom - 28), 2)
        self.text(surface, "ACTIVE BUILD", (summary_x, summary_y), self.font, COLOR_AMBER)
        passives = get_active_passives(game.player)
        evolutions = get_active_evolutions(game.player)
        if not passives and not evolutions:
            self.text(surface, "No family passives unlocked yet.", (summary_x, summary_y + 36), self.font_sm, COLOR_MUTED)
            self.text(surface, "Stack matching families to unlock build bonuses.", (summary_x, summary_y + 58), self.font_sm, COLOR_MUTED)
            return
        rows: list[tuple[str, str, str, bool]] = []
        for evolution in evolutions:
            rows.append((evolution.family, f"EVOLUTION: {evolution.name}", evolution.description, True))
        for passive in passives:
            rows.append((passive.family, f"{passive.family} {passive.roman_tier} - {passive.name}", passive.description, False))
        for idx, (family, label, description, is_evolution) in enumerate(rows[:8]):
            y = summary_y + 34 + idx * 38
            color = COLOR_AMBER if is_evolution else self._family_color(family)
            label_x = summary_x
            if is_evolution:
                icon = game.assets.icons.get(f"evolution_{family.lower()}")
                if icon:
                    self._blit_pixel_fit(surface, icon, pygame.Rect(summary_x, y - 2, 26, 26))
                    label_x += 32
            self.text(surface, self._fit_text(label, self.font_sm, 390 - (label_x - summary_x)), (label_x, y), self.font_sm, color)
            self.text(surface, self._fit_text(description, self.font_sm, 372 - (label_x - summary_x)), (label_x + 18, y + 15), self.font_sm, COLOR_MUTED)

    def draw_level_up(self, surface: pygame.Surface, game: object, choices: Sequence[Upgrade]) -> None:
        self._dark_overlay(surface, 205)
        self.text(surface, "LEVEL UP", (SCREEN_WIDTH // 2, 134), self.font_xl, COLOR_AMBER, center=True)
        self.text(surface, "Choose one upgrade", (SCREEN_WIDTH // 2, 188), self.font_sm, COLOR_MUTED, center=True)
        for idx, (rect, upgrade) in enumerate(zip(self.level_card_rects(len(choices)), choices), start=1):
            color = self._upgrade_color(upgrade)
            self._panel(surface, rect, color=color)
            if upgrade.rarity == "evolution":
                pygame.draw.rect(surface, color, rect.inflate(-8, -8), 2)
            family = upgrade_family(upgrade)
            evolution_icon = f"evolution_{family.lower()}" if upgrade.rarity == "evolution" else ""
            # Use individual generated level-up art first. Evolution cards
            # prefer their matching tank portrait; the family icon remains a fallback.
            icon = game.assets.icons.get(evolution_icon) or game.assets.icons.get(upgrade.id, game.assets.icons.get(upgrade.icon))
            if icon:
                self._blit_pixel_fit(surface, icon, pygame.Rect(rect.centerx - 26, rect.y + 22, 52, 52))
            self.text(surface, f"{idx}", (rect.x + 16, rect.y + 16), self.font, COLOR_MUTED)
            title = f"EVOLUTION: {upgrade.name}" if upgrade.rarity == "evolution" else upgrade.name
            self.text(surface, self._fit_text(title, self.font, rect.width - 28), (rect.centerx, rect.y + 82), self.font, color, center=True)
            tier = tier_text(upgrade)
            tier = {"Tier I": "I", "Tier II": "II", "Tier III": "III"}.get(tier, tier)
            badge = f"{family_label(family)} | {tier}"
            if upgrade.rarity != "common":
                badge = f"{badge} | {upgrade.rarity.title()}"
            self.text(surface, self._fit_text(badge, self.font_sm, rect.width - 40), (rect.centerx, rect.y + 110), self.font_sm, COLOR_MUTED, center=True)
            self._draw_multiline_text(surface, upgrade.description, pygame.Rect(rect.x + 24, rect.y + 142, rect.width - 48, 48), self.font_sm, COLOR_TEXT)
            progress = family_progress_text(game.player, upgrade)
            self.text(surface, self._fit_text(progress, self.font_sm, rect.width - 48), (rect.x + 24, rect.y + 208), self.font_sm, color)
            hint = unlock_hint_text(game.player, upgrade)
            if hint:
                self.text(surface, self._fit_text(hint, self.font_sm, rect.width - 48), (rect.x + 24, rect.y + 232), self.font_sm, COLOR_AMBER)
            self.text(surface, self._fit_text(stack_text(game.player, upgrade), self.font_sm, 120), (rect.x + 24, rect.bottom - 28), self.font_sm, COLOR_CYAN)
        self.text(surface, "PRESS 1 / 2 / 3 OR CLICK TO CHOOSE", (SCREEN_WIDTH // 2, 662), self.font_sm, COLOR_AMBER, center=True)

    def draw_game_over(self, surface: pygame.Surface, game: object) -> None:
        self._dark_overlay(surface, 215)
        self.text(surface, "SCRAPPED", (SCREEN_WIDTH // 2, 142), self.font_xl, COLOR_RED, center=True)
        tank_name = TANK_BY_ID.get(game.stats.tank_used, TANK_BY_ID["starter"]).name
        lines = [
            f"Time survived: {format_time(game.stats.time_survived)}",
            f"Tank used: {tank_name}",
            f"Final level: {game.player.level}",
            f"Enemies defeated: {game.stats.defeated}",
            f"Elemental combos: {game.stats.elemental_combos}",
            f"Blueprint fragments: {game.save_data.get('blueprint_fragments', 0)}",
            f"Run coins earned: {game.stats.run_coins}",
            f"Persistent coins: {game.save_data.get('coins', 0)}",
        ]
        if game.stats.chests_opened or game.stats.gear_found:
            lines.append(f"Chests opened: {game.stats.chests_opened}  Gear found: {game.stats.gear_found}")
        if game.save_data.get("loot_unlocked", False):
            lines.append("Meta loot: ONLINE")
        for i, line in enumerate(lines):
            color = COLOR_AMBER if "coins" in line.lower() else COLOR_TEXT
            if "Meta loot" in line:
                color = COLOR_MAGENTA
            self.text(surface, line, (SCREEN_WIDTH // 2, 218 + i * 28), self.font, color, center=True)
        self._button(surface, self.game_over_restart_rect(), "RUN AGAIN", COLOR_CYAN)
        self._button(surface, self.game_over_menu_rect(), "GARAGE", COLOR_GREEN)

    def draw_passive_popups(self, surface: pygame.Surface, game: object) -> None:
        popups = getattr(game, "passive_popups", [])
        if not popups:
            return
        passive, ttl = popups[-1]
        family = getattr(passive, "family", "Build")
        if family in ("", "Core") and getattr(passive, "rarity", "") == "evolution":
            family = upgrade_family(passive)
        color = self._family_color(family)
        is_evolution = (
            getattr(passive, "rarity", "") == "evolution"
            or (
                hasattr(passive, "threshold")
                and getattr(passive, "id", "") in getattr(game.player, "evolutions", set())
                and getattr(passive, "roman_tier", None) is None
            )
        )
        alpha = int(255 * min(1.0, ttl / 0.35))
        rect = pygame.Rect(SCREEN_WIDTH // 2 - 380, 74, 760, 160) if is_evolution else pygame.Rect(SCREEN_WIDTH // 2 - 290, 92, 580, 118)
        backing = pygame.Surface(rect.size, pygame.SRCALPHA)
        backing.fill((*COLOR_PANEL_DARK, min(218, alpha)))
        surface.blit(backing, rect)
        pygame.draw.rect(surface, (0, 0, 0), rect.inflate(6, 6), 3)
        pygame.draw.rect(surface, COLOR_LINE, rect, 2)
        pygame.draw.line(surface, color, rect.topleft, (rect.right, rect.y), 3)
        if is_evolution:
            art = game.assets.icons.get(f"evolution_{family.lower()}")
            if art:
                self._blit_pixel_fit(surface, art, pygame.Rect(rect.x + 22, rect.y + 26, 108, 108))
            text_center = rect.x + 134 + (rect.width - 150) // 2
            self.text(surface, f"{family.upper()} EVOLUTION UNLOCKED", (text_center, rect.y + 18), self.font, color, center=True)
            self.text(surface, getattr(passive, "name", "Evolution"), (text_center, rect.y + 52), self.font_lg, COLOR_TEXT, center=True)
            threshold = getattr(passive, "threshold", 0)
            reason = f"{threshold} {family} upgrades" if threshold else "Run evolution acquired"
            self.text(surface, reason, (text_center, rect.y + 92), self.font_sm, COLOR_MUTED, center=True)
            self.text(surface, self._fit_text(getattr(passive, "description", ""), self.font_sm, rect.width - 188), (text_center, rect.y + 118), self.font_sm, color, center=True)
        else:
            self.text(surface, f"{family.upper()} SYNERGY", (rect.centerx, rect.y + 16), self.font_sm, color, center=True)
            self.text(surface, getattr(passive, "name", "Passive"), (rect.centerx, rect.y + 42), self.font, COLOR_TEXT, center=True)
            reason = f"{getattr(passive, 'threshold', 0)} {family} upgrades unlocked this passive"
            self.text(surface, reason, (rect.centerx, rect.y + 70), self.font_sm, COLOR_MUTED, center=True)
            self.text(surface, self._fit_text(getattr(passive, "description", ""), self.font_sm, rect.width - 48), (rect.centerx, rect.y + 92), self.font_sm, color, center=True)

    def _draw_shop_row(self, surface: pygame.Surface, game: object, rect: pygame.Rect, upgrade: object, level: int, cost: int | None) -> None:
        mouse = pygame.mouse.get_pos()
        hovered = rect.collidepoint(mouse)
        can_buy = cost is not None and game.save_data.get("coins", 0) >= cost
        border = COLOR_CYAN if hovered else COLOR_LINE
        if cost is None:
            border = COLOR_GREEN
        self._panel(surface, rect, color=border)
        if hovered:
            pygame.draw.rect(surface, (35, 45, 58), rect.inflate(-6, -6), 1)

        layout = self._shop_row_layout(rect)
        icon_rect = layout["icon"]
        text_rect = layout["text"]
        button = layout["button"]
        pygame.draw.rect(surface, COLOR_PANEL_DARK, icon_rect)
        pygame.draw.rect(surface, COLOR_LINE, icon_rect, 2)
        icon = game.assets.icons.get(upgrade.icon)
        if icon:
            scaled = pygame.transform.scale(icon, (30, 30))
            surface.blit(scaled, scaled.get_rect(center=icon_rect.center))

        self.text(surface, self._fit_text(upgrade.name, self.font, text_rect.width), (text_rect.x, rect.y + 10), self.font, COLOR_TEXT)
        self.text(surface, self._fit_text(upgrade.description, self.font_sm, text_rect.width), (text_rect.x, rect.y + 36), self.font_sm, COLOR_MUTED)
        self.text(surface, f"Lv {level}/{upgrade.max_level}", (text_rect.x, rect.y + 56), self.font_sm, COLOR_CYAN)

        button_color = COLOR_GREEN if cost is None else (COLOR_AMBER if can_buy else COLOR_RED)
        pygame.draw.rect(surface, COLOR_PANEL_DARK, button)
        pygame.draw.rect(surface, button_color, button, 2)
        label = "MAX" if cost is None else f"{cost} COINS"
        self.text(surface, label, button.center, self.font_sm, button_color, center=True)

    def _shop_row_layout(self, rect: pygame.Rect) -> dict[str, pygame.Rect]:
        icon = pygame.Rect(rect.x + 20, rect.centery - 22, 44, 44)
        button = pygame.Rect(rect.right - 144, rect.centery - 17, 122, 34)
        text_x = icon.right + 20
        text_w = max(120, button.x - text_x - 18)
        return {
            "icon": icon,
            "text": pygame.Rect(text_x, rect.y + 8, text_w, rect.height - 16),
            "button": button,
        }

    def _reward_text(self, reward: str, value: float) -> str:
        if reward == "pickup_radius":
            return f"+{int(value)} radius"
        if reward == "ability_cooldown":
            return f"-{int(value * 100)}% ability cooldown"
        if reward == "regen_rate":
            return f"+{int(value * 100)}% regen rate"
        if reward == "drop_rate":
            return f"+{int(value * 100)}% chest quality"
        return f"+{int(value * 100)}% {reward.replace('_', ' ')}"

    def _family_color(self, family: str) -> tuple[int, int, int]:
        family_colors = {
            "Projectile": COLOR_AMBER,
            "Fire": COLOR_RED,
            "Cryo": COLOR_CYAN,
            "Lightning": COLOR_BLUE,
            "Poison": COLOR_GREEN,
            "Defense": COLOR_BLUE,
            "Summon": COLOR_GREEN,
            "Mobility": COLOR_MAGENTA,
            "Economy": COLOR_AMBER,
            "Ability": COLOR_PURPLE,
            "Critical": COLOR_RED,
            "Explosion": COLOR_MAGENTA,
        }
        return family_colors.get(family, COLOR_CYAN)

    def _upgrade_color(self, upgrade: Upgrade) -> tuple[int, int, int]:
        if upgrade.rarity == "evolution":
            return COLOR_MAGENTA
        if upgrade.rarity == "epic":
            return COLOR_PURPLE
        if upgrade.rarity == "rare":
            return self._family_color(upgrade_family(upgrade))
        return self._family_color(upgrade_family(upgrade))

    def _fit_text(self, value: str, font: pygame.font.Font, max_width: int) -> str:
        if font.size(value)[0] <= max_width:
            return value
        ellipsis = "..."
        trimmed = value
        while trimmed and font.size(trimmed + ellipsis)[0] > max_width:
            trimmed = trimmed[:-1]
        return trimmed.rstrip() + ellipsis

    def _panel(self, surface: pygame.Surface, rect: pygame.Rect, color: tuple[int, int, int] = COLOR_CYAN) -> None:
        pygame.draw.rect(surface, (0, 0, 0), rect.inflate(8, 8))
        pygame.draw.rect(surface, COLOR_PANEL, rect)
        pygame.draw.rect(surface, COLOR_LINE, rect, 2)
        pygame.draw.line(surface, color, rect.topleft, (rect.right, rect.y), 2)

    def _button(self, surface: pygame.Surface, rect: pygame.Rect, label: str, color: tuple[int, int, int]) -> None:
        pygame.draw.rect(surface, (0, 0, 0), rect.inflate(7, 7))
        pygame.draw.rect(surface, COLOR_PANEL, rect)
        pygame.draw.rect(surface, color, rect, 3)
        font = self.font if rect.height <= 44 else self.font_lg
        self.text(surface, label, rect.center, font, color, center=True)

    def _dark_overlay(self, surface: pygame.Surface, alpha: int) -> None:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((*COLOR_BG, alpha))
        surface.blit(overlay, (0, 0))

    def _draw_multiline_text(self, surface: pygame.Surface, text: str, rect: pygame.Rect, font: pygame.font.Font, color: tuple[int, int, int], center: bool = False) -> None:
        words = text.split(" ")
        lines = []
        current_line = []
        for word in words:
            test_line = " ".join(current_line + [word])
            if font.size(test_line)[0] < rect.width:
                current_line.append(word)
            else:
                lines.append(" ".join(current_line))
                current_line = [word]
        if current_line:
            lines.append(" ".join(current_line))
            
        y = rect.y
        for line in lines:
            if y + font.get_linesize() > rect.bottom:
                break
            self.text(surface, line, (rect.centerx if center else rect.x, y), font, color, center=center)
            y += font.get_linesize()

    def get_achievement_at(self, pos: tuple[int, int]) -> object | None:
        rects = self.achievement_tile_rects()
        for achievement in ACHIEVEMENTS:
            rect = rects.get(achievement.id)
            if rect is not None and rect.collidepoint(pos):
                return achievement
        return None
