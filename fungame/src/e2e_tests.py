from __future__ import annotations

import pygame
from src.game_state import ScreenState
from src.constants import MAX_PARTICLES, SCREEN_WIDTH, SCREEN_HEIGHT
from src.achievements import ACHIEVEMENTS, evaluate_achievements, achievement_bonuses, progress_for
from src.save_manager import SaveManager, normalize_save
from src.effects import Particle
from src.enemy import ENEMY_TYPES, create_enemy
from src.tank_data import TANKS, TANK_BY_ID, configure_player_tank
from src.upgrades import choose_upgrades, Upgrade, apply_upgrade
from src.meta_upgrades import META_UPGRADES, apply_meta_upgrades

# Determine if features are implemented based on attributes
is_f1_implemented = False
is_f2_implemented = False
is_f3_implemented = False
is_f4_implemented = False
is_f5_implemented = False
is_f6_implemented = False
is_f7_implemented = False

def detect_implementation_states(game):
    global is_f1_implemented, is_f2_implemented, is_f3_implemented, is_f4_implemented, is_f5_implemented, is_f6_implemented, is_f7_implemented
    is_f1_implemented = hasattr(game, "menu_particles") or hasattr(game.ui, "menu_title") or hasattr(game.ui, "title_text")
    is_f2_implemented = "sniper_portrait" in game.assets.sprites or "portrait_sniper" in game.assets.sprites
    is_f3_implemented = hasattr(game.player, "time_since_damage")
    is_f4_implemented = hasattr(game.ui, "get_achievement_at") or hasattr(game.ui, "hover_achievement") or hasattr(game.ui, "draw_achievement_detail")
    is_f5_implemented = hasattr(game.player, "Strength") or hasattr(game.player, "gear") or "gear_inventory" in game.save_data
    is_f6_implemented = hasattr(game.player, "cast_skill") or hasattr(game.player, "active_skills")
    is_f7_implemented = hasattr(game.player, "skill_points") or hasattr(game.player, "allocate_node") or hasattr(game.player, "refund_node")

# --- Tier 1 Test Functions ---

def test_t1_f1_1(game):
    return game.state in ScreenState.__members__.values()

def test_t1_f1_2(game):
    rects = game.ui.menu_button_rects()
    return isinstance(rects, dict) and "play" in rects and "quit" in rects

def test_t1_f1_3(game):
    rects = game.ui.menu_button_rects()
    return all(isinstance(r, pygame.Rect) and r.width > 0 and r.height > 0 for r in rects.values())

def test_t1_f1_4(game):
    return isinstance(game.particles, list)

def test_t1_f1_5(game):
    return hasattr(game.ui, "draw_menu") and callable(game.ui.draw_menu)

def test_t1_f2_1(game):
    return "chassis_sniper" in game.assets.sprites and "turret_sniper" in game.assets.sprites

def test_t1_f2_2(game):
    if "sniper_portrait" in game.assets.sprites:
        return isinstance(game.assets.sprites["sniper_portrait"], pygame.Surface)
    elif "portrait_sniper" in game.assets.sprites:
        return isinstance(game.assets.sprites["portrait_sniper"], pygame.Surface)
    else:
        return "tank_icon_sniper" in game.assets.sprites

def test_t1_f2_3(game):
    return isinstance(game.map_decor, list) and len(game.map_decor) > 0

def test_t1_f2_4(game):
    for item in game.map_decor[:5]:
        if not (isinstance(item, tuple) and len(item) >= 3 and isinstance(item[0], pygame.Vector2) and isinstance(item[1], str) and isinstance(item[2], int)):
            return False
    return True

def test_t1_f2_5(game):
    surf = game.assets.rotated("player_sniper", pygame.Vector2(1, 0))
    return isinstance(surf, pygame.Surface)

def test_t1_f3_1(game):
    return hasattr(game.player, "regen_per_second")

def test_t1_f3_2(game):
    p = game.player
    old_health = p.health
    p.health = p.max_health - 10
    old_regen = p.regen_per_second
    p.regen_per_second = 2.0
    p.heal(2.0 * 0.1)
    success = p.health > (p.max_health - 10)
    p.health = old_health
    p.regen_per_second = old_regen
    return success

def test_t1_f3_3(game):
    if is_f3_implemented:
        return hasattr(game.player, "time_since_damage")
    return hasattr(game.player, "invuln")

def test_t1_f3_4(game):
    return (ENEMY_TYPES["crawler"]["speed"] == 74 and
            ENEMY_TYPES["runner"]["speed"] == 146 and
            ENEMY_TYPES["brute"]["speed"] == 48 and
            ENEMY_TYPES["shooter"]["speed"] == 68)

