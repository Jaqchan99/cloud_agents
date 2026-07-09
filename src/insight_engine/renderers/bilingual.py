"""
Bilingual renderer — 2000-4000 字符中英双语版本。

无论 package language 是什么，都调用双语 prompt（prompts 内部用 zh 模板，
输出的中英文由 LLM 自行决定，两者独立写作而非翻译）。

温度 0.6 / max_tokens 1500。
失败时返回 degraded_output，不抛异常。
"""

from prompts import get

from ._common import build_themes_text, call_llm, degraded_output


def render_bilingual(package: dict) -> str:
    """渲染中英双语版。

    Args:
        package: InsightPackage dict

    Returns:
        双语 markdown 文本。失败时返回退化文本。
    """
    # 双语版 language 固定用 zh（中文主版在上，英文版在下分隔）
    language = "zh"
    key_signal = package.get("key_signal", "")
    cross_theme = package.get("cross_theme_connection", "")
    themes_text = build_themes_text(package)

    try:
        system_prompt = get("insight_render_bilingual_system", language)
        user_prompt = get("insight_render_bilingual_user", language).format(
            key_signal=key_signal,
            themes_text=themes_text,
            cross_theme_connection=cross_theme,
        )
        text = call_llm(system_prompt, user_prompt, temperature=0.6, max_tokens=1500)
    except Exception as e:
        print(f"[Insight] Renderer/Bilingual: 失败 — {type(e).__name__}: {e}")
        return degraded_output("bilingual", package, e)

    print(f"[Insight] Renderer/Bilingual: 完成 — {len(text)} 字符")
    return text