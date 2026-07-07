# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

An AI-driven idle wuxia (martial arts) RPG set in the 天书大陆 universe. The player types commands or clicks in a browser — the engine ticks the world forward automatically, and an AI GM narrates in Jin Yong style. World lore is sourced from a local SillyTavern world book (天书江湖录).

## How to Run

```powershell
$env:PYTHONIOENCODING="utf-8"
cd C:\Users\admin\Desktop\game
python play_wuxia.py          # Terminal mode
python server.py              # Web UI at http://localhost:8080
```

## Architecture

Pure Python 3, no build step, no external dependencies beyond Flask. Layered engine with AI integration:

### Core Engine Layer
1. **`xiuxian_world.py`** — Single-file core engine. `GameState` is a plain class (not dataclass) with `to_dict()`/`from_dict()`/`save()`/`load()` for JSON persistence. `WorldEngine.tick()` advances game time by 15 min, moves NPCs according to their schedules, and generates random events. `CommandHandler.process()` returns structured result dicts. Turn-based combat via `CombatState` embedded in `GameState` (`start_combat()`, `combat_action()`, `end_combat()`). NPC database (16 major NPCs) is defined inline in this file.

2. **`wuxia_api.py`** — Universal OpenAI-compatible API client with multi-provider fallback chain. Config via `wuxia_config.json` or env vars (`STEPFUN_API_KEY`). `call_api()` tries primary provider, then falls back to stepfun → deepseek → openai → ollama. Includes LLM diagnostic system: `WUXIA_LOG_LLM=1` prints call stats, `WUXIA_DUMP_LLM=1` writes full call records to `logs/llm_calls/`.

3. **`wuxia_ai.py`** — Builds AI GM context string from game state + lore. Reads `wuxia_save.json` directly. Used as a subprocess by terminal mode (`python wuxia_ai.py state`).

4. **`wuxia_ai_integration.py`** — Wires AI into NPC dialogue, quest generation, and event generation. Falls back to static content when API is unavailable.

### NPC System (Two-Tier)
5. **`wuxia_npc_memory.py`** — Two-tier NPC memory: **Major NPCs** (16 static, defined in `xiuxian_world.py` with fixed personalities/schedules) and **Minor NPCs** (AI-generated per location from `LOCATION_NPC_TEMPLATES`, persistent with memory archive). Memory uses tiered compression (raw → short → medium → permanent) with configurable thresholds (`RAW_MAX=8`, `SHORT_MAX=4`, `MEDIUM_MAX=3`). Each NPC also has an `NPCMind` tracking transient thoughts (mood/feeling/emotion with tick-based decay) and persistent thoughts (goals, opinions, secret plans). Keyword extraction is CJK-safe with stop-word filtering. Memory persisted to `wuxia_npc_memory.json`.

6. **`wuxia_npc_ai.py`** — Prompt definitions for major NPC AI dialogue.

### Quest & Content Layer
7. **`wuxia_quests.py`** — Static quest definitions: 4-chapter main quest chain (`MAIN_QUESTS`), 5 side quests (`SIDE_QUESTS`), 3 daily quests (`DAILY_QUESTS`), 8 achievements (`ACHIEVEMENTS`). Data is compact JSON arrays of dicts.

8. **`wuxia_ai_quests.py`** — Dynamic quest generation (10 types: deliver, escort, defeat, collect, investigate, rescue, explore, learn, trade, social) + event templates. `AIQuestSystem` manages active quests and events. State saved to `wuxia_ai_quests.json`.

9. **`wuxia_integration.py`** — Quest tracking, achievement checking, and bridging static + AI quest data for the UI. `init_quest_state()` ensures `state.quest_state` exists.

### Lore & World Data
10. **`wuxia_lore.py`** — Extracted constants from 天书江湖录 world book: `WORLD_SETTING`, `MAP_INFO`, `ECONOMY_SYSTEM`, `PACING_RULES`, `COMBAT_RULES`, `IRON_RULES`, `TOURNAMENT_RULES`.

11. **`wuxia_maps.py`** — World map (8 regions, 35+ sub-areas).

### Web Layer
12. **`server.py` + `templates/index.html`** — Flask REST API + single-page wuxia-themed UI. Uses `threading.local()` to cache `WorldEngine` per request thread (no shared global state). API endpoints: `/api/state`, `/api/command`, `/api/save`/`/api/load`, `/api/quests`, `/api/npcs`, `/api/combat`, `/api/ai-status`/`/api/ai-config`, `/api/quests/ai`.

## Key Data Files

- `wuxia_save.json` — Main game state (auto-saved on every action)
- `wuxia_npc_memory.json` — NPC memory archive (minor NPCs + interaction history + NPC minds)
- `wuxia_ai_quests.json` — AI-generated quests and events
- `wuxia_config.json` — AI API config (optional; env vars take precedence)
- `saves/*.json` — Named save slots (web UI only)
- `logs/llm_calls/` — Full LLM call dumps (when `WUXIA_DUMP_LLM=1`)

## Game Constants

- **8 locations**: 平安镇, 龙门客栈, 黑风寨, 温泉谷, 襄阳城, 武林秘籍库, 回春堂, 擂台
- **7 realms**: 初入江湖 → 三流高手 → 二流高手 → 一流高手 → 宗师 → 大宗师 → 天下第一
- **16 major NPCs**: 老拳师, 铁匠张伯, 说书人吴六, 受伤镖师, 小医师阿青, 武痴赵猛, 看门老者, 酒楼掌柜王胖子, 郭靖, 黄蓉, 乔峰, 洪七公, 周伯通, 欧阳锋, 令狐冲, 韦小宝
- **Combat templates**: 山贼喽啰, 受伤镖师, 山贼头目, 恶霸, 高手, 武林败类, 黑风寨主, 神秘高手

## Constraints & Bugs

- **Windows encoding**: `$env:PYTHONIOENCODING="utf-8"` required for terminal mode.
- **Port bug**: `server.py` listens on `8080` but prints "浏览器打开: http://localhost:5000".
- **No test suite**: no tests, no linter, no build step.
- **AI optional**: Game works without API key; AI enhances dialogue, quests, and events when available.
- **"Wuxia" not "xiuxian"**: martial arts setting. No cultivation/immortality mechanics despite some legacy naming in filenames.

## Debugging AI Calls

```powershell
# Print LLM call stats per action (tokens, time)
$env:WUXIA_LOG_LLM="1"

# Write full LLM call records (messages + responses) to disk
$env:WUXIA_DUMP_LLM="1"
# Output directory: logs/llm_calls/ (customize with WUXIA_DUMP_DIR)
```

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

## Uncommitted Changes (Working Tree)

The following files have uncommitted modifications:
- `wuxia_api.py` — LLM diagnostics, multi-provider fallback
- `wuxia_npc_memory.py` — Tiered memory compression, NPCMind, keyword extraction
- `server.py` — Added `realm_index` to `/api/state` response
- `templates/index.html` — UI changes
- `gen_html.py` — New untracked file
