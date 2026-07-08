from __future__ import annotations

import os
import sys
import tempfile
import math
from collections import defaultdict
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pygame

from src.achievements import ACHIEVEMENTS, achievement_bonuses, evaluate_achievements
from src.assets import SpriteBank
from src.constants import FPS, MAX_DAMAGE_NUMBERS, MAX_PARTICLES, MAX_PICKUPS
from src.enemy import ENEMY_TYPES, create_enemy
from src.equipment import EQUIPMENT_TEMPLATES
from src.game import COIN_PICKUP_CAP, HEALTH_PICKUP_CAP, LOOT_UNLOCK_SECONDS, SHAKE_CAPS, XP_PICKUP_CAP, Game
from src.game_state import ScreenState
from src.pickup import Pickup
from src.player import Player
from src.projectile import Projectile
from src.save_manager import SaveManager, normalize_save
from src.skill_tree import SKILL_BY_ID, available_skill_points, node_status, unlock_skill_node
from src.stages import STAGE_BY_ID, STAGES
from src.summon import MiniTurret
from src.tank_data import configure_player_tank
from src.meta_upgrades import apply_meta_upgrades
from src.progression import RESEARCH_BY_ID, RESEARCH_CATEGORIES, UNLOCKS, RunContract, apply_research_modifiers, evaluate_unlocks, purchase_research
from src.upgrades import (
    UPGRADES,
    UPGRADE_BY_ID,
    apply_upgrade,
    available_upgrades,
    choose_upgrades,
    family_progress_text,
    get_active_evolutions,
    get_active_passives,
    get_family_counts,
)


def temp_save(name: str) -> Path:
    path = Path(tempfile.gettempdir()) / f"scrapstorm_qa_{name}_{os.getpid()}.json"
    try:
        path.unlink()
    except FileNotFoundError:
        pass
    os.environ["NEON_SCRAP_SAVE"] = str(path)
    return path


def new_game(name: str, *, debug_unlock_loot: bool = False) -> Game:
    temp_save(name)
    screen = pygame.display.get_surface()
    assert screen is not None
    return Game(screen, smoke=True, debug_unlock_loot=debug_unlock_loot)


def test_fresh_save_creation() -> None:
    path = temp_save("fresh")
    data = SaveManager(path).load()
    assert data["coins"] == 0
    assert data["selected_tank"] == "starter"
    assert data["unlocked_tanks"] == ["starter"]
    assert data["loot_unlocked"] is False


def test_save_migration() -> None:
    migrated = normalize_save(
        {
            "coins": -100,
            "selected_tank": "not_a_tank",
            "unlocked_tanks": ["starter", "sniper", "not_a_tank"],
            "achievements": ["survive_5", "not_real"],
            "stats": {"best_time": 601, "total_kills": 5.8},
            "gear_inventory": [
                {
                    "id": "gear1",
                    "name": "Old Rail",
                    "type": "weapon",
                    "rarity": "Unique",
                    "stats": {"Strength": 3, "Nope": 9},
                    "effect": "bullets_explode",
                }
            ],
            "equipped_gear": {"weapon": "gear1", "armor": "missing", "trinket": None},
        }
    )
    assert migrated["coins"] == 0
    assert migrated["selected_tank"] == "starter"
    assert migrated["unlocked_tanks"] == ["sniper", "starter"]
    assert migrated["loot_unlocked"] is True
    assert migrated["achievements"] == ["survive_5"]
    assert migrated["equipped_gear"]["weapon"] == "gear1"
    assert migrated["equipped_gear"]["armor"] is None


def test_achievement_unlock_once() -> None:
    data = normalize_save({"stats": {"total_chests_opened": 1}})
    unlocked = evaluate_achievements(data)
    assert [achievement.id for achievement in unlocked] == ["first_chest"]
    assert evaluate_achievements(data) == []
    bonuses = achievement_bonuses(data)
    assert bonuses["luck"] > 0
    assert len(ACHIEVEMENTS) == 41


def test_five_minute_loot_unlock() -> None:
    game = new_game("unlock")
    game.start_run()
    game.stats.time_survived = LOOT_UNLOCK_SECONDS - 0.1
    game.update(0.2)
    assert game.save_data["loot_unlocked"] is True
    assert game.is_meta_loot_unlocked() is True


def test_upgrade_tree_rules() -> None:
    game = new_game("upgrade_tree")
    player = game.player
    start_ids = {upgrade.id for upgrade in available_upgrades(player)}
    assert "split_shot" not in start_ids
    assert "minigun_core" not in start_ids

    player.upgrade_counts["pierce"] = 1
    assert "split_shot" in {upgrade.id for upgrade in available_upgrades(player)}

    player.upgrade_counts.clear()
    player.upgrade_counts.update({"rapid_fire": 4, "multi_shot": 2})
    assert "minigun_core" in {upgrade.id for upgrade in available_upgrades(player)}

    player.upgrade_counts = defaultdict(int)
    for upgrade in UPGRADES:
        for req_id, req_level in upgrade.prerequisites + upgrade.any_prerequisites:
            player.upgrade_counts[req_id] = max(player.upgrade_counts[req_id], req_level)
        apply_upgrade(player, upgrade)
    assert player.evolutions >= {
        "minigun_mode",
        "railgun_core",
        "scrapstorm_detonator",
        "drone_network",
        "fortress_core",
        "hyperdrive_core",
    }
    for tank_id in ("starter", "sniper", "engineer", "twin_shot", "flame_caster"):
        assert len(choose_upgrades(player, tank_id=tank_id)) <= 3


