"""
wuxia_combat.py - Turn-based combat system
"""
import json, os, sys, random

COMBAT_SAVE_KEY = "combat_state"

REALMS = [
    {"name": "初入江湖", "icon": "🐾", "hp": 100, "atk": 5, "def": 2},
    {"name": "三流高手", "icon": "🗡", "hp": 200, "atk": 12, "def": 5},
    {"name": "二流高手", "icon": "⚔️", "hp": 500, "atk": 28, "def": 12},
    {"name": "一流高手", "icon": "🛡", "hp": 1200, "atk": 65, "def": 28},
    {"name": "宗师",   "icon": "👨‍🦳", "hp": 3000, "atk": 150, "def": 60},
    {"name": "大宗师", "icon": "🌟", "hp": 8000, "atk": 350, "def": 140},
    {"name": "天下第一", "icon": "👑", "hp": 20000,"atk": 800, "def": 320},
]

SKILLS = {
    "基础剑法": {"atk_bonus": 1.0, "desc": "最基础的剑法招式", "type": "physical"},
    "基础掌法": {"atk_bonus": 1.0, "desc": "最常见的掌法", "type": "physical"},
    "基础拳法": {"atk_bonus": 1.0, "desc": "刚猛的拳法", "type": "physical"},
    "轻功": {"atk_bonus": 0.3, "desc": "身法轻盈，闪避提升", "type": "buff", "effect": "dodge_up"},
    "内功心法": {"atk_bonus": 1.2, "desc": "以内力驱动的攻击", "type": "internal"},
    "擒拿手": {"atk_bonus": 1.1, "desc": "控制型武学", "type": "physical", "effect": "stun"},
    "暗器": {"atk_bonus": 0.8, "desc": "远程暗器攻击", "type": "ranged"},
    "金钟罩": {"atk_bonus": 0.5, "desc": "防御型武学", "type": "defense", "effect": "defense_up"},
}

ENEMY_TEMPLATES = {
    "山贼喽啰": {"base_hp": 80, "base_atk": 8, "base_def": 3, "realm_index": 0},
    "受伤镖师": {"base_hp": 150, "base_atk": 15, "base_def": 6, "realm_index": 0},
    "山贼头目": {"base_hp": 300, "base_atk": 25, "base_def": 10, "realm_index": 1},
    "恶霸": {"base_hp": 250, "base_atk": 20, "base_def": 8, "realm_index": 1},
    "高手": {"base_hp": 500, "base_atk": 40, "base_def": 18, "realm_index": 2},
    "武林败类": {"base_hp": 400, "base_atk": 35, "base_def": 15, "realm_index": 2},
    "黑风寨主": {"base_hp": 800, "base_atk": 55, "base_def": 25, "realm_index": 3},
    "神秘高手": {"base_hp": 1200, "base_atk": 80, "base_def": 35, "realm_index": 4},
}


class CombatState:
    def __init__(self):
        self.in_combat = False
        self.round = 0
        self.player_hp = 0
        self.player_max_hp = 0
        self.player_atk = 0
        self.player_def = 0
        self.enemy_name = ""
        self.enemy_hp = 0
        self.enemy_max_hp = 0
        self.enemy_atk = 0
        self.enemy_def = 0
        self.player_skills = []
        self.log = []
        self.result = None  # "victory", "defeat", None
        self.player_defending = False
        self.enemy_defending = False
        self.player_stunned = 0
        self.enemy_stunned = 0
        self.flee_attempts = 0
        self.rewards = {}

    def to_dict(self):
        return {
            "in_combat": self.in_combat,
            "round": self.round,
            "player_hp": self.player_hp,
            "player_max_hp": self.player_max_hp,
            "player_atk": self.player_atk,
            "player_def": self.player_def,
            "enemy_name": self.enemy_name,
            "enemy_hp": self.enemy_hp,
            "enemy_max_hp": self.enemy_max_hp,
            "enemy_atk": self.enemy_atk,
            "enemy_def": self.enemy_def,
            "player_skills": self.player_skills,
            "log": self.log[-20:],
            "result": self.result,
            "player_defending": self.player_defending,
            "enemy_defending": self.enemy_defending,
            "player_stunned": self.player_stunned,
            "enemy_stunned": self.enemy_stunned,
            "flee_attempts": self.flee_attempts,
            "rewards": self.rewards,
        }

    @classmethod
    def from_dict(cls, data):
        cs = cls()
        for k, v in data.items():
            if hasattr(cs, k):
                setattr(cs, k, v)
        return cs


