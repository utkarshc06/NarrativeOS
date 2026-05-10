import pytest
from httpx import ASGITransport, AsyncClient

from agents.visualization_agent.app import app


@pytest.mark.anyio
async def test_health():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["agent"] == "visualization"


@pytest.mark.anyio
async def test_pipeline_status():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "ingress" in data
    assert "analysis" in data
    assert "execution" in data
    assert data["ingress"]["active"] is True
    assert data["ingress"]["events24h"] > 0


@pytest.mark.anyio
async def test_narrative_events():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/datasets/narrative_events/items?limit=5")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) > 0
    assert data[0]["id"].startswith("evt_")


@pytest.mark.anyio
async def test_analysis_signals():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/datasets/analysis_signals/items?limit=5")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) > 0


@pytest.mark.anyio
async def test_executed_signals():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/datasets/executed_signals/items?limit=5")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) > 0


@pytest.mark.anyio
async def test_agent_traces():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/traces")
    assert resp.status_code == 200
    data = resp.json()
    assert "narrative" in data
    assert "sentiment" in data
    assert "debate" in data
    assert "strategy" in data
