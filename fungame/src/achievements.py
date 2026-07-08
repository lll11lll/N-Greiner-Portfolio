from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Achievement:
    id: str
    name: str
    description: str
    stat: str
    target: int
    reward: str
    reward_value: float
    icon: str


ACHIEVEMENTS: tuple[Achievement, ...] = (
    Achievement("survive_5", "Stay Online", "Survive 5 minutes.", "best_time", 300, "max_health", 0.02, "ach_survive"),
    Achievement("survive_10", "Long Haul", "Survive 10 minutes.", "best_time", 600, "xp_gain", 0.02, "ach_survive"),
    Achievement("survive_15", "Infinite Power", "Survive 15 minutes.", "best_time", 900, "move_speed", 0.03, "ach_survive"),
    Achievement("survive_20", "Scrap Marathon", "Survive 20 minutes.", "best_time", 1200, "regen_rate", 0.04, "ach_survive"),
    Achievement("survive_30", "Endless Engine", "Survive 30 minutes.", "best_time", 1800, "ability_cooldown", 0.03, "ach_survive"),
    Achievement("first_boss", "Boss Breaker", "Defeat a boss.", "total_bosses", 1, "boss_damage", 0.02, "ach_boss"),
    Achievement("kills_500", "Scrap Sweeper", "Defeat 500 enemies.", "total_kills", 500, "fire_rate", 0.01, "ach_kill"),
    Achievement("kills_5000", "Arena Cleaner", "Defeat 5000 enemies.", "total_kills", 5000, "damage", 0.02, "ach_kill"),
    Achievement("kills_10000", "Unstoppable", "Defeat 10000 enemies.", "total_kills", 10000, "damage", 0.03, "ach_kill"),
    Achievement("kills_25000", "Machine Graveyard", "Defeat 25000 enemies.", "total_kills", 25000, "damage", 0.04, "ach_kill"),
    Achievement("coins_100", "Coin Cache", "Bank 100 coins.", "total_coins_earned", 100, "coin_gain", 0.02, "ach_coin"),
    Achievement("coins_1000", "Scrap Tycoon", "Bank 1000 coins.", "total_coins_earned", 1000, "coin_gain", 0.03, "ach_coin"),
    Achievement("coins_5000", "Gold Vault", "Bank 5000 coins.", "total_coins_earned", 5000, "coin_gain", 0.05, "ach_coin"),
    Achievement("coins_20000", "Neon Mint", "Bank 20000 coins.", "total_coins_earned", 20000, "coin_gain", 0.05, "ach_coin"),
    Achievement("level_10", "Fast Learner", "Reach level 10 in a run.", "best_level", 10, "xp_gain", 0.02, "ach_level"),
    Achievement("level_25", "Overbuilt", "Reach level 25 in a run.", "best_level", 25, "pickup_radius", 4.0, "ach_level"),
    Achievement("level_40", "Core Overload", "Reach level 40 in a run.", "best_level", 40, "fire_rate", 0.03, "ach_level"),
    Achievement("level_60", "Prototype Limit", "Reach level 60 in a run.", "best_level", 60, "xp_gain", 0.04, "ach_level"),
    Achievement("starter_clear", "Starter Veteran", "Survive 8 minutes with Starter.", "starter_best_time", 480, "max_health", 0.02, "ach_tank"),
    Achievement("sniper_clear", "Scope Discipline", "Survive 8 minutes with Sniper.", "sniper_best_time", 480, "boss_damage", 0.02, "ach_tank"),
    Achievement("engineer_clear", "Field Builder", "Survive 8 minutes with Engineer.", "engineer_best_time", 480, "luck", 0.01, "ach_tank"),
    Achievement("twin_shot_clear", "Double Caliber", "Survive 8 minutes with Twin-Shot.", "twin_shot_best_time", 480, "fire_rate", 0.02, "ach_tank"),
    Achievement("flame_caster_clear", "Inferno Core", "Survive 8 minutes with Flame Caster.", "flame_caster_best_time", 480, "damage", 0.02, "ach_tank"),
    Achievement("shopper_5", "Garage Regular", "Purchase 5 upgrades.", "upgrades_purchased", 5, "pickup_radius", 3.0, "ach_shop"),
    Achievement("upgrades_20", "Workshop Master", "Purchase 20 upgrades.", "upgrades_purchased", 20, "pickup_radius", 5.0, "ach_shop"),
    Achievement("all_tanks", "Full Garage", "Unlock every tank.", "unlocked_tank_count", 5, "coin_gain", 0.02, "ach_tank"),
    Achievement("boss_triplet", "Triple Threat", "Defeat 3 bosses in one run.", "best_run_bosses", 3, "damage", 0.02, "ach_boss"),
    Achievement("boss_ten", "Boss Decimator", "Defeat 10 bosses.", "total_bosses", 10, "boss_damage", 0.04, "ach_boss"),
    Achievement("boss_25", "Boss Breakyard", "Defeat 25 bosses.", "total_bosses", 25, "boss_damage", 0.04, "ach_boss"),
    Achievement("no_panic", "Clean Wiring", "Survive 5 minutes above 25% HP.", "clean_run_time", 300, "move_speed", 0.01, "ach_shield"),
    Achievement("clean_10", "No Sparks Lost", "Survive 10 minutes above 25% HP.", "clean_run_time", 600, "max_health", 0.03, "ach_shield"),
    Achievement("first_chest", "Crate Popper", "Open your first chest.", "total_chests_opened", 1, "luck", 0.01, "ach_coin"),
    Achievement("chests_25", "Loot Circuit", "Open 25 chests.", "total_chests_opened", 25, "drop_rate", 0.03, "ach_coin"),
    Achievement("chests_100", "Scrap Prospector", "Open 100 chests.", "total_chests_opened", 100, "drop_rate", 0.05, "ach_coin"),
    Achievement("first_gear", "First Fit", "Find your first gear item.", "total_gear_found", 1, "pickup_radius", 3.0, "ach_shop"),
    Achievement("gear_20", "Loaded Garage", "Find 20 gear items.", "total_gear_found", 20, "luck", 0.02, "ach_shop"),
    Achievement("gear_100", "Arsenal Wall", "Find 100 gear items.", "total_gear_found", 100, "drop_rate", 0.06, "ach_shop"),
    Achievement("first_unique", "Prototype Spark", "Find a Unique gear item.", "total_unique_gear_found", 1, "ability_cooldown", 0.02, "ach_shop"),
    Achievement("unique_5", "Signature Build", "Find 5 Unique gear items.", "total_unique_gear_found", 5, "luck", 0.03, "ach_shop"),
    Achievement("abilities_25", "Hotkey Habit", "Cast 25 active skills.", "total_abilities_cast", 25, "ability_cooldown", 0.02, "ach_level"),
    Achievement("abilities_250", "Cast Engine", "Cast 250 active skills.", "total_abilities_cast", 250, "ability_cooldown", 0.04, "ach_level"),
)

