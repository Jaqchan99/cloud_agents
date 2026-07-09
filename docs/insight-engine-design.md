# Insight Engine — Design Document

## 0. Why This Architecture Is Chosen Over a Single-Prompt Solution

A single-prompt solution ("take these articles and write a LinkedIn post") appears simpler but fails on four fronts:

| Concern | Single-prompt | Multi-stage pipeline |
|---|---|---|
| **Token cost** | Sends all articles + full instruction each time. Every format variant re-processes the full input. | Articles are condensed into a compact `InsightPackage` once. Format renderers consume only the condensed representation (~1/5 the tokens). |
| **Quality control** | Unstructured output; no guarantee of analytical depth. Hard to debug why an output was shallow. | Each stage has a typed, validated intermediate schema. You can inspect "the narrative" before it's rendered, and debug a single stage. |
| **Extensibility** | Adding a new output format means rewriting the whole prompt. | New format = new renderer function that implements a known interface. Core analysis stages are untouched. |
| **Caching granularity** | Cannot cache partial work. Re-rendering for a different format repeats the full LLM call. | The InsightPackage is cacheable. Re-rendering to a different format only invokes the cheap renderer stage. |

The pipeline also creates the right **intellectual separation**: analysis/interpretation work is done once upstream, and formatting decisions are made independently downstream. This matches the business requirement of decoupling "what we think about the news" from "how we present it."

---

## 1. Overall Architecture

```
                    ┌─────────────────────┐
                    │  Upstream:           │
                    │  AI News Feed Bot    │
                    │  (existing, separate │
                    │   GitHub workflow)   │
                    │                      │
                    │  Output:             │
                    │   config/            │
                    │   today_thought_     │
                    │   context.json       │
                    │   (all_articles)     │
                    └──────────┬──────────┘
                               │
                               │ articles (JSON file — sole interface)
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│                    Insight Engine (new module)                    │
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌───────────────────┐  │
│  │ Stage 1:     │    │ Stage 2:     │    │ Stage 3:          │  │
│  │ Ingestion    │───▶│ Analysis     │───▶│ Rendering         │  │
│  │              │    │              │    │                   │  │
│  │ - Validate   │    │ - Thematic   │    │ - LinkedIn format │  │
│  │ - Dedup      │    │   clustering │    │ - Newsletter      │  │
│  │ - Classify   │    │ - Narrative  │    │ - Podcast script  │  │
│  │              │    │   synthesis  │    │ - Bilingual (zh)  │  │
│  │              │    │ - Signal     │    │ - Bilingual (en)  │  │
│  │              │    │   extraction │    │                   │  │
│  └──────────────┘    └──────┬───────┘    └──────┬────────────┘  │
│                             │                   │               │
│                             ▼                   ▼               │
│                    ┌──────────────────┐                          │
│                    │  Intermediate    │                          │
│                    │  InsightPackage  │                          │
│                    │  (cacheable)     │                          │
│                    └──────────────────┘                          │
└──────────────────────────────────────────────────────────────────┘
                               │
                               │ rendered output (format-specific)
                               ▼
                    ┌─────────────────────┐
                    │  Output Channel(s)   │
                    │  (future: social     │
                    │   media API,         │
                    │   newsletter, etc.)  │
                    └─────────────────────┘
```

**Key boundary**: The Insight Engine is a separate GitHub Actions workflow that reads `config/today_thought_context.json` (written by the upstream push pipeline). No module imports cross the boundary. It is triggered by `workflow_run` after `daily_push.yml` completes, can be re-run independently without re-pushing to Discord, and its failures do not affect the upstream push.

---

## 2. Module Responsibilities

### 2.1 `src/insight_engine/__init__.py`
Package init. Exports the main entry point `run_insight_pipeline()`.

### 2.2 `src/insight_engine/ingestion.py` (Stage 1)
- **Input**: Raw article list (`list[dict]` with `title`, `source`, `link`, `ai_summary`, `category`).
- **Output**: Cleaned, normalized article list (`list[dict]`).
- **Responsibilities**:
  - Validate that each article has the required fields (title, link, ai_summary).
  - Remove duplicates by link.
  - Tag articles with sub-categories or themes if missing (lightweight keyword-based, no LLM call).