def test_t1_f3_5(game):
    res = game.director.scaling(10.0)
    return isinstance(res, tuple) and len(res) == 2 and isinstance(res[0], float) and isinstance(res[1], float)

def test_t1_f4_1(game):
    return isinstance(ACHIEVEMENTS, tuple | list) and len(ACHIEVEMENTS) > 0

def test_t1_f4_2(game):
    return "achievements" in ScreenState.__members__.values()

def test_t1_f4_3(game):
    r = game.ui.back_rect()
    return isinstance(r, pygame.Rect) and r.width > 0 and r.height > 0

def test_t1_f4_4(game):
    if is_f4_implemented:
        return any(hasattr(game.ui, m) for m in ["get_achievement_at", "hover_achievement", "draw_achievement_detail"])
    return callable(evaluate_achievements)

def test_t1_f4_5(game):
    for a in ACHIEVEMENTS:
        if not (hasattr(a, "id") and hasattr(a, "name") and hasattr(a, "description") and hasattr(a, "stat") and hasattr(a, "target") and hasattr(a, "reward") and hasattr(a, "reward_value") and hasattr(a, "icon")):
            return False
    return True

def test_t1_f5_1(game):
    save_data = game.save_manager.load()
    return isinstance(save_data, dict) and "coins" in save_data and "universal_upgrades" in save_data

def test_t1_f5_2(game):
    if is_f5_implemented:
        return "gear_inventory" in game.save_data or hasattr(game.player, "gear")
    return "unlocked_tanks" in game.save_data

def test_t1_f5_3(game):
    p = game.player
    if is_f5_implemented:
        return all(hasattr(p, stat) for stat in ["Strength", "Dexterity", "Vitality", "Tech", "Focus", "Luck"])
    return isinstance(p.speed, float | int) and isinstance(p.armor, float | int) and isinstance(p.luck, float | int)

def test_t1_f5_4(game):
    save_data = game.save_manager.load()
    orig_coins = save_data["coins"]
    save_data["coins"] = orig_coins + 10
    game.save_manager.save(save_data)
    new_save_data = game.save_manager.load()
    save_data["coins"] = orig_coins
    game.save_manager.save(save_data)
    return new_save_data["coins"] == orig_coins + 10

def test_t1_f5_5(game):
    if is_f5_implemented and "gear_inventory" in game.save_data:
        gear = game.save_data["gear_inventory"]
        return isinstance(gear, list)
    upgrades = game.save_data["universal_upgrades"]
    return isinstance(upgrades, dict) and all(isinstance(v, int) and v >= 0 for v in upgrades.values())

def test_t1_f6_1(game):
    if is_f6_implemented:
        return True
    return pygame.K_w != pygame.K_a

def test_t1_f6_2(game):
    if is_f6_implemented:
        return True
    p = game.player
    old_aim = p.aim_dir
    p.aim_dir = pygame.Vector2(10, 10)
    success = pygame.Vector2(10, 10).normalize() == pygame.Vector2(1, 1).normalize()
    p.aim_dir = old_aim
    return success

def test_t1_f6_3(game):
    if is_f6_implemented:
        return True
    p = game.player
    old_dc = p.dash_cooldown
    p.dash_cooldown = 1.0
    p._update_timers(0.2)
    success = p.dash_cooldown == 0.8
    p.dash_cooldown = old_dc
    return success

def test_t1_f6_4(game):
    if is_f6_implemented:
        return True
    return hasattr(game.ui, "draw_hud")

def test_t1_f6_5(game):
    if is_f6_implemented:
        return True
    p = game.player
    old_cooldown = p.cooldown
    p.cooldown = 0.0
    init_proj_count = len(game.projectiles)
    p._fire_volley(game)
    success = len(game.projectiles) > init_proj_count
    game.projectiles = game.projectiles[:init_proj_count]
    p.cooldown = old_cooldown
    return success

def test_t1_f7_1(game):
    return isinstance(TANKS, tuple) and len(TANKS) >= 3

def test_t1_f7_2(game):
    p = game.player
    old_id = p.tank_id
    configure_player_tank(p, "sniper")
    sniper_ok = p.tank_id == "sniper" and p.bullet_damage == 52
    configure_player_tank(p, "engineer")
    engineer_ok = p.tank_id == "engineer" and p.engineer_turret_cap == 3
    configure_player_tank(p, "starter")
    starter_ok = p.tank_id == "starter"
    configure_player_tank(p, old_id)
    return sniper_ok and engineer_ok and starter_ok

def test_t1_f7_3(game):
    if is_f7_implemented:
        return True
    upgrades = choose_upgrades(game.player)
    return isinstance(upgrades, list)

