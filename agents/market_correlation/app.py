"""Agent 4: Market Correlation Agent — maps narratives to assets, sectors, and macro relationships."""

import re

from fastapi import FastAPI

from agents.schemas import CorrelationResult, MarketCorrelationOutput, NarrativeEvent

app = FastAPI(title="Market Correlation Agent", version="0.1.0")

SECTOR_MAP: dict[str, str] = {
    "NVDA": "Technology", "AMD": "Technology", "AAPL": "Technology",
    "MSFT": "Technology", "GOOGL": "Technology", "AMZN": "Technology",
    "META": "Technology", "TSLA": "Automotive", "JPM": "Financials",
    "GS": "Financials", "SPY": "ETF", "QQQ": "ETF",
    "PLTR": "Technology", "AVGO": "Technology", "TSM": "Technology",
    "ARM": "Technology",
}

SECTOR_KEYWORDS: dict[str, list[str]] = {
    "Technology": ["semiconductor", "chip", "ai", "data center", "software", "cloud", "cyber"],
    "Financials": ["bank", "rate", "yield", "fed", "treasury", "credit", "loan"],
    "Automotive": ["ev", "auto", "car", "battery", "manufacturing", "supply chain"],
    "Energy": ["oil", "gas", "renewable", "solar", "wind", "crude"],
    "Healthcare": ["pharma", "biotech", "fda", "clinical", "drug", "trial"],
    "Consumer": ["retail", "consumer", "e-commerce", "spending", "demand"],
}


def extract_sectors(ticker_mentions: list[str]) -> list[str]:
    sectors = set()
    for t in ticker_mentions:
        if t in SECTOR_MAP:
            sectors.add(SECTOR_MAP[t])
    return list(sectors)


def score_sector_relevance(body: str, sectors: list[str]) -> float:
    body_lower = body.lower()
    matches = 0
    total = 0
    for sector in sectors:
        keywords = SECTOR_KEYWORDS.get(sector, [])
        for kw in keywords:
            total += 1
            if kw in body_lower:
                matches += 1
    return round(matches / max(total, 1), 4)


def estimate_impact_direction(body: str) -> str:
    positive = r"\b(bullish|upside|growth|surge|beat|positive|outperform|profit|breakthrough|surge)\b"
    negative = r"\b(bearish|downside|decline|miss|negative|underperform|loss|deficit|risk|crash)\b"
    body_lower = body.lower()
    pos_count = len(re.findall(positive, body_lower))
    neg_count = len(re.findall(negative, body_lower))
    if pos_count > neg_count:
        return "positive"
    if neg_count > pos_count:
        return "negative"
    return "neutral"


@app.get("/health")
def health():
    return {"status": "ok", "agent": "market-correlation", "version": "0.1.0"}


@app.post("/correlate", response_model=MarketCorrelationOutput)
def correlate(payload: dict):
    events_data = payload.get("events", [])
    events = [NarrativeEvent(**e) if isinstance(e, dict) else e for e in events_data]

    correlations: list[CorrelationResult] = []
    cross_market_impacts: list[dict] = []
    macro_relationships: list[dict] = []

    for event in events:
        sectors = extract_sectors(event.ticker_mentions)
        relevance = score_sector_relevance(event.body, sectors)
        direction = estimate_impact_direction(event.body)

        for ticker in event.ticker_mentions:
            sector = SECTOR_MAP.get(ticker, "Unknown")
            correlations.append(CorrelationResult(
                ticker=ticker,
                sector=sector,
                correlation_score=relevance,
                impact_direction=direction,
                reasoning=f"Narrative '{event.title[:60]}' has {direction} implications for {ticker} ({sector})",
            ))

        for sector in sectors:
            cross_market_impacts.append({
                "source_tickers": event.ticker_mentions,
                "affected_sector": sector,
                "propagation_score": relevance,
                "direction": direction,
                "trigger": event.title[:80],
            })

    macro_relationships.append({
        "narrative_theme": events[0].title[:60] if events else "unknown",
        "involved_sectors": list(set(c.sector for c in correlations)),
        "cross_sector_propagation": len(cross_market_impacts),
        "average_correlation": round(
            sum(c.correlation_score for c in correlations) / max(len(correlations), 1), 4
        ),
    })

    return MarketCorrelationOutput(
        correlations=correlations,
        cross_market_impacts=cross_market_impacts,
        macro_relationships=macro_relationships,
    )
