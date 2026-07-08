from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Iterable

from .progression import CONTENT_GATED_UPGRADES


BRANCH_LABELS = {
    "ballistics": "Ballistics",
    "explosives": "Explosives",
    "engineer": "Engineer",
    "defense": "Defense",
    "mobility": "Mobility",
    "ability": "Ability",
    "general": "Core",
}

RARITY_LABELS = {
    "common": "Common",
    "rare": "Rare",
    "epic": "Epic",
    "evolution": "Evolution",
}


@dataclass(frozen=True)
class Upgrade:
    id: str
    name: str
    description: str
    icon: str
    branch: str = "general"
    tier: int = 1
    max_stack: int | None = None
    weight: float = 1.0
    prerequisites: tuple[tuple[str, int], ...] = ()
    tags: tuple[str, ...] = ()
    rarity: str = "common"
    any_prerequisites: tuple[tuple[str, int], ...] = ()
    family: str = "Core"
    tank_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        # Compatibility with the old positional form:
        # Upgrade(id, name, description, icon, max_stack, weight)
        if not isinstance(self.branch, str):
            legacy_max_stack = self.branch
            legacy_weight = self.tier
            object.__setattr__(self, "branch", "general")
            object.__setattr__(self, "tier", 1)
            object.__setattr__(self, "max_stack", None if legacy_max_stack is None else int(legacy_max_stack))
            object.__setattr__(self, "weight", float(legacy_weight))


@dataclass(frozen=True)
class FamilyPassive:
    id: str
    family: str
    threshold: int
    roman_tier: str
    name: str
    description: str
    icon: str


@dataclass(frozen=True)
class FamilyEvolution:
    id: str
    family: str
    threshold: int
    name: str
    description: str
    icon: str


FAMILY_THRESHOLDS = (2, 4, 6)
FAMILY_EVOLUTION_THRESHOLD = 10
FAMILY_EVOLUTION_BIAS_START = 7

FAMILY_LABELS = {
    "Projectile": "Projectile",
    "Fire": "Fire",
    "Cryo": "Cryo",
    "Lightning": "Lightning",
    "Poison": "Poison",
    "Defense": "Defense",
    "Summon": "Summon",
    "Mobility": "Mobility",
    "Economy": "Economy",
    "Ability": "Ability",
    "Critical": "Critical",
    "Explosion": "Explosion",
    "Core": "Core",
}

PASSIVE_DEFINITIONS: dict[str, tuple[FamilyPassive, ...]] = {
    "Projectile": (
        FamilyPassive("Projectile:2", "Projectile", 2, "I", "Ballistic Momentum", "+5% bullet speed.", "bullet_speed"),
        FamilyPassive("Projectile:4", "Projectile", 4, "II", "Traveling Impact", "Shots gain bonus damage after traveling.", "bullet_damage"),
        FamilyPassive("Projectile:6", "Projectile", 6, "III", "Piercing Rhythm", "Every 8th shot pierces one extra enemy.", "pierce"),
    ),
    "Fire": (
        FamilyPassive("Fire:2", "Fire", 2, "I", "Hotter Fuel", "Burn effects last longer.", "burn_oil"),
        FamilyPassive("Fire:4", "Fire", 4, "II", "Burning Core", "Burning deaths may spread flames.", "burn_oil"),
        FamilyPassive("Fire:6", "Fire", 6, "III", "Flameburst Engine", "Every few shots adds a small flame burst.", "explosive_shot"),
    ),
    "Cryo": (
        FamilyPassive("Cryo:2", "Cryo", 2, "I", "Deep Chill", "Slow effects last longer.", "freeze_shot"),
        FamilyPassive("Cryo:4", "Cryo", 4, "II", "Frostbite Targeting", "Slowed enemies take extra projectile damage.", "freeze_shot"),
        FamilyPassive("Cryo:6", "Cryo", 6, "III", "Freeze Capacitor", "Periodic shots create a freeze burst.", "freeze_shot"),
    ),
    "Lightning": (
        FamilyPassive("Lightning:2", "Lightning", 2, "I", "Extended Arcs", "Chain lightning reaches farther.", "lightning_chain"),
        FamilyPassive("Lightning:4", "Lightning", 4, "II", "Overload Pulse", "Repeated hits trigger extra arcs.", "lightning_chain"),
        FamilyPassive("Lightning:6", "Lightning", 6, "III", "Storm Lattice", "Arcs can hit one extra enemy.", "lightning_chain"),
    ),
    "Poison": (
        FamilyPassive("Poison:2", "Poison", 2, "I", "Lingering Toxin", "Toxin stacks up to 3 and lasts longer.", "poison_shot"),
        FamilyPassive("Poison:4", "Poison", 4, "II", "Corrosive Venom", "Poisoned enemies take 8% more damage.", "poison_shot"),
        FamilyPassive("Poison:6", "Poison", 6, "III", "Toxic Cloud", "Poison deaths spread a capped toxic cloud.", "poison_shot"),
    ),
    "Defense": (
        FamilyPassive("Defense:2", "Defense", 2, "I", "Reinforced Timing", "Damage invulnerability lasts slightly longer.", "armor"),
        FamilyPassive("Defense:4", "Defense", 4, "II", "Repulsor Plating", "Taking damage releases a knockback pulse.", "emergency_shield"),
        FamilyPassive("Defense:6", "Defense", 6, "III", "Emergency Loop", "Low-health shield cooldown is reduced.", "emergency_shield"),
    ),
    "Economy": (
        FamilyPassive("Economy:2", "Economy", 2, "I", "Salvage Margin", "Coin gain is slightly increased.", "coin_gain"),
        FamilyPassive("Economy:4", "Economy", 4, "II", "Magnet Heart", "A pickup pulse fires every few seconds.", "magnet_pulse"),
        FamilyPassive("Economy:6", "Economy", 6, "III", "Prize Calibration", "Chests have slightly better quality odds.", "lucky_drop"),
    ),
    "Summon": (
        FamilyPassive("Summon:2", "Summon", 2, "I", "Servomotor Sync", "Summons gain a little range.", "shield_drone"),
        FamilyPassive("Summon:4", "Summon", 4, "II", "Drone Focus", "Summons hit a little harder.", "targeting_ai"),
        FamilyPassive("Summon:6", "Summon", 6, "III", "Network Relay", "Swarm drones deploy more reliably.", "shield_drone"),
    ),
    "Mobility": (
        FamilyPassive("Mobility:2", "Mobility", 2, "I", "Hyper Treads", "Movement speed improves slightly.", "move_speed"),
        FamilyPassive("Mobility:4", "Mobility", 4, "II", "Drift Engine", "Moving charge shields build faster.", "dash_cooldown"),
        FamilyPassive("Mobility:6", "Mobility", 6, "III", "Kinetic Loop", "Dash cooldown is reduced.", "dash_cooldown"),
    ),
    "Ability": (
        FamilyPassive("Ability:2", "Ability", 2, "I", "Coolant Routing", "Active abilities recharge faster.", "overclock"),
        FamilyPassive("Ability:4", "Ability", 4, "II", "Mana Condenser", "Active abilities hit harder.", "overclock"),
        FamilyPassive("Ability:6", "Ability", 6, "III", "Overdrive Loop", "Leveling grants a stronger overclock burst.", "overclock"),
    ),
    "Critical": (
        FamilyPassive("Critical:2", "Critical", 2, "I", "Target Optics", "Critical chance improves slightly.", "crit_chance"),
        FamilyPassive("Critical:4", "Critical", 4, "II", "Weakspot Memory", "Critical hits hit a little harder.", "crit_chance"),
        FamilyPassive("Critical:6", "Critical", 6, "III", "Execution Lens", "Critical kills can refund a spark of XP.", "crit_chance"),
    ),
    "Explosion": (
        FamilyPassive("Explosion:2", "Explosion", 2, "I", "Blast Packing", "Explosions are slightly larger.", "explosive_shot"),
        FamilyPassive("Explosion:4", "Explosion", 4, "II", "Shrapnel Bloom", "Explosions deal steadier splash damage.", "bullet_size"),
        FamilyPassive("Explosion:6", "Explosion", 6, "III", "Chain Fuse", "Explosion kills may trigger a tiny capped blast.", "explosive_shot"),
    ),
}

