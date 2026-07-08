"""Build transparent, gameplay-scale evolution assets from image-generation sources."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "assets" / "prompts" / "imagegen_sources"
TANK_DIR = ROOT / "assets" / "tanks" / "evolutions"
ICON_DIR = ROOT / "assets" / "icons" / "evolutions"
CONTACT_SHEET = ROOT / "assets" / "prompts" / "evolution_tank_contact_sheet.png"

FAMILIES = ("projectile", "fire", "poison", "cryo", "lightning")
DISPLAY_NAMES = {
    "projectile": "PROJECTILE",
    "fire": "FIRE",
    "poison": "POISON",
    "cryo": "CRYO",
    "lightning": "LIGHTNING",
}


def _square_subject(image: Image.Image) -> Image.Image:
    """Crop transparent padding while preserving enough clearance for rotation."""
    image = image.convert("RGBA")
    bounds = image.getchannel("A").getbbox()
    if bounds is None:
        raise ValueError("Evolution source has no visible subject")

    left, top, right, bottom = bounds
    width = right - left
    height = bottom - top
    padding = max(12, round(max(width, height) * 0.08))
    side = max(width, height) + padding * 2
    center_x = (left + right) // 2
    center_y = (top + bottom) // 2
    crop_box = (
        center_x - side // 2,
        center_y - side // 2,
        center_x - side // 2 + side,
        center_y - side // 2 + side,
    )
    return image.crop(crop_box)


def _pixel_resize(image: Image.Image, size: int) -> Image.Image:
    return image.resize((size, size), Image.Resampling.NEAREST)


def main() -> int:
    TANK_DIR.mkdir(parents=True, exist_ok=True)
    ICON_DIR.mkdir(parents=True, exist_ok=True)

    sprites: list[tuple[str, Image.Image]] = []
    for family in FAMILIES:
        source = SOURCE_DIR / f"evolution_tank_{family}_alpha.png"
        if not source.exists():
            raise FileNotFoundError(source)
        subject = _square_subject(Image.open(source))
        sprite = _pixel_resize(subject, 96)
        icon = _pixel_resize(subject, 64)
        sprite.save(TANK_DIR / f"tank_evolution_{family}.png")
        icon.save(ICON_DIR / f"icon_evolution_{family}.png")
        sprites.append((family, sprite))

    cell_w, cell_h = 182, 190
    sheet = Image.new("RGBA", (cell_w * len(sprites), cell_h), (10, 16, 25, 255))
    draw = ImageDraw.Draw(sheet)
    for index, (family, sprite) in enumerate(sprites):
        x = index * cell_w
        preview = sprite.resize((144, 144), Image.Resampling.NEAREST)
        sheet.alpha_composite(preview, (x + (cell_w - preview.width) // 2, 12))
        label = DISPLAY_NAMES[family]
        label_box = draw.textbbox((0, 0), label)
        draw.text(
            (x + (cell_w - (label_box[2] - label_box[0])) // 2, 166),
            label,
            fill=(210, 225, 240, 255),
        )
    sheet.save(CONTACT_SHEET)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