def test_family_passive_unlocks() -> None:
    game = new_game("family_passives")
    player = game.player

    apply_upgrade(player, UPGRADE_BY_ID["rapid_fire"])
    assert "Projectile:2" not in player.family_passives_unlocked
    apply_upgrade(player, UPGRADE_BY_ID["bullet_speed"])
    assert "Projectile:2" in player.family_passives_unlocked
    assert get_family_counts(player)["Projectile"] == 2
    assert any(passive.name == "Ballistic Momentum" for passive in get_active_passives(player))

    progress = family_progress_text(player, UPGRADE_BY_ID["bullet_damage"])
    assert "Projectile: 2/4" in progress

    player.upgrade_counts.clear()
    player.family_passives_unlocked.clear()
    game.level_choices = [UPGRADE_BY_ID["burn_oil"], UPGRADE_BY_ID["wildfire_rounds"]]
    player.upgrade_counts["burn_oil"] = 1
    game.select_upgrade(1)
    assert "Fire:2" in player.family_passives_unlocked
    assert game.passive_popups


def test_family_evolution_unlocks() -> None:
    game = new_game("family_evolutions")
    player = game.player
    unlock_cases = (
        ("burn_oil", "inferno_core", "Inferno Core"),
        ("poison_shot", "plague_network", "Plague Network"),
        ("freeze_shot", "absolute_zero", "Absolute Zero"),
        ("lightning_chain", "storm_grid", "Storm Grid"),
    )

    for upgrade_id, evolution_id, evolution_name in unlock_cases:
        player.upgrade_counts.clear()
        player.family_passives_unlocked.clear()
        player.evolutions.clear()
        player.last_evolution_unlocks.clear()
        for _ in range(10):
            apply_upgrade(player, UPGRADE_BY_ID[upgrade_id])
        assert evolution_id in player.evolutions
        assert any(evolution.name == evolution_name for evolution in get_active_evolutions(player))
        assert player.last_evolution_unlocks[-1].name == evolution_name

    progress = family_progress_text(player, UPGRADE_BY_ID["lightning_chain"])
    assert "Lightning: Evolution active" in progress


def test_poison_stacks_corrosion_and_conductive_arcs() -> None:
    game = new_game("poison_identity")
    poisoned = create_enemy("crawler", pygame.Vector2(120, 120))
    for _ in range(4):
        poisoned.apply_poison(10.0, 3.6, "Poison")
    assert poisoned.poison_stacks == 3
    assert poisoned.corrosion_bonus >= 0.08
    before = poisoned.health
    poisoned.update(0.5, game.player.pos, game)
    assert poisoned.health < before - 15.0

    first = create_enemy("crawler", pygame.Vector2(240, 120))
    target = create_enemy("crawler", pygame.Vector2(470, 120))
    first.apply_poison(8.0, 3.6, "Poison")
    game.enemies = [first, target]
    target_before = target.health
    game._chain_lightning(first, 1, 10.0)
    assert target.health < target_before


def test_level_up_recovery_and_healing_upgrades() -> None:
    game = new_game("level_recovery")
    game.start_run()
    player = game.player
    player.health = 1.0
    player.xp = player.xp_to_next
    expected = min(player.max_health, player.health + player.level_up_heal_amount())
    game._open_level_up()
    assert player.health == expected
    assert any("HP" in message for message, _, _ in game.messages)
    assert any(number.text.endswith("HP") for number in game.damage_numbers)

    player.bloodless_harvest = True
    player.health = player.max_health
    player.kinetic_barrier_shield = 0.0
    game._collect_pickup(Pickup("health", player.pos.copy(), 18))
    assert player.kinetic_barrier_shield > 0
    player.kinetic_barrier_shield = 22.0
    coins_before = game.stats.run_coins
    game._collect_pickup(Pickup("health", player.pos.copy(), 18))
    assert game.stats.run_coins > coins_before


def test_evolution_art_integration() -> None:
    bank = SpriteBank()
    for family in ("projectile", "fire", "poison", "cryo", "lightning"):
        sprite = bank.sprites[f"evolution_{family}"]
        icon = bank.icons[f"evolution_{family}"]
        assert sprite.get_size() == (96, 96)
        assert icon.get_size() == (64, 64)
        assert sprite.get_at((0, 0)).a == 0

    player = Player(pygame.Vector2(0, 0))
    configure_player_tank(player, "poison")
    player.evolutions.add("plague_network")
    assert player.sprite_key == "evolution_poison"


