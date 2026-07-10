"""
Insight Engine run script — GitHub Actions 入口点。

读取 config/today_thought_context.json，执行完整 Insight 流水线，
将渲染结果写入 output/insight/{date}/{format}.md，并可选推送到 Discord 频道。

用法：
    python scripts/insight_engine_run.py [--formats linkedin,newsletter]
                                         [--language zh]
                                         [--push-discord]
"""
import sys
import os
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from insight_engine import run_insight_pipeline, DEFAULT_FORMATS
from insight_engine.config import load_insight_config


# Discord 频道里每个格式的展示名 + emoji
DISCORD_FORMAT_LABELS: dict[str, str] = {
    "linkedin": "💼 LinkedIn 帖子",
    "newsletter": "📰 Newsletter",
    "podcast_script": "🎙️ 播客脚本",
    "bilingual": "🌐 中英双语",
}


def push_to_discord(rendered: dict[str, str], date: str) -> None:
    """将渲染结果发送到 Discord insight 频道。

    每个格式一条带头部标注的消息；超长由 send_long_message 自动分块。
    """
    from discord_client import send_long_message

    channel_id = os.environ.get("DISCORD_INSIGHT_CHANNEL_ID", "")
    if not channel_id:
        print("[Insight] Discord: DISCORD_INSIGHT_CHANNEL_ID 未设置，跳过推送")
        return
    if not os.environ.get("DISCORD_BOT_TOKEN"):
        print("[Insight] Discord: DISCORD_BOT_TOKEN 未设置，跳过推送")
        return

    header = f"📋 **AI 深度解读 · {date}**\n\n"
    send_long_message(header, channel_id=channel_id)

    for fmt, text in rendered.items():
        label = DISCORD_FORMAT_LABELS.get(fmt, fmt)
        separator = f"\n\n---\n**{label}**\n\n"
        send_long_message(separator + text, channel_id=channel_id)
        print(f"[Insight] Discord: 已推送 {fmt} → 频道 {channel_id}")

    # 推送配置面板（交互式按钮/菜单）
    try:
        from insight_engine.config_panel import build_config_panel
        from insight_engine.config import load_insight_config
        from discord_client import send_message_with_components

        cfg = load_insight_config()
        panel = build_config_panel(cfg)
        send_message_with_components(
            content="⚙️ **配置面板** — 点击下方按钮调整 Insight Engine 设置，修改即时生效。",
            components=panel,
            channel_id=channel_id,
        )
        print("[Insight] Discord: 已推送配置面板")
    except Exception as e:
        print(f"[Insight] Discord: 配置面板推送失败（不影响主流程）— {e}")


def main():
    insight_config = load_insight_config()

    parser = argparse.ArgumentParser(description="运行 Insight Engine 流水线")
    parser.add_argument(
        "--formats",
        type=str,
        default=",".join(insight_config.get("formats", DEFAULT_FORMATS)),
        help=f"要渲染的格式，逗号分隔。默认: {','.join(insight_config.get('formats', DEFAULT_FORMATS))}",
    )
    parser.add_argument(
        "--language",
        type=str,
        default=insight_config.get("language", "zh"),
        choices=["zh", "en"],
        help=f"分析语言（zh/en）。默认 {insight_config.get('language', 'zh')}。",
    )
    parser.add_argument(
        "--push-discord",
        action="store_true",
        dest="push_discord",
        help="渲染后推送到 Discord insight 频道（需设置 DISCORD_INSIGHT_CHANNEL_ID）",
    )
    parser.add_argument(
        "--no-push-discord",
        action="store_false",
        dest="push_discord",
        help="不推送到 Discord",
    )
    parser.set_defaults(push_discord=insight_config.get("push_to_discord", True))
    args = parser.parse_args()

    formats = args.formats.split(",") if args.formats else None

    # DEEPSEEK_API_KEY 检查
    if not os.environ.get("DEEPSEEK_API_KEY"):
        print("[Insight] 错误: DEEPSEEK_API_KEY 环境变量未设置")
        sys.exit(1)

    result = run_insight_pipeline(
        formats=formats,
        language=args.language,
        parallel=True,
        write_files=True,
    )

    article_count = result["article_count"]
    if article_count == 0:
        print("[Insight] 无有效文章，流水线提前结束")
        sys.exit(0)

    rendered = result["rendered"]
    output_paths = result["output_paths"]
    date = result["date"]

    print(f"[Insight] 完成: {article_count} 篇文章 → {len(rendered)} 个格式")
    for fmt, path in output_paths.items():
        text = rendered.get(fmt, "")
        print(f"  {fmt}: {path}（{len(text)} 字符）")

    if args.push_discord:
        print("[Insight] 开始推送到 Discord insight 频道...")
        try:
            push_to_discord(rendered, date)
            print("[Insight] Discord 推送完成")
        except Exception as e:
            print(f"[Insight] Discord 推送失败（不影响主流程）— {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
