"""
Bilingual social media renderer — 观点驱动的中英双语社媒帖子。

替代旧 linkedin + newsletter + bilingual 三个 renderer。
单次 LLM 调用输出中英两版社媒帖子（各自独立写作，非互译）。

温度 0.7 / max_tokens 1200。
失败时返回 degraded_output，不抛异常。
无强信号时输出降级提示。
"""

import json

from prompts import get

from ._common import build_themes_text, call_llm, degraded_output


def render_bilingual_social(package: dict) -> str:
    """渲染中英双语社媒帖子。

    Args:
        package: InsightPackage dict

    Returns:
        Markdown 文本，中文版 + --- + 英文版。失败或无信号时返回退化文本。
    """
    language = "zh"  # 双语版固定用 zh 模板
    key_signal = package.get("key_signal", "")
    cross_theme = package.get("cross_theme_connection", "")
    themes_text = build_themes_text(package)

    try:
        system_prompt = get("insight_render_bilingual_social_system", language)
        user_prompt = get("insight_render_bilingual_social_user", language).format(
            key_signal=key_signal,
            themes_text=themes_text,
            cross_theme_connection=cross_theme,
        )
        raw = call_llm(system_prompt, user_prompt, temperature=0.7, max_tokens=1200)
        result = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"[Insight] Renderer/BilingualSocial: JSON 解析失败 — {e}")
        return degraded_output("bilingual_social", package, e)
    except Exception as e:
        print(f"[Insight] Renderer/BilingualSocial: 失败 — {type(e).__name__}: {e}")
        return degraded_output("bilingual_social", package, e)

    post_zh = result.get("post_zh", "")
    post_en = result.get("post_en", "")
    title_zh = result.get("title_zh", "")

    # 无强信号：不生成评论
    if not post_zh or title_zh == "今天没有形成足够强的行业信号，不生成评论。":
        msg = "今天没有形成足够强的行业信号，不生成评论。"
        print(f"[Insight] Renderer/BilingualSocial: {msg}")
        return msg

    output = f"# {title_zh}\n\n{post_zh}\n\n---\n\n# {result.get('title_en', '')}\n\n{post_en}"
    print(f"[Insight] Renderer/BilingualSocial: 完成 — {len(output)} 字符")
    return output
