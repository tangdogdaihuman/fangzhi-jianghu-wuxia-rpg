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

## 注意事项

- 无构建步骤，无测试套件
- Web 服务端口为 `8080`（启动横幅显示 5000 是个 bug）
- 存档文件（`.json`）已加入 `.gitignore`，不会上传
- AI API Key 不会硬编码，需通过配置文件或环境变量提供

## License

MIT
