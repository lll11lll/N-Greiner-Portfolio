from __future__ import annotations

"""Curated equipment identities used by chest loot and the Garage loadout UI."""

from dataclasses import dataclass
from typing import Any


EQUIPMENT_SLOTS = ("weapon", "armor", "trinket", "tracks")


@dataclass(frozen=True)
class EquipmentTemplate:
    id: str
    name: str
    slot: str
    stats: dict[str, int]
    effect: str
    description: str

    @property
    def art_key(self) -> str:
        return f"equipment_{self.slot}_{self.id}"


EQUIPMENT_TEMPLATES: tuple[EquipmentTemplate, ...] = (
    EquipmentTemplate("scrap_repeater", "Scrap Repeater", "weapon", {"Dexterity": 1, "Strength": 1}, "repeater_drive", "Rapid recycler barrel: faster sustained fire."),
    EquipmentTemplate("rail_lance", "Rail Lance", "weapon", {"Strength": 2, "Focus": 1}, "rail_impact", "Dense penetrator with stronger projectile impact."),
    EquipmentTemplate("furnace_cannon", "Furnace Cannon", "weapon", {"Strength": 2, "Tech": 1}, "furnace_payload", "Heavy furnace chamber that widens explosions."),
    EquipmentTemplate("arc_splitter", "Arc Splitter", "weapon", {"Tech": 2, "Focus": 1}, "arc_splitter", "Conductive prongs that improve lightning chaining."),
    EquipmentTemplate("venom_mortar", "Venom Mortar", "weapon", {"Focus": 2, "Luck": 1}, "venom_payload", "Pressurized shell that improves poison duration."),
    EquipmentTemplate("reinforced_plating", "Reinforced Plating", "armor", {"Vitality": 2}, "reinforced_plating", "Layered hull panels reduce incoming impact damage."),
    EquipmentTemplate("reactive_shell", "Reactive Shell", "armor", {"Vitality": 1, "Tech": 1}, "reactive_shell", "Reactive armor gives a brief shield after a heavy hit."),
    EquipmentTemplate("cryo_insulation", "Cryo Insulation", "armor", {"Vitality": 1, "Focus": 1}, "cryo_insulation", "Thermal lining improves Cryo status control."),
    EquipmentTemplate("volatile_hull", "Volatile Hull", "armor", {"Strength": 1, "Tech": 1}, "volatile_hull", "Unstable plating increases explosive output."),
    EquipmentTemplate("conductive_chassis", "Conductive Chassis", "armor", {"Tech": 2}, "conductive_chassis", "Conductive frame strengthens arc and gadget systems."),
    EquipmentTemplate("salvage_beacon", "Salvage Beacon", "trinket", {"Luck": 1, "Tech": 1}, "salvage_beacon", "Signal beacon widens pickup attraction."),
    EquipmentTemplate("shock_capacitor", "Shock Capacitor", "trinket", {"Tech": 1, "Focus": 1}, "shock_capacitor", "Stores charge for stronger right-click abilities."),
    EquipmentTemplate("lucky_scrap_charm", "Lucky Scrap Charm", "trinket", {"Luck": 2}, "lucky_scrap_charm", "Improves chest and salvage odds."),
    EquipmentTemplate("focus_lens", "Focus Lens", "trinket", {"Focus": 2}, "focus_lens", "Precision lens improves crit and status potency."),
    EquipmentTemplate("emergency_repair_module", "Emergency Repair Module", "trinket", {"Vitality": 1, "Luck": 1}, "emergency_repair", "Repairs hull slowly after avoiding damage."),
    EquipmentTemplate("reinforced_treads", "Reinforced Treads", "tracks", {"Vitality": 1, "Strength": 1}, "track_ram", "Heavy treads increase ram force and impact knockback."),
    EquipmentTemplate("drift_treads", "Drift Treads", "tracks", {"Dexterity": 2}, "track_drift", "Responsive treads improve acceleration and dodge feel."),
    EquipmentTemplate("magnet_tracks", "Magnet Tracks", "tracks", {"Luck": 1, "Tech": 1}, "track_magnet", "Magnetized runners pull salvage from farther away."),
    EquipmentTemplate("shock_absorber_wheels", "Shock Absorber Wheels", "tracks", {"Vitality": 2}, "track_stability", "Suspension reduces collision shock and recoil."),
    EquipmentTemplate("siege_tracks", "Siege Tracks", "tracks", {"Strength": 2}, "track_siege", "Anchored tracks reinforce impact damage while moving."),
    EquipmentTemplate("scout_treads", "Scout Treads", "tracks", {"Dexterity": 1, "Luck": 1}, "track_scout", "Light treads boost speed and salvage routing."),
)

EQUIPMENT_BY_ID = {template.id: template for template in EQUIPMENT_TEMPLATES}
EQUIPMENT_BY_SLOT = {
    slot: tuple(template for template in EQUIPMENT_TEMPLATES if template.slot == slot)
    for slot in EQUIPMENT_SLOTS
}


def template_from_item(item: dict[str, Any]) -> EquipmentTemplate | None:
    template_id = item.get("template_id")
    return EQUIPMENT_BY_ID.get(template_id) if isinstance(template_id, str) else None


def item_description(item: dict[str, Any]) -> str:
    template = template_from_item(item)
    return template.description if template else "Scavenged equipment with permanent chassis stat bonuses."
