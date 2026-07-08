from __future__ import annotations

"""Slice generated City and Jungle terrain atlases into runtime game assets."""

from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets" / "prompts" / "imagegen_sources"
PROMPTS = ROOT / "assets" / "prompts"

CITY_TILES = (
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
)
CITY_PROPS = (
    "prop_city_barrier_01.png",
    "prop_city_barrier_02.png",
    "prop_city_roadblock.png",
    "prop_city_broken_terminal.png",
    "prop_city_street_sign_broken.png",
    "prop_city_neon_sign_small.png",
    "prop_city_utility_box.png",
    "prop_city_debris_pile.png",
    "prop_city_wrecked_car_small.png",
    "prop_city_scrap_barricade.png",
)
CITY_LANDMARKS = (
    "landmark_city_broken_bus.png",
    "landmark_city_billboard_wreck.png",
    "landmark_city_power_node.png",
    "landmark_city_collapsed_overpass_piece.png",
)
JUNGLE_TILES = (
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
)
JUNGLE_PROPS = (
    "prop_jungle_vine_cluster.png",
    "prop_jungle_bush_cluster.png",
    "prop_jungle_root_tangle.png",
    "prop_jungle_broken_ruin_piece.png",
    "prop_jungle_overgrown_machine.png",
    "prop_jungle_scrap_pile_mossy.png",
    "prop_jungle_fern_cluster.png",
    "prop_jungle_stone_shard.png",
    "prop_jungle_small_relay_ruin.png",
    "prop_jungle_vine_barrier.png",
)
JUNGLE_LANDMARKS = (
    "landmark_jungle_root_wrapped_wreck.png",
    "landmark_jungle_relay_ruin.png",
    "landmark_jungle_rock_formation.png",
    "landmark_jungle_overgrown_outpost.png",
)


def atlas_cell(image: Image.Image, columns: int, rows: int, index: int) -> Image.Image:
    column, row = index % columns, index // columns
    return image.crop((
        round(column * image.width / columns),
        round(row * image.height / rows),
        round((column + 1) * image.width / columns),
        round((row + 1) * image.height / rows),
    ))


def terrain_tile(cell: Image.Image) -> Image.Image:
    return cell.convert("RGBA").resize((32, 32), Image.Resampling.LANCZOS)


def transparent_asset(cell: Image.Image, size: tuple[int, int]) -> Image.Image:
    image = cell.convert("RGBA")
    bounds = image.getchannel("A").getbbox()
    if bounds is None:
        return Image.new("RGBA", size, (0, 0, 0, 0))
    subject = image.crop(bounds)
    subject.thumbnail((int(size[0] * 0.88), int(size[1] * 0.88)), Image.Resampling.LANCZOS)
    output = Image.new("RGBA", size, (0, 0, 0, 0))
    output.alpha_composite(subject, ((size[0] - subject.width) // 2, (size[1] - subject.height) // 2))
    return output


def write_atlas(source_name: str, names: tuple[str, ...], columns: int, rows: int, output: Path, size: tuple[int, int], transparent: bool) -> list[Path]:
    source = Image.open(SOURCE / source_name).convert("RGBA")
    output.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for index, name in enumerate(names):
        image = atlas_cell(source, columns, rows, index)
        rendered = transparent_asset(image, size) if transparent else terrain_tile(image)
        path = output / name
        rendered.save(path)
        paths.append(path)
    return paths


def contact_sheet(paths: list[Path], output: Path, columns: int, size: tuple[int, int]) -> None:
    width, height = size
    rows = (len(paths) + columns - 1) // columns
    image = Image.new("RGBA", (columns * width, rows * height), (11, 15, 24, 255))
    draw = ImageDraw.Draw(image)
    for index, path in enumerate(paths):
        asset = Image.open(path).convert("RGBA")
        asset.thumbnail((width - 14, height - 14), Image.Resampling.LANCZOS)
        x, y = (index % columns) * width, (index // columns) * height
        draw.rectangle((x + 3, y + 3, x + width - 4, y + height - 4), outline=(54, 76, 104, 255), width=2)
        image.alpha_composite(asset, (x + (width - asset.width) // 2, y + (height - asset.height) // 2))
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output)


def main() -> int:
    city = ROOT / "assets" / "environment" / "city"
    jungle = ROOT / "assets" / "environment" / "jungle"
    city_paths = []
    city_paths += write_atlas("city_tiles_source.png", CITY_TILES, 4, 3, city, (32, 32), False)
    city_paths += write_atlas("city_props_source_alpha.png", CITY_PROPS, 5, 2, city, (48, 48), True)
    city_paths += write_atlas("city_landmarks_source_alpha.png", CITY_LANDMARKS, 2, 2, city, (192, 144), True)
    jungle_paths = []
    jungle_paths += write_atlas("jungle_tiles_source.png", JUNGLE_TILES, 4, 3, jungle, (32, 32), False)
    jungle_paths += write_atlas("jungle_props_source_alpha.png", JUNGLE_PROPS, 5, 2, jungle, (48, 48), True)
    jungle_paths += write_atlas("jungle_landmarks_source_alpha.png", JUNGLE_LANDMARKS, 2, 2, jungle, (192, 144), True)
    contact_sheet(city_paths, PROMPTS / "city_tileset_contact_sheet.png", 6, (112, 96))
    contact_sheet(jungle_paths, PROMPTS / "jungle_tileset_contact_sheet.png", 6, (112, 96))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
