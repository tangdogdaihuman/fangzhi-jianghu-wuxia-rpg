"""
wuxia_ai_integration.py - Main AI integration module
Connects AI API to NPC dialogue, quest generation, and event generation
"""
import json, os, sys, random
from datetime import datetime

from wuxia_api import get_config, is_api_available, call_api
from wuxia_npc_memory import get_archive, MAJOR_NPCS, MEMORY_TIERS
from wuxia_ai_quests import get_system as get_quest_system, QUEST_TYPES, EVENT_TEMPLATES


def get_ai_status():
    config = get_config()
    available = is_api_available(config)
    return {
        "available": available,
        "base_url": config.get("base_url", ""),
        "model": config.get("model", ""),
        "has_key": bool(config.get("api_key", "")),
    }


def generate_npc_dialogue(npc_id, player_name="少侠", context=""):
    npc_ctx = get_archive().get_npc_context(npc_id)
    if not npc_ctx:
        return None

    if not is_api_available(get_config()):
        if npc_id in MAJOR_NPCS:
            major_dialogues = {
                "老拳师": ["少侠且慢，我观你骨骼清奇，似有习武之才。", "武学之事，欲速则不达，心静则水清。", "江湖路漫漫，少侠切莫急躁。"],
                "铁匠张伯": ["嘿！要兵器？我张伯打的剑，整个龙门客栈找不出第二把！", "喝酒吗？我请！今天刚酿的，上头！"],
                "说书人吴六": ["客官请坐！要说这江湖上的故事啊，且听我慢慢道来！", "最近江湖上可不太平啊……"],
                "受伤镖师": ["……别过来，我还能打。", "黑风寨的山贼……比传说中还凶残……"],
                "小医师阿青": ["这些草药是我昨天采的，你要不要试试？", "习武需要心无杂念，你最近是不是太急了？"],
                "武痴赵猛": ["喂！来切磋一场！我保证不收力！", "你刚才那招不错，再来一次！"],
                "看门老者": ["武林秘籍库重地，请自重。", "你想借阅秘籍？需要盟主同意。"],
                "酒楼掌柜王胖子": ["客官里面请！今天有新鲜的江湖菜！", "哎哟，最近襄阳城可不太平，您多小心。"],
                "郭靖": ["少侠你好，襄阳城如今不太平，出门多加小心。", "侠之大者，为国为民。"],
                "黄蓉": ["你这人看起来倒是有几分机灵，可愿帮我个忙？", "我爹桃花岛的武功秘籍多得很……"],
                "乔峰": ["好！少侠有胆色，我乔峰交你这个朋友！", "人生如酒，难得快意恩仇。来，喝一杯！"],
                "洪七公": ["哎哟！这儿的烧鸡味道不错！", "小子，我看你根骨不错，要不要学两招？"],
                "周伯通": ["嘿嘿！我们来玩个游戏好不好？", "我左右互搏之术天下无双，想不想学？"],
                "欧阳锋": ["嘿嘿嘿……你小子胆子不小，敢在本大爷面前晃悠。", "我的蛤蟆功天下第一！"],
                "令狐冲": ["人生在世，最重要的就是开心嘛。来，喝一杯！", "我这一身剑法，是风清扬前辈所传。"],
                "韦小宝": ["兄弟！我韦小宝虽然武功不行，但这嘴皮子功夫天下第一！", "想不想发财？我告诉你一个赚钱的门路……"],
            }
            dialogues = major_dialogues.get(npc_id, ["……"])
            return {"dialogue": random.choice(dialogues), "type": "static"}
        return None

    role = npc_ctx.get("role", "路人")
    personality = npc_ctx.get("personality", "普通")
    # Use tiered memory compression for AI context
    archive = get_archive()
    memory_summary = archive.get_npc_context_for_ai(npc_id, max_tokens=600)
    if not memory_summary:
        # Fallback to raw memory
        if npc_ctx.get("memory"):
            recent = npc_ctx["memory"][-3:]
            memory_summary = "记忆：" + "；".join([m.get("text", m)[:30] for m in recent])

    prompt = f"你是武侠角色【{npc_id}】，身份：{role}。性格：{personality}。{memory_summary}"
    prompt += f" 现在{player_name}来找你交谈。"
    if context:
        prompt += f" 当前情境：{context}"
    prompt += " 请用金庸武侠文笔，以第一人称回复。回复要简洁（30-80字），符合角色性格。不要说你是AI。直接输出对话内容，不要加引号。"

    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": f"{player_name}走近了你，开口说道：" + (context or "你好")},
    ]
    result = call_api(get_config(), messages, temperature=0.9, max_tokens=200)
    if result and not result.startswith("ERROR:"):
        dialogue = result.strip().strip('"').strip()
        # Update NPC mind with inner thoughts after dialogue
        _update_npc_mind(npc_id, dialogue, player_name)
        return {"dialogue": dialogue, "type": "ai_generated"}
    return None


