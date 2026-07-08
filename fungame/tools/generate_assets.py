from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "sprites"
sys.path.insert(0, str(ROOT))

from src.assets import SpriteBank
from src.asset_manifest import ICON_FILENAMES, SPRITE_FILENAMES


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    pygame.init()
    pygame.display.set_mode((1, 1))
    bank = SpriteBank()
    for name, surface in bank.sprites.items():
        pygame.image.save(surface, OUT / f"{name}.png")
        if name in SPRITE_FILENAMES:
            pygame.image.save(surface, OUT / SPRITE_FILENAMES[name])
    for i, surface in enumerate(bank.tiles):
        pygame.image.save(surface, OUT / f"tile_{i}.png")
    for tileset_name, groups in bank.tilesets.items():
        for group_name, surfaces in groups.items():
            for i, surface in enumerate(surfaces):
                pygame.image.save(surface, OUT / f"tile_{tileset_name}_{group_name}_{i}.png")
    for i, surface in enumerate(bank.explosions):
        pygame.image.save(surface, OUT / f"explosion_{i}.png")
    for name, surface in bank.icons.items():
        pygame.image.save(surface, OUT / f"icon_{name}.png")
        if name in ICON_FILENAMES:
            pygame.image.save(surface, OUT / ICON_FILENAMES[name])
    pygame.quit()
    print(f"Wrote sprites to {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
