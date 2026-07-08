from __future__ import annotations

"""Persistent six-branch Skill Tree definitions and allocation rules."""

from dataclasses import dataclass
from typing import Any


SKILL_POINT_SECONDS = 120
SKILL_BRANCHES = ("Strength", "Dexterity", "Vitality", "Tech", "Focus", "Luck")


@dataclass(frozen=True)
class SkillNode:
    id: str
    name: str
    branch: str
    description: str
    cost: int = 1
    prerequisite: str = ""
    icon: str = ""


SKILL_NODES: tuple[SkillNode, ...] = (
    SkillNode("strength_impact", "Impact Drive", "Strength", "+1 Strength; projectile impact and ram damage improve.", icon="skill_strength"),
    SkillNode("strength_ram", "Ramming Plates", "Strength", "Rams deal 45% more damage and knock enemies farther.", prerequisite="strength_impact", icon="skill_strength"),
    SkillNode("strength_blast", "Blast Yield", "Strength", "Explosions gain +22 radius.", prerequisite="strength_ram", icon="skill_strength"),
    SkillNode("dexterity_trigger", "Trigger Servo", "Dexterity", "+1 Dexterity; faster fire rate and projectile speed.", icon="skill_dexterity"),
    SkillNode("dexterity_vector", "Vector Steering", "Dexterity", "Responsive handling reaches your movement input faster.", prerequisite="dexterity_trigger", icon="skill_dexterity"),
    SkillNode("dexterity_cycle", "Quick Cycle", "Dexterity", "Right-click ability cooldowns are reduced by 10%.", prerequisite="dexterity_vector", icon="skill_dexterity"),
    SkillNode("vitality_hull", "Armored Core", "Vitality", "+1 Vitality; more maximum health and armor.", icon="skill_vitality"),
    SkillNode("vitality_repair", "Recovery Mesh", "Vitality", "Gain 0.7 hull repair per second after avoiding damage.", prerequisite="vitality_hull", icon="skill_vitality"),
    SkillNode("vitality_contact", "Impact Dampers", "Vitality", "Collision damage is reduced by 14%.", prerequisite="vitality_repair", icon="skill_vitality"),
    SkillNode("tech_grid", "Grid Link", "Tech", "+1 Tech; summons and deployed systems hit harder.", icon="skill_tech"),
    SkillNode("tech_turret", "Turret Firmware", "Tech", "Turrets deal 20% more damage and fire more reliably.", prerequisite="tech_grid", icon="skill_tech"),
    SkillNode("tech_contract", "Contract Uplink", "Tech", "Completed contracts grant +2 run coins.", prerequisite="tech_turret", icon="skill_tech"),
    SkillNode("focus_calibration", "Target Calibration", "Focus", "+1 Focus; ability and critical systems improve.", icon="skill_focus"),
    SkillNode("focus_pulse", "Ability Pulse", "Focus", "Right-click abilities deal 16% more damage.", prerequisite="focus_calibration", icon="skill_focus"),
    SkillNode("focus_status", "Status Amplifier", "Focus", "Freeze, burn, and poison effects last 25% longer.", prerequisite="focus_pulse", icon="skill_focus"),
    SkillNode("luck_salvage", "Salvage Instinct", "Luck", "+1 Luck; improved crit and drop quality.", icon="skill_luck"),
    SkillNode("luck_chest", "Crate Finder", "Luck", "Chest gear chance increases by 8%.", prerequisite="luck_salvage", icon="skill_luck"),
    SkillNode("luck_contract", "Fortune Circuit", "Luck", "Contracts have a 15% chance to award one extra Blueprint Fragment.", prerequisite="luck_chest", icon="skill_luck"),
)

SKILL_BY_ID = {node.id: node for node in SKILL_NODES}
NODES_BY_BRANCH = {
    branch: tuple(node for node in SKILL_NODES if node.branch == branch)
    for branch in SKILL_BRANCHES
}


def total_skill_points(save_data: dict[str, Any], tank_id: str) -> int:
    best_time = save_data.get("stats", {}).get(f"{tank_id}_best_time", 0)
    return max(0, int(best_time) // SKILL_POINT_SECONDS)


def allocations(save_data: dict[str, Any], tank_id: str) -> list[str]:
    trees = save_data.setdefault("tank_skill_trees", {})
    current = trees.setdefault(tank_id, [])
    return current if isinstance(current, list) else []


def available_skill_points(save_data: dict[str, Any], tank_id: str) -> int:
    return max(0, total_skill_points(save_data, tank_id) - len(allocations(save_data, tank_id)))


def node_status(save_data: dict[str, Any], tank_id: str, node: SkillNode) -> str:
    allocated = set(allocations(save_data, tank_id))
    if node.id in allocated:
        return "Completed"
    if node.prerequisite and node.prerequisite not in allocated:
        return "Locked"
    return "Available" if available_skill_points(save_data, tank_id) >= node.cost else "Locked"


def unlock_skill_node(save_data: dict[str, Any], tank_id: str, node_id: str) -> tuple[bool, str]:
    node = SKILL_BY_ID.get(node_id)
    if node is None:
        return False, "Unknown skill node"
    status = node_status(save_data, tank_id, node)
    if status == "Completed":
        return False, "Skill already learned"
    if status == "Locked":
        return False, "Prerequisite or skill point missing"
    allocations(save_data, tank_id).append(node.id)
    return True, node.name


def refund_skill_tree(save_data: dict[str, Any], tank_id: str) -> bool:
    current = allocations(save_data, tank_id)
    if not current:
        return False
    current.clear()
    return True
