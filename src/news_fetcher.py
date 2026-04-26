"""
信息采集模块 - 从多个 RSS 源和 API 抓取 AI 相关资讯
"""
import feedparser
import requests
import json
import time
from datetime import datetime, timedelta, timezone
from typing import Optional


FEED_SOURCES = [
    # 高频更新源（每日发文）
    {
        "name": "TechCrunch AI",
        "url": "https://techcrunch.com/category/artificial-intelligence/feed/",
        "category": "行业新闻",
    },
    {
        "name": "VentureBeat AI",
        "url": "https://venturebeat.com/category/ai/feed/",
        "category": "行业新闻",
    },
    {
        "name": "The Verge AI",
        "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
        "category": "行业新闻",
    },
    {
        "name": "Ars Technica",
        "url": "https://feeds.arstechnica.com/arstechnica/technology-lab",
        "category": "行业新闻",
    },
    {
        "name": "MIT Technology Review AI",
        "url": "https://www.technologyreview.com/feed/",
        "category": "行业新闻",
    },
    # 官方博客（低频但权威）
    {
        "name": "HuggingFace Blog",
        "url": "https://huggingface.co/blog/feed.xml",
        "category": "技术博客",
    },
    {
        "name": "OpenAI Blog",
        "url": "https://openai.com/blog/rss.xml",
        "category": "行业动态",
    },
    {
        "name": "Google AI Blog",
        "url": "https://blog.research.google/feeds/posts/default?alt=rss",
        "category": "行业动态",
    },
    # 学术论文（工作日更新）
    {
        "name": "Arxiv AI",
        "url": "https://rss.arxiv.org/rss/cs.AI",
        "category": "论文",
    },
    {
        "name": "Arxiv ML",
        "url": "https://rss.arxiv.org/rss/cs.LG",
        "category": "论文",
    },
]

HACKER_NEWS_API = "https://hacker-news.firebaseio.com/v0"


def fetch_rss_feed(source: dict, hours_back: int = 24) -> list[dict]:
    """抓取单个 RSS 源的文章，只返回指定小时内的内容"""
    articles = []
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)

    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; AINewsBot/1.0)"}
        resp = requests.get(source["url"], headers=headers, timeout=15)
        feed = feedparser.parse(resp.content)

        for entry in feed.entries[:20]:
            pub_date = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                pub_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                pub_date = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)

            # 没有时间信息的条目也纳入（容错）
            if pub_date and pub_date < cutoff_time:
                continue

            title = entry.get("title", "").strip()
            link = entry.get("link", "").strip()
            summary = ""
            if hasattr(entry, "summary"):
                summary = entry.summary[:500]
            elif hasattr(entry, "description"):
                summary = entry.description[:500]

            if title and link:
                articles.append(
                    {
                        "title": title,
                        "link": link,
                        "summary": summary,
                        "source": source["name"],
                        "category": source["category"],
                        "pub_date": pub_date.isoformat() if pub_date else "",
                    }
                )
    except Exception as e:
        print(f"[RSS] 抓取 {source['name']} 失败: {e}")

    return articles


def fetch_hacker_news_ai(top_n: int = 10) -> list[dict]:
    """抓取 Hacker News 上的 AI 相关热门讨论"""
    articles = []
    ai_keywords = [
        "llm", "gpt", "claude", "gemini", "ai ", "artificial intelligence",
        "machine learning", "deep learning", "neural", "openai", "anthropic",
        "mistral", "llama", "transformer", "diffusion", "stable diffusion",
        "midjourney", "sora", "deepseek", "agent",
    ]

    try:
        resp = requests.get(f"{HACKER_NEWS_API}/topstories.json", timeout=10)
        story_ids = resp.json()[:100]

        count = 0
        for story_id in story_ids:
            if count >= top_n:
                break
            try:
                story_resp = requests.get(
                    f"{HACKER_NEWS_API}/item/{story_id}.json", timeout=5
                )
                story = story_resp.json()
                if not story or story.get("type") != "story":
                    continue

                title = story.get("title", "").lower()
                url = story.get("url", "")

                if any(kw in title for kw in ai_keywords):
                    articles.append(
                        {
                            "title": story.get("title", ""),
                            "link": url or f"https://news.ycombinator.com/item?id={story_id}",
                            "summary": f"HN 评论数: {story.get('descendants', 0)}，得分: {story.get('score', 0)}",
                            "source": "Hacker News",
                            "category": "社区讨论",
                            "pub_date": datetime.fromtimestamp(
                                story.get("time", 0), tz=timezone.utc
                            ).isoformat(),
                        }
                    )
                    count += 1
                time.sleep(0.1)
            except Exception:
                continue
    except Exception as e:
        print(f"[HN] 抓取失败: {e}")

    return articles


def filter_by_keywords(
    articles: list[dict], include_keywords: list[str], exclude_keywords: list[str]
) -> list[dict]:
    """根据用户配置的关键词过滤文章"""
    if not include_keywords and not exclude_keywords:
        return articles

    filtered = []
    for article in articles:
        text = (article["title"] + " " + article["summary"]).lower()

        if exclude_keywords and any(kw.lower() in text for kw in exclude_keywords):
            continue

        if include_keywords:
            if any(kw.lower() in text for kw in include_keywords):
                filtered.append(article)
        else:
            filtered.append(article)

    return filtered


def fetch_all_news(config: dict) -> list[dict]:
    """
    汇总抓取所有来源的新闻

    Args:
        config: 用户配置，包含 include_keywords, exclude_keywords, hours_back 等字段
    """
    hours_back = config.get("hours_back", 72)  # 默认 72 小时，覆盖周末不更新的情况
    include_keywords = config.get("include_keywords", [])
    exclude_keywords = config.get("exclude_keywords", [])
    enabled_sources = config.get("enabled_sources", [s["name"] for s in FEED_SOURCES])

    all_articles: list[dict] = []

    for source in FEED_SOURCES:
        if source["name"] not in enabled_sources:
            continue
        articles = fetch_rss_feed(source, hours_back=hours_back)
        all_articles.extend(articles)
        time.sleep(0.5)

    if config.get("include_hacker_news", True):
        hn_articles = fetch_hacker_news_ai(top_n=10)
        all_articles.extend(hn_articles)

    all_articles = filter_by_keywords(all_articles, include_keywords, exclude_keywords)

    # 按时间倒序排列，没有时间的排后面
    all_articles.sort(key=lambda x: x.get("pub_date", ""), reverse=True)

    print(f"[Fetcher] 共抓取 {len(all_articles)} 条文章")
    return all_articles


if __name__ == "__main__":
    sample_config = {
        "hours_back": 24,
        "include_keywords": [],
        "exclude_keywords": [],
        "include_hacker_news": True,
    }
    articles = fetch_all_news(sample_config)
    for a in articles[:5]:
        print(f"[{a['source']}] {a['title']}")
        print(f"  {a['link']}")
        print()
