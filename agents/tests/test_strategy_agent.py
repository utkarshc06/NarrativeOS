import pytest
from httpx import ASGITransport, AsyncClient

from agents.strategy_agent.app import app, compute_confidence, compute_position_size, determine_direction


@pytest.mark.anyio
async def test_health():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["agent"] == "strategy"


@pytest.mark.anyio
async def test_formulate_returns_signal(sample_debate_result):
    risk_assessment = {"risk_score": 0.35, "risk_factors": ["Valuation"]}
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/formulate", json={
            "risk_assessment": risk_assessment,
            "debate": sample_debate_result,
            "config": {"signal_types": ["BUY", "SELL", "HOLD", "WATCHLIST"]},
        })
    assert resp.status_code == 200
    data = resp.json()
    assert "ticker" in data
    assert "direction" in data
    assert "confidence" in data
    assert "reasoning_trace" in data
    assert data["direction"] in ("BUY", "SELL", "HOLD", "WATCHLIST")
    assert 0 <= data["confidence"] <= 1


@pytest.mark.anyio
async def test_determine_direction_bull():
    debate = {
        "bull_case": "Strong growth drivers with expanding margins and multiple tailwinds supporting continued outperformance",
        "bear_case": "Some minor headwinds but manageable",
        "arbiter_ruling": "Bull case is significantly stronger with clear catalysts ahead",
        "debate_rounds": 3,
    }
    direction = determine_direction(0.3, debate)
    assert direction == "BUY"


@pytest.mark.anyio
async def test_determine_direction_hold_high_risk():
    debate = {
        "bull_case": "Good outlook",
        "bear_case": "Significant risks ahead",
        "arbiter_ruling": "Uncertain with high volatility expected",
        "debate_rounds": 2,
    }
    direction = determine_direction(0.8, debate)
    assert direction == "HOLD"


@pytest.mark.anyio
async def test_confidence_bounds():
    debate = {
        "bull_case": "B",
        "bear_case": "A",
        "arbiter_ruling": "Uncertain",
        "debate_rounds": 1,
    }
    for risk in [0.1, 0.5, 0.9]:
        conf = compute_confidence("HOLD", risk, debate)
        assert 0 <= conf <= 1


@pytest.mark.anyio
async def test_position_size_zero_for_hold():
    pct, size = compute_position_size("HOLD", 0.8, 0.3)
    assert pct == 0.0
    assert size == 0.0
