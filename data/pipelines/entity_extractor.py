import re
from typing import NamedTuple

KNOWN_COMPANIES: dict[str, str] = {
    "NVDA": "NVIDIA",
    "AMD": "Advanced Micro Devices",
    "AAPL": "Apple",
    "MSFT": "Microsoft",
    "GOOGL": "Alphabet (Google)",
    "GOOG": "Alphabet (Google)",
    "AMZN": "Amazon",
    "META": "Meta Platforms",
    "TSLA": "Tesla",
    "JPM": "JPMorgan Chase",
    "GS": "Goldman Sachs",
    "SPY": "SPDR S&P 500 ETF",
    "QQQ": "Invesco QQQ Trust",
    "PLTR": "Palantir Technologies",
    "AVGO": "Broadcom",
    "TSM": "Taiwan Semiconductor",
    "ARM": "ARM Holdings",
    "NFLX": "Netflix",
    "DIS": "Walt Disney",
    "BA": "Boeing",
    "COIN": "Coinbase",
    "HOOD": "Robinhood Markets",
    "MSTR": "MicroStrategy",
    "BTC": "Bitcoin",
    "ETH": "Ethereum",
    "SOL": "Solana",
}

TICKER_PATTERN = re.compile(r'\b[A-Z]{1,5}\b')


class ExtractedEntity(NamedTuple):
    name: str
    entity_type: str
    ticker: str


def extract_tickers(text: str) -> list[str]:
    if not text:
        return []
    words = TICKER_PATTERN.findall(text)
    seen: set[str] = set()
    result: list[str] = []
    for w in words:
        if w in KNOWN_COMPANIES and w not in seen:
            seen.add(w)
            result.append(w)
    return result


def extract_entities(text: str) -> list[dict]:
    tickers = extract_tickers(text)
    entities: list[dict] = []
    seen_tickers: set[str] = set()
    for t in tickers:
        if t not in seen_tickers:
            seen_tickers.add(t)
            entities.append({
                "name": KNOWN_COMPANIES.get(t, t),
                "type": "company",
                "ticker": t,
            })
    return entities