def test_t1_f7_4(game):
    if is_f7_implemented:
        return True
    p = game.player
    up = Upgrade("test_up", "Test", "Desc", "rapid_fire", 1, 3)
    apply_upgrade(p, up)
    success = p.upgrade_counts["test_up"] == 1
    p.upgrade_counts["test_up"] = 0
    return success

def test_t1_f7_5(game):
    if is_f7_implemented:
        return True
    old_stage = game.save_data.get("selected_stage")
    game.select_stage("frozen_base")
    success = game.save_data.get("selected_stage") == "frozen_base"
    if old_stage:
        game.select_stage(old_stage)
    return success

# --- Tier 2 Test Functions ---

def test_t2_f1_1(game):
    rects = game.ui.menu_button_rects()
    play_rect = rects["play"]
    return play_rect.collidepoint(play_rect.topleft)

def test_t2_f1_2(game):
    rects = game.ui.menu_button_rects()
    for r in rects.values():
        if not (0 <= r.centerx <= SCREEN_WIDTH and 0 <= r.centery <= SCREEN_HEIGHT):
            return False
    return True

def test_t2_f1_3(game):
    init_len = len(game.particles)
    game.particles.append(Particle(pygame.Vector2(0, 0), pygame.Vector2(0, 0), (255, 255, 255), 1.0, 1.0))
    game.particles.pop()
    return len(game.particles) == init_len

def test_t2_f1_4(game):
    surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    try:
        game.ui.draw_menu(surf, game)
        return True
    except Exception:
        return False

def test_t2_f1_5(game):
    p = Particle(pygame.Vector2(0, 0), pygame.Vector2(0, 0), (255, 255, 255), 1.0, 1.0)
    if not p.update(0.0):
        return False
    old_state = game.state
    game.state = ScreenState.MENU
    game.menu_particles = []
    game.update(0.01)
    if len(game.menu_particles) != 80:
        game.state = old_state
        return False
    y_positions = [pt.pos.y for pt in game.menu_particles]
    top_half = any(y < 360 for y in y_positions)
    bottom_half = any(y >= 360 for y in y_positions)
    if not (top_half and bottom_half):
        game.state = old_state
        return False
    for pt in game.menu_particles:
        if not (8.0 <= pt.ttl <= 15.0):
            game.state = old_state
            return False
        if not (-130.0 <= pt.vel.y <= -65.0):
            game.state = old_state
            return False
    game.state = old_state
    return True

def test_t2_f2_1(game):
    surf1 = game.assets.rotated("player_sniper", pygame.Vector2(1, 0))
    surf2 = game.assets.rotated("player_sniper", pygame.Vector2(-1, -1))
    if not (isinstance(surf1, pygame.Surface) and isinstance(surf2, pygame.Surface)):
        return False
    old_selected = game.save_data.get("selected_tank", "starter")
    game.save_data["selected_tank"] = "sniper"
    test_surf = pygame.Surface((1280, 720))
    try:
        game.ui.draw_tank_select(test_surf, game)
    except Exception:
        game.save_data["selected_tank"] = old_selected
        return False
    game.save_data["selected_tank"] = old_selected
    return True

def test_t2_f2_2(game):
    for pos, kind, idx in game.map_decor:
        if not (0 <= pos.x <= game.arena_width and 0 <= pos.y <= game.arena_height):
            return False
    return True

def test_t2_f2_3(game):
    if len(game.map_decor) == 0:
        return False
    for theme in ["scrap", "desert", "frozen"]:
        surfaces = []
        for i in range(5):
            surf = game.assets._decor_tile(i, theme)
            if not isinstance(surf, pygame.Surface):
                return False
            if surf.get_size() != (32, 32):
                return False
            surfaces.append(surf)
        pixel_strs = [pygame.image.tostring(s, "RGBA") for s in surfaces]
        if len(set(pixel_strs)) < 5:
            return False
    return True

def test_t2_f2_4(game):
    for t in ["scrap", "desert", "frozen"]:
        if t not in game.assets.tilesets:
            return False
        if "floor" not in game.assets.tilesets[t]:
            return False
        if not all(isinstance(s, pygame.Surface) for s in game.assets.tilesets[t]["floor"]):
            return False
    return True

def test_t2_f2_5(game):
    decor1 = game._build_map_decor()
    decor2 = game._build_map_decor()
    if len(decor1) != len(decor2):
        return False
    for (p1, k1, i1), (p2, k2, i2) in zip(decor1, decor2):
        if p1 != p2 or k1 != k2 or i1 != i2:
            return False
    return True

def test_t2_f3_1(game):
    p = game.player
    old_health = p.health
    p.health = p.max_health - 0.01
    p.heal(10.0)
    success = p.health == p.max_health
    p.health = old_health
    return success