PASSIVE_BY_ID = {
    passive.id: passive
    for passives in PASSIVE_DEFINITIONS.values()
    for passive in passives
}

FAMILY_EVOLUTIONS: dict[str, FamilyEvolution] = {
    "Fire": FamilyEvolution(
        "inferno_core",
        "Fire",
        FAMILY_EVOLUTION_THRESHOLD,
        "Inferno Core",
        "Burning kills release small flame bursts.",
        "burn_oil",
    ),
    "Poison": FamilyEvolution(
        "plague_network",
        "Poison",
        FAMILY_EVOLUTION_THRESHOLD,
        "Plague Network",
        "Poison spreads to nearby enemies.",
        "poison_shot",
    ),
    "Cryo": FamilyEvolution(
        "absolute_zero",
        "Cryo",
        FAMILY_EVOLUTION_THRESHOLD,
        "Absolute Zero",
        "Chilled enemies become vulnerable.",
        "freeze_shot",
    ),
    "Lightning": FamilyEvolution(
        "storm_grid",
        "Lightning",
        FAMILY_EVOLUTION_THRESHOLD,
        "Storm Grid",
        "Lightning arcs farther and occasionally pulses.",
        "lightning_chain",
    ),
}

FAMILY_EVOLUTION_BY_ID = {evolution.id: evolution for evolution in FAMILY_EVOLUTIONS.values()}


