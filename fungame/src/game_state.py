from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ScreenState(str, Enum):
    MENU = "menu"
    TANK_SELECT = "tank_select"
    SHOP = "shop"
    UNLOCKS = "unlocks"
    RESEARCH = "research"
    ACHIEVEMENTS = "achievements"
    STAGE_SELECT = "stage_select"
    PLAYING = "playing"
    PAUSED = "paused"
    LEVEL_UP = "level_up"
    GAME_OVER = "game_over"


@dataclass
class RunStats:
    time_survived: float = 0.0
    score: int = 0
    run_coins: int = 0
    banked_coins: int = 0
    defeated: int = 0
    bosses_defeated: int = 0
    chests_opened: int = 0
    gear_found: int = 0
    unique_gear_found: int = 0
    abilities_cast: int = 0
    elemental_combos: int = 0
    contracts_completed: int = 0
    elites_defeated: int = 0
    salvage_surges_completed: int = 0
    tank_used: str = "starter"
    min_health_pct: float = 1.0

    def reset(self) -> None:
        self.time_survived = 0.0
        self.score = 0
        self.run_coins = 0
        self.banked_coins = 0
        self.defeated = 0
        self.bosses_defeated = 0
        self.chests_opened = 0
        self.gear_found = 0
        self.unique_gear_found = 0
        self.abilities_cast = 0
        self.elemental_combos = 0
        self.contracts_completed = 0
        self.elites_defeated = 0
        self.salvage_surges_completed = 0
        self.tank_used = "starter"
        self.min_health_pct = 1.0
