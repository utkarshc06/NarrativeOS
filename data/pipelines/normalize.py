import hashlib
from datetime import datetime, timezone
from typing import Any

from data.pipelines.entity_extractor import extract_entities, extract_tickers


def build_event_id(source: str, url: str) -> str:
    raw = f"{source}:{url}"
    h = hashlib.sha256(raw.encode()).hexdigest()[:12]
    return f"evt_{source}_{h}"


def normalize_reddit_post(post: dict[str, Any]) -> dict[str, Any]:
    text = f"{post.get('title', '')} {post.get('selftext', '')}"
    return {
        "id": build_event_id("reddit", post.get("url", post.get("permalink", ""))),
        "source": "reddit",
        "source_actor": "narrativeos-reddit-scraper",
        "title": post.get("title", ""),
        "body": post.get("selftext", ""),
        "url": post.get("url", post.get("permalink", "")),
        "author": post.get("author", ""),
        "published_at": _to_iso(post.get("created_utc")),
        "collected_at": _now_iso(),
        "ticker_mentions": extract_tickers(text),
        "entities": extract_entities(text),
        "sentiment_score": None,
        "metadata": {
            "upvotes": post.get("ups", 0) or post.get("score", 0),
            "comments": post.get("num_comments", 0),
            "subreddit": post.get("subreddit", ""),
            "post_type": _detect_post_type(post.get("link_flair_text", "")),
        },
    }


def normalize_article(article: dict[str, Any]) -> dict[str, Any]:
    text = f"{article.get('title', '')} {article.get('body', '')} {article.get('summary', '')}"
    return {
        "id": build_event_id("news", article.get("url", article.get("link", ""))),
        "source": "news",
        "source_actor": "narrativeos-news-scraper",
        "title": article.get("title", ""),
        "body": article.get("body", article.get("summary", "")),
        "url": article.get("url", article.get("link", "")),
        "author": article.get("author", ""),
        "published_at": _to_iso(article.get("published_parsed") or article.get("published")),
        "collected_at": _now_iso(),
        "ticker_mentions": extract_tickers(text),
        "entities": extract_entities(text),
        "sentiment_score": None,
        "metadata": {
            "source_domain": _extract_domain(article.get("url", article.get("link", ""))),
            "word_count": len(article.get("body", "").split()),
        },
    }


def normalize_sec_filing(filing: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": build_event_id("sec_filing", filing.get("url", "")),
        "source": "sec_filing",
        "source_actor": "narrativeos-sec-scraper",
        "title": f"{filing.get('company_name', 'Unknown')} — {filing.get('form_type', '')}",
        "body": filing.get("description", ""),
        "url": filing.get("url", ""),
        "author": filing.get("company_name", ""),
        "published_at": _to_iso(filing.get("filing_date")),
        "collected_at": _now_iso(),
        "ticker_mentions": list(filing.get("tickers", [])),
        "entities": [{"name": filing.get("company_name", ""), "type": "company", "ticker": t} for t in filing.get("tickers", [])],
        "sentiment_score": None,
        "metadata": {
            "form_type": filing.get("form_type", ""),
            "cik": filing.get("cik", ""),
            "filing_period": filing.get("period", ""),
        },
    }


def _to_iso(val: Any) -> str:
    if val is None:
        return _now_iso()
    if isinstance(val, (int, float)):
        return datetime.fromtimestamp(val, tz=timezone.utc).isoformat()
    if isinstance(val, str):
        return val
    return _now_iso()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _extract_domain(url: str) -> str:
    try:
        from urllib.parse import urlparse
        return urlparse(url).netloc
    except Exception:
        return ""


def _detect_post_type(flair: str) -> str:
    flair_lower = flair.lower()
    if "dd" in flair_lower or "due diligence" in flair_lower:
        return "DD"
    if "gain" in flair_lower:
        return "GAIN"
    if "loss" in flair_lower:
        return "LOSS"
    if "discussion" in flair_lower or "question" in flair_lower:
        return "DISCUSSION"
    if "meme" in flair_lower:
        return "MEME"
    return "GENERAL"
