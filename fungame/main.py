from __future__ import annotations

import argparse
import asyncio
import os
import sys
import tempfile


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scrapstorm Overdrive")
    parser.add_argument("--smoke", action="store_true", help="Run a short headless simulation.")
    parser.add_argument("--frames", type=int, default=360, help="Frame count for --smoke.")
    parser.add_argument("--debug-unlock-loot", action="store_true", help="Persistently unlock meta loot for QA testing.")
    parser.add_argument("--debug-unlock-gear", action="store_true", help="Alias for --debug-unlock-loot.")
    parser.add_argument("--debug-performance", action="store_true", help="Show lightweight FPS/entity counters.")
    return parser.parse_args(argv)


async def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.smoke:
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
        os.environ["NEON_SCRAP_SAVE"] = os.path.join(tempfile.gettempdir(), f"neon_scrap_smoke_save_{os.getpid()}.json")

    import pygame

    from src.constants import SCREEN_HEIGHT, SCREEN_WIDTH
    from src.game import Game

    pygame.init()
    pygame.display.set_caption("Scrapstorm Overdrive")
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    game = Game(
        screen,
        smoke=args.smoke,
        debug_unlock_loot=args.debug_unlock_loot or args.debug_unlock_gear,
        debug_performance=args.debug_performance,
    )
    ok = await game.run_async(max_frames=args.frames if args.smoke else None, auto_start=args.smoke)
    if sys.platform != "emscripten":
        pygame.quit()
    return 0 if ok else 1


if __name__ == "__main__":
    if sys.platform == "emscripten":
        asyncio.run(main([]))
    else:
        raise SystemExit(asyncio.run(main()))
