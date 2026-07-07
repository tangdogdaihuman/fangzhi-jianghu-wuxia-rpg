#!/usr/bin/env python3
import json, os, sys, shutil, threading
from datetime import datetime
from flask import Flask, request, jsonify, render_template

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from xiuxian_world import GameState, WorldEngine, CommandHandler, format_output
from wuxia_ai import get_state

def get_quest_info(state):
    try:
        from wuxia_integration import get_quest_summary
        return get_quest_summary(state)
    except ImportError:
        return {}

app = Flask(__name__)

# ========== 字段名翻译映射 ==========
响应翻译 = {
    "hp": "生命", "max_hp": "最大生命",
    "atk": "攻击", "defense": "防御",
    "cultivation": "真气",
    "silver": "银两", "gold": "铜钱",
    "skills": "技能", "inventory": "物品栏",
    "location": "地点", "relationship": "关系",
    "game_day": "游戏天数",
    "time_display": "时间显示",
    "realm": "境界", "npcs_here": "人物列表",
    "combat_state": "战斗状态",
    "quest_summary": "任务摘要",
    "flags": "标记",
    "npc_states": "人物状态",
    "ai_status": "人工智能状态",
}

战斗翻译 = {
    "in_combat": "在战斗中",
    "enemy_name": "敌方名称",
    "enemy_level": "敌方等级",
    "enemy_hp": "敌方生命",
    "enemy_max_hp": "敌方最大生命",
    "enemy_cultivation": "敌方真气",
    "enemy_atk": "敌方攻击",
    "player_hp": "我方生命",
    "player_max_hp": "我方最大生命",
    "player_cultivation": "我方真气",
    "round": "回合",
    "log": "日志",
}

def 翻译响应(数据):
    if isinstance(数据, dict):
        result = {}
        for k, v in 数据.items():
            new_key = 响应翻译.get(k, k)
            if isinstance(v, dict):
                if any(x in v for x in ["enemy_name", "enemy_hp", "player_hp", "in_combat"]):
                    result[new_key] = 翻译战斗响应(v)
                else:
                    result[new_key] = 翻译响应(v)
            elif isinstance(v, list):
                result[new_key] = [翻译响应(item) if isinstance(item, dict) else item for item in v]
            else:
                result[new_key] = v
        return result
    elif isinstance(数据, list):
        return [翻译响应(item) for item in 数据]
    return 数据

def 翻译战斗响应(战斗数据):
    if not isinstance(战斗数据, dict):
        return 战斗数据
    result = {}
    for k, v in 战斗数据.items():
        new_key = 战斗翻译.get(k, k)
        result[new_key] = 翻译响应(v) if isinstance(v, (dict, list)) else v
    return result

def 获取任务信息(state):
    try:
        from wuxia_integration import get_quest_summary
        return get_quest_summary(state)
    except ImportError:
        return {}
SAVES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saves")
os.makedirs(SAVES_DIR, exist_ok=True)

# ========== 静态文件路由 ==========
# ========== 中文路由别名 ==========
@app.route("/api/状态")
def api_state_zh():
    return api_state()

@app.route("/api/任务")
def api_quests_zh():
    return api_quests()

@app.route("/api/命令", methods=["POST"])
def api_command_zh():
    return api_command()

@app.route("/api/战斗", methods=["POST"])
def api_combat_zh():
    return api_combat()

@app.route("/api/保存", methods=["POST"])
def api_save_zh():
    return api_save()

@app.route("/api/读取", methods=["POST"])
def api_load_zh():
    return api_load()

@app.route("/api/删除", methods=["POST"])
def api_delete_zh():
    return api_delete()

@app.route("/api/存档")
def api_saves_zh():
    return api_saves()

@app.route("/api/人物")
def api_npcs_zh():
    return api_npcs()

_state_local = threading.local()

def get_engine():
    if not hasattr(_state_local, "engine"):
        state = GameState.load()
        _state_local.engine = WorldEngine(state)
    return _state_local.engine

def get_handler():
    engine = get_engine()
    return CommandHandler(engine, engine.state)

