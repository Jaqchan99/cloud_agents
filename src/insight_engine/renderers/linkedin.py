"""
LinkedIn renderer — 800-1500 字符 LinkedIn 帖子。

温度 0.7 / max_tokens 800。
失败时返回 degraded_output，不抛异常。
"""

from prompts import get

from ._common import build_themes_text, call_llm, degraded_output


def render_linkedin(package: dict) -> str:
    """渲染 LinkedIn 帖子。

    Args:
        package: InsightPackage dict

    Returns:
        帖子正文文本。失败时返回退化文本。
    """
    language = package.get("language", "zh")
    key_signal = package.get("key_signal", "")
    cross_theme = package.get("cross_theme_connection", "")
    themes_text = build_themes_text(package)

    try:
        system_prompt = get("insight_render_linkedin_system", language)
        user_prompt = get("insight_render_linkedin_user", language).format(
            key_signal=key_signal,
            themes_text=themes_text,
            cross_theme_connection=cross_theme,
        )
        text = call_llm(system_prompt, user_prompt, temperature=0.7, max_tokens=800)
    except Exception as e:
        print(f"[Insight] Renderer/LinkedIn: 失败 — {type(e).__name__}: {e}")
        return degraded_output("linkedin", package, e)

    print(f"[Insight] Renderer/LinkedIn: 完成 — {len(text)} 字符")
    return text
