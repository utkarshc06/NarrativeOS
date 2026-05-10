import pytest
from httpx import ASGITransport, AsyncClient

from agents.market_correlation.app import app


@pytest.mark.anyio
async def test_health():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["agent"] == "market-correlation"


@pytest.mark.anyio
async def test_correlate_returns_correlations(sample_narrative_events):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/correlate", json={"events": sample_narrative_events})
    assert resp.status_code == 200
    data = resp.json()
    assert "correlations" in data
    assert len(data["correlations"]) > 0
    correlation = data["correlations"][0]
    assert "ticker" in correlation
    assert "sector" in correlation
    assert "correlation_score" in correlation
    assert "impact_direction" in correlation


@pytest.mark.anyio
async def test_correlate_sector_mapping():
    event = {
        "id": "evt_001",
        "source": "news",
        "source_actor": "test",
        "title": "JPM earnings beat",
        "body": "JPMorgan reported strong quarterly earnings with revenue exceeding expectations.",
        "url": "https://example.com",
        "published_at": "2026-05-09T14:00:00Z",
        "collected_at": "2026-05-09T14:01:00Z",
        "ticker_mentions": ["JPM", "GS"],
        "entities": [],
    }
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/correlate", json={"events": [event]})
    assert resp.status_code == 200
    data = resp.json()
    sectors = {c["sector"] for c in data["correlations"]}
    assert "Financials" in sectors


@pytest.mark.anyio
async def test_correlate_macro_relationships(sample_narrative_events):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/correlate", json={"events": sample_narrative_events})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["macro_relationships"]) > 0
    assert "involved_sectors" in data["macro_relationships"][0]
    assert "cross_sector_propagation" in data["macro_relationships"][0]
