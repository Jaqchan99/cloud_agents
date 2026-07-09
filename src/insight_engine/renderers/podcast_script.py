"""
Podcast script renderer — ~3 分钟 A/B 对话脚本。

温度 0.7 / max_tokens 1000。
失败时返回 degraded_output，不抛异常。
"""

from prompts import get

from ._common import build_themes_text, call_llm, degraded_output


def render_podcast_script(package: dict) -> str:
    """渲染播客脚本。

    Args:
        package: InsightPackage dict

    Returns:
        A/B 对话脚本文本。失败时返回退化文本。
    """
    language = package.get("language", "zh")
    key_signal = package.get("key_signal", "")
    cross_theme = package.get("cross_theme_connection", "")
    themes_text = build_themes_text(package)

    try:
        system_prompt = get("insight_render_podcast_system", language)
        user_prompt = get("insight_render_podcast_user", language).format(
            key_signal=key_signal,
            themes_text=themes_text,
            cross_theme_connection=cross_theme,
        )
        text = call_llm(system_prompt, user_prompt, temperature=0.7, max_tokens=1000)
    except Exception as e:
        print(f"[Insight] Renderer/Podcast: 失败 — {type(e).__name__}: {e}")
        return degraded_output("podcast_script", package, e)

    print(f"[Insight] Renderer/Podcast: 完成 — {len(text)} 字符")
    return text