# Insight Engine — 完整数据流分析

> 本文档梳理从上游 news bot 到下游 Insight Engine 的完整数据流，作为实现前的对齐记录。
> 设计文档见 [`insight-engine-design.md`](./insight-engine-design.md)。

---

## 1. 数据流总览（三层）

```
┌────────────────────────────────────────────────────────────────────┐
│  第 1 层：上游 — 信息采集                                           │
│  RSS/HN → news_fetcher → ai_processor (DeepSeek select+summarize)  │
│  产出：selected articles + ai_summary                              │
└──────────────────────────┬─────────────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────────────────┐
│  第 2 层：上游 — 推送管线 (daily_push.py)                            │
│  weather + greeting (DeepSeek) + Discord 推送                      │
│  + thought question (DeepSeek)                                     │
│  产出：config/today_thought_context.json                           │
│  其中 all_articles 字段 = 下游输入接口                              │
└──────────────────────────┬─────────────────────────────────────────┘
                           │
                           │ ★ 解耦边界（仅文件接口，无 import 跨界）
                           ▼
┌────────────────────────────────────────────────────────────────────┐
│  第 3 层：下游 — Insight Engine (新建，独立 workflow)                │
│  读 all_articles → ingestion → cache → analysis (DeepSeek)         │
│  → renderers (DeepSeek per format) → output/insight/{date}/        │
└────────────────────────────────────────────────────────────────────┘
```

---

## 2. 第 1 层：信息采集

### 2.1 数据流

```
RSS / HN API
    │
    ▼
news_fetcher.fetch_all_news(config)
    │  - 抓取 RSS 源（FEED_SOURCES 中 enabled 的）
    │  - 抓取 HN Top Stories（AI 关键词过滤）
    │  - 按 include/exclude_keywords 过滤
    │  - 按 pub_date 倒序排列
    │
    ▼
ai_processor.select_and_summarize(articles, config)
    │  - DeepSeek 调用（temp=0.3, max_tokens=3000）
    │  - 从 ≤60 篇里选 max_items 条（默认 8）
    │  - 为每条生成 2-3 句中文 ai_summary
    │  - 按重要性排序
    │
    ▼
selected articles (list[dict])
```

### 2.2 数据结构

**Raw article**（news_fetcher 产出）：
```python
{
    "title": str,
    "link": str,
    "summary": str,           # RSS summary 前 500 字符
    "source": str,            # 如 "TechCrunch AI"
    "category": str,          # 论文/技术博客/行业动态/行业新闻/社区讨论
    "pub_date": str,          # ISO 8601 UTC
}
```

**Selected article**（ai_processor 产出，加上 ai_summary）：
```python
{
    "index": int,             # 原始编号
    "title": str,
    "source": str,
    "category": str,
    "link": str,
    "ai_summary": str,        # 2-3 句中文摘要
}
```

### 2.3 LLM 调用

| 调用 | 模型 | temp | max_tokens | 用途 |
|---|---|---|---|---|
| `select_and_summarize` | deepseek-chat | 0.3 | 3000 | 筛选 + 摘要 |

---

## 3. 第 2 层：推送管线 (daily_push.py)

### 3.1 6 步流水线

```
Step 1: weather_fetcher.get_weather(location)
        → wttr.in API
        → weather dict (temp_c, description, ...)

Step 2: news_fetcher.fetch_all_news(config)
        → list[dict] (raw articles)

Step 3: ai_processor.select_and_summarize(articles, config)
        → list[dict] (selected + ai_summary)   ← 1 次 DeepSeek

Step 4: morning_greeter.generate_morning_greeting(...)
        → ≤150 字问候语                         ← 1 次 DeepSeek (temp=0.8)

Step 5: discord_client.send_digest(greeting, selected, ...)
        → 发送到 Discord 频道（Embed 批量）

Step 6: thought_generator.generate_thought_question(selected, ...)
        → {question, context, related_articles}  ← 1 次 DeepSeek (temp=0.7)
        → 发送思考题消息到 Discord
        → 保存到 config/today_thought_context.json

Final:  mark_pushed_today() → 写入 last_push_date.txt
```

### 3.2 上游产出文件（解耦边界）

**`config/today_thought_context.json`**：

```json
{
  "date": "2026-07-07",
  "question": "...",
  "context": "...",
  "related_articles": [
    {"title": "...", "source": "...", "link": "..."}
  ],
  "all_articles": [
    {
      "title": "...",
      "source": "...",
      "link": "...",
      "ai_summary": "..."
    },
    ...
  ],
  "answered": false
}
```

**`all_articles` 是下游 Insight Engine 的唯一输入接口**。

注意：`all_articles` 中每条只含 4 个字段（`title`, `source`, `link`, `ai_summary`），不再有 `category`、`pub_date`、`summary`。下游必须基于这 4 个字段工作。

### 3.3 上游 LLM 调用总计

每次 `daily_push` 运行共 **3 次 DeepSeek 调用**：
1. select_and_summarize（筛选 + 摘要）
2. generate_morning_greeting（问候语）
3. generate_thought_question（思考题）

---

## 4. 第 3 层：下游 Insight Engine（待实现）

### 4.1 触发方式

独立 GitHub Actions workflow：`.github/workflows/insight_engine.yml`

```yaml
on:
  workflow_run:
    workflows: ["AI 每日资讯推送"]
    types: [completed]
    branches: [main]
  workflow_dispatch:  # 支持手动触发，便于调试
```