def start_combat(state, enemy_name=None, enemy_template=None):
    cs = CombatState()
    cs.in_combat = True
    cs.round = 1
    cs.player_hp = state.hp
    cs.player_max_hp = state.max_hp
    cs.player_atk = state.atk
    cs.player_def = state.defense
    cs.player_skills = list(state.skills.keys())

    if enemy_template:
        template = enemy_template
    elif enemy_name and enemy_name in ENEMY_TEMPLATES:
        template = ENEMY_TEMPLATES[enemy_name]
    else:
        realm = REALMS[state.realm_index]
        scale = 0.8 + random.random() * 0.4
        template = {
            "base_hp": int(realm["hp"] * 0.6 * scale),
            "base_atk": int(realm["atk"] * 0.7 * scale),
            "base_def": int(realm["def"] * 0.7 * scale),
            "realm_index": state.realm_index,
        }
        enemy_name = "野怪"

    cs.enemy_name = enemy_name
    cs.enemy_hp = template["base_hp"]
    cs.enemy_max_hp = template["base_hp"]
    cs.enemy_atk = template["base_atk"]
    cs.enemy_def = template["base_def"]
    cs.log.append(f"战斗开始！{enemy_name} 出现了！")
    state.combat_state = cs.to_dict()
    return cs


def get_available_skills(state):
    skills = list(state.skills.keys()) if state.skills else ["基础拳法"]
    if "基础内功心法" not in skills:
        skills.append("基础内功心法")
    return skills[:5]


def execute_player_action(cs, state, action, skill_name=None):
    if cs.result:
        return {"ok": False, "msg": "战斗已经结束。"}

    if cs.player_stunned > 0:
        cs.player_stunned -= 1
        cs.round += 1
        cs.log.append(f"你被眩晕了，无法行动！（剩余 {cs.player_stunned} 回合）")
        check_combat_end(cs, state)
        return {"ok": True, "log": cs.log[-1:]}

    cs.player_defending = False
    cs.round += 1

    if action == "attack":
        if not skill_name:
            skill_name = cs.player_skills[0] if cs.player_skills else "基础拳法"
        skill_data = SKILLS.get(skill_name, {"atk_bonus": 1.0, "type": "physical"})
        base_dmg = cs.player_atk * skill_data["atk_bonus"]
        dmg = max(1, int(base_dmg - cs.enemy_def * 0.5))
        crit = random.random() < 0.15
        if crit:
            dmg = int(dmg * 1.5)
            cs.log.append(f"暴击！你用「{skill_name}」攻击，造成 {dmg} 点伤害！")
        else:
            cs.log.append(f"你用「{skill_name}」攻击，造成 {dmg} 点伤害。")
        cs.enemy_hp = max(0, cs.enemy_hp - dmg)
        if skill_data.get("effect") == "stun" and random.random() < 0.3:
            cs.enemy_stunned = 1
            cs.log.append(f"「{skill_name}」击中了要害，{cs.enemy_name} 被眩晕 1 回合！")

    elif action == "defend":
        cs.player_defending = True
        cs.log.append("你摆出防御姿态，准备接下敌人的攻击。")

    elif action == "skill":
        if not skill_name:
            return {"ok": False, "msg": "请选择技能。"}
        if skill_name not in cs.player_skills and skill_name not in SKILLS:
            return {"ok": False, "msg": f"你不会「{skill_name}」。"}
        skill_data = SKILLS.get(skill_name, {"atk_bonus": 1.0, "type": "physical"})
        if skill_data["type"] == "defense":
            cs.player_defending = True
            cs.log.append(f"你施展「{skill_name}」，防御大幅提升。")
        elif skill_data.get("effect") == "dodge_up":
            cs.log.append(f"你施展「{skill_name}」，身形变得轻盈。")
        else:
            base_dmg = cs.player_atk * skill_data["atk_bonus"]
            dmg = max(1, int(base_dmg - cs.enemy_def * 0.5))
            cs.log.append(f"你用「{skill_name}」攻击，造成 {dmg} 点伤害。")
            cs.enemy_hp = max(0, cs.enemy_hp - dmg)

    elif action == "item":
        if not skill_name:
            return {"ok": False, "msg": "请选择物品。"}
        if skill_name == "heal_potion" and state.inventory.get("heal_potion", 0) > 0:
            heal = 50
            cs.player_hp = min(cs.player_max_hp, cs.player_hp + heal)
            state.inventory["heal_potion"] = state.inventory.get("heal_potion", 0) - 1
            cs.log.append(f"你使用了金疮药，恢复 {heal} 点生命。")
        elif skill_name == "bread" and state.inventory.get("bread", 0) > 0:
            heal = 20
            cs.player_hp = min(cs.player_max_hp, cs.player_hp + heal)
            state.inventory["bread"] = state.inventory.get("bread", 0) - 1
            cs.log.append(f"你吃了干粮，恢复 {heal} 点生命。")
        else:
            return {"ok": False, "msg": f"你没有「{skill_name}」。"}
    elif action == "flee":
        cs.flee_attempts += 1
        flee_chance = max(0.2, 0.6 - cs.flee_attempts * 0.1)
        if random.random() < flee_chance:
            cs.result = "flee"
            cs.log.append("你成功逃跑了！")
            cs.in_combat = False
            state.combat_state = None
        else:
            cs.log.append("逃跑失败！")

    check_combat_end(cs, state)
    return {"ok": True, "log": cs.log[-1:]}


