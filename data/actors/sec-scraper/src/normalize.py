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


def build_event_id(source: str, url: str) -> str:
    h = hashlib.sha256(f"{source}:{url}".encode()).hexdigest()[:12]
    return f"evt_{source}_{h}"


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
    return str(val)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
