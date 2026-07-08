from __future__ import annotations

import math
import os
from pathlib import Path

import pygame

from .asset_manifest import ICON_FALLBACK_PATHS, ICON_FILENAMES, LEVELUP_ICON_DIRECTORY, MENU_FILENAMES, SPRITE_FALLBACK_PATHS, SPRITE_FILENAMES
from .constants import PALETTE, TILE_SIZE


def _surf(size: tuple[int, int]) -> pygame.Surface:
    return pygame.Surface(size, pygame.SRCALPHA)


def _rect(surface: pygame.Surface, color: tuple[int, int, int], rect: tuple[int, int, int, int]) -> None:
    pygame.draw.rect(surface, color, pygame.Rect(rect))


def _load_image(path: Path) -> pygame.Surface:
    return pygame.image.load(path.as_posix()).convert_alpha()


def _poly(surface: pygame.Surface, color: tuple[int, int, int], points: list[tuple[int, int]]) -> None:
    pygame.draw.polygon(surface, color, points)


def _outline_rect(
    surface: pygame.Surface,
    rect: tuple[int, int, int, int],
    fill: tuple[int, int, int],
    outline: tuple[int, int, int] | None = None,
    width: int = 2,
) -> None:
    outline = outline or PALETTE["outline"]
    pygame.draw.rect(surface, outline, pygame.Rect(rect))
    inner = pygame.Rect(rect).inflate(-width * 2, -width * 2)
    if inner.width > 0 and inner.height > 0:
        pygame.draw.rect(surface, fill, inner)