UPGRADES: tuple[Upgrade, ...] = (
    # Ballistics branch
    Upgrade(
        "rapid_fire",
        "Spool Chamber",
        "Barrel cycles faster.",
        "rapid_fire",
        branch="ballistics",
        tier=1,
        max_stack=5,
        weight=1.1,
        tags=("projectile", "fire_rate"),
    ),
    Upgrade(
        "bullet_damage",
        "High-Caliber Core",
        "Shots punch harder.",
        "bullet_damage",
        branch="ballistics",
        tier=1,
        max_stack=5,
        weight=1.1,
        tags=("projectile", "damage"),
    ),
    Upgrade(
        "bullet_speed",
        "Coil Accelerator",
        "Shots fly faster and farther.",
        "bullet_speed",
        branch="ballistics",
        tier=1,
        max_stack=4,
        weight=0.82,
        tags=("projectile",),
    ),
    Upgrade(
        "multi_shot",
        "Forked Barrel",
        "Adds another shot to each volley.",
        "multi_shot",
        branch="ballistics",
        tier=1,
        max_stack=3,
        weight=0.78,
        tags=("projectile", "crowd_clear"),
    ),
    Upgrade(
        "pierce",
        "Rail Punch",
        "Shots punch through another target.",
        "pierce",
        branch="ballistics",
        tier=1,
        max_stack=4,
        weight=0.86,
        tags=("projectile",),
    ),
    Upgrade(
        "crit_chance",
        "Target Optics",
        "Weak spots light up more often.",
        "crit_chance",
        branch="ballistics",
        tier=2,
        max_stack=4,
        weight=0.66,
        prerequisites=(("bullet_damage", 1),),
        tags=("projectile", "damage"),
        rarity="rare",
    ),
    Upgrade(
        "ricochet",
        "Ricochet Core",
        "Bullets bounce off walls once.",
        "ricochet",
        branch="ballistics",
        tier=2,
        max_stack=2,
        weight=0.62,
        prerequisites=(("pierce", 1),),
        tags=("projectile", "crowd_clear"),
        rarity="rare",
    ),
    Upgrade(
        "hollow_point",
        "Heavy Rounds",
        "More damage, slower fire.",
        "hollow_point",
        branch="ballistics",
        tier=2,
        max_stack=3,
        weight=0.62,
        prerequisites=(("bullet_damage", 2),),
        tags=("projectile", "damage"),
        rarity="rare",
    ),
    Upgrade(
        "freeze_shot",
        "Cryo Coating",
        "Hits can slow enemies.",
        "freeze_shot",
        branch="ballistics",
        tier=2,
        max_stack=3,
        weight=0.58,
        prerequisites=(("bullet_speed", 1),),
        tags=("projectile", "crowd_control"),
        rarity="rare",
    ),
    Upgrade(
        "frostbite_rounds",
        "Frostbite Rounds",
        "Slowed enemies take more bullet damage.",
        "freeze_shot",
        branch="ballistics",
        tier=2,
        max_stack=3,
        weight=0.5,
        prerequisites=(("freeze_shot", 1),),
        tags=("projectile", "crowd_control", "damage"),
        rarity="rare",
    ),
    Upgrade(
        "shatter_freeze",
        "Shatter Freeze",
        "Slowed kills burst into fragments.",
        "freeze_shot",
        branch="ballistics",
        tier=3,
        max_stack=2,
        weight=0.42,
        prerequisites=(("freeze_shot", 2),),
        tags=("projectile", "crowd_control", "fragment"),
        rarity="epic",
    ),
    Upgrade(
        "ice_barrier",
        "Ice Barrier",
        "Taking damage releases a chill pulse.",
        "freeze_shot",
        branch="defense",
        tier=2,
        max_stack=2,
        weight=0.44,
        any_prerequisites=(("freeze_shot", 1), ("armor", 1)),
        tags=("defense", "crowd_control"),
        rarity="rare",
    ),
    Upgrade(
        "split_shot",
        "Shatter Rounds",
        "Bullets split after a hit.",
        "split_shot",
        branch="ballistics",
        tier=3,
        max_stack=3,
        weight=0.55,
        any_prerequisites=(("bullet_damage", 2), ("pierce", 1)),
        tags=("projectile", "fragment", "crowd_clear"),
        rarity="epic",
    ),
    Upgrade(
        "overpressure_ammo",
        "Overpressure Ammo",
        "Every 6th shot becomes a heavy round.",
        "bullet_damage",
        branch="ballistics",
        tier=2,
        max_stack=3,
        weight=0.56,
        prerequisites=(("bullet_damage", 1),),
        tags=("projectile", "knockback"),
        rarity="rare",
    ),
    Upgrade(
        "serrated_rounds",
        "Serrated Rounds",
        "Pierced targets take bonus damage.",
        "pierce",
        branch="ballistics",
        tier=3,
        max_stack=3,
        weight=0.48,
        prerequisites=(("pierce", 2),),
        tags=("projectile", "damage"),
        rarity="epic",
    ),
    Upgrade(
        "corrosion_rounds",
        "Corrosion Rounds",
        "Hits weaken enemy armor briefly.",
        "bullet_damage",
        branch="ballistics",
        tier=2,
        max_stack=3,
        weight=0.52,
        prerequisites=(("rapid_fire", 2),),
        tags=("projectile", "debuff"),
        rarity="rare",
    ),

    # Explosives branch
    Upgrade(
        "bullet_size",
        "Heavy Caliber",
        "Bigger rounds add impact and blast.",
        "bullet_size",
        branch="explosives",
        tier=1,
        max_stack=4,
        weight=0.85,
        tags=("projectile", "aoe"),
    ),
    Upgrade(
        "explosive_shot",
        "Explosive Shot",
        "Bullets burst on impact.",
        "explosive_shot",
        branch="explosives",
        tier=1,
        max_stack=3,
        weight=0.76,
        tags=("projectile", "aoe"),
    ),
    Upgrade(
        "lightning_chain",
        "Static Charge",
        "Every few shots chain lightning.",
        "lightning_chain",
        branch="explosives",
        tier=1,
        max_stack=4,
        weight=0.68,
        tags=("aoe", "crowd_clear"),
    ),
    Upgrade(
        "arc_rounds",
        "Arc Rounds",
        "Shots occasionally arc to a nearby target.",
        "lightning_chain",
        branch="explosives",
        tier=2,
        max_stack=3,
        weight=0.54,
        prerequisites=(("lightning_chain", 1),),
        tags=("aoe", "crowd_clear"),
        rarity="rare",
    ),
    Upgrade(
        "capacitor_link",
        "Capacitor Link",
        "Turrets can chain lightning.",
        "lightning_chain",
        branch="engineer",
        tier=2,
        max_stack=2,
        weight=0.48,
        any_prerequisites=(("lightning_chain", 1), ("side_cannon", 1), ("shield_drone", 1)),
        tags=("summon", "aoe"),
        rarity="rare",
    ),
    Upgrade(
        "storm_battery",
        "Storm Battery",
        "Faster firing charges arcs sooner.",
        "lightning_chain",
        branch="explosives",
        tier=3,
        max_stack=2,
        weight=0.4,
        any_prerequisites=(("rapid_fire", 2), ("lightning_chain", 2)),
        tags=("aoe", "fire_rate"),
        rarity="epic",
    ),
    Upgrade(
        "poison_shot",
        "Toxic Rounds",
        "Hits stack toxic damage and corrosion.",
        "poison_shot",
        branch="explosives",
        tier=1,
        max_stack=3,
        weight=0.6,
        tags=("projectile", "dot"),
    ),
    Upgrade(
        "plague_burst",
        "Plague Burst",
        "Poisoned kills spread toxin farther.",
        "poison_shot",
        branch="explosives",
        tier=2,
        max_stack=3,
        weight=0.5,
        prerequisites=(("poison_shot", 1),),
        tags=("projectile", "dot", "crowd_clear"),
        rarity="rare",
    ),
    Upgrade(
        "acid_pool",
        "Acid Pool",
        "Poison kills splash corrosive toxin.",
        "poison_shot",
        branch="explosives",
        tier=3,
        max_stack=2,
        weight=0.4,
        prerequisites=(("poison_shot", 2),),
        tags=("dot", "aoe"),
        rarity="epic",
    ),
    Upgrade(
        "venom_engine",
        "Venom Engine",
        "Toxins hit harder and last longer.",
        "poison_shot",
        branch="explosives",
        tier=2,
        max_stack=3,
        weight=0.46,
        prerequisites=(("poison_shot", 1),),
        tags=("projectile", "dot"),
        rarity="rare",
    ),
    Upgrade(
        "volatile_payload",
        "Volatile Payload",
        "Bullet kills can explode.",
        "explosive_shot",
        branch="explosives",
        tier=2,
        max_stack=3,
        weight=0.52,
        prerequisites=(("explosive_shot", 1),),
        tags=("projectile", "aoe", "crowd_clear"),
        rarity="rare",
    ),
    Upgrade(
        "burn_oil",
        "Burn Oil",
        "Shots can ignite enemies.",
        "poison_shot",
        branch="explosives",
        tier=2,
        max_stack=3,
        weight=0.54,
        any_prerequisites=(("explosive_shot", 1), ("poison_shot", 1)),
        tags=("projectile", "fire", "dot"),
        rarity="rare",
    ),
    Upgrade(
        "wildfire_rounds",
        "Wildfire Rounds",
        "Burning kills can spread burn.",
        "poison_shot",
        branch="explosives",
        tier=2,
        max_stack=3,
        weight=0.5,
        prerequisites=(("burn_oil", 1),),
        tags=("projectile", "fire", "dot", "crowd_clear"),
        rarity="rare",
    ),
    Upgrade(
        "molten_payload",
        "Molten Payload",
        "Explosions apply brief burn.",
        "explosive_shot",
        branch="explosives",
        tier=3,
        max_stack=2,
        weight=0.42,
        any_prerequisites=(("burn_oil", 1), ("explosive_shot", 2)),
        tags=("fire", "aoe"),
        rarity="epic",
    ),
    Upgrade(
        "ash_collector",
        "Ash Collector",
        "Burning kills can drop salvage.",
        "coin_gain",
        branch="mobility",
        tier=2,
        max_stack=2,
        weight=0.4,
        prerequisites=(("burn_oil", 1),),
        tags=("fire", "economy"),
        rarity="rare",
    ),

    # Engineer branch
    Upgrade(
        "side_cannon",
        "Turret Support",
        "Adds auto-firing side cannons.",
        "side_cannon",
        branch="engineer",
        tier=1,
        max_stack=3,
        weight=0.76,
        tags=("summon",),
    ),
    Upgrade(
        "shield_drone",
        "Orbiting Drone",
        "Drone damages nearby bots.",
        "shield_drone",
        branch="engineer",
        tier=1,
        max_stack=3,
        weight=0.7,
        tags=("summon", "defense"),
    ),
    Upgrade(
        "targeting_ai",
        "Targeting Relay",
        "Summons hit harder and prefer elites.",
        "targeting_ai",
        branch="engineer",
        tier=2,
        max_stack=3,
        weight=0.56,
        prerequisites=(("side_cannon", 1),),
        tags=("summon", "boss"),
        rarity="rare",
    ),
    Upgrade(
        "mine_layer",
        "Mine Layer",
        "Shots may drop mines.",
        "mine_layer",
        branch="engineer",
        tier=2,
        max_stack=3,
        weight=0.56,
        tags=("summon", "aoe"),
        rarity="rare",
    ),
    Upgrade(
        "drone_swarm",
        "Drone Swarm",
        "Kill streaks deploy temporary drones.",
        "shield_drone",
        branch="engineer",
        tier=3,
        max_stack=2,
        weight=0.42,
        any_prerequisites=(("shield_drone", 2), ("side_cannon", 2)),
        tags=("summon", "crowd_clear"),
        rarity="epic",
    ),
    Upgrade(
        "repair_drone",
        "Repair Drone",
        "A drone slowly heals your tank.",
        "shield_drone",
        branch="engineer",
        tier=2,
        max_stack=2,
        weight=0.52,
        prerequisites=(("shield_drone", 1),),
        tags=("summon", "regen", "defense"),
        rarity="rare",
    ),

    # Defense branch
    Upgrade(
        "max_health",
        "Reinforced Hull",
        "+18 max health and repair.",
        "max_health",
        branch="defense",
        tier=1,
        max_stack=4,
        weight=0.86,
        tags=("defense",),
    ),
    Upgrade(
        "armor",
        "Scrap Armor",
        "Reduce incoming damage.",
        "armor",
        branch="defense",
        tier=1,
        max_stack=4,
        weight=0.72,
        tags=("defense",),
    ),
    Upgrade(
        "nanobot_repair",
        "Repair Nanites",
        "After avoiding damage, regenerate slowly.",
        "nanobot_repair",
        branch="defense",
        tier=2,
        max_stack=3,
        weight=0.6,
        prerequisites=(("max_health", 1),),
        tags=("defense", "regen"),
        rarity="rare",
    ),
    Upgrade(
        "emergency_shield",
        "Emergency Plating",
        "Brief shield at low HP.",
        "emergency_shield",
        branch="defense",
        tier=2,
        max_stack=2,
        weight=0.55,
        prerequisites=(("armor", 1),),
        tags=("defense",),
        rarity="rare",
    ),
    Upgrade(
        "kinetic_barrier",
        "Kinetic Barrier",
        "Moving builds a small shield.",
        "armor",
        branch="defense",
        tier=2,
        max_stack=2,
        weight=0.5,
        prerequisites=(("move_speed", 2),),
        tags=("defense", "mobility"),
        rarity="rare",
    ),
    Upgrade(
        "last_stand",
        "Last Stand Capacitor",
        "Low HP boosts fire rate and vacuum.",
        "emergency_shield",
        branch="defense",
        tier=3,
        max_stack=2,
        weight=0.42,
        prerequisites=(("emergency_shield", 1),),
        tags=("defense", "fire_rate", "economy"),
        rarity="epic",
    ),

    # Mobility and economy branch
    Upgrade(
        "move_speed",
        "Hyper Treads",
        "+15% speed and better impact spacing.",
        "move_speed",
        branch="mobility",
        tier=1,
        max_stack=4,
        weight=0.9,
        tags=("mobility",),
    ),
    Upgrade(
        "magnet",
        "Scrap Magnet",
        "Pulse-pulls pickups from farther away.",
        "magnet",
        branch="mobility",
        tier=1,
        max_stack=5,
        weight=0.9,
        tags=("economy",),
    ),
    Upgrade(
        "xp_gain",
        "Data Leech",
        "Bonus XP sparks feed faster leveling.",
        "xp_gain",
        branch="mobility",
        tier=1,
        max_stack=4,
        weight=0.72,
        tags=("economy",),
    ),
    Upgrade(
        "coin_gain",
        "Salvage Booster",
        "Coin pickups pay out more.",
        "coin_gain",
        branch="mobility",
        tier=1,
        max_stack=3,
        weight=0.55,
        tags=("economy",),
    ),
    Upgrade(
        "dash_cooldown",
        "Dash Coolant",
        "Dash recharges faster.",
        "dash_cooldown",
        branch="mobility",
        tier=1,
        max_stack=3,
        weight=0.65,
        tags=("mobility", "ability"),
    ),
    Upgrade(
        "magnet_pulse",
        "Magnet Pulse",
        "Periodically vacuums pickups.",
        "magnet_pulse",
        branch="mobility",
        tier=2,
        max_stack=3,
        weight=0.58,
        prerequisites=(("magnet", 2),),
        tags=("economy",),
        rarity="rare",
    ),
    Upgrade(
        "lucky_drop",
        "Lucky Drops",
        "More rare pickups.",
        "lucky_drop",
        branch="mobility",
        tier=2,
        max_stack=3,
        weight=0.55,
        tags=("economy",),
        rarity="rare",
    ),
    Upgrade(
        "bloodless_harvest",
        "Bloodless Harvest",
        "Full-health pickups grant shield, then coins.",
        "max_health",
        branch="mobility",
        tier=2,
        max_stack=1,
        weight=0.5,
        prerequisites=(("max_health", 1),),
        tags=("economy", "defense"),
        rarity="rare",
    ),
    Upgrade(
        "salvage_converter",
        "Salvage Converter",
        "Excess level-up XP becomes coins.",
        "xp_gain",
        branch="mobility",
        tier=2,
        max_stack=3,
        weight=0.48,
        prerequisites=(("xp_gain", 1),),
        tags=("economy",),
        rarity="rare",
    ),

    # Ability branch
    Upgrade(
        "overclock",
        "Overclock",
        "Fire-rate burst after levels.",
        "overclock",
        branch="ability",
        tier=2,
        max_stack=3,
        weight=0.62,
        prerequisites=(("rapid_fire", 1),),
        tags=("ability", "fire_rate"),
        rarity="rare",
    ),
    Upgrade(
        "coolant_loop",
        "Coolant Loop",
        "Reduce active ability cooldowns.",
        "dash_cooldown",
        branch="ability",
        tier=2,
        max_stack=3,
        weight=0.52,
        prerequisites=(("dash_cooldown", 1),),
        tags=("ability",),
        rarity="rare",
    ),
    Upgrade(
        "mana_battery",
        "Mana Battery",
        "Active abilities hit harder.",
        "overclock",
        branch="ability",
        tier=1,
        max_stack=3,
        weight=0.58,
        tags=("ability", "damage"),
    ),
    Upgrade(
        "cursor_minefield",
        "Cursor Minefield",
        "Abilities drop mines near the cursor.",
        "mine_layer",
        branch="ability",
        tier=3,
        max_stack=2,
        weight=0.4,
        prerequisites=(("mana_battery", 1),),
        tags=("ability", "aoe"),
        rarity="epic",
    ),
    Upgrade(
        "firestorm_catalyst",
        "Firestorm Catalyst",
        "Fireballs split into burning fragments.",
        "explosive_shot",
        branch="ability",
        tier=3,
        max_stack=2,
        weight=0.38,
        any_prerequisites=(("burn_oil", 1), ("explosive_shot", 2)),
        tags=("ability", "fire", "aoe"),
        rarity="epic",
    ),

    # Core practical option
    Upgrade(
        "repair",
        "Emergency Repair",
        "Heal now, gain protection, then overdrive.",
        "repair",
        branch="general",
        tier=1,
        max_stack=None,
        weight=0.72,
        tags=("defense", "regen"),
    ),

    # Evolution cards
    Upgrade(
        "minigun_core",
        "Minigun Core",
        "Evolve into a high-rate bullet stream.",
        "minigun_mode",
        branch="ballistics",
        tier=4,
        max_stack=1,
        weight=0.34,
        prerequisites=(("rapid_fire", 4), ("multi_shot", 2)),
        tags=("evolution", "projectile", "fire_rate"),
        rarity="evolution",
    ),
    Upgrade(
        "railgun_core",
        "Railgun Core",
        "Evolve into piercing precision shots.",
        "pierce",
        branch="ballistics",
        tier=4,
        max_stack=1,
        weight=0.34,
        prerequisites=(("bullet_damage", 3), ("bullet_speed", 2), ("pierce", 2)),
        tags=("evolution", "projectile", "damage"),
        rarity="evolution",
    ),
    Upgrade(
        "scrapstorm_detonator",
        "Scrapstorm Detonator",
        "Evolve explosions into fragment storms.",
        "rocket_core",
        branch="explosives",
        tier=4,
        max_stack=1,
        weight=0.34,
        prerequisites=(("explosive_shot", 3), ("bullet_size", 2)),
        tags=("evolution", "aoe", "fragment"),
        rarity="evolution",
    ),
    Upgrade(
        "drone_network",
        "Drone Network",
        "Evolve summons into coordinated support.",
        "shield_drone",
        branch="engineer",
        tier=4,
        max_stack=1,
        weight=0.34,
        prerequisites=(("shield_drone", 2), ("side_cannon", 2)),
        tags=("evolution", "summon"),
        rarity="evolution",
    ),
    Upgrade(
        "fortress_core",
        "Fortress Core",
        "Evolve into a slower armored tank.",
        "armor",
        branch="defense",
        tier=4,
        max_stack=1,
        weight=0.34,
        prerequisites=(("max_health", 3), ("armor", 2), ("emergency_shield", 1)),
        tags=("evolution", "defense"),
        rarity="evolution",
    ),
    Upgrade(
        "hyperdrive_core",
        "Hyperdrive Core",
        "Evolve into a fast vacuum build.",
        "magnet_pulse",
        branch="mobility",
        tier=4,
        max_stack=1,
        weight=0.34,
        prerequisites=(("move_speed", 3), ("magnet", 2)),
        tags=("evolution", "mobility", "economy"),
        rarity="evolution",
    ),

    # Unlock-added pool. These cards are deliberately unavailable until their
    # named milestone is completed; none of them are starter-pool upgrades.
    Upgrade(
        "conductive_wildfire",
        "Conductive Wildfire",
        "Fire spreads harder through conductive enemies.",
        "lightning_chain",
        branch="explosives",
        tier=3,
        max_stack=2,
        weight=0.32,
        prerequisites=(("burn_oil", 1), ("lightning_chain", 1)),
        tags=("fire", "lightning", "fusion"),
        rarity="epic",
    ),
    Upgrade(
        "toxic_frostbite",
        "Toxic Frostbite",
        "Poison gains power against chilled enemies.",
        "poison_shot",
        branch="ability",
        tier=3,
        max_stack=2,
        weight=0.32,
        prerequisites=(("poison_shot", 1), ("freeze_shot", 1)),
        tags=("poison", "cryo", "fusion"),
        rarity="epic",
    ),
    Upgrade(
        "storm_shatter",
        "Storm Shatter",
        "Lightning bursts from brittle enemies.",
        "freeze_shot",
        branch="ability",
        tier=3,
        max_stack=2,
        weight=0.32,
        prerequisites=(("lightning_chain", 1), ("freeze_shot", 1)),
        tags=("lightning", "cryo", "fusion"),
        rarity="epic",
    ),
    Upgrade(
        "salvage_momentum",
        "Salvage Momentum",
        "Contract progress grants a temporary combat boost.",
        "coin_gain",
        branch="general",
        tier=2,
        max_stack=2,
        weight=0.44,
        tags=("contract", "economy", "fire_rate"),
        rarity="rare",
    ),
    Upgrade(
        "blueprint_echo",
        "Blueprint Echo",
        "Contracts release a temporary XP pulse.",
        "xp_gain",
        branch="general",
        tier=2,
        max_stack=1,
        weight=0.38,
        tags=("contract", "xp", "economy"),
        rarity="rare",
    ),
    Upgrade(
        "relay_overcharge",
        "Relay Overcharge",
        "Charge your next shot while near the stage relay.",
        "magnet_pulse",
        branch="ability",
        tier=3,
        max_stack=2,
        weight=0.34,
        prerequisites=(("magnet", 1),),
        tags=("contract", "ability", "damage"),
        rarity="epic",
    ),
    Upgrade(
        "split_fireball",
        "Split Fireball",
        "Fireball bursts into two smaller flame impacts.",
        "ability_fireball",
        branch="ability",
        tier=3,
        max_stack=2,
        weight=0.34,
        prerequisites=(("burn_oil", 1),),
        tags=("ability", "variant", "fire"),
        rarity="epic",
        tank_ids=("flame_caster",),
    ),
    Upgrade(
        "chilling_ring",
        "Chilling Ring",
        "Frost Nova leaves a short slowing ring.",
        "ability_frost_nova",
        branch="ability",
        tier=3,
        max_stack=2,
        weight=0.34,
        prerequisites=(("freeze_shot", 1),),
        tags=("ability", "variant", "cryo"),
        rarity="epic",
        tank_ids=("cryo",),
    ),
    Upgrade(
        "corrosive_burst",
        "Corrosive Burst",
        "Acid Glob detonates into a corrosive poison pulse.",
        "ability_acid_glob",
        branch="ability",
        tier=3,
        max_stack=2,
        weight=0.34,
        prerequisites=(("poison_shot", 1),),
        tags=("ability", "variant", "poison"),
        rarity="epic",
        tank_ids=("poison",),
    ),
    Upgrade(
        "arc_echo",
        "Arc Echo",
        "Arc Surge can repeat a weaker second chain.",
        "ability_arc_surge",
        branch="ability",
        tier=3,
        max_stack=2,
        weight=0.34,
        prerequisites=(("lightning_chain", 1),),
        tags=("ability", "variant", "lightning"),
        rarity="epic",
        tank_ids=("lightning",),
    ),
)

