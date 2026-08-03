"""
Stage 3: Renderers — 将 InsightPackage 转换为多种终端格式

每个 renderer 接收 InsightPackage dict，调用 DeepSeek 生成对应格式的文本。
注册表 `RENDERERS` 映射格式名到渲染函数，pipeline 通过它动态选择输出格式。

格式列表：
- bilingual_social : 中英双语社媒帖子（观点驱动）
- podcast_script   : ~3 分钟 A/B 对话脚本
"""

from typing import Callable

from .bilingual_social import render_bilingual_social
from .podcast_script import render_podcast_script


RENDERERS: dict[str, Callable[[dict], str]] = {
    "bilingual_social": render_bilingual_social,
    "podcast_script": render_podcast_script,
}


def render(format_name: str, package: dict) -> str:
    """按格式名调用对应 renderer。

    Args:
        format_name: RENDERERS 中的 key
        package: InsightPackage dict

    Returns:
        渲染后的文本。未知格式返回错误信息字符串。
    """
    renderer = RENDERERS.get(format_name)
    if renderer is None:
        return f"[Insight] Renderer: 未知格式 '{format_name}'，可用：{list(RENDERERS.keys())}"
    return renderer(package)


__all__ = ["RENDERERS", "render"]
