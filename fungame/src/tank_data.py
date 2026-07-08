from __future__ import annotations

from dataclasses import dataclass
import pygame


@dataclass(frozen=True)
class TankDefinition:
    id: str
    name: str
    cost: int
    sprite_key: str
    icon_key: str
    description: str
    strengths: str
    aim_angle_offset: float = 90.0


TANKS: tuple[TankDefinition, ...] = (
    TankDefinition(
        "starter",
        "Starter Tank",
        0,
        "player",
        "tank_icon_starter",
        "Balanced scrap tank with steady fire and reliable handling.",
        "Versatile, beginner-friendly, strong upgrade scaling.",
    ),
    TankDefinition(
        "sniper",
        "Sniper Tank",
        80,
        "player_sniper",
        "tank_icon_sniper",
        "Long-range glass cannon with slow, piercing precision shots.",
        "High damage, long range, default pierce.",
    ),
    TankDefinition(
        "engineer",
        "Engineer Tank",
        110,
        "player_engineer",
        "tank_icon_engineer",
        "Utility tank that deploys temporary mini turrets for map control.",
        "Support fire, turret pressure, lower direct burst.",
    ),
    TankDefinition(
        "twin_shot",
        "Twin-Shot Tank",
        150,
        "player_twin",
        "tank_icon_twin",
        "Fires dual streams of scrap bullets. High default multi-shot, slightly slower firing.",
        "Double fire, wide spread, strong Tech potential.",
    ),
    TankDefinition(
        "flame_caster",
        "Flame Caster Tank",
        200,
        "player_flame",
        "tank_icon_flame",
        "Burns down close-range Scrap waves with short-range explosive fireballs.",
        "Burn damage, high AoE pressure, defense-friendly.",
        90.0,
    ),
    TankDefinition(
        "cryo",
        "Frostline Tank",
        240,
        "player_cryo",
        "tank_icon_cryo",
        "Control tank with chill rounds and a cursor-targeted Frost Nova.",
        "Slows threats, creates openings, strong Cryo upgrade access.",
        90.0,
    ),
    TankDefinition(
        "poison",
        "Venom Rig",
        260,
        "player_poison",
        "tank_icon_poison",
        "Damage-over-time rig that saturates targets and pools the arena with acid.",
        "Sustained boss damage, toxin spread, Economy upgrade access.",
        90.0,
    ),
    TankDefinition(
        "lightning",
        "Storm Capacitor",
        280,
        "player_lightning",
        "tank_icon_lightning",
        "Fast capacitor tank that stores charge and bursts through clustered enemies.",
        "Chain damage, mobility, Ability and Summon upgrade access.",
        90.0,
    ),
)

TANK_BY_ID = {tank.id: tank for tank in TANKS}


