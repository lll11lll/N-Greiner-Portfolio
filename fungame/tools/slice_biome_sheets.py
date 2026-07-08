from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "assets" / "prompts" / "imagegen_sources"
OUT_DIR = ROOT / "assets" / "environment"


@dataclass(frozen=True)
class AssetSpec:
    filename: str
    size: tuple[int, int]


@dataclass(frozen=True)
class SheetSpec:
    source: str
    folder: str
    columns: int
    rows: int
    assets: tuple[AssetSpec, ...]


SHEETS: tuple[SheetSpec, ...] = (
    SheetSpec(
        source="scrapyard_outskirts_sheet.png",
        folder="scrapyard_outskirts",
        columns=4,
        rows=4,
        assets=(
            AssetSpec("tile_floor_01.png", (32, 32)),
            AssetSpec("tile_floor_02.png", (32, 32)),
            AssetSpec("tile_floor_03.png", (32, 32)),
            AssetSpec("tile_wall.png", (32, 32)),
            AssetSpec("tile_border.png", (32, 32)),
            AssetSpec("tile_path_worn_ground.png", (32, 32)),
            AssetSpec("prop_scrap_pile_01.png", (48, 48)),
            AssetSpec("prop_scrap_pile_02.png", (48, 48)),
            AssetSpec("prop_metal_crate.png", (40, 40)),
            AssetSpec("prop_broken_pipe.png", (48, 48)),
            AssetSpec("prop_hazard_barrier.png", (64, 48)),
            AssetSpec("prop_broken_machine.png", (64, 64)),
            AssetSpec("prop_neon_sign_small.png", (48, 48)),
            AssetSpec("prop_rusted_tank_hulk.png", (64, 64)),
            AssetSpec("prop_wrecked_turret.png", (64, 64)),
        ),
    ),
    SheetSpec(
        source="desert_wasteland_sheet.png",
        folder="desert_wasteland",
        columns=4,
        rows=3,
        assets=(
            AssetSpec("tile_sand_floor_01.png", (32, 32)),
            AssetSpec("tile_sand_floor_02.png", (32, 32)),
            AssetSpec("tile_cracked_earth.png", (32, 32)),
            AssetSpec("tile_rusted_wall.png", (32, 32)),
            AssetSpec("tile_border.png", (32, 32)),
            AssetSpec("prop_rusted_wreckage.png", (64, 64)),
            AssetSpec("prop_desert_barricade.png", (64, 48)),
            AssetSpec("prop_dusty_scrap_pile.png", (48, 48)),
            AssetSpec("prop_broken_sign.png", (48, 48)),
            AssetSpec("prop_buried_pipe.png", (48, 48)),
        ),
    ),
    SheetSpec(
        source="frozen_tech_base_sheet.png",
        folder="frozen_tech_base",
        columns=4,
        rows=3,
        assets=(
            AssetSpec("tile_ice_floor_01.png", (32, 32)),
            AssetSpec("tile_ice_floor_02.png", (32, 32)),
            AssetSpec("tile_frozen_panel.png", (32, 32)),
            AssetSpec("tile_tech_wall.png", (32, 32)),
            AssetSpec("tile_border.png", (32, 32)),
            AssetSpec("prop_frozen_pipe.png", (48, 48)),
            AssetSpec("prop_damaged_machine.png", (64, 64)),
            AssetSpec("prop_ice_crate.png", (48, 48)),
            AssetSpec("prop_snowdrift_scrap.png", (48, 48)),
            AssetSpec("prop_frozen_barrier.png", (64, 48)),
        ),
    ),
)


def remove_key(image: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
    pixels = rgba.load()
    for y in range(rgba.height):
        for x in range(rgba.width):
            r, g, b, a = pixels[x, y]
            is_key_core = g > 175 and r < 110 and b < 120
            is_key_fringe = g > 95 and g > r * 1.28 and g > b * 1.22
            is_dark_key_remnant = g > 45 and r < 46 and b < 46
            if is_key_core or is_key_fringe or is_dark_key_remnant:
                pixels[x, y] = (r, g, b, 0)
    return rgba


def fit_to_canvas(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    keyed = remove_key(image)
    bbox = keyed.getchannel("A").getbbox()
    if bbox is not None:
        keyed = keyed.crop(bbox)
    else:
        keyed = Image.new("RGBA", (1, 1), (0, 0, 0, 0))

    max_w = max(1, size[0] - 2)
    max_h = max(1, size[1] - 2)
    scale = min(max_w / keyed.width, max_h / keyed.height)
    resized = keyed.resize(
        (max(1, int(keyed.width * scale)), max(1, int(keyed.height * scale))),
        Image.Resampling.LANCZOS,
    )
    canvas = Image.new("RGBA", size, (0, 0, 0, 0))
    canvas.alpha_composite(resized, ((size[0] - resized.width) // 2, (size[1] - resized.height) // 2))
    return canvas


def slice_sheet(sheet: SheetSpec) -> int:
    source_path = SOURCE_DIR / sheet.source
    image = Image.open(source_path).convert("RGBA")
    out_folder = OUT_DIR / sheet.folder
    out_folder.mkdir(parents=True, exist_ok=True)

    cell_w = image.width / sheet.columns
    cell_h = image.height / sheet.rows
    written = 0
    for index, asset in enumerate(sheet.assets):
        col = index % sheet.columns
        row = index // sheet.columns
        box = (
            int(round(col * cell_w)),
            int(round(row * cell_h)),
            int(round((col + 1) * cell_w)),
            int(round((row + 1) * cell_h)),
        )
        sprite = fit_to_canvas(image.crop(box), asset.size)
        sprite.save(out_folder / asset.filename)
        written += 1
    return written


def main() -> int:
    total = 0
    for sheet in SHEETS:
        total += slice_sheet(sheet)
    print(f"Sliced {total} biome assets into {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
