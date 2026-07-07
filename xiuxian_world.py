#!/usr/bin/env python3
"""
xiuxian_world.py - 放置江湖 · 武侠世界 核心引擎
运行：python xiuxian_world.py
输出 JSON 格式的世界状态，供 AI GM 读取并驱动叙事
"""

import json, time, random, math
from datetime import datetime, timedelta
from enum import Enum

# ─── 常量 ───
TICK_INTERVAL = 10          # 每 tick 秒数（真实秒）
SAVE_FILE = "wuxia_save.json"

LOCATIONS = [
    "平安镇", "龙门客栈", "黑风寨", "温泉谷",
    "襄阳城", "武林秘籍库", "回春堂", "擂台"
]

REALMS = [
    {"name": "初入江湖", "icon": "🐾", "hp": 100,  "atk": 5,   "def": 2},
    {"name": "三流高手", "icon": "🗡", "hp": 200,  "atk": 12,  "def": 5},
    {"name": "二流高手", "icon": "⚔️", "hp": 500,  "atk": 28,  "def": 12},
    {"name": "一流高手", "icon": "🛡", "hp": 1200, "atk": 65,  "def": 28},
    {"name": "宗师",   "icon": "👨‍🦳", "hp": 3000, "atk": 150, "def": 60},
    {"name": "大宗师", "icon": "🌟", "hp": 8000, "atk": 350, "def": 140},
    {"name": "天下第一", "icon": "👑", "hp": 20000,"atk": 800, "def": 320},
]

# ─── 工具函数 ───
def time_str(game_time):
    h = int(game_time) % 24
    if 5 <= h < 7:   return f"凌晨 {h}时", "dawn"
    if 7 <= h < 12:  return f"上午 {h}时", "morning"
    if 12 <= h < 14: return f"正午 {h}时", "noon"
    if 14 <= h < 17: return f"下午 {h}时", "afternoon"
    if 17 <= h < 19: return f"傍晚 {h}时", "evening"
    if 19 <= h < 22: return f"夜晚 {h}时", "night"
    return f"深夜 {h}时", "midnight"

def get_season(game_day):
    day_of_year = game_day % 360
    if 60 <= day_of_year < 150:  return "春", "🌸 万物复苏，桃花盛开"
    if 150 <= day_of_year < 240: return "夏", "☀️ 烈日炎炎，蝉鸣不止"
    if 240 <= day_of_year < 330: return "秋", "🍂 秋风萧瑟，落叶纷飞"
    return "冬", "❄️ 白雪皑皑，寒风刺骨"

def weather_desc(game_day):
    seed = game_day * 7 + 13
    r = (seed * 9301 + 49297) % 233280 / 233280
    if r < 0.15: return "暴雨倾盆", "rain_storm"
    if r < 0.30: return "细雨蒙蒙", "rain_light"
    if r < 0.45: return "乌云密布", "cloudy"
    if r < 0.60: return "万里晴空", "sunny"
    if r < 0.72: return "微风拂面", "breeze"
    if r < 0.82: return "大雾弥漫", "fog"
    if r < 0.90: return "繁星点点", "clear_night"
    return "月朗星稀", "moonlit"

