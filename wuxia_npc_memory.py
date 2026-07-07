"""
wuxia_npc_memory.py - NPC memory archive system with tiered compression and NPC minds
"""
import json, os, sys, random, time, re
from datetime import datetime

SAVE_FILE = "wuxia_npc_memory.json"

# ─── Memory tier constants ──────────────────────────────────────
MEM_RAW = "raw"            # Uncompressed interaction records (last N)
MEM_SHORT = "short"        # LLM-compressed scene summary (~4 actions)
MEM_MEDIUM = "medium"      # LLM-compressed chapter summary (~4 SHORTs)
MEM_PERMANENT = "permanent"  # Permanent facts (identity, relationships, completed quests)

MEMORY_TIERS = [MEM_RAW, MEM_SHORT, MEM_MEDIUM, MEM_PERMANENT]

# Thresholds for auto-compression
RAW_MAX = 8          # keep last 8 raw events before compressing
SHORT_MAX = 4        # keep last 4 short summaries before merging to medium
MEDIUM_MAX = 3       # keep last 3 medium summaries before merging to permanent

# Decay defaults: how many ticks before transient thoughts expire (None = never)
THOUGHT_DECAY_DEFAULTS = {
    "feeling": 5,
    "mood": 5,
    "emotion": 5,
    "goal": None,
    "opinion_of_player": None,
    "secret_plan": None,
}

# Stop words for keyword extraction (CJK-safe: skip short tokens)
_STOP_WORDS = {
    "的", "了", "在", "是", "我", "你", "他", "她", "它", "们", "这", "那", "有", "和",
    "就", "都", "而", "及", "与", "着", "或", "一个", "没有", "不是", "什么", "怎么",
    "the", "and", "for", "that", "this", "with", "you", "your", "are", "was", "were",
    "has", "have", "had", "been", "will", "not", "but", "from", "they", "she", "his",
    "her", "its", "our", "que", "para", "com", "uma", "por", "ele", "ela", "seu", "sua",
    "dos", "das", "nos", "nas", "mais", "como", "tem", "foi", "ser", "ter", "mas",
    "quando", "sobre", "entre", "muito", "pode", "seus", "suas", "ainda", "também",
    "apenas", "cada", "outro", "outra",
}


def _extract_keywords(text):
    """Extract meaningful keywords from text for relevance scoring."""
    if not text:
        return set()
    # Match CJK characters (always meaningful) and Latin words >= 3 chars
    tokens = re.findall(r"[一-鿿]|[a-zA-ZÀ-ÿ]{3,}", text.lower())
    # CJK chars pass if not in stop words (even single-char); Latin needs len>=3
    result = set()
    for t in tokens:
        if t in _STOP_WORDS:
            continue
        # CJK: include if not stop word (single chars are meaningful)
        # Latin: include if len >= 3
        if re.match(r'[一-鿿]', t) or len(t) >= 3:
            result.add(t)
    return result


