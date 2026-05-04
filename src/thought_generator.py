"""
思考题生成模块 - 每日推送后生成一个深度思考题，并整理用户回复为结构化观点
"""
import os
import json
from openai import OpenAI

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
