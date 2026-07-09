"""
集中管理所有双语 prompt 和显示文本。
通过 get(key, lang, **kwargs) 获取对应语言的字符串。

新增 prompt 只需在这里加，不要在其他模块硬编码中文/英文。
"""

# ═══════════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════════

def get(key: str, lang: str = "zh", **kwargs) -> str:
    """获取 prompt，支持 str.format(**kwargs)"""
    entry = _PROMPTS.get(key)
    if entry is None:
        raise KeyError(f"Unknown prompt key: {key}")
    if isinstance(entry, dict):
        text = entry.get(lang, entry.get("zh", str(entry)))
    else:
        text = entry
    if kwargs:
        return text.format(**kwargs)
    return text


# ═══════════════════════════════════════════════
# ai_processor.py
# ═══════════════════════════════════════════════

_SELECT_SUMMARIZE_SYSTEM = {
    "zh": "你是一名专注于 AI 领域的资讯编辑，帮助用户筛选和总结最有价值的 AI 资讯。请用中文回复。",
    "en": "You are an AI industry editor, helping users filter and summarize the most valuable AI news. Please reply in English.",
}

_SELECT_SUMMARIZE_USER = {
    "zh": (
        "以下是今天抓取的 AI 相关文章列表，请完成：\n\n"
        "1. 从中选出最值得关注的 {max_items} 条（优先关注：{focus_str}）{user_note_str}\n"
        "2. 为每条文章生成 2-3 句话的中文简介，说明其核心内容和意义\n"
        "3. 按重要性从高到低排序\n\n"
        "请严格以如下 JSON 数组格式返回，不要包含其他文字：\n"
        '[\n'
        '  {{\n'
        '    "index": <原始编号>,\n'
        '    "title": "<原始标题>",\n'
        '    "source": "<来源>",\n'
        '    "category": "<分类>",\n'
        '    "link": "<链接>",\n'
        '    "ai_summary": "<你写的中文摘要>"\n'
        '  }},\n'
        '  ...\n'
        ']\n\n'
        '文章列表：\n'
        '{articles_text}'
    ),
    "en": (
        "Below is a list of AI-related articles scraped today. Please:\n\n"
        "1. Select the {max_items} most noteworthy ones (priority: {focus_str}){user_note_str}\n"
        "2. Write a 2-3 sentence English summary for each, explaining the core content and significance\n"
        "3. Sort by importance, highest first\n\n"
        "Return strictly as the following JSON array, no other text:\n"
        '[\n'
        '  {{\n'
        '    "index": <original number>,\n'
        '    "title": "<original title>",\n'
        '    "source": "<source>",\n'
        '    "category": "<category>",\n'
        '    "link": "<link>",\n'
        '    "ai_summary": "<your English summary>"\n'
        '  }},\n'
        '  ...\n'
        ']\n\n'
        'Articles:\n'
        '{articles_text}'
    ),
}

_SELECT_SUMMARIZE_FOCUS_FALLBACK = {
    "zh": "大语言模型、AI Agent、开源模型、行业动态",
    "en": "LLMs, AI Agents, Open-source Models, Industry Trends",
}

_SELECT_SUMMARIZE_USER_NOTE_PREFIX = {
    "zh": "\n用户特别备注：{user_note}",
    "en": "\nUser special note: {user_note}",
}

_PROCESS_COMMAND_SYSTEM = {
    "zh": "你是一名 AI 资讯推送助手，负责管理用户的资讯推送偏好。请用中文回复，语气友好简洁。",
    "en": "You are an AI news push assistant, managing the user's news push preferences. Reply in English, with a friendly and concise tone.",
}

_PROCESS_COMMAND_USER = {
    "zh": (
        "当前用户配置如下：\n"
        "{config_json}\n\n"
        '用户发送了以下消息："{user_message}"\n\n'
        "请判断用户意图，并返回如下 JSON 格式（不要包含其他文字）：\n"
        '{{\n'
        '  "reply": "<给用户的回复，说明你做了什么调整>",\n'
        '  "updated_config": <更新后的完整配置 JSON，若无需修改则返回 null>\n'
        '}}\n\n'
        "可调整的配置字段说明：\n"
        "- focus_topics: list[str]，关注的主题列表\n"
        "- include_keywords: list[str]，必须包含的关键词\n"
        "- exclude_keywords: list[str]，过滤掉的关键词\n"
        "- max_items: int，每次推送条数（1-15）\n"
        "- hours_back: int，抓取多少小时内的文章（6-48）\n"
        "- push_time: str，推送时间，格式 \"HH:MM\"（UTC）\n"
        "- user_note: str，给 AI 编辑的特别备注\n"
        "- language: str，推送语言，\"zh\" 中文或 \"en\" 英文\n"
        "- enabled_sources: list[str]，启用的新闻来源列表\n"
        "- weather_location: str，天气城市（中英文均可）\n"
        "\n"
        "用户消息示例及对应操作：\n"
        '- "我只想看 Claude 和 GPT 的新闻" → 更新 include_keywords\n'
        '- "去掉论文类内容" → 更新 exclude_keywords 或 enabled_sources\n'
        '- "每次推送 10 条" → 更新 max_items\n'
        '- "改为早上 8 点推送" → 更新 push_time（注意转换为 UTC）\n'
        '- "帮我关注 AI 安全方向" → 更新 focus_topics\n'
        '- "用英文推送" → 更新 language 为 "en"\n'
    ),
    "en": (
        "Current user config:\n"
        "{config_json}\n\n"
        'User message: "{user_message}"\n\n'
        "Determine the user's intent and return JSON (no other text):\n"
        '{{\n'
        '  "reply": "<your reply to the user, explaining what you adjusted>",\n'
        '  "updated_config": <complete updated config JSON, or null if no change>\n'
        '}}\n\n'
        "Configurable fields:\n"
        "- focus_topics: list[str], topics of interest\n"
        "- include_keywords: list[str], must-include keywords\n"
        "- exclude_keywords: list[str], filter-out keywords\n"
        "- max_items: int, articles per push (1-15)\n"
        "- hours_back: int, hours to look back (6-48)\n"
        "- push_time: str, push time in \"HH:MM\" (UTC)\n"
        "- user_note: str, special note for the AI editor\n"
        "- language: str, push language, \"zh\" or \"en\"\n"
        "- enabled_sources: list[str], enabled news sources\n"
        "- weather_location: str, city name for weather\n"
        "\n"
        "Examples:\n"
        '- "I only want news about OpenAI and Anthropic" → update include_keywords\n'
        '- "Remove academic papers" → update enabled_sources\n'
        '- "Push 10 articles each time" → update max_items\n'
        '- "Change push time to 9 AM Beijing" → update push_time (convert to UTC)\n'
        '- "Focus on AI safety" → update focus_topics\n'
        '- "Switch to English" → update language to "en"\n'
    ),
}