# ─── NPC 数据库 ───
NPCS = {
    "老拳师": {
        "role": "前辈高人", "location": "平安镇",
        "personality": "仙风道骨，言语玄妙，偶尔会给出武功指点",
        "schedule": {"0-5": "练功", "6-11": "平安镇", "12-14": "回春堂", "15-22": "龙门客栈", "23-23": "练功"},
        "memory": {}, "relationship": 0,
        "dialogues": [
            "少侠且慢，我观你骨骼清奇，似有习武之才。",
            "武学之事，欲速则不达，心静则水清。",
            "昨日我观星象，似有异动……",
            "这瓶金疮药你拿去，对你行走江湖或有裨益。",
            "江湖路漫漫，少侠切莫急躁。",
        ]
    },
    "铁匠张伯": {
        "role": "铸剑师", "location": "龙门客栈",
        "personality": "豪爽直率，爱喝酒，手艺精湛但脾气火爆",
        "schedule": {"0-5": "睡觉", "6-17": "龙门客栈", "18-22": "酒馆", "23-23": "睡觉"},
        "memory": {}, "relationship": 0,
        "dialogues": [
            "嘿！要兵器？我张伯打的剑，整个龙门客栈找不出第二把！",
            "喝酒吗？我请！今天刚酿的，上头！",
            "最近铁矿品质越来越差了……",
            "你那把剑该磨了，来找我，免费！",
        ]
    },
    "说书人吴六": {
        "role": "说书人", "location": "龙门客栈",
        "personality": "机灵鬼，嘴甜，消息灵通",
        "schedule": {"0-6": "睡觉", "7-18": "龙门客栈", "19-22": "酒馆", "23-23": "睡觉"},
        "memory": {}, "relationship": 0,
        "dialogues": [
            "客官请坐！要说这江湖上的故事啊，且听我慢慢道来！",
            "嘿嘿，看你面善，给你说个独家消息。",
            "最近黑风寨那边不太平，您出门小心。",
            "昨天襄阳城来的消息说那边武林盟主又要开比武大会了……",
        ]
    },
    "受伤镖师": {
        "role": "镖师", "location": "黑风寨",
        "personality": "沉默寡言，身受重伤，对世界充满戒备",
        "schedule": {"0-23": "黑风寨"},
        "memory": {}, "relationship": 0,
        "dialogues": [
            "……别过来，我还能打。",
            "黑风寨的山贼……比传说中还凶残……",
            "多谢关心，但我不需要帮助。",
            "小心那为首的人……他的刀法……非同寻常……",
        ]
    },
    "小医师阿青": {
        "role": "医师", "location": "温泉谷",
        "personality": "温柔善良，喜欢研究草药，话不多但很真诚",
        "schedule": {"0-5": "练功", "6-16": "温泉谷", "17-22": "襄阳城", "23-23": "练功"},
        "memory": {}, "relationship": 0,
        "dialogues": [
            "这些草药是我昨天采的，你要不要试试？",
            "习武需要心无杂念，你最近是不是太急了？",
            "师父说我天赋不够……但我相信勤能补拙。",
            "温泉的水有疗伤之效，你受伤了可以来这里泡一泡。",
        ]
    },
    "武痴赵猛": {
        "role": "武痴", "location": "擂台",
        "personality": "好斗，见人就想切磋，输了不服输",
        "schedule": {"0-6": "睡觉", "7-22": "擂台", "23-23": "睡觉"},
        "memory": {}, "relationship": 0,
        "dialogues": [
            "喂！来切磋一场！我保证不收力！",
            "你刚才那招不错，再来一次！",
            "我输了……再来！我还没出全力！",
            "比武台上没有朋友，只有对手！",
        ]
    },
    "看门老者": {
        "role": "守卫", "location": "武林秘籍库",
        "personality": "忠于职守，说话刻板，但对有缘人很客气",
        "schedule": {"0-5": "练功", "6-22": "武林秘籍库", "23-23": "练功"},
        "memory": {}, "relationship": 0,
        "dialogues": [
            "武林秘籍库重地，请自重。",
            "你想借阅秘籍？需要盟主同意。",
            "看你气质不凡，或许是哪门哪派的高徒？",
            "最近夜里总听到阁楼里有声音，也许是耗子吧……",
        ]
    },
    "酒楼掌柜王胖子": {
        "role": "商人", "location": "襄阳城",
        "personality": "圆滑世故，消息灵通，见人说人话",
        "schedule": {"0-4": "睡觉", "5-23": "襄阳城", "23-23": "睡觉"},
        "memory": {}, "relationship": 0,
        "dialogues": [
            "客官里面请！今天有新鲜的江湖菜！",
            "哎哟，最近襄阳城可不太平，您多小心。",
            "我这儿消息最灵通，想知道什么，请我喝一杯就行。",
            "昨天来了个穿紫袍的人，出手阔绰，不知道什么来头。",
        ]
    },
    "郭靖": {
        "role": "大侠", "location": "襄阳城",
        "personality": "忠厚老实，侠肝义胆，守护襄阳城",
        "schedule": {"0-5": "练功", "6-17": "襄阳城", "18-22": "练功", "23-23": "睡觉"},
        "memory": {}, "relationship": 0,
        "dialogues": [
            "少侠你好，襄阳城如今不太平，出门多加小心。",
            "侠之大者，为国为民。这话我记了一辈子。",
            "我夫人黄蓉才智过人，若有疑难不妨找她聊聊。",
            "你内力根基不错，好好修炼，他日必成大器。",
        ]
    },
    "黄蓉": {
        "role": "女侠", "location": "襄阳城",
        "personality": "聪慧过人，古灵精怪，丐帮帮主",
        "schedule": {"0-6": "睡觉", "7-12": "襄阳城", "12-14": "回春堂", "15-22": "龙门客栈", "23-23": "睡觉"},
        "memory": {}, "relationship": 0,
        "dialogues": [
            "你这人看起来倒是有几分机灵，可愿帮我个忙？",
            "我爹桃花岛的武功秘籍多得很，你要是帮了我，送你几本也无妨。",
            "襄阳城防的事，我相公操心太多，我也得帮着出谋划策。",
            "最近丐帮弟兄来报，前方有些异动……",
        ]
    },
    "乔峰": {
        "role": "英雄", "location": "龙门客栈",
        "personality": "豪迈大气，义薄云天，虽身在江湖却心系苍生",
        "schedule": {"0-5": "练功", "6-14": "龙门客栈", "15-22": "黑风寨", "23-23": "练功"},
        "memory": {}, "relationship": 0,
        "dialogues": [
            "好！少侠有胆色，我乔峰交你这个朋友！",
            "人生如酒，难得快意恩仇。来，喝一杯！",
            "我虽身世坎坷，但行侠仗义之心从未改变。",
            "你这一身武功，是跟谁学的？颇有几分门道。",
        ]
    },
    "洪七公": {
        "role": "前辈", "location": "龙门客栈",
        "personality": "贪吃好玩，豪爽不羁，丐帮前任帮主",
        "schedule": {"0-6": "睡觉", "7-12": "龙门客栈", "12-14": "回春堂", "15-19": "平安镇", "20-22": "龙门客栈", "23-23": "睡觉"},
        "memory": {}, "relationship": 0,
        "dialogues": [
            "哎哟！这儿的烧鸡味道不错，比我上次吃的强多了！",
            "小子，我看你根骨不错，要不要学两招降龙十八掌？",
            "行走江湖，最重要的是吃遍天下美食！",
            "欧阳锋那老匹夫最近又不知道在搞什么鬼……",
        ]
    },
    "周伯通": {
        "role": "老顽童", "location": "温泉谷",
        "personality": "天真烂漫，好武成痴，游戏人间",
        "schedule": {"0-5": "睡觉", "6-16": "温泉谷", "17-22": "擂台", "23-23": "睡觉"},
        "memory": {}, "relationship": 0,
        "dialogues": [
            "嘿嘿！我们来玩个游戏好不好？你打我一下，我打你一下！",
            "我左右互搏之术天下无双，想不想学？叫一声师叔我就教你！",
            "这温泉泡着真舒服，瑛姑那家伙要是也在就好了……",
            "快来看！我发现了一套新的拳法！我们一起去试试！",
        ]
    },
    "欧阳锋": {
        "role": "反派", "location": "黑风寨",
        "personality": "阴险狡诈，武功高强，逆练九阴真经后时而疯癫",
        "schedule": {"0-5": "练功", "6-14": "黑风寨", "15-22": "温泉谷", "23-23": "练功"},
        "memory": {}, "relationship": 0,
        "dialogues": [
            "嘿嘿嘿……你小子胆子不小，敢在本大爷面前晃悠。",
            "我的蛤蟆功天下第一！谁敢和我过招？",
            "我义兄洪七公……哼，总有一天要和他决一死战！",
            "九阴真经……九阴真经……在哪里……",
        ]
    },
    "令狐冲": {
        "role": "剑客", "location": "擂台",
        "personality": "潇洒不羁，重情重义，独孤九剑传人",
        "schedule": {"0-6": "睡觉", "7-17": "擂台", "18-22": "龙门客栈", "23-23": "睡觉"},
        "memory": {}, "relationship": 0,
        "dialogues": [
            "人生在世，最重要的就是开心嘛。来，喝一杯！",
            "我这一身剑法，是风清扬前辈所传，至今已无敌手。",
            "小师妹她……唉，不提也罢。",
            "你这家伙倒是有趣，要不要学两招独孤九剑？",
        ]
    },
    "韦小宝": {
        "role": "混混", "location": "龙门客栈",
        "personality": "机灵滑头，贪生怕死，却也重情重义",
        "schedule": {"0-6": "睡觉", "7-14": "龙门客栈", "15-19": "平安镇", "20-22": "龙门客栈", "23-23": "睡觉"},
        "memory": {}, "relationship": 0,
        "dialogues": [
            "兄弟！我韦小宝虽然武功不行，但这嘴皮子功夫天下第一！",
            "我告诉你啊，这江湖上水很深，小心被人卖了还帮人数钱。",
            "我七个老婆……啊不，我七个朋友！个个都是女中豪杰！",
            "想不想发财？我告诉你一个赚钱的门路……",
        ]
    },
}

