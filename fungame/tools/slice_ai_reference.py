from __future__ import annotations

from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SHEET = ROOT / "assets" / "sprites" / "ai_expanded_reference_sheet.png"
OUT = ROOT / "assets" / "sprites"


ASSETS: dict[str, tuple[tuple[int, int, int, int], tuple[int, int]]] = {
    "starter_tank.png": ((55, 54, 225, 238), (40, 40)),
    "sniper_tank.png": ((345, 48, 535, 238), (44, 40)),
    "engineer_tank.png": ((595, 55, 805, 230), (42, 42)),
    "starter_tank_chassis.png": ((55, 78, 225, 238), (42, 42)),
    "sniper_tank_chassis.png": ((405, 48, 535, 238), (42, 42)),
    "engineer_tank_chassis.png": ((595, 72, 805, 230), (42, 42)),
    "mini_turret.png": ((865, 54, 1010, 235), (28, 28)),
    "pickup_coin.png": ((1052, 86, 1155, 190), (18, 18)),
    "pickup_xp.png": ((1205, 74, 1325, 200), (16, 16)),
    "pickup_health.png": ((1362, 78, 1470, 198), (18, 18)),
    "enemy_crawler.png": ((70, 292, 190, 430), (32, 32)),
    "enemy_runner.png": ((335, 292, 490, 435), (32, 32)),
    "enemy_brute.png": ((585, 270, 825, 450), (44, 44)),
    "enemy_shooter.png": ((860, 268, 1025, 440), (38, 38)),
    "enemy_boss.png": ((1100, 250, 1515, 470), (72, 72)),
    "bullet_standard.png": ((55, 510, 220, 582), (22, 12)),
    "bullet_sniper.png": ((305, 508, 515, 582), (28, 10)),
    "bullet_turret.png": ((755, 506, 875, 585), (18, 11)),
    "bullet_enemy.png": ((925, 505, 1080, 588), (16, 16)),
    "bullet_rocket.png": ((1210, 482, 1495, 595), (26, 14)),
    "explosion_0.png": ((700, 688, 790, 775), (40, 40)),
    "explosion_1.png": ((785, 675, 885, 785), (40, 40)),
    "explosion_2.png": ((880, 668, 990, 790), (40, 40)),
    "explosion_3.png": ((980, 652, 1110, 800), (40, 40)),
    "explosion_4.png": ((1095, 640, 1250, 810), (40, 40)),
    "explosion_5.png": ((1215, 620, 1420, 830), (40, 40)),
    "icon_meta_health.png": ((32, 822, 145, 948), (28, 28)),
    "icon_meta_speed.png": ((162, 822, 280, 948), (28, 28)),
    "icon_meta_fire_rate.png": ((294, 822, 412, 948), (28, 28)),
    "icon_meta_damage.png": ((425, 822, 540, 948), (28, 28)),
    "icon_meta_projectile_speed.png": ((555, 822, 672, 948), (28, 28)),
    "icon_meta_xp.png": ((1205, 74, 1325, 200), (28, 28)),
    "icon_meta_coin.png": ((1052, 86, 1155, 190), (28, 28)),
    "icon_meta_pickup_radius.png": ((1082, 850, 1138, 918), (28, 28)),
}


BARRELS: dict[str, tuple[tuple[int, int, int, int], tuple[int, int], int, int, int, float]] = {
    "starter_tank_turret.png": ((82, 520, 214, 574), (56, 56), 30, 13, 3, 0),
    "sniper_tank_turret.png": ((305, 508, 515, 582), (64, 56), 44, 10, 4, 0),
    "engineer_tank_turret.png": ((755, 506, 875, 585), (56, 56), 24, 12, 4, 0),
    "turret_rocket.png": ((1210, 482, 1495, 595), (64, 56), 38, 17, 5, 0),
}


