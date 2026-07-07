# 放置江湖 · 武侠传

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![AI Powered](https://img.shields.io/badge/AI-GM_Narrative-green)

AI 驱动的武侠世界放置 RPG。你是一个初入江湖的少侠，在 AI 的驱动下，整个世界实时运转。金庸风格的叙事、回合制战斗、动态任务、NPC 记忆系统——一切皆在江湖中。

> "江湖不是打打杀杀，是人情世故。"

## 快速开始

```bash
# 终端模式
python play_wuxia.py

# Web UI（浏览器打开 http://localhost:8080）
python server.py
```

**Windows 用户请先设置编码：**
```powershell
$env:PYTHONIOENCODING="utf-8"
```

## 游戏特色

### AI GM 叙事
- 输入任意行动指令，AI 用金庸武侠文笔生成叙事
- 世界状态自动推进（时间、天气、季节、NPC 移动、随机事件）
- 世界设定源自 [天书江湖录](https://sillytavernai.com/) 世界书

### 回合制战斗
- 指令式战斗：**攻击 / 防御 / 技能 / 物品 / 逃跑**
- 暴击（15%）、眩晕、防御削减等战斗机制
- 7 种敌人模板，随玩家境界动态 scaling
- 击败敌人获得武学修为（经验）和银两

### NPC 系统（两级架构）
- **16 位主要 NPC**：郭靖、黄蓉、乔峰、洪七公、周伯通、欧阳锋、令狐冲、韦小宝 等，各有固定性格、台词、日程
- **动态 NPC**：每个地点根据场景自动生成（商贩、镖师、书生等），具备记忆存档，会记住与玩家的互动

### 任务系统
- **主线任务**：4 章主线剧情，从初入江湖到位列宗师
- **支线任务**：5 个静态支线 + AI 动态生成（10 种类型：送信、护卫、追敌、收集、调查、救援、探索、学艺、贸易、社交）
- **每日任务** + **8 个成就**

### 七大境界
| 境界 | 说明 |
|------|------|
| 🐾 初入江湖 | 初出茅庐 |
| 🗡 三流高手 | 初窥门径 |
| ⚔️ 二流高手 | 小有所成 |
| 🛡 一流高手 | 名震一方 |
| 👨‍🦳 宗师 | 开宗立派 |
| 🌟 大宗师 | 登峰造极 |
| 👑 天下第一 | 武林至尊 |

### 八大核心场景
平安镇、龙门客栈、黑风寨、温泉谷、襄阳城、武林秘籍库、回春堂、擂台

## 项目结构

```
├── xiuxian_world.py      # 核心引擎：状态管理、世界 tick、命令解析、战斗系统
├── wuxia_api.py          # 通用 OpenAI 兼容 API 客户端
├── wuxia_ai.py           # AI GM 上下文构建（读取状态 + 世界观）
├── wuxia_ai_integration.py # AI 接入：NPC 对话、任务生成、事件生成
├── wuxia_ai_client.py    # 通用 AI 客户端类
├── wuxia_npc_memory.py   # NPC 记忆存档（创建时间、互动历史、好感度）
├── wuxia_ai_quests.py    # AI 动态任务生成（10 种类型）
├── wuxia_combat.py       # 回合制战斗系统
├── wuxia_integration.py  # 任务追踪 + 成就检查 + 桥接静态/AI 任务
├── wuxia_quests.py       # 静态主线/支线/日常/成就定义
├── wuxia_lore.py         # 天书江湖录世界观常量
├── wuxia_maps.py         # 世界地图（8 大区域，35+ 子区域）
├── wuxia_npc_ai.py       # 主要 NPC AI 对话 prompt 定义
├── wuxia_config.json     # AI API 配置（可选，可环境变量代替）
├── server.py             # Flask Web API（终端 + 浏览器）
├── play_wuxia.py         # 终端模式启动器
├── templates/
│   └── index.html        # Web UI（武侠风格单页应用）
└── saves/                # 存档目录
```

## 常用指令

### 移动 & 探索
| 指令 | 说明 |
|------|------|
| `look` / `看` | 观察当前环境 |
| `go <地点>` / `去` | 前往指定地点 |
| `map` / `地图` | 查看江湖地图 |
| `wait <n>` / `等` | 等待 n 个时辰 |

### 交互
| 指令 | 说明 |
|------|------|
| `talk <人物>` / `聊` | 与 NPC 交谈 |
| `npcs` / `附近` | 查看周围人物 |
| `practice` / `练功` | 修习内功 |
| `breakthrough` / `突破` | 尝试境界突破 |
| `rest` / `休息` | 恢复生命 |

### 战斗
| 指令 | 说明 |
|------|------|
| `combat` / `战斗` | 开始战斗 |
| `attack` / `攻击` | 普通攻击 |
| `defend` / `防御` | 防御姿态 |
| `skill` / `技能` | 使用武学技能 |
| `item` / `物品` | 使用物品（治疗） |
| `flee` / `逃跑` | 逃跑 |

### 其他
| 指令 | 说明 |
|------|------|
| `status` / `状态` | 查看自身属性 |
| `inventory` / `背包` | 查看物品 |
| `help` / `帮助` | 显示帮助 |
| `save` / `存` | 保存进度 |

## AI 配置

游戏无需 AI 即可运行（使用静态内容作为 fallback）。开启 AI 后获得完整动态体验：

**方式一：配置文件 `wuxia_config.json`**
```json
{
  "api_key": "your-api-key",
  "base_url": "https://api.stepfun.com/step_plan/v1",
  "model": "step-2-16k"
}
```

**方式二：环境变量**
```bash
# Windows PowerShell
$env:STEPFUN_API_KEY = "your-api-key"

# Linux / macOS
export STEPFUN_API_KEY="your-api-key"
```

支持任何 OpenAI 兼容 API 端点（StepFun、OpenAI、DeepSeek、本地 Ollama 等）。

## Web API

| 端点 | 方法 | 说明 |
|------|------|------|
| `/` | GET | Web UI |
| `/api/state` | GET | 完整游戏状态 |
| `/api/command` | POST | 执行命令 |
| `/api/saves` | GET | 存档列表 |
| `/api/save` | POST | 保存存档 |
| `/api/load` | POST | 读取存档 |
| `/api/quests` | GET | 任务数据 |
| `/api/quests/ai` | POST | 生成 AI 任务 |
| `/api/npcs` | GET | 当前地点 NPC |
| `/api/combat` | POST | 战斗操作 |
| `/api/ai-status` | GET | AI 状态 |
| `/api/ai-config` | GET/POST | AI 配置 |

## 技术栈

- **纯 Python 3**，无外部依赖（Flask 用于 Web 模式）
- **OpenAI 兼容 API** 接口，支持任何 LLM 提供商
- **JSON 持久化**：游戏状态、NPC 记忆、任务数据
- **双语指令**：中文 + English aliases

## AI 增强功能

### 分层记忆系统

NPC 记忆采用四级分层压缩架构，自动管理上下文长度：

| 层级 | 说明 | 保留上限 |
|------|------|---------|
| `raw` | 原始互动记录（完整对话） | 最近 8 条 |
| `short` | LLM 压缩的场景摘要（约4条互动） | 最近 4 条 |
| `medium` | LLM 压缩的章节摘要（约4个场景） | 最近 3 条 |
| `permanent` | 永久事实（身份、关系、已完成任务） | 无上限 |

每次世界 tick 自动检查压缩阈值，无需手动干预。记忆数据持久化到 `wuxia_npc_memory.json`。

### NPC 内心世界

每个 NPC 拥有独立的 `NPCMind`，追踪内心状态：

- **持久想法**：对玩家的看法、个人目标、秘密计划（永不过期）
- **短暂想法**：当前情绪、心情、感受（5 个 tick 后自动消退）
- **关键词提取**：每次互动自动提取 CJK/英文关键词，用于记忆检索

对话时 NPC 的内心状态会被注入 AI prompt，使对话更加连贯和个性化。

### 装备战斗加成

装备现在直接影响战斗属性。穿戴武器、护甲会实时生效：

| 装备 | 攻击加成 | 防御加成 | 生命加成 |
|------|---------|---------|---------|
| 铁剑 | +5 | — | — |
| 钢刀 | +12 | — | — |
| 皮甲 | — | +3 | +20 |
| 铁甲 | — | +8 | +50 |

战斗时通过 `get_effective_stats()` 动态计算实际属性，无需手动装备管理。

### LLM 诊断工具

调试 AI 调用时可启用诊断模式：

```powershell
# 打印每次 LLM 调用的 token 消耗和耗时
$env:WUXIA_LOG_LLM="1"

# 将完整 LLM 调用记录（messages + responses）写入磁盘
$env:WUXIA_DUMP_LLM="1"
# 输出目录：logs/llm_calls/（可通过 WUXIA_DUMP_DIR 自定义）
```

诊断数据包括：输入/输出 token 估算、系统 prompt 字符数、调用耗时、消息数量。

## 注意事项

- 无构建步骤，无测试套件
- Web 服务端口为 `8080`（启动横幅显示 5000 是个 bug）
- 存档文件（`.json`）已加入 `.gitignore`，不会上传
- AI API Key 不会硬编码，需通过配置文件或环境变量提供

## License

MIT