# ─── 事件库 ───
EVENT_TEMPLATES = {
    "encounter": [
        "{npc}走了过来，向你打了个招呼。",
        "{npc}似乎遇到了什么麻烦，眉头紧锁。",
        "{npc}正在和人激烈地争论着什么。",
        "{npc}看到你，微微点头示意。",
        "{npc}急匆匆地从你身边跑过，好像有什么急事。",
    ],
    "world": [
        "远处传来一阵惊天动地的巨响，整个大地都震了一下。",
        "天边划过一道奇异的光芒，转瞬即逝。",
        "一只信鸽从头顶飞过，嘴里叼着一封信。",
        "风突然变大，卷起漫天尘土，空气中弥漫着一股肃杀的气息。",
        "地面微微震动，似乎是大队人马在远处移动。",
        "一道金光从云层中射下，照亮了半个天空，持续了片刻后消失。",
        "你感觉到空气中的内力突然变得浓郁了一些，似乎有什么变故发生。",
    ],
    "location_specific": {
        "黑风寨": [
            "寨边传来一声长长的狼嚎，震得树叶哗哗作响。",
            "你注意到寨墙上似乎刻着一些帮派标记。",
            "一个巨大的黑影在山谷间一闪而过。",
            "脚下的地面微微松动，似乎有什么人在下面活动。",
        ],
        "温泉谷": [
            "温泉中冒出的热气在阳光下形成了一道绚丽的彩虹。",
            "你看到几只山鹿在泉边饮水，见人来便飞快地逃走了。",
            "泉水散发出的暖意让你感到精神一振。",
        ],
        "武林秘籍库": [
            "阁楼深处传来轻微的翻书声，但那里似乎很久没人进去了。",
            "书架上的灰尘很厚，说明很久没有人翻阅这些典籍了。",
            "你感觉某个角落有一道目光在注视着你。",
        ],
        "擂台": [
            "台上两位高手打得难解难分，围观的众人喝彩连连。",
            "有人打赌下注，气氛热烈。",
            "擂台的木柱上刻满了深深的剑痕，记录着一场场精彩的对决。",
        ],
    }
}

