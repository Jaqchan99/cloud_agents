"""
注册 Discord Slash Commands（全局或指定服务器）

用法：
    python scripts/register_commands.py              # 全局注册（最多1小时生效）
    python scripts/register_commands.py --guild ID   # 指定服务器（即时生效，测试用）

环境变量：
    DISCORD_APP_ID    — Discord Application ID
    DISCORD_BOT_TOKEN — Bot Token
"""
import os
import sys
import requests

DISCORD_API = "https://discord.com/api/v10"

COMMANDS = [
    {
        "name": "push",
        "name_localizations": {"zh-CN": "push"},
        "description": "立即推送今日 AI 早报（强制）",
        "description_localizations": {"zh-CN": "立即推送今日 AI 早报（强制）"},
    },
    {
        "name": "config",
        "name_localizations": {"zh-CN": "config"},
        "description": "查看当前推送配置",
        "description_localizations": {"zh-CN": "查看当前推送配置"},
    },
    {
        "name": "insight-config",
        "name_localizations": {"zh-CN": "insight-config"},
        "description": "查看/编辑 Insight Engine 配置（附带交互面板）",
        "description_localizations": {"zh-CN": "查看/编辑 Insight Engine 配置（附带交互面板）"},
    },
    {
        "name": "thought",
        "name_localizations": {"zh-CN": "thought"},
        "description": "查看今日思考题",
        "description_localizations": {"zh-CN": "查看今日思考题"},
    },
    {
        "name": "status",
        "name_localizations": {"zh-CN": "status"},
        "description": "查看推送状态（最近推送日期）",
        "description_localizations": {"zh-CN": "查看推送状态（最近推送日期）"},
    },
    {
        "name": "insight",
        "name_localizations": {"zh-CN": "insight"},
        "description": "运行 Insight Engine 深度解读",
        "description_localizations": {"zh-CN": "运行 Insight Engine 深度解读"},
    },
]


def main():
    import argparse
    parser = argparse.ArgumentParser(description="注册 Discord Slash Commands")
    parser.add_argument("--guild", help="服务器 ID（即时生效，测试用）。不传则全局注册。")
    args = parser.parse_args()

    app_id = os.environ.get("DISCORD_APP_ID", "")
    bot_token = os.environ.get("DISCORD_BOT_TOKEN", "")
    if not app_id or not bot_token:
        print("错误: 请设置 DISCORD_APP_ID 和 DISCORD_BOT_TOKEN 环境变量")
        sys.exit(1)

    if args.guild:
        url = f"{DISCORD_API}/applications/{app_id}/guilds/{args.guild}/commands"
        scope = f"服务器 {args.guild}"
    else:
        url = f"{DISCORD_API}/applications/{app_id}/commands"
        scope = "全局"

    headers = {"Authorization": f"Bot {bot_token}", "Content-Type": "application/json"}
    resp = requests.put(url, json=COMMANDS, headers=headers, timeout=15)

    if resp.status_code not in (200, 201):
        print(f"注册失败 ({resp.status_code}): {resp.text}")
        sys.exit(1)

    commands = resp.json()
    print(f"已注册 {len(commands)} 个命令到 {scope}:")
    for cmd in commands:
        print(f"  /{cmd['name']} — {cmd['description']}")


if __name__ == "__main__":
    main()
