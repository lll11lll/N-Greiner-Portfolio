from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Stage:
    id: str
    name: str
    tileset: str
    enemy_pool: tuple[str, ...]
    boss: str
    description: str
    width: int
    height: int
    boss_pool: tuple[str, ...] = ()
    contract_kind: str = "kills"
    contract_goal: int = 70
    contract_name: str = "Scrap Sweep"
    modifier_name: str = "Salvage Field"
    modifier_description: str = "Pickup magnet radius is increased."


STAGES: tuple[Stage, ...] = (
    Stage(
        "scrap_outskirts",
        "Scrapyard Outskirts",
        "scrap",
        (
            "crawler",
            "runner",
            "dash_scrapper",
            "drone_swarm",
            "brute",
            "medium_bruiser",
            "shield_carrier",
            "mine_layer",
            "shooter",
            "artillery_buggy",
            "repair_node",
            "lightning_node",
        ),
        "boss_rift_charger",
        "Industrial junk lanes, neon scrap piles, drone swarms, and open kill zones.",
        3600,
        2600,
        ("boss_rift_charger", "boss_storm_capacitor", "boss_scrap_hive_core"),
        contract_kind="xp",
        contract_goal=150,
        contract_name="Salvage Sweep",
        modifier_name="Salvage Field",
        modifier_description="+20 pickup magnet radius.",
    ),
    Stage(
        "desert_wrecks",
        "Desert Wasteland",
        "desert",
        (
            "crawler",
            "runner",
            "dash_scrapper",
            "medium_bruiser",
            "mine_layer",
            "artillery_buggy",
            "fire_mote",
            "poison_spitter",
        ),
        "boss_furnace_king",
        "Dusty cracked ground with fire motes, toxic scrap, and wider sightlines.",
        3800,
        2700,
        ("boss_furnace_king", "boss_toxic_maw", "boss_rift_charger"),
        contract_kind="kills",
        contract_goal=85,
        contract_name="Wreck Breaker",
        modifier_name="Heat Haze",
        modifier_description="Enemy movement speed is increased by 12%.",
    ),
    Stage(
        "frozen_base",
        "Frozen Tech Base",
        "frozen",
        (
            "crawler",
            "runner",
            "drone_swarm",
            "shooter",
            "repair_node",
            "cryo_crawler",
            "lightning_node",
            "shield_carrier",
        ),
        "boss_glacier_engine",
        "Cold blue floors, damaged machinery, cryo crawlers, and tighter tech corridors.",
        3500,
        2550,
        ("boss_glacier_engine", "boss_storm_capacitor", "boss_scrap_hive_core"),
        contract_kind="time",
        contract_goal=150,
        contract_name="Relay Stabilization",
        modifier_name="Coolant Grid",
        modifier_description="Cryo effects last 0.35s longer.",
    ),
    Stage(
        "shattered_metro",
        "Shattered Metro",
        "city",
        (
            "crawler",
            "runner",
            "shooter",
            "shield_carrier",
            "artillery_buggy",
            "drone_swarm",
            "repair_node",
            "lightning_node",
        ),
        "boss_rift_charger",
        "A ruined neon city of broken streets, transit wrecks, power stations, and urban crossfire.",
        3900,
        2750,
        ("boss_rift_charger", "boss_storm_capacitor", "boss_scrap_hive_core"),
        contract_kind="kills",
        contract_goal=92,
        contract_name="Street Sweep",
        modifier_name="Urban Crossfire",
        modifier_description="Ranged enemies arrive earlier; salvage density is higher.",
    ),
    Stage(
        "overgrowth_basin",
        "Overgrowth Basin",
        "jungle",
        (
            "crawler",
            "runner",
            "brute",
            "poison_spitter",
            "fire_mote",
            "cryo_crawler",
            "drone_swarm",
            "mine_layer",
        ),
        "boss_toxic_maw",
        "A humid reclaimed battlefield where roots, vines, moss, and ruined machines close in around salvage routes.",
        3700,
        2800,
        ("boss_toxic_maw", "boss_scrap_hive_core", "boss_glacier_engine"),
        contract_kind="xp",
        contract_goal=170,
        contract_name="Canopy Recovery",
        modifier_name="Overgrowth Surge",
        modifier_description="Pickup density rises, but overgrown routes feel tighter.",
    ),
)

STAGE_BY_ID = {stage.id: stage for stage in STAGES}
DEFAULT_STAGE_ID = "scrap_outskirts"


def get_stage(stage_id: str | None) -> Stage:
    return STAGE_BY_ID.get(stage_id or DEFAULT_STAGE_ID, STAGE_BY_ID[DEFAULT_STAGE_ID])
