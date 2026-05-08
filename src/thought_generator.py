"""
思考题生成模块 - 每日推送后生成一个深度思考题，并整理用户回复为结构化观点
"""
import os
import json
import re
from openai import OpenAI


# 明确要求 AI 整理/润色的关键词（快速规则匹配，避免不必要的 API 调用）
_REFINE_KEYWORDS = [
    "整理", "润色", "帮我整理", "帮我润色", "优化一下", "优化下",
    "polish", "refine", "rewrite", "帮我写", "整理成", "帮我表达",
    "文字不好", "写得不好", "表达一下", "更好地表达",
]


def should_refine(text: str) -> bool:
    """
    判断用户是否希望 AI 整理/润色回复。
    先用关键词快速匹配，再用 DeepSeek 做兜底判断。

    返回 True 表示需要整理，False 表示仅保存原文。
    """
    text_lower = text.lower()

    # 快速关键词匹配
    if any(kw in text_lower for kw in _REFINE_KEYWORDS):
        return True

    # 关键词未命中时，调用 DeepSeek 判断意图（短文本不必调用）
    if len(text) < 60:
        return False

    try:
        client = get_client()
        resp = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "你判断用户的消息是否明确希望 AI 帮助整理、润色或优化他的文字表达。"
                               "只回答 yes 或 no，不要有任何其他内容。",
                },
                {
                    "role": "user",
                    "content": f'用户消息："{text[:300]}"',
                },
            ],
            temperature=0,
            max_tokens=5,
        )
        answer = resp.choices[0].message.content.strip().lower()
        return answer.startswith("yes")
    except Exception:
        return False

DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-chat"


def get_client() -> OpenAI:
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY 未设置")
    return OpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL)


def generate_thought_question(articles: list[dict], date_str: str) -> dict:
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

    prompt = f"""今天是 {date_str}，以下是今日 AI 精选资讯：

{articles_text}

请基于以上内容，生成一个高质量的每日思考题，要求：
1. 聚焦最有讨论价值的核心议题，而非事实性问题
2. 问题有助于读者形成自己的观点，可以联系到实际工作或行业趋势
3. 问题不要太宽泛（"你怎么看AI的未来"），要有具体的切入点

严格按以下 JSON 格式返回，不要有其他文字：
{{
  "question": "<思考题，1-2句话>",
  "context": "<提这个问题的背景，1-2句，说明为什么这个问题重要>",
  "related_articles": [
    {{"title": "<文章标题>", "source": "<来源>", "link": "<链接>"}},
    ...
  ]
}}

related_articles 选最相关的 1-3 篇，从上面文章列表中选取。"""

    client = get_client()
    response = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=[
            {"role": "system", "content": "你是一个帮助用户深度思考 AI 趋势的助手，善于提出有洞察力的问题。"},
            {"role": "user", "content": prompt},
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
) -> dict:
    """
    将用户的粗糙回复整理为结构化观点，并提取关键词

    返回：
    {
        "refined_answer": "整理后的观点（200-400字）",
        "keywords": ["关键词1", "关键词2", ...],
        "sources_mentioned": ["用户提到的来源1", ...]  # 从用户回复中识别
    }
    """
    articles_context = "\n".join(
        f"- [{a.get('source','')}] {a.get('title','')}" for a in related_articles
    )

    prompt = f"""用户回答了以下思考题：

**问题：** {question}

**相关文章：**
{articles_context}

**用户的原始回复：**
{raw_reply}

请完成以下任务：
1. 将用户回复整理为一段有条理的观点（150-300字），保留用户的核心想法，补充逻辑结构，语言更清晰有力
2. 提取 3-6 个核心关键词（名词或概念，如"长上下文"、"工具调用"、"Agent框架"）
3. 从用户回复中识别他明确提到的信息来源编号或名称（如"第2条"、"TechCrunch那篇"等）

严格按以下 JSON 格式返回：
{{
  "refined_answer": "<整理后的观点>",
  "keywords": ["关键词1", "关键词2", ...],
  "sources_mentioned": ["来源名称或描述1", ...]
}}"""

    client = get_client()
    response = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=[
            {"role": "system", "content": "你是一个帮助用户整理和表达思考的助手，风格清晰、专业、保留用户个人视角。"},
            {"role": "user", "content": prompt},
        ],
        temperature=0.4,
        max_tokens=800,
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
) -> dict:
    """
    仅提取关键词和信息来源，不整理正文。
    用于用户不要求润色时的轻量处理。

    返回：
    {
        "keywords": [...],
        "sources_mentioned": [...]
    }
    """
    articles_context = "\n".join(
        f"- [{a.get('source','')}] {a.get('title','')}" for a in related_articles
    )

    prompt = f"""问题：{question}
相关文章：
{articles_context}

用户回复：{raw_reply[:500]}

请完成：
1. 提取 3-6 个核心关键词（名词或概念）
2. 识别用户提到的信息来源（编号或名称）

严格按 JSON 格式返回：
{{"keywords": ["关键词1", ...], "sources_mentioned": ["来源1", ...]}}"""

    try:
        client = get_client()
        resp = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[{"role": "user", "content": prompt}],
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


