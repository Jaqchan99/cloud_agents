"""
Renderer 共用工具：DeepSeek client、themes_text 构造、fence 剥离、语言降级。
"""

import os
from openai import OpenAI


DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-chat"


def get_client() -> OpenAI:
    """返回 DeepSeek OpenAI 客户端。未设置 key 时抛 ValueError。"""
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY 环境变量未设置")
    return OpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL)


def strip_fence(raw: str) -> str:
    """移除 LLM 可能包裹的 ```json / ```markdown fence。"""
    content = raw.strip()
    if "```" in content:
        parts = content.split("```")
        if len(parts) >= 2:
            content = parts[1]
            if content.startswith("json"):
                content = content[4:]
            elif content.startswith("markdown"):
                content = content[8:]
            content = content.strip()
    return content


def build_themes_text(package: dict) -> str:
    """将 InsightPackage.themes 格式化为 LLM 可读的文本块。

    每个主题输出：名称、叙述、矛盾点（若有）、关联文章标题与来源。
    """
    themes = package.get("themes", [])
    language = package.get("language", "zh")
    is_zh = language == "zh"

    lines = []
    for i, theme in enumerate(themes, 1):
        name = theme.get("name", "")
        narrative = theme.get("narrative", "")
        tension = theme.get("tension")

        header = f"### 主题 {i}: {name}" if is_zh else f"### Theme {i}: {name}"
        lines.append(header)
        if narrative:
            lines.append(narrative)
        if tension:
            label = "矛盾点" if is_zh else "Tension"
            lines.append(f"**{label}:** {tension}")

        articles = theme.get("articles", [])
        if articles:
            ref_label = "关联文章" if is_zh else "Related articles"
            lines.append(f"**{ref_label}:**")
            for a in articles:
                title = a.get("title", "")
                source = a.get("source", "")
                link = a.get("link", "")
                lines.append(f"- {title} ({source}) {link}")
        lines.append("")  # 空行分隔

    return "\n".join(lines).strip()


def call_llm(
    system_prompt: str,
    user_prompt: str,
    temperature: float,
    max_tokens: int,
) -> str:
    """统一 LLM 调用入口。返回 strip_fence 后的内容。失败时抛异常。"""
    client = get_client()
    response = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    raw = response.choices[0].message.content or ""
    return strip_fence(raw)


def degraded_output(format_name: str, package: dict, err: Exception) -> str:
    """渲染失败时返回的退化文本，保留日期与文章计数等基本信息。"""
    date = package.get("date", "?")
    count = package.get("article_count", 0)
    language = package.get("language", "zh")
    is_zh = language == "zh"

    if is_zh:
        return (
            f"# 渲染失败（{format_name}）\n\n"
            f"日期：{date}｜文章数：{count}\n\n"
            f"原因：{type(err).__name__}: {err}\n\n"
            f"请检查 DEEPSEEK_API_KEY 与上游 InsightPackage。"
        )
    return (
        f"# Render failed ({format_name})\n\n"
        f"Date: {date} | Articles: {count}\n\n"
        f"Reason: {type(err).__name__}: {err}\n\n"
        f"Check DEEPSEEK_API_KEY and upstream InsightPackage."
    )