# ═══════════════════════════════════════════════
# morning_greeter.py
# ═══════════════════════════════════════════════

def get_time_greeting(lang: str, hour: int) -> str:
    """根据北京时间小时返回对应语言的问候语"""
    if lang == "en":
        if 5 <= hour < 12:
            return "Good morning"
        elif 12 <= hour < 17:
            return "Good afternoon"
        elif 17 <= hour < 22:
            return "Good evening"
        else:
            return "Good night (take care of yourself)"
    # zh
    if 5 <= hour < 10:
        return "早上好"
    elif 10 <= hour < 13:
        return "上午好"
    elif 13 <= hour < 18:
        return "下午好"
    elif 18 <= hour < 22:
        return "晚上好"
    else:
        return "夜深了，注意休息"


_WEEKDAY_NAMES = {
    "zh": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"],
    "en": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
}


def get_weekday_name(lang: str, weekday: int) -> str:
    return _WEEKDAY_NAMES.get(lang, _WEEKDAY_NAMES["zh"])[weekday]


_GREETING_SYSTEM = {
    "zh": "你是一个温暖、简洁、有品味的 AI 助手，擅长写每日早报开场白。",
    "en": "You are a warm, concise, tasteful AI assistant, skilled at writing daily briefing openers.",
}

_GREETING_USER = {
    "zh": (
        "今天是 {date_str}（{weekday}），当前北京时间约 {hour} 点。\n"
        "天气数据：{weather_text}\n"
        "今日 AI 日报共收录 {news_count} 条精选资讯。\n"
        "\n"
        "请你作为一个贴心的 AI 助手，为用户 Jocelyn 生成一段温暖的早报开场白，要求：\n"
        "\n"
        "1. **问候语**（1-2句）：用“{time_greeting}，Jocelyn！”开头，结合日期/星期和天气，语气自然亲切\n"
        "2. **天气 + 出行/生活提示**（2-3句）：根据天气数据给出实用的今日注意事项，如是否需要带伞、防晒、多穿衣等，语气贴心不啰嗦\n"
        "3. **AI 日报导语**（1句）：用简短一句话自然过渡到今日 AI 资讯，点出今天大模型/AI 领域有什么值得关注，带一点好奇心引导\n"
        "\n"
        "格式要求：\n"
        "- 使用 Discord markdown（**加粗**、换行用 \\n）\n"
        "- 总长度控制在 150 字以内\n"
        "- 不要加任何标题或编号\n"
        "- 直接输出正文，不要有前缀说明"
    ),
    "en": (
        "Today is {date_str} ({weekday}), current Beijing time approx {hour}:00.\n"
        "Weather: {weather_text}\n"
        "Today's AI digest includes {news_count} curated articles.\n"
        "\n"
        "As a thoughtful AI assistant for Jocelyn, write a warm daily briefing opener:\n"
        "\n"
        "1. **Greeting** (1-2 sentences): Start with \"{time_greeting}, Jocelyn!\", weaving in the date/day/weather naturally\n"
        "2. **Weather + tips** (2-3 sentences): Practical advice based on weather (umbrella, sunscreen, layers, etc.), warm but concise\n"
        "3. **AI digest intro** (1 sentence): Brief transition into the AI news, hinting at what's notable today with a touch of curiosity\n"
        "\n"
        "Format:\n"
        "- Use Discord markdown (**bold**, line breaks with \\n)\n"
        "- Keep total under 150 words\n"
        "- No titles or numbering\n"
        "- Output the body text directly, no preamble"
    ),
}

_GREETING_FALLBACK = {
    "zh": (
        "**{time_greeting}，Jocelyn！** 今天是 {date_str}（{weekday}）。\n"
        "{weather_text}\n"
        "以下是今日精选 AI 资讯，一起来看看 AI 世界今天发生了什么 ↓"
    ),
    "en": (
        "**{time_greeting}, Jocelyn!** Today is {date_str} ({weekday}).\n"
        "{weather_text}\n"
        "Here are today's curated AI stories — let's see what's happening in the AI world ↓"
    ),
}


# ═══════════════════════════════════════════════
# thought_generator.py
# ═══════════════════════════════════════════════

_THOUGHT_QUESTION_SYSTEM = {
    "zh": "你是一个帮助用户深度思考 AI 趋势的助手，善于提出有洞察力的问题。",
    "en": "You are an assistant that helps users think deeply about AI trends, skilled at asking insightful questions.",
}

