from __future__ import annotations

import json
import os
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

from .achievements import default_stats
from .equipment import EQUIPMENT_SLOTS
from .progression import LEGACY_UNLOCK_ALIASES, RESEARCH_BY_ID, UNLOCK_BY_ID, sync_unlock_progress
from .skill_tree import SKILL_BY_ID
from .stages import DEFAULT_STAGE_ID, STAGE_BY_ID


SAVE_PATH = Path("save.json")
SAVE_SCHEMA_VERSION = 5
LOOT_UNLOCK_SECONDS = 300
KNOWN_TANK_IDS = {"starter", "sniper", "engineer", "twin_shot", "flame_caster", "cryo", "poison", "lightning"}
GEAR_TYPES = set(EQUIPMENT_SLOTS)
RARITIES = {"Common", "Uncommon", "Rare", "Epic", "Legendary", "Unique"}
META_STATS = ("Strength", "Dexterity", "Vitality", "Tech", "Focus", "Luck")

DEFAULT_SAVE: dict[str, Any] = {
    "schema_version": SAVE_SCHEMA_VERSION,
    "coins": 0,
    "selected_tank": "starter",
    "unlocked_tanks": ["starter"],
    "universal_upgrades": {
        "max_health": 0,
        "move_speed": 0,
        "fire_rate": 0,
        "bullet_damage": 0,
        "xp_bonus": 0,
        "coin_bonus": 0,
        "pickup_radius": 0,
        "projectile_speed": 0,
    },
    "settings": {},
    "selected_stage": DEFAULT_STAGE_ID,
    "loot_unlocked": False,
    "blueprint_fragments": 0,
    # Unlocks are automatic milestone rewards. Research is a separate paid
    # progression track; never combine these two lists.
    "unlocks_completed": [],
    "unlocks_progress": {},
    "unlocks_new": [],
    "research_completed": [],
    "lifetime_contracts_completed": 0,
    "lifetime_elites_defeated": 0,
    "lifetime_bosses_defeated": 0,
    "lifetime_chests_opened": 0,
    "best_survival_time": 0,
    "lifetime_evolutions_triggered": 0,
    "lifetime_ability_uses": 0,
    "lifetime_stage_contracts_completed": 0,
    "lifetime_salvage_surges_survived": 0,
    "stage_best_times": {},
    "stage_contract_counts": {},
    "stage_contracts_completed": [],
    "elemental_evolution_families": [],
    "achievements": [],
    "stats": default_stats(),
    "gear_inventory": [],
    "equipped_gear": {
        "weapon": None,
        "armor": None,
        "trinket": None,
        "tracks": None,
    },
    "tank_skill_trees": {},
    "meta_stats": {
        "Strength": 0,
        "Dexterity": 0,
        "Vitality": 0,
        "Tech": 0,
        "Focus": 0,
        "Luck": 0,
    },
}


class SaveManager:
    def __init__(self, path: Path | str | None = None) -> None:
        self.path = Path(path or os.environ.get("NEON_SCRAP_SAVE", SAVE_PATH))

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            data = deepcopy(DEFAULT_SAVE)
            self.save(data)
            return data

        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            raw = {}

        data = normalize_save(raw)
        self.save(data)
        return data

    def save(self, data: dict[str, Any]) -> None:
        try:
            self.path.write_text(json.dumps(normalize_save(data), indent=2), encoding="utf-8")
        except OSError:
            if sys.platform != "emscripten":
                raise


