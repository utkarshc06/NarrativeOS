"""Agent 6: Risk Intelligence Agent — evaluates systemic uncertainty and signal reliability."""

import re

from fastapi import FastAPI

app = FastAPI(title="Risk Intelligence Agent", version="0.1.0")

RISK_KEYWORDS: dict[str, float] = {
    "regulation": 0.6, "investigation": 0.7, "lawsuit": 0.8,
    "fraud": 0.9, "sanctions": 0.7, "tariff": 0.5,
    "recession": 0.6, "inflation": 0.4, "default": 0.8,
    "volatility": 0.4, "uncertainty": 0.3, "bankruptcy": 0.9,
    "downgrade": 0.6, "sell-off": 0.5, "crash": 0.8,
}

ANOMALY_PATTERNS: list[dict] = [
    {"pattern": r"\b(breakout|moon|rocket|to the moon|pump)\b", "label": "hype_detected", "severity": 0.3},
    {"pattern": r"\b(FUD|panic|dumping|crash|bloodbath)\b", "label": "fear_detected", "severity": 0.4},
    {"pattern": r"\b(guaranteed|risk-free|sure thing|no downside)\b", "label": "misleading_confidence", "severity": 0.6},
    {"pattern": r"\b(insider|SEC|subpoena|investigation)\b", "label": "regulatory_risk", "severity": 0.7},
]


def compute_risk_score(debate_result: dict, narrative: dict, sentiment: dict) -> float:
    score = 0.3

    debate_text = str(debate_result.get("arbiter_ruling", "")) + str(debate_result.get("bull_case", "")) + str(debate_result.get("bear_case", ""))
    narrative_text = str(narrative.get("summary", "")) + str(narrative.get("momentum_score", ""))
    sentiment_text = str(sentiment.get("intensity", "")) + str(sentiment.get("instability_score", ""))
    combined = debate_text + " " + narrative_text + " " + sentiment_text

    keyword_score = 0.0
    for word, weight in RISK_KEYWORDS.items():
        if word in combined.lower():
            keyword_score += weight
    keyword_score = min(keyword_score / 3.0, 0.8)

    instability = float(sentiment.get("instability_score", 0) or 0)
    intensity = float(sentiment.get("intensity", 0) or 0)
    sentiment_factor = (instability * 0.5) + (intensity * 0.2)

    score = min(0.3 + keyword_score * 0.5 + sentiment_factor, 0.95)
    return round(score, 4)


def extract_risk_factors(combined: str) -> list[str]:
    factors = []
    for word, _ in RISK_KEYWORDS.items():
        if word in combined.lower():
            factors.append(word.capitalize())
    return factors[:5]


def detect_anomalies(combined: str) -> list[dict]:
    flags = []
    for ap in ANOMALY_PATTERNS:
        if re.search(ap["pattern"], combined, re.IGNORECASE):
            flags.append({
                "type": ap["label"],
                "severity": ap["severity"],
                "details": f"Pattern matched in narrative content: {ap['label']}",
            })
    return flags


def compute_confidence_degradation(risk_score: float, anomaly_count: int) -> float:
    degradation = (risk_score * 0.6) + (min(anomaly_count, 5) * 0.08)
    return round(min(degradation, 0.9), 4)


def estimate_volatility(sentiment: dict) -> float:
    intensity = float(sentiment.get("intensity", 0) or 0)
    instability = float(sentiment.get("instability_score", 0) or 0)
    polarity = abs(float(sentiment.get("polarity", 0) or 0))
    return round(min((intensity * 0.4) + (instability * 0.4) + (polarity * 0.2), 1.0), 4)


@app.get("/health")
def health():
    return {"status": "ok", "agent": "risk-intelligence", "version": "0.1.0"}


@app.post("/assess")
def assess(payload: dict):
    debate_result = payload.get("debate_result", {})
    narrative = payload.get("narrative", {})
    sentiment = payload.get("sentiment", {})

    combined = str(debate_result) + " " + str(narrative) + " " + str(sentiment)

    risk_score = compute_risk_score(debate_result, narrative, sentiment)
    risk_factors = extract_risk_factors(combined)
    anomaly_flags = detect_anomalies(combined)
    confidence_degradation = compute_confidence_degradation(risk_score, len(anomaly_flags))
    volatility_forecast = estimate_volatility(sentiment)

    return {
        "risk_score": risk_score,
        "risk_factors": risk_factors,
        "anomaly_flags": anomaly_flags,
        "volatility_forecast": volatility_forecast,
        "confidence_degradation": confidence_degradation,
    }