_THOUGHT_QUESTION_USER = {
    "zh": (
        "今天是 {date_str}，以下是今日 AI 精选资讯：\n\n"
        "{articles_text}\n"
        "请基于以上内容，生成一个高质量的每日思考题，要求：\n"
        "1. 聚焦最有讨论价值的核心议题，而非事实性问题\n"
        "2. 问题有助于读者形成自己的观点，可以联系到实际工作或行业趋势\n"
        "3. 问题不要太宽泛（“你怎么看AI的未来”），要有具体的切入点\n\n"
        "严格按以下 JSON 格式返回，不要有其他文字：\n"
        '{{\n'
        '  "question": "<思考题，1-2句话>",\n'
        '  "context": "<提这个问题的背景，1-2句，说明为什么这个问题重要>",\n'
        '  "related_articles": [\n'
        '    {{"title": "<文章标题>", "source": "<来源>", "link": "<链接>"}},\n'
        '    ...\n'
        '  ]\n'
        '}}\n\n'
        "related_articles 选最相关的 1-3 篇，从上面文章列表中选取。"
    ),
    "en": (
        "Today is {date_str}. Here are today's AI highlights:\n\n"
        "{articles_text}\n"
        "Based on the above, generate a high-quality daily thought question:\n"
        "1. Focus on the most discussion-worthy core issue, not factual questions\n"
        "2. Help readers form their own opinions, connecting to real work or industry trends\n"
        "3. Not too broad (\"What do you think about AI's future?\"), have a specific angle\n\n"
        "Return strictly as JSON, no other text:\n"
        '{{\n'
        '  "question": "<thought question, 1-2 sentences>",\n'
        '  "context": "<background on why this question matters, 1-2 sentences>",\n'
        '  "related_articles": [\n'
        '    {{"title": "<article title>", "source": "<source>", "link": "<link>"}},\n'
        '    ...\n'
        '  ]\n'
        '}}\n\n'
        "Select the 1-3 most relevant related_articles from the article list above."
    ),
}

_REFINE_SYSTEM = {
    "zh": (
        "你是一位科技媒体评论编辑，专注于 AI 和企业技术领域。\n\n"
        "你的任务是对用户的科技评论进行**结构性重写**，而非仅优化用词。\n\n"
        "## 核心目标（按优先级）\n\n"
        "1. **理清论点层次** —— 识别用户真正想表达的核心观点，剔除赘述\n"
        "2. **重组信息框架** —— 将分散表达归并为清晰的逻辑段落（如：现状 → 驱动因素 → 问题/Trade-off → 结论）\n"
        "3. **提升信息密度** —— 保留有价值的细节，去掉填充句\n"
        "4. **统一论述口吻** —— 保持观察者视角，客观但有立场\n\n"
        "## 输出要求\n\n"
        "- 优先整合跨话题的重复内容，合并为单一论点\n"
        "- 每段只服务一个核心意思\n"
        "- 段落顺序遵循“结论前置 → 论据支撑”逻辑\n"
        "- 保留用户原有的判断和洞察，不引入新观点\n"
        "- 输出后附一行说明：**改动了哪些结构**（而非改了哪些词）\n\n"
        "## 输入\n\n"
        "用户将提供一段非正式的中文科技评论，可能语序混乱、话题交叉或逻辑跳跃。"
    ),
    "en": (
        "You are a tech media commentary editor, focused on AI and enterprise technology.\n\n"
        "Your task is a **structural rewrite** of the user's tech commentary, not just word polishing.\n\n"
        "## Core Goals (in priority order)\n\n"
        "1. **Clarify argument layers** — Identify the core points the user wants to express, remove filler\n"
        "2. **Restructure information** — Organize scattered thoughts into clear logical paragraphs (e.g., Status quo → Drivers → Issues/Trade-offs → Conclusion)\n"
        "3. **Increase information density** — Keep valuable details, drop padding\n"
        "4. **Unify tone** — Maintain an observer's perspective, objective but with a stance\n\n"
        "## Output Requirements\n\n"
        "- Merge cross-topic repetition into single arguments\n"
        "- Each paragraph serves one core idea\n"
        "- Paragraph order follows \"conclusion first → supporting evidence\" logic\n"
        "- Preserve the user's original judgments and insights, do not introduce new opinions\n"
        "- Append a note: **what structural changes were made** (not what words were changed)\n\n"
        "## Input\n\n"
        "The user will provide an informal tech commentary that may have disordered phrasing, topic crossovers, or logical jumps."
    ),
}

_REFINE_USER = {
    "zh": (
        "请对以下科技评论进行结构性重写。\n\n"
        "**背景问题：** {question}\n\n"
        "**相关文章：**\n"
        "{articles_context}\n\n"
        "**用户的原始评论：**\n"
        "{raw_reply}\n\n"
        "完成重写后，额外提取：\n"
        "1. 3-6 个核心关键词（概念名词，如“工具调用”、“Agent框架”、“长上下文”）\n"
        "2. 用户明确提到的信息来源（如“第2条”、“TechCrunch那篇”）\n\n"
        "严格按以下 JSON 格式返回，不要有其他文字：\n"
        '{{\n'
        '  "refined_answer": "<结构性重写后的完整内容，含末尾的改动说明>",\n'
        '  "keywords": ["关键词1", ...],\n'
        '  "sources_mentioned": ["来源描述1", ...]\n'
        '}}'
    ),
    "en": (
        "Please structurally rewrite the following tech commentary.\n\n"
        "**Background question:** {question}\n\n"
        "**Related articles:**\n"
        "{articles_context}\n\n"
        "**User's original comment:**\n"
        "{raw_reply}\n\n"
        "After rewriting, extract:\n"
        "1. 3-6 core keywords (concept nouns, e.g., \"tool calling\", \"Agent framework\", \"long context\")\n"
        "2. Information sources explicitly mentioned by the user (e.g., \"article #2\", \"the TechCrunch piece\")\n\n"
        "Return strictly as JSON, no other text:\n"
        '{{\n'
        '  "refined_answer": "<structurally rewritten content with change note at end>",\n'
        '  "keywords": ["keyword1", ...],\n'
        '  "sources_mentioned": ["source description1", ...]\n'
        '}}'
    ),
}

_INTENT_CLASSIFY_SYSTEM = {
    "zh": (
        "判断用户消息的意图，只回答一个词：answer / note / config。"
        "若用户在回应或讨论给定的问题 → answer；"
        "若用户在分享独立想法、观点、分析，与给定问题无直接关联 → note；"
        "若用户明确要求修改推送配置（如调整话题、数量、来源、天气城市等）→ config。"
        "只输出 answer、note 或 config，不要有其他内容。"
    ),
    "en": (
        "Classify the user's message intent, answer with ONE word: answer / note / config. "
        "If the user is responding to or discussing the given question → answer; "
        "If the user is sharing an independent thought, opinion, or analysis unrelated to the given question → note; "
        "If the user is explicitly requesting config changes (topics, count, sources, weather city, etc.) → config. "
        "Output only answer, note, or config, nothing else."
    ),
}