- **Non-responsibilities**: No LLM call. Pure data processing.

### 2.3 `src/insight_engine/analysis.py` (Stage 2 — LLM core)
- **Input**: Cleaned article list from Stage 1.
- **Output**: An `InsightPackage` (see Section 4 for schema).
- **Responsibilities**:
  - **Thematic clustering**: Group articles into 2-5 broad themes (e.g., "Model Releases", "Regulation", "Open Source vs Closed Source").
  - **Narrative synthesis**: For each theme, write a 2-3 sentence interpretation of *what changed today* — not a summary of each article, but an analysis of the direction/trend.
  - **Signal extraction**: Identify the single most important signal of the day (one sentence: "The key takeaway from today's news is...").
  - **Tension/contradiction detection**: If articles within a theme contradict each other, flag it.
- **LLM calls**: One call. The prompt asks for analysis, not formatting. Temperature: 0.5 (balance of creativity and consistency). Max tokens: 2000.

### 2.4 `src/insight_engine/renderers/__init__.py`
Renderer registry. Maps format name → renderer function.

```python
RENDERERS: dict[str, Callable] = {
    "linkedin": render_linkedin,
    "newsletter": render_newsletter,
    "podcast_script": render_podcast_script,
    "bilingual_zh": render_bilingual_zh,
    "bilingual_en": render_bilingual_en,
}
```

### 2.5 `src/insight_engine/renderers/linkedin.py`
- **Input**: `InsightPackage`.
- **Output**: LinkedIn-optimized post text.
- **Style**: Professional but not corporate. 800–1500 characters. Has a hook opening, thematic breakdown, key signal, and a closing question to drive engagement.

### 2.6 `src/insight_engine/renderers/newsletter.py`
- **Input**: `InsightPackage`.
- **Output**: Newsletter-style HTML/text.
- **Style**: Longer-form (1500–3000 chars). Section headers for each theme. More explanatory. Can include pull quotes from original articles.

### 2.7 `src/insight_engine/renderers/podcast_script.py`
- **Input**: `InsightPackage`.
- **Output**: Script for a ~3-minute podcast segment.
- **Style**: Conversational. Host + co-host dialogue format. Timing annotations ((30s)). Segues between themes.

### 2.8 `src/insight_engine/renderers/bilingual.py`
- **Input**: `InsightPackage`.
- **Output**: Side-by-side Chinese/English or paragraph-alternating format.
- **Style**: Both languages carry the full narrative (not translation of one to the other). Two variants via a `lang` parameter: `"zh_first"` and `"en_first"`.

### 2.9 `src/insight_engine/pipeline.py`
- **Orchestrator**. Calls Stage 1 → Stage 2 → Stage 3.
- **Input**: articles + format name(s).
- **Output**: Rendered text for each requested format.
- **Caching**: Before calling Stage 2, checks cache for a `InsightPackage` matching today's article fingerprints. If miss, calls Stage 2 and writes to cache.

---

## 3. Prompt Engineering Strategy

### Guiding principles

