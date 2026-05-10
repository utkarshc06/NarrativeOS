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


def _extract_domain(url: str) -> str:
    try:
        from urllib.parse import urlparse
        return urlparse(url).netloc
    except Exception:
        return ""


def _to_iso(val: Any) -> str:
    if val is None:
        return _now_iso()
    if isinstance(val, (int, float)):
        return datetime.fromtimestamp(val, tz=timezone.utc).isoformat()
    if hasattr(val, 'tm_year'):
        return datetime(val.tm_year, val.tm_mon, val.tm_mday,
                        val.tm_hour, val.tm_min, val.tm_sec, tzinfo=timezone.utc).isoformat()
    return str(val)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
