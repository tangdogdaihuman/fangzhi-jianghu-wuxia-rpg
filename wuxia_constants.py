"""
wuxia_constants.py - Shared game constants
Single source of truth for realm definitions, locations, etc.
"""

# ─── 境界定义 ──────────────────────────────────────────────────
REALMS = [
    {"name": "初入江湖", "icon": "🐾", "hp": 100,  "atk": 5,   "def": 2},
    {"name": "三流高手", "icon": "🗡", "hp": 200,  "atk": 12,  "def": 5},
    {"name": "二流高手", "icon": "⚔️", "hp": 500,  "atk": 28,  "def": 12},
    {"name": "一流高手", "icon": "🛡", "hp": 1200, "atk": 65,  "def": 28},
    {"name": "宗师",     "icon": "👨‍🦳", "hp": 3000, "atk": 150, "def": 60},
    {"name": "大宗师",   "icon": "🌟", "hp": 8000, "atk": 350, "def": 140},
    {"name": "天下第一", "icon": "👑", "hp": 20000, "atk": 800, "def": 320},
]

# ─── 地点 ──────────────────────────────────────────────────────
LOCATIONS = [
    "平安镇", "龙门客栈", "黑风寨", "温泉谷",
    "襄阳城", "武林秘籍库", "回春堂", "擂台",
]

# ─── 境界名称/图标映射（用于 UI 显示） ──────────────────────────
REALM_NAMES = [r["name"] for r in REALMS]
REALM_ICONS = [r["icon"] for r in REALMS]
