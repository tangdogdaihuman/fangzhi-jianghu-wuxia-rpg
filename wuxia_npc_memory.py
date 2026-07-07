"""
wuxia_npc_memory.py - NPC memory archive system
"""
import json, os, sys, random, time
from datetime import datetime

SAVE_FILE = "wuxia_npc_memory.json"

LOCATION_NPC_TEMPLATES = {
    "平安镇": [
        {"role": "卖菜农夫", "role_en": "vegetable_vendor", "mobility": "wandering", "trait": "淳朴善良"},
        {"role": "铁匠学徒", "role_en": "blacksmith_apprentice", "mobility": "fixed", "trait": "勤奋好学"},
        {"role": "茶馆老板", "role_en": "teahouse_owner", "mobility": "fixed", "trait": "见多识广"},
        {"role": "砍柴樵夫", "role_en": "woodcutter", "mobility": "wandering", "trait": "沉默寡言"},
        {"role": "小乞丐", "role_en": "beggar_child", "mobility": "wandering", "trait": "机灵鬼"},
    ],
    "龙门客栈": [
        {"role": "店小二", "role_en": "waiter", "mobility": "fixed", "trait": "嘴甜手快"},
        {"role": "过路客商", "role_en": "merchant", "mobility": "wandering", "trait": "见多识广"},
        {"role": "江湖刀客", "role_en": "swordsman", "mobility": "wandering", "trait": "沉默寡言"},
        {"role": "说书人", "role_en": "storyteller", "mobility": "fixed", "trait": "口若悬河"},
        {"role": "跑堂伙计", "role_en": "runner", "mobility": "fixed", "trait": "活泼好动"},
    ],
    "黑风寨": [
        {"role": "山贼喽啰", "role_en": "bandit_minion", "mobility": "fixed", "trait": "凶神恶煞"},
        {"role": "受伤山贼", "role_en": "injured_bandit", "mobility": "fixed", "trait": "痛苦呻吟"},
        {"role": "探子", "role_en": "scout", "mobility": "wandering", "trait": "机警谨慎"},
        {"role": "寨主亲信", "role_en": "chief_aide", "mobility": "fixed", "trait": "目中无人"},
    ],
    "温泉谷": [
        {"role": "采药人", "role_en": "herbalist", "mobility": "wandering", "trait": "精通草药"},
        {"role": "疗伤游客", "role_en": "healing_tourist", "mobility": "wandering", "trait": "面带愁容"},
        {"role": "温泉管理人", "role_en": "spring_keeper", "mobility": "fixed", "trait": "热情好客"},
    ],
    "襄阳城": [
        {"role": "守城兵士", "role_en": "guard", "mobility": "fixed", "trait": "警惕认真"},
        {"role": "街头卖艺人", "role_en": "performer", "mobility": "wandering", "trait": "技艺精湛"},
        {"role": "酒楼小二", "role_en": "inn_staff", "mobility": "fixed", "trait": "嘴甜手快"},
        {"role": "书生", "role_en": "scholar", "mobility": "wandering", "trait": "满腹经纶"},
        {"role": "乞丐头目", "role_en": "beggar_leader", "mobility": "fixed", "trait": "看似乞丐"},
    ],
    "武林秘籍库": [
        {"role": "扫地僧", "role_en": "sweeper", "mobility": "fixed", "trait": "深藏不露"},
        {"role": "借书学者", "role_en": "scholar_reader", "mobility": "wandering", "trait": "沉迷武学"},
        {"role": "藏书管理员", "role_en": "librarian", "mobility": "fixed", "trait": "认真负责"},
    ],
    "回春堂": [
        {"role": "抓药伙计", "role_en": "medicine_helper", "mobility": "fixed", "trait": "手脚麻利"},
        {"role": "求医患者", "role_en": "patient", "mobility": "wandering", "trait": "愁眉苦脸"},
        {"role": "大夫", "role_en": "doctor", "mobility": "fixed", "trait": "医术高明"},
    ],
    "擂台": [
        {"role": "比武选手", "role_en": "fighter", "mobility": "wandering", "trait": "好胜心强"},
        {"role": "押注赌徒", "role_en": "gambler", "mobility": "wandering", "trait": "赌性大发"},
        {"role": "裁判", "role_en": "referee", "mobility": "fixed", "trait": "公平公正"},
        {"role": "观众", "role_en": "spectator", "mobility": "wandering", "trait": "热血沸腾"},
    ],
}