_INTENT_CLASSIFY_NO_QUESTION_SYSTEM = {
    "zh": (
        "判断用户消息的意图，只回答一个词：note / config。"
        "若用户明确要求修改推送配置（调整话题、数量、来源、语言、天气城市等）→ config；"
        "其他情况（分享想法、观点、分析等）→ note。"
        "只输出 config 或 note，不要有其他内容。"
    ),
    "en": (
        "Classify the user's message intent, answer with ONE word: note / config. "
        "If the user is explicitly requesting config changes (topics, count, sources, language, weather city, etc.) → config; "
        "Otherwise (sharing thoughts, opinions, analysis, etc.) → note. "
        "Output only config or note, nothing else."
    ),
}

_EXTRACT_KEYWORDS_USER = {
    "zh": (
        "问题：{question}\n"
        "相关文章：\n"
        "{articles_context}\n\n"
        "用户回复：{raw_reply[:500]}\n\n"
        "请完成：\n"
        "1. 提取 3-6 个核心关键词（名词或概念）\n"
        "2. 识别用户提到的信息来源（编号或名称）\n\n"
        "严格按 JSON 格式返回：\n"
        '{{"keywords": ["关键词1", ...], "sources_mentioned": ["来源1", ...]}}'
    ),
    "en": (
        "Question: {question}\n"
        "Related articles:\n"
        "{articles_context}\n\n"
        "User reply: {raw_reply[:500]}\n\n"
        "Please:\n"
        "1. Extract 3-6 core keywords (nouns or concepts)\n"
        "2. Identify information sources mentioned by the user (by number or name)\n\n"
        "Return strictly as JSON:\n"
        '{{"keywords": ["keyword1", ...], "sources_mentioned": ["source1", ...]}}'
    ),
}

_GENERATE_QUESTION_SYSTEM = {
    "zh": (
        "根据用户的想法，提炼出一个简洁的问题（15-40字），"
        "概括该想法在讨论什么核心议题。"
        "问题要有探讨价值，不要过于宽泛。"
        "只输出问题本身，不要有其他文字。"
    ),
    "en": (
        "Based on the user's thought, distill a concise question (10-30 words), "
        "summarizing the core topic being discussed. "
        "The question should have discussion value, not be too broad. "
        "Output only the question itself, nothing else."
    ),
}

_GENERATE_QUESTION_FALLBACK = {
    "zh": "独立思考记录",
    "en": "Independent Thought Record",
}

_FORMAT_THOUGHT_SECTION_TITLE = {
    "zh": "💭 **今日思考题**",
    "en": "💭 **Today's Thought Question**",
}

_FORMAT_THOUGHT_RELATED_LABEL = {
    "zh": "相关资讯：",
    "en": "Related articles:",
}

_FORMAT_THOUGHT_FOOTER = {
    "zh": (
        "_💡 直接回复你的想法，我会帮你整理成结构化观点并存入 Notion_\n"
        "_回复时可指出参考了哪几条资讯（如「参考第2、3条」）_"
    ),
    "en": (
        "_💡 Reply with your thoughts and I'll organize them into structured notes for Notion_\n"
        "_You can reference specific articles (e.g. \"referring to article #2, #3\")_"
    ),
}

_REFINE_KEYWORDS = {
    "zh": [
        "整理", "润色", "帮我整理", "帮我润色", "优化一下", "优化下",
        "polish", "refine", "rewrite", "帮我写", "整理成", "帮我表达",
        "文字不好", "写得不好", "表达一下", "更好地表达",
    ],
    "en": [
        "polish", "refine", "rewrite", "clean up", "edit", "reorganize",
        "help me write", "improve the wording", "make it better",
        "could you refine", "help me express",
        "整理", "润色", "帮我整理", "帮我润色", "优化一下",
    ],
}

_REFINE_CLASSIFY_SYSTEM = {
    "zh": "你判断用户的消息是否明确希望 AI 帮助整理、润色或优化他的文字表达。只回答 yes 或 no，不要有任何其他内容。",
    "en": "Determine if the user's message explicitly asks the AI to organize, polish, or refine their writing. Answer only yes or no, nothing else.",
}

_CONFIG_KEYWORDS = [
    # 中文
    "每次推送", "推送改为", "推送数量", "推送条数",
    "关注话题", "关注方向", "新闻方向",
    "天气改", "天气换", "城市改", "城市换", "城市设置",
    "把城市",
    "修改配置", "更新配置", "配置修改",
    # 英文
    "change weather", "change city", "set city", "update city",
    "change topics", "update topics", "focus on",
    "push count", "max articles", "number of articles",
    "change language", "switch to english", "switch to chinese",
    "enabled sources", "add source", "remove source",
    # 字段名
    "hours_back", "max_items", "enabled_sources",
    "focus_topics", "user_note", "weather_location", "language",
]


# ═══════════════════════════════════════════════
# weather_fetcher.py
# ═══════════════════════════════════════════════

_WEATHER_DESC_MAP = {
    "zh": {
        "Sunny": "晴",
        "Clear": "晴",
        "Partly cloudy": "多云",
        "Partly Cloudy": "多云",
        "Cloudy": "阴",
        "Overcast": "阴",
        "Mist": "薄雾",
        "Fog": "雾",
        "Freezing fog": "冻雾",
        "Light drizzle": "小雨",
        "Patchy light drizzle": "局部小雨",
        "Light rain": "小雨",
        "Patchy light rain": "局部小雨",
        "Moderate rain": "中雨",
        "Heavy rain": "大雨",
        "Light snow": "小雪",
        "Patchy light snow": "局部小雪",
        "Moderate snow": "中雪",
        "Heavy snow": "大雪",
        "Thunderstorm": "雷暴",
        "Patchy rain nearby": "局部有雨",
        "Light rain shower": "阵雨",
        "Moderate or heavy rain shower": "中到大阵雨",
        "Torrential rain shower": "暴雨",
        "Light sleet": "小雨夹雪",
        "Moderate or heavy sleet": "中到大雨夹雪",
        "Blizzard": "暴风雪",
        "Blowing snow": "吹雪",
        "Ice pellets": "冰粒",
    },
    "en": {},  # English stays as-is, no translation needed
}

