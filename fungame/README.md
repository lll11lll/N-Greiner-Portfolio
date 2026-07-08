# Scrapstorm Overdrive

A single-player Pygame CE arena shooter with diep.io-style tank movement and aiming, plus Vampire Survivors-style XP, upgrades, waves, bosses, and weapon evolutions.

## Run

```powershell
python main.py
```

For gear QA without waiting 5 minutes:

```powershell
python main.py --debug-unlock-gear
```

For live FPS/entity counters:

```powershell
python main.py --debug-performance
```

## Controls

- `WASD` move
- Mouse aim
- Auto-fire is always on
- Right click active tank skill (aims at the cursor)
- `Space` dash
- `Esc` pause
- `R` restart after game over
- `1`, `2`, `3` choose level-up upgrades

## Progression

The run has two progression layers:

- Run progression: XP pickups, level-up cards, temporary upgrades, and weapon evolutions.
- Meta progression: rare run coins, persistent `save.json`, unlockable tanks, universal upgrades, achievements, tank specialization nodes, and gear.

Fresh saves start with 0 coins and only the Starter Tank unlocked. Coins are intentionally rare: survival milestones and bosses are the reliable sources, while normal enemies only sometimes drop coin pickups.

Meta gear unlocks after surviving 5 straight minutes. Before that, chests award coins. After unlock, chests and boss rewards can add persistent weapons, armor, and trinkets with stat bonuses and Unique effects.

## Tanks

- Starter Tank: balanced and reliable.
- Sniper Tank: slow-firing, high-damage, piercing long-range shots.
- Engineer Tank: lower direct burst, but deploys temporary mini turrets that shoot nearby enemies.
- Twin-Shot Tank: starts with dual fire and trades precision for spread pressure.
- Flame Caster Tank: fires explosive shots and leans into ability damage.

## Assets

The game ships with AI-sliced pixel-art sprites plus deterministic procedural fallbacks. The current AI reference sheets are stored at `assets/sprites/ai_reference_sheet.png` and `assets/sprites/ai_expanded_reference_sheet.png`. Production prompts live in `assets/prompts/asset_prompts.md` and `assets/prompts/sprite_prompts.md`.

The active replacement filenames are centralized in `src/asset_manifest.py`. Drop final transparent PNGs at those filenames to replace sprites without changing gameplay code.

Omni is not available in this Codex session. A generator handoff with exact prompts and filenames is available at `assets/prompts/omni_asset_handoff.md`.

To regenerate deterministic fallback PNGs:

```powershell
python tools/generate_assets.py
```

To re-slice the current AI-generated sheet into active sprite filenames:

```powershell
python tools/slice_ai_reference.py
```

## Verification

```powershell
python -m compileall main.py src tools
python main.py --smoke --frames 360
python tools/qa_sanity.py
```