- 上游 `daily_push.yml` 完成后自动触发
- 失败/取消的上游运行不会触发下游
- 可手动 `workflow_dispatch` 单独重跑，不影响 Discord

### 4.2 数据流（下游内部）

```
① 读取 config/today_thought_context.json
   → all_articles: list[dict]
   → 提取 date 用于缓存键

② ingestion.py（零 LLM）
   → 验证字段（title, link, ai_summary 必填）
   → 按 link 去重
   → 标准化为内部 article 格式

③ cache.py（文件缓存）
   → 指纹 = hash(date + sorted(links) + language)
   → 命中 → 跳过 analysis，直接读 InsightPackage
   → 未命中 → 进入 ④

④ analysis.py（1 次 DeepSeek，temp=0.5）
   → 主题聚类（2-5 个 themes）
   → 每个 theme 内嵌精简文章（title/link/source/ai_summary）
   → key_signal（一句话核心信号）
   → cross_theme_connection（跨主题关联）
   → tension（同主题内矛盾点，可为 null）
   → 写入 config/insight_cache/{date}.json

⑤ renderers/（每格式 1 次 DeepSeek）
   → linkedin.py    → output/insight/{date}/linkedin.md
   → newsletter.py  → output/insight/{date}/newsletter.md
   → podcast_script.py → output/insight/{date}/podcast_script.md
   → bilingual.py   → output/insight/{date}/bilingual.md
   （调试期可同时发送到 Discord 测试频道）

⑥ 输出
   → output/insight/{date}/{format}.md（落盘，便于检视）
   → 未来：social media API
```

### 4.3 下游 LLM 调用

每次运行共 **1 + N 次** DeepSeek 调用（N = 请求的格式数）：

| 调用 | temp | max_tokens | 用途 |
|---|---|---|---|
| `analysis` | 0.5 | 2000 | 主题聚类 + 叙述合成 + 信号提取 |
| `render_linkedin` | 0.7 | 800 | LinkedIn post |
| `render_newsletter` | 0.6 | 1200 | Newsletter |
| `render_podcast` | 0.7 | 1000 | Podcast script |
| `render_bilingual` | 0.6 | 1500 | 中英双语 |

缓存命中时跳过 `analysis`，仅剩 N 次渲染调用。

---

## 5. 解耦边界明确化

### 5.1 上游→下游的唯一数据接口

```
config/today_thought_context.json
  └── all_articles: list[dict]
        └── {title, source, link, ai_summary}
```

### 5.2 边界两侧的独立性

| 维度 | 上游 (daily_push) | 下游 (insight_engine) |
|---|---|---|
| Workflow 文件 | `daily_push.yml` | `insight_engine.yml` |
| 触发 | 外部 cron-job.org + 手动 | `workflow_run` + 手动 |
| Python 入口 | `scripts/daily_push.py` | `scripts/insight_engine_run.py` |
| 模块路径 | `src/` 根目录 | `src/insight_engine/` 子包 |
| 失败影响 | Discord 推送失败 | 仅 insight 输出缺失，不影响推送 |
| 重跑代价 | 重复推送 Discord | 仅重新生成 insight 输出 |
| 状态文件 | `last_push_date.txt`, `today_thought_context.json` | `config/insight_cache/{date}.json` |
| 输出位置 | Discord 频道 | `output/insight/{date}/` |

### 5.3 边界两侧禁止的事

- ❌ 下游 import 上游模块（如 `from ai_processor import ...`）
- ❌ 上游 import 下游模块
- ❌ 下游直接调用 Discord 推送函数（除非显式选择发送到测试频道）
- ❌ 下游修改 `today_thought_context.json`（只读）

---

## 6. 关键时间线

```
T+0:00   外部 cron-job.org 触发 daily_push.yml
T+0:30   daily_push 开始：weather + news_fetch
T+1:30   DeepSeek select_and_summarize 完成
T+1:45   DeepSeek greeting 完成
T+1:50   Discord 推送完成
T+2:00   DeepSeek thought_question 完成
T+2:10   today_thought_context.json 写入并 commit
T+2:15   daily_push.yml 标记 completed

T+2:16   workflow_run 触发 insight_engine.yml
T+2:20   读取 today_thought_context.json
T+2:21   ingestion 完成（零 LLM）
T+2:22   cache 未命中 → 进入 analysis
T+2:35   DeepSeek analysis 完成 → InsightPackage 缓存
T+2:36   4 个 renderer 并行调用 DeepSeek
T+2:50   全部渲染完成 → 写入 output/insight/{date}/
T+2:51   insight_engine.yml 标记 completed
```

总计：从上游触发到下游完成约 **3 分钟**，新增 5 次 DeepSeek 调用（1 analysis + 4 render）。

---

## 7. 实现顺序（对应 TaskList）

1. **`src/insight_engine/schemas.py`** — InsightPackage TypedDict
2. **`src/insight_engine/ingestion.py`** — 验证 + 去重
3. **`src/insight_engine/cache.py`** — 文件缓存
4. **`src/insight_engine/analysis.py`** — 1 次 LLM 调用 + prompts
5. **`src/insight_engine/renderers/`** — 4 个渲染器 + 注册表
6. **`src/insight_engine/pipeline.py`** — 编排器
7. **`scripts/insight_engine_run.py` + `.github/workflows/insight_engine.yml`**

步骤 1-3 无 LLM 依赖，可独立测试。
