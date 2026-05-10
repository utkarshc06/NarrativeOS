import pytest
from httpx import ASGITransport, AsyncClient

from agents.risk_intelligence.app import app, compute_risk_score, detect_anomalies, extract_risk_factors


@pytest.mark.anyio
async def test_health():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["agent"] == "risk-intelligence"


@pytest.mark.anyio
async def test_assess_returns_risk_score(sample_debate_result, sample_narrative, sample_sentiment):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/assess", json={
            "debate_result": sample_debate_result,
            "narrative": sample_narrative,
            "sentiment": sample_sentiment,
        })
    assert resp.status_code == 200
    data = resp.json()
    assert "risk_score" in data
    assert 0 <= data["risk_score"] <= 1
    assert "risk_factors" in data
    assert "anomaly_flags" in data
    assert "confidence_degradation" in data


@pytest.mark.anyio
async def test_high_risk_keywords_increase_score():
    debate = {
        "bull_case": "fraud investigation risk",
        "bear_case": "bankruptcy default crash",
        "arbiter_ruling": "lawsuit risk",
        "debate_rounds": 2,
    }
    narrative = {"summary": "recession", "momentum_score": 0.2}
    sentiment = {"intensity": 0.5, "instability_score": 0.3}
    score = compute_risk_score(debate, narrative, sentiment)
    assert score > 0.5


@pytest.mark.anyio
async def test_anomaly_detection():
    combined = "This is a guaranteed moon shot to the moon! Pump it!"
    flags = detect_anomalies(combined)
    assert len(flags) > 0
    assert any(f["type"] == "hype_detected" for f in flags)


@pytest.mark.anyio
async def test_risk_factors_extraction():
    combined = "regulation inflation tariff default"
    factors = extract_risk_factors(combined)
    assert len(factors) > 0
    assert "Regulation" in factors