UPGRADE_BY_ID = {upgrade.id: upgrade for upgrade in UPGRADES}

EVOLUTION_UPGRADE_TO_ID = {
    "minigun_core": "minigun_mode",
    "railgun_core": "railgun_core",
    "scrapstorm_detonator": "scrapstorm_detonator",
    "drone_network": "drone_network",
    "fortress_core": "fortress_core",
    "hyperdrive_core": "hyperdrive_core",
}

TANK_BRANCH_BIAS: dict[str, dict[str, float]] = {
    "starter": {},
    "sniper": {"ballistics": 1.45, "engineer": 0.55, "explosives": 0.82, "ability": 0.92},
    "engineer": {"engineer": 1.55, "ability": 1.2, "ballistics": 0.72},
    "twin_shot": {"ballistics": 1.32, "explosives": 1.2, "engineer": 0.9},
    "flame_caster": {"explosives": 1.55, "ability": 1.32, "ballistics": 0.72},
    "cryo": {"ballistics": 1.12, "ability": 1.08, "explosives": 0.82},
    "poison": {"ballistics": 1.1, "ability": 1.12, "explosives": 0.9},
    "lightning": {"ability": 1.3, "engineer": 1.15, "ballistics": 1.05},
}

TANK_FAMILY_BIAS: dict[str, dict[str, float]] = {
    "starter": {},
    "sniper": {"Projectile": 1.45, "Cryo": 1.35, "Critical": 1.25, "Summon": 0.65},
    "engineer": {"Summon": 1.55, "Lightning": 1.45, "Ability": 1.25, "Projectile": 0.82},
    "twin_shot": {"Projectile": 1.35, "Lightning": 1.18, "Critical": 1.12, "Defense": 0.92},
    "flame_caster": {"Fire": 1.6, "Explosion": 1.35, "Ability": 1.25, "Defense": 1.12, "Cryo": 0.65},
    "cryo": {"Cryo": 1.65, "Projectile": 1.22, "Defense": 1.14, "Critical": 1.12},
    "poison": {"Poison": 1.7, "Defense": 1.16, "Projectile": 1.18, "Economy": 1.12},
    "lightning": {"Lightning": 1.7, "Ability": 1.28, "Mobility": 1.25, "Summon": 1.14},
}

