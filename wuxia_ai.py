#!/usr/bin/env python3
"""
wuxia_ai.py - AI 叙事层（武侠版）
读取游戏状态 + 天书江湖录世界书，输出给 AI GM 用于生成金庸风格叙事
"""

import json, subprocess, sys, os
from wuxia_npc_memory import _estimate_tokens

SAVE_FILE = "wuxia_save.json"

def _load_lore():
    """加载从世界书提取的武侠设定"""
    lore = {}
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from wuxia_lore import (
            WORLD_SETTING, MAP_INFO, ECONOMY_SYSTEM,
            PACING_RULES, COMBAT_RULES, ACTION_FORMAT,
            IRON_RULES, TOURNAMENT_RULES
        )
        lore = {
            "world_setting": WORLD_SETTING,
            "map_info": MAP_INFO,
            "economy": ECONOMY_SYSTEM[:1500],
            "pacing": PACING_RULES,
            "combat": COMBAT_RULES,
            "action_format": ACTION_FORMAT,
            "iron_rules": IRON_RULES,
            "tournament": TOURNAMENT_RULES[:800],
        }
    except ImportError:
        pass
    return lore

def get_state():
    """读取当前游戏状态并格式化为 AI 可读的上下文"""
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            state = json.load(f)
    except:
        state = {}

    realm_names = ["初入江湖", "三流高手", "二流高手", "一流高手", "宗师", "大宗师", "天下第一"]
    realm_icons = ["🐾", "🗡", "⚔️", "🛡", "👨‍🦳", "🌟", "👑"]
    ri = state.get("realm_index", 0)
    hp = state.get("hp", 0)
    mhp = state.get("max_hp", 0)
    cult = round(state.get("cultivation", 0), 1)

    hour = (state.get("game_time", 0) // 60) % 24
    if 5 <= hour < 7:   period = "凌晨"
    elif 7 <= hour < 12: period = "上午"
    elif 12 <= hour < 14: period = "正午"
    elif 14 <= hour < 17: period = "下午"
    elif 17 <= hour < 19: period = "傍晚"
    elif 19 <= hour < 22: period = "夜晚"
    else: period = "深夜"

    day = state.get("game_day", 1)
    season_idx = (day % 360) // 90
    seasons = ["春", "夏", "秋", "冬"]
    season = seasons[season_idx]

    loc = state.get("location", "???")
    loc_descs = {
        "平安镇": "宁静小镇，民风淳朴，远离江湖喧嚣",
        "龙门客栈": "山脚下的热闹客栈，江湖人士云集，消息四通八达",
        "黑风寨": "阴森险峻的山寨，据说有山贼盘踞",
        "温泉谷": "云雾缭绕的山谷，温泉有疗伤养神之效",
        "襄阳城": "繁华大城，城墙高耸，武林人士聚集之地",
        "武林秘籍库": "古老藏书楼，藏着无数武功秘籍",
        "回春堂": "飘着药香的医馆，大夫医术高明",
        "擂台": "巨大演武场，经常有高手切磋比试",
    }
    loc_desc = loc_descs.get(loc, "一个神秘的地方")

    context = f"""=== 武侠世界状态（AI GM 视角）===
时间：第{day}天 {period}（{hour}时） | {season}季
地点：{loc} — {loc_desc}
境界：{realm_icons[ri]} {realm_names[ri]}
生命：{hp}/{mhp} | 攻击：{state.get('atk',0)} | 防御：{state.get('defense',0)}
武学修为（内力）：{cult} | 银两：{state.get('silver',0)} 💎 | 铜钱：{state.get('gold',0)} 🪙
武功：{', '.join(f'{k}Lv{v}' for k,v in state.get('skills',{}).items()) or '无'}
背包：{', '.join(f'{k}x{v}' for k,v in state.get('inventory',{}).items()) or '空'}
好感度：{json.dumps(state.get('relationship',{}), ensure_ascii=False)}
江湖经历：{sorted(state.get('flags',[]))}
"""

    npc_states = state.get("npc_states", {})
    if npc_states:
        context += "\nNPC 动向：\n"
        for name, s in npc_states.items():
            context += f"  {name}: {s.get('action','?')}\n"

    # Append lore from world book
    lore = _load_lore()
    if lore:
        context += "\n=== 世界设定（来自天书江湖录）===\n"
        context += lore.get("world_setting", "")[:1500] + "\n"
        context += "\n=== 叙事规则 ===\n"
        context += lore.get("iron_rules", "")[:600] + "\n"
        context += "\n=== 物价参考 ===\n"
        context += lore.get("economy", "")[:600] + "\n"

    return context

def get_state_for_ai(state, npc_context=None, max_context_tokens=4000):
    """Build AI context within token budget.

    Priority: core state > NPC info > memory.
    Returns (context_string, estimated_tokens).
    """
    parts = []
    budget = max_context_tokens

    realm_names = ["初入江湖","三流高手","二流高手","一流高手","宗师","大宗师","天下第一"]
    ri = state.get("realm_index", 0)
    hp = state.get("hp", 0)
    mhp = state.get("max_hp", 0)
    cult = round(state.get("cultivation", 0), 1)
    hour = (state.get("game_time", 0) // 60) % 24
    if 5 <= hour < 7:   period = "凌晨"
    elif 7 <= hour < 12: period = "上午"
    elif 12 <= hour < 14: period = "正午"
    elif 14 <= hour < 17: period = "下午"
    elif 17 <= hour < 19: period = "傍晚"
    elif 19 <= hour < 22: period = "夜晚"
    else: period = "深夜"
    day = state.get("game_day", 1)
    season_idx = (day % 360) // 90
    seasons = ["春", "夏", "秋", "冬"]
    season = seasons[season_idx]
    loc = state.get("location", "???")
    silver = state.get('silver', 0)
    gold = state.get('gold', 0)
    skills = state.get('skills', {})
    inventory = state.get('inventory', {})

    core_lines = [
        f"时间：第{day}天 {period}({hour}时) | {season}季",
        f"地点：{loc}",
        f"境界：{realm_names[ri]}",
        f"生命：{hp}/{mhp} | 攻击：{state.get('atk',0)} | 防御：{state.get('defense',0)}",
        f"武学修为：{cult} | 银两：{silver} | 铜钱：{gold}",
        f"武功：{', '.join(f'{k}Lv{v}' for k,v in skills.items()) or '无'}",
        f"背包：{', '.join(f'{k}x{v}' for k,v in inventory.items()) or '空'}",
    ]
    core = "\n".join(core_lines)
    parts.append(core)
    budget -= len(core) // 4

    if npc_context and budget > 100:
        npc_text = "\n当前NPC：" + str(npc_context)[:budget // 3]
        parts.append(npc_text)
        budget -= len(npc_text) // 4

    if budget > 100:
        npc_states = state.get("npc_states", {})
        if npc_states:
            mem_lines = []
            for name, s in list(npc_states.items())[:3]:
                mem_lines.append(f"  {name}: {s.get('action', '?')}")
            mem_text = "\nNPC动向：\n" + "\n".join(mem_lines)
            parts.append(mem_text[:budget // 2])

    return ("\n".join(parts), _estimate_tokens("\n".join(parts)))


def show_commands():
    return """可用命令（武侠版）：
  look / 看 / 观察      — 观察当前环境
  go <地点> / 去        — 前往地点（平安镇/龙门客栈/黑风寨/温泉谷/襄阳城/武林秘籍库/回春堂/擂台）
  npcs / 附近           — 查看周围人物
  talk <人物> / 聊      — 与NPC交谈
  practice / 练功       — 修习内功（需灵气之地）
  breakthrough / 突破   — 尝试突破瓶颈
  rest / 休息           — 恢复生命
  wait <n> / 等         — 等待n个时辰
  status / 状态         — 查看自身属性
  map / 地图            — 查看江湖地图
  inventory / 背包      — 查看物品
  help / 帮助           — 显示此帮助
  save / 存             — 保存进度
  quit / 退出           — 保存并离开"""

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "state":
            print(get_state())
        elif sys.argv[1] == "commands":
            print(show_commands())
        elif sys.argv[1] == "world" and len(sys.argv) > 2:
            sys.path.insert(0, os.path.dirname(__file__))
            from xiuxian_world import GameState, WorldEngine, time_str
            state = GameState.load()
            engine = WorldEngine(state)
            ticks = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 1
            for _ in range(ticks):
                td, events = engine.tick()
            print(json.dumps({"time": td, "events": events}, ensure_ascii=False))
    else:
        print(get_state())
        print()
        print(show_commands())
