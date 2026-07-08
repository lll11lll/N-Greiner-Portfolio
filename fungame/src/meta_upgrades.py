from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .achievements import achievement_bonuses
from .equipment import EQUIPMENT_SLOTS
from .skill_tree import allocations, available_skill_points


@dataclass(frozen=True)
class MetaUpgrade:
    id: str
    name: str
    description: str
    icon: str
    max_level: int
    base_cost: int
    cost_scale: float

    def cost_for_level(self, level: int) -> int | None:
        if level >= self.max_level:
            return None
        return int(round(self.base_cost * (self.cost_scale**level) / 5) * 5)


META_UPGRADES: tuple[MetaUpgrade, ...] = (
    MetaUpgrade("max_health", "Max Health", "+8 max health per level.", "meta_max_health", 5, 20, 1.65),
    MetaUpgrade("move_speed", "Movement Speed", "+4% movement speed per level.", "meta_move_speed", 5, 24, 1.7),
    MetaUpgrade("fire_rate", "Fire Rate", "+5% fire rate per level.", "meta_fire_rate", 5, 28, 1.75),
    MetaUpgrade("bullet_damage", "Bullet Damage", "+6% bullet damage per level.", "meta_bullet_damage", 5, 30, 1.78),
    MetaUpgrade("xp_bonus", "XP Gain", "+6% XP collected per level.", "meta_xp_bonus", 5, 26, 1.72),
    MetaUpgrade("coin_bonus", "Coin Bonus", "+7% run coin payouts per level.", "meta_coin_bonus", 5, 35, 1.9),
    MetaUpgrade("pickup_radius", "Pickup Radius", "+18 pickup magnet range per level.", "meta_pickup_radius", 5, 22, 1.62),
    MetaUpgrade("projectile_speed", "Projectile Speed", "+5% bullet speed and range per level.", "meta_projectile_speed", 5, 25, 1.68),
)

META_BY_ID = {upgrade.id: upgrade for upgrade in META_UPGRADES}