ACHIEVEMENT_BY_ID = {achievement.id: achievement for achievement in ACHIEVEMENTS}


def default_stats() -> dict[str, int]:
    return {
        "total_kills": 0,
        "total_bosses": 0,
        "total_coins_earned": 0,
        "best_time": 0,
        "best_level": 1,
        "best_run_bosses": 0,
        "clean_run_time": 0,
        "starter_best_time": 0,
        "sniper_best_time": 0,
        "engineer_best_time": 0,
        "twin_shot_best_time": 0,
        "flame_caster_best_time": 0,
        "upgrades_purchased": 0,
        "unlocked_tank_count": 1,
        "total_chests_opened": 0,
        "total_gear_found": 0,
        "total_unique_gear_found": 0,
        "total_abilities_cast": 0,
    }


def evaluate_achievements(save_data: dict[str, Any]) -> list[Achievement]:
    unlocked = set(save_data.get("achievements", []))
    stats = save_data.get("stats", {})
    newly_unlocked: list[Achievement] = []
    for achievement in ACHIEVEMENTS:
        if achievement.id in unlocked:
            continue
        if int(stats.get(achievement.stat, 0)) >= achievement.target:
            unlocked.add(achievement.id)
            newly_unlocked.append(achievement)
    if newly_unlocked:
        save_data["achievements"] = sorted(unlocked)
    return newly_unlocked


def achievement_bonuses(save_data: dict[str, Any]) -> dict[str, float]:
    bonuses = {
        "max_health": 0.0,
        "coin_gain": 0.0,
        "xp_gain": 0.0,
        "move_speed": 0.0,
        "fire_rate": 0.0,
        "damage": 0.0,
        "pickup_radius": 0.0,
        "boss_damage": 0.0,
        "luck": 0.0,
        "drop_rate": 0.0,
        "regen_rate": 0.0,
        "ability_cooldown": 0.0,
    }
    unlocked = set(save_data.get("achievements", []))
    for achievement in ACHIEVEMENTS:
        if achievement.id in unlocked:
            bonuses[achievement.reward] += achievement.reward_value
    return bonuses


def progress_for(achievement: Achievement, save_data: dict[str, Any]) -> tuple[int, int]:
    current = int(save_data.get("stats", {}).get(achievement.stat, 0))
    return min(current, achievement.target), achievement.target