def test_elemental_passive_effect_hooks() -> None:
    game = new_game("elemental_hooks")
    game.random_chance = lambda chance: True

    fire_source = create_enemy("crawler", pygame.Vector2(120, 120))
    fire_target = create_enemy("crawler", pygame.Vector2(170, 120))
    fire_source.health = 0
    fire_source.dot_family = "Fire"
    game.enemies = [fire_source, fire_target]
    game.player.wildfire_level = 1
    game._handle_elemental_death(fire_source)
    assert fire_target.dot_family == "Fire"
    assert fire_target.poison_timer > 0

    poison_source = create_enemy("crawler", pygame.Vector2(240, 120))
    poison_target = create_enemy("crawler", pygame.Vector2(285, 120))
    poison_source.health = 0
    poison_source.dot_family = "Poison"
    game.enemies = [poison_source, poison_target]
    game.player.plague_burst_level = 1
    game.player.poison_dps = 6
    game._handle_elemental_death(poison_source)
    assert poison_target.dot_family == "Poison"
    assert poison_target.poison_timer > 0

    cryo_source = create_enemy("crawler", pygame.Vector2(360, 120))
    cryo_target = create_enemy("crawler", pygame.Vector2(388, 120))
    cryo_source.health = 0
    cryo_source.slow_timer = 1.0
    game.enemies = [cryo_source, cryo_target]
    game.player.shatter_freeze_level = 1
    before = cryo_target.health
    game._handle_elemental_death(cryo_source)
    assert cryo_target.health < before

    chain_source = create_enemy("crawler", pygame.Vector2(460, 120))
    chain_target = create_enemy("crawler", pygame.Vector2(620, 120))
    game.enemies = [chain_source, chain_target]
    before = chain_target.health
    game._chain_lightning(chain_source, 1, 9)
    assert chain_target.health < before

    fire_source = create_enemy("crawler", pygame.Vector2(120, 260))
    fire_target = create_enemy("crawler", pygame.Vector2(150, 260))
    fire_source.health = 0
    fire_source.dot_family = "Fire"
    game.enemies = [fire_source, fire_target]
    game.player.evolutions.add("inferno_core")
    game.player.burn_dps = 8
    before = fire_target.health
    game._handle_elemental_death(fire_source)
    assert fire_target.health < before
    assert fire_target.dot_family == "Fire"

    poison_source = create_enemy("crawler", pygame.Vector2(240, 260))
    poison_target = create_enemy("crawler", pygame.Vector2(290, 260))
    poison_source.health = 0
    poison_source.dot_family = "Poison"
    game.enemies = [poison_source, poison_target]
    game.player.evolutions.add("plague_network")
    game.player.poison_dps = 7
    game.player.plague_network_cooldown = 0
    game._handle_elemental_death(poison_source)
    assert poison_target.dot_family == "Poison"
    assert poison_target.poison_timer > 0

    cryo_source = create_enemy("crawler", pygame.Vector2(360, 260))
    cryo_target = create_enemy("crawler", pygame.Vector2(395, 260))
    cryo_source.health = 0
    cryo_source.slow_timer = 1.0
    game.enemies = [cryo_source, cryo_target]
    game.player.evolutions.add("absolute_zero")
    game.player.absolute_zero_cooldown = 0
    before = cryo_target.health
    game._handle_elemental_death(cryo_source)
    assert cryo_target.health < before

    storm_source = create_enemy("crawler", pygame.Vector2(460, 260))
    storm_target_1 = create_enemy("crawler", pygame.Vector2(620, 260))
    storm_target_2 = create_enemy("crawler", pygame.Vector2(760, 260))
    game.enemies = [storm_source, storm_target_1, storm_target_2]
    game.player.evolutions.add("storm_grid")
    before = storm_target_2.health
    game._chain_lightning(storm_source, 1, 9)
    assert storm_target_2.health < before


def test_enemy_boss_variety_assets_and_spawns() -> None:
    game = new_game("enemy_variety")
    sprite_keys = {
        "enemy_dash_scrapper",
        "enemy_medium_bruiser",
        "enemy_shield_carrier",
        "enemy_mine_layer",
        "enemy_drone_swarm_unit",
        "enemy_artillery_buggy",
        "enemy_repair_node",
        "enemy_fire_mote",
        "enemy_cryo_crawler",
        "enemy_poison_spitter",
        "enemy_lightning_node",
        "boss_rift_charger",
        "boss_furnace_king",
        "boss_glacier_engine",
        "boss_toxic_maw",
        "boss_storm_capacitor",
        "boss_scrap_hive_core",
        "enemy_projectile_artillery_shell",
        "enemy_projectile_poison_glob",
        "enemy_projectile_lightning_arc",
        "effect_frost_zone",
        "effect_mine_hazard",
    }
    missing = sprite_keys.difference(game.assets.sprites)
    assert not missing

    enemy_kinds = {
        "dash_scrapper",
        "medium_bruiser",
        "shield_carrier",
        "mine_layer",
        "drone_swarm",
        "artillery_buggy",
        "repair_node",
        "fire_mote",
        "cryo_crawler",
        "poison_spitter",
        "lightning_node",
        "boss_rift_charger",
        "boss_furnace_king",
        "boss_glacier_engine",
        "boss_toxic_maw",
        "boss_storm_capacitor",
        "boss_scrap_hive_core",
    }
    for kind in enemy_kinds:
        enemy = create_enemy(kind, pygame.Vector2(100, 100))
        assert kind in ENEMY_TYPES
        assert enemy.sprite_key in game.assets.sprites
        assert enemy.radius > 0


