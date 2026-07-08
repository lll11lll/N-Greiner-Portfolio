from __future__ import annotations

"""Slice the generated Unlocks/Research sheets into alpha-safe UI icons."""

from math import ceil
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "assets" / "prompts" / "imagegen_sources"
UNLOCK_DIR = ROOT / "assets" / "icons" / "unlocks"
RESEARCH_DIR = ROOT / "assets" / "icons" / "research"
UI_DIR = ROOT / "assets" / "ui" / "progression"
CONTACT_SHEET = ROOT / "assets" / "prompts" / "research_unlocks_contact_sheet.png"

UNLOCKS = (
    "elemental_fusion_pack",
    "ability_variant_pack",
    "elemental_elites",
    "relic_prototypes",
    "elite_contract_board",
    "surge_contract_license",
    "hazard_modifiers",
    "anomaly_routes",
)
RESEARCH = (
    "flame_injector",
    "cryo_amplifier",
    "toxin_pressurizer",
    "overcharge_coil",
    "ability_augments",
    "contract_tech",
    "gear_lab",
    "evolution_lab",
)
CONTRACT_TECH_SOURCE = "research_unlocks_contract_tech_pack_source.png"


def remove_magenta(image: Image.Image) -> Image.Image:
    image = image.convert("RGBA")
    pixels = image.load()
    for y in range(image.height):
        for x in range(image.width):
            red, green, blue, alpha = pixels[x, y]
            if red > 185 and blue > 185 and green < 105:
                pixels[x, y] = (red, green, blue, 0)
            elif alpha:
                pixels[x, y] = (red, green, blue, 255)
    return image


def fit_icon(cell: Image.Image, size: int = 96) -> Image.Image:
    cell = remove_magenta(cell)
    bounds = cell.getchannel("A").getbbox()
    if bounds is None:
        return Image.new("RGBA", (size, size), (0, 0, 0, 0))
    subject = cell.crop(bounds)
    max_side = int(size * 0.82)
    subject.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
    output = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    output.alpha_composite(subject, ((size - subject.width) // 2, (size - subject.height) // 2))
    return output


def slice_sheet(source_name: str, names: tuple[str, ...], output_dir: Path) -> list[Path]:
    source = Image.open(SOURCE_DIR / source_name).convert("RGBA")
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for index, name in enumerate(names):
        col = index % 4
        row = index // 4
        left = round(col * source.width / 4)
        top = round(row * source.height / 2)
        right = round((col + 1) * source.width / 4)
        bottom = round((row + 1) * source.height / 2)
        icon = fit_icon(source.crop((left, top, right, bottom)))
        path = output_dir / f"icon_{name}.png"
        icon.save(path)
        written.append(path)
    return written


def build_contact_sheet(paths: list[Path]) -> None:
    cell = 132
    columns = 4
    rows = ceil(len(paths) / columns)
    sheet = Image.new("RGBA", (cell * columns, cell * rows), (11, 15, 24, 255))
    draw = ImageDraw.Draw(sheet)
    for index, path in enumerate(paths):
        icon = Image.open(path).convert("RGBA")
        column = index % columns
        row = index // columns
        x = column * cell + (cell - icon.width) // 2
        y = row * cell + 12
        draw.rectangle((column * cell + 4, row * cell + 4, (column + 1) * cell - 5, (row + 1) * cell - 5), outline=(54, 76, 104, 255), width=2)
        sheet.alpha_composite(icon, (x, y))
    CONTACT_SHEET.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(CONTACT_SHEET)


def main() -> int:
    unlock_paths = slice_sheet("research_unlocks_unlocks_source.png", UNLOCKS, UNLOCK_DIR)
    contract_tech_pack = fit_icon(Image.open(SOURCE_DIR / CONTRACT_TECH_SOURCE))
    contract_tech_path = UNLOCK_DIR / "icon_contract_tech_pack.png"
    contract_tech_pack.save(contract_tech_path)
    research_paths = slice_sheet("research_unlocks_research_source.png", RESEARCH, RESEARCH_DIR)
    UI_DIR.mkdir(parents=True, exist_ok=True)
    accent = Image.open(unlock_paths[3]).convert("RGBA").resize((144, 144), Image.Resampling.LANCZOS)
    accent.save(UI_DIR / "tooltip_relic_accent.png")
    build_contact_sheet(unlock_paths + [contract_tech_path] + research_paths)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