def apply_meta_upgrades(player: object, save_data: dict[str, Any]) -> tuple[float, float]:
    levels = save_data.get("universal_upgrades", {})
    max_health = int(levels.get("max_health", 0))
    move_speed = int(levels.get("move_speed", 0))
    fire_rate = int(levels.get("fire_rate", 0))
    bullet_damage = int(levels.get("bullet_damage", 0))
    pickup_radius = int(levels.get("pickup_radius", 0))
    projectile_speed = int(levels.get("projectile_speed", 0))

    # Base universal upgrades scaling
    player.max_health += max_health * 8
    player.health = player.max_health
    player.speed *= 1.0 + move_speed * 0.04
    player.fire_rate *= 1.0 + fire_rate * 0.05
    player.bullet_damage *= 1.0 + bullet_damage * 0.06
    player.magnet_radius += pickup_radius * 18
    player.bullet_speed *= 1.0 + projectile_speed * 0.05
    player.bullet_range *= 1.0 + projectile_speed * 0.05

    # 1. Sum up base meta_stats
    meta_stats = save_data.get("meta_stats", {})
    player.Strength = meta_stats.get("Strength", 0)
    player.Dexterity = meta_stats.get("Dexterity", 0)
    player.Vitality = meta_stats.get("Vitality", 0)
    player.Tech = meta_stats.get("Tech", 0)
    player.Focus = meta_stats.get("Focus", 0)
    player.Luck = meta_stats.get("Luck", 0)

    # 2. Sum up equipped gear stats
    equipped_gear = save_data.get("equipped_gear", {})
    inventory = save_data.get("gear_inventory", [])
    inv_by_id = {item["id"]: item for item in inventory}
    
    player.equipped_effects = set()
    player.handling_response = 13.5
    player.ram_damage_mult = 1.0
    player.ram_knockback_mult = 1.0
    player.contact_damage_reduction = 0.0
    player.track_dash_mult = 1.0
    player.gear_chest_bonus = 0.0
    player.contract_blueprint_bonus_chance = 0.0
    player.status_duration_mult = 1.0
    player.ability_cooldown_reduction = 0.0
    for slot in EQUIPMENT_SLOTS:
        item_id = equipped_gear.get(slot)
        if item_id and item_id in inv_by_id:
            item = inv_by_id[item_id]
            item_stats = item.get("stats", {})
            player.Strength += item_stats.get("Strength", 0)
            player.Dexterity += item_stats.get("Dexterity", 0)
            player.Vitality += item_stats.get("Vitality", 0)
            player.Tech += item_stats.get("Tech", 0)
            player.Focus += item_stats.get("Focus", 0)
            player.Luck += item_stats.get("Luck", 0)
            if item.get("effect"):
                player.equipped_effects.add(item["effect"])

    # 3. Equipment effects and the dedicated six-branch Skill Tree.
    for effect in player.equipped_effects:
        if effect == "repeater_drive":
            player.fire_rate *= 1.08
        elif effect == "rail_impact":
            player.bullet_pierce += 1
        elif effect == "furnace_payload":
            player.explosion_radius += 18
        elif effect == "arc_splitter":
            player.lightning_chain_range += 24
        elif effect == "venom_payload":
            player.poison_duration += 0.8
        elif effect == "reinforced_plating":
            player.armor = min(0.38, player.armor + 0.05)
        elif effect == "reactive_shell":
            player.damage_invuln_bonus += 0.08
        elif effect == "cryo_insulation":
            player.cryo_duration_bonus += 0.3
        elif effect == "volatile_hull":
            player.explosion_radius += 14
        elif effect == "conductive_chassis":
            player.turret_damage_mult *= 1.10
        elif effect == "salvage_beacon":
            player.magnet_radius += 36
        elif effect == "shock_capacitor":
            player.ability_power_mult *= 1.10
        elif effect == "lucky_scrap_charm":
            player.gear_chest_bonus += 0.05
        elif effect == "focus_lens":
            player.crit_chance += 0.05
            player.status_duration_mult *= 1.10
        elif effect == "emergency_repair":
            player.regen_per_second += 0.45
        elif effect == "track_ram":
            player.ram_damage_mult *= 1.30
            player.ram_knockback_mult *= 1.25
        elif effect == "track_drift":
            player.handling_response += 5.0
            player.speed *= 1.05
            player.track_dash_mult *= 1.10
        elif effect == "track_magnet":
            player.magnet_radius += 64
        elif effect == "track_stability":
            player.contact_damage_reduction += 0.10
            player.damage_invuln_bonus += 0.07
        elif effect == "track_siege":
            player.ram_damage_mult *= 1.48
            player.ram_knockback_mult *= 1.32
        elif effect == "track_scout":
            player.speed *= 1.10
            player.handling_response += 2.5

    tree_allocations = allocations(save_data, player.tank_id)
    player.skill_points = available_skill_points(save_data, player.tank_id)
    for node in tree_allocations:
        if node == "strength_impact":
            player.Strength += 1
            player.ram_damage_mult *= 1.12
        elif node == "strength_ram":
            player.ram_damage_mult *= 1.45
            player.ram_knockback_mult *= 1.35
        elif node == "strength_blast":
            player.explosion_radius += 22
        elif node == "dexterity_trigger":
            player.Dexterity += 1
        elif node == "dexterity_vector":
            player.handling_response += 5.0
        elif node == "dexterity_cycle":
            player.ability_cooldown_reduction += 0.10
        elif node == "vitality_hull":
            player.Vitality += 1
        elif node == "vitality_repair":
            player.regen_per_second += 0.7
        elif node == "vitality_contact":
            player.contact_damage_reduction += 0.14
        elif node == "tech_grid":
            player.Tech += 1
        elif node == "tech_turret":
            player.turret_damage_mult *= 1.20
            player.engineer_turret_rate_bonus += 0.10
        elif node == "tech_contract":
            player.contract_coin_bonus += 2
        elif node == "focus_calibration":
            player.Focus += 1
        elif node == "focus_pulse":
            player.ability_power_mult *= 1.16
        elif node == "focus_status":
            player.status_duration_mult *= 1.25
        elif node == "luck_salvage":
            player.Luck += 1
        elif node == "luck_chest":
            player.gear_chest_bonus += 0.08
        elif node == "luck_contract":
            player.contract_blueprint_bonus_chance += 0.15

    # 4. Apply stat scaling to attributes
    player.bullet_damage *= 1.0 + player.Strength * 0.03
    player.fire_rate *= 1.0 + player.Dexterity * 0.03
    player.bullet_speed *= 1.0 + player.Dexterity * 0.02
    player.bullet_range *= 1.0 + player.Dexterity * 0.02
    player.max_health += player.Vitality * 5
    player.health = player.max_health
    player.armor = min(0.38, player.armor + player.Vitality * 0.01)
    player.turret_damage_mult *= 1.0 + player.Tech * 0.05
    player.crit_chance += player.Luck * 0.02
    player.luck += player.Luck * 0.03
    if "boss_relic_damage" in player.equipped_effects:
        player.boss_damage_bonus += 0.12

    xp_mult = 1.0 + int(levels.get("xp_bonus", 0)) * 0.06
    coin_mult = 1.0 + int(levels.get("coin_bonus", 0)) * 0.07
    bonuses = achievement_bonuses(save_data)
    player.max_health *= 1.0 + bonuses["max_health"]
    player.health = player.max_health
    player.speed *= 1.0 + bonuses["move_speed"]
    player.fire_rate *= 1.0 + bonuses["fire_rate"]
    player.bullet_damage *= 1.0 + bonuses["damage"]
    player.magnet_radius += bonuses["pickup_radius"]
    player.boss_damage_bonus += bonuses["boss_damage"]
    player.luck += bonuses["luck"]
    player.luck += bonuses["drop_rate"]
    player.passive_regen_rate *= 1.0 + bonuses["regen_rate"]
    player.ability_cooldown_reduction += bonuses["ability_cooldown"]
    xp_mult *= 1.0 + bonuses["xp_gain"]
    coin_mult *= 1.0 + bonuses["coin_gain"]
    return xp_mult, coin_mult
