"""
Insight engine config — load/save insight_config.json.

Mirrors the user_config pattern: load/save from JSON, defaults fallback,
independent from the upstream news bot config.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

DEFAULT_INSIGHT_CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "insight_config.json"


def get_default_insight_config() -> dict:
    return {
        "formats": ["linkedin", "newsletter", "podcast_script", "bilingual"],
        "language": "zh",
        "push_to_discord": True,
    }


def load_insight_config(config_path: Path = DEFAULT_INSIGHT_CONFIG_PATH) -> dict:
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return get_default_insight_config()


def save_insight_config(config: dict, config_path: Path = DEFAULT_INSIGHT_CONFIG_PATH):
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    print(f"[Insight Config] 配置已保存: {config_path}")
