"""
File-based cache for InsightPackage.

缓存键 = hash(date + sorted(article links) + language)
缓存位置：config/insight_cache/{date}.json
TTL：24 小时（按文件 mtime）；日期变更自然失效。
"""

import hashlib
import json
import time
from pathlib import Path
from typing import Optional


DEFAULT_CACHE_DIR = Path(__file__).parent.parent.parent / "config" / "insight_cache"
DEFAULT_TTL_SECONDS = 24 * 3600  # 24 小时


def _fingerprint(date: str, links: list[str], language: str) -> str:
    """生成缓存指纹：date + sorted(links) + language 的 sha256 前 16 字符"""
    parts = [date, language] + sorted(links)
    raw = "|".join(parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _cache_path(date: str, cache_dir: Path = DEFAULT_CACHE_DIR) -> Path:
    return cache_dir / f"{date}.json"


def _meta_path(date: str, cache_dir: Path = DEFAULT_CACHE_DIR) -> Path:
    return cache_dir / f"{date}_meta.json"


def get_cache(
    date: str,
    links: list[str],
    language: str,
    cache_dir: Path = DEFAULT_CACHE_DIR,
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
) -> Optional[dict]:
    """读取缓存。命中返回 InsightPackage dict，未命中返回 None。"""
    pkg_path = _cache_path(date, cache_dir)
    meta_path = _meta_path(date, cache_dir)

    if not pkg_path.exists() or not meta_path.exists():
        return None

    # TTL 检查
    age = time.time() - meta_path.stat().st_mtime
    if age > ttl_seconds:
        print(f"[Insight] Cache: {date} 缓存已过期（{int(age/3600)}h）")
        return None

    # 指纹校验
    expected_fp = _fingerprint(date, links, language)
    try:
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
    except (json.JSONDecodeError, OSError):
        return None

    if meta.get("fingerprint") != expected_fp:
        print(f"[Insight] Cache: {date} 指纹不匹配（文章集变化）")
        return None

    # 读取 InsightPackage
    try:
        with open(pkg_path, "r", encoding="utf-8") as f:
            package = json.load(f)
        print(f"[Insight] Cache: {date} 命中 ✅")
        return package
    except (json.JSONDecodeError, OSError) as e:
        print(f"[Insight] Cache: 读取失败 {e}")
        return None


def set_cache(
    date: str,
    links: list[str],
    language: str,
    package: dict,
    cache_dir: Path = DEFAULT_CACHE_DIR,
) -> None:
    """写入 InsightPackage 和元数据。"""
    cache_dir.mkdir(parents=True, exist_ok=True)

    pkg_path = _cache_path(date, cache_dir)
    meta_path = _meta_path(date, cache_dir)

    # 写 InsightPackage
    with open(pkg_path, "w", encoding="utf-8") as f:
        json.dump(package, f, ensure_ascii=False, indent=2)

    # 写元数据
    meta = {
        "date": date,
        "language": language,
        "fingerprint": _fingerprint(date, links, language),
        "article_count": len(links),
        "created_at": time.time(),
    }
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"[Insight] Cache: {date} 已写入（指纹 {meta['fingerprint'][:8]}...）")


def clear_cache(date: Optional[str] = None, cache_dir: Path = DEFAULT_CACHE_DIR) -> int:
    """清理缓存。不传 date 则清空整个目录。返回删除的文件数。"""
    if not cache_dir.exists():
        return 0

    removed = 0
    if date:
        for p in [_cache_path(date, cache_dir), _meta_path(date, cache_dir)]:
            if p.exists():
                p.unlink()
                removed += 1
    else:
        for p in cache_dir.iterdir():
            if p.is_file():
                p.unlink()
                removed += 1

    print(f"[Insight] Cache: 清理了 {removed} 个文件")
    return removed