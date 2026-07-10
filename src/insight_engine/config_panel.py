"""
Insight Engine 配置面板 — Discord Message Components

构建 insight 频道消息下方的交互式配置面板：
  - Select Menu: 语言切换 (中文/English)
  - Buttons: 格式开关 (LinkedIn, Newsletter, 播客, 双语)
  - Button: 推送开关
  - Button: 立即重跑
"""

ALL_FORMATS = ["linkedin", "newsletter", "podcast_script", "bilingual"]

FORMAT_LABELS: dict[str, str] = {
    "linkedin": "LinkedIn",
    "newsletter": "Newsletter",
    "podcast_script": "播客",
    "bilingual": "双语",
}

FORMAT_EMOJI: dict[str, str] = {
    "linkedin": "💼",
    "newsletter": "📰",
    "podcast_script": "🎙️",
    "bilingual": "🌐",
}


def build_config_panel(config: dict) -> list[dict]:
    """构建配置面板的 Discord Message Component JSON (action rows)."""
    formats = config.get("formats", [])
    lang = config.get("language", "zh")
    push_on = config.get("push_to_discord", True)

    components = []

    # Row 1: Language select menu
    components.append({
        "type": 1,
        "components": [{
            "type": 3,
            "custom_id": "insight:set_lang",
            "placeholder": "语言 / Language",
            "options": [
                {"label": "中文", "value": "zh", "default": lang == "zh"},
                {"label": "English", "value": "en", "default": lang == "en"},
            ],
            "min_values": 1,
            "max_values": 1,
        }]
    })

    # Row 2: Format toggle buttons
    format_buttons = []
    for fmt in ALL_FORMATS:
        is_on = fmt in formats
        emoji = FORMAT_EMOJI.get(fmt, "")
        label = FORMAT_LABELS.get(fmt, fmt)
        format_buttons.append({
            "type": 2,
            "style": 3 if is_on else 2,  # 3=green(SUCCESS), 2=grey(SECONDARY)
            "label": f"{'✅ ' if is_on else ''}{emoji} {label}",
            "custom_id": f"insight:toggle_format:{fmt}",
        })
    components.append({"type": 1, "components": format_buttons})

    # Row 3: Push toggle + Rerun
    components.append({
        "type": 1,
        "components": [
            {
                "type": 2,
                "style": 3 if push_on else 2,
                "label": f"{'🟢' if push_on else '🔴'} 推送: {'开' if push_on else '关'}",
                "custom_id": "insight:toggle_push",
            },
            {
                "type": 2,
                "style": 1,  # PRIMARY (blurple)
                "label": "🔄 立即重跑",
                "custom_id": "insight:rerun",
            },
        ]
    })

    return components


def get_config_panel_content(config: dict) -> dict:
    """构建完整配置面板消息的 content + components."""
    formats = config.get("formats", [])
    lang = config.get("language", "zh")
    push_on = config.get("push_to_discord", True)

    lang_label = "中文" if lang == "zh" else "English"
    if formats:
        format_labels = [f"{FORMAT_EMOJI.get(f, '')} {FORMAT_LABELS.get(f, f)}" for f in formats]
        format_str = "  ".join(format_labels)
    else:
        format_str = "无"

    content = (
        f"⚙️ **Insight Engine 配置面板**\n"
        f"🔤 语言：**{lang_label}**\n"
        f"📋 格式：{format_str}\n"
        f"📤 Discord 推送：**{'开 🟢' if push_on else '关 🔴'}**\n"
        f"\n点击下方按钮即时调整配置，修改自动保存。"
    )

    return {
        "content": content,
        "components": build_config_panel(config),
    }
