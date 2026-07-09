"""
Insight Engine — 三阶段 AI 新闻解读流水线。

Stage 1 ingestion (零 LLM) → Stage 2 analysis (1 次 LLM, 可缓存)
→ Stage 3 renderers (每格式 1 次 LLM, 可并行)

公共入口：run_insight_pipeline()
"""

from .config import load_insight_config, save_insight_config, get_default_insight_config
from .pipeline import run_insight_pipeline, DEFAULT_FORMATS
from .schemas import InsightPackage, Theme, ArticleBrief

__all__ = [
    "run_insight_pipeline",
    "DEFAULT_FORMATS",
    "load_insight_config",
    "save_insight_config",
    "get_default_insight_config",
    "InsightPackage",
    "Theme",
    "ArticleBrief",
]