def execute_enemy_turn(cs, state):
    if not cs.in_combat or cs.result:
        return

    if cs.enemy_stunned > 0:
        cs.enemy_stunned -= 1
        cs.round += 1
        cs.log.append(f"{cs.enemy_name} 被眩晕，无法行动！")
        check_combat_end(cs, state)
        return

    cs.enemy_defending = False
    action_roll = random.random()
    if action_roll < 0.7:
        dmg = max(1, int(cs.enemy_atk - cs.player_def * (0.6 if cs.player_defending else 0.3)))
        cs.player_hp = max(0, cs.player_hp - dmg)
        defense_note = "（防御姿态减免）" if cs.player_defending else ""
        cs.log.append(f"{cs.enemy_name} 攻击了你，造成 {dmg} 点伤害。{defense_note}")
    elif action_roll < 0.85:
        cs.enemy_defending = True
        cs.log.append(f"{cs.enemy_name} 进入防御姿态。")
    else:
        if random.random() < 0.25:
            cs.player_stunned = 1
            cs.log.append(f"{cs.enemy_name} 使出一记重击！你被眩晕 1 回合！")
        else:
            dmg = max(1, int(cs.enemy_atk * 1.3 - cs.player_def * 0.3))
            cs.player_hp = max(0, cs.player_hp - dmg)
            cs.log.append(f"{cs.enemy_name} 发动猛攻！造成 {dmg} 点伤害！")

    check_combat_end(cs, state)


def check_combat_end(cs, state):
    if cs.enemy_hp <= 0 and cs.result is None:
        cs.result = "victory"
        cs.in_combat = False
        xp_gain = cs.enemy_max_hp // 10
        silver_gain = random.randint(5, 20) * (cs.round // 2 + 1)
        cs.rewards = {"xp": xp_gain, "silver": silver_gain}
        state.cultivation += xp_gain
        state.silver += silver_gain
        cs.log.append(f"胜利！获得 {xp_gain} 武学修为，{silver_gain} 银两。")
        state.combat_state = None
    elif cs.player_hp <= 0 and cs.result is None:
        cs.result = "defeat"
        cs.in_combat = False
        loss = int(state.silver * 0.2)
        state.silver = max(0, state.silver - loss)
        state.hp = state.max_hp // 2
        cs.log.append(f"你被击败了……损失 {loss} 银两。")
        state.combat_state = None

    state.combat_state = cs.to_dict()


def end_combat(state):
    state.combat_state = None


def get_combat_state(state):
    if not state.combat_state:
        return None
    return CombatState.from_dict(state.combat_state)
