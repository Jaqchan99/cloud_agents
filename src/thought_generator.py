"""
思考题生成模块 - 每日推送后生成一个深度思考题，并整理用户回复为结构化观点
"""
import os
import json
import re
from openai import OpenAI
from prompts import get, get_refine_keywords, get_config_keywords

DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-chat"


def should_refine(text: str, lang: str = "zh") -> bool:
    """
    判断用户是否希望 AI 整理/润色回复。
    先用关键词快速匹配，再用 DeepSeek 做兜底判断。
    """
    text_lower = text.lower()
    keywords = get_refine_keywords(lang)

    # 快速关键词匹配
    if any(kw.lower() in text_lower for kw in keywords):
        return True

    # 关键词未命中时，调用 DeepSeek 判断意图（短文本不必调用）
    if len(text) < 60:
        return False

    try:
        client = get_client()
        resp = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": get("refine_classify_system", lang)},
                {"role": "user", "content": f'User message: "{text[:300]}"'},
            ],
            temperature=0,
            max_tokens=5,
        )
        answer = resp.choices[0].message.content.strip().lower()
        return answer.startswith("yes")
    except Exception:
        return False


def get_client() -> OpenAI:
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY 未设置")
    return OpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL)


def generate_thought_question(articles: list[dict], date_str: str, lang: str = "zh") -> dict:
    """
    根据今日精选文章，生成一个有深度的思考题

    返回：
    {
        "question": "思考题正文",
        "context": "为什么提这个问题的背景说明（1-2句）",
        "related_articles": [{"title": ..., "source": ..., "link": ...}]  # 与该题最相关的 1-3 篇
    }
    """
    articles_text = ""
    for i, a in enumerate(articles[:10], 1):
        articles_text += f"{i}. [{a.get('source','')}] {a.get('title','')}\n   {a.get('ai_summary','')[:150]}\n\n"

    client = get_client()
    response = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=[
            {"role": "system", "content": get("thought_question_system", lang)},
            {"role": "user", "content": get("thought_question_user", lang).format(
                date_str=date_str, articles_text=articles_text
            )},
        ],
        temperature=0.7,
        max_tokens=600,
    )

    raw = response.choices[0].message.content.strip()
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    return json.loads(raw)


def refine_user_reply(
    question: str,
    raw_reply: str,
    related_articles: list[dict],
    lang: str = "zh",
) -> dict:
    """
    将用户的粗糙回复进行结构性重写，并提取关键词

    返回：
    {
        "refined_answer": "结构性重写后的观点",
        "keywords": ["关键词1", "关键词2", ...],
        "sources_mentioned": ["用户提到的来源1", ...]
    }
    """
    articles_context = "\n".join(
        f"- [{a.get('source','')}] {a.get('title','')}" for a in related_articles
    ) if related_articles else "(no related articles)" if lang == "en" else "（无特定关联文章）"

    client = get_client()
    response = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=[
            {"role": "system", "content": get("refine_system", lang)},
            {"role": "user", "content": get("refine_user", lang).format(
                question=question,
                articles_context=articles_context,
                raw_reply=raw_reply,
            )},
        ],
        temperature=0.4,
        max_tokens=1200,
    )

    raw = response.choices[0].message.content.strip()
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    return json.loads(raw)


def extract_keywords_and_sources(
    question: str,
    raw_reply: str,
    related_articles: list[dict],
    lang: str = "zh",
) -> dict:
    """
    仅提取关键词和信息来源，不整理正文。
    """
    articles_context = "\n".join(
        f"- [{a.get('source','')}] {a.get('title','')}" for a in related_articles
    )

    try:
        client = get_client()
        resp = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[
                {"role": "user", "content": get("extract_keywords_user", lang).format(
                    question=question,
                    articles_context=articles_context,
                    raw_reply=raw_reply,
                )},
            ],
            temperature=0.2,
            max_tokens=200,
        )
        raw = resp.choices[0].message.content.strip()
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())
    except Exception as e:
        print(f"[ThoughtGen] 关键词提取失败: {e}")
        return {"keywords": [], "sources_mentioned": []}


def format_thought_question_message(question_data: dict, lang: str = "zh") -> str:
    """格式化为 Discord 消息"""
    question = question_data.get("question", "")
    context = question_data.get("context", "")
    articles = question_data.get("related_articles", [])

    lines = [
        "---",
        get("format_thought_section_title", lang),
        "",
        f"**{question}**",
    ]
    if context:
        lines.append(f"_{context}_")
    if articles:
        lines.append("")
        lines.append(get("format_thought_related_label", lang))
        for a in articles:
            title = a.get("title", "")
            link = a.get("link", "")
            source = a.get("source", "")
            if link:
                lines.append(f"• [{title}]({link}) — {source}")
            else:
                lines.append(f"• {title} — {source}")
    lines += [
        "",
        get("format_thought_footer", lang),
    ]
    return "\n".join(lines)


# ── 快速规则：config 调整类关键词 ──────────────────────────────────
def classify_message_intent(text: str, today_question: str, lang: str = "zh") -> str:
    """
    判断用户消息的意图，返回三种之一：
      "config"  - 修改推送配置
      "answer"  - 回答今日思考题
      "note"    - 独立想法

    策略：
    1. 关键词快速匹配 config → 无需调用 API
    2. 若今日无思考题 → 统一归为 note
    3. 剩余情况调用 DeepSeek 三分类
    """
    text_lower = text.lower()
    config_keywords = get_config_keywords()

    # 规则层：config 关键词
    if any(kw.lower() in text_lower for kw in config_keywords):
        return "config"

    # 无今日思考题，仍需要 LLM 区分 config 和 note（不能直接给 answer）
    if not today_question:
        try:
            client = get_client()
            resp = client.chat.completions.create(
                model=DEEPSEEK_MODEL,
                messages=[
                    {"role": "system", "content": get("intent_classify_no_question_system", lang)},
                    {"role": "user", "content": f"User message: {text[:400]}"},
                ],
                temperature=0,
                max_tokens=5,
            )
            result = resp.choices[0].message.content.strip().lower()
            return "config" if result.startswith("config") else "note"
        except Exception:
            return "note"

    # LLM 三分类
    try:
        client = get_client()
        resp = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": get("intent_classify_system", lang)},
                {"role": "user", "content": f"Today's question: {today_question}\n\nUser message: {text[:400]}"},
            ],
            temperature=0,
            max_tokens=5,
        )
        result = resp.choices[0].message.content.strip().lower()
        if result.startswith("config"):
            return "config"
        return "answer" if result.startswith("answer") else "note"
    except Exception as e:
        print(f"[Intent] 意图分类 API 失败，默认 note: {e}")
        return "note"


def generate_question_from_thought(text: str, lang: str = "zh") -> str:
    """
    针对独立想法（note 类型），由 AI 根据内容反推一个问题
    """
    try:
        client = get_client()
        resp = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": get("generate_question_system", lang)},
                {"role": "user", "content": f"User's thought: {text[:500]}"},
            ],
            temperature=0.5,
            max_tokens=60,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print(f"[Intent] 问题生成失败，使用默认: {e}")
        return get("generate_question_fallback", lang)
