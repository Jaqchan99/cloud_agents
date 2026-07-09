"""
Insight Engine 数据类型定义。
所有模块通过这里定义的类型进行通信，不直接传递原始 dict。
"""

from typing import TypedDict, Optional


class ArticleBrief(TypedDict):
    """上游 article 的精简表示，仅保留下游渲染器需要的字段"""
    title: str
    link: str
    source: str
    ai_summary: str


class Theme(TypedDict):
    """一个主题聚类：文章内联 + 叙述 + 矛盾点"""
    name: str
    articles: list[ArticleBrief]
    narrative: str
    tension: Optional[str]  # null 表示无矛盾，str 表示矛盾说明


class InsightPackage(TypedDict):
    """分析阶段产出的自包含数据包，是缓存单元和渲染器输入。

    设计原则：
    - 完全自包含：渲染器不需要访问原始 article list
    - 紧凑但完整：themes 内嵌精简文章字段而非索引引用
    - 可串行化：纯 JSON 结构，可直接缓存到文件
    """
    date: str
    language: str
    article_count: int
    themes: list[Theme]
    key_signal: str
    cross_theme_connection: str