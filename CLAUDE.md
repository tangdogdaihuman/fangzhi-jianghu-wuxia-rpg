# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A terminal + web-based wuxia (martial arts) idle RPG set in the 天书大陆 universe. Player types commands or clicks in browser -> engine ticks the world forward -> AI GM narrates in Jin Yong style. World lore sourced from a local SillyTavern world book (天书江湖录).

## How to Run

```powershell
$env:PYTHONIOENCODING="utf-8"
cd C:\Users\admin\Desktop\game
python play_wuxia.py          # Terminal mode
python server.py              # Web UI at http://localhost:8080
```

## Architecture

Pure Python, no build step, no dependencies beyond Flask. Layered engine with AI integration:

1. **`xiuxian_world.py`** — Core engine. `GameState` (dataclass-like, JSON-serialized) holds all mutable data. `WorldEngine.tick()` advances time 15 min, moves NPCs by schedule, generates random events. `CommandHandler.process()` returns structured dicts; `format_output()` renders to terminal. Turn-based combat via `CombatState` integration (`start_combat()`, `combat_action()`, `end_combat()`).

2. **`wuxia_api.py`** — Universal OpenAI-compatible API client. Config via `wuxia_config.json` or `STEPFUN_API_KEY` env var. `call_api()` handles chat completions.

3. **`wuxia_ai.py`** — Builds AI GM context string from game state + lore. Used by terminal mode or as a subprocess (`python wuxia_ai.py state`).

4. **`wuxia_ai_integration.py`** — Wires AI into NPC dialogue, quest generation, and event generation. Falls back to static content when API unavailable.

5. **`wuxia_npc_memory.py`** — Two-tier NPC system: **Major** (16 static characters with hardcoded personalities/schedules) + **Minor** (AI-generated, location-appropriate, persistent with memory archive). Memory persisted to `wuxia_npc_memory.json`.

6. **`wuxia_ai_quests.py`** — Dynamic quest generation (10 quest types: deliver, escort, defeat, collect, investigate, rescue, explore, learn, trade, social). State saved to `wuxia_ai_quests.json`.

7. **`wuxia_integration.py`** — Quest tracking, achievement checking, and bridging static + AI quest data for the UI.

8. **`wuxia_combat.py`** — Turn-based combat: attack/defend/skill/item/flee actions, critical hits (15%), stuns, defense reduction. Enemy templates scale with player realm. Rewards: XP + silver. `CombatState` embedded in `GameState`.

9. **`wuxia_lore.py`** — Extracted constants from 天书江湖录: `WORLD_SETTING`, `MAP_INFO`, `ECONOMY_SYSTEM`, `PACING_RULES`, `COMBAT_RULES`, `IRON_RULES`, `TOURNAMENT_RULES`.

10. **`server.py` + `templates/index.html`** — Flask REST API + single-page wuxia-themed UI. Three-column layout: status / terminal / quests + save. Uses `threading.local()` to cache `WorldEngine` per request thread.

## Key Data Files

- `wuxia_save.json` — Main game state
- `wuxia_npc_memory.json` — NPC memory archive (minor NPCs + interaction history)
- `wuxia_ai_quests.json` — AI-generated quests and events
- `wuxia_config.json` — AI API config (optional)
- `saves/*.json` — Named save slots (web UI)

## Game Constants

- **8 locations**: 平安镇, 龙门客栈, 黑风寨, 温泉谷, 襄阳城, 武林秘籍库, 回春堂, 擂台
- **7 realms**: 初入江湖 → 三流高手 → 二流高手 → 一流高手 → 宗师 → 大宗师 → 天下第一
- **16 major NPCs**: 老拳师, 铁匠张伯, 说书人吴六, 受伤镖师, 小医师阿青, 武痴赵猛, 看门老者, 酒楼掌柜王胖子, 郭靖, 黄蓉, 乔峰, 洪七公, 周伯通, 欧阳锋, 令狐冲, 韦小宝
- **Combat templates**: 山贼喽啰, 山贼头目, 恶霸, 高手, 武林败类, 黑风寨主, 神秘高手

## Constraints & Bugs

- **Windows encoding**: `$env:PYTHONIOENCODING="utf-8"` required.
- **Port bug**: `server.py` listens on 8080 but prints "浏览器打开: http://localhost:5000".
- **No test suite**: pure Python 3, no build step.
- **AI optional**: Game works without API key; AI enhances dialogue, quests, and events when available.
- **Wuxia, not xiuxian**: martial arts setting. No cultivation/immortality mechanics despite some legacy naming.

## Common Patterns

```python
import sys; sys.path.insert(0, '.')
from xiuxian_world import GameState, WorldEngine, CommandHandler, format_output
state = GameState.load()
engine = WorldEngine(state)
handler = CommandHandler(engine, state)
result = handler.process('look')
print(format_output(result, engine.get_time_display()))
```

When modifying game systems (combat, quests, NPCs), changes typically need to be reflected in both the engine (`xiuxian_world.py`) and the web API (`server.py`).