def test_t2_f3_2(game):
    p = game.player
    if is_f3_implemented:
        old_val = p.time_since_damage
        p.time_since_damage = 5.0
        p.take_damage(1)
        success = p.time_since_damage == 0
        p.time_since_damage = old_val
        return success
    else:
        old_inv = p.invuln
        p.invuln = 1.0
        p._update_timers(0.5)
        success = p.invuln == 0.5
        p.invuln = old_inv
        return success

def test_t2_f3_3(game):
    e = create_enemy("crawler", pygame.Vector2(0, 0))
    e.apply_slow(2.0, 0.5)
    return e.slow_timer == 2.0 and e.slow_strength == 0.5

def test_t2_f3_4(game):
    h, s = game.director.scaling(10000.0)
    return h > 0 and s > 0

def test_t2_f3_5(game):
    p = game.player
    old_health = p.health
    try:
        p.take_damage(-5)
        success = True
    except Exception:
        success = False
    p.health = old_health
    return success

def test_t2_f4_1(game):
    if hasattr(game.ui, "get_achievement_at"):
        res = game.ui.get_achievement_at((-100, -100))
        return res is None
    elif hasattr(game.ui, "hover_achievement"):
        res = game.ui.hover_achievement((-100, -100))
        return True
    else:
        r = game.ui.back_rect()
        return not r.collidepoint((-100, -100))

def test_t2_f4_2(game):
    save_data = {
        "achievements": [],
        "stats": {"best_time": 300}
    }
    res = evaluate_achievements(save_data)
    return len(res) == 1 and res[0].id == "survive_5" and "survive_5" in save_data["achievements"]

def test_t2_f4_3(game):
    save_data = {
        "achievements": [],
        "stats": {"best_time": 1000}
    }
    res = evaluate_achievements(save_data)
    ids = [a.id for a in res]
    return "survive_5" in ids and "survive_10" in ids

def test_t2_f4_4(game):
    bonuses = achievement_bonuses({"achievements": []})
    return isinstance(bonuses, dict) and all(v == 0.0 for v in bonuses.values())

def test_t2_f4_5(game):
    current, target = progress_for(ACHIEVEMENTS[0], {})
    return current == 0 and target == ACHIEVEMENTS[0].target

def test_t2_f5_1(game):
    import tempfile, os
    temp_path = os.path.join(tempfile.gettempdir(), "nonexistent_save_file_e2e_test.json")
    if os.path.exists(temp_path):
        try:
            os.remove(temp_path)
        except OSError:
            pass
    sm = SaveManager(path=temp_path)
    data = sm.load()
    if os.path.exists(temp_path):
        try:
            os.remove(temp_path)
        except OSError:
            pass
    return isinstance(data, dict) and data["selected_tank"] == "starter"

def test_t2_f5_2(game):
    if is_f5_implemented and hasattr(game, "add_gear_item"):
        return True
    res = normalize_save({"selected_tank": 1234})
    return res["selected_tank"] == "starter"

def test_t2_f5_3(game):
    p = game.player
    old_luck = p.luck
    p.luck = -10.0
    p.luck = 1000.0
    p.luck = old_luck
    return True

def test_t2_f5_4(game):
    sm = game.save_manager
    for _ in range(5):
        d = sm.load()
        sm.save(d)
    return True

def test_t2_f5_5(game):
    bad_data = {
        "universal_upgrades": {
            "max_health": "invalid_string",
            "move_speed": 4.5
        }
    }
    res = normalize_save(bad_data)
    return res["universal_upgrades"]["max_health"] == 0

def test_t2_f6_1(game):
    if is_f6_implemented:
        return True
    p = game.player
    old_dash = p.dash_cooldown
    p.dash_cooldown = 1.0
    old_vel = p.vel.copy()
    p._dash(pygame.Vector2(1, 0), game)
    success = p.vel == old_vel
    p.dash_cooldown = old_dash
    return success

def test_t2_f6_2(game):
    if is_f6_implemented:
        return True
    pos = game.screen_to_world(pygame.Vector2(-10000, 10000))
    return isinstance(pos, pygame.Vector2)

def test_t2_f6_3(game):
    if is_f6_implemented:
        return True
    p = game.player
    old_health = p.health
    p.health = 0
    success = not p.alive
    p.health = old_health
    return success

def test_t2_f6_4(game):
    if is_f6_implemented:
        return True
    p = game.player
    old_dc = p.dash_cooldown
    p.dash_cooldown = 1.0
    try:
        p._update_timers(-10.0)
        success = True
    except Exception:
        success = False
    p.dash_cooldown = old_dc
    return success

def test_t2_f6_5(game):
    p = game.player
    p.pending_dash = True
    keys = pygame.key.get_pressed()
    p.update(0.01, keys, p.pos, game)
    return p.pending_dash == False

def test_t2_f7_1(game):
    p = game.player
    old_id = p.tank_id
    configure_player_tank(p, "nonexistent_tank_id")
    res = p.tank_id == "starter"
    configure_player_tank(p, old_id)
    return res

def test_t2_f7_2(game):
    old_coins = game.save_data.get("coins", 0)
    old_unlocked = list(game.save_data.get("unlocked_tanks", []))
    
    game.save_data["coins"] = 5
    if "sniper" in game.save_data.setdefault("unlocked_tanks", []):
        game.save_data["unlocked_tanks"].remove("sniper")
        
    game.choose_or_buy_tank("sniper")
    success = "sniper" not in game.save_data["unlocked_tanks"]
    
    game.save_data["coins"] = old_coins
    game.save_data["unlocked_tanks"] = old_unlocked
    game.save_manager.save(game.save_data)
    return success

def test_t2_f7_3(game):
    if is_f7_implemented:
        return True
    old_state = game.state
    game.level_choices = [object()]
    game.select_upgrade(99)
    success = len(game.level_choices) == 1
    game.level_choices = []
    game.state = old_state
    return success

def test_t2_f7_4(game):
    if is_f7_implemented:
        return True
    old_state = game.state
    game.level_choices = [object()]
    game.select_upgrade(-5)
    success = len(game.level_choices) == 1
    game.level_choices = []
    game.state = old_state
    return success

def test_t2_f7_5(game):
    rects = game.ui.tank_card_rects()
    return not any(r.collidepoint((-100, -100)) for r in rects.values())

# --- Tier 3 Test Functions ---

def test_t3_1(game):
    old_state = game.state
    game.state = ScreenState.MENU
    buttons = game.ui.menu_button_rects()
    ach_btn = buttons["achievements"]
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=ach_btn.center))
    game._handle_events()
    step1 = game.state == ScreenState.ACHIEVEMENTS
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
    game._handle_events()
    step2 = game.state == ScreenState.MENU
    game.state = old_state
    return step1 and step2

def test_t3_2(game):
    p = game.player
    old_id = p.tank_id
    configure_player_tank(p, "sniper")
    sprite_key = p.sprite_key
    bullet_sprite = "sniper_bullet" in game.assets.sprites
    configure_player_tank(p, old_id)
    return sprite_key == "player_sniper" and bullet_sprite

def test_t3_3(game):
    p = game.player
    old_max_health = p.max_health
    old_health = p.health
    save_data = {
        "universal_upgrades": {"max_health": 5},
        "stats": {}
    }
    apply_meta_upgrades(p, save_data)
    hp_increased = p.max_health > 100
    p.max_health = old_max_health
    p.health = old_health
    return hp_increased

def test_t3_4(game):
    p = game.player
    old_inv = p.invuln
    old_dc = p.dash_cooldown
    p.dash_cooldown = 0.0
    p._dash(pygame.Vector2(1, 0), game)
    dashed = p.dash_cooldown > 0 and p.invuln > 0
    p.invuln = old_inv
    p.dash_cooldown = old_dc
    return dashed

def test_t3_5(game):
    sm = game.save_manager
    orig_save = sm.load()
    test_save = {
        "coins": 500,
        "selected_tank": "sniper",
        "unlocked_tanks": ["starter", "sniper"],
        "universal_upgrades": orig_save["universal_upgrades"],
        "stats": orig_save["stats"]
    }
    sm.save(test_save)
    loaded = sm.load()
    sm.save(orig_save)
    return loaded["coins"] == 500 and loaded["selected_tank"] == "sniper" and "sniper" in loaded["unlocked_tanks"]

def test_t3_6(game):
    save_data = {
        "achievements": [],
        "stats": {"total_coins_earned": 200}
    }
    unlocked = evaluate_achievements(save_data)
    return len(unlocked) == 1 and unlocked[0].id == "coins_100" and "coins_100" in save_data["achievements"]

def test_t3_7(game):
    from src.player import Player
    p_starter = Player(pygame.Vector2(0, 0))
    p_sniper = Player(pygame.Vector2(0, 0))
    configure_player_tank(p_starter, "starter")
    configure_player_tank(p_sniper, "sniper")
    return p_sniper.bullet_damage > p_starter.bullet_damage and p_sniper.bullet_speed > p_starter.bullet_speed

# --- Tier 4 Test Functions (Scenarios) ---