def normalize_save(raw: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raw = {}
    data = deepcopy(DEFAULT_SAVE)
    data["schema_version"] = SAVE_SCHEMA_VERSION
    if isinstance(raw.get("coins"), int | float) and not isinstance(raw.get("coins"), bool):
        data["coins"] = max(0, int(raw["coins"]))
    if isinstance(raw.get("selected_tank"), str) and raw["selected_tank"] in KNOWN_TANK_IDS:
        data["selected_tank"] = raw["selected_tank"]
    if isinstance(raw.get("unlocked_tanks"), list):
        unlocked = [tank for tank in raw["unlocked_tanks"] if isinstance(tank, str) and tank in KNOWN_TANK_IDS]
        data["unlocked_tanks"] = sorted(set(unlocked + ["starter"]))
    if isinstance(raw.get("universal_upgrades"), dict):
        for key in data["universal_upgrades"]:
            value = raw["universal_upgrades"].get(key, 0)
            data["universal_upgrades"][key] = _nonnegative_int(value)
    if isinstance(raw.get("settings"), dict):
        data["settings"] = raw["settings"]
    if isinstance(raw.get("selected_stage"), str) and raw["selected_stage"] in STAGE_BY_ID:
        data["selected_stage"] = raw["selected_stage"]
    if isinstance(raw.get("loot_unlocked"), bool):
        data["loot_unlocked"] = raw["loot_unlocked"]
    data["blueprint_fragments"] = _nonnegative_int(raw.get("blueprint_fragments", 0))
    if isinstance(raw.get("unlocks_completed"), list):
        data["unlocks_completed"] = sorted({LEGACY_UNLOCK_ALIASES.get(value, value) for value in raw["unlocks_completed"] if isinstance(value, str) and LEGACY_UNLOCK_ALIASES.get(value, value) in UNLOCK_BY_ID})
    if isinstance(raw.get("unlocks_new"), list):
        data["unlocks_new"] = sorted({LEGACY_UNLOCK_ALIASES.get(value, value) for value in raw["unlocks_new"] if isinstance(value, str) and LEGACY_UNLOCK_ALIASES.get(value, value) in UNLOCK_BY_ID})
    if isinstance(raw.get("research_completed"), list):
        data["research_completed"] = sorted({value for value in raw["research_completed"] if isinstance(value, str) and value in RESEARCH_BY_ID})
    if isinstance(raw.get("achievements"), list):
        from .achievements import ACHIEVEMENT_BY_ID

        data["achievements"] = sorted({item for item in raw["achievements"] if isinstance(item, str) and item in ACHIEVEMENT_BY_ID})
    if isinstance(raw.get("stats"), dict):
        for key in data["stats"]:
            value = raw["stats"].get(key, 0)
            data["stats"][key] = _nonnegative_int(value, data["stats"][key])

    # Schema v3 derives its first lifetime values from the old statistics
    # fields, then keeps dedicated counters from this point forward.
    raw_stats = raw.get("stats", {}) if isinstance(raw.get("stats"), dict) else {}
    migrations = {
        "lifetime_bosses_defeated": raw_stats.get("total_bosses", 0),
        "lifetime_chests_opened": raw_stats.get("total_chests_opened", 0),
        "best_survival_time": raw_stats.get("best_time", 0),
        "lifetime_ability_uses": raw_stats.get("total_abilities_cast", 0),
    }
    for key in (
        "lifetime_contracts_completed",
        "lifetime_elites_defeated",
        "lifetime_bosses_defeated",
        "lifetime_chests_opened",
        "best_survival_time",
        "lifetime_evolutions_triggered",
        "lifetime_ability_uses",
        "lifetime_stage_contracts_completed",
        "lifetime_salvage_surges_survived",
    ):
        data[key] = max(_nonnegative_int(raw.get(key, 0)), _nonnegative_int(migrations.get(key, 0)))
    if isinstance(raw.get("stage_best_times"), dict):
        data["stage_best_times"] = {
            stage_id: _nonnegative_int(value)
            for stage_id, value in raw["stage_best_times"].items()
            if isinstance(stage_id, str) and stage_id in STAGE_BY_ID
        }
    if isinstance(raw.get("stage_contract_counts"), dict):
        data["stage_contract_counts"] = {
            stage_id: _nonnegative_int(value)
            for stage_id, value in raw["stage_contract_counts"].items()
            if isinstance(stage_id, str) and stage_id in STAGE_BY_ID
        }
    if isinstance(raw.get("stage_contracts_completed"), list):
        data["stage_contracts_completed"] = sorted({stage_id for stage_id in raw["stage_contracts_completed"] if isinstance(stage_id, str) and stage_id in STAGE_BY_ID})
    if isinstance(raw.get("elemental_evolution_families"), list):
        valid_families = {"Fire", "Cryo", "Lightning", "Poison"}
        data["elemental_evolution_families"] = sorted({family for family in raw["elemental_evolution_families"] if isinstance(family, str) and family in valid_families})
    
    # Normalize gear_inventory
    if isinstance(raw.get("gear_inventory"), list):
        data["gear_inventory"] = []
        for item in raw["gear_inventory"]:
            if isinstance(item, dict) and "id" in item and "name" in item and "type" in item and "rarity" in item:
                item_type = str(item["type"]) if str(item["type"]) in GEAR_TYPES else "trinket"
                rarity = str(item["rarity"]) if str(item["rarity"]) in RARITIES else "Common"
                data["gear_inventory"].append({
                    "id": str(item["id"]),
                    "name": str(item["name"]),
                    "type": item_type,
                    "rarity": rarity,
                    "stats": {
                        k: _nonnegative_int(v)
                        for k, v in item.get("stats", {}).items()
                        if isinstance(k, str) and k in META_STATS
                    } if isinstance(item.get("stats"), dict) else {},
                    "effect": str(item["effect"]) if "effect" in item else None,
                    "template_id": str(item["template_id"]) if isinstance(item.get("template_id"), str) else None,
                    "art_key": str(item["art_key"]) if isinstance(item.get("art_key"), str) else None,
                })
                
    # Normalize equipped_gear
    if isinstance(raw.get("equipped_gear"), dict):
        for slot in EQUIPMENT_SLOTS:
            val = raw["equipped_gear"].get(slot)
            if isinstance(val, str) or val is None:
                data["equipped_gear"][slot] = val
    valid_item_ids = {item["id"] for item in data["gear_inventory"]}
    for slot, item_id in list(data["equipped_gear"].items()):
        if item_id is not None and item_id not in valid_item_ids:
            data["equipped_gear"][slot] = None
                
    # Normalize tank_skill_trees
    if isinstance(raw.get("tank_skill_trees"), dict):
        legacy_nodes = {
            "node_offense": "strength_impact",
            "node_defense": "vitality_hull",
            "node_specialty": "focus_calibration",
            "node_overclock": "dexterity_trigger",
        }
        for k, v in raw["tank_skill_trees"].items():
            if isinstance(v, list):
                valid_nodes = []
                for node in v:
                    if not isinstance(node, str):
                        continue
                    node_id = legacy_nodes.get(node, node)
                    if node_id in SKILL_BY_ID and node_id not in valid_nodes:
                        valid_nodes.append(node_id)
                data["tank_skill_trees"][str(k)] = valid_nodes
                
    # Normalize meta_stats
    if isinstance(raw.get("meta_stats"), dict):
        for stat in data["meta_stats"]:
            val = raw["meta_stats"].get(stat, 0)
            data["meta_stats"][stat] = _nonnegative_int(val)

    if data["selected_tank"] not in data["unlocked_tanks"]:
        data["selected_tank"] = "starter"
    data["stats"]["unlocked_tank_count"] = len(set(data["unlocked_tanks"]))
    if data["stats"].get("best_time", 0) >= LOOT_UNLOCK_SECONDS:
        data["loot_unlocked"] = True
    sync_unlock_progress(data)
    return data


def _nonnegative_int(value: Any, default: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return default
    return max(0, int(value))
