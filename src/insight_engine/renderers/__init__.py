"""
Stage 3: Renderers — 将 InsightPackage 转换为多种终端格式

每个 renderer 接收 InsightPackage dict，调用 DeepSeek 生成对应格式的文本。
注册表 `RENDERERS` 映射格式名到渲染函数，pipeline 通过它动态选择输出格式。

格式列表：
- linkedin        : 800-1500 字符 LinkedIn 帖子
- newsletter      : 1500-3000 字符 markdown 通讯
- podcast_script  : ~3 分钟 A/B 对话脚本
- bilingual       : 2000-4000 字符中英双语版本
"""

from typing import Callable

from .linkedin import render_linkedin
from .newsletter import render_newsletter
from .podcast_script import render_podcast_script
from .bilingual import render_bilingual


RENDERERS: dict[str, Callable[[dict], str]] = {
    "linkedin": render_linkedin,
    "newsletter": render_newsletter,
    "podcast_script": render_podcast_script,
    "bilingual": render_bilingual,
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