1. **Separation of analysis and formatting**: The analysis prompt never mentions output format. The format prompts never analyze content. This is the core architectural insight.
2. **LLM for interpretation, not summarization**: Every prompt is designed to push toward "what does this mean" rather than "what does this say."
3. **Bilingual at the analysis level**: The analysis stage works in a single language (user's choice, default zh). Bilingual rendering is a rendering concern, not an analysis concern.

### Stage 2 prompt (analysis)

```
System: You are a senior AI analyst. Your job is to interpret today's AI news — 
not to summarize individual articles, but to identify what changed and why it matters.

User: Here are today's AI news highlights. Each has a title, source, and AI-generated summary.

[articles]

Please analyze and return a JSON object with these fields:
1. "themes": Group articles into 2-5 themes. For each theme:
   - "name": short theme name
   - "articles": array of article indices
   - "narrative": 2-3 sentences interpreting the combined signal of these articles — what direction do they point in?
   - "tension": if any, note contradictions between articles in this theme
2. "key_signal": One sentence — the single most important takeaway from today's news
3. "cross_theme_connection": If themes relate or conflict, explain in 1-2 sentences

Focus on interpretation. Avoid starting with "Several articles discussed X" — 
instead, say what the articles collectively reveal.
```

### Renderer prompts (Stage 3, example: LinkedIn)

```
System: You write LinkedIn posts about AI that make readers feel smarter, 
not overwhelmed. Short paragraphs. One big idea per post. End with a question.

User: Here is today's AI news analysis:

[key_signal]
[themes with narratives]
[cross_theme_connection]

Write a LinkedIn post based on this analysis. Requirements:
- Hook in the first line
- Cover each theme in 1-2 sentences
- Include the key signal as the core takeaway
- End with a question to invite discussion
- Professional but conversational tone
- 800-1500 characters
```

### Prompt registry integration

All prompts live in `prompts.py` following the existing pattern:

```python
_INSIGHT_ANALYSIS_SYSTEM = {"zh": "…", "en": "…"}
_INSIGHT_ANALYSIS_USER = {"zh": "…", "en": "…"}
_INSIGHT_RENDER_LINKEDIN = {"zh": "…", "en": "…"}
_INSIGHT_RENDER_NEWSLETTER = {"zh": "…", "en": "…"}
_INSIGHT_RENDER_PODCAST = {"zh": "…", "en": "…"}
_INSIGHT_RENDER_BILINGUAL = {"zh": "…", "en": "…"}
```

---

## 4. Intermediate JSON Schemas

### 4.1 InsightPackage (output of Stage 2, input to Stage 3)

```json
{
  "date": "2026-07-07",
  "language": "zh",
  "article_count": 10,

  "themes": [
    {
      "name": "开源模型竞争白热化",
      "articles": [
        {
          "title": "Llama 4 released with 400B context...",
          "link": "https://techcrunch.com/...",
          "source": "TechCrunch",
          "ai_summary": "Meta 发布 Llama 4，支持 400B token 上下文……"
        },
        {
          "title": "Mistral releases...",
          "link": "https://venturebeat.com/...",
          "source": "VentureBeat",
          "ai_summary": "Mistral 推出……"
        }
      ],
      "narrative": "本周开源社区发布了三个新模型……",
      "tension": null
    },
    {
      "name": "AI 监管框架出现分歧",
      "articles": [...],
      "narrative": "美国和欧盟在……",
      "tension": "EU 主张严格监管，而美国倾向于行业自律"
    }
  ],

  "key_signal": "开源模型能力的快速提升正在压缩闭源模型的差异化空间，这可能改变整个 AI 产业的竞争格局。",

  "cross_theme_connection": "监管分歧的加剧与开源模型的爆发相互交织——开源降低了准入门槛，使得监管更难落地。"
}
```

**Design notes**:
- Articles are embedded inline (compact fields: `title`, `link`, `source`, `ai_summary`). The `InsightPackage` is fully self-contained — renderers do not need access to the original article list.
- `tension` is `null` when no contradiction is detected, not an empty string. This lets renderers branch on `is None`.
- The schema trades a few hundred extra tokens of cache size for the convenience of a self-contained intermediate artifact — important for the future publisher module, which will receive only the `InsightPackage` and need nothing else.

### 4.2 Cache key schema

```json
{
  "date": "2026-07-07",
  "article_fingerprints": ["url1", "url2", ...],
  "language": "zh"
}
```

The cache key is a hash of `date + sorted article URLs + language`. This means:
- Same articles on the same day → cache hit (regardless of article text changes from upstream).
- New article appears → cache miss (fingerprints changed).
- Language changes → cache miss (different analysis context).

---

## 5. LLM Call Sequence

```
                    ┌─────────────────────┐
                    │  User request:       │
                    │  "generate LinkedIn  │
                    │   post + newsletter" │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Stage 1: Ingestion  │
                    │ (zero LLM calls)    │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Cache check          │
                    │ (by fingerprint)     │
                    └──────────┬──────────┘
                               │
                    ┌──────────┴──────────┐
                    │                     │
                    ▼                     ▼
            ┌─────────────────┐   ┌──────────────┐
            │ Cache MISS      │   │ Cache HIT    │
            │ Stage 2:        │   │ Skip Stage 2 │
            │ 1 LLM call      │   │              │
            │ (analysis)      │   │              │
            └────────┬────────┘   └──────┬───────┘
                     │                   │
                     └──────┬────────────┘
                            │
                            ▼
                    ┌─────────────────────┐
                    │ InsightPackage ready │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Stage 3: Render     │
                    │ 1 LLM call per      │
                    │ requested format    │
                    │ (parallelizable)    │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Rendered outputs     │
                    │ (N texts for N       │
                    │  formats)           │
                    └─────────────────────┘
```

**Total LLM calls in the worst case**: 1 (analysis) + N (formats).

**Worst-case tokens (example)**:
- Stage 2: ~3000 input (articles) + ~600 output (InsightPackage) ≈ 3600 tokens
- Stage 3 per format: ~400 input (InsightPackage) + ~800 output ≈ 1200 tokens
- 3 formats (LinkedIn + newsletter + bilingual): 1 + 3 = 4 calls, ~7200 tokens total

Compare to single-prompt for 3 formats: 3 × 3000 input = 9000 input tokens + 3 × 800 output = 2400 tokens = 11400 total. The pipeline saves ~37% on tokens even in worst case, and after caching the analysis, refreshes for additional formats are essentially free (~1200 tokens each).

---

## 6. Caching Strategy

### What to cache
The `InsightPackage` (Stage 2 output). This is the expensive artifact.

### Cache backend
**File-based**, consistent with the existing project pattern (`config/today_thought_context.json` style).

### Cache location
```
config/insight_cache/
  ├── {date}.json          # today's InsightPackage
  └── {date}_meta.json     # fingerprint + timestamp
```

### Cache invalidation
- **Automatic**: Cache is keyed by date + article URL fingerprints. If any article URL changes or a new article appears, the fingerprints differ → cache miss.
- **TTL**: 24 hours by file timestamp. On the next day's run, the date component of the key changes, so the previous day's cache is naturally ignored.
- **Manual**: Delete the `config/insight_cache/` directory.

### No cache for Stage 3
Renderer outputs are cheap to generate (~1200 tokens) and format-specific. Caching them would add complexity with minimal benefit.

---

## 7. Error Handling

### Principle
The Insight Engine is a downstream consumer. Its failure must not affect the upstream push pipeline. All errors are caught at the pipeline boundary.

### Per-stage error handling

| Stage | Failure mode | Behavior |
|---|---|---|
| Stage 1 (ingestion) | Empty/malformed input | Return empty result. Pipeline exits early with a clear log message. |
| Stage 2 (analysis) | LLM call fails, JSON parse fails | Retry once after 5s. If still fails, fall back to a degraded `InsightPackage` with a single theme "Uncategorized" containing all articles and a generic key_signal "Unable to generate analysis." |
| Stage 3 (renderer) | LLM call fails for one format | Return error string for that format only. Other formats still render. |

### Logging
Follow the existing `print()` pattern with `[Insight]` prefix:
```
[Insight] Stage 1: ingested 12 articles
[Insight] Stage 2: cache MISS → calling LLM
[Insight] Stage 2: analysis complete (3 themes, 568 tokens)
[Insight] Stage 3: rendering "linkedin" → OK (892 chars)
[Insight] Stage 3: rendering "newsletter" → FAILED (retry exhausted)
```

### Graceful degradation
If the LLM analysis call fails entirely (after retry), the pipeline can still produce a **summary-only** output using a template-based approach: group articles by their existing `category` field, produce a bullet-list. No interpretation, but the pipeline doesn't silently fail.

---

## 8. Cost Estimation

Assumptions:
- DeepSeek pricing: ¥1 per 1M input tokens, ¥2 per 1M output tokens (approximate).
- Average 15 articles per day.

### Per-run cost (worst case, no cache)

| Stage | Input tokens | Output tokens | Cost (CNY) |
|---|---|---|---|
| Stage 2 (analysis) | ~2800 | ~600 | 0.0028 + 0.0012 = 0.0040 |
| Stage 3 (LinkedIn) | ~400 | ~800 | 0.0004 + 0.0016 = 0.0020 |
| Stage 3 (Newsletter) | ~400 | ~1200 | 0.0004 + 0.0024 = 0.0028 |
| Stage 3 (Podcast) | ~400 | ~1000 | 0.0004 + 0.0020 = 0.0024 |
| Stage 3 (Bilingual) | ~400 | ~1500 | 0.0004 + 0.0030 = 0.0034 |

| Scenario | Total tokens | Total cost (CNY) | Per month (30d) |
|---|---|---|---|
| 1 format (LinkedIn only) | ~4200 | ~0.006 | ~0.18 |
| 2 formats (LinkedIn + Newsletter) | ~6200 | ~0.009 | ~0.27 |
| All 4 formats, no cache | ~10200 | ~0.015 | ~0.45 |
| All 4 formats, cache hit (analysis cached) | ~6600 | ~0.011 | ~0.33 |

**If cache hit rate is 70%** (some days the article set changes, some it doesn't): weighted average ≈ ~0.35 CNY/month.

This is negligible compared to the existing pipeline cost. The Insight Engine adds <10% to the total LLM cost.

---

## 9. Future Extensibility

### 9.1 New output format
Add a new file `src/insight_engine/renderers/thread.py` (for Twitter/X threads), implement the function, register it in `RENDERERS`. No changes to analysis logic.

### 9.2 Scheduled auto-post to social media
The pipeline already produces format-specific text. A new module `src/insight_engine/publishers/` can handle API calls:
```
src/insight_engine/publishers/
  ├── __init__.py
  ├── linkedin_api.py      # LinkedIn API client
  ├── twitter_api.py       # Twitter/X API client
  └── substack_api.py      # Newsletter platform
```

The pipeline becomes: analysis → render → publish. Each stage is independently testable.

### 9.3 Multi-language analysis
If the user wants analysis in a different language (not just bilingual rendering), the Stage 2 prompt accepts a `language` parameter. The `InsightPackage.language` field signals to renderers which language the analysis is in, so bilingual renderers can decide whether to translate.

### 9.4 Tone customization
Add a `tone` parameter to the pipeline entry point. Each renderer receives it and includes it in its prompt:
```python
def render_linkedin(package: InsightPackage, tone: str = "professional") -> str:
```

Supported tones: professional, casual, critical, optimistic.

### 9.5 User feedback loop
If a user comments on a rendered output (e.g., "this take is wrong"), the feedback can be stored and injected into the next day's Stage 2 analysis prompt as context, enabling the analysis to learn from prior misses.

### 9.6 Multiple articles-sets-per-day
The cache key includes date + fingerprint. If the upstream bot pushes multiple times per day, the cache naturally invalidates on the second push (different fingerprint). Add a `session_id` field to the cache key to handle this explicitly if needed.

---

## 10. File Layout Summary

```
src/
  insight_engine/
    __init__.py          # run_insight_pipeline() entry point
    pipeline.py          # orchestrator: cache check → Stage 1 → 2 → 3
    ingestion.py         # Stage 1: validate, dedup, light classification
    analysis.py          # Stage 2: LLM-based analysis → InsightPackage
    cache.py             # file-based cache logic
    schemas.py           # InsightPackage dataclass or TypedDict
    renderers/
      __init__.py        # RENDERERS registry
      linkedin.py        # LinkedIn post renderer
      newsletter.py      # Newsletter renderer
      podcast_script.py  # Podcast script renderer
      bilingual.py       # Bilingual output renderer

config/
  insight_cache/         # cached InsightPackage files (auto-managed)
```

**Integration with existing code — independent workflow (Option B chosen)**

The Insight Engine runs as a **separate GitHub Actions workflow**, triggered by `workflow_run` after `daily_push.yml` completes. The data interface is the existing `config/today_thought_context.json` file — specifically its `all_articles` field, which the upstream pipeline already writes after every push:

```json
// config/today_thought_context.json (existing, written by daily_push.py)
{
  "date": "2026-07-07",
  "all_articles": [
    {"title": "...", "source": "...", "link": "...", "ai_summary": "..."},
    ...
  ],
  ...
}
```

This means:
- **No coupling** — Insight Engine reads a file, never imports from `daily_push.py`.
- **Independent retry** — can be re-run without re-pushing to Discord.
- **Independent failure** — if Insight Engine breaks, the daily push is unaffected.
- **Interface contract** — `all_articles` (list of `{title, source, link, ai_summary}`) is the formal handoff from upstream to downstream.

The new workflow file `.github/workflows/insight_engine.yml` will:
1. Trigger on `workflow_run` event for `daily_push.yml` (and `discord_handler_main.yml` as fallback).
2. Read `config/today_thought_context.json` from the repo.
3. Run `python scripts/insight_engine_run.py` which calls `run_insight_pipeline(...)`.
4. Write rendered outputs to `output/insight/{date}/{format}.md`.
5. Optionally post results to a Discord channel (future: social media APIs).

---

## 11. Data Flow Diagram (Detailed)

```
daily_push.yml (existing)                    insight_engine.yml (new, separate workflow)
┌──────────────────────┐        ┌─────────────────────────────────────────────┐
│                      │        │                                             │
│  fetch → AI select   │        │  Read config/today_thought_context.json    │
│  → push to Discord   │        │  (all_articles field is the interface)      │
│  → write thought_    │──┐     │                                             │
│     context.json     │  │     │  ingestion.py                               │
│                      │  │     │    │                                        │
└──────────────────────┘  │     │    ▼                                        │
                          │     │  validated articles                         │
                          │     │    │                                        │
                          └────▶│    ▼                                        │
                                │  analysis.py ←── cache check                │
                                │    │              (file-based)              │
                                │    ▼                                        │
                                │  InsightPackage (self-contained)            │
                                │  - themes[].articles[] embedded inline      │
                                │  - no external article list needed          │
                                │  (JSON, on disk)                            │
                                │    │                                        │
                                │    ├──────────┬──────────┬──────────┐       │
                                │    ▼          ▼          ▼          ▼       │
                                │  linkedin  newsletter  podcast   bilingual  │
                                │  .py       .py        .py       .py        │
                                │    │          │          │          │       │
                                │    ▼          ▼          ▼          ▼       │
                                │  "text"    "text"     "text"     "text"     │
                                └─────────────────────────────────────────────┘
                                              │
                                              │ output saved to files / posted
                                              ▼
                                    output/insight/{date}/{format}.md
                                    (future: social media API)
```

**Decoupling boundary**: the only thing upstream writes that downstream reads is `config/today_thought_context.json`'s `all_articles` field. No module imports cross the boundary. Either side can be modified, swapped, or rerun independently.

---

## 12. Implementation Order

1. **`src/insight_engine/schemas.py`** — Define `InsightPackage` as a `TypedDict` or dataclass. This sets the contract.
2. **`src/insight_engine/ingestion.py`** — Article cleaning and dedup. Simple, testable, no LLM.
3. **`src/insight_engine/cache.py`** — File-based cache with fingerprinting.
4. **`src/insight_engine/analysis.py`** — Single LLM call with the interpretation prompt.
5. **`src/insight_engine/renderers/`** — One file per format, implement in priority order: LinkedIn → bilingual → newsletter → podcast_script.
6. **`src/insight_engine/pipeline.py`** — Orchestrator tying everything together.
7. **`src/insight_engine/__init__.py`** — Public API.
8. **Integration** — One optional step in `daily_push.py`.
9. **Prompts** — Add all prompts to `src/prompts.py` at any point.

Steps 1–3 have no LLM dependency and can be built and tested first.