ALIASES = {
    "starter_tank_icon.png": "starter_tank.png",
    "sniper_tank_icon.png": "sniper_tank.png",
    "engineer_tank_icon.png": "engineer_tank.png",
    "icon_meta_turret.png": "mini_turret.png",
    "turret_starter.png": "starter_tank_turret.png",
    "turret_sniper.png": "sniper_tank_turret.png",
    "turret_engineer.png": "engineer_tank_turret.png",
    "turret_minigun.png": "starter_tank_turret.png",
    "turret_twin.png": "engineer_tank_turret.png",
}


def remove_key(image: Image.Image, key: tuple[int, int, int] | None = None) -> Image.Image:
    rgba = image.convert("RGBA")
    key = key or rgba.getpixel((0, 0))[:3]
    pixels = rgba.load()
    for y in range(rgba.height):
        for x in range(rgba.width):
            r, g, b, a = pixels[x, y]
            dist = abs(r - key[0]) + abs(g - key[1]) + abs(b - key[2])
            is_bright_green_backdrop = g > 225 and r < 70 and b < 70
            if dist < 45 or is_bright_green_backdrop:
                pixels[x, y] = (r, g, b, 0)
    return rgba


def fit_to_canvas(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    alpha = image.getchannel("A")
    bbox = alpha.getbbox()
    if bbox:
        image = image.crop(bbox)
    max_w = max(1, size[0] - 2)
    max_h = max(1, size[1] - 2)
    scale = min(max_w / image.width, max_h / image.height)
    resized = image.resize((max(1, int(image.width * scale)), max(1, int(image.height * scale))), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", size, (0, 0, 0, 0))
    canvas.alpha_composite(resized, ((size[0] - resized.width) // 2, (size[1] - resized.height) // 2))
    return canvas


def turret_sprite(image: Image.Image, size: tuple[int, int], rotation: float, key: tuple[int, int, int]) -> Image.Image:
    keyed = remove_key(image, key)
    alpha = keyed.getchannel("A")
    bbox = alpha.getbbox()
    if bbox:
        keyed = keyed.crop(bbox)
    if rotation:
        keyed = keyed.rotate(rotation, resample=Image.Resampling.BICUBIC, expand=True)
    return fit_to_canvas(keyed, size)


def barrel_sprite(
    image: Image.Image,
    size: tuple[int, int],
    length: int,
    max_height: int,
    anchor_back: int,
    rotation: float,
    key: tuple[int, int, int],
) -> Image.Image:
    keyed = remove_key(image, key)
    alpha = keyed.getchannel("A")
    bbox = alpha.getbbox()
    if bbox:
        keyed = keyed.crop(bbox)
    if rotation:
        keyed = keyed.rotate(rotation, resample=Image.Resampling.BICUBIC, expand=True)
    scale = min(length / keyed.width, max_height / keyed.height)
    resized = keyed.resize(
        (max(1, int(keyed.width * scale)), max(1, int(keyed.height * scale))),
        Image.Resampling.LANCZOS,
    )
    canvas = Image.new("RGBA", size, (0, 0, 0, 0))
    x = size[0] // 2 - anchor_back
    y = (size[1] - resized.height) // 2
    canvas.alpha_composite(resized, (x, y))
    return canvas


def main() -> int:
    if not SHEET.exists():
        raise FileNotFoundError(SHEET)
    sheet = Image.open(SHEET).convert("RGBA")
    sheet_key = sheet.getpixel((0, 0))[:3]
    OUT.mkdir(parents=True, exist_ok=True)
    for filename, (box, size) in ASSETS.items():
        sprite = fit_to_canvas(remove_key(sheet.crop(box), sheet_key), size)
        sprite.save(OUT / filename)
    for filename, (box, size, length, max_height, anchor_back, rotation) in BARRELS.items():
        barrel_sprite(sheet.crop(box), size, length, max_height, anchor_back, rotation, sheet_key).save(OUT / filename)
    for alias, source in ALIASES.items():
        Image.open(OUT / source).save(OUT / alias)
    print(f"Sliced {len(ASSETS) + len(BARRELS) + len(ALIASES)} AI assets into {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