UPGRADE_FAMILY_OVERRIDES = {
    "rapid_fire": "Projectile",
    "bullet_damage": "Projectile",
    "bullet_speed": "Projectile",
    "multi_shot": "Projectile",
    "pierce": "Projectile",
    "ricochet": "Projectile",
    "hollow_point": "Projectile",
    "split_shot": "Projectile",
    "overpressure_ammo": "Projectile",
    "serrated_rounds": "Projectile",
    "minigun_core": "Projectile",
    "railgun_core": "Projectile",
    "crit_chance": "Critical",
    "bullet_size": "Explosion",
    "explosive_shot": "Explosion",
    "volatile_payload": "Explosion",
    "scrapstorm_detonator": "Explosion",
    "burn_oil": "Fire",
    "wildfire_rounds": "Fire",
    "molten_payload": "Fire",
    "ash_collector": "Fire",
    "firestorm_catalyst": "Fire",
    "conductive_wildfire": "Fire",
    "freeze_shot": "Cryo",
    "frostbite_rounds": "Cryo",
    "shatter_freeze": "Cryo",
    "ice_barrier": "Cryo",
    "lightning_chain": "Lightning",
    "arc_rounds": "Lightning",
    "capacitor_link": "Lightning",
    "storm_battery": "Lightning",
    "storm_shatter": "Lightning",
    "poison_shot": "Poison",
    "corrosion_rounds": "Poison",
    "plague_burst": "Poison",
    "acid_pool": "Poison",
    "venom_engine": "Poison",
    "toxic_frostbite": "Poison",
    "side_cannon": "Summon",
    "shield_drone": "Summon",
    "targeting_ai": "Summon",
    "mine_layer": "Summon",
    "drone_swarm": "Summon",
    "repair_drone": "Summon",
    "drone_network": "Summon",
    "max_health": "Defense",
    "armor": "Defense",
    "nanobot_repair": "Defense",
    "emergency_shield": "Defense",
    "kinetic_barrier": "Defense",
    "last_stand": "Defense",
    "fortress_core": "Defense",
    "repair": "Defense",
    "move_speed": "Mobility",
    "dash_cooldown": "Mobility",
    "hyperdrive_core": "Mobility",
    "magnet": "Economy",
    "xp_gain": "Economy",
    "coin_gain": "Economy",
    "magnet_pulse": "Economy",
    "salvage_momentum": "Economy",
    "blueprint_echo": "Economy",
    "relay_overcharge": "Ability",
    "split_fireball": "Fire",
    "chilling_ring": "Cryo",
    "corrosive_burst": "Poison",
    "arc_echo": "Lightning",
    "lucky_drop": "Economy",
    "bloodless_harvest": "Economy",
    "salvage_converter": "Economy",
    "overclock": "Ability",
    "coolant_loop": "Ability",
    "mana_battery": "Ability",
    "cursor_minefield": "Ability",
}


def _level(counts: object, upgrade_id: str) -> int:
    if hasattr(counts, "get"):
        return int(counts.get(upgrade_id, 0))
    return int(counts[upgrade_id])


def _meets_prerequisites(player: object, upgrade: Upgrade) -> bool:
    counts = player.upgrade_counts
    if any(_level(counts, req_id) < req_level for req_id, req_level in upgrade.prerequisites):
        return False
    if upgrade.any_prerequisites and not any(
        _level(counts, req_id) >= req_level for req_id, req_level in upgrade.any_prerequisites
    ):
        return False
    return True


