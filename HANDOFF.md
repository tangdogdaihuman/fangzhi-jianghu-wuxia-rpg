# 交接文档：武侠传 AI 增强 — 未完成项

## 已完成（已提交到 GitHub）

1. `wuxia_api.py` — LLM 诊断工具（`reset_call_log`, `get_call_summary`, `_dump_llm_call`）+ 4 个 fallback providers + `_estimate_tokens`
2. `wuxia_npc_memory.py` — NPCMind 类（thoughts + decay）+ 分层记忆压缩（raw→short→medium→permanent）+ 结构化互动记录 + `get_npc_context_for_ai()` + `get_mind_for_prompt()`
3. `wuxia_combat.py` — `get_effective_stats()`（装备加成）+ `advance_kill_quests()`（击杀任务追踪）+ `ITEM_COMBAT_STATS` + `_grant_quest_rewards()`
4. `wuxia_ai.py` — `get_state_for_ai()` 上下文预算管理器（返回 `(str, int)` 元组）
5. `wuxia_ai_integration.py` — `_update_npc_mind()` + 对话后自动更新 NPC 内心 + tiered memory 上下文注入
6. `xiuxian_world.py` — `WorldEngine.tick()` 调用 `advance_tick()` + `talk()` 传递 `mind` 字段

## 未完成（需下一个 agent 执行）

### 1. 最终验证测试（Test [7] 失败）
`CommandHandler.process('talk 老拳师')` 在测试中断言失败。可能原因：
- `archive.get_mind_for_prompt(npc_id)` 返回空字符串（major NPC 没有 mind 实例）
- 需要确保 `get_or_create_mind` 在对话时被调用

**修复位置**: `xiuxian_world.py` 的 `talk()` 方法，major NPC 分支（约第 744-754 行）
**建议**: 在 `archive.record_interaction()` 之前添加 `archive.get_or_create_mind(npc_name, npc["personality"])`

### 2. 提交代码到 GitHub
```bash
git add -A
git commit -m "feat: AI enhancements — tiered memory, NPC minds, combat equipment, LLM diagnostics"
git push
```

### 3. 更新 README.md
在 README 中添加新功能的说明：
- 分层记忆系统
- NPC 内心世界
- 装备 combat 加成
- LLM 诊断工具（WUXIA_DUMP_LLM=1）

## 关键文件变更总结

| 文件 | 新增行数 | 主要变更 |
|------|---------|---------|
| `wuxia_api.py` | +120 | 诊断工具 + fallback providers |
| `wuxia_npc_memory.py` | +380 | NPCMind + 分层压缩 + 结构化记录 |
| `wuxia_combat.py` | +65 | 装备 stats + kill-quest |
| `wuxia_ai.py` | +55 | 上下文预算管理 |
| `wuxia_ai_integration.py` | +60 | NPC mind 更新 |
| `xiuxian_world.py` | +15 | tick + talk 集成 |

## 调试模式

```powershell
# 启用 LLM 调用日志
$env:WUXIA_DUMP_LLM=1
$env:WUXIA_LOG_LLM=1
python play_wuxia.py

# 日志输出到 logs/llm_calls/ 目录
```

## 已知问题

1. `wuxia_config.json` 中的 API key 不会被 fallback providers 使用（每个 provider 需要自己的 key）
2. 分层压缩在没有 API key 时不会执行（需要 LLM 压缩）
3. `get_state_for_ai()` 的 `_estimate_tokens` 是从 `wuxia_npc_memory` 导入的（已添加 import）
