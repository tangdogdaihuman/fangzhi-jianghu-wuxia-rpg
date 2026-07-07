#!/usr/bin/env python3
"""
江湖入口 - 放置江湖 · 武侠传 启动器
"""

import subprocess, sys, os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("""
╔══════════════════════════════════════════╗
║           ⚔ 放 置 江 湖 · 武 侠 传 ⚔     ║
║        AI 驱 动 的 江 湖 世 界            ║
╠══════════════════════════════════════════╣
║  江湖不是打打杀杀，是人情世故。           ║
║  你是一个初入江湖的少侠，路在脚下。       ║
╚══════════════════════════════════════════╝
""")

has_save = os.path.exists("wuxia_save.json")

if not has_save:
    print("  你背着行囊，站在平安镇的街头。")
    print("  江湖路远，一切从零开始。\n")
    print("  玩法：在这里输入你的行动，AI 会驱动整个世界实时运转")
    print("  输入 help 查看所有可用命令\n")
else:
    print("   detecting save... 欢迎回来，少侠！\n")
    result = subprocess.run(
        [sys.executable, "wuxia_ai.py", "state"],
        capture_output=True, text=True, encoding="utf-8"
    )
    if result.stdout:
        for line in result.stdout.strip().split("\n")[:10]:
            print(f"  {line}")
    print()
    print("  输入 help 查看命令，输入 look 看看周围\n")