@app.route("/")
def index():
    try:
        from wuxia_integration import get_quest_summary
        from wuxia_quests import MAIN_QUESTS
        qs = get_quest_summary(get_engine().state)
        main_q = qs.get('main_quest')
        main_quest_html = ''
        if main_q:
            main_quest_html = '<div style="color:var(--gold);font-weight:700;margin-bottom:4px;">主线：' + main_q['name'] + '</div>'
            main_quest_html += '<div style="font-size:11px;margin-bottom:4px;">' + main_q['desc'] + '</div>'
            for obj in main_q.get('objectives', []):
                main_quest_html += '<div style="font-size:11px;padding:2px 0;">• ' + obj['desc'] + '</div>'
        else:
            main_quest_html = '<div style="color:var(--text2)">暂无主线任务</div>'
        achs = qs.get('achievements', [])
        if achs:
            main_quest_html += '<div style="color:var(--gold);margin-top:6px;font-size:11px;">成就：' + str(len(achs)) + ' 个</div>'
    except Exception as e:
        import traceback
        traceback.print_exc()
        main_quest_html = '<div style="color:var(--text2)">任务系统加载中...</div>'
    return render_template("index.html", quest_html=main_quest_html)

@app.route("/api/state")
def api_state():
    engine = get_engine()
    s = engine.state
    from wuxia_constants import REALM_NAMES, REALM_ICONS
    realm_names = REALM_NAMES
    realm_icons = REALM_ICONS
    ri = s.realm_index
    td = engine.get_time_display()
    npcs_here = engine.get_npcs_here()

    # Ensure time_display has all fields
    if not td.get('时辰'):
        hour = (td.get('game_time', 0) // 60) % 24
        if 5 <= hour < 7: td['时辰'] = '卯时'
        elif 7 <= hour < 12: td['时辰'] = '辰时'
        elif 12 <= hour < 14: td['时辰'] = '午时'
        elif 14 <= hour < 17: td['时辰'] = '未时'
        elif 17 <= hour < 19: td['时辰'] = '酉时'
        elif 19 <= hour < 22: td['时辰'] = '戌时'
        else: td['时辰'] = '子时'
    if not td.get('时段'):
        td['时段'] = '白天' if 6 <= (td.get('game_time', 0) // 60) % 24 < 18 else '夜晚'
    if not td.get('日期'):
        td['日期'] = getattr(engine.state, 'game_day', 1)
    if not td.get('天气'):
        td['天气'] = '晴朗' 
    try:
        from wuxia_ai_integration import get_ai_status
        ai_status = get_ai_status()
    except ImportError:
        ai_status = {"available": False}
    raw = {
        "time_display": td,
        "realm": {"name": realm_names[ri], "icon": realm_icons[ri], "index": ri},
        "hp": s.hp, "max_hp": s.max_hp,
        "atk": s.atk, "defense": s.defense,
        "cultivation": round(s.cultivation, 1),
        "silver": s.silver, "gold": s.gold,
        "skills": dict(s.skills),
        "inventory": dict(s.inventory),
        "location": s.location,
        "relationship": dict(s.relationship),
        "flags": sorted(list(s.flags)),
        "npcs_here": npcs_here,
        "npc_states": dict(s.npc_states),
        "game_day": s.game_day,
        "combat_state": s.combat_state,
        "quest_summary": get_quest_info(s),
        "ai_status": ai_status,
        "visited": dict(getattr(s, 'visited_locations', {})),
    }
    return jsonify(翻译响应(raw))

@app.route("/api/quests")
def api_quests():
    engine = get_engine()
    try:
        from wuxia_ai_integration import get_quest_info_for_ui
        qs = get_quest_info_for_ui()
        return jsonify({
            "main_quest": qs.get("main_quest"),
            "main_completed": qs.get("main_completed", []),
            "side_active": qs.get("side_active", []),
            "achievements": qs.get("achievements", []),
            "stats": qs.get("stats", {}),
            "ai_quests": qs.get("active_quests", []),
            "completed_ai_quests": qs.get("recent_completed", []),
        })
    except ImportError:
        try:
            from wuxia_integration import get_quest_summary
            qs = get_quest_summary(engine.state)
            return jsonify({
                "main_quest": qs.get("main_quest"),
                "main_completed": qs.get("main_completed", []),
                "side_active": qs.get("side_active", []),
                "achievements": qs.get("achievements", []),
                "stats": qs.get("stats", {}),
            })
        except ImportError:
            return jsonify({"error": "Quest system not loaded"})

@app.route("/api/command", methods=["POST"])
def api_command():
    data = request.get_json()
    cmd = data.get("command", "").strip()
    if not cmd:
        return jsonify({"ok": False, "msg": "请输入命令", "output": ""})
    handler = get_handler()
    engine = get_engine()
    result = handler.process(cmd)
    td = engine.get_time_display()

    # Don't tick during combat
    in_combat = bool(engine.state.combat_state)
    info_cmds = {"status","stat","s","help","?","map","inventory","inv","i","npcs","npc","saves","load","save","combat_status","cs","combat","battle","战斗","attack","defend","skill","use","flee","逃跑","攻击","防御"}
    combat_cmds = {"attack","defend","skill","use","flee","逃跑","攻击","防御","skill","use","flee"}
    should_tick = cmd.split()[0].lower() not in info_cmds and not in_combat
    # Special handling for combat commands
    if cmd.split()[0].lower() in combat_cmds:
        should_tick = False
    if should_tick:
        td2, events = engine.tick()
        if events:
            result["events"] = [{"text": ev["text"], "type": ev.get("type","world")} for ev in events]
    output = format_output(result, td)
    response_data = {
        "ok": result.get("ok", True),
        "输出": output,
        "类型": result.get("type", ""),
    }
    cs = engine.state.combat_state
    if cs:
        cs_dict = {
            "在战斗中": getattr(cs, 'in_combat', False),
            "敌方名称": getattr(cs, 'enemy_name', '???'),
            "敌方等级": getattr(cs, 'enemy_level', 1),
            "敌方生命": getattr(cs, 'enemy_hp', 0),
            "敌方最大生命": getattr(cs, 'enemy_max_hp', 100),
            "敌方真气": getattr(cs, 'enemy_cultivation', 0),
            "敌方攻击": getattr(cs, 'enemy_atk', 0),
            "我方生命": getattr(cs, 'player_hp', 0),
            "我方最大生命": getattr(cs, 'player_max_hp', 100),
            "我方真气": getattr(cs, 'player_cultivation', 0),
            "回合": getattr(cs, 'round', 0),
        }
        response_data["战斗状态"] = cs_dict
    return jsonify(response_data)

@app.route("/api/saves", methods=["GET"])
def api_saves():
    slots = []
    for f in os.listdir(SAVES_DIR):
        if f.endswith(".json") and not f.startswith("."):
            path = os.path.join(SAVES_DIR, f)
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    d = json.load(fh)
                mt = os.path.getmtime(path)
                from wuxia_constants import REALM_NAMES
                realm_names = REALM_NAMES
                ri = d.get("realm_index", 0)
                slots.append({
                    "名称": f.replace(".json", ""),
                    "地点": d.get("location", "?"),
                    "境界": realm_names[ri],
                    "游戏天数": d.get("game_day", 1),
                    "生命": d.get("hp", 0),
                    "最大生命": d.get("max_hp", 0),
                    "真气": round(d.get("cultivation", 0), 1),
                    "更新时间": datetime.fromtimestamp(mt).strftime("%m-%d %H:%M"),
                })
            except:
                pass
    slots.sort(key=lambda x: x["更新时间"], reverse=True)
    return jsonify({"存档": slots})

@app.route("/api/save", methods=["POST"])
def api_save():
    data = request.get_json()
    slot = data.get("slot", "").strip()
    if not slot:
        return jsonify({"成功": False, "消息": "请指定存档名"})
    safe = "".join(c for c in slot if c.isalnum() or c in "-_ ").strip() or "quick"
    path = os.path.join(SAVES_DIR, safe + ".json")
    engine = get_engine()
    engine.state.save()
    try:
        shutil.copy2("wuxia_save.json", path)
        return jsonify({"成功": True, "消息": "已保存: " + safe, "名称": safe})
    except Exception as e:
        return jsonify({"成功": False, "消息": str(e)})

@app.route("/api/load", methods=["POST"])
def api_load():
    data = request.get_json()
    slot = data.get("slot", "").strip()
    if not slot:
        return jsonify({"成功": False, "消息": "请指定存档名"})
    path = os.path.join(SAVES_DIR, slot + ".json")
    if not os.path.exists(path):
        return jsonify({"成功": False, "消息": "存档不存在: " + slot})
    try:
        shutil.copy2(path, "wuxia_save.json")
        if hasattr(_state_local, "engine"):
            delattr(_state_local, "engine")
        return jsonify({"成功": True, "消息": "已读取: " + slot})
    except Exception as e:
        return jsonify({"成功": False, "消息": str(e)})

@app.route("/api/delete", methods=["POST"])
def api_delete():
    data = request.get_json()
    slot = data.get("slot", "").strip()
    path = os.path.join(SAVES_DIR, slot + ".json")
    if not os.path.exists(path):
        return jsonify({"成功": False, "消息": "存档不存在"})
    try:
        os.remove(path)
        return jsonify({"成功": True, "消息": "已删除: " + slot})
    except Exception as e:
        return jsonify({"成功": False, "消息": str(e)})

@app.route("/api/context")
def api_context():
    return jsonify({"context": get_state()})

@app.route("/api/npcs")
def api_npcs():
    engine = get_engine()
    try:
        from wuxia_npc_memory import get_archive
        npcs = get_archive().get_npcs_at_location(engine.state.location)
        return jsonify({"location": engine.state.location, "npcs": npcs})
    except ImportError:
        npcs = [{"id": name, "name": name, "type": "major",
                 "role": data["role"], "personality": data["personality"]}
                for name, data in {
                    "老拳师": {"role": "前辈高人", "personality": "仙风道骨"},
                    "铁匠张伯": {"role": "铸剑师", "personality": "豪爽直率"},
                }.items()]
        return jsonify({"location": engine.state.location, "npcs": npcs})

@app.route("/api/combat", methods=["POST"])
def api_combat():
    data = request.get_json()
    action = data.get("action", "")
    skill = data.get("skill")
    engine = get_engine()

    if action == "start":
        result = engine.start_combat()
    elif action in ("attack", "defend", "skill", "item", "flee"):
        result = engine.combat_action(action, skill)
    elif action == "status":
        cs = engine.get_combat_state()
        if cs:
            result = {"ok": True, "type": "combat_status", "combat": cs.to_dict()}
        else:
            result = {"ok": False, "msg": "不在战斗中"}
    elif action == "end":
        result = engine.end_combat()
    else:
        result = {"ok": False, "msg": "未知战斗命令"}

    td = engine.get_time_display()
    output = format_output(result, td)
    return jsonify({
        "ok": result.get("ok", True),
        "output": output,
        "type": result.get("type", ""),
        "combat_state": engine.state.combat_state,
    })

@app.route("/api/ai-status")
def api_ai_status():
    try:
        from wuxia_ai_integration import get_ai_status
        return jsonify(get_ai_status())
    except ImportError:
        return jsonify({"available": False, "base_url": "", "model": "", "has_key": False})

@app.route("/api/ai-config", methods=["GET", "POST"])
def api_ai_config():
    try:
        from wuxia_api import get_config, save_config, init_config, is_api_available
        if request.method == "POST":
            data = request.get_json()
            api_key = data.get("api_key", "")
            base_url = data.get("base_url", "")
            model = data.get("model", "")
            config = init_config(
                api_key=api_key if api_key else None,
                base_url=base_url if base_url else None,
                model=model if model else None,
            )
            return jsonify({"ok": True, "config": {
                "base_url": config.get("base_url", ""),
                "model": config.get("model", ""),
                "has_key": is_api_available(config),
            }})
        config = get_config()
        return jsonify({
            "base_url": config.get("base_url", ""),
            "model": config.get("model", ""),
            "has_key": is_api_available(config),
        })
    except ImportError:
        return jsonify({"error": "AI module not loaded"})

@app.route("/api/quests/ai", methods=["POST"])
def api_ai_quest():
    try:
        from wuxia_ai_integration import generate_ai_quest
        engine = get_engine()
        data = request.get_json() or {}
        level = engine.state.realm_index * 10 + 1
        quest = generate_ai_quest(engine.state.location, level, data.get("context", ""))
        return jsonify({"ok": True, "quest": quest})
    except ImportError:
        return jsonify({"ok": False, "msg": "AI quest system not loaded"})

if __name__ == "__main__":
    print("=" * 50)
    print("  放置江湖 · 武侠传  Web 版")
    print("  浏览器打开: http://localhost:5000")
    print("=" * 50)
    app.run(host="0.0.0.0", port=8080, debug=False)