def upgrade_family(upgrade: Upgrade) -> str:
    return UPGRADE_FAMILY_OVERRIDES.get(upgrade.id, upgrade.family)


def family_label(family: str) -> str:
    return FAMILY_LABELS.get(family, family.replace("_", " ").title())


def passive_id(family: str, threshold: int) -> str:
    return f"{family}:{threshold}"


def has_family_passive(player: object, family: str, threshold: int) -> bool:
    return passive_id(family, threshold) in getattr(player, "family_passives_unlocked", set())


def get_family_counts(player: object) -> dict[str, int]:
    counts: dict[str, int] = {}
    for upgrade in UPGRADES:
        level = _level(player.upgrade_counts, upgrade.id)
        if level <= 0:
            continue
        family = upgrade_family(upgrade)
        if family == "Core":
            continue
        counts[family] = counts.get(family, 0) + level
    return counts


def next_family_passive(player: object, family: str) -> FamilyPassive | None:
    current = get_family_counts(player).get(family, 0)
    for passive in PASSIVE_DEFINITIONS.get(family, ()):
        if current < passive.threshold:
            return passive
    return None


def get_active_passives(player: object) -> list[FamilyPassive]:
    unlocked = getattr(player, "family_passives_unlocked", set())
    active = [PASSIVE_BY_ID[passive_id] for passive_id in unlocked if passive_id in PASSIVE_BY_ID]
    return sorted(active, key=lambda passive: (passive.family, passive.threshold))


def get_active_evolutions(player: object) -> list[FamilyEvolution]:
    active = [
        FAMILY_EVOLUTION_BY_ID[evolution_id]
        for evolution_id in getattr(player, "evolutions", set())
        if evolution_id in FAMILY_EVOLUTION_BY_ID
    ]
    return sorted(active, key=lambda evolution: evolution.family)


def check_family_passives(player: object) -> list[FamilyPassive]:
    unlocked = getattr(player, "family_passives_unlocked", None)
    if unlocked is None:
        unlocked = set()
        setattr(player, "family_passives_unlocked", unlocked)
    counts = get_family_counts(player)
    newly_unlocked: list[FamilyPassive] = []
    for family, passives in PASSIVE_DEFINITIONS.items():
        count = counts.get(family, 0)
        for passive in passives:
            if count >= passive.threshold and passive.id not in unlocked:
                unlocked.add(passive.id)
                _apply_passive_bonus(player, passive)
                newly_unlocked.append(passive)
    setattr(player, "last_passive_unlocks", newly_unlocked)
    return newly_unlocked


def _apply_passive_bonus(player: object, passive: FamilyPassive) -> None:
    pid = passive.id
    if pid == "Projectile:2":
        player.bullet_speed *= 1.05
        player.bullet_range *= 1.03
    elif pid == "Projectile:4":
        player.travel_damage_bonus = max(getattr(player, "travel_damage_bonus", 0.0), 0.1)
    elif pid == "Fire:2":
        player.fire_duration_bonus = max(getattr(player, "fire_duration_bonus", 0.0), 0.55)
    elif pid == "Cryo:2":
        player.cryo_duration_bonus = max(getattr(player, "cryo_duration_bonus", 0.0), 0.45)
    elif pid == "Lightning:2":
        player.lightning_chain_range = max(getattr(player, "lightning_chain_range", 175.0), 230.0)
    elif pid == "Poison:2":
        player.poison_duration_bonus = max(getattr(player, "poison_duration_bonus", 0.0), 0.9)
    elif pid == "Defense:2":
        player.damage_invuln_bonus = max(getattr(player, "damage_invuln_bonus", 0.0), 0.08)
    elif pid == "Economy:2":
        player.run_coin_bonus *= 1.06
    elif pid == "Summon:2":
        player.turret_range_bonus += 35
    elif pid == "Summon:4":
        player.turret_damage_mult *= 1.08
    elif pid == "Mobility:2":
        player.speed *= 1.05
    elif pid == "Mobility:4":
        player.kinetic_charge_mult = max(getattr(player, "kinetic_charge_mult", 1.0), 1.18)
    elif pid == "Mobility:6":
        player.dash_cooldown_duration = max(0.62, player.dash_cooldown_duration * 0.9)
    elif pid == "Ability:2":
        player.ability_cooldown_reduction += 0.06
    elif pid == "Ability:4":
        player.ability_power_mult *= 1.08
    elif pid == "Critical:2":
        player.crit_chance += 0.03
    elif pid == "Critical:4":
        player.crit_damage_bonus = max(getattr(player, "crit_damage_bonus", 0.0), 0.14)
    elif pid == "Explosion:2":
        player.explosion_radius += 7
    elif pid == "Explosion:4":
        player.explosion_falloff_bonus = max(getattr(player, "explosion_falloff_bonus", 0.0), 0.08)


def family_progress_text(player: object, upgrade: Upgrade) -> str:
    family = upgrade_family(upgrade)
    if family == "Core":
        return "Core utility"
    label = family_label(family)
    counts = get_family_counts(player)
    current = counts.get(family, 0)
    for passive in PASSIVE_DEFINITIONS.get(family, ()):
        if current < passive.threshold:
            return f"{label}: {current}/{passive.threshold}"
    evolution = FAMILY_EVOLUTIONS.get(family)
    if evolution is not None:
        if evolution.id in getattr(player, "evolutions", set()):
            return f"{label}: Evolution active"
        return f"{label}: {current}/{evolution.threshold} -> Evolution"
    return f"{label}: {current}"


def unlock_hint_text(player: object, upgrade: Upgrade) -> str:
    family = upgrade_family(upgrade)
    if family != "Core":
        counts = get_family_counts(player)
        current = counts.get(family, 0)
        for passive in PASSIVE_DEFINITIONS.get(family, ()):
            if current < passive.threshold:
                needed = passive.threshold - current
                if needed <= 1:
                    return f"Next: {passive.name}"
                return ""
        evolution = FAMILY_EVOLUTIONS.get(family)
        if evolution is not None and evolution.id not in getattr(player, "evolutions", set()):
            if current + 1 >= evolution.threshold:
                return f"Unlocks {evolution.name}"
            if current >= FAMILY_EVOLUTION_BIAS_START:
                return "Next: Evolution"
    if upgrade.prerequisites or upgrade.any_prerequisites:
        return f"Path: deeper {family} investment"
    return ""


def _near_threshold_families(player: object) -> set[str]:
    counts = get_family_counts(player)
    near: set[str] = set()
    for family, passives in PASSIVE_DEFINITIONS.items():
        count = counts.get(family, 0)
        for passive in passives:
            if 0 < passive.threshold - count <= 1:
                near.add(family)
            if count < passive.threshold:
                break
    evolutions = getattr(player, "evolutions", set())
    for family, evolution in FAMILY_EVOLUTIONS.items():
        count = counts.get(family, 0)
        if evolution.id not in evolutions and FAMILY_EVOLUTION_BIAS_START <= count < evolution.threshold:
            near.add(family)
    return near


def available_upgrades(player: object) -> list[Upgrade]:
    choices: list[Upgrade] = []
    counts = player.upgrade_counts
    evolutions = getattr(player, "evolutions", set())
    for upgrade in UPGRADES:
        required_unlock = CONTENT_GATED_UPGRADES.get(upgrade.id)
        if required_unlock is not None and required_unlock not in getattr(player, "content_unlocks", set()):
            continue
        if upgrade.tank_ids and getattr(player, "tank_id", "starter") not in upgrade.tank_ids:
            continue
        if upgrade.max_stack is not None and _level(counts, upgrade.id) >= upgrade.max_stack:
            continue
        evolution_id = EVOLUTION_UPGRADE_TO_ID.get(upgrade.id)
        if evolution_id is not None and evolution_id in evolutions:
            continue
        if not _meets_prerequisites(player, upgrade):
            continue
        choices.append(upgrade)
    return choices