def test_screen_shake_policy() -> None:
    game = new_game("shake")
    game.add_screen_shake(99, source_type="normal_hit")
    assert game.shake == 0
    game.add_screen_shake(99, source_type="pickup")
    assert game.shake == 0
    game.add_screen_shake(99, source_type="player_hit")
    assert 0 < game.shake <= SHAKE_CAPS["player_hit"]


def test_pickup_caps_and_merge() -> None:
    game = new_game("pickup_caps")
    game.start_run()
    for i in range(XP_PICKUP_CAP + 24):
        game._add_pickup(Pickup("xp", pygame.Vector2(120 + i * 45, 120), 1))
    for i in range(COIN_PICKUP_CAP + 24):
        game._add_pickup(Pickup("coin", pygame.Vector2(120 + i * 45, 240), 1))
    for i in range(HEALTH_PICKUP_CAP + 24):
        game._add_pickup(Pickup("health", pygame.Vector2(120 + i * 45, 360), 10))

    game._enforce_pickup_caps()
    assert sum(1 for pickup in game.pickups if pickup.kind == "xp") <= XP_PICKUP_CAP
    assert sum(1 for pickup in game.pickups if pickup.kind == "coin") <= COIN_PICKUP_CAP
    assert sum(1 for pickup in game.pickups if pickup.kind == "health") <= HEALTH_PICKUP_CAP
    assert len(game.pickups) <= MAX_PICKUPS


def test_ninety_second_performance_window_caps() -> None:
    game = new_game("perf_window")
    game.start_run()
    game.player.max_health = 99999
    game.player.health = game.player.max_health
    max_counts = {
        "particles": 0,
        "damage_numbers": 0,
        "pickups": 0,
    }

    for _ in range(90 * FPS):
        if game.state == ScreenState.LEVEL_UP and game.level_choices:
            game.select_upgrade(0)
        if game.state != ScreenState.PLAYING:
            game.state = ScreenState.PLAYING
        game.player.health = game.player.max_health
        game.update(1 / FPS)
        max_counts["particles"] = max(max_counts["particles"], len(game.particles))
        max_counts["damage_numbers"] = max(max_counts["damage_numbers"], len(game.damage_numbers))
        max_counts["pickups"] = max(max_counts["pickups"], len(game.pickups))

    assert game.stats.time_survived >= 89.0
    assert max_counts["particles"] <= MAX_PARTICLES
    assert max_counts["damage_numbers"] <= MAX_DAMAGE_NUMBERS
    assert max_counts["pickups"] <= MAX_PICKUPS


def test_chest_reward_generation() -> None:
    game = new_game("chest_locked")
    game.start_run()
    game._open_loot_chest(quality=3)
    assert game.stats.chests_opened == 1
    assert game.stats.run_coins > 0
    assert game.save_data["gear_inventory"] == []

    game = new_game("chest_unlocked")
    game.save_data["loot_unlocked"] = True
    game.run_loot_unlocked = True
    import src.game as game_module

    old_random = game_module.random.random
    try:
        game_module.random.random = lambda: 0.0
        game._open_loot_chest(quality=3)
    finally:
        game_module.random.random = old_random
    assert game.stats.gear_found == 1
    assert len(game.save_data["gear_inventory"]) == 1


def test_equipping_unique_gear() -> None:
    item = {
        "id": "unique1",
        "name": "Blastcore Array",
        "type": "weapon",
        "rarity": "Unique",
        "stats": {"Strength": 2},
        "effect": "bullets_explode",
    }
    save_data = normalize_save({"gear_inventory": [item], "equipped_gear": {"weapon": "unique1"}})
    player = Player(pygame.Vector2(0, 0))
    configure_player_tank(player, "starter")
    apply_meta_upgrades(player, save_data)
    assert "bullets_explode" in player.equipped_effects
    assert player.Strength == 2


def equip_unique(game: Game, effect: str, tank_id: str = "starter", slot: str = "weapon") -> None:
    item = {
        "id": f"{effect}_id",
        "name": effect,
        "type": slot,
        "rarity": "Unique",
        "stats": {},
        "effect": effect,
    }
    game.save_data["selected_tank"] = tank_id
    game.save_data["unlocked_tanks"] = sorted(set(game.save_data.get("unlocked_tanks", ["starter"]) + [tank_id]))
    game.save_data["gear_inventory"] = [item]
    game.save_data["equipped_gear"] = {"weapon": None, "armor": None, "trinket": None}
    game.save_data["equipped_gear"][slot] = item["id"]
    configure_player_tank(game.player, tank_id)
    apply_meta_upgrades(game.player, game.save_data)
    assert effect in game.player.equipped_effects