_WEATHER_TEXT_TEMPLATE = {
    "zh": (
        "当前天气：{desc}，{temp}°C（体感 {feels_like}°C），"
        "最高 {high}°C / 最低 {low}°C，湿度 {humidity}%"
    ),
    "en": (
        "Currently: {desc}, {temp}°C (feels like {feels_like}°C), "
        "high {high}°C / low {low}°C, humidity {humidity}%"
    ),
}

_WEATHER_TEXT_TODAY = {
    "zh": "今天：{desc}，最高 {high}°C / 最低 {low}°C",
    "en": "Today: {desc}, high {high}°C / low {low}°C",
}

_WEATHER_TEXT_TOMORROW = {
    "zh": "明天：{desc}，最高 {high}°C / 最低 {low}°C",
    "en": "Tomorrow: {desc}, high {high}°C / low {low}°C",
}

_WEATHER_FALLBACK = {
    "zh": "暂无天气数据",
    "en": "Weather data unavailable",
}


# ═══════════════════════════════════════════════
# discord_client.py
# ═══════════════════════════════════════════════

_CATEGORY_LABELS = {
    "zh": {
        "论文": "论文",
        "技术博客": "技术博客",
        "行业动态": "行业动态",
        "行业新闻": "行业新闻",
        "社区讨论": "社区讨论",
    },
    "en": {
        "论文": "Paper",
        "技术博客": "Tech Blog",
        "行业动态": "Industry",
        "行业新闻": "Industry News",
        "社区讨论": "Community",
    },
}

_CATEGORY_ICONS = {
    "论文": "📄",
    "技术博客": "📝",
    "行业动态": "🏢",
    "行业新闻": "📰",
    "社区讨论": "💬",
}

_DIGEST_HEADER = {
    "zh": "📋 **{date_str} AI 日报** — 精选 {count} 条资讯",
    "en": "📋 **{date_str} AI Digest** — {count} curated articles",
}

_DIGEST_EMPTY = {
    "zh": "📭 **{date_str} AI 日报**\n\n今日暂无符合条件的 AI 资讯。",
    "en": "📭 **{date_str} AI Digest**\n\nNo qualifying AI articles today.",
}

_DIGEST_FOOTER = {
    "zh": "_由 AI News Bot 自动推送 · 发送 `!help` 查看可用指令_",
    "en": "_Auto-pushed by AI News Bot · Send `!help` to see available commands_",
}


# ═══════════════════════════════════════════════
# discord_handler.py
# ═══════════════════════════════════════════════

_HELP_TEXT = {
    "zh": (
        "🤖 **AI News Bot 使用指南**\n\n"
        "**内置命令：**\n"
        "`!help` - 查看帮助\n"
        "`!config` - 查看当前配置\n"
        "`!status` - 检查运行状态和最后推送时间\n"
        "`!push` - 立即推送今日 AI 早报\n\n"
        "**自然语言调整（直接发消息即可）：**\n"
        "  • 我只想看大模型相关的新闻\n"
        "  • 去掉论文类内容，只要行业新闻\n"
        "  • 每次推送改为 10 条\n"
        "  • 帮我关注 AI 安全和 AI Agent 方向\n"
        "  • 过滤掉关于图像生成的内容\n"
        "  • 天气改成北京\n"
        "  • 用英文推送\n\n"
        "> ⚠️ 使用 GitHub Actions 简化版，命令响应可能有延迟（`!push` 除外，实时执行）。"
    ),
    "en": (
        "🤖 **AI News Bot Guide**\n\n"
        "**Commands:**\n"
        "`!help` - Show this help\n"
        "`!config` - View current config\n"
        "`!status` - Check status and last push time\n"
        "`!push` - Push today's AI digest now\n\n"
        "**Natural language adjustments (just type a message):**\n"
        "  • I only want news about LLMs\n"
        "  • Remove paper content, only industry news\n"
        "  • Change to 10 articles per push\n"
        "  • Focus on AI safety and AI agents\n"
        "  • Filter out image generation content\n"
        "  • Change weather to London\n"
        "  • Switch to English\n\n"
        "> ⚠️ Using GitHub Actions simplified version, commands may have delays (except `!push` which runs immediately)."
    ),
}

_TEST_RESET_MESSAGE = {
    "zh": (
        "🧪 **测试配置已重置为默认值！**\n\n"
        "你现在可以重新指定所有偏好设置，例如：\n"
        "• 用英文推送\n"
        "• 每次推送 5 条\n"
        "• 只看 OpenAI 和 Anthropic 相关\n"
        "• 天气改成 New York\n"
        "• 去掉论文类内容\n\n"
        "配置完成后发送 `!push` 即可测试推送。"
    ),
    "en": (
        "🧪 **Test config reset to defaults!**\n\n"
        "You can now re-specify all preferences, for example:\n"
        "• Switch to Chinese\n"
        "• Push 5 articles each time\n"
        "• Only show OpenAI and Anthropic related news\n"
        "• Change weather to London\n"
        "• Remove paper content\n\n"
        "Send `!push` when ready to test."
    ),
}

_STATUS_TEMPLATE = {
    "zh": "✅ AI News Bot 运行正常！\n📅 最后推送日期：{last_push}\n⏰ 每天北京时间 09:00 自动推送。",
    "en": "✅ AI News Bot is running!\n📅 Last push date: {last_push}\n⏰ Auto push daily at 09:00 Beijing time.",
}

_DATE_FORMAT = {
    "zh": "{year}年{month}月{day}日",
    "en": "{month} {day}, {year}",
}


# ═══════════════════════════════════════════════
# insight_engine/analysis.py
# ═══════════════════════════════════════════════