MAJOR_NPCS = {
    "老拳师": {"role": "前辈高人", "personality": "仙风道骨，言语玄妙"},
    "铁匠张伯": {"role": "铸剑师", "personality": "豪爽直率，爱喝酒"},
    "说书人吴六": {"role": "说书人", "personality": "机灵鬼，嘴甜"},
    "受伤镖师": {"role": "镖师", "personality": "沉默寡言，身受重伤"},
    "小医师阿青": {"role": "医师", "personality": "温柔善良，话不多"},
    "武痴赵猛": {"role": "武痴", "personality": "好斗，见人就想切磋"},
    "看门老者": {"role": "守卫", "personality": "忠于职守，说话刻板"},
    "酒楼掌柜王胖子": {"role": "商人", "personality": "圆滑世故，消息灵通"},
    "郭靖": {"role": "大侠", "personality": "忠厚老实，侠肝义胆"},
    "黄蓉": {"role": "女侠", "personality": "聪慧过人，古灵精怪"},
    "乔峰": {"role": "英雄", "personality": "豪迈大气，义薄云天"},
    "洪七公": {"role": "前辈", "personality": "贪吃好玩，豪爽不羁"},
    "周伯通": {"role": "老顽童", "personality": "天真烂漫，好武成痴"},
    "欧阳锋": {"role": "反派", "personality": "阴险狡诈，武功高强"},
    "令狐冲": {"role": "剑客", "personality": "潇洒不羁，重情重义"},
    "韦小宝": {"role": "混混", "personality": "机灵滑头，贪生怕死"},
}


class NPCMemoryArchive:
    def __init__(self):
        self.memories = {}
        self.load()

    def load(self):
        try:
            if os.path.exists(SAVE_FILE):
                with open(SAVE_FILE, "r", encoding="utf-8") as f:
                    self.memories = json.load(f)
        except Exception:
            self.memories = {}

    def save(self):
        try:
            with open(SAVE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.memories, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def get_or_create_minor_npc(self, location, template=None):
        loc_templates = LOCATION_NPC_TEMPLATES.get(location, [])
        if not loc_templates:
            return None, None
        existing = []
        for npc_id, npc_data in self.memories.items():
            if npc_data.get("type") == "minor" and npc_data.get("location") == location:
                existing.append((npc_id, npc_data))
        if existing:
            npc_id, npc_data = random.choice(existing)
            return npc_id, npc_data
        if template is None:
            candidates = [t for t in loc_templates if t["mobility"] == "wandering"]
            if not candidates:
                candidates = loc_templates
            template = random.choice(candidates)
        npc_id = template["role_en"] + "_" + str(int(time.time() * 1000) % 10000)
        npc_data = {
            "type": "minor", "role": template["role"], "role_en": template["role_en"],
            "personality": template["trait"], "location": location, "mobility": template["mobility"],
            "created_at": datetime.now().isoformat(), "last_seen": datetime.now().isoformat(),
            "interactions": 0, "memory": [], "relationship": 0, "is_alive": True, "health": 100,
        }
        self.memories[npc_id] = npc_data
        self.save()
        return npc_id, npc_data

    def record_interaction(self, npc_id, interaction_text, player_action="talk"):
        if npc_id not in self.memories:
            return
        npc = self.memories[npc_id]
        npc["interactions"] = npc.get("interactions", 0) + 1
        npc["last_seen"] = datetime.now().isoformat()
        if "memory" not in npc:
            npc["memory"] = []
        npc["memory"].append({"time": datetime.now().isoformat(), "action": player_action, "text": interaction_text})
        if len(npc["memory"]) > 20:
            npc["memory"] = npc["memory"][-20:]
        self.save()

    def update_npc_location(self, npc_id, new_location):
        if npc_id in self.memories:
            self.memories[npc_id]["location"] = new_location
            self.memories[npc_id]["last_seen"] = datetime.now().isoformat()
            self.save()

    def get_npcs_at_location(self, location):
        result = []
        for name, data in MAJOR_NPCS.items():
            result.append({"id": name, "name": name, "type": "major", "role": data["role"], "personality": data["personality"]})
        for npc_id, npc_data in self.memories.items():
            if npc_data.get("type") == "minor" and npc_data.get("location") == location and npc_data.get("is_alive", True):
                result.append({"id": npc_id, "name": npc_data.get("role", npc_id), "type": "minor", "role": npc_data.get("role", "路人"), "personality": npc_data.get("personality", "普通"), "mobility": npc_data.get("mobility", "wandering")})
        return result

    def get_npc_context(self, npc_id):
        if npc_id in MAJOR_NPCS:
            return MAJOR_NPCS[npc_id]
        npc = self.memories.get(npc_id)
        if npc:
            return {"role": npc.get("role", "路人"), "personality": npc.get("personality", "普通"), "memory": npc.get("memory", [])[-5:], "relationship": npc.get("relationship", 0)}
        return None

    def set_npc_dead(self, npc_id):
        if npc_id in self.memories:
            self.memories[npc_id]["is_alive"] = False
            self.save()

    def get_available_minor_npcs(self):
        return {nid: ndata for nid, ndata in self.memories.items() if ndata.get("type") == "minor" and ndata.get("is_alive", True)}


_archive = None

def get_archive():
    global _archive
    if _archive is None:
        _archive = NPCMemoryArchive()
    return _archive