def test_unique_effect_hooks() -> None:
    direction = pygame.Vector2(1, 0)

    game = new_game("unique_explode")
    equip_unique(game, "bullets_explode")
    game.player.shot_counter = 5
    assert game.player._make_projectile(direction, game).explosion_radius >= 54

    game = new_game("unique_freeze")
    equip_unique(game, "sniper_freeze", tank_id="sniper")
    sniper_projectile = game.player._make_projectile(direction, game)
    assert sniper_projectile.slow_chance > 0
    assert sniper_projectile.slow_duration > 0

    game = new_game("unique_tesla")
    equip_unique(game, "turret_lightning", tank_id="engineer")
    game.enemies = [create_enemy("crawler", pygame.Vector2(110, 0))]
    turret = MiniTurret(pygame.Vector2(0, 0), cooldown=0.0)
    turret.update(0.2, game)
    assert any(projectile.kind == "turret" and projectile.chain == 1 for projectile in game.projectiles)

    game = new_game("unique_burn")
    equip_unique(game, "crit_burn")
    game.player.crit_chance = 1.0
    burn_projectile = game.player._make_projectile(direction, game)
    assert burn_projectile.crit is True
    assert burn_projectile.poison_dps > 0

    game = new_game("unique_split")
    equip_unique(game, "impact_split", tank_id="flame_caster")
    assert game.player._make_projectile(direction, game).split >= 2

    game = new_game("unique_lifesteal")
    equip_unique(game, "drone_lifesteal", tank_id="engineer")
    enemy = create_enemy("crawler", pygame.Vector2(30, 0))
    game.enemies = [enemy]
    game.player.health = game.player.max_health - 10
    before = game.player.health
    projectile = Projectile(pygame.Vector2(30, 0), pygame.Vector2(1, 0), 5, 25, "player", 1.0, kind="turret")
    game._handle_player_projectile(projectile)
    assert game.player.health > before

    game = new_game("unique_ricochet")
    equip_unique(game, "ricochet_double", tank_id="twin_shot")
    assert game.player._make_projectile(direction, game).bounces >= 1

    game = new_game("unique_chests")
    equip_unique(game, "rare_chests", slot="trinket")
    game.save_data["loot_unlocked"] = True
    game.run_loot_unlocked = True
    game._open_loot_chest(quality=1)
    assert game.stats.chests_opened == 1

    game = new_game("unique_shield")
    equip_unique(game, "low_hp_shield", slot="armor")
    game.player.health = game.player.max_health * 0.2
    assert game.player.take_damage(20) is False
    assert game.player.invuln > 0


def test_missing_asset_fallback() -> None:
    bank = SpriteBank()
    assert "player" in bank.sprites
    assert "chest" in bank.sprites
    assert isinstance(bank.missing_assets, list)


def test_city_and_jungle_generated_tileset_contract() -> None:
    manifests = {
        "city": {
            "tiles": (
                "tile_city_road_01.png",
                "tile_city_road_02.png",
                "tile_city_road_cracked.png",
                "tile_city_concrete_01.png",
                "tile_city_concrete_02.png",
                "tile_city_sidewalk.png",
                "tile_city_intersection_marking.png",
                "tile_city_lane_marking.png",
                "tile_city_hazard_patch.png",
                "tile_city_border.png",
                "tile_city_wall.png",
                "tile_city_path_01.png",
            ),
            "props": (
                "prop_city_barrier_01.png",
                "prop_city_barrier_02.png",
                "prop_city_roadblock.png",
                "prop_city_scrap_barricade.png",
                "prop_city_broken_terminal.png",
                "prop_city_street_sign_broken.png",
                "prop_city_neon_sign_small.png",
                "prop_city_utility_box.png",
                "prop_city_debris_pile.png",
                "prop_city_wrecked_car_small.png",
            ),
            "landmarks": (
                "landmark_city_broken_bus.png",
                "landmark_city_billboard_wreck.png",
                "landmark_city_power_node.png",
                "landmark_city_collapsed_overpass_piece.png",
            ),
            "stage": "shattered_metro",
        },
        "jungle": {
            "tiles": (
                "tile_jungle_ground_01.png",
                "tile_jungle_ground_02.png",
                "tile_jungle_moss_01.png",
                "tile_jungle_root_path.png",
                "tile_jungle_ruin_floor.png",
                "tile_jungle_leaf_litter.png",
                "tile_jungle_wet_earth.png",
                "tile_jungle_glow_patch.png",
                "tile_jungle_border.png",
                "tile_jungle_wall.png",
                "tile_jungle_path_01.png",
            ),
            "props": (
                "prop_jungle_vine_cluster.png",
                "prop_jungle_bush_cluster.png",
                "prop_jungle_root_tangle.png",
                "prop_jungle_broken_ruin_piece.png",
                "prop_jungle_overgrown_machine.png",
                "prop_jungle_scrap_pile_mossy.png",
                "prop_jungle_fern_cluster.png",
                "prop_jungle_stone_shard.png",
                "prop_jungle_vine_barrier.png",
                "prop_jungle_small_relay_ruin.png",
            ),
            "landmarks": (
                "landmark_jungle_overgrown_outpost.png",
                "landmark_jungle_relay_ruin.png",
                "landmark_jungle_rock_formation.png",
                "landmark_jungle_root_wrapped_wreck.png",
            ),
            "stage": "overgrowth_basin",
        },
    }
    bank = SpriteBank()
    for theme, manifest in manifests.items():
        folder = ROOT / "assets" / "environment" / theme
        expected_paths = [folder / name for group in ("tiles", "props", "landmarks") for name in manifest[group]]
        assert all(path.is_file() for path in expected_paths)
        for path in (folder / name for name in manifest["tiles"]):
            surface = pygame.image.load(path).convert_alpha()
            assert surface.get_size() == (32, 32)
            assert surface.get_alpha() is None or surface.get_at((0, 0)).a == 255
        for path in (folder / name for name in (*manifest["props"], *manifest["landmarks"])):
            surface = pygame.image.load(path).convert_alpha()
            assert surface.get_at((0, 0)).a == 0
        relative_paths = {str(path.relative_to(ROOT / "assets")) for path in expected_paths}
        assert relative_paths.issubset(bank.loaded_external_assets)
        assert len(bank.landmarks[manifest["stage"]]) >= len(manifest["landmarks"])


