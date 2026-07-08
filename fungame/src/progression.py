from __future__ import annotations

"""Separate permanent content Unlocks and Blueprint-powered Research augments."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class UnlockDefinition:
    id: str
    name: str
    category: str
    requirement: str
    progress_key: str
    target: int
    reward: str
    icon: str


@dataclass(frozen=True)
class ResearchProject:
    id: str
    name: str
    category: str
    description: str
    fragment_cost: int
    icon: str
    requirement: str = ""
    requirement_kind: str = ""
    coin_cost: int = 0


@dataclass(frozen=True)
class RunContract:
    id: str
    name: str
    kind: str
    goal: int
    description: str
    reward: str


@dataclass(frozen=True)
class RunModifier:
    id: str
    name: str
    description: str


# Every reward below expands a future-run content pool. Existing enemies and
# existing upgrades are intentionally not repackaged as unlock rewards.
UNLOCKS: tuple[UnlockDefinition, ...] = (
    UnlockDefinition("elite_contract_board", "Elite Contract Board", "Contract Pack", "Complete 5 contracts.", "lifetime_contracts_completed", 5, "Adds the new Elite Hunt contract to future runs.", "unlock_elite_contract_board"),
    UnlockDefinition("surge_contract_license", "Surge Contract License", "Contract Pack", "Survive 3 Salvage Surges.", "lifetime_salvage_surges_survived", 3, "Adds the new Surge Salvage contract to future runs.", "unlock_surge_contract_license"),
    UnlockDefinition("hazard_modifiers", "Hazard Modifier Pack", "Event Pack", "Survive 8 minutes once.", "best_survival_time", 480, "Adds Volatile Scrap and Charged Wreckage modifiers.", "unlock_hazard_modifiers"),
    UnlockDefinition("anomaly_routes", "Anomaly Route Signal", "Route Event", "Defeat 3 bosses total.", "lifetime_bosses_defeated", 3, "Adds post-boss anomaly route events.", "unlock_anomaly_routes"),
    UnlockDefinition("elemental_elites", "Elemental Elite Pack", "Elite Variant", "Trigger any elemental evolution once.", "lifetime_evolutions_triggered", 1, "Adds new elemental elite variants with elemental behavior.", "unlock_elemental_elites"),
    UnlockDefinition("relic_prototypes", "Relic Prototypes", "Gear Category", "Defeat your first boss.", "lifetime_bosses_defeated", 1, "Adds the new boss relic gear category.", "unlock_relic_prototypes"),
    UnlockDefinition("ability_variant_pack", "Ability Variant Pack", "Level-up Pack", "Use right-click abilities 100 times.", "lifetime_ability_uses", 100, "Adds Split Fireball, Chilling Ring, Corrosive Burst, and Arc Echo cards.", "unlock_ability_variant_pack"),
    UnlockDefinition("elemental_fusion_pack", "Elemental Fusion Pack", "Level-up Pack", "Trigger 2 different elemental evolutions across all runs.", "distinct_elemental_evolutions", 2, "Adds Conductive Wildfire, Toxic Frostbite, and Storm Shatter cards.", "unlock_elemental_fusion_pack"),
    UnlockDefinition("contract_tech_pack", "Contract Tech Pack", "Level-up Pack", "Complete 10 contracts total.", "lifetime_contracts_completed", 10, "Adds Salvage Momentum, Blueprint Echo, and Relay Overcharge cards.", "unlock_contract_tech_pack"),
)

UNLOCK_BY_ID = {unlock.id: unlock for unlock in UNLOCKS}
LEGACY_UNLOCK_ALIASES = {
    "hazard_route_access": "hazard_modifiers",
    "elemental_elite_signals": "elemental_elites",
    "boss_relic_drops": "relic_prototypes",
    "unique_gear_drops": "relic_prototypes",
    "ability_variant_system": "ability_variant_pack",
    "elemental_fusion_upgrades": "elemental_fusion_pack",
    "contract_tech_upgrades": "contract_tech_pack",
}


RESEARCH_PROJECTS: tuple[ResearchProject, ...] = (
    ResearchProject("flame_injector", "Flame Injector", "Tank Augments", "Fireball leaves a wider flame patch and burns longer.", 3, "research_flame_injector", "Flame Caster unlocked", "tank:flame_caster"),
    ResearchProject("cryo_amplifier", "Cryo Amplifier", "Tank Augments", "Frost Nova reaches farther.", 3, "research_cryo_amplifier", "Cryo Tank unlocked", "tank:cryo"),
    ResearchProject("toxin_pressurizer", "Toxin Pressurizer", "Tank Augments", "Acid puddles linger longer and tick faster.", 3, "research_toxin_pressurizer", "Poison Tank unlocked", "tank:poison"),
    ResearchProject("overcharge_coil", "Overcharge Coil", "Tank Augments", "Arc Surge chains to one extra enemy.", 3, "research_overcharge_coil", "Lightning Tank unlocked", "tank:lightning"),
    ResearchProject("sniper_stabilizer", "Sniper Stabilizer", "Tank Augments", "Sniper shots gain an additional pierce and stronger falloff scaling.", 2, "research_ability_augments", "Sniper unlocked", "tank:sniper"),
    ResearchProject("engineer_fabricator", "Engineer Fabricator", "Tank Augments", "Engineer turrets last longer and fire slightly faster.", 3, "research_ability_augments", "Engineer unlocked", "tank:engineer"),
    ResearchProject("fireball_splitter", "Fireball Splitter", "Ability Augments", "Fireball splits into two smaller bursts on impact.", 4, "research_ability_augments", "Flame Caster unlocked", "tank:flame_caster"),
    ResearchProject("frost_shockwave", "Frost Shockwave", "Ability Augments", "Frost Nova leaves a brief slowing field.", 4, "research_ability_augments", "Cryo Tank unlocked", "tank:cryo"),
    ResearchProject("acid_mist", "Acid Mist", "Ability Augments", "Acid Glob leaves a lingering poison cloud.", 4, "research_ability_augments", "Poison Tank unlocked", "tank:poison"),
    ResearchProject("chain_echo", "Chain Echo", "Ability Augments", "Arc Surge can repeat a weaker follow-up chain.", 4, "research_ability_augments", "Lightning Tank unlocked", "tank:lightning"),
    ResearchProject("contract_negotiation", "Contract Negotiation", "Contract Tech", "Completed contracts grant more run coins.", 2, "research_contract_tech"),
    ResearchProject("blueprint_analysis", "Blueprint Analysis", "Contract Tech", "Your first completed contract each run can grant +1 Blueprint Fragment.", 4, "research_contract_tech"),
    ResearchProject("salvage_relay_tools", "Salvage Relay Tools", "Contract Tech", "Relay-style contracts progress faster.", 3, "research_contract_tech"),
    ResearchProject("surge_stabilizer", "Surge Stabilizer", "Contract Tech", "Salvage Surges are less punishing without reducing rewards.", 3, "research_contract_tech"),
    ResearchProject("chest_calibration", "Chest Calibration", "Gear Lab", "Improves high-quality chest odds.", 3, "research_gear_lab"),
    ResearchProject("boss_salvage_tools", "Boss Salvage Tools", "Gear Lab", "Boss chests have improved rare and unique odds.", 5, "research_gear_lab", "Defeat 3 bosses", "metric:lifetime_bosses_defeated:3"),
    ResearchProject("evolution_stabilizer", "Evolution Stabilizer", "Evolution Lab", "Elemental evolution effects gain a small duration or radius bonus.", 5, "research_evolution_lab", "Trigger any evolution once", "metric:lifetime_evolutions_triggered:1"),
    ResearchProject("fusion_resonance", "Fusion Resonance", "Evolution Lab", "Unlocked fusion cards appear more reliably and hit slightly harder.", 6, "research_evolution_lab", "Elemental Fusion Pack unlocked", "unlock:elemental_fusion_pack"),
)

RESEARCH_BY_ID = {project.id: project for project in RESEARCH_PROJECTS}
RESEARCH_CATEGORIES = ("All", "Tank Augments", "Ability Augments", "Contract Tech", "Gear Lab", "Evolution Lab")


CONTENT_GATED_UPGRADES = {
    "conductive_wildfire": "elemental_fusion_pack",
    "toxic_frostbite": "elemental_fusion_pack",
    "storm_shatter": "elemental_fusion_pack",
    "salvage_momentum": "contract_tech_pack",
    "blueprint_echo": "contract_tech_pack",
    "relay_overcharge": "contract_tech_pack",
    "split_fireball": "ability_variant_pack",
    "chilling_ring": "ability_variant_pack",
    "corrosive_burst": "ability_variant_pack",
    "arc_echo": "ability_variant_pack",
}


def _integer(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return 0
    return max(0, int(value))


def unlock_progress(save_data: dict[str, Any], unlock: UnlockDefinition | str) -> int:
    definition = UNLOCK_BY_ID[unlock] if isinstance(unlock, str) else unlock
    if definition.progress_key == "distinct_elemental_evolutions":
        values = save_data.get("elemental_evolution_families", [])
        return len({value for value in values if isinstance(value, str)}) if isinstance(values, list) else 0
    return _integer(save_data.get(definition.progress_key, 0))


def sync_unlock_progress(save_data: dict[str, Any]) -> bool:
    progress = save_data.setdefault("unlocks_progress", {})
    changed = False
    for unlock in UNLOCKS:
        value = unlock_progress(save_data, unlock)
        if progress.get(unlock.id) != value:
            progress[unlock.id] = value
            changed = True
    return changed


def evaluate_unlocks(save_data: dict[str, Any]) -> list[UnlockDefinition]:
    sync_unlock_progress(save_data)
    completed = {value for value in save_data.get("unlocks_completed", []) if value in UNLOCK_BY_ID}
    newly_completed = [unlock for unlock in UNLOCKS if unlock.id not in completed and unlock_progress(save_data, unlock) >= unlock.target]
    if newly_completed:
        completed.update(unlock.id for unlock in newly_completed)
        save_data["unlocks_completed"] = sorted(completed)
        new_flags = {value for value in save_data.get("unlocks_new", []) if value in UNLOCK_BY_ID}
        new_flags.update(unlock.id for unlock in newly_completed)
        save_data["unlocks_new"] = sorted(new_flags)
    return newly_completed


def content_unlocked(save_data: dict[str, Any], unlock_id: str) -> bool:
    return unlock_id in set(save_data.get("unlocks_completed", []))


def research_requirement_met(save_data: dict[str, Any], project: ResearchProject | str) -> bool:
    definition = RESEARCH_BY_ID[project] if isinstance(project, str) else project
    if not definition.requirement_kind:
        return True
    kind, *parts = definition.requirement_kind.split(":")
    if kind == "tank" and parts:
        return parts[0] in set(save_data.get("unlocked_tanks", []))
    if kind == "unlock" and parts:
        return content_unlocked(save_data, parts[0])
    if kind == "metric" and len(parts) == 2:
        return _integer(save_data.get(parts[0], 0)) >= _integer(parts[1])
    return False


def research_status(save_data: dict[str, Any], project: ResearchProject | str) -> str:
    definition = RESEARCH_BY_ID[project] if isinstance(project, str) else project
    if definition.id in set(save_data.get("research_completed", [])):
        return "Completed"
    return "Available" if research_requirement_met(save_data, definition) else "Locked"


def purchase_research(save_data: dict[str, Any], project_id: str) -> tuple[bool, str]:
    project = RESEARCH_BY_ID.get(project_id)
    if project is None:
        return False, "Unknown research project"
    state = research_status(save_data, project)
    if state == "Completed":
        return False, "Research already completed"
    if state == "Locked":
        return False, "Research requirement not met"
    fragments = _integer(save_data.get("blueprint_fragments", 0))
    if fragments < project.fragment_cost:
        return False, "Not enough Blueprint Fragments"
    save_data["blueprint_fragments"] = fragments - project.fragment_cost
    completed = {value for value in save_data.get("research_completed", []) if value in RESEARCH_BY_ID}
    completed.add(project_id)
    save_data["research_completed"] = sorted(completed)
    return True, project.name


def apply_research_modifiers(player: object, save_data: dict[str, Any]) -> None:
    """Apply permanent augment projects to a freshly configured run player."""
    completed = set(save_data.get("research_completed", []))
    player.fire_patch_radius_bonus = 26.0 if "flame_injector" in completed else 0.0
    player.frost_nova_radius_bonus = 24.0 if "cryo_amplifier" in completed else 0.0
    player.acid_puddle_duration_bonus = 1.6 if "toxin_pressurizer" in completed else 0.0
    player.poison_tick_speed_bonus = 0.22 if "toxin_pressurizer" in completed else 0.0
    player.arc_surge_chain_bonus = 1 if "overcharge_coil" in completed else 0
    player.engineer_turret_duration_bonus = 2.5 if "engineer_fabricator" in completed else 0.0
    player.engineer_turret_rate_bonus = 0.18 if "engineer_fabricator" in completed else 0.0
    player.contract_coin_bonus = 2 if "contract_negotiation" in completed else 0
    player.blueprint_analysis_active = "blueprint_analysis" in completed
    player.relay_tools_active = "salvage_relay_tools" in completed
    player.surge_stabilizer_active = "surge_stabilizer" in completed
    player.chest_calibration_active = "chest_calibration" in completed
    player.boss_salvage_tools_active = "boss_salvage_tools" in completed
    player.evolution_stabilizer_active = "evolution_stabilizer" in completed
    player.fireball_splitter_active = "fireball_splitter" in completed
    player.frost_shockwave_active = "frost_shockwave" in completed
    player.acid_mist_active = "acid_mist" in completed
    player.chain_echo_active = "chain_echo" in completed
    player.fusion_resonance_active = "fusion_resonance" in completed
    if "sniper_stabilizer" in completed and getattr(player, "tank_id", "") == "sniper":
        player.bullet_pierce += 1
        player.sniper_pierce_damage_bonus = 0.12


def baseline_contract(stage: object) -> RunContract:
    return RunContract(
        id=f"{getattr(stage, 'id', 'stage')}_standard",
        name=str(getattr(stage, "contract_name", "Salvage Sweep")),
        kind=str(getattr(stage, "contract_kind", "kills")),
        goal=int(getattr(stage, "contract_goal", 70)),
        description="Complete the stage contract to earn a Blueprint Fragment.",
        reward="1 Blueprint Fragment + chest + coins",
    )


ELITE_HUNT_CONTRACT = RunContract("elite_hunt", "Elite Hunt", "elites", 2, "Defeat 2 elites before the boss arrives.", "1 Blueprint Fragment + elite chest")
SURGE_SALVAGE_CONTRACT = RunContract("surge_salvage", "Surge Salvage", "surge", 1, "Complete a Salvage Surge while it is active.", "1 Blueprint Fragment + upgraded chest")


def available_contracts(stage: object, save_data: dict[str, Any]) -> list[RunContract]:
    contracts = [baseline_contract(stage)]
    if content_unlocked(save_data, "elite_contract_board"):
        contracts.append(ELITE_HUNT_CONTRACT)
    if content_unlocked(save_data, "surge_contract_license"):
        contracts.append(SURGE_SALVAGE_CONTRACT)
    return contracts


def available_modifiers(stage: object, save_data: dict[str, Any]) -> list[RunModifier]:
    modifiers = [RunModifier("stage_default", str(getattr(stage, "modifier_name", "Salvage Field")), str(getattr(stage, "modifier_description", "")))]
    if content_unlocked(save_data, "hazard_modifiers"):
        modifiers.extend((
            RunModifier("volatile_scrap", "Volatile Scrap", "Explosions are stronger, but enemies are more aggressive."),
            RunModifier("charged_wreckage", "Charged Wreckage", "Lightning interactions are stronger, but more electric enemies spawn."),
        ))
    return modifiers