# ─── 游戏状态 ───
class GameState:
    def __init__(self):
        self.game_time = 7 * 60       # 从早上7点开始（分钟）
        self.game_day = 1
        self.location = "平安镇"
        self.realm_index = 0
        self.cultivation = 0
        self.hp = 100
        self.max_hp = 100
        self.atk = 5
        self.defense = 2
        self.silver = 20
        self.gold = 50
        self.skills = {"基础内功心法": 1}
        self.inventory = {"bread": 3, "heal_potion": 1}
        self.quest_log = []
        self.event_queue = []
        self.npc_states = {}
        self.relationship = {}
        self.flags = set()
        self.tick_count = 0
        self.combat_state = None

        # 初始化NPC状态
        for name in NPCS:
            self.npc_states[name] = {"action": " idle", "mood": "normal"}

        # 任务统计
        self.quest_stats = {
            "practice_count": 0, "talk_count": 0,
            "unique_locations": [], "breakthroughs": 0,
        }
        self.combat_state = None

    def to_dict(self):
        return {
            "game_time": self.game_time,
            "game_day": self.game_day,
            "location": self.location,
            "realm_index": self.realm_index,
            "cultivation": self.cultivation,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "atk": self.atk,
            "defense": self.defense,
            "silver": self.silver,
            "gold": self.gold,
            "skills": self.skills,
            "inventory": self.inventory,
            "quest_log": self.quest_log,
            "npc_states": self.npc_states,
            "relationship": self.relationship,
            "flags": list(self.flags),
            "tick_count": self.tick_count,
            "combat_state": self.combat_state,
        }

    @classmethod
    def from_dict(cls, data):
        s = cls()
        for k, v in data.items():
            if k == "flags":
                s.flags = set(v)
            elif k == "npc_states":
                # Merge: keep saved states, add any new NPCs from current NPCS dict
                for npc_name in NPCS:
                    if npc_name not in v:
                        v[npc_name] = {"action": " idle", "mood": "normal"}
                s.npc_states = v
            elif hasattr(s, k):
                setattr(s, k, v)
        return s

    def save(self):
        try:
            with open(SAVE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
        except: pass

    @classmethod
    def load(cls):
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return cls.from_dict(data)
        except:
            return cls()

# ─── 世界引擎 ───
class WorldEngine:
    def __init__(self, state: GameState):
        self.state = state

    def get_time_display(self):
        t, period = time_str(self.state.game_time)
        season, season_desc = get_season(self.state.game_day)
        weather, w_desc = weather_desc(self.state.game_day)
        return {
            "time": t, "period": period,
            "day": self.state.game_day,
            "season": season, "season_desc": season_desc,
            "weather": weather, "weather_desc": w_desc,
            "realm": REALMS[self.state.realm_index],
            "location": self.state.location,
        }

    def get_npcs_here(self):
        return [name for name, n in NPCS.items() if n["location"] == self.state.location]

    def tick(self):
        """推进世界一刻钟"""
        self.state.game_time += 15
        self.state.tick_count += 1

        # 日期推进
        if self.state.game_time >= 24 * 60:
            self.state.game_time -= 24 * 60
            self.state.game_day += 1

        # 恢复 HP
        if self.state.hp < self.state.max_hp:
            self.state.hp = min(self.state.max_hp, self.state.hp + 2)

        # 武学修为自动增长（三流高手以上）
        if self.state.realm_index >= 1:
            realm = REALMS[self.state.realm_index]
            gain = realm["hp"] * 0.001
            self.state.cultivation += gain

        # NPC 移动
        self._update_npcs()

        # 随机事件
        events = self._generate_events()

        # 自动存档
        if self.state.tick_count % 4 == 0:
            self.state.save()

        return self.get_time_display(), events

    def _update_npcs(self):
        hour = (self.state.game_time // 60) % 24
        for name, npc in NPCS.items():
            schedule = npc["schedule"]
            old_loc = npc["location"]
            new_loc = old_loc
            for (time_range, loc) in schedule.items():
                start, end = map(int, time_range.split("-"))
                if start <= hour <= end:
                    new_loc = loc
                    break
            npc["location"] = new_loc
            self.state.npc_states[name]["moved"] = new_loc != old_loc
            self.state.npc_states[name]["action"] = schedule.get(
                f"{hour}-{hour}", "闲逛中"
            )

        # Spawn minor NPCs for the current location
        try:
            from wuxia_npc_memory import get_archive
            archive = get_archive()
            archive.get_or_create_minor_npc(self.state.location)
        except ImportError:
            pass

    def _generate_events(self):
        events = []
        hour = (self.state.game_time // 60) % 24

        # 世界事件（低概率）
        seed = self.state.tick_count * 1337 + 7
        r = ((seed * 9301 + 49297) % 233280) / 233280
        if r < 0.12:
            template = random.choice(EVENT_TEMPLATES["world"])
            events.append({"type": "world", "text": template})

        # 地点特定事件
        loc_events = EVENT_TEMPLATES["location_specific"].get(self.state.location, [])
        if loc_events and random.random() < 0.25:
            events.append({"type": "location", "text": random.choice(loc_events)})

        # NPC 出现事件
        npcs_here = self.get_npcs_here()
        if npcs_here and random.random() < 0.35:
            npc = random.choice(npcs_here)
            templates = EVENT_TEMPLATES["encounter"]
            text = random.choice(templates).format(npc=npc)
            events.append({"type": "encounter", "npc": npc, "text": text})

        # 交易事件
        if random.random() < 0.08:
            events.append({"type": "trade_opportunity", "text": "路过的商人看你面善，主动搭话："})

        return events

    def get_location_info(self):
        loc_descs = {
            "平安镇": "天书大陆边陲的一座宁静小镇，远离江湖喧嚣，民风淳朴",
            "龙门客栈": "天书大陆山脚下的热闹客栈，江湖人士云集，消息四通八达",
            "黑风寨": "天书大陆阴森险峻的山寨，据传有高手盘踞，空气中弥漫着肃杀之气",
            "温泉谷": "天书大陆云雾缭绕的山谷，温泉有疗伤养神之效，常有高人隐居",
            "襄阳城": "天书大陆繁华大城，城墙高耸，武林人士聚集之地，郭靖黄蓉镇守于此",
            "武林秘籍库": "天书大陆古老的藏书楼，据说藏着无数武功秘籍，非有缘人不得入内",
            "回春堂": "天书大陆飘着药香的医馆，大夫医术高明，温泉疗伤闻名江湖",
            "擂台": "天书大陆巨大的演武场，擂台上经常有高手切磋比试，是扬名立万之地",
        }
        desc = loc_descs.get(self.state.location, "一个神秘的地方")
        npcs = self.get_npcs_here()
        return {
            "location": self.state.location,
            "description": desc,
            "npcs_present": npcs,
            "can_practice": self.state.location in ["平安镇", "温泉谷", "黑风寨"],
            "can_rest": self.state.location in ["平安镇", "襄阳城", "龙门客栈"],
        }

    def get_player_status(self):
        realm = REALMS[self.state.realm_index]
        return {
            "realm": realm,
            "cultivation": round(self.state.cultivation, 1),
            "hp": self.state.hp,
            "max_hp": self.state.max_hp,
            "atk": self.state.atk,
            "defense": self.state.defense,
            "silver": self.state.silver,
            "gold": self.state.gold,
            "skills": self.state.skills,
            "inventory": self.state.inventory,
        }

    def get_quest_info(self):
        try:
            from wuxia_integration import get_quest_summary
            return get_quest_summary(self.state)
        except ImportError:
            return {"main_quest": None, "main_completed": [], "side_active": [], "achievements": [], "stats": {}}

    def get_npc_detail(self, npc_name):
        npc = NPCS.get(npc_name)
        if not npc:
            return None
        rel = self.state.relationship.get(npc_name, 0)
        mem = self.state.npc_states.get(npc_name, {})
        return {
            "name": npc_name,
            "role": npc["role"],
            "personality": npc["personality"],
            "location": npc["location"],
            "relationship": rel,
            "memory": mem,
        }

    def travel(self, destination):
        if destination not in LOCATIONS:
            return {"ok": False, "msg": f"未知地点：{destination}。可去：{'、'.join(LOCATIONS)}"}
        if destination == self.state.location:
            return {"ok": False, "msg": f"你已经在 {destination} 了。"}
        self.state.location = destination
        self.state.save()
        return {"ok": True, "msg": f"你来到了 {destination}。"}

    def practice(self):
        loc_info = self.get_location_info()
        if not loc_info["can_practice"]:
            return {"ok": False, "msg": f"{self.state.location} 不适合练功。"}
        realm = REALMS[self.state.realm_index]
        req = realm["hp"] * (self.state.realm_index + 1) * 2
        gained = realm["hp"] * 0.05
        self.state.cultivation += gained
        self.state.quest_stats = getattr(self.state, 'quest_stats', {'practice_count': 0, 'talk_count': 0, 'unique_locations': [], 'breakthroughs': 0})
        self.state.quest_stats['practice_count'] = self.state.quest_stats.get('practice_count', 0) + 1
        msg = f"你运功修炼了一个时辰，内力增长了 {round(gained, 1)} 点。"
        if self.state.cultivation >= req and self.state.realm_index < len(REALMS) - 1:
            msg += f" ⚡ 武学修为已满，可以去突破瓶颈了！"
        return {"ok": True, "msg": msg}

    def breakthrough(self):
        realm = REALMS[self.state.realm_index]
        req = realm["hp"] * (self.state.realm_index + 1) * 2
        if self.state.cultivation < req:
            return {"ok": False, "msg": f"武学修为不足（需要 {req}，当前 {round(self.state.cultivation, 1)}），无法突破瓶颈。"}
        if self.state.realm_index >= len(REALMS) - 1:
            return {"ok": False, "msg": "你已达到最高境界【天下第一】，举世无敌！"}

        # 突破成功率随境界降低
        rate = max(0.3, 0.85 - self.state.realm_index * 0.08)
        if random.random() < rate:
            self.state.realm_index += 1
            new_realm = REALMS[self.state.realm_index]
            self.state.max_hp = new_realm["hp"]
            self.state.hp = new_realm["hp"]
            self.state.atk = new_realm["atk"]
            self.state.defense = new_realm["def"]
            self.state.cultivation = 0
            self.state.save()
            return {"ok": True, "success": True, "msg": f"🌟 突破成功！恭喜踏入 {new_realm['icon']}【{new_realm['name']}】！"}
        else:
            loss = self.state.cultivation * 0.3
            self.state.cultivation -= loss
            self.state.save()
            return {"ok": True, "success": False, "msg": f"💥 突破失败！内力岔气，损失 {round(loss, 1)} 点武学修为。"}

    def start_combat(self, enemy_name=None, enemy_template=None):
        from wuxia_combat import start_combat as sc
        if self.state.combat_state:
            return {"ok": False, "msg": "你已经在战斗中了！"}
        cs = sc(self.state, enemy_name, enemy_template)
        self.state.save()
        return {"ok": True, "type": "combat_start", "combat": cs.to_dict()}

    def combat_action(self, action, skill_name=None):
        from wuxia_combat import execute_player_action, execute_enemy_turn, get_available_skills, CombatState
        cs_data = self.state.combat_state
        if not cs_data:
            return {"ok": False, "msg": "当前不在战斗中。"}

        # Convert dict to CombatState if needed
        cs = cs_data if isinstance(cs_data, CombatState) else CombatState.from_dict(cs_data)

        # Sync HP from combat state to main state
        self.state.hp = cs.player_hp
        self.state.max_hp = cs.player_max_hp

        if cs.result:
            self.state.combat_state = None
            self.state.save()
            return {"ok": False, "msg": "战斗已经结束。"}

        if cs.player_stunned > 0:
            cs.player_stunned -= 1
            cs.round += 1
            cs.log.append(f"你被眩晕了，无法行动！（剩余 {cs.player_stunned} 回合）")
            self.state.combat_state = cs.to_dict()
            self.state.save()
            return {"ok": True, "type": "combat_round", "combat": cs.to_dict(), "log": cs.log[-1:]}

        if action in ("skills", "items", "技能", "物品"):
            if action in ("skills", "技能"):
                skills = get_available_skills(self.state)
                return {"ok": True, "type": "combat_info", "skills": skills}
            items = {k: v for k, v in self.state.inventory.items() if v > 0 and k in ("heal_potion", "bread")}
            return {"ok": True, "type": "combat_info", "items": items}

        if cs.result:
            return {"ok": False, "msg": "战斗已经结束。"}

        result = execute_player_action(cs, self.state, action, skill_name)
        if not result.get("ok"):
            return result

        self.state.combat_state = cs.to_dict()
        self.state.hp = cs.player_hp
        self.state.max_hp = cs.player_max_hp

        if cs.result:
            self.state.combat_state = None
            self.state.save()
            return {"ok": True, "type": "combat_end", "result": cs.result,
                    "combat": cs.to_dict(), "log": cs.log}

        execute_enemy_turn(cs, self.state)

        self.state.combat_state = cs.to_dict()
        self.state.hp = cs.player_hp
        self.state.max_hp = cs.player_max_hp

        if cs.result:
            self.state.combat_state = None
            self.state.save()
            return {"ok": True, "type": "combat_end", "result": cs.result,
                    "combat": cs.to_dict(), "log": cs.log}

        self.state.save()
        return {"ok": True, "type": "combat_round", "combat": cs.to_dict(),
                "log": cs.log[-3:]}

    def end_combat(self):
        from wuxia_combat import end_combat
        end_combat(self.state)
        return {"ok": True, "msg": "战斗结束。"}

    def get_combat_state(self):
        if not self.state.combat_state:
            return None
        from wuxia_combat import get_combat_state
        return get_combat_state(self.state)

    def talk(self, npc_name):
        from wuxia_npc_memory import get_archive
        from wuxia_ai_integration import generate_npc_dialogue, record_npc_interaction

        # Check major NPCs first
        npc = NPCS.get(npc_name)
        archive = get_archive()

        # If not a major NPC, check minor NPCs
        if not npc:
            ctx = archive.get_npc_context(npc_name)
            if not ctx:
                return {"ok": False, "msg": "这里没有这个人。"}
            # It's a minor NPC
            if archive.memories.get(npc_name, {}).get("location") != self.state.location:
                return {"ok": False, "msg": f"{npc_name} 不在 {self.state.location}。"}

            # Try AI dialogue for minor NPCs
            ai_result = generate_npc_dialogue(npc_name, context=f"在{self.state.location}遇到{npc_name}")
            if ai_result and ai_result.get("type") == "ai_generated":
                dialogue = ai_result["dialogue"]
                archive.record_interaction(npc_name, dialogue)
                self.state.relationship[npc_name] = self.state.relationship.get(npc_name, 0) + 1
                self.state.save()
                return {"ok": True, "type": "talk", "npc": npc_name,
                        "role": ctx.get("role", "路人"),
                        "personality": ctx.get("personality", ""),
                        "dialogue": dialogue,
                        "relationship": self.state.relationship[npc_name],
                        "dialogue_type": "ai"}

            # Fallback static dialogue
            static_dialogues = [
                f"「{npc_name}」看了你一眼，似乎没什么想说的。",
                f"「{npc_name}」点了点头，继续忙自己的事。",
                f"「{npc_name}」微微点头，算是打过招呼了。",
            ]
            dialogue = random.choice(static_dialogues)
            archive.record_interaction(npc_name, dialogue)
            self.state.relationship[npc_name] = self.state.relationship.get(npc_name, 0) + 1
            self.state.save()
            return {"ok": True, "type": "talk", "npc": npc_name,
                    "role": ctx.get("role", "路人"),
                    "personality": ctx.get("personality", ""),
                    "dialogue": dialogue,
                    "relationship": self.state.relationship[npc_name],
                    "dialogue_type": "static"}

        # Major NPC - check location
        if npc["location"] != self.state.location:
            return {"ok": False, "msg": f"{npc_name} 不在 {self.state.location}，目前似乎在 {npc['location']}。"}

        # Try AI dialogue for major NPCs
        ai_result = generate_npc_dialogue(npc_name)
        if ai_result and ai_result.get("type") == "ai_generated":
            dialogue = ai_result["dialogue"]
            archive.record_interaction(npc_name, dialogue)
            self.state.relationship[npc_name] = self.state.relationship.get(npc_name, 0) + 1
            self.state.quest_stats["talk_count"] = self.state.quest_stats.get("talk_count", 0) + 1
            self.state.save()
            return {"ok": True, "type": "talk", "npc": npc_name, "role": npc["role"],
                    "personality": npc["personality"],
                    "dialogue": dialogue, "relationship": self.state.relationship[npc_name],
                    "dialogue_type": "ai"}

        # Fallback to static dialogue
        dialogue = random.choice(npc["dialogues"])
        archive.record_interaction(npc_name, dialogue)
        self.state.relationship[npc_name] = self.state.relationship.get(npc_name, 0) + 1
        self.state.quest_stats["talk_count"] = self.state.quest_stats.get("talk_count", 0) + 1
        self.state.save()
        return {"ok": True, "type": "talk", "npc": npc_name, "role": npc["role"],
                "personality": npc["personality"],
                "dialogue": dialogue, "relationship": self.state.relationship[npc_name],
                "dialogue_type": "static"}

    def get_npcs_here(self):
        try:
            from wuxia_npc_memory import get_archive
            return [n["id"] for n in get_archive().get_npcs_at_location(self.state.location)]
        except ImportError:
            return [name for name, n in NPCS.items() if n["location"] == self.state.location]

    def wait(self, hours=1):
        self.state.game_time += hours * 60
        if self.state.game_time >= 24 * 60:
            self.state.game_time -= 24 * 60
            self.state.game_day += 1
        self._update_npcs()
        self.state.save()
        t, _ = time_str(self.state.game_time)
        return {"ok": True, "msg": f"你原地等候了 {hours} 个时辰，现在已是 {t}。"}

    def status(self):
        return self.get_player_status()

    def look(self):
        return self.get_location_info()

    def inventory(self):
        return self.get_player_status()["inventory"]

# ─── 命令处理 ───
class CommandHandler:
    def __init__(self, engine: WorldEngine, state: GameState):
        self.engine = engine
        self.state = state

    def process(self, cmd: str) -> dict:
        parts = cmd.strip().lower().split()
        if not parts:
            return {"ok": True, "msg": ""}

        action = parts[0]

        if action in ("look", "l", "看", "观察"):
            info = self.engine.look()
            npcs_str = "、".join(info["npcs_present"]) if info["npcs_present"] else "无"
            return {"ok": True, "type": "look", "data": {
                "location": info["location"],
                "description": info["description"],
                "npcs": info["npcs_present"],
                "time_display": self.engine.get_time_display(),
            }}

        elif action in ("go", "move", "去", "前往"):
            if len(parts) < 2:
                return {"ok": False, "msg": "去哪里？用法：go <地点名>"}
            dest = parts[1]
            if dest in ("town", "镇"): dest = "龙门客栈"
            if dest in ("village", "村"): dest = "平安镇"
            if dest in ("city", "城"): dest = "襄阳城"
            if dest in ("cave", "寨"): dest = "黑风寨"
            if dest in ("valley", "谷"): dest = "温泉谷"
            if dest in ("pavilion", "阁"): dest = "武林秘籍库"
            if dest in ("arena", "场"): dest = "擂台"
            if dest in ("lab", "丹房"): dest = "回春堂"
            return self.engine.travel(dest)

        elif action in ("practice", "cultivate", "meditate", "修炼", "练功"):
            return self.engine.practice()

        elif action in ("breakthrough", "bt", "突破"):
            return self.engine.breakthrough()

        elif action in ("combat", "battle", "战斗", "combat"):
            return self.engine.start_combat()

        elif action in ("attack", "a", "攻击", "打"):
            skill = " ".join(parts[1:]) if len(parts) > 1 else None
            return self.engine.combat_action("attack", skill)

        elif action in ("defend", "d", "防御", "挡"):
            return self.engine.combat_action("defend")

        elif action in ("skill", "spell", "技能"):
            skill = " ".join(parts[1:]) if len(parts) > 1 else None
            return self.engine.combat_action("skill", skill)

        elif action in ("use", "item", "使用", "药"):
            item = " ".join(parts[1:]) if len(parts) > 1 else "heal_potion"
            return self.engine.combat_action("item", item)

        elif action in ("flee", "run", "逃跑", "逃"):
            return self.engine.combat_action("flee")

        elif action in ("combat_status", "cs", "战斗状态"):
            cs = self.engine.get_combat_state()
            if not cs:
                return {"ok": False, "msg": "当前不在战斗中。"}
            return {"ok": True, "type": "combat_status", "combat": cs.to_dict()}

        elif action in ("end_combat", "quit_combat", "结束战斗"):
            return self.engine.end_combat()

        elif action in ("talk", "speak", "说话", "交谈", "聊"):
            if len(parts) < 2:
                npcs = self.engine.get_npcs_here()
                if not npcs:
                    return {"ok": False, "msg": "周围没有人可以交谈。"}
                return {"ok": False, "msg": f"想和谁说话？这里能看到：{'、'.join(npcs)}"}
            target = parts[1]
            # 模糊匹配
            matched = None
            for n in NPCS:
                if target in n or n in target:
                    matched = n
                    break
            if not matched:
                return {"ok": False, "msg": f"没有叫「{target}」的人。"}
            return self.engine.talk(matched)

        elif action in ("rest", "sleep", "休息", "睡觉"):
            return self.engine.rest()

        elif action in ("wait", "等", "等待"):
            hours = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 1
            return self.engine.wait(hours)

        elif action in ("status", "stat", "s", "状态", "属性"):
            return {"ok": True, "type": "status", "data": self.engine.status(),
                    "time": self.engine.get_time_display()}

        elif action in ("help", "?", "帮助", "help"):
            return {"ok": True, "type": "help"}

        elif action in ("inventory", "inv", "i", "背包", "物品"):
            return {"ok": True, "type": "inventory", "data": self.engine.inventory()}

        elif action in ("npcs", "npc", "人物", "附近"):
            npcs = self.engine.get_npcs_here()
            return {"ok": True, "type": "npcs", "data": {
                "location": self.state.location,
                "npcs": npcs
            }}

        elif action in ("travel", "map", "地图", "地点"):
            return {"ok": True, "type": "map", "data": {
                "current": self.state.location,
                "all": LOCATIONS,
                "time": self.engine.get_time_display(),
            }}

        elif action in ("region", "regions", "区域"):
            return {"ok": True, "type": "region"}

        elif action in ("quest", "任务", "quests"):
            return {"ok": True, "type": "quest", "data": self.engine.get_quest_info()}

        elif action in ("save", "存"):
            self.state.save()
            return {"ok": True, "msg": "💾 进度已保存。"}

        elif action in ("quit", "exit", "退出", "离开"):
            self.state.save()
            return {"ok": True, "quit": True, "msg": "📖 已保存进度，少侠请慢走。"}

        else:
            return {"ok": False, "msg": f"未知命令「{action}」。输入 help 查看可用命令。"}

# ─── 输出格式化 ───
def format_output(result, time_display):
    lines = []

    # 时间栏
    t, period = time_display["time"], time_display["period"]
    icons = {"dawn": "🌅", "morning": "☀️", "noon": "🌞", "afternoon": "🌤", "evening": "🌇", "night": "🌙", "midnight": "🌌"}
    icon = icons.get(period, "🕐")
    lines.append(f"{icon} {time_display['day']}日 | {t} | {time_display['season']}季 | {time_display['weather']}")
    lines.append("─" * 50)

    r = result

    if r.get("type") == "help":
        lines.extend([
            "┌─ 武 侠 世 界 命 令 指 南 ─┐",
            "│ look / 看          — 观察周围环境        │",
            "│ go <地点> / 去     — 前往指定地点        │",
            "│ npcs / 附近        — 查看周围人物        │",
            "│ talk <人物> / 聊   — 与NPC交谈          │",
            "│ practice / 练功    — 修习内功            │",
            "│ breakthrough / 突破— 尝试突破瓶颈       │",
            "│ rest / 休息        — 恢复生命            │",
            "│ combat / 战斗      — 开始战斗            │",
            "│ attack <技能>      — 战斗：攻击          │",
            "│ defend / 防御      — 战斗：防御          │",
            "│ skill <技能>       — 战斗：使用技能      │",
            "│ use <物品>         — 战斗：使用物品      │",
            "│ flee / 逃跑        — 战斗：逃跑          │",
            "│ wait <n> / 等      — 等待n个时辰        │",
            "│ status / 状态      — 查看自身属性        │",
            "│ inventory / 背包   — 查看物品           │",
            "│ map / 地图         — 查看世界地图        │",
            "│ save / 存          — 保存进度           │",
            "│ quit / 退出        — 保存并离开          │",
            "└──────────────────────────┘",
        ])

    elif r.get("type") == "look":
        d = r["data"]
        lines.append(f"📍 {d['location']}")
        lines.append(f"   {d['description']}")
        npcs = d.get("npcs", [])
        if npcs:
            lines.append(f"   👥 这里能看到：{'、'.join(npcs)}")
        else:
            lines.append("   👥 这里空无一人。")

    elif r.get("type") == "status":
        d = r["data"]
        realm = d["realm"]
        lines.append(f"⚔ ═══ 少 侠 状 态 ═══")
        lines.append(f"   境界：{realm['icon']} {realm['name']}")
        lines.append(f"   生命：{d['hp']} / {d['max_hp']}")
        lines.append(f"   攻击：{d['atk']}    防御：{d['defense']}")
        lines.append(f"   武学修为：{round(d['cultivation'], 1)}")
        lines.append(f"   银两：{d['silver']} 💎    铜钱：{d['gold']} 🪙")
        if d["skills"]:
            lines.append(f"   武功秘籍：{'、'.join(f'{k}Lv{v}' for k,v in d['skills'].items())}")
        inv = d["inventory"]
        if inv:
            lines.append(f"   背包：{'、'.join(f'{k}x{v}' for k,v in inv.items())}")
        else:
            lines.append("   背包：空空如也")

    elif r.get("type") == "map":
        d = r["data"]
        lines.append("🗺 ═══ 江 湖 地 图 ═══")
        for loc in d["all"]:
            marker = "◉" if loc == d["current"] else "○"
            lines.append(f"   {marker} {loc}")

    elif r.get("type") == "region":
        try:
            from wuxia_maps import REGIONS
            lines.append("🗺 ═══ 天 书 大 陆 · 区 域 ═══")
            for region, info in REGIONS.items():
                lines.append(f"   【{region}】 {info['desc']}")
                lines.append(f"      等级: {info['level_range']} | 区域: {', '.join(info['areas'][:3])}")
        except ImportError:
            lines.append("🗺 ═══ 江 湖 地 图 ═══")
            for loc in LOCATIONS:
                marker = "◉" if loc == self.state.location else "○"
                lines.append(f"   {marker} {loc}")

    elif r.get("type") == "quest":
        lines.append("📜 ═══ 任 务 追 踪 ═══")
        data = r.get("data", {})
        main_q = data.get('main_quest')
        if main_q:
            lines.append(f"   主线：{main_q['name']} — {main_q['desc']}")
            for obj in main_q.get('objectives', []):
                lines.append(f"   • {obj['desc']}")
        else:
            lines.append("   主线：暂无进行中的主线任务")
        completed = data.get('main_completed', [])
        if completed:
            lines.append(f"   已完成主线：{len(completed)} 个")
        achs = data.get('achievements', [])
        if achs:
            lines.append(f"   成就解锁：{len(achs)} 个")

    elif r.get("type") == "inventory":
        lines.append("🎒 ═══ 背 包 ═══")
        inv = r["data"]
        if not inv:
            lines.append("   空空如也")
        else:
            for k, v in inv.items():
                lines.append(f"   {k} x{v}")

    elif r.get("type") == "npcs":
        d = r["data"]
        lines.append(f"📍 {d['location']} 的人物：")
        if not d["npcs"]:
            lines.append("   这里没有人。")
        else:
            for name in d["npcs"]:
                try:
                    npc = NPCS[name]
                    lines.append(f"   👤 {name}（{npc['role']}）：{npc['personality'][:20]}...")
                except KeyError:
                    lines.append(f"   👤 {name}（路人）")

    elif r.get("type") == "combat_start":
        c = r["combat"]
        lines.append(f"⚔ ═══ 战斗开始！{c['enemy_name']} 出现了！═══")
        lines.append(f"   敌人 HP：{c['enemy_hp']}/{c['enemy_max_hp']}")
        lines.append(f"   你的 HP：{c['player_hp']}/{c['player_max_hp']}")
        skills_str = ", ".join(c['player_skills']) if c.get('player_skills') else "基础拳法"
        lines.append(f"   可用技能：{skills_str}")
        lines.append(f"   命令：attack / defend / skill <技能> / use <物品> / flee")
        for log in c.get("log", []):
            if "战斗开始" not in log:
                lines.append(f"   > {log}")

    elif r.get("type") == "combat_round":
        c = r["combat"]
        lines.append(f"⚔ ═══ 第 {c['round']} 回合 ═══")
        lines.append(f"   你 HP：{c['player_hp']}/{c['player_max_hp']} | 敌人 HP：{c['enemy_hp']}/{c['enemy_max_hp']}")
        for log in r.get("log", []):
            lines.append(f"   > {log}")
        if not c.get("result"):
            lines.append(f"   命令：attack / defend / skill / use / flee")

    elif r.get("type") == "combat_end":
        c = r["combat"]
        result_map = {"victory": "胜利！", "defeat": "战败...", "flee": "逃跑成功"}
        result_text = result_map.get(c.get("result"), "结束")
        lines.append(f"⚔ ═══ 战斗{result_text} ═══")
        lines.append(f"   你的 HP：{c['player_hp']}/{c['player_max_hp']}")
        if c.get("rewards"):
            rwd = c["rewards"]
            lines.append(f"   获得：{rwd.get('xp', 0)} 武学修为，{rwd.get('silver', 0)} 银两")
        for log in c.get("log", [])[-5:]:
            lines.append(f"   > {log}")

    elif r.get("type") == "combat_status":
        c = r["combat"]
        lines.append(f"⚔ ═══ 战斗中 ═══")
        lines.append(f"   回合：{c['round']}")
        lines.append(f"   你 HP：{c['player_hp']}/{c['player_max_hp']}")
        lines.append(f"   敌人 {c['enemy_name']} HP：{c['enemy_hp']}/{c['enemy_max_hp']}")

    else:
        # 普通结果
        if r.get("success"):
            lines.append(f"🎉 {r['msg']}")
        elif not r.get("ok", True):
            lines.append(f"⚠️ {r['msg']}")
        else:
            lines.append(r.get("msg", ""))

        # 对话结果特殊处理
        if r.get("type") == "talk":
            lines.append("")
            lines.append(f"💬 {r['npc']}：「{r['dialogue']}」")
            lines.append(f"   （好感度：{'❤' * min(5, r['relationship'])} {r['relationship']}）")

    return "\n".join(lines)

# ─── 主循环 ───
def main():
    import sys
    state = GameState.load()
    engine = WorldEngine(state)
    handler = CommandHandler(engine, state)

    print("╔══════════════════════════════════════╗")
    print("║      🏯  放 置 江 湖 · 武 侠 传     ║")
    print("║      AI 驱 动 的 江 湖 世 界        ║")
    print("╠══════════════════════════════════════╣")
    print("║   输入 help 查看命令                 ║")
    print("║   输入 quit 保存并退出               ║")
    print("╚══════════════════════════════════════╝")
    print()

    # 输出初始状态
    td = engine.get_time_display()
    print(format_output({"type": "look", "data": engine.look()}, td))
    print()

    if state.tick_count == 0:
        print("👋 欢迎来到武侠世界！你是一个初入江湖的少侠，在平安镇开始了你的江湖之路。")
        print("   输入 help 查看所有可用命令。\n")

    while True:
        try:
            cmd = input("❯ ")
            if not cmd.strip():
                continue

            result = handler.process(cmd)
            td = engine.get_time_display()

            print()
            print(format_output(result, td))
            print()

            if result.get("quit"):
                break

            # 自动推进世界（非战斗状态下）
            if not self.state.combat_state and cmd.strip().lower() not in ("status", "stat", "s", "help", "?", "map", "inventory", "inv", "i", "npcs", "npc"):
                td2, events = engine.tick()
                for ev in events:
                    print(format_output({"msg": ev["text"]}, td2))
                    print()
                # 刷新 NPC 显示
                if result.get("type") in ("look", None):
                    npcs_here = engine.get_npcs_here()
                    if npcs_here:
                        npc_str = "、".join(npcs_here)
                        print(f"   👥 这里能看到：{npc_str}")
                        print()

        except KeyboardInterrupt:
            state.save()
            print("\n📖 已保存进度，少侠请慢走。")
            break
        except EOFError:
            state.save()
            break

if __name__ == "__main__":
    main()