def test_city_and_jungle_layout_composition() -> None:
    game = new_game("biome_layout")
    game.select_stage("shattered_metro")
    game.reset_run()
    city_x = game.arena_width // (2 * 32)
    city_y = game.arena_height // (2 * 32)
    assert game._terrain_tile_index(city_x, city_y) == 6
    assert game._terrain_tile_index(city_x + 3, city_y) == 5
    assert game._terrain_tile_index(city_x + 7, city_y) in (3, 4)
    assert all(
        kind == "landmark" or game._terrain_tile_index(int(pos.x // 32), int(pos.y // 32)) not in (0, 1, 2, 6, 7)
        for pos, kind, _ in game.map_decor
    )

    game.select_stage("overgrowth_basin")
    game.reset_run()
    jungle_x = game.arena_width // (2 * 32)
    jungle_y = game.arena_height // (2 * 32)
    assert game._terrain_tile_index(jungle_x, jungle_y) == 4
    trail_y = jungle_y + 8
    trail_x = round(jungle_x + math.sin(trail_y * 0.17) * 3.4 + math.sin(trail_y * 0.055) * 1.6)
    trail_band = {game._terrain_tile_index(trail_x + offset, trail_y) for offset in range(-2, 3)}
    assert 8 in trail_band
    assert 3 in trail_band


def test_tank_selection() -> None:
    game = new_game("tank")
    game.save_data["unlocked_tanks"] = ["starter", "sniper"]
    game.choose_or_buy_tank("sniper")
    assert game.save_data["selected_tank"] == "sniper"


def test_run_end_coin_payout() -> None:
    game = new_game("payout")
    game.stats.run_coins = 12
    game.finish_run()
    assert game.save_data["coins"] == 12
    assert game.save_data["stats"]["total_coins_earned"] == 12


def test_debug_unlock_flag() -> None:
    game = new_game("debug", debug_unlock_loot=True)
    assert game.save_data["loot_unlocked"] is True


def test_unlock_milestones_and_gated_content() -> None:
    data = normalize_save(
        {
            "lifetime_contracts_completed": 10,
            "lifetime_salvage_surges_survived": 3,
            "best_survival_time": 480,
            "lifetime_bosses_defeated": 3,
            "lifetime_chests_opened": 10,
            "lifetime_evolutions_triggered": 2,
            "lifetime_ability_uses": 100,
            "stage_best_times": {"desert_wrecks": 300},
            "stage_contract_counts": {"frozen_base": 2},
            "stage_contracts_completed": ["scrap_outskirts", "desert_wrecks", "frozen_base"],
            "elemental_evolution_families": ["Fire", "Cryo"],
        }
    )
    newly_unlocked = {unlock.id for unlock in evaluate_unlocks(data)}
    assert "elite_contract_board" in newly_unlocked
    assert "elemental_fusion_pack" in newly_unlocked
    assert "contract_tech_pack" in newly_unlocked
    assert "ability_variant_pack" in newly_unlocked
    assert not data["research_completed"]

    player = Player(pygame.Vector2(0, 0))
    configure_player_tank(player, "starter")
    player.upgrade_counts.update({"burn_oil": 1, "lightning_chain": 1})
    assert "conductive_wildfire" not in {upgrade.id for upgrade in available_upgrades(player)}
    player.content_unlocks.add("elemental_fusion_pack")
    assert "conductive_wildfire" in {upgrade.id for upgrade in available_upgrades(player)}

    flame = Player(pygame.Vector2(0, 0))
    configure_player_tank(flame, "flame_caster")
    flame.content_unlocks.add("ability_variant_pack")
    flame.upgrade_counts["burn_oil"] = 1
    assert "split_fireball" in {upgrade.id for upgrade in available_upgrades(flame)}


def test_research_purchase_and_modifier_separation() -> None:
    data = normalize_save(
        {
            "coins": 5000,
            "blueprint_fragments": 20,
            "unlocked_tanks": ["starter", "flame_caster", "sniper", "engineer"],
        }
    )
    fragments_before = data["blueprint_fragments"]
    purchased, detail = purchase_research(data, "flame_injector")
    assert purchased and detail == "Flame Injector"
    assert data["coins"] == 5000
    assert data["blueprint_fragments"] == fragments_before - RESEARCH_BY_ID["flame_injector"].fragment_cost
    assert "flame_injector" in data["research_completed"]
    assert not data["unlocks_completed"]

    player = Player(pygame.Vector2(0, 0))
    configure_player_tank(player, "flame_caster")
    apply_research_modifiers(player, data)
    assert player.fire_patch_radius_bonus > 0


def test_progression_screens_and_contract_completion() -> None:
    game = new_game("progression_screens")
    game.state = ScreenState.ACHIEVEMENTS
    game.progression_tab = "achievements"
    game.draw()
    game.progression_tab = "unlocks"
    game.draw()
    game.state = ScreenState.TANK_SELECT
    game.garage_tab = "research"
    game.research_category = "Ability Augments"
    game.draw()

    game.start_run()
    game.active_contract = RunContract("qa_contract", "QA Contract", "kills", 1, "QA", "QA")
    game._advance_contract("kills", 1)
    assert game.contract_completed is True
    assert game.save_data["lifetime_contracts_completed"] == 1
    assert game.save_data["blueprint_fragments"] >= 1


def test_progression_navigation_is_compact() -> None:
    game = new_game("progression_navigation")
    buttons = game.ui.menu_button_rects()
    assert set(buttons) == {"play", "tanks", "shop", "achievements", "stages", "quit"}

    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": buttons["achievements"].center}))
    game._handle_events()
    assert game.state == ScreenState.ACHIEVEMENTS
    assert game.progression_tab == "achievements"

    next_page = game.ui.achievement_page_rects()["next"]
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": next_page.center}))
    game._handle_events()
    assert game.achievement_page == 1

    unlock_tab = game.ui.progression_tab_rects()["unlocks"]
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": unlock_tab.center}))
    game._handle_events()
    assert game.progression_tab == "unlocks"

    game.state = ScreenState.MENU
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": buttons["tanks"].center}))
    game._handle_events()
    assert game.state == ScreenState.TANK_SELECT

    research_tab = game.ui.garage_tab_rects()["research"]
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": research_tab.center}))
    game._handle_events()
    assert game.garage_tab == "research"

    category = "Ability Augments"
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": game.ui.research_filter_rects()[category].center}))
    game._handle_events()
    assert game.research_category == category
    assert {project.category for project in RESEARCH_BY_ID.values()}.issubset(set(RESEARCH_CATEGORIES))


def test_progression_image_assets_and_legacy_migration() -> None:
    game = new_game("progression_images")
    required = {
        "unlock_elemental_fusion_pack",
        "unlock_ability_variant_pack",
        "unlock_elemental_elites",
        "unlock_relic_prototypes",
        "unlock_contract_tech_pack",
        "research_flame_injector",
        "research_ability_augments",
        "research_contract_tech",
        "research_evolution_lab",
        "progression_tooltip_accent",
    }
    assert required.issubset(game.assets.icons)
    for key in required:
        assert game.assets.icons[key].get_flags() & pygame.SRCALPHA
    assert {unlock.icon for unlock in UNLOCKS}.issubset(game.assets.icons)

    migrated = normalize_save({"unlocks_completed": ["elemental_fusion_upgrades", "boss_relic_drops"]})
    assert {"elemental_fusion_pack", "relic_prototypes"}.issubset(migrated["unlocks_completed"])


def test_tracks_equipment_and_skill_tree_progression() -> None:
    track = {
        "id": "track_qa",
        "name": "Drift Treads",
        "type": "tracks",
        "rarity": "Rare",
        "stats": {"Dexterity": 2},
        "effect": "track_drift",
        "template_id": "drift_treads",
        "art_key": "equipment_tracks_drift_treads",
    }
    data = normalize_save(
        {
            "gear_inventory": [track],
            "equipped_gear": {"tracks": "track_qa"},
            "stats": {"starter_best_time": 480},
            "tank_skill_trees": {"starter": ["node_offense"]},
        }
    )
    assert data["equipped_gear"]["tracks"] == "track_qa"
    assert data["tank_skill_trees"]["starter"] == ["strength_impact"]
    assert available_skill_points(data, "starter") == 3
    assert node_status(data, "starter", SKILL_BY_ID["strength_ram"]) == "Available"
    learned, _ = unlock_skill_node(data, "starter", "strength_ram")
    assert learned

    player = Player(pygame.Vector2(0, 0))
    configure_player_tank(player, "starter")
    apply_meta_upgrades(player, data)
    assert player.speed > 220
    assert player.handling_response > 13.5
    assert player.ram_damage_mult > 1.0


def test_equipment_skill_assets_and_new_stage_integration() -> None:
    game = new_game("equipment_stage_assets")
    expected_equipment = {template.art_key for template in EQUIPMENT_TEMPLATES}
    expected_skills = {f"skill_{branch.lower()}" for branch in ("Strength", "Dexterity", "Vitality", "Tech", "Focus", "Luck")}
    assert expected_equipment.issubset(game.assets.icons)
    assert expected_skills.issubset(game.assets.icons)
    assert {"shattered_metro", "overgrowth_basin"}.issubset(STAGE_BY_ID)
    assert len(STAGES) == 5
    for stage_id in ("scrap_outskirts", "desert_wrecks", "frozen_base", "shattered_metro", "overgrowth_basin"):
        stage = STAGE_BY_ID[stage_id]
        assert stage.tileset in game.assets.tilesets
        assert len(game.assets.landmarks[stage_id]) >= 4
        game.select_stage(stage_id)
        game.reset_run()
        assert game.stage.id == stage_id
        assert game.map_decor[-1][1] == "landmark"
        game.start_run()
        game.update(1 / 60)
    game.state = ScreenState.TANK_SELECT
    game.garage_tab = "gear"
    game.draw()
    game.garage_tab = "skill_tree"
    game.draw()


def test_skill_tree_navigation_and_city_jungle_modifiers() -> None:
    game = new_game("skill_tree_navigation")
    game.state = ScreenState.TANK_SELECT
    skill_tab = game.ui.garage_tab_rects()["skill_tree"]
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": skill_tab.center}))
    game._handle_events()
    assert game.garage_tab == "skill_tree"
    game.save_data["stats"]["starter_best_time"] = 120
    first_node = game.ui.skill_tree_node_rects()["strength_impact"]
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": first_node.center}))
    game._handle_events()
    assert "strength_impact" in game.save_data["tank_skill_trees"]["starter"]

    game.state = ScreenState.STAGE_SELECT
    city_card = game.ui.stage_card_rects()["shattered_metro"]
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": city_card.center}))
    game._handle_events()
    assert game.save_data["selected_stage"] == "shattered_metro"

    game.reset_run()
    assert game.urban_crossfire_active is True
    assert game.stage_pickup_density_bonus > 0
    game.select_stage("overgrowth_basin")
    game.reset_run()
    assert game.urban_crossfire_active is False
    assert game.stage_pickup_density_bonus > 0
    assert game.player.speed < 220


def test_equipment_screen_tracks_click_and_persistence() -> None:
    game = new_game("equipment_tracks_click")
    item = {
        "id": "magnet_tracks_qa",
        "name": "Magnet Tracks",
        "type": "tracks",
        "rarity": "Rare",
        "stats": {"Tech": 1, "Luck": 1},
        "effect": "track_magnet",
        "template_id": "magnet_tracks",
        "art_key": "equipment_tracks_magnet_tracks",
    }
    game.save_data["gear_inventory"] = [item]
    game.state = ScreenState.TANK_SELECT
    game.garage_tab = "gear"
    target = game.ui.equipment_inventory_rects()[0]
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": target.center}))
    game._handle_events()
    assert game.save_data["equipped_gear"]["tracks"] == item["id"]
    assert game.player.magnet_radius > 115
    game.draw()


def main() -> int:
    pygame.init()
    pygame.display.set_mode((1280, 720))
    tests = [
        test_fresh_save_creation,
        test_save_migration,
        test_achievement_unlock_once,
        test_five_minute_loot_unlock,
        test_upgrade_tree_rules,
        test_family_passive_unlocks,
        test_family_evolution_unlocks,
        test_poison_stacks_corrosion_and_conductive_arcs,
        test_level_up_recovery_and_healing_upgrades,
        test_evolution_art_integration,
        test_elemental_passive_effect_hooks,
        test_enemy_boss_variety_assets_and_spawns,
        test_screen_shake_policy,
        test_pickup_caps_and_merge,
        test_ninety_second_performance_window_caps,
        test_chest_reward_generation,
        test_equipping_unique_gear,
        test_unique_effect_hooks,
        test_missing_asset_fallback,
        test_city_and_jungle_generated_tileset_contract,
        test_city_and_jungle_layout_composition,
        test_tank_selection,
        test_run_end_coin_payout,
        test_debug_unlock_flag,
        test_unlock_milestones_and_gated_content,
        test_research_purchase_and_modifier_separation,
        test_progression_screens_and_contract_completion,
        test_progression_navigation_is_compact,
        test_progression_image_assets_and_legacy_migration,
        test_tracks_equipment_and_skill_tree_progression,
        test_equipment_skill_assets_and_new_stage_integration,
        test_skill_tree_navigation_and_city_jungle_modifiers,
        test_equipment_screen_tracks_click_and_persistence,
    ]
    for test in tests:
        test()
        print(f"[PASS] {test.__name__}")
    pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