def configure_player_tank(player: object, tank_id: str) -> None:
    player.active_skills = []
    if tank_id == "sniper":
        player.tank_id = "sniper"
        player.tank_name = "Sniper Tank"
        player.max_health = 82
        player.health = player.max_health
        player.speed = 205
        player.fire_rate = 1.12
        player.bullet_damage = 52
        player.bullet_speed = 920
        player.bullet_size = 4
        player.bullet_pierce = 1
        player.bullet_range = 1320
        player.magnet_radius = 108
        player.active_skills.append({
            "name": "Piercing Laser",
            "cooldown": 0.0,
            "max_cooldown": 7.0,
            "key": pygame.K_q,
            "cast_fn_name": "cast_piercing_laser"
        })
    elif tank_id == "engineer":
        player.tank_id = "engineer"
        player.tank_name = "Engineer Tank"
        player.max_health = 96
        player.health = player.max_health
        player.speed = 214
        player.fire_rate = 2.35
        player.bullet_damage = 13
        player.bullet_speed = 610
        player.bullet_size = 5
        player.bullet_range = 720
        player.engineer_turret_cap = 3
        player.engineer_deploy_interval = 3.8
        player.engineer_turret_cooldown = 0.55
        player.active_skills.append({
            "name": "Deploy Sentry",
            "cooldown": 0.0,
            "max_cooldown": 8.0,
            "key": pygame.K_q,
            "cast_fn_name": "cast_deploy_sentry"
        })
    elif tank_id == "twin_shot":
        player.tank_id = "twin_shot"
        player.tank_name = "Twin-Shot Tank"
        player.max_health = 110
        player.health = player.max_health
        player.speed = 205
        player.fire_rate = 2.4
        player.bullet_damage = 14
        player.bullet_speed = 580
        player.bullet_size = 5
        player.bullet_range = 720
        player.multi_shot = 2
        player.active_skills.append({
            "name": "Bullet Fan",
            "cooldown": 0.0,
            "max_cooldown": 6.0,
            "key": pygame.K_q,
            "cast_fn_name": "cast_bullet_fan"
        })
    elif tank_id == "flame_caster":
        player.tank_id = "flame_caster"
        player.tank_name = "Flame Caster Tank"
        player.max_health = 100
        player.health = player.max_health
        player.speed = 200
        player.fire_rate = 1.8
        player.bullet_damage = 22
        player.bullet_speed = 520
        player.bullet_size = 7
        player.bullet_range = 680
        player.explosion_radius = 24
        player.burn_chance = 0.45
        player.burn_dps = 8.0
        player.fire_duration_bonus = 0.9
        player.active_skills.append({
            "name": "Fireball",
            "cooldown": 0.0,
            "max_cooldown": 5.0,
            "key": pygame.K_q,
            "cast_fn_name": "cast_fireball"
        })
    elif tank_id == "cryo":
        player.tank_id = "cryo"
        player.tank_name = "Frostline Tank"
        player.max_health = 104
        player.health = player.max_health
        player.speed = 208
        player.fire_rate = 2.15
        player.bullet_damage = 17
        player.bullet_speed = 640
        player.bullet_size = 5
        player.bullet_range = 760
        player.slow_chance = 0.28
        player.slow_duration = 1.15
        player.cryo_duration_bonus = 0.3
        player.active_skills.append({
            "name": "Frost Nova",
            "cooldown": 0.0,
            "max_cooldown": 7.0,
            "cast_fn_name": "cast_frost_nova"
        })
    elif tank_id == "poison":
        player.tank_id = "poison"
        player.tank_name = "Venom Rig"
        player.max_health = 108
        player.health = player.max_health
        player.speed = 202
        player.fire_rate = 1.95
        player.bullet_damage = 18
        player.bullet_speed = 575
        player.bullet_size = 6
        player.bullet_range = 735
        player.poison_dps = 8.5
        player.poison_duration = 3.6
        player.poison_duration_bonus = 0.65
        player.active_skills.append({
            "name": "Acid Glob",
            "cooldown": 0.0,
            "max_cooldown": 6.5,
            "cast_fn_name": "cast_acid_glob"
        })
    elif tank_id == "lightning":
        player.tank_id = "lightning"
        player.tank_name = "Storm Capacitor"
        player.max_health = 88
        player.health = player.max_health
        player.speed = 238
        player.fire_rate = 2.45
        player.bullet_damage = 15
        player.bullet_speed = 720
        player.bullet_size = 4.5
        player.bullet_range = 790
        player.lightning_level = 1
        player.lightning_every = 4
        player.lightning_chain_range = 205
        player.active_skills.append({
            "name": "Arc Surge",
            "cooldown": 0.0,
            "max_cooldown": 6.0,
            "cast_fn_name": "cast_arc_surge"
        })
    else:
        player.tank_id = "starter"
        player.tank_name = "Starter Tank"
        player.active_skills.append({
            "name": "Burst Barrage",
            "cooldown": 0.0,
            "max_cooldown": 5.0,
            "key": pygame.K_q,
            "cast_fn_name": "cast_burst_barrage"
        })