def choose_upgrades(player: object, count: int = 3, tank_id: str | None = None) -> list[Upgrade]:
    pool = available_upgrades(player)
    if len(pool) <= count:
        random.shuffle(pool)
        return pool

    tank_id = tank_id or getattr(player, "tank_id", "starter")
    active_branches = set(get_active_branches(player))
    family_counts = get_family_counts(player)
    active_families = {family for family, value in family_counts.items() if value > 0}
    near_families = _near_threshold_families(player)
    branch_bias = TANK_BRANCH_BIAS.get(tank_id, {})
    family_bias = TANK_FAMILY_BIAS.get(tank_id, {})
    selected: list[Upgrade] = []
    remaining = list(pool)

    while remaining and len(selected) < count:
        roll = random.random()
        if active_families and roll < 0.5:
            candidates = [u for u in remaining if upgrade_family(u) in active_families]
        elif roll < 0.75:
            candidates = [u for u in remaining if u.branch == "general" or u.tier == 1 or _is_practical(u, player)]
        elif near_families and roll < 0.9:
            candidates = [u for u in remaining if upgrade_family(u) in near_families]
        else:
            candidates = [
                u
                for u in remaining
                if upgrade_family(u) not in active_families and u.branch != "general" and u.tier <= 2
            ]
        if not candidates:
            candidates = remaining
        pick = _weighted_pick(candidates, active_branches, active_families, near_families, branch_bias, family_bias, getattr(player, "fusion_resonance_active", False))
        selected.append(pick)
        remaining.remove(pick)

    if count >= 3 and not any(_is_practical(upgrade, player) for upgrade in selected):
        practical = [upgrade for upgrade in remaining if _is_practical(upgrade, player)]
        if practical:
            selected[-1] = _weighted_pick(practical, active_branches, active_families, near_families, branch_bias, family_bias, getattr(player, "fusion_resonance_active", False))

    return selected


def _weighted_pick(
    candidates: list[Upgrade],
    active_branches: set[str],
    active_families: set[str],
    near_families: set[str],
    branch_bias: dict[str, float],
    family_bias: dict[str, float],
    fusion_resonance: bool = False,
) -> Upgrade:
    weights: list[float] = []
    for upgrade in candidates:
        family = upgrade_family(upgrade)
        weight = upgrade.weight
        if upgrade.branch in active_branches:
            weight *= 1.25
        if family in active_families:
            weight *= 1.75
        if family in near_families:
            weight *= 1.65
        elif upgrade.branch != "general" and upgrade.tier > 1:
            weight *= 0.45
        if upgrade.rarity == "evolution":
            weight *= 1.35 if (upgrade.branch in active_branches or family in active_families) else 0.7
        if fusion_resonance and "fusion" in upgrade.tags:
            weight *= 1.45
        weight *= branch_bias.get(upgrade.branch, 1.0)
        weight *= family_bias.get(family, 1.0)
        weights.append(max(0.01, weight))
    return random.choices(candidates, weights=weights, k=1)[0]


def _is_practical(upgrade: Upgrade, player: object) -> bool:
    if upgrade.id == "repair":
        return getattr(player, "health", 1) < getattr(player, "max_health", 1) * 0.72
    return upgrade_family(upgrade) in {"Defense", "Economy", "Mobility"} or bool({"defense", "economy", "regen"} & set(upgrade.tags))


def apply_upgrade(player: object, upgrade: Upgrade) -> list[str]:
    player.upgrade_counts[upgrade.id] += 1
    uid = upgrade.id

    if uid == "rapid_fire":
        player.fire_rate *= 1.16
    elif uid == "bullet_damage":
        player.bullet_damage *= 1.15
    elif uid == "multi_shot":
        player.multi_shot += 1
    elif uid == "move_speed":
        player.speed *= 1.15
    elif uid == "pierce":
        player.bullet_pierce += 1
    elif uid == "bullet_size":
        player.bullet_size += 2.0
        player.bullet_damage += 2.0
    elif uid == "max_health":
        player.max_health += 18
        player.health = min(player.max_health, player.health + 18)
    elif uid == "magnet":
        player.magnet_radius += 45
    elif uid == "repair":
        player.health = min(player.max_health, player.health + player.max_health * 0.24)
        player.invuln = max(player.invuln, 0.55)
        player.overclock_timer = max(player.overclock_timer, 3.0)
    elif uid == "explosive_shot":
        player.explosion_radius += 16
    elif uid == "side_cannon":
        player.side_cannon_level += 1
        player.side_cannon_rate = max(0.34, player.side_cannon_rate * 0.84)
    elif uid == "split_shot":
        player.split_level += 1
    elif uid == "shield_drone":
        player.shield_drone_level += 1
    elif uid == "lightning_chain":
        player.lightning_level += 1
        player.lightning_every = max(3, player.lightning_every - 1)
    elif uid == "bullet_speed":
        player.bullet_speed *= 1.18
        player.bullet_range *= 1.12
    elif uid == "xp_gain":
        player.run_xp_bonus *= 1.12
    elif uid == "coin_gain":
        player.run_coin_bonus *= 1.2
    elif uid == "crit_chance":
        player.crit_chance += 0.07
    elif uid == "ricochet":
        player.ricochet += 1
    elif uid == "freeze_shot":
        player.slow_chance += 0.12
        player.slow_duration += 0.45
    elif uid == "frostbite_rounds":
        player.frostbite_level += 1
    elif uid == "shatter_freeze":
        player.shatter_freeze_level += 1
    elif uid == "ice_barrier":
        player.ice_barrier_level += 1
    elif uid == "poison_shot":
        player.poison_dps += 5.0
        player.poison_duration = max(player.poison_duration, 3.0)
    elif uid == "plague_burst":
        player.plague_burst_level += 1
    elif uid == "acid_pool":
        player.acid_pool_level += 1
    elif uid == "venom_engine":
        player.venom_engine_level += 1
        player.poison_dps += 2.5
        player.poison_duration = max(player.poison_duration + 0.4, 3.3)
    elif uid == "emergency_shield":
        player.emergency_shield_level += 1
    elif uid == "magnet_pulse":
        player.magnet_pulse_level += 1
        player.magnet_pulse_timer = 1.0
    elif uid == "overclock":
        player.overclock_level += 1
        player.overclock_timer = 7.0
    elif uid == "hollow_point":
        player.bullet_damage *= 1.22
        player.fire_rate *= 0.93
    elif uid == "nanobot_repair":
        player.regen_per_second += 0.75
    elif uid == "mine_layer":
        player.mine_layer_level += 1
    elif uid == "targeting_ai":
        player.turret_damage_mult *= 1.18
        player.turret_range_bonus += 45
    elif uid == "dash_cooldown":
        player.dash_cooldown_duration = max(0.72, player.dash_cooldown_duration * 0.82)
    elif uid == "armor":
        player.armor = min(0.38, player.armor + 0.06)
    elif uid == "lucky_drop":
        player.luck += 0.08
    elif uid == "overpressure_ammo":
        player.overpressure_level += 1
    elif uid == "serrated_rounds":
        player.serrated_bonus += 0.24
    elif uid == "volatile_payload":
        player.volatile_chance += 0.1
    elif uid == "burn_oil":
        player.burn_chance += 0.1
        player.burn_dps += 5.0
    elif uid == "wildfire_rounds":
        player.wildfire_level += 1
    elif uid == "molten_payload":
        player.molten_payload_level += 1
        player.explosion_radius += 6
    elif uid == "ash_collector":
        player.ash_collector_level += 1
        player.luck += 0.03
    elif uid == "corrosion_rounds":
        player.corrosion_level += 1
    elif uid == "kinetic_barrier":
        player.kinetic_barrier_level += 1
    elif uid == "last_stand":
        player.last_stand_level += 1
    elif uid == "bloodless_harvest":
        player.bloodless_harvest = True
    elif uid == "salvage_converter":
        player.salvage_pct += 0.1
    elif uid == "coolant_loop":
        player.ability_cooldown_reduction += 0.12
    elif uid == "mana_battery":
        player.ability_power_mult *= 1.15
    elif uid == "cursor_minefield":
        player.cursor_minefield_level += 1
    elif uid == "firestorm_catalyst":
        player.firestorm_catalyst_level += 1
    elif uid == "drone_swarm":
        player.drone_swarm_level += 1
    elif uid == "repair_drone":
        player.repair_drone_level += 1
    elif uid == "arc_rounds":
        player.arc_rounds_level += 1
    elif uid == "capacitor_link":
        player.capacitor_link_level += 1
        player.turret_damage_mult *= 1.04
    elif uid == "storm_battery":
        player.storm_battery_level += 1
        player.lightning_every = max(3, player.lightning_every - 1)
    elif uid == "conductive_wildfire":
        player.conductive_wildfire_level += 1
    elif uid == "toxic_frostbite":
        player.toxic_frostbite_level += 1
    elif uid == "storm_shatter":
        player.storm_shatter_level += 1
    elif uid == "salvage_momentum":
        player.salvage_momentum_level += 1
    elif uid == "blueprint_echo":
        player.blueprint_echo_level += 1
    elif uid == "relay_overcharge":
        player.relay_overcharge_level += 1
    elif uid == "split_fireball":
        player.split_fireball_level += 1
    elif uid == "chilling_ring":
        player.chilling_ring_level += 1
    elif uid == "corrosive_burst":
        player.corrosive_burst_level += 1
    elif uid == "arc_echo":
        player.arc_echo_level += 1

    evolution_messages = check_evolutions(player)
    check_family_passives(player)
    return evolution_messages