_INSIGHT_ANALYSIS_SYSTEM = {
    "zh": (
        "你是一名资深 AI 行业分析师。你的工作不是逐条总结新闻，"
        "而是识别今日 AI 领域发生了什么变化、为什么重要。\n\n"
        "## 核心要求\n\n"
        "1. **解读而非总结**：避免用「几篇文章讨论了 X」开头，"
        "而是直接说明这些文章共同揭示了什么趋势或方向\n"
        "2. **主题聚类**：把文章归入 2-5 个主题，每个主题是一个有意义的"
        "叙事单元，不是简单按来源分类\n"
        "3. **矛盾识别**：同主题内若文章立场冲突，必须在 tension 中点明\n"
        "4. **核心信号**：key_signal 是一句话，必须是「今天最重要的变化是…」"
        "级别的判断，不是「今天有几条新闻」\n"
        "5. **跨主题关联**：找出主题之间的因果、对立或呼应关系\n\n"
        "## 输出要求\n\n"
        "严格返回 JSON，不要包裹 markdown 代码块，不要有任何解释性文字。"
    ),
    "en": (
        "You are a senior AI industry analyst. Your job is not to summarize "
        "individual news items, but to identify what changed today in the AI "
        "field and why it matters.\n\n"
        "## Core Requirements\n\n"
        "1. **Interpretation, not summary**: Avoid opening with \"Several articles "
        "discussed X\". Instead, state directly what trend or direction the articles "
        "collectively reveal.\n"
        "2. **Thematic clustering**: Group articles into 2-5 themes. Each theme must "
        "be a meaningful narrative unit, not a simple source-based grouping.\n"
        "3. **Tension detection**: If articles within a theme conflict, you MUST flag "
        "it in the tension field.\n"
        "4. **Key signal**: key_signal is a single sentence at the level of "
        "\"The most important change today is...\", not \"There were N news items today.\"\n"
        "5. **Cross-theme connection**: Identify causal, opposing, or echoing "
        "relationships between themes.\n\n"
        "## Output Requirements\n\n"
        "Return strict JSON. Do not wrap in markdown code blocks. Do not include "
        "any explanatory text."
    ),
}

_INSIGHT_ANALYSIS_USER = {
    "zh": (
        "今天是 {date}。以下是今日 AI 精选资讯（每条含标题、来源、链接、摘要）：\n\n"
        "{articles_text}\n"
        "请分析并返回如下 JSON 结构：\n"
        "{{\n"
        '  "date": "{date}",\n'
        '  "language": "zh",\n'
        '  "article_count": {article_count},\n'
        '  "themes": [\n'
        '    {{\n'
        '      "name": "<主题名，简短>",\n'
        '      "articles": [\n'
        '        {{\n'
        '          "title": "<原标题>",\n'
        '          "link": "<原链接>",\n'
        '          "source": "<来源>",\n'
        '          "ai_summary": "<原摘要>"\n'
        '        }}\n'
        '      ],\n'
        '      "narrative": "<2-3 句解读：这些文章共同揭示了什么>",\n'
        '      "tension": null 或 "<同主题内的矛盾点说明>"\n'
        '    }}\n'
        '  ],\n'
        '  "key_signal": "<一句话：今日最重要的变化>",\n'
        '  "cross_theme_connection": "<1-2 句：主题间的关联或对立>"\n'
        "}}\n\n"
        "注意事项：\n"
        "- articles 字段必须完整内联文章的 4 个字段，不要用索引引用\n"
        "- 每篇文章必须归入某个主题，不要遗漏\n"
        "- tension 为 null 时表示无矛盾，不要写空字符串\n"
        "- 不要包裹 ```json，直接输出 JSON 对象"
    ),
    "en": (
        "Today is {date}. Below are today's curated AI news (each has title, source, link, summary):\n\n"
        "{articles_text}\n"
        "Analyze and return the following JSON structure:\n"
        "{{\n"
        '  "date": "{date}",\n'
        '  "language": "en",\n'
        '  "article_count": {article_count},\n'
        '  "themes": [\n'
        '    {{\n'
        '      "name": "<short theme name>",\n'
        '      "articles": [\n'
        '        {{\n'
        '          "title": "<original title>",\n'
        '          "link": "<original link>",\n'
        '          "source": "<source>",\n'
        '          "ai_summary": "<original summary>"\n'
        '        }}\n'
        '      ],\n'
        '      "narrative": "<2-3 sentences: what these articles collectively reveal>",\n'
        '      "tension": null or "<contradiction within this theme>"\n'
        '    }}\n'
        '  ],\n'
        '  "key_signal": "<one sentence: the most important change today>",\n'
        '  "cross_theme_connection": "<1-2 sentences: relationship between themes>"\n'
        "}}\n\n"
        "Notes:\n"
        "- articles field must inline all 4 article fields, do not use index references\n"
        "- every article must be assigned to a theme, none omitted\n"
        "- tension is null when no contradiction, not an empty string\n"
        "- do not wrap in ```json, output the JSON object directly"
    ),
}


# ═══════════════════════════════════════════════
# insight_engine/renderers/
# ═══════════════════════════════════════════════

_INSIGHT_RENDER_LINKEDIN_SYSTEM = {
    "zh": (
        "你写 LinkedIn 帖子，让读者读完后觉得自己变聪明了，而不是被信息淹没。"
        "短段落。一篇帖子只讲一个大观点。以提问结尾引发讨论。"
    ),
    "en": (
        "You write LinkedIn posts that make readers feel smarter, not overwhelmed. "
        "Short paragraphs. One big idea per post. End with a question to invite discussion."
    ),
}

_INSIGHT_RENDER_LINKEDIN_USER = {
    "zh": (
        "基于以下 AI 新闻分析，写一篇 LinkedIn 帖子：\n\n"
        "**核心信号：** {key_signal}\n\n"
        "**主题分析：**\n{themes_text}\n\n"
        "**跨主题关联：** {cross_theme_connection}\n\n"
        "要求：\n"
        "- 开头一行抓住注意力（hook）\n"
        "- 每个主题用 1-2 句话讲清楚\n"
        "- 核心信号作为关键 takeaway 呈现\n"
        "- 以一个开放性问题结尾，引发讨论\n"
        "- 专业但有对话感的语气，不要企业腔\n"
        "- 800-1500 字符\n"
        "- 不要使用 hashtag\n"
        "- 直接输出帖子正文，不要加「LinkedIn 帖子：」之类的前缀"
    ),
    "en": (
        "Write a LinkedIn post based on the following AI news analysis:\n\n"
        "**Key signal:** {key_signal}\n\n"
        "**Theme analysis:**\n{themes_text}\n\n"
        "**Cross-theme connection:** {cross_theme_connection}\n\n"
        "Requirements:\n"
        "- Hook in the first line\n"
        "- Cover each theme in 1-2 sentences\n"
        "- Include the key signal as the core takeaway\n"
        "- End with an open question to invite discussion\n"
        "- Professional but conversational tone, not corporate\n"
        "- 800-1500 characters\n"
        "- No hashtags\n"
        "- Output the post body directly, no preamble like \"LinkedIn post:\""
    ),
}

