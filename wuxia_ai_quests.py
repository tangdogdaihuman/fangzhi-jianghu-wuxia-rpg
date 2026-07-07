"""
wuxia_ai_quests.py - AI-driven quest and event generation system
"""
import json, os, sys, random
from datetime import datetime

SAVE_FILE = "wuxia_ai_quests.json"

QUEST_TYPES = {
    "deliver": "送信/传递物品",
    "escort": "护送某人",
    "defeat": "击败敌人",
    "collect": "收集物品",
    "investigate": "调查事件",
    "rescue": "救援被困者",
    "explore": "探索地点",
    "learn": "学习武功/技能",
    "trade": "商业交易",
    "social": "社交/建立关系",
}

EVENT_TEMPLATES = [
    "你听到前方传来一阵喧哗声，似乎有人在争吵。",
    "路边有一个老人在哭泣，他的财物被抢走了。",
    "你发现地上有一封未拆的信，似乎是某个帮派的密信。",
    "远处传来打斗声，似乎有人正在交手。",
    "一个衣衫褴褛的人倒在路边，似乎受了重伤。",
    "你看到一群人在围着一个告示牌，似乎在讨论什么大事。",
    "天边突然出现异象，一道金光闪过，引起众人惊呼。",
    "你闻到一阵奇异的香气，似乎是从某个方向传来的。",
    "路边的茶馆里有人在议论最近的江湖大事。",
    "你发现地上有一把断剑，剑身上似乎还残留着血迹。",
]


class AIQuestSystem:
    def __init__(self):
        self.quests = {}
        self.events = []
        self.load()

    def load(self):
        try:
            if os.path.exists(SAVE_FILE):
                with open(SAVE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.quests = data.get("quests", {})
                    self.events = data.get("events", [])
        except Exception:
            self.quests = {}
            self.events = []

    def save(self):
        try:
            with open(SAVE_FILE, "w", encoding="utf-8") as f:
                json.dump({"quests": self.quests, "events": self.events}, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def generate_quest(self, location, player_level, context=""):
        qtypes = list(QUEST_TYPES.keys())
        qtype = random.choice(qtypes)
        difficulty = ["简单", "普通", "困难", "极难"][min(player_level // 3, 3)]
        titles = {
            "deliver": ["密信传递", "物品送达", "紧急传书"],
            "escort": ["护送商队", "护送要人", "护送病患"],
            "defeat": ["山贼讨伐", "恶霸清除", "比武挑战"],
            "collect": ["草药采集", "材料收集", "宝物搜寻"],
            "investigate": ["失踪调查", "秘密探查", "真相追寻"],
            "rescue": ["人质救援", "被困救助", "困境脱险"],
            "explore": ["古迹探索", "秘境探险", "禁地探索"],
            "learn": ["武功求教", "秘籍研读", "技艺学习"],
            "trade": ["货物采购", "物品买卖", "商业合作"],
            "social": ["调解纠纷", "结交豪杰", "拜访名士"],
        }
        title = random.choice(titles.get(qtype, ["未知任务"]))
        descs = {
            "deliver": f"有人请求你将一封密信送往{location}附近。",
            "escort": f"一位商人需要你护送他通过{location}的危险地带。",
            "defeat": f"{location}最近出现了一些麻烦，需要有人出手解决。",
            "collect": f"有人急需一些特殊的材料，据说在{location}附近可以找到。",
            "investigate": f"{location}最近发生了一些奇怪的事情，需要调查清楚。",
            "rescue": f"有人被困在{location}附近，急需救援。",
            "explore": f"传闻{location}附近有一处神秘所在，需要有人前去探查。",
            "learn": f"听说{location}有一位高人，可以传授独门技艺。",
            "trade": f"有人需要在{location}进行一笔重要的交易。",
            "social": f"{location}最近有人需要调解一些纠纷。",
        }
        quest = {
            "id": "aiq_" + str(int(datetime.now().timestamp() * 1000) % 100000),
            "title": title,
            "type": qtype,
            "description": descs.get(qtype, f"在{location}发生的一件事情。"),
            "location": location,
            "difficulty": difficulty,
            "level_req": max(1, player_level),
            "rewards": {"silver": random.randint(20, 100) * (player_level + 1), "xp": random.randint(10, 50) * (player_level + 1)},
            "objectives": [{"desc": title, "completed": False}],
            "status": "active",
            "created_at": datetime.now().isoformat(),
        }
        self.quests[quest["id"]] = quest
        self.save()
        return quest

    def complete_quest(self, quest_id):
        if quest_id not in self.quests:
            return None
        quest = self.quests[quest_id]
        quest["status"] = "completed"
        quest["completed_at"] = datetime.now().isoformat()
        for obj in quest.get("objectives", []):
            obj["completed"] = True
        self.save()
        return quest

    def fail_quest(self, quest_id):
        if quest_id not in self.quests:
            return None
        quest = self.quests[quest_id]
        quest["status"] = "failed"
        quest["failed_at"] = datetime.now().isoformat()
        self.save()
        return quest

    def get_active_quests(self):
        return {qid: q for qid, q in self.quests.items() if q.get("status") == "active"}

    def get_completed_quests(self):
        return [q for q in self.quests.values() if q.get("status") == "completed"]

    def get_failed_quests(self):
        return [q for q in self.quests.values() if q.get("status") == "failed"]

    def add_event(self, text, event_type="world", location=None, npc=None):
        event = {
            "id": "evt_" + str(int(datetime.now().timestamp() * 1000) % 100000),
            "text": text, "type": event_type,
            "location": location, "npc": npc,
            "created_at": datetime.now().isoformat(),
        }
        self.events.append(event)
        if len(self.events) > 100:
            self.events = self.events[-100:]
        self.save()
        return event

    def get_random_event(self, location):
        loc_events = [e for e in self.events if e.get("location") == location]
        if loc_events and random.random() < 0.3:
            return random.choice(loc_events)
        if random.random() < 0.15:
            return {"text": random.choice(EVENT_TEMPLATES), "type": "world"}
        return None

    def get_quest_summary(self):
        active = self.get_active_quests()
        completed = self.get_completed_quests()
        return {
            "active_count": len(active),
            "completed_count": len(completed),
            "active_quests": list(active.values()),
            "recent_completed": completed[-5:],
        }


_system = None

def get_system():
    global _system
    if _system is None:
        _system = AIQuestSystem()
    return _system