def check_evolutions(player: object) -> list[str]:
    counts = player.upgrade_counts
    unlocked: list[str] = []
    family_unlocks: list[FamilyEvolution] = []

    family_counts = get_family_counts(player)
    for family, evolution in FAMILY_EVOLUTIONS.items():
        if family_counts.get(family, 0) >= evolution.threshold and evolution.id not in player.evolutions:
            player.evolutions.add(evolution.id)
            _apply_family_evolution_bonus(player, evolution)
            family_unlocks.append(evolution)
            unlocked.append(f"{family.upper()} EVOLUTION UNLOCKED: {evolution.name.upper()}")

    if _level(counts, "minigun_core") and "minigun_mode" not in player.evolutions:
        player.evolutions.add("minigun_mode")
        player.fire_rate *= 1.35
        player.bullet_damage *= 0.88
        player.bullet_speed *= 1.08
        unlocked.append("MINIGUN CORE ONLINE")

    if _level(counts, "railgun_core") and "railgun_core" not in player.evolutions:
        player.evolutions.add("railgun_core")
        player.fire_rate *= 0.48
        player.bullet_damage *= 2.65
        player.bullet_pierce += 4
        player.bullet_speed *= 1.3
        unlocked.append("RAILGUN CORE ENGAGED")

    if _level(counts, "scrapstorm_detonator") and "scrapstorm_detonator" not in player.evolutions:
        player.evolutions.add("scrapstorm_detonator")
        player.explosion_radius += 42
        player.bullet_size += 3
        player.bullet_damage += 6
        player.scrapstorm_fragment_level += 1
        unlocked.append("SCRAPSTORM DETONATOR ARMED")

    if _level(counts, "fortress_core") and "fortress_core" not in player.evolutions:
        player.evolutions.add("fortress_core")
        player.max_health += 80
        player.health = min(player.max_health, player.health + 80)
        player.armor = min(0.55, player.armor + 0.15)
        player.speed *= 0.82
        player.regen_per_second += 1.5
        unlocked.append("FORTRESS CORE ACTIVATED")

    if _level(counts, "drone_network") and "drone_network" not in player.evolutions:
        player.evolutions.add("drone_network")
        player.shield_drone_level += 2
        player.turret_damage_mult *= 1.4
        player.turret_range_bonus += 80
        unlocked.append("DRONE NETWORK ONLINE")

    if _level(counts, "hyperdrive_core") and "hyperdrive_core" not in player.evolutions:
        player.evolutions.add("hyperdrive_core")
        player.speed *= 1.2
        player.magnet_radius += 130
        player.magnet_pulse_level += 2
        player.hyperdrive_level += 1
        unlocked.append("HYPERDRIVE CORE ENGAGED")

    setattr(player, "last_evolution_unlocks", family_unlocks)
    return unlocked


def _apply_family_evolution_bonus(player: object, evolution: FamilyEvolution) -> None:
    if evolution.id == "inferno_core":
        player.burn_chance += 0.04
        stabilized = 1.2 if getattr(player, "evolution_stabilizer_active", False) else 0.9
        player.fire_duration_bonus = max(getattr(player, "fire_duration_bonus", 0.0), stabilized)
    elif evolution.id == "plague_network":
        player.poison_dps += 2.5
        stabilized = 1.35 if getattr(player, "evolution_stabilizer_active", False) else 1.05
        player.poison_duration_bonus = max(getattr(player, "poison_duration_bonus", 0.0), stabilized)
    elif evolution.id == "absolute_zero":
        player.slow_chance += 0.05
        player.slow_duration += 0.25
        stabilized = 0.95 if getattr(player, "evolution_stabilizer_active", False) else 0.7
        player.cryo_duration_bonus = max(getattr(player, "cryo_duration_bonus", 0.0), stabilized)
    elif evolution.id == "storm_grid":
        stabilized = 315.0 if getattr(player, "evolution_stabilizer_active", False) else 285.0
        player.lightning_chain_range = max(getattr(player, "lightning_chain_range", 175.0), stabilized)
        player.lightning_every = max(3, player.lightning_every - 1)


def stack_text(player: object, upgrade: Upgrade) -> str:
    current = _level(player.upgrade_counts, upgrade.id)
    if upgrade.max_stack is None:
        return f"Stack {current}"
    return f"Stack {current}/{upgrade.max_stack}"


def evolution_names(evolutions: Iterable[str]) -> str:
    names = {
        "minigun_mode": "Minigun",
        "railgun_core": "Railgun",
        "scrapstorm_detonator": "Scrapstorm",
        "fortress_core": "Fortress",
        "drone_network": "Drone Net",
        "hyperdrive_core": "Hyperdrive",
    }
    active = [names[evo] for evo in evolutions if evo in names]
    return " + ".join(active) if active else "Scrap Cannon"


def get_active_branches(player: object) -> dict[str, int]:
    branches: dict[str, int] = {}
    for upgrade in UPGRADES:
        level = _level(player.upgrade_counts, upgrade.id)
        if level > 0 and upgrade.branch != "general":
            branches[upgrade.branch] = branches.get(upgrade.branch, 0) + level
    return branches


def branch_label(branch: str) -> str:
    return BRANCH_LABELS.get(branch, branch.replace("_", " ").title())


def tier_text(upgrade: Upgrade) -> str:
    if upgrade.rarity == "evolution" or upgrade.tier >= 4:
        return "Evolution"
    return {1: "Tier I", 2: "Tier II", 3: "Tier III"}.get(upgrade.tier, f"Tier {upgrade.tier}")


def rarity_label(upgrade: Upgrade) -> str:
    return RARITY_LABELS.get(upgrade.rarity, upgrade.rarity.title())


def prerequisite_text(upgrade: Upgrade) -> str:
    parts = [_format_requirement(req_id, req_level) for req_id, req_level in upgrade.prerequisites]
    if upgrade.any_prerequisites:
        options = " or ".join(_format_requirement(req_id, req_level) for req_id, req_level in upgrade.any_prerequisites)
        parts.append(options)
    return ", ".join(parts) if parts else "Starter path"


def synergy_text(upgrade: Upgrade) -> str:
    useful = [tag.replace("_", " ").title() for tag in upgrade.tags if tag != "evolution"]
    return ", ".join(useful[:3]) if useful else "Flexible"


def _format_requirement(req_id: str, req_level: int) -> str:
    name = UPGRADE_BY_ID.get(req_id).name if req_id in UPGRADE_BY_ID else req_id.replace("_", " ").title()
    return f"{name} {roman(req_level)}"


def roman(value: int) -> str:
    return {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V"}.get(value, str(value))