def _estimate_tokens(text):
    if not text:
        return 0
    return max(1, len(text) // 4)


# ─── NPC Mind (inner thoughts) ─────────────────────────────────

class NPCMind:
    """NPC inner thought model. Tracks transient and persistent mental state."""

    def __init__(self, name, personality="普通"):
        self.name = name
        self.personality = personality
        self.thoughts = {}
        self.thought_updated_at = {}
        self.aliases = []
        self.created_at_tick = 0

    def set_thought(self, key, value, current_tick=0):
        self.thoughts[key] = value
        self.thought_updated_at[key] = current_tick

    def get_thought(self, key):
        return self.thoughts.get(key, "")

    def get_persistent_thoughts(self):
        return {k: v for k, v in self.thoughts.items()
                if THOUGHT_DECAY_DEFAULTS.get(k) is None}

    def get_transient_thoughts(self):
        return {k: v for k, v in self.thoughts.items()
                if THOUGHT_DECAY_DEFAULTS.get(k) is not None}

    def decay_check(self, current_tick):
        expired = []
        for key, thought_val in list(self.thoughts.items()):
            decay_after = THOUGHT_DECAY_DEFAULTS.get(key)
            if decay_after is None:
                continue
            updated = self.thought_updated_at.get(key, 0)
            if (current_tick - updated) >= decay_after:
                expired.append(key)
                del self.thoughts[key]
                del self.thought_updated_at[key]
        return expired

    def to_dict(self):
        return {
            "name": self.name,
            "personality": self.personality,
            "thoughts": dict(self.thoughts),
            "thought_updated_at": dict(self.thought_updated_at),
            "aliases": list(self.aliases),
            "created_at_tick": self.created_at_tick,
        }

    @classmethod
    def from_dict(cls, data):
        mind = cls(data.get("name", "?"), data.get("personality", "普通"))
        mind.thoughts = data.get("thoughts", {})
        mind.thought_updated_at = data.get("thought_updated_at", {})
        mind.aliases = data.get("aliases", [])
        mind.created_at_tick = data.get("created_at_tick", 0)
        return mind


def _is_generic_npc_name(name):
    n = name.lower().strip()
    generic_markers = {
        "卖菜农夫", "铁匠学徒", "茶馆老板", "砍柴樵夫", "小乞丐",
        "店小二", "过路客商", "江湖刀客", "说书人", "跑堂伙计",
        "山贼喽啰", "受伤山贼", "探子", "寨主亲信",
        "采药人", "疗伤游客", "温泉管理人",
        "守城兵士", "街头卖艺人", "酒楼小二", "书生", "乞丐头目",
        "扫地僧", "借书学者", "藏书管理员",
        "抓药伙计", "求医患者", "大夫",
        "比武选手", "押注赌徒", "裁判", "观众",
        "vegetable_vendor", "blacksmith_apprentice", "teahouse_owner",
        "woodcutter", "beggar_child", "waiter", "merchant", "swordsman",
        "storyteller", "runner", "bandit_minion", "injured_bandit",
        "scout", "chief_aide", "herbalist", "healing_tourist",
        "spring_keeper", "guard", "performer", "inn_staff", "scholar",
        "beggar_leader", "sweeper", "scholar_reader", "librarian",
        "medicine_helper", "patient", "doctor", "fighter", "gambler",
        "referee", "spectator",
    }
    return n in generic_markers


# ─── Structured interaction schema ──────────────────────────────
# Each record follows this schema for consistency and searchability.
# {
#     "tick": int, "game_day": int, "timestamp": str,
#     "action": str, "player_text": str, "npc_response": str,
#     "type": str,           # "ai" | "static" | "combat"
#     "outcome": str,        # brief outcome note
#     "relationship_delta": int,
#     "keywords": [str],     # auto-extracted
#     "tier": str,           # "raw" | "short" | "medium" | "permanent"
# }


def _build_structured_interaction(tick=0, game_day=1, action="talk",
                                   player_text="", npc_response="",
                                   i_type="static", outcome="",
                                   rel_delta=0, tier=MEM_RAW):
    text = f"{player_text} {npc_response}"
    return {
        "tick": tick,
        "game_day": game_day,
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "player_text": player_text,
        "npc_response": npc_response,
        "type": i_type,
        "outcome": outcome,
        "relationship_delta": rel_delta,
        "keywords": list(_extract_keywords(text)),
        "tier": tier,
    }


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

MAJOR_NPCS = {}
_MAJOR_NPCS_LOADED = False


def _ensure_major_npcs_loaded():
    """Lazy-load MAJOR_NPCS from xiuxian_world to avoid circular imports."""
    global _MAJOR_NPCS_LOADED, MAJOR_NPCS
    if _MAJOR_NPCS_LOADED:
        return
    _MAJOR_NPCS_LOADED = True
    try:
        from xiuxian_world import NPCS
        for name, data in NPCS.items():
            MAJOR_NPCS[name] = {"role": data["role"], "personality": data["personality"]}
    except ImportError:
        pass
class NPCMemoryArchive:
    def __init__(self):
        self.memories = {}
        self.minds = {}
        self.tick_counter = 0
        self.load()

    def load(self):
        try:
            if os.path.exists(SAVE_FILE):
                with open(SAVE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.memories = data.get("memories", {})
                minds_data = data.get("minds", {})
                for npc_id, mind_data in minds_data.items():
                    self.minds[npc_id] = NPCMind.from_dict(mind_data)
                self.tick_counter = data.get("tick_counter", 0)
        except Exception:
            self.memories = {}
            self.minds = {}
            self.tick_counter = 0

    def reload(self):
        """Discard in-memory state and reload from disk."""
        self.memories = {}
        self.minds = {}
        self.tick_counter = 0
        self.load()

    def save(self):
        try:
            minds_serialized = {nid: m.to_dict() for nid, m in self.minds.items()}
            payload = {
                "memories": self.memories,
                "minds": minds_serialized,
                "tick_counter": self.tick_counter,
                "saved_at": datetime.now().isoformat(),
            }
            with open(SAVE_FILE, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def advance_tick(self):
        """Advance tick counter and decay expired transient thoughts."""
        self.tick_counter += 1
        expired_all = {}
        for npc_id, mind in self.minds.items():
            expired = mind.decay_check(self.tick_counter)
            if expired:
                expired_all[npc_id] = expired
        if self.tick_counter % 20 == 0:
            self.save()
        return expired_all

    # ── Mind management ──────────────────────────────────────────

    def get_or_create_mind(self, npc_id, personality="普通"):
        if npc_id not in self.minds:
            mind = NPCMind(npc_id, personality)
            mind.created_at_tick = self.tick_counter
            self.minds[npc_id] = mind
            self.save()
        else:
            # Update personality if it changed (e.g., loaded from save with older data)
            if personality and self.minds[npc_id].personality != personality:
                self.minds[npc_id].personality = personality
        return self.minds[npc_id]

    def get_mind(self, npc_id):
        return self.minds.get(npc_id)

    def update_mind_thoughts(self, npc_id, thoughts_dict, current_tick=None):
        if current_tick is None:
            current_tick = self.tick_counter
        mind = self.get_or_create_mind(npc_id)
        for key, value in thoughts_dict.items():
            if value:
                mind.set_thought(key, value, current_tick)
        self.save()

    def get_mind_summary(self, npc_id):
        mind = self.minds.get(npc_id)
        if not mind:
            return ""
        parts = []
        for key in ["feeling", "mood", "goal", "opinion_of_player", "secret_plan"]:
            val = mind.get_thought(key)
            if val:
                parts.append(f"{key}: {val}")
        return "; ".join(parts) if parts else ""

    def get_mind_for_prompt(self, npc_id):
        """Get mind info formatted for AI prompt injection (Chinese labels)."""
        mind = self.minds.get(npc_id)
        if not mind:
            return ""
        parts = []
        label_map = {
            "feeling": "情绪", "mood": "心情", "goal": "目标",
            "opinion_of_player": "对玩家的看法", "secret_plan": "秘密计划",
        }
        for key in ["feeling", "mood", "goal", "opinion_of_player", "secret_plan"]:
            val = mind.get_thought(key)
            if val:
                parts.append(f"{label_map.get(key, key)}：{val}")
        return "；".join(parts) if parts else ""

    # ── Tiered memory compression ────────────────────────────────

    def _compress_raw_to_short(self, npc_id):
        npc_data = self.memories.get(npc_id, {})
        all_events = npc_data.get("interactions_structured", [])
        recent = [e for e in all_events if e.get("tier") == MEM_RAW][-4:]
        if not recent:
            return None

        npc_name = npc_data.get("role", npc_id)
        personality = npc_data.get("personality", "普通")

        lines = []
        for ev in recent:
            action = ev.get("action", "?")
            resp = ev.get("npc_response", ev.get("text", ""))[:120]
            ply = ev.get("player_text", "")[:80]
            lines.append(f"[{action}] 玩家:{ply} | {npc_name}:{resp}")

        source_text = "\n".join(lines)
        prompt = (
            f"你是武侠世界的记忆压缩器。将以下与【{npc_name}】（性格：{personality}）"
            f"的互动记录压缩为一段简洁的场景摘要。"
            f"要求：50-80字，保留关键信息，不编造。\n\n"
            f"互动记录：\n{source_text}\n\n"
            f"输出JSON：{{\"summary\": \"...\", \"keywords\": [\"...\"]}}"
        )

        messages = [{"role": "system", "content": prompt},
                    {"role": "user", "content": "压缩。"}]

        try:
            from wuxia_api import call_api, get_config
            result = call_api(get_config(), messages, temperature=0.3, max_tokens=200, json_mode=True)
        except Exception:
            result = None

        summary = ""
        keywords = []
        if result is not None and not result.startswith("ERROR:"):
            try:
                parsed = json.loads(result)
                summary = parsed.get("summary", "")[:200]
                keywords = parsed.get("keywords", [])[:10]
            except (json.JSONDecodeError, TypeError):
                summary = recent[-1].get("npc_response", "")[:100]

        if not summary:
            summary = recent[-1].get("npc_response", "")[:100]

        compressed_ids = {id(e) for e in recent}
        for ev in all_events:
            if id(ev) in compressed_ids:
                ev["tier"] = MEM_SHORT

        return {"summary": summary, "keywords": keywords}

    def _compress_shorts_to_medium(self, npc_id):
        npc_data = self.memories.get(npc_id, {})
        all_events = npc_data.get("interactions_structured", [])
        shorts = [e for e in all_events if e.get("tier") == MEM_SHORT][-SHORT_MAX:]
        if len(shorts) < 2:
            return None

        npc_name = npc_data.get("role", npc_id)
        summaries = [e.get("npc_response", "") for e in shorts]

        prompt = (
            f"将以下与【{npc_name}】的{len(summaries)}个场景摘要合并为一个章节级摘要。"
            f"要求：80-120字，描述与NPC关系的变化。\n\n"
            f"场景摘要：\n" + "\n".join(f"- {s}" for s in summaries) + "\n\n"
            f"输出JSON：{{\"summary\": \"...\"}}"
        )

        messages = [{"role": "system", "content": prompt},
                    {"role": "user", "content": "合并。"}]

        try:
            from wuxia_api import call_api, get_config
            result = call_api(get_config(), messages, temperature=0.3, max_tokens=300, json_mode=True)
        except Exception:
            result = None

        summary = ""
        if result is not None and not result.startswith("ERROR:"):
            try:
                parsed = json.loads(result)
                summary = parsed.get("summary", "")[:300]
            except (json.JSONDecodeError, TypeError):
                summary = "；".join(summaries[-3:])[:200]

        if not summary:
            summary = "；".join(summaries[-3:])[:200]

        compressed_ids = {id(e) for e in shorts}
        for ev in all_events:
            if id(ev) in compressed_ids:
                ev["tier"] = MEM_MEDIUM

        return {"summary": summary}

    def _compress_mediums_to_permanent(self, npc_id):
        npc_data = self.memories.get(npc_id, {})
        all_events = npc_data.get("interactions_structured", [])
        mediums = [e for e in all_events if e.get("tier") == MEM_MEDIUM]
        if len(mediums) < 2:
            return None

        npc_name = npc_data.get("role", npc_id)
        rel = npc_data.get("relationship", 0)
        summaries = [e.get("npc_response", "") for e in mediums]

        prompt = (
            f"将以下与【{npc_name}】的章节摘要提炼为永久记忆。"
            f"当前好感度：{rel}"
            f"要求：100-200字，只保留永久重要信息。\n\n"
            f"章节摘要：\n" + "\n".join(f"- {s}" for s in summaries) + "\n\n"
            f"输出JSON：{{\"summary\": \"...\"}}"
        )

        messages = [{"role": "system", "content": prompt},
                    {"role": "user", "content": "提炼。"}]

        try:
            from wuxia_api import call_api, get_config
            result = call_api(get_config(), messages, temperature=0.2, max_tokens=500, json_mode=True)
        except Exception:
            result = None

        summary = ""
        if result is not None and not result.startswith("ERROR:"):
            try:
                parsed = json.loads(result)
                summary = parsed.get("summary", "")[:400]
            except (json.JSONDecodeError, TypeError):
                summary = "；".join(summaries[-2:])[:300]

        if not summary:
            summary = "；".join(summaries[-2:])[:300]

        npc_data["permanent_memory"] = summary
        compressed_ids = {id(e) for e in mediums}
        for ev in all_events:
            if id(ev) in compressed_ids:
                ev["tier"] = MEM_PERMANENT

        return {"summary": summary}

    def auto_compress_if_needed(self, npc_id):
        npc_data = self.memories.get(npc_id)
        if not npc_data:
            return None
        all_events = npc_data.get("interactions_structured", [])
        raw_count = sum(1 for e in all_events if e.get("tier") == MEM_RAW)
        short_count = sum(1 for e in all_events if e.get("tier") == MEM_SHORT)
        medium_count = sum(1 for e in all_events if e.get("tier") == MEM_MEDIUM)

        compressed = []
        if raw_count >= RAW_MAX:
            result = self._compress_raw_to_short(npc_id)
            if result:
                compressed.append(result)
                self.save()
        if short_count >= SHORT_MAX:
            result = self._compress_shorts_to_medium(npc_id)
            if result:
                compressed.append(result)
                self.save()
        if medium_count >= MEDIUM_MAX:
            result = self._compress_mediums_to_permanent(npc_id)
            if result:
                compressed.append(result)
                self.save()
        return compressed if compressed else None

    def get_npc_context_for_ai(self, npc_id, max_tokens=2000):
        """Build compact AI context from tiered memory within token budget."""
        npc_data = self.memories.get(npc_id)
        if not npc_data:
            return "", 0

        parts = []
        budget = max_tokens

        perm = npc_data.get("permanent_memory", "")
        if perm:
            parts.append(f"[长期记忆] {perm}")
            budget -= _estimate_tokens(parts[-1])

        all_events = npc_data.get("interactions_structured", [])
        mediums = [e for e in all_events if e.get("tier") == MEM_MEDIUM]
        if mediums and budget > 100:
            text = " [章节] " + "；".join(
                e.get("npc_response", "")[:100] for e in mediums[-2:]
            )
            parts.append(text)
            budget -= _estimate_tokens(parts[-1])

        shorts = [e for e in all_events if e.get("tier") == MEM_SHORT]
        if shorts and budget > 100:
            text = " [近期] " + "；".join(
                e.get("npc_response", "")[:80] for e in shorts[-3:]
            )
            parts.append(text)
            budget -= _estimate_tokens(parts[-1])

        raws = [e for e in all_events if e.get("tier") == MEM_RAW]
        if raws and budget > 200:
            text = " [最近] " + "；".join(
                f"{e.get('action','?')}:{e.get('npc_response', '')[:60]}"
                for e in raws[-3:]
            )
            parts.append(text)

        full = "\n".join(parts)
        return full, _estimate_tokens(full)

    # ── Backward-compat minor NPC management ─────────────────────

    def get_or_create_minor_npc(self, location, template=None):
        loc_templates = LOCATION_NPC_TEMPLATES.get(location, [])
        if not loc_templates:
            return None, None
        existing = [(nid, nd) for nid, nd in self.memories.items()
                    if nd.get("type") == "minor" and nd.get("location") == location]
        if existing:
            return random.choice(existing)
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
            "interactions": 0, "relationship": 0, "is_alive": True, "health": 100,
            "memory": [],
            "interactions_structured": [],
            "permanent_memory": "",
            "permanent_facts": [],
        }
        self.memories[npc_id] = npc_data
        self.get_or_create_mind(npc_id, template["trait"])
        self.save()
        return npc_id, npc_data

    def record_interaction(self, npc_id, interaction_text, player_action="talk",
                           player_text="", i_type="static", outcome="", rel_delta=0):
        _ensure_major_npcs_loaded()
        is_major = npc_id in MAJOR_NPCS

        # For major NPCs, ensure a memory entry exists for tiered tracking
        if is_major and npc_id not in self.memories:
            self.memories[npc_id] = {
                "type": "major",
                "role": MAJOR_NPCS[npc_id]["role"],
                "personality": MAJOR_NPCS[npc_id]["personality"],
                "location": "",
                "interactions": 0,
                "relationship": 0,
                "is_alive": True,
                "health": 100,
                "memory": [],
                "interactions_structured": [],
                "permanent_memory": "",
            }

        if npc_id not in self.memories:
            return

        tick = self.tick_counter

        if npc_id in self.memories:
            npc = self.memories[npc_id]
            npc["interactions"] = npc.get("interactions", 0) + 1
            npc["last_seen"] = datetime.now().isoformat()

            if "memory" not in npc:
                npc["memory"] = []
            npc["memory"].append(interaction_text)
            if len(npc["memory"]) > 20:
                npc["memory"] = npc["memory"][-20:]

            if "interactions_structured" not in npc:
                npc["interactions_structured"] = []
            record = _build_structured_interaction(
                tick=tick, game_day=0, action=player_action,
                player_text=player_text, npc_response=interaction_text,
                i_type=i_type, outcome=outcome, rel_delta=rel_delta,
            )
            npc["interactions_structured"].append(record)

            npc["relationship"] = npc.get("relationship", 0) + rel_delta

            self.auto_compress_if_needed(npc_id)
            self.save()

    def update_npc_location(self, npc_id, new_location):
        if npc_id in self.memories:
            self.memories[npc_id]["location"] = new_location
            self.memories[npc_id]["last_seen"] = datetime.now().isoformat()
            self.save()

    def get_npcs_at_location(self, location):
        _ensure_major_npcs_loaded()
        result = []
        for name, data in MAJOR_NPCS.items():
            result.append({"id": name, "name": name, "type": "major",
                           "role": data["role"], "personality": data["personality"]})
        for npc_id, npc_data in self.memories.items():
            if (npc_data.get("type") == "minor"
                    and npc_data.get("location") == location
                    and npc_data.get("is_alive", True)):
                result.append({
                    "id": npc_id, "name": npc_data.get("role", npc_id),
                    "type": "minor", "role": npc_data.get("role", "路人"),
                    "personality": npc_data.get("personality", "普通"),
                    "mobility": npc_data.get("mobility", "wandering"),
                })
        return result

    def get_npc_context(self, npc_id):
        _ensure_major_npcs_loaded()
        if npc_id in MAJOR_NPCS:
            return MAJOR_NPCS[npc_id]
        npc = self.memories.get(npc_id)
        if npc:
            return {
                "role": npc.get("role", "路人"),
                "personality": npc.get("personality", "普通"),
                "memory": npc.get("memory", [])[-5:],
                "relationship": npc.get("relationship", 0),
                "location": npc.get("location", "?"),
                "type": "minor",
            }
        return None

    def get_npc_context_for_ai(self, npc_id, max_tokens=1500):
        _ensure_major_npcs_loaded()
        if npc_id in MAJOR_NPCS:
            return MAJOR_NPCS[npc_id].get("personality", "")
        npc = self.memories.get(npc_id)
        if not npc:
            return ""
        personality = npc.get("personality", "普通")
        relationship = npc.get("relationship", 0)
        parts = [f"性格：{personality}"]
        if relationship != 0:
            parts.append(f"好感度：{relationship}")
        return " | ".join(parts)

    def set_npc_dead(self, npc_id):
        if npc_id in self.memories:
            self.memories[npc_id]["is_alive"] = False
            self.save()

    def get_available_minor_npcs(self):
        return {nid: nd for nid, nd in self.memories.items()
                if nd.get("type") == "minor" and nd.get("is_alive", True)}

    def get_archive_stats(self):
        total_npcs = len(self.memories)
        total_minds = len(self.minds)
        total_interactions = sum(n.get("interactions", 0) for n in self.memories.values())
        tier_counts = {}
        for npc_data in self.memories.values():
            for ev in npc_data.get("interactions_structured", []):
                tier = ev.get("tier", MEM_RAW)
                tier_counts[tier] = tier_counts.get(tier, 0) + 1
        return {
            "total_npcs": total_npcs,
            "total_minds": total_minds,
            "total_interactions": total_interactions,
            "tier_distribution": tier_counts,
            "tick_counter": self.tick_counter,
        }


_archive = None

def get_archive():
    global _archive
    if _archive is None:
        _archive = NPCMemoryArchive()
    return _archive