class SpriteBank:
    """Creates cohesive pixel sprites at startup and caches rotated variants."""

    def __init__(self) -> None:
        self.sprites: dict[str, pygame.Surface] = {}
        self.icons: dict[str, pygame.Surface] = {}
        self.menu: dict[str, pygame.Surface] = {}
        self.missing_assets: list[str] = []
        self.loaded_external_assets: list[str] = []
        self.tiles: list[pygame.Surface] = []
        self.explosions: list[pygame.Surface] = []
        self._rotation_cache: dict[tuple, pygame.Surface] = {}
        self._build()

    def _build(self) -> None:
        self.sprites = {
            "player": self._player(),
            "chassis_starter": self._tank_chassis(PALETTE["cyan"]),
            "chassis_sniper": self._tank_chassis(PALETTE["amber"], slim=True),
            "chassis_engineer": self._tank_chassis(PALETTE["green"], pods=True),
            "turret_starter": self._tank_turret(PALETTE["cyan"]),
            "turret_sniper": self._tank_turret(PALETTE["amber"], long=True),
            "turret_engineer": self._tank_turret(PALETTE["green"], stub=True),
            "turret_minigun": self._tank_turret(PALETTE["amber"], barrels=True),
            "turret_rocket": self._tank_turret(PALETTE["magenta"], rocket=True),
            "turret_twin": self._tank_turret(PALETTE["green"], twin=True),
            "player_sniper": self._sniper_player(),
            "player_engineer": self._engineer_player(),
            "player_minigun": self._player(glow=PALETTE["amber"], barrels=True),
            "player_rocket": self._player(glow=PALETTE["magenta"], rocket=True),
            "player_twin": self._player(glow=PALETTE["green"], twin=True),
            "player_flame": self._player(glow=PALETTE["amber"], rocket=True),
            "player_cryo": self._player(glow=PALETTE["cyan"]),
            "player_poison": self._player(glow=PALETTE["green"]),
            "player_lightning": self._player(glow=PALETTE["amber"], twin=True),
            "crawler": self._crawler(),
            "runner": self._runner(),
            "brute": self._brute(),
            "shooter": self._shooter(),
            "boss": self._boss(),
            "bullet": self._bullet(PALETTE["cyan"], 18, 8),
            "sniper_bullet": self._bullet(PALETTE["amber"], 24, 6),
            "bullet_rocket": self._bullet(PALETTE["amber"], 22, 10, fins=True),
            "turret_bullet": self._bullet(PALETTE["green"], 14, 7),
            "enemy_bullet": self._enemy_bullet(),
            "xp": self._xp_pickup(),
            "coin": self._coin_pickup(),
            "health": self._health_pickup(),
            "shield": self._shield_drone(),
            "mini_turret": self._mini_turret(),
            "mine": self._mine(),
            "chest": self._chest_sprite(),
            "chest_basic": self._chest_sprite(boss=False),
            "chest_boss": self._chest_sprite(boss=True),
            "bullet_arrow": self._bullet(PALETTE["cyan"], 16, 6),
        }
        self.sprites["tank_icon_starter"] = self._tank_icon("player", PALETTE["cyan"])
        self.sprites["tank_icon_sniper"] = self._tank_icon("player_sniper", PALETTE["amber"])
        self.sprites["tank_icon_engineer"] = self._tank_icon("player_engineer", PALETTE["green"])
        self.sprites["tank_icon_twin"] = self._tank_icon("player_twin", PALETTE["green"])
        self.sprites["tank_icon_flame"] = self._tank_icon("player_rocket", PALETTE["magenta"])
        self.sprites["tank_icon_cryo"] = self._tank_icon("player_cryo", PALETTE["cyan"])
        self.sprites["tank_icon_poison"] = self._tank_icon("player_poison", PALETTE["green"])
        self.sprites["tank_icon_lightning"] = self._tank_icon("player_lightning", PALETTE["amber"])
        self.sprites["sniper_portrait"] = self._sniper_portrait()
        self.tilesets = {
            "scrap": self._tileset("scrap"),
            "desert": self._tileset("desert"),
            "frozen": self._tileset("frozen"),
            "city": self._tileset("city"),
            "jungle": self._tileset("jungle"),
        }
        self.landmarks: dict[str, list[pygame.Surface]] = {}
        self.tiles = self.tilesets["scrap"]["floor"]
        self.explosions = [self._explosion(i) for i in range(7)]
        self.icons = self._icons()
        self._load_external_assets()

    def rotated(self, key: str, direction: pygame.Vector2, base_angle: float = 0.0) -> pygame.Surface:
        if direction.length_squared() == 0:
            angle = 0
        else:
            angle = int(round((math.degrees(math.atan2(-direction.y, direction.x)) - base_angle) / 5) * 5)
        cache_key = (key, angle)
        if cache_key not in self._rotation_cache:
            self._rotation_cache[cache_key] = pygame.transform.rotate(self.sprites[key], angle)
        return self._rotation_cache[cache_key]

    def scaled_rotated(self, key: str, direction: pygame.Vector2, scale: float, base_angle: float = 0.0) -> pygame.Surface:
        if direction.length_squared() == 0:
            angle = 0
        else:
            angle = int(round((math.degrees(math.atan2(-direction.y, direction.x)) - base_angle) / 5) * 5)
        scale_key = round(scale, 2)
        cache_key = (key, angle, scale_key)
        if cache_key not in self._rotation_cache:
            rotated = pygame.transform.rotate(self.sprites[key], angle)
            if scale_key != 1.0:
                w = max(4, int(rotated.get_width() * scale_key))
                h = max(4, int(rotated.get_height() * scale_key))
                self._rotation_cache[cache_key] = pygame.transform.scale(rotated, (w, h))
            else:
                self._rotation_cache[cache_key] = rotated
        return self._rotation_cache[cache_key]

    def _player(
        self,
        glow: tuple[int, int, int] = PALETTE["cyan"],
        barrels: bool = False,
        rocket: bool = False,
        twin: bool = False,
    ) -> pygame.Surface:
        s = _surf((40, 40))
        _outline_rect(s, (5, 11, 8, 18), (35, 40, 50))
        _outline_rect(s, (8, 8, 18, 24), (48, 56, 70))
        _outline_rect(s, (24, 15, 12, 8), (54, 64, 78))
        _rect(s, glow, (15, 15, 7, 7))
        _rect(s, PALETTE["metal_hi"], (10, 10, 9, 3))
        _rect(s, PALETTE["magenta"], (9, 27, 4, 3))
        if barrels:
            _rect(s, PALETTE["outline"], (31, 11, 7, 4))
            _rect(s, PALETTE["outline"], (31, 25, 7, 4))
            _rect(s, glow, (32, 12, 5, 2))
            _rect(s, glow, (32, 26, 5, 2))
        if rocket:
            _poly(s, PALETTE["outline"], [(28, 9), (38, 20), (28, 31)])
            _poly(s, PALETTE["amber"], [(29, 12), (35, 20), (29, 28)])
        if twin:
            _outline_rect(s, (19, 4, 7, 9), (42, 52, 60))
            _outline_rect(s, (19, 27, 7, 9), (42, 52, 60))
            _rect(s, glow, (22, 5, 3, 7))
            _rect(s, glow, (22, 28, 3, 7))
        return s

    def _tank_chassis(self, glow: tuple[int, int, int], slim: bool = False, pods: bool = False) -> pygame.Surface:
        s = _surf((42, 42))
        if slim:
            _outline_rect(s, (7, 12, 10, 18), (32, 38, 48))
            _outline_rect(s, (14, 9, 16, 24), (43, 50, 62))
            _rect(s, glow, (19, 16, 5, 6))
        else:
            _outline_rect(s, (5, 11, 9, 20), (35, 40, 50))
            _outline_rect(s, (10, 8, 20, 26), (48, 56, 70))
            _rect(s, glow, (17, 16, 7, 7))
        if pods:
            _outline_rect(s, (27, 4, 8, 8), (41, 58, 50))
            _outline_rect(s, (27, 30, 8, 8), (41, 58, 50))
            _rect(s, PALETTE["amber"], (10, 7, 6, 4))
            _rect(s, PALETTE["amber"], (10, 31, 6, 4))
        _rect(s, PALETTE["metal_hi"], (12, 10, 8, 3))
        _rect(s, PALETTE["magenta"], (10, 29, 4, 3))
        return s

    def _tank_turret(
        self,
        glow: tuple[int, int, int],
        long: bool = False,
        stub: bool = False,
        barrels: bool = False,
        rocket: bool = False,
        twin: bool = False,
    ) -> pygame.Surface:
        s = _surf((56, 56))
        _outline_rect(s, (21, 21, 14, 14), (45, 52, 64))
        if long:
            _outline_rect(s, (32, 25, 22, 6), (64, 69, 76))
            _rect(s, glow, (48, 27, 5, 2))
        elif rocket:
            _poly(s, PALETTE["outline"], [(32, 18), (54, 28), (32, 38)])
            _poly(s, glow, [(34, 21), (49, 28), (34, 35)])
        elif twin:
            _outline_rect(s, (31, 19, 18, 5), (54, 64, 78))
            _outline_rect(s, (31, 32, 18, 5), (54, 64, 78))
            _rect(s, glow, (45, 21, 4, 2))
            _rect(s, glow, (45, 34, 4, 2))
        elif barrels:
            _outline_rect(s, (31, 20, 19, 5), (54, 64, 78))
            _outline_rect(s, (31, 31, 19, 5), (54, 64, 78))
            _rect(s, glow, (45, 22, 5, 2))
            _rect(s, glow, (45, 33, 5, 2))
        elif stub:
            _outline_rect(s, (31, 24, 14, 8), (51, 62, 67))
            _rect(s, glow, (40, 27, 4, 2))
        else:
            _outline_rect(s, (31, 24, 17, 8), (54, 64, 78))
            _rect(s, glow, (43, 27, 4, 2))
        _rect(s, glow, (25, 25, 6, 6))
        return s

    def _sniper_player(self) -> pygame.Surface:
        s = _surf((44, 40))
        _outline_rect(s, (5, 12, 8, 16), (32, 38, 48))
        _outline_rect(s, (10, 9, 17, 22), (43, 50, 62))
        _outline_rect(s, (24, 17, 17, 5), (61, 65, 72))
        _rect(s, PALETTE["amber"], (16, 15, 6, 6))
        _rect(s, PALETTE["cyan"], (37, 18, 5, 2))
        _poly(s, PALETTE["outline"], [(9, 9), (16, 4), (20, 9)])
        _poly(s, PALETTE["outline"], [(9, 31), (16, 36), (20, 31)])
        _rect(s, PALETTE["metal_hi"], (12, 10, 8, 3))
        return s

    def _engineer_player(self) -> pygame.Surface:
        s = _surf((42, 42))
        _outline_rect(s, (6, 12, 9, 18), (35, 42, 47))
        _outline_rect(s, (10, 9, 20, 24), (44, 52, 58))
        _outline_rect(s, (27, 16, 10, 7), (51, 62, 67))
        _rect(s, PALETTE["green"], (17, 16, 7, 7))
        _rect(s, PALETTE["amber"], (10, 7, 6, 4))
        _rect(s, PALETTE["amber"], (10, 31, 6, 4))
        _outline_rect(s, (27, 4, 8, 8), (41, 58, 50))
        _outline_rect(s, (27, 30, 8, 8), (41, 58, 50))
        _rect(s, PALETTE["green"], (30, 7, 2, 2))
        _rect(s, PALETTE["green"], (30, 33, 2, 2))
        return s

    def _sniper_portrait(self) -> pygame.Surface:
        s = _surf((120, 120))
        _outline_rect(s, (0, 0, 120, 120), (22, 27, 39), width=3)
        pygame.draw.rect(s, PALETTE["amber"], pygame.Rect(0, 0, 120, 120), 2)
        _rect(s, PALETTE["outline"], (10, 10, 100, 100))
        # Draw a technical scope reticle inside portrait
        pygame.draw.circle(s, PALETTE["amber"], (60, 60), 32, 2)
        pygame.draw.circle(s, PALETTE["cyan"], (60, 60), 4, 0)
        pygame.draw.line(s, PALETTE["amber"], (60, 20), (60, 100), 2)
        pygame.draw.line(s, PALETTE["amber"], (20, 60), (100, 60), 2)
        return s

    def _tank_icon(self, sprite_key: str, color: tuple[int, int, int]) -> pygame.Surface:
        s = _surf((44, 44))
        _outline_rect(s, (3, 3, 38, 38), (18, 23, 34))
        sprite = pygame.transform.scale(self.sprites[sprite_key], (30, 30))
        s.blit(sprite, (7, 7))
        pygame.draw.rect(s, color, pygame.Rect(3, 3, 38, 38), 2)
        return s

    def _crawler(self) -> pygame.Surface:
        s = _surf((32, 32))
        _outline_rect(s, (8, 9, 16, 15), (57, 48, 62))
        _rect(s, PALETTE["green"], (13, 13, 6, 5))
        for y in (8, 14, 21):
            _rect(s, PALETTE["outline"], (3, y, 6, 3))
            _rect(s, PALETTE["outline"], (23, y, 6, 3))
        _rect(s, PALETTE["magenta"], (9, 6, 5, 3))
        _rect(s, PALETTE["magenta"], (18, 6, 5, 3))
        return s

    def _runner(self) -> pygame.Surface:
        s = _surf((32, 32))
        _poly(s, PALETTE["outline"], [(6, 16), (23, 5), (27, 16), (23, 27)])
        _poly(s, (61, 54, 76), [(8, 16), (22, 8), (25, 16), (22, 24)])
        _rect(s, PALETTE["amber"], (17, 14, 7, 4))
        _rect(s, PALETTE["cyan"], (10, 15, 4, 3))
        return s

    def _brute(self) -> pygame.Surface:
        s = _surf((44, 44))
        _outline_rect(s, (7, 9, 30, 26), (58, 63, 74), width=3)
        _outline_rect(s, (11, 13, 22, 18), (43, 47, 56))
        _rect(s, PALETTE["red"], (17, 18, 10, 7))
        _rect(s, PALETTE["metal_hi"], (6, 14, 4, 16))
        _rect(s, PALETTE["metal_hi"], (34, 14, 4, 16))
        return s

    def _shooter(self) -> pygame.Surface:
        s = _surf((38, 38))
        _outline_rect(s, (9, 9, 20, 20), (46, 52, 66))
        _rect(s, PALETTE["purple"], (15, 15, 8, 8))
        _outline_rect(s, (24, 16, 11, 6), (55, 65, 79))
        _rect(s, PALETTE["cyan"], (27, 18, 7, 2))
        _rect(s, PALETTE["magenta"], (7, 7, 5, 5))
        _rect(s, PALETTE["magenta"], (7, 26, 5, 5))
        return s

    def _boss(self) -> pygame.Surface:
        s = _surf((72, 72))
        _outline_rect(s, (13, 16, 46, 40), (50, 49, 65), width=3)
        _outline_rect(s, (20, 23, 32, 26), (37, 41, 52))
        _rect(s, PALETTE["magenta"], (28, 30, 16, 10))
        _rect(s, PALETTE["amber"], (8, 20, 8, 11))
        _rect(s, PALETTE["amber"], (56, 20, 8, 11))
        _rect(s, PALETTE["cyan"], (9, 44, 9, 6))
        _rect(s, PALETTE["cyan"], (54, 44, 9, 6))
        for x in (19, 47):
            _outline_rect(s, (x, 8, 7, 13), (65, 72, 86))
        return s

    def _bullet(self, color: tuple[int, int, int], width: int, height: int, fins: bool = False) -> pygame.Surface:
        s = _surf((width + 4, height + 4))
        h = height // 2 + 2
        _poly(s, PALETTE["outline"], [(2, h), (width - 2, 2), (width + 2, h), (width - 2, height + 2)])
        _poly(s, color, [(4, h), (width - 3, 4), (width, h), (width - 3, height)])
        if fins:
            _rect(s, PALETTE["magenta"], (4, 2, 5, 3))
            _rect(s, PALETTE["magenta"], (4, height + 1, 5, 3))
        return s

    def _enemy_bullet(self) -> pygame.Surface:
        s = _surf((16, 16))
        _poly(s, PALETTE["outline"], [(8, 1), (15, 8), (8, 15), (1, 8)])
        _poly(s, PALETTE["purple"], [(8, 3), (13, 8), (8, 13), (3, 8)])
        _rect(s, PALETTE["magenta"], (7, 7, 2, 2))
        return s

    def _xp_pickup(self) -> pygame.Surface:
        s = _surf((16, 16))
        _poly(s, PALETTE["outline"], [(8, 1), (15, 8), (8, 15), (1, 8)])
        _poly(s, PALETTE["cyan"], [(8, 3), (13, 8), (8, 13), (3, 8)])
        _rect(s, PALETTE["white"], (7, 5, 2, 2))
        return s

    def _health_pickup(self) -> pygame.Surface:
        s = _surf((18, 18))
        _outline_rect(s, (3, 3, 12, 12), (40, 54, 44))
        _rect(s, PALETTE["green"], (7, 4, 4, 10))
        _rect(s, PALETTE["green"], (4, 7, 10, 4))
        return s

    def _coin_pickup(self) -> pygame.Surface:
        s = _surf((18, 18))
        _poly(s, PALETTE["outline"], [(9, 1), (16, 5), (16, 13), (9, 17), (2, 13), (2, 5)])
        _poly(s, PALETTE["amber"], [(9, 3), (14, 6), (14, 12), (9, 15), (4, 12), (4, 6)])
        _rect(s, PALETTE["white"], (7, 5, 4, 2))
        _rect(s, PALETTE["magenta"], (8, 11, 3, 2))
        return s

    def _shield_drone(self) -> pygame.Surface:
        s = _surf((20, 20))
        _outline_rect(s, (5, 5, 10, 10), (47, 58, 67))
        _rect(s, PALETTE["green"], (8, 8, 4, 4))
        return s

    def _mini_turret(self) -> pygame.Surface:
        s = _surf((28, 28))
        _outline_rect(s, (7, 10, 14, 13), (39, 49, 52))
        _outline_rect(s, (13, 4, 6, 10), (52, 62, 65))
        _rect(s, PALETTE["green"], (12, 14, 5, 4))
        _rect(s, PALETTE["cyan"], (15, 4, 2, 8))
        _rect(s, PALETTE["metal_hi"], (5, 22, 18, 3))
        return s

    def _mine(self) -> pygame.Surface:
        s = _surf((24, 24))
        _outline_rect(s, (7, 7, 10, 10), (45, 38, 42))
        _rect(s, PALETTE["red"], (10, 10, 4, 4))
        for point in ((3, 10), (18, 10), (10, 3), (10, 18)):
            _rect(s, PALETTE["outline"], (*point, 4, 4))
        return s

    def _chest_sprite(self, boss: bool = False) -> pygame.Surface:
        s = _surf((22, 22))
        color = PALETTE["magenta"] if boss else (100, 60, 30)
        _outline_rect(s, (3, 3, 16, 16), color)
        _rect(s, PALETTE["amber"], (3, 7, 16, 3))
        _rect(s, PALETTE["amber"], (7, 3, 3, 16))
        _rect(s, PALETTE["white"] if not boss else PALETTE["cyan"], (9, 9, 4, 4))
        return s

    def _tileset(self, theme: str) -> dict[str, list[pygame.Surface]]:
        return {
            "floor": [self._tile(i, theme) for i in range(5)],
            "wall": [self._wall_tile(i, theme) for i in range(3)],
            "obstacle": [self._obstacle_tile(i, theme) for i in range(4)],
            "decor": [self._decor_tile(i, theme) for i in range(5)],
        }

    def _tile(self, variant: int, theme: str = "scrap") -> pygame.Surface:
        s = _surf((TILE_SIZE, TILE_SIZE))
        palettes = {
            "scrap": ((18, 22, 31), (36, 44, 56), PALETTE["cyan"], PALETTE["magenta"]),
            "desert": ((50, 40, 28), (82, 66, 43), PALETTE["amber"], (176, 92, 47)),
            "frozen": ((20, 34, 45), (54, 83, 99), PALETTE["cyan"], (157, 220, 255)),
            "city": ((29, 31, 46), (54, 58, 86), PALETTE["magenta"], PALETTE["cyan"]),
            "jungle": ((19, 48, 34), (43, 83, 55), PALETTE["green"], (114, 165, 70)),
        }
        base_color, line_base, accent, accent2 = palettes[theme]
        base = tuple(min(255, base_color[i] + variant * (2 + i)) for i in range(3))
        s.fill(base)
        line = tuple(min(255, line_base[i] + variant * 3) for i in range(3))
        pygame.draw.line(s, line, (0, 0), (31, 0))
        pygame.draw.line(s, line, (0, 0), (0, 31))
        if variant % 2 == 0:
            _rect(s, line, (7, 11, 6, 3))
            _rect(s, accent, (23, 24, 2, 2))
        else:
            _rect(s, line, (17, 8, 8, 3))
            _rect(s, accent2, (5, 21, 2, 2))
        return s

    def _wall_tile(self, variant: int, theme: str) -> pygame.Surface:
        s = self._tile(variant, theme)
        overlay = {
            "scrap": (55, 61, 74),
            "desert": (105, 76, 47),
            "frozen": (72, 111, 130),
            "city": (70, 76, 106),
            "jungle": (51, 95, 61),
        }[theme]
        _outline_rect(s, (2, 7, 28, 18), overlay, width=2)
        return s

    def _obstacle_tile(self, variant: int, theme: str) -> pygame.Surface:
        s = _surf((TILE_SIZE, TILE_SIZE))
        color = {
            "scrap": (58, 62, 72),
            "desert": (92, 63, 37),
            "frozen": (60, 92, 108),
            "city": (67, 69, 88),
            "jungle": (52, 91, 56),
        }[theme]
        accent = {"scrap": PALETTE["magenta"], "desert": PALETTE["amber"], "frozen": PALETTE["cyan"], "city": PALETTE["magenta"], "jungle": PALETTE["green"]}[theme]
        _outline_rect(s, (5, 8, 22, 17), color)
        _rect(s, accent, (10 + variant % 6, 12, 4, 3))
        return s

    def _decor_tile(self, variant: int, theme: str) -> pygame.Surface:
        s = _surf((TILE_SIZE, TILE_SIZE))
        if theme == "city":
            if variant % 2 == 0:
                _rect(s, PALETTE["outline"], (5, 7, 22, 19))
                _rect(s, (52, 56, 78), (7, 9, 18, 15))
                for x in (9, 15, 21):
                    _rect(s, PALETTE["cyan"] if x != 15 else PALETTE["magenta"], (x, 12, 2, 5))
            else:
                _rect(s, (42, 44, 56), (3, 17, 26, 6))
                _rect(s, PALETTE["amber"], (5, 18, 8, 2))
                _rect(s, PALETTE["amber"], (19, 18, 7, 2))
        elif theme == "jungle":
            if variant % 2 == 0:
                _poly(s, (20, 67, 39), [(4, 24), (11, 6), (17, 19), (23, 5), (29, 23)])
                _poly(s, (70, 130, 57), [(6, 23), (12, 9), (17, 21), (23, 8), (28, 22)])
            else:
                _rect(s, (74, 68, 45), (14, 6, 4, 22))
                pygame.draw.line(s, (79, 151, 61), (16, 9), (7, 20), 2)
                pygame.draw.line(s, (79, 151, 61), (16, 13), (25, 23), 2)
        elif theme == "desert":
            if variant == 0:
                # Half-buried rusted pipe / scrap iron
                _rect(s, (60, 40, 20), (2, 12, 10, 8))
                _rect(s, (140, 70, 30), (2, 13, 10, 6))
                _rect(s, (60, 40, 20), (20, 12, 10, 8))
                _rect(s, (140, 70, 30), (20, 13, 10, 6))
                _rect(s, PALETTE["amber"], (4, 14, 4, 2))
                _rect(s, PALETTE["amber"], (24, 14, 4, 2))
            elif variant == 1:
                # Small stone/rock cluster in sand
                _poly(s, (80, 70, 55), [(6, 20), (12, 10), (18, 16), (14, 24), (8, 24)])
                _poly(s, (110, 95, 80), [(17, 26), (22, 16), (28, 20), (26, 28), (19, 28)])
                pygame.draw.polygon(s, (50, 40, 30), [(6, 20), (12, 10), (18, 16), (14, 24), (8, 24)], 1)
                pygame.draw.polygon(s, (50, 40, 30), [(17, 26), (22, 16), (28, 20), (26, 28), (19, 28)], 1)
            elif variant == 2:
                # A sand-swept metal shard
                _poly(s, (50, 35, 20), [(8, 24), (24, 8), (20, 28)])
                _poly(s, (160, 100, 50), [(9, 23), (23, 9), (19, 27)])
                _rect(s, PALETTE["amber"], (15, 17, 3, 3))
            elif variant == 3:
                # A small desert shrub or debris object
                pygame.draw.line(s, (100, 60, 30), (16, 26), (16, 16), 2)
                pygame.draw.line(s, (100, 60, 30), (16, 16), (8, 10), 2)
                pygame.draw.line(s, (100, 60, 30), (16, 16), (24, 12), 2)
                pygame.draw.line(s, (120, 80, 40), (8, 10), (5, 12), 1)
                pygame.draw.line(s, (120, 80, 40), (24, 12), (28, 10), 1)
            else:
                # A piece of skeletal metal junk
                _rect(s, (90, 60, 35), (4, 15, 24, 2))
                for x in (8, 14, 20, 26):
                    pygame.draw.line(s, (90, 60, 35), (x, 8), (x, 24), 2)
                    pygame.draw.line(s, PALETTE["amber"], (x, 15), (x, 17), 2)
        elif theme == "frozen":
            if variant == 0:
                # Sharp ice crystal / icicle fragment
                _poly(s, PALETTE["outline"], [(16, 4), (24, 20), (16, 28), (8, 20)])
                _poly(s, (142, 218, 244), [(16, 6), (22, 20), (16, 26), (10, 20)])
                pygame.draw.line(s, PALETTE["white"], (16, 8), (16, 24), 1)
            elif variant == 1:
                # Frost-covered pipeline piece
                _rect(s, (30, 50, 70), (4, 12, 24, 8))
                _rect(s, (80, 120, 150), (4, 13, 24, 6))
                _rect(s, PALETTE["white"], (4, 11, 24, 2))
                _rect(s, PALETTE["cyan"], (10, 13, 6, 2))
            elif variant == 2:
                # Shard of glowing blue crystal
                _poly(s, PALETTE["outline"], [(6, 22), (18, 6), (26, 16), (20, 26)])
                _poly(s, PALETTE["cyan"], [(8, 21), (18, 8), (24, 16), (20, 24)])
                _poly(s, PALETTE["white"], [(12, 16), (18, 9), (20, 15)])
            elif variant == 3:
                # A piece of frozen scrap paneling
                _rect(s, PALETTE["outline"], (6, 6, 20, 20))
                _rect(s, (50, 75, 95), (7, 7, 18, 18))
                _poly(s, (160, 220, 240), [(7, 7), (18, 7), (12, 15), (7, 12)])
                _rect(s, PALETTE["white"], (8, 8, 4, 4))
            else:
                # A frozen sprocket or wheel fragment
                center = (16, 24)
                radius = 10
                pygame.draw.circle(s, PALETTE["outline"], center, radius + 2)
                pygame.draw.circle(s, (70, 100, 120), center, radius)
                for angle_deg in (45, 90, 135):
                    rad = math.radians(180 + angle_deg)
                    tx = int(center[0] + (radius + 3) * math.cos(rad))
                    ty = int(center[1] + (radius + 3) * math.sin(rad))
                    pygame.draw.line(s, PALETTE["outline"], center, (tx, ty), 3)
                    pygame.draw.line(s, PALETTE["cyan"], center, (tx, ty), 1)
                pygame.draw.circle(s, (160, 220, 240), center, 4)
                pygame.draw.circle(s, PALETTE["white"], center, 2)
        else:
            if variant == 0:
                # A small metallic pipe or tube
                _rect(s, PALETTE["outline"], (4, 12, 24, 8))
                _rect(s, (80, 88, 100), (4, 13, 24, 6))
                _rect(s, PALETTE["metal_hi"], (4, 14, 24, 2))
                _rect(s, PALETTE["outline"], (10, 11, 3, 10))
                _rect(s, PALETTE["amber"], (10, 12, 3, 8))
            elif variant == 1:
                # A scrap metal gear piece
                center = (16, 16)
                radius = 6
                _rect(s, (70, 78, 90), (14, 6, 4, 20))
                _rect(s, (70, 78, 90), (6, 14, 20, 4))
                _poly(s, (70, 78, 90), [(8, 8), (24, 24), (23, 25), (7, 9)])
                _poly(s, (70, 78, 90), [(24, 8), (8, 24), (9, 25), (25, 9)])
                pygame.draw.circle(s, PALETTE["outline"], center, radius + 2)
                pygame.draw.circle(s, (90, 100, 115), center, radius)
                pygame.draw.circle(s, PALETTE["outline"], center, 2)
            elif variant == 2:
                # A square metal plate / loose plating
                _rect(s, PALETTE["outline"], (8, 8, 16, 16))
                _rect(s, (60, 66, 76), (9, 9, 14, 14))
                _rect(s, PALETTE["metal_hi"], (10, 10, 2, 2))
                _rect(s, PALETTE["metal_hi"], (20, 10, 2, 2))
                _rect(s, PALETTE["metal_hi"], (10, 20, 2, 2))
                _rect(s, PALETTE["metal_hi"], (20, 20, 2, 2))
                pygame.draw.line(s, PALETTE["magenta"], (11, 15), (17, 21), 1)
            elif variant == 3:
                # A diagonal cross-bracing or bracket wire
                pygame.draw.line(s, PALETTE["outline"], (6, 6), (26, 26), 4)
                pygame.draw.line(s, (100, 110, 120), (7, 7), (25, 25), 2)
                pygame.draw.line(s, PALETTE["outline"], (26, 6), (6, 26), 4)
                pygame.draw.line(s, (100, 110, 120), (25, 7), (7, 25), 2)
                pygame.draw.circle(s, PALETTE["cyan"], (16, 16), 3)
            else:
                # A cluster of small metallic debris/rubble particles
                _rect(s, PALETTE["outline"], (6, 8, 5, 5))
                _rect(s, (80, 85, 95), (7, 9, 3, 3))
                _rect(s, PALETTE["outline"], (18, 20, 6, 4))
                _rect(s, (110, 115, 125), (19, 21, 4, 2))
                _rect(s, PALETTE["outline"], (22, 7, 4, 4))
                _rect(s, PALETTE["cyan"], (23, 8, 2, 2))
                _rect(s, PALETTE["outline"], (9, 22, 5, 5))
                _rect(s, PALETTE["magenta"], (10, 23, 3, 3))
        return s

    def _explosion(self, frame: int) -> pygame.Surface:
        s = _surf((40, 40))
        center = pygame.Vector2(20, 20)
        colors = [PALETTE["white"], PALETTE["amber"], PALETTE["magenta"], PALETTE["red"]]
        for i, color in enumerate(colors):
            radius = max(1, 5 + frame * 3 - i * 4)
            if radius <= 0:
                continue
            for a in range(0, 360, 45):
                direction = pygame.Vector2(math.cos(math.radians(a)), math.sin(math.radians(a)))
                p = center + direction * (radius + i * 2)
                _rect(s, color, (int(p.x) - 2, int(p.y) - 2, 4, 4))
        return s

    def _icons(self) -> dict[str, pygame.Surface]:
        icons: dict[str, pygame.Surface] = {}
        keys = [
            ("rapid_fire", PALETTE["cyan"]),
            ("bullet_damage", PALETTE["red"]),
            ("multi_shot", PALETTE["amber"]),
            ("move_speed", PALETTE["green"]),
            ("pierce", PALETTE["purple"]),
            ("bullet_size", PALETTE["blue"]),
            ("magnet", PALETTE["magenta"]),
            ("repair", PALETTE["green"]),
            ("explosive_shot", PALETTE["amber"]),
            ("side_cannon", PALETTE["cyan"]),
            ("split_shot", PALETTE["purple"]),
            ("shield_drone", PALETTE["green"]),
            ("lightning_chain", PALETTE["cyan"]),
            ("bullet_speed", PALETTE["blue"]),
            ("max_health", PALETTE["green"]),
            ("xp_gain", PALETTE["cyan"]),
            ("coin_gain", PALETTE["amber"]),
            ("crit_chance", PALETTE["red"]),
            ("ricochet", PALETTE["cyan"]),
            ("freeze_shot", PALETTE["cyan"]),
            ("poison_shot", PALETTE["green"]),
            ("emergency_shield", PALETTE["blue"]),
            ("magnet_pulse", PALETTE["magenta"]),
            ("overclock", PALETTE["amber"]),
            ("hollow_point", PALETTE["red"]),
            ("nanobot_repair", PALETTE["green"]),
            ("mine_layer", PALETTE["red"]),
            ("targeting_ai", PALETTE["green"]),
            ("dash_cooldown", PALETTE["cyan"]),
            ("armor", PALETTE["blue"]),
            ("lucky_drop", PALETTE["amber"]),
            ("turret_support", PALETTE["green"]),
            ("ach_survive", PALETTE["cyan"]),
            ("ach_boss", PALETTE["magenta"]),
            ("ach_kill", PALETTE["red"]),
            ("ach_coin", PALETTE["amber"]),
            ("ach_level", PALETTE["cyan"]),
            ("ach_tank", PALETTE["green"]),
            ("ach_shop", PALETTE["amber"]),
            ("ach_shield", PALETTE["blue"]),
            ("meta_max_health", PALETTE["green"]),
            ("meta_move_speed", PALETTE["green"]),
            ("meta_fire_rate", PALETTE["cyan"]),
            ("meta_bullet_damage", PALETTE["red"]),
            ("meta_xp_bonus", PALETTE["cyan"]),
            ("meta_coin_bonus", PALETTE["amber"]),
            ("meta_pickup_radius", PALETTE["magenta"]),
            ("meta_projectile_speed", PALETTE["blue"]),
            ("minigun_mode", PALETTE["amber"]),
            ("rocket_core", PALETTE["magenta"]),
            ("twin_turret_form", PALETTE["green"]),
        ]
        for key, color in keys:
            s = _surf((28, 28))
            _outline_rect(s, (3, 3, 22, 22), (23, 28, 39))
            if key in ("repair", "meta_max_health", "max_health", "nanobot_repair"):
                _rect(s, color, (12, 7, 4, 14))
                _rect(s, color, (7, 12, 14, 4))
            elif key in ("magnet", "meta_pickup_radius", "magnet_pulse"):
                _rect(s, color, (7, 8, 4, 12))
                _rect(s, color, (17, 8, 4, 12))
                _rect(s, color, (9, 18, 10, 3))
            elif key in ("meta_coin_bonus", "coin_gain", "lucky_drop", "ach_coin", "ach_shop"):
                _poly(s, color, [(14, 5), (21, 9), (21, 19), (14, 23), (7, 19), (7, 9)])
                _rect(s, PALETTE["white"], (12, 9, 4, 2))
            elif key in ("meta_xp_bonus", "xp_gain"):
                _poly(s, color, [(14, 5), (22, 14), (14, 23), (6, 14)])
                _rect(s, PALETTE["white"], (13, 9, 2, 2))
            elif key in ("shield_drone", "emergency_shield", "armor", "ach_shield"):
                _poly(s, color, [(14, 6), (22, 11), (19, 22), (14, 24), (9, 22), (6, 11)])
            elif key.startswith("ach_"):
                _poly(s, color, [(14, 4), (18, 10), (24, 11), (20, 16), (21, 23), (14, 20), (7, 23), (8, 16), (4, 11), (10, 10)])
            elif key in ("lightning_chain", "overclock"):
                _poly(s, color, [(16, 5), (9, 15), (14, 15), (11, 23), (20, 11), (15, 11)])
            elif key == "ricochet":
                pygame.draw.arc(s, color, pygame.Rect(7, 7, 14, 14), 0.5, 5.0, 3)
                _poly(s, color, [(19, 6), (23, 11), (17, 11)])
            elif key == "freeze_shot":
                for a in range(0, 180, 45):
                    pygame.draw.line(s, color, (14, 14), (14 + int(9 * math.cos(math.radians(a))), 14 + int(9 * math.sin(math.radians(a)))), 2)
                    pygame.draw.line(s, color, (14, 14), (14 - int(9 * math.cos(math.radians(a))), 14 - int(9 * math.sin(math.radians(a)))), 2)
            elif key == "poison_shot":
                _rect(s, color, (10, 8, 8, 12))
                _rect(s, PALETTE["white"], (12, 10, 2, 2))
            elif key == "mine_layer":
                _outline_rect(s, (9, 9, 10, 10), (59, 40, 45))
                _rect(s, color, (12, 12, 4, 4))
            elif key in ("targeting_ai", "turret_support"):
                _rect(s, color, (13, 7, 3, 14))
                _rect(s, color, (7, 13, 14, 3))
                pygame.draw.circle(s, color, (14, 14), 8, 2)
            elif key == "dash_cooldown":
                _poly(s, color, [(7, 9), (20, 14), (7, 19)])
                _rect(s, color, (5, 12, 8, 4))
            elif key in ("rocket_core", "explosive_shot"):
                _poly(s, color, [(8, 20), (18, 6), (22, 18)])
                _rect(s, PALETTE["red"], (7, 19, 6, 4))
            elif "twin" in key or key == "side_cannon":
                _rect(s, color, (8, 8, 4, 13))
                _rect(s, color, (17, 8, 4, 13))
            elif key == "split_shot":
                pygame.draw.line(s, color, (7, 20), (14, 8), 3)
                pygame.draw.line(s, color, (21, 20), (14, 8), 3)
            elif key == "multi_shot":
                for x in (8, 14, 20):
                    _rect(s, color, (x, 8, 3, 13))
            else:
                _poly(s, color, [(6, 14), (18, 7), (23, 14), (18, 21)])
            icons[key] = s
            
        # Add default fallbacks for loot items in self.icons
        loot_keys = {
            "loot_frame_common": PALETTE["outline"],
            "loot_frame_uncommon": PALETTE["green"],
            "loot_frame_rare": PALETTE["cyan"],
            "loot_frame_epic": PALETTE["purple"],
            "loot_frame_legendary": PALETTE["amber"],
            "loot_frame_unique": PALETTE["magenta"],
            "loot_weapon_scrap_cannon": PALETTE["cyan"],
            "loot_weapon_sniper_core": PALETTE["amber"],
            "loot_armor_plated_shell": PALETTE["blue"],
            "loot_armor_regen_core": PALETTE["green"],
            "loot_trinket_lucky_coin": PALETTE["amber"],
            "loot_trinket_xp_magnet": PALETTE["magenta"],
            "loot_unique_boss_core": PALETTE["magenta"],
        }
        for key, color in loot_keys.items():
            s = _surf((28, 28))
            _outline_rect(s, (3, 3, 22, 22), color)
            if "frame" in key:
                pygame.draw.rect(s, color, pygame.Rect(3, 3, 22, 22), 2)
            else:
                pygame.draw.circle(s, color, (14, 14), 6)
            icons[key] = s
            
        return icons

    def _load_external_assets(self) -> None:
        root = Path(__file__).parent.parent / "assets"
        sprite_dir = root / "sprites"
        for key, filename in SPRITE_FILENAMES.items():
            candidates = [root / rel_path for rel_path in SPRITE_FALLBACK_PATHS.get(key, ())]
            candidates.append(sprite_dir / filename)
            surface, used_path = self._load_first_existing(candidates)
            if surface is not None:
                self.sprites[key] = surface
                self.loaded_external_assets.append(str(used_path.relative_to(root)))
            else:
                self.missing_assets.append(str(candidates[0].relative_to(root)))
        for key, filename in ICON_FILENAMES.items():
            candidates = [root / rel_path for rel_path in ICON_FALLBACK_PATHS.get(key, ())]
            candidates.append(sprite_dir / filename)
            surface, used_path = self._load_first_existing(candidates)
            if surface is not None:
                self.icons[key] = surface
                self.loaded_external_assets.append(str(used_path.relative_to(root)))
            else:
                self.missing_assets.append(str(candidates[0].relative_to(root)))
        # Every level-up definition has a dedicated generated icon named after
        # its upgrade ID.  Loading this directory independently keeps the
        # manifest fallbacks intact while avoiding shared generic card art.
        levelup_dir = root / LEVELUP_ICON_DIRECTORY
        for path in sorted(levelup_dir.glob("icon_*.png")):
            key = path.stem.removeprefix("icon_")
            try:
                self.icons[key] = _load_image(path)
                self.loaded_external_assets.append(str(path.relative_to(root)))
            except pygame.error:
                self.missing_assets.append(str(path.relative_to(root)) + " (failed to load)")
        equipment_dirs = {
            "weapons": "weapon",
            "armor": "armor",
            "trinkets": "trinket",
            "tracks": "tracks",
        }
        for folder, slot in equipment_dirs.items():
            for path in sorted((root / "icons" / "equipment" / folder).glob("icon_*.png")):
                key = f"equipment_{slot}_{path.stem.removeprefix('icon_')}"
                try:
                    self.icons[key] = _load_image(path)
                    self.loaded_external_assets.append(str(path.relative_to(root)))
                except pygame.error:
                    self.missing_assets.append(str(path.relative_to(root)) + " (failed to load)")
        for path in sorted((root / "icons" / "skill_tree").glob("icon_*.png")):
            key = f"skill_{path.stem.removeprefix('icon_')}"
            try:
                self.icons[key] = _load_image(path)
                self.loaded_external_assets.append(str(path.relative_to(root)))
            except pygame.error:
                self.missing_assets.append(str(path.relative_to(root)) + " (failed to load)")
        for key, rel_paths in MENU_FILENAMES.items():
            candidates = [root / rel_path for rel_path in rel_paths]
            surface, used_path = self._load_first_existing(candidates)
            if surface is not None:
                self.menu[key] = surface
                self.loaded_external_assets.append(str(used_path.relative_to(root)))
            else:
                self.missing_assets.append(str(candidates[0].relative_to(root)))
                
        # Load environment scrap assets
        env_dir = root / "environment" / "scrap"
        
        # 1. Floor tiles
        floor_paths = [
            env_dir / "tile_scrap_floor_01.png",
            env_dir / "tile_scrap_floor_02.png",
            env_dir / "tile_scrap_floor_03.png"
        ]
        loaded_floors = []
        for path in floor_paths:
            if path.exists():
                try:
                    loaded_floors.append(_load_image(path))
                except pygame.error:
                    self.missing_assets.append(f"environment/scrap/{path.name} (failed to load)")
            else:
                self.missing_assets.append(f"environment/scrap/{path.name}")
        
        if loaded_floors:
            # We want floor_03 to be rare (e.g. 1 in 5 tiles) to avoid noisy combat background
            f1 = loaded_floors[0]
            f2 = loaded_floors[1] if len(loaded_floors) > 1 else f1
            f3 = loaded_floors[2] if len(loaded_floors) > 2 else f2
            self.tilesets["scrap"]["floor"] = [f1, f2, f1, f2, f3]
            self.tiles = self.tilesets["scrap"]["floor"]

        # 2. Wall tile
        wall_path = env_dir / "tile_scrap_wall.png"
        if wall_path.exists():
            try:
                wall_img = _load_image(wall_path)
                self.tilesets["scrap"]["wall"] = [wall_img] * 3
            except pygame.error:
                self.missing_assets.append("environment/scrap/tile_scrap_wall.png (failed to load)")
        else:
            self.missing_assets.append("environment/scrap/tile_scrap_wall.png")
            
        # 3. Obstacles
        obs_names = ["prop_crate_metal.png", "prop_hazard_barrier.png", "prop_broken_machine.png", "tile_scrap_border.png"]
        loaded_obs = []
        for name in obs_names:
            path = env_dir / name
            if path.exists():
                try:
                    loaded_obs.append(_load_image(path))
                except pygame.error:
                    self.missing_assets.append(f"environment/scrap/{name} (failed to load)")
            else:
                self.missing_assets.append(f"environment/scrap/{name}")
        if loaded_obs:
            self.tilesets["scrap"]["obstacle"] = loaded_obs
            
        # 4. Decor
        decor_names = ["prop_scrap_pile_01.png", "prop_scrap_pile_02.png", "prop_broken_pipe.png", "prop_neon_sign_small.png"]
        loaded_decors = []
        for name in decor_names:
            path = env_dir / name
            if path.exists():
                try:
                    loaded_decors.append(_load_image(path))
                except pygame.error:
                    self.missing_assets.append(f"environment/scrap/{name} (failed to load)")
            else:
                self.missing_assets.append(f"environment/scrap/{name}")
        if loaded_decors:
            self.tilesets["scrap"]["decor"] = loaded_decors

        self._load_environment_tileset(
            "scrap",
            "scrapyard_outskirts",
            floors=[
                "tile_floor_01.png",
                "tile_floor_02.png",
                "tile_floor_01.png",
                "tile_floor_02.png",
                "tile_floor_03.png",
                "tile_path_worn_ground.png",
            ],
            walls=["tile_wall.png", "tile_border.png"],
            obstacles=[
                "tile_border.png",
                "prop_metal_crate.png",
                "prop_hazard_barrier.png",
                "prop_broken_machine.png",
                "prop_rusted_tank_hulk.png",
                "prop_wrecked_turret.png",
            ],
            decor=[
                "prop_scrap_pile_01.png",
                "prop_scrap_pile_02.png",
                "prop_broken_pipe.png",
                "prop_neon_sign_small.png",
            ],
        )
        self._load_environment_tileset(
            "desert",
            "desert_wasteland",
            floors=[
                "tile_sand_floor_01.png",
                "tile_sand_floor_02.png",
                "tile_sand_floor_01.png",
                "tile_sand_floor_02.png",
                "tile_cracked_earth.png",
            ],
            walls=["tile_rusted_wall.png", "tile_border.png"],
            obstacles=["tile_border.png", "prop_rusted_wreckage.png", "prop_desert_barricade.png"],
            decor=["prop_dusty_scrap_pile.png", "prop_broken_sign.png", "prop_buried_pipe.png"],
        )
        self._load_environment_tileset(
            "frozen",
            "frozen_tech_base",
            floors=[
                "tile_ice_floor_01.png",
                "tile_ice_floor_02.png",
                "tile_ice_floor_01.png",
                "tile_ice_floor_02.png",
                "tile_frozen_panel.png",
            ],
            walls=["tile_tech_wall.png", "tile_border.png"],
            obstacles=["tile_border.png", "prop_ice_crate.png", "prop_frozen_barrier.png", "prop_damaged_machine.png"],
            decor=["prop_frozen_pipe.png", "prop_snowdrift_scrap.png"],
        )
        self._load_environment_tileset(
            "city",
            "city",
            floors=[
                "tile_city_road_01.png",
                "tile_city_road_02.png",
                "tile_city_road_cracked.png",
                "tile_city_concrete_01.png",
                "tile_city_concrete_02.png",
                "tile_city_sidewalk.png",
                "tile_city_intersection_marking.png",
                "tile_city_lane_marking.png",
                "tile_city_hazard_patch.png",
                "tile_city_path_01.png",
            ],
            walls=["tile_city_wall.png", "tile_city_border.png"],
            obstacles=[
                "prop_city_barrier_01.png",
                "prop_city_barrier_02.png",
                "prop_city_roadblock.png",
                "prop_city_scrap_barricade.png",
            ],
            decor=[
                "prop_city_broken_terminal.png",
                "prop_city_street_sign_broken.png",
                "prop_city_neon_sign_small.png",
                "prop_city_utility_box.png",
                "prop_city_debris_pile.png",
                "prop_city_wrecked_car_small.png",
            ],
        )
        self._load_environment_tileset(
            "jungle",
            "jungle",
            floors=[
                "tile_jungle_ground_01.png",
                "tile_jungle_ground_02.png",
                "tile_jungle_moss_01.png",
                "tile_jungle_root_path.png",
                "tile_jungle_ruin_floor.png",
                "tile_jungle_leaf_litter.png",
                "tile_jungle_wet_earth.png",
                "tile_jungle_glow_patch.png",
                "tile_jungle_path_01.png",
            ],
            walls=["tile_jungle_wall.png", "tile_jungle_border.png"],
            obstacles=[
                "prop_jungle_root_tangle.png",
                "prop_jungle_broken_ruin_piece.png",
                "prop_jungle_overgrown_machine.png",
                "prop_jungle_vine_barrier.png",
            ],
            decor=[
                "prop_jungle_vine_cluster.png",
                "prop_jungle_bush_cluster.png",
                "prop_jungle_scrap_pile_mossy.png",
                "prop_jungle_fern_cluster.png",
                "prop_jungle_stone_shard.png",
                "prop_jungle_small_relay_ruin.png",
            ],
        )
        self._load_landmarks(root)
        self.tiles = self.tilesets["scrap"]["floor"]
            
        if self.missing_assets:
            print("Missing optional assets using procedural fallbacks:")
            for path in self.missing_assets:
                print(f"  - assets/{path}")

    def _load_environment_tileset(
        self,
        theme: str,
        folder_name: str,
        *,
        floors: list[str],
        walls: list[str],
        obstacles: list[str],
        decor: list[str],
    ) -> None:
        root = Path(__file__).parent.parent / "assets" / "environment" / folder_name
        if not root.exists():
            self.missing_assets.append(f"environment/{folder_name}")
            return

        loaded_floors = self._load_environment_group(root, floors, folder_name)
        loaded_walls = self._load_environment_group(root, walls, folder_name)
        loaded_obstacles = self._load_environment_group(root, obstacles, folder_name)
        loaded_decor = self._load_environment_group(root, decor, folder_name)

        if loaded_floors:
            self.tilesets[theme]["floor"] = loaded_floors
        if loaded_walls:
            self.tilesets[theme]["wall"] = loaded_walls
        if loaded_obstacles:
            self.tilesets[theme]["obstacle"] = loaded_obstacles
        if loaded_decor:
            self.tilesets[theme]["decor"] = loaded_decor

    def _load_environment_group(self, root: Path, names: list[str], folder_name: str) -> list[pygame.Surface]:
        loaded: list[pygame.Surface] = []
        for name in names:
            path = root / name
            if not path.exists():
                self.missing_assets.append(f"environment/{folder_name}/{name}")
                continue
            try:
                loaded.append(_load_image(path))
                asset_root = Path(__file__).parent.parent / "assets"
                self.loaded_external_assets.append(str(path.relative_to(asset_root)))
            except pygame.error:
                self.missing_assets.append(f"environment/{folder_name}/{name} (failed to load)")
        return loaded

    def _load_landmarks(self, root: Path) -> None:
        stage_themes = {
            "scrap_outskirts": "scrap",
            "desert_wrecks": "desert",
            "frozen_base": "frozen",
            "shattered_metro": "city",
            "overgrowth_basin": "jungle",
        }
        landmark_root = root / "environment" / "landmarks"
        for stage_id, theme in stage_themes.items():
            paths = sorted(landmark_root.glob(f"landmark_{stage_id}_*.png"))
            stage_root = root / "environment" / stage_id
            paths.extend(sorted(stage_root.glob("landmark_*.png")))
            theme_root = root / "environment" / theme
            if theme_root != stage_root:
                paths.extend(sorted(theme_root.glob("landmark_*.png")))
            loaded: list[pygame.Surface] = []
            for path in paths:
                try:
                    loaded.append(_load_image(path))
                    self.loaded_external_assets.append(str(path.relative_to(root)))
                except pygame.error:
                    self.missing_assets.append(str(path.relative_to(root)) + " (failed to load)")
            self.landmarks[stage_id] = loaded or [self._landmark_placeholder(theme, index) for index in range(4)]

    def _landmark_placeholder(self, theme: str, variant: int) -> pygame.Surface:
        surface = _surf((176, 128))
        palette = {
            "scrap": ((63, 70, 79), PALETTE["magenta"]),
            "desert": ((117, 78, 43), PALETTE["amber"]),
            "frozen": ((67, 111, 132), PALETTE["cyan"]),
            "city": ((69, 73, 101), PALETTE["magenta"]),
            "jungle": ((52, 105, 60), PALETTE["green"]),
        }[theme]
        body, accent = palette
        _outline_rect(surface, (14, 18, 148, 92), PALETTE["outline"], width=5)
        _rect(surface, body, (18, 22, 140, 84))
        _rect(surface, accent, (36 + variant * 7, 44, 94, 12))
        _rect(surface, PALETTE["metal_hi"], (50, 70, 75, 8))
        return surface

    def _load_first_existing(self, candidates: list[Path]) -> tuple[pygame.Surface | None, Path]:
        for path in candidates:
            if path.exists():
                try:
                    return _load_image(path), path
                except pygame.error:
                    self.missing_assets.append(f"{path.name} (failed to load)")
        return None, candidates[0]
