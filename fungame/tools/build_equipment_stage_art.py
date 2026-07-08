from __future__ import annotations

"""Slice chroma-keyed generated equipment, skill-tree, and landmark sheets."""

from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets" / "prompts" / "imagegen_sources"
ASSETS = ROOT / "assets"
PROMPTS = ASSETS / "prompts"

EQUIPMENT = {
    "weapons": ("scrap_repeater", "rail_lance", "furnace_cannon", "arc_splitter", "venom_mortar"),
    "armor": ("reinforced_plating", "reactive_shell", "cryo_insulation", "volatile_hull", "conductive_chassis"),
    "trinkets": ("salvage_beacon", "shock_capacitor", "lucky_scrap_charm", "focus_lens", "emergency_repair_module"),
    "tracks": ("reinforced_treads", "drift_treads", "magnet_tracks", "shock_absorber_wheels", "siege_tracks", "scout_treads"),
}
SKILL_ICONS = ("strength", "dexterity", "vitality", "tech", "focus", "luck")
LANDMARKS = {
    "scrap_outskirts": ("crane", "tank_hulk", "conveyor", "mech_torso"),
    "desert_wrecks": ("artillery", "fuel_tank", "comms_tower", "bunker_hatch"),
    "frozen_base": ("relay_spire", "coolant_tower", "generator", "cryo_chamber"),
    "shattered_metro": ("metro_bus", "billboard", "overpass", "power_station"),
    "overgrowth_basin": ("root_wreck", "relay_ruin", "vine_machine", "moss_tank"),
}


def fit(cell: Image.Image, size: tuple[int, int]) -> Image.Image:
    cell = cell.convert("RGBA")
    bounds = cell.getchannel("A").getbbox()
    if bounds is None:
        return Image.new("RGBA", size, (0, 0, 0, 0))
    subject = cell.crop(bounds)
    max_width, max_height = int(size[0] * 0.88), int(size[1] * 0.88)
    subject.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
    result = Image.new("RGBA", size, (0, 0, 0, 0))
    result.alpha_composite(subject, ((size[0] - subject.width) // 2, (size[1] - subject.height) // 2))
    return result


def cell(image: Image.Image, columns: int, rows: int, index: int) -> Image.Image:
    column, row = index % columns, index // columns
    left = round(column * image.width / columns)
    top = round(row * image.height / rows)
    right = round((column + 1) * image.width / columns)
    bottom = round((row + 1) * image.height / rows)
    return image.crop((left, top, right, bottom))


def read_alpha(name: str) -> Image.Image:
    return Image.open(SOURCE / name).convert("RGBA")


def write_equipment() -> list[Path]:
    sheet = read_alpha("equipment_icons_source_alpha.png")
    paths: list[Path] = []
    rows = tuple(EQUIPMENT.items())
    for row, (folder, names) in enumerate(rows):
        output = ASSETS / "icons" / "equipment" / folder
        output.mkdir(parents=True, exist_ok=True)
        for column, name in enumerate(names):
            path = output / f"icon_{name}.png"
            fit(cell(sheet, 6, 4, row * 6 + column), (96, 96)).save(path)
            paths.append(path)
    return paths


def write_skill_icons() -> list[Path]:
    sheet = read_alpha("skill_tree_icons_source_alpha.png")
    output = ASSETS / "icons" / "skill_tree"
    output.mkdir(parents=True, exist_ok=True)
    paths = []
    for index, name in enumerate(SKILL_ICONS):
        path = output / f"icon_{name}.png"
        fit(cell(sheet, 3, 2, index), (112, 112)).save(path)
        paths.append(path)
    return paths


def write_landmarks() -> list[Path]:
    output = ASSETS / "environment" / "landmarks"
    output.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for stage_id, names in LANDMARKS.items():
        sheet = read_alpha(f"landmarks_{stage_id}_source_alpha.png")
        for index, name in enumerate(names):
            path = output / f"landmark_{stage_id}_{index + 1:02d}_{name}.png"
            fit(cell(sheet, 2, 2, index), (192, 144)).save(path)
            paths.append(path)
    return paths


def contact_sheet(paths: list[Path], out: Path, columns: int, cell_size: tuple[int, int]) -> None:
    width, height = cell_size
    rows = (len(paths) + columns - 1) // columns
    image = Image.new("RGBA", (columns * width, rows * height), (11, 15, 24, 255))
    draw = ImageDraw.Draw(image)
    for index, path in enumerate(paths):
        icon = Image.open(path).convert("RGBA")
        icon.thumbnail((width - 18, height - 18), Image.Resampling.LANCZOS)
        x, y = (index % columns) * width, (index // columns) * height
        draw.rectangle((x + 4, y + 4, x + width - 5, y + height - 5), outline=(54, 76, 104, 255), width=2)
        image.alpha_composite(icon, (x + (width - icon.width) // 2, y + (height - icon.height) // 2))
    out.parent.mkdir(parents=True, exist_ok=True)
    image.save(out)


def main() -> int:
    equipment = write_equipment()
    skills = write_skill_icons()
    landmarks = write_landmarks()
    contact_sheet(equipment, PROMPTS / "equipment_contact_sheet.png", 6, (120, 120))
    contact_sheet(skills, PROMPTS / "skill_tree_contact_sheet.png", 3, (156, 156))
    contact_sheet(landmarks, PROMPTS / "stage_landmarks_contact_sheet.png", 4, (220, 170))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
