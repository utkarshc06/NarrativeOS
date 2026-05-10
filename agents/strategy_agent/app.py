"""Agent 7: Strategy Agent — generates adaptive trading signals from validated narratives."""

from fastapi import FastAPI

app = FastAPI(title="Strategy Agent", version="0.1.0")


def determine_direction(risk_score: float, debate: dict) -> str:
    arbiter = str(debate.get("arbiter_ruling", "")).lower()

    if risk_score > 0.7:
        return "HOLD"

    if "bull" in arbiter and risk_score < 0.5:
        return "BUY"
    if "bear" in arbiter and risk_score < 0.5:
        return "SELL"

    bull_strength = len(str(debate.get("bull_case", "")))
    bear_strength = len(str(debate.get("bear_case", "")))

    if bull_strength > bear_strength * 1.3 and risk_score < 0.5:
        return "BUY"
    if bear_strength > bull_strength * 1.3 and risk_score < 0.5:
        return "SELL"
    if risk_score > 0.5:
        return "WATCHLIST"

    return "HOLD"


def compute_confidence(direction: str, risk_score: float, debate: dict) -> float:
    base = 0.5
    arbiter = str(debate.get("arbiter_ruling", "")).lower()

    if "bull" in arbiter and direction == "BUY":
        base += 0.2
    elif "bear" in arbiter and direction == "SELL":
        base += 0.2
    elif "uncertain" in arbiter or "ambiguous" in arbiter:
        base -= 0.15

    risk_penalty = risk_score * 0.3
    debate_rounds = int(debate.get("debate_rounds", 1))
    debate_bonus = min(debate_rounds * 0.03, 0.12)

    confidence = base - risk_penalty + debate_bonus
    return round(max(min(confidence, 0.95), 0.1), 4)


def build_reasoning_trace(direction: str, confidence: float, risk_score: float, debate: dict) -> list[str]:
    trace = []
    trace.append(f"Strategy Agent: Direction determined as {direction}")
    trace.append(f"Strategy Agent: Confidence score {confidence:.2f} based on risk ({risk_score:.2f}) and debate quality")
    trace.append(f"Bull Case: {debate.get('bull_case', 'N/A')[:80]}")
    trace.append(f"Bear Case: {debate.get('bear_case', 'N/A')[:80]}")
    trace.append(f"Arbiter Ruling: {debate.get('arbiter_ruling', 'N/A')[:80]}")
    trace.append(f"Risk-adjusted confidence: {confidence:.4f}")
    return trace


def compute_position_size(direction: str, confidence: float, risk_score: float) -> tuple[float, float]:
    if direction in ("HOLD", "WATCHLIST"):
        return 0.0, 0.0

    max_allocation = 0.25
    risk_cap = 1.0 - risk_score
    allocation = round(max_allocation * confidence * risk_cap, 4)
    allocation = min(allocation, max_allocation)
    return round(allocation * 100, 2), round(allocation * 1_000_000_000, 2)


@app.get("/health")
def health():
    return {"status": "ok", "agent": "strategy", "version": "0.1.0"}


@app.post("/formulate")
def formulate(payload: dict):
    risk_assessment = payload.get("risk_assessment", {})
    debate = payload.get("debate", {})

    risk_score = float(risk_assessment.get("risk_score", 0.5))
    ticker = debate.get("ticker") or risk_assessment.get("ticker") or "UNKNOWN"

    direction = determine_direction(risk_score, debate)
    confidence = compute_confidence(direction, risk_score, debate)
    reasoning_trace = build_reasoning_trace(direction, confidence, risk_score, debate)
    allocation_pct, position_size = compute_position_size(direction, confidence, risk_score)

    if "reasoning_trace" not in [x.lower() for x in reasoning_trace]:
        reasoning_trace.insert(0, f"Ticker: {ticker}")

    return {
        "ticker": ticker,
        "direction": direction,
        "confidence": confidence,
        "reasoning_trace": reasoning_trace,
        "position_size": position_size,
        "allocation_pct": allocation_pct,
    }