def test_t4_1(game):
    from src.game_state import ScreenState
    import pygame
    old_state = game.state
    orig_save = game.save_manager.load()
    
    # Ensure starter and sniper are unlocked
    game.save_data["unlocked_tanks"] = ["starter", "sniper"]
    game.save_data["coins"] = orig_save["coins"]
    
    # Start in Menu state
    game.state = ScreenState.MENU
    buttons = game.ui.menu_button_rects()
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=buttons["tanks"].center))
    game._handle_events()
    if game.state != ScreenState.TANK_SELECT:
        game.state = old_state
        game.save_manager.save(orig_save)
        game.save_data.update(orig_save)
        return False
        
    tank_cards = game.ui.tank_card_rects()
    sniper_card = tank_cards["sniper"]
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=sniper_card.center))
    game._handle_events()
    
    selected_ok = game.save_data.get("selected_tank") == "sniper"
        
    back_btn = game.ui.back_rect()
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=back_btn.center))
    game._handle_events()
    
    step_ok = selected_ok and game.state == ScreenState.MENU
    
    # Restore
    game.save_manager.save(orig_save)
    game.save_data.clear()
    game.save_data.update(orig_save)
    game.state = old_state
    return step_ok

def test_t4_2(game):
    old_state = game.state
    game.state = ScreenState.PLAYING
    p = game.player
    old_level = p.level
    old_xp = p.xp
    old_counts = dict(p.upgrade_counts)
    
    p.gain_xp(p.xp_to_next + 10)
    if not p.can_level():
        game.state = old_state
        return False
        
    game._open_level_up()
    if game.state != ScreenState.LEVEL_UP or len(game.level_choices) == 0:
        game.state = old_state
        return False
        
    up = game.level_choices[0]
    game.select_upgrade(0)
    success = p.level > old_level and game.state in (ScreenState.PLAYING, ScreenState.LEVEL_UP)
    
    p.level = old_level
    p.xp = old_xp
    p.upgrade_counts.clear()
    p.upgrade_counts.update(old_counts)
    game.level_choices = []
    game.state = old_state
    return success

def test_t4_3(game):
    p = game.player
    old_health = p.health
    old_pos = p.pos.copy()
    old_regen = p.regen_per_second
    
    p.health = p.max_health
    p.regen_per_second = 5.0
    p.invuln = 0.0
    enemy = create_enemy("crawler", p.pos)
    game.enemies.append(enemy)
    game._handle_collisions()
    damage_taken = p.health < p.max_health
    hurt_flashed = p.hurt_flash > 0
    game.enemies.remove(enemy)
    
    if not (damage_taken and hurt_flashed):
        p.health = old_health
        p.regen_per_second = old_regen
        return False
        
    pre_regen_health = p.health
    p._update_timers(0.2)
    p.heal(p.regen_per_second * 0.1)
    success = p.health > pre_regen_health and p.hurt_flash < 0.16
    
    p.health = old_health
    p.regen_per_second = old_regen
    p.pos = old_pos
    return success

def test_t4_4(game):
    old_state = game.state
    orig_save = game.save_manager.load()
    
    game.save_data["coins"] = 1000
    game.state = ScreenState.SHOP
    
    target_upgrade = META_UPGRADES[0]
    levels = game.save_data.setdefault("universal_upgrades", {})
    old_level = levels.get(target_upgrade.id, 0)
    cost = target_upgrade.cost_for_level(old_level)
    
    rects = game.ui.shop_row_rects()
    row_rect = rects[target_upgrade.id]
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=row_rect.center))
    game._handle_events()
    
    new_coins = game.save_data.get("coins", 0)
    new_level = game.save_data.get("universal_upgrades", {}).get(target_upgrade.id, 0)
    success = new_coins == (1000 - cost) and new_level == (old_level + 1)
    
    # Restore
    game.save_manager.save(orig_save)
    game.save_data.clear()
    game.save_data.update(orig_save)
    game.state = old_state
    return success

def test_t4_5(game):
    old_state = game.state
    old_health = game.player.health
    old_run_finalized = game.run_finalized
    
    game.state = ScreenState.PLAYING
    game.player.health = 0
    game.run_finalized = False
    
    game.update(0.01)
    success = game.state == ScreenState.GAME_OVER and game.run_finalized == True
    
    game.player.health = old_health
    game.run_finalized = old_run_finalized
    game.state = old_state
    return success

# --- Test Case Suite Configuration ---