def _update_npc_mind(npc_id, dialogue, player_name):
    """Update NPC mind with inner thoughts after dialogue exchange."""
    try:
        archive = get_archive()
        mind = archive.get_mind(npc_id)
        if not mind:
            return
        if not is_api_available(get_config()):
            # Static fallback based on personality keywords
            p = mind.personality
            if any(k in p for k in ["豪爽", "侠", "忠厚"]):
                thoughts = {"feeling": "欣慰"}
            elif any(k in p for k in ["机灵", "滑头", "聪明"]):
                thoughts = {"feeling": "有趣"}
            elif any(k in p for k in ["天真", "烂漫"]):
                thoughts = {"feeling": "开心"}
            elif any(k in p for k in ["阴险", "狡诈"]):
                thoughts = {"feeling": "审视"}
            elif any(k in p for k in ["温柔", "善良"]):
                thoughts = {"feeling": "善意"}
            else:
                thoughts = {"feeling": "平静"}
            archive.update_mind_thoughts(npc_id, thoughts)
            return

        # AI-generated inner thoughts
        mind_summary = archive.get_mind_for_prompt(npc_id)
        prompt_lines = [
            "你是武侠角色【" + npc_id + "】的内心独白生成器。",
            "性格：" + mind.personality,
        ]
        if mind_summary:
            prompt_lines.append("近期内心：" + mind_summary)
        prompt_lines.append(player_name + "刚刚对你说：" + dialogue[:80])
        prompt_lines.append("")
        prompt_lines.append("请生成你的内心反应（30-50字），用JSON格式：")
        prompt_lines.append('{"feeling": "当前情绪", "goal": "当前目标"}')
        prompt = "\n".join(prompt_lines)
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": "生成内心独白。"},
        ]
        result = call_api(get_config(), messages, temperature=0.8, max_tokens=100, json_mode=True)
        if result and not result.startswith("ERROR:"):
            try:
                parsed = json.loads(result)
                thoughts = {k: v for k, v in parsed.items() if v}
                archive.update_mind_thoughts(npc_id, thoughts)
            except (json.JSONDecodeError, TypeError):
                pass
    except Exception:
        pass

def generate_ai_quest(location, player_level, context=""):
    quest_sys = get_quest_system()
    quest = quest_sys.generate_quest(location, player_level, context)
    return quest


def generate_ai_event(location, game_day, period):
    if not is_api_available(get_config()):
        if random.random() < 0.3:
            return {"text": random.choice(EVENT_TEMPLATES), "type": "world"}
        return None

    prompt = f"你是武侠世界的旁白者。当前地点：{location}，第{game_day}天，{period}。请生成一个简短的事件描述（20-50字），用金庸武侠文笔。直接输出事件描述，不要加引号。"
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": f"当前在{location}，发生了什么？"},
    ]
    result = call_api(get_config(), messages, temperature=0.8, max_tokens=100)
    if result and not result.startswith("ERROR:"):
        return {"text": result.strip().strip('"').strip(), "type": "ai_event"}
    return None


def record_npc_interaction(npc_id, text, action="talk"):
    get_archive().record_interaction(npc_id, text, action)


def init_quests_for_new_player():
    quest_sys = get_quest_system()
    return quest_sys.get_quest_summary()


def get_quest_info_for_ui():
    quest_sys = get_quest_system()
    return quest_sys.get_quest_summary()