def format_thought_question_message(question_data: dict) -> str:
    """格式化为 Discord 消息"""
    question = question_data.get("question", "")
    context = question_data.get("context", "")
    articles = question_data.get("related_articles", [])

    lines = [
        "---",
        "💭 **今日思考题**",
        "",
        f"**{question}**",
    ]
    if context:
        lines.append(f"_{context}_")
    if articles:
        lines.append("")
        lines.append("相关资讯：")
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
        "_💡 直接回复你的想法，我会帮你整理成结构化观点并存入 Notion_",
        "_回复时可指出参考了哪几条资讯（如「参考第2、3条」）_",
    ]
    return "\n".join(lines)


# ── 快速规则：config 调整类关键词 ──────────────────────────────────
_CONFIG_KEYWORDS = [
    "每次推送", "推送改为", "推送数量", "关注话题", "只想看", "不想看",
    "过滤掉", "去掉", "排除", "加上", "添加", "天气改", "天气换",
    "换成", "改为", "修改配置", "更新配置", "hours_back", "max_items",
    "enabled_sources", "focus_topics", "user_note", "weather_location",
]


def classify_message_intent(text: str, today_question: str) -> str:
    """
    判断用户消息的意图，返回三种之一：
      "config"  - 修改推送配置（weather、topics、max_items 等）
      "answer"  - 回答今日思考题
      "note"    - 独立想法，与今日思考题无直接关联

    策略：
    1. 关键词快速匹配 config → 无需调用 API
    2. 若今日无思考题 → 统一归为 note
    3. 剩余情况调用 DeepSeek 判断 answer vs note
    """
    text_lower = text.lower()

    # 规则层：config 关键词
    if any(kw in text_lower for kw in _CONFIG_KEYWORDS):
        return "config"

    # 无今日思考题，无法判断 answer，直接归 note
    if not today_question:
        return "note"

    # LLM 判断 answer vs note
    try:
        client = get_client()
        resp = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "判断用户消息与给定问题的关联性。"
                        "若用户在回应或讨论该问题，回答 answer；"
                        "若用户在分享与该问题无直接关联的独立想法，回答 note。"
                        "只回答 answer 或 note，不要有其他内容。"
                    ),
                },
                {
                    "role": "user",
                    "content": f"今日问题：{today_question}\n\n用户消息：{text[:400]}",
                },
            ],
            temperature=0,
            max_tokens=5,
        )
        result = resp.choices[0].message.content.strip().lower()
        return "answer" if result.startswith("answer") else "note"
    except Exception as e:
        print(f"[Intent] 意图分类 API 失败，默认 note: {e}")
        return "note"


def generate_question_from_thought(text: str) -> str:
    """
    针对独立想法（note 类型），由 AI 根据内容反推一个问题，
    填入 Notion 的[问题]字段，实现与每日思考题的解耦。

    例：用户说「开源模型生态比闭源更可持续，社区驱动的创新更难被垄断」
    → 返回「开源与闭源模型的生态发展路径，哪种长期更具可持续性？」
    """
    try:
        client = get_client()
        resp = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "根据用户的想法，提炼出一个简洁的问题（15-40字），"
                        "概括该想法在讨论什么核心议题。"
                        "问题要有探讨价值，不要过于宽泛。"
                        "只输出问题本身，不要有其他文字。"
                    ),
                },
                {"role": "user", "content": f"用户的想法：{text[:500]}"},
            ],
            temperature=0.5,
            max_tokens=60,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print(f"[Intent] 问题生成失败，使用默认: {e}")
        return "独立思考记录"