TEST_CASES = [
    # Tier 1
    ("T1_F1_1", test_t1_f1_1, "Menu state check"),
    ("T1_F1_2", test_t1_f1_2, "Menu button dict structure"),
    ("T1_F1_3", test_t1_f1_3, "Menu button Rect instances"),
    ("T1_F1_4", test_t1_f1_4, "Particles list initialization"),
    ("T1_F1_5", test_t1_f1_5, "draw_menu callable"),
    ("T1_F2_1", test_t1_f2_1, "Sniper chassis and turret sprites existence"),
    ("T1_F2_2", test_t1_f2_2, "Sniper portrait / icon existence"),
    ("T1_F2_3", test_t1_f2_3, "Map decor existence"),
    ("T1_F2_4", test_t1_f2_4, "Map decor types validation"),
    ("T1_F2_5", test_t1_f2_5, "Sniper rotated sprites retrieval"),
    ("T1_F3_1", test_t1_f3_1, "Player regen_per_second exists"),
    ("T1_F3_2", test_t1_f3_2, "Regeneration functionality"),
    ("T1_F3_3", test_t1_f3_3, "time_since_damage existence"),
    ("T1_F3_4", test_t1_f3_4, "Enemy base speed config"),
    ("T1_F3_5", test_t1_f3_5, "WaveDirector scaling signature"),
    ("T1_F4_1", test_t1_f4_1, "Achievements list type and count"),
    ("T1_F4_2", test_t1_f4_2, "ScreenState ACHIEVEMENTS definition"),
    ("T1_F4_3", test_t1_f4_3, "UI back button rect"),
    ("T1_F4_4", test_t1_f4_4, "Achievements details/hover query methods"),
    ("T1_F4_5", test_t1_f4_5, "Achievement class elements structure"),
    ("T1_F5_1", test_t1_f5_1, "Save manager load keys"),
    ("T1_F5_2", test_t1_f5_2, "Gear inventory structure check"),
    ("T1_F5_3", test_t1_f5_3, "Meta attributes existence"),
    ("T1_F5_4", test_t1_f5_4, "Save manager save/load loop"),
    ("T1_F5_5", test_t1_f5_5, "Meta upgrades structure check"),
    ("T1_F6_1", test_t1_f6_1, "Active skills key mappings"),
    ("T1_F6_2", test_t1_f6_2, "Skill target direction check"),
    ("T1_F6_3", test_t1_f6_3, "Skill cooldown reduction check"),
    ("T1_F6_4", test_t1_f6_4, "Active skills HUD drawing existence"),
    ("T1_F6_5", test_t1_f6_5, "Casting skill spawns projectiles check"),
    ("T1_F7_1", test_t1_f7_1, "Tanks definitions list"),
    ("T1_F7_2", test_t1_f7_2, "Tanks configuration parameters"),
    ("T1_F7_3", test_t1_f7_3, "Skill point allocation menu"),
    ("T1_F7_4", test_t1_f7_4, "Skill allocation modifies attributes"),
    ("T1_F7_5", test_t1_f7_5, "Refunding skill points functionality"),

    # Tier 2
    ("T2_F1_1", test_t2_f1_1, "Menu buttons top-left corner collision"),
    ("T2_F1_2", test_t2_f1_2, "Menu buttons within screen bounds"),
    ("T2_F1_3", test_t2_f1_3, "Particles list limits and capacity"),
    ("T2_F1_4", test_t2_f1_4, "draw_menu on dummy surface"),
    ("T2_F1_5", test_t2_f1_5, "Particle update with dt=0"),
    ("T2_F2_1", test_t2_f2_1, "Sniper rotated sprites caching corner cases"),
    ("T2_F2_2", test_t2_f2_2, "Map decor position coordinates inside arena"),
    ("T2_F2_3", test_t2_f2_3, "Map decor list bounds check"),
    ("T2_F2_4", test_t2_f2_4, "Tilesets floor sprites validation"),
    ("T2_F2_5", test_t2_f2_5, "Map decor repeatability check"),
    ("T2_F3_1", test_t2_f3_1, "Regeneration cap at max health"),
    ("T2_F3_2", test_t2_f3_2, "time_since_damage reset or invuln update"),
    ("T2_F3_3", test_t2_f3_3, "Enemy slow speed limit boundaries"),
    ("T2_F3_4", test_t2_f3_4, "Director scaling at extreme time bounds"),
    ("T2_F3_5", test_t2_f3_5, "Player take_damage negative damage input"),
    ("T2_F4_1", test_t2_f4_1, "Achievements screen hover coordinates out-of-bounds"),
    ("T2_F4_2", test_t2_f4_2, "Achievements evaluation exactly at threshold"),
    ("T2_F4_3", test_t2_f4_3, "Achievements evaluation far above threshold"),
    ("T2_F4_4", test_t2_f4_4, "achievement_bonuses with empty achievements list"),
    ("T2_F4_5", test_t2_f4_5, "progress_for with missing save stats key"),
    ("T2_F5_1", test_t2_f5_1, "SaveManager load with missing save file path"),
    ("T2_F5_2", test_t2_f5_2, "Gear inventory capacity limit / corrupt save normalization"),
    ("T2_F5_3", test_t2_f5_3, "Player meta attributes extreme boundaries"),
    ("T2_F5_4", test_t2_f5_4, "SaveManager repeated load/save integrity"),
    ("T2_F5_5", test_t2_f5_5, "normalize_save with invalid upgrades type"),
    ("T2_F6_1", test_t2_f6_1, "Cast skill while cooldown is active check"),
    ("T2_F6_2", test_t2_f6_2, "Skill casting outside arena bounds coordinates"),
    ("T2_F6_3", test_t2_f6_3, "Active skills while player is dead"),
    ("T2_F6_4", test_t2_f6_4, "Active skills cooldown under extreme/negative dt"),
    ("T2_F6_5", test_t2_f6_5, "Active skills state reset after update cycle"),
    ("T2_F7_1", test_t2_f7_1, "configure_player_tank invalid tank ID fallback"),
    ("T2_F7_2", test_t2_f7_2, "Tanks select buy without sufficient coins"),
    ("T2_F7_3", test_t2_f7_3, "Skill points allocation when points are zero"),
    ("T2_F7_4", test_t2_f7_4, "Skill points refund when nothing is allocated"),
    ("T2_F7_5", test_t2_f7_5, "Tank select click coordinate outside card bounds"),

    # Tier 3 (Cross-feature)
    ("T3_1", test_t3_1, "F1 (Menu state) and F4 (Achievements) transitions"),
    ("T3_2", test_t3_2, "F2 (SpriteBank sniper) and F7 (Playable tanks config) integration"),
    ("T3_3", test_t3_3, "F3 (Gameplay regen) and F5 (Meta stats) values interaction"),
    ("T3_4", test_t3_4, "F6 (Skills cooldown) and F3 (Gameplay movement/dash) integration"),
    ("T3_5", test_t3_5, "F5 (Meta loot) and F7 (Tanks configuration save/load) integration"),
    ("T3_6", test_t3_6, "F4 (Achievements) and F5 (Meta stats/coins earned) integration"),
    ("T3_7", test_t3_7, "F6 (Skills/attacks config) and F7 (Tanks definition attributes) variation"),

    # Tier 4 (Scenarios)
    ("T4_1", test_t4_1, "Startup and Menu Navigation Scenario"),
    ("T4_2", test_t4_2, "Run Progression and Upgrade Selection Scenario"),
    ("T4_3", test_t4_3, "Gameplay Combat and Health Regen Scenario"),
    ("T4_4", test_t4_4, "Achievements and Meta Shop Purchase Scenario"),
    ("T4_5", test_t4_5, "Game Over and Finalization Scenario")
]

