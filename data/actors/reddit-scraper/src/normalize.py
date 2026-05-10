import hashlib
import re
from datetime import datetime, timezone
from typing import Any

KNOWN_COMPANIES: dict[str, str] = {
    "NVDA": "NVIDIA", "AMD": "Advanced Micro Devices", "AAPL": "Apple",
    "MSFT": "Microsoft", "GOOGL": "Alphabet (Google)", "GOOG": "Alphabet (Google)",
    "AMZN": "Amazon", "META": "Meta Platforms", "TSLA": "Tesla",
    "JPM": "JPMorgan Chase", "GS": "Goldman Sachs", "SPY": "SPDR S&P 500 ETF",
    "QQQ": "Invesco QQQ Trust", "PLTR": "Palantir Technologies", "AVGO": "Broadcom",
    "TSM": "Taiwan Semiconductor", "ARM": "ARM Holdings", "NFLX": "Netflix",
    "DIS": "Walt Disney", "BA": "Boeing", "COIN": "Coinbase",
    "HOOD": "Robinhood Markets", "MSTR": "MicroStrategy",
}

TICKER_PATTERN = re.compile(r'\b[A-Z]{1,5}\b')


def extract_tickers(text: str) -> list[str]:
    if not text:
        return []
    words = TICKER_PATTERN.findall(text)
    seen: set[str] = set()
    return [w for w in words if w in KNOWN_COMPANIES and not (w in seen or seen.add(w))]


def extract_entities(text: str) -> list[dict]:
    return [
        {"name": KNOWN_COMPANIES.get(t, t), "type": "company", "ticker": t}
        for t in dict.fromkeys(extract_tickers(text))
    ]


def build_event_id(source: str, url: str) -> str:
    h = hashlib.sha256(f"{source}:{url}".encode()).hexdigest()[:12]
    return f"evt_{source}_{h}"


def normalize_reddit_post(post: dict[str, Any]) -> dict[str, Any]:
    text = f"{post.get('title', '')} {post.get('selftext', '')}"
    flair = (post.get("link_flair_text") or "").lower()
    post_type = "DD" if "dd" in flair else "GAIN" if "gain" in flair else "LOSS" if "loss" in flair else "GENERAL"
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
            "post_type": post_type,
        },
    }


def _to_iso(val: Any) -> str:
    if val is None:
        return _now_iso()
    if isinstance(val, (int, float)):
        return datetime.fromtimestamp(val, tz=timezone.utc).isoformat()
    return str(val)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