_INSIGHT_RENDER_NEWSLETTER_SYSTEM = {
    "zh": "你写一份每日 AI 通讯，读者是技术从业者。语气专业但有观点，段落之间有过渡。",
    "en": "You write a daily AI newsletter for technical practitioners. Professional but opinionated, with smooth transitions between sections.",
}

_INSIGHT_RENDER_NEWSLETTER_USER = {
    "zh": (
        "基于以下 AI 新闻分析，写一份 newsletter：\n\n"
        "**核心信号：** {key_signal}\n\n"
        "**主题分析：**\n{themes_text}\n\n"
        "**跨主题关联：** {cross_theme_connection}\n\n"
        "要求：\n"
        "- 标题（subject line）：一句话概括今日最重要的变化\n"
        "- 开头导语（2-3 句）：点明今天的关键信号\n"
        "- 每个主题作为一个小节，标题用 ## 标记\n"
        "- 每节内容 100-200 字，给出解读而非罗列\n"
        "- 引用原文时可附链接（markdown 格式）\n"
        "- 结尾一段总结性观点，呼应跨主题关联\n"
        "- 1500-3000 字符\n"
        "- markdown 格式输出"
    ),
    "en": (
        "Write a newsletter based on the following AI news analysis:\n\n"
        "**Key signal:** {key_signal}\n\n"
        "**Theme analysis:**\n{themes_text}\n\n"
        "**Cross-theme connection:** {cross_theme_connection}\n\n"
        "Requirements:\n"
        "- Subject line: one sentence summarizing today's most important change\n"
        "- Opening (2-3 sentences): state the key signal\n"
        "- Each theme as a section, with ## heading\n"
        "- 100-200 words per section, interpretation not listing\n"
        "- Include links when referencing articles (markdown format)\n"
        "- Closing paragraph with a synthesizing view, echoing the cross-theme connection\n"
        "- 1500-3000 characters\n"
        "- Markdown format"
    ),
}

_INSIGHT_RENDER_PODCAST_SYSTEM = {
    "zh": (
        "你为一档 3 分钟的 AI 播客节目写脚本。主持人（A）和嘉宾（B）对话形式。"
        "语气自然、口语化，像两个内行人在聊天。每段对话有时间标注。"
    ),
    "en": (
        "You write scripts for a 3-minute AI podcast. Host (A) and guest (B) dialogue format. "
        "Natural, conversational tone, like two insiders chatting. Include time markers per segment."
    ),
}

_INSIGHT_RENDER_PODCAST_USER = {
    "zh": (
        "基于以下 AI 新闻分析，写一档约 3 分钟播客的脚本：\n\n"
        "**核心信号：** {key_signal}\n\n"
        "**主题分析：**\n{themes_text}\n\n"
        "**跨主题关联：** {cross_theme_connection}\n\n"
        "要求：\n"
        "- 主持人 A 和嘉宾 B 交替发言，每段标注时长（如 (30s)）\n"
        "- 开场（~20s）：A 引出今日主题\n"
        "- 每个主题一段对话（~30-40s each）\n"
        "- 收尾（~20s）：B 给出一句结论性观点\n"
        "- 总时长控制在 3 分钟左右\n"
        "- 口语化，避免书面语；可以适度用「啊」「嗯」「对」等语气词，但不要过量\n"
        "- 不要逐条念新闻，要像两个人在讨论\n"
        "- 格式：\n"
        "  A (20s): ...\n"
        "  B (30s): ...\n"
        "  A (15s): ..."
    ),
    "en": (
        "Write a ~3-minute podcast script based on the following AI news analysis:\n\n"
        "**Key signal:** {key_signal}\n\n"
        "**Theme analysis:**\n{themes_text}\n\n"
        "**Cross-theme connection:** {cross_theme_connection}\n\n"
        "Requirements:\n"
        "- Host A and guest B alternate, with time markers per turn (e.g., (30s))\n"
        "- Opening (~20s): A introduces today's topic\n"
        "- One segment per theme (~30-40s each)\n"
        "- Closing (~20s): B gives a concluding thought\n"
        "- Total ~3 minutes\n"
        "- Conversational, avoid written-style phrasing; use \"yeah\", \"right\", \"hmm\" sparingly\n"
        "- Don't read news items one by one; make it sound like a real discussion\n"
        "- Format:\n"
        "  A (20s): ...\n"
        "  B (30s): ...\n"
        "  A (15s): ..."
    ),
}

_INSIGHT_RENDER_BILINGUAL_SYSTEM = {
    "zh": (
        "你为中英双语读者写一份每日 AI 分析。两种语言都承载完整叙述，"
        "不是把一种语言翻译成另一种。中文部分用中文写作思维，"
        "英文部分用英文写作思维，两者内容对等但表达各自自然。"
    ),
    "en": (
        "You write a daily AI analysis for bilingual readers. Both languages carry "
        "full narratives — not translation of one to the other. Write the Chinese part "
        "with Chinese thinking patterns, the English part with English thinking patterns. "
        "The two are equivalent in content but each reads naturally in its own language."
    ),
}

_INSIGHT_RENDER_BILINGUAL_USER = {
    "zh": (
        "基于以下 AI 新闻分析，写一份中英双语版本：\n\n"
        "**核心信号：** {key_signal}\n\n"
        "**主题分析：**\n{themes_text}\n\n"
        "**跨主题关联：** {cross_theme_connection}\n\n"
        "要求：\n"
        "- 先写中文版完整叙述，再写英文版完整叙述，用 --- 分隔\n"
        "- 中文版：标题 + 导语（核心信号）+ 每个主题一段 + 收尾\n"
        "- 英文版：同样的结构，但用英文写作思维表达，不要逐句翻译中文版\n"
        "- 每段 80-150 字/词\n"
        "- markdown 格式\n"
        "- 总长度控制在 2000-4000 字符\n"
        "- 输出格式：\n"
        "  # 今日 AI 解读 / Today's AI Brief\n"
        "  \n"
        "  ## 中文版\n"
        "  ...\n"
        "  \n"
        "  ---\n"
        "  \n"
        "  ## English Version\n"
        "  ..."
    ),
    "en": (
        "Write a bilingual (Chinese + English) version based on the following AI news analysis:\n\n"
        "**Key signal:** {key_signal}\n\n"
        "**Theme analysis:**\n{themes_text}\n\n"
        "**Cross-theme connection:** {cross_theme_connection}\n\n"
        "Requirements:\n"
        "- Write the Chinese version first as a complete narrative, then the English version, separated by ---\n"
        "- Chinese version: title + lead (key signal) + one paragraph per theme + closing\n"
        "- English version: same structure, but written with English thinking, not sentence-by-sentence translation\n"
        "- 80-150 words/chars per paragraph\n"
        "- Markdown format\n"
        "- Total 2000-4000 characters\n"
        "- Output format:\n"
        "  # 今日 AI 解读 / Today's AI Brief\n"
        "  \n"
        "  ## 中文版\n"
        "  ...\n"
        "  \n"
        "  ---\n"
        "  \n"
        "  ## English Version\n"
        "  ..."
    ),
}


# ═══════════════════════════════════════════════
# 注册表
# ═══════════════════════════════════════════════

# 特殊类型：非字符串，不能通过 get() 获取，直接从模块导入
REFINE_KEYWORDS = _REFINE_KEYWORDS
CONFIG_KEYWORDS = _CONFIG_KEYWORDS
CATEGORY_ICONS = _CATEGORY_ICONS


def get_refine_keywords(lang: str = "zh") -> list[str]:
    """获取润色关键词列表（合并中英文）"""
    zh_kw = _REFINE_KEYWORDS.get("zh", [])
    en_kw = _REFINE_KEYWORDS.get("en", [])
    if lang == "en":
        return en_kw + zh_kw
    return zh_kw + en_kw


def get_config_keywords() -> list[str]:
    """获取配置关键词列表（中英文合并）"""
    return _CONFIG_KEYWORDS


_PROMPTS = {
    # ai_processor
    "select_summarize_system": _SELECT_SUMMARIZE_SYSTEM,
    "select_summarize_user": _SELECT_SUMMARIZE_USER,
    "select_summarize_focus_fallback": _SELECT_SUMMARIZE_FOCUS_FALLBACK,
    "select_summarize_user_note_prefix": _SELECT_SUMMARIZE_USER_NOTE_PREFIX,
    "process_command_system": _PROCESS_COMMAND_SYSTEM,
    "process_command_user": _PROCESS_COMMAND_USER,
    # morning_greeter
    "greeting_system": _GREETING_SYSTEM,
    "greeting_user": _GREETING_USER,
    "greeting_fallback": _GREETING_FALLBACK,
    # thought_generator
    "thought_question_system": _THOUGHT_QUESTION_SYSTEM,
    "thought_question_user": _THOUGHT_QUESTION_USER,
    "refine_system": _REFINE_SYSTEM,
    "refine_user": _REFINE_USER,
    "intent_classify_system": _INTENT_CLASSIFY_SYSTEM,
    "intent_classify_no_question_system": _INTENT_CLASSIFY_NO_QUESTION_SYSTEM,
    "extract_keywords_user": _EXTRACT_KEYWORDS_USER,
    "generate_question_system": _GENERATE_QUESTION_SYSTEM,
    "generate_question_fallback": _GENERATE_QUESTION_FALLBACK,
    "format_thought_section_title": _FORMAT_THOUGHT_SECTION_TITLE,
    "format_thought_related_label": _FORMAT_THOUGHT_RELATED_LABEL,
    "format_thought_footer": _FORMAT_THOUGHT_FOOTER,
    "refine_classify_system": _REFINE_CLASSIFY_SYSTEM,
    # weather_fetcher
    "weather_desc_map": _WEATHER_DESC_MAP,
    "weather_text_template": _WEATHER_TEXT_TEMPLATE,
    "weather_text_today": _WEATHER_TEXT_TODAY,
    "weather_text_tomorrow": _WEATHER_TEXT_TOMORROW,
    "weather_fallback": _WEATHER_FALLBACK,
    # discord_client
    "category_labels": _CATEGORY_LABELS,
    "digest_header": _DIGEST_HEADER,
    "digest_empty": _DIGEST_EMPTY,
    "digest_footer": _DIGEST_FOOTER,
    # discord_handler
    "help_text": _HELP_TEXT,
    "test_reset_message": _TEST_RESET_MESSAGE,
    "status_template": _STATUS_TEMPLATE,
    "date_format": _DATE_FORMAT,
    # insight_engine/analysis
    "insight_analysis_system": _INSIGHT_ANALYSIS_SYSTEM,
    "insight_analysis_user": _INSIGHT_ANALYSIS_USER,
    # insight_engine/renderers
    "insight_render_linkedin_system": _INSIGHT_RENDER_LINKEDIN_SYSTEM,
    "insight_render_linkedin_user": _INSIGHT_RENDER_LINKEDIN_USER,
    "insight_render_newsletter_system": _INSIGHT_RENDER_NEWSLETTER_SYSTEM,
    "insight_render_newsletter_user": _INSIGHT_RENDER_NEWSLETTER_USER,
    "insight_render_podcast_system": _INSIGHT_RENDER_PODCAST_SYSTEM,
    "insight_render_podcast_user": _INSIGHT_RENDER_PODCAST_USER,
    "insight_render_bilingual_system": _INSIGHT_RENDER_BILINGUAL_SYSTEM,
    "insight_render_bilingual_user": _INSIGHT_RENDER_BILINGUAL_USER,
}