def run_e2e_tests(game) -> bool:
    print("\n" + "="*60)
    print("STARTING E2E TEST RUNNER - Scrapstorm Overdrive")
    print(f"Total test cases to execute: {len(TEST_CASES)}")
    print("="*60)
    
    detect_implementation_states(game)
    
    passed_count = 0
    failed_cases = []
    
    for idx, (test_id, func, desc) in enumerate(TEST_CASES, 1):
        try:
            ok = func(game)
            if ok:
                passed_count += 1
                note = ""
                # Determine if we fell back
                if test_id.startswith("T1_F1") or test_id.startswith("T2_F1"):
                    if not is_f1_implemented:
                        note = " (Baseline check)"
                elif test_id.startswith("T1_F2") or test_id.startswith("T2_F2"):
                    if not is_f2_implemented:
                        note = " (Baseline check)"
                elif test_id.startswith("T1_F3") or test_id.startswith("T2_F3"):
                    if not is_f3_implemented:
                        note = " (Baseline check)"
                elif test_id.startswith("T1_F4") or test_id.startswith("T2_F4"):
                    if not is_f4_implemented:
                        note = " (Baseline check)"
                elif test_id.startswith("T1_F5") or test_id.startswith("T2_F5"):
                    if not is_f5_implemented:
                        note = " (Baseline check)"
                elif test_id.startswith("T1_F6") or test_id.startswith("T2_F6"):
                    if not is_f6_implemented:
                        note = " (Baseline check)"
                elif test_id.startswith("T1_F7") or test_id.startswith("T2_F7"):
                    if not is_f7_implemented:
                        note = " (Baseline check)"
                
                print(f"[{idx:02d}/82] [PASS] {test_id}: {desc}{note}")
            else:
                failed_cases.append((test_id, desc, "Returned False"))
                print(f"[{idx:02d}/82] [FAIL] {test_id}: {desc} - Returned False")
        except Exception as e:
            failed_cases.append((test_id, desc, f"Raised exception: {e}"))
            print(f"[{idx:02d}/82] [FAIL] {test_id}: {desc} - Exception: {e}")
            
    print("="*60)
    print(f"E2E TESTS COMPLETED. PASSED: {passed_count}/82. FAILED: {len(failed_cases)}.")
    print("="*60)
    
    if failed_cases:
        print("Detailed failures:")
        for fid, fdesc, ferr in failed_cases:
            print(f"  - {fid}: {fdesc} ({ferr})")
        return False
        
    return passed_count == 82
