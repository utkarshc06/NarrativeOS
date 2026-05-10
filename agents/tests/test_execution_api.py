import pytest
from httpx import ASGITransport, AsyncClient

from agents.execution_api.app import app


@pytest.mark.anyio
async def test_health():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["service"] == "execution-api"


@pytest.mark.anyio
async def test_execute_buy_returns_execution():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/execute", json={
            "signal": {"ticker": "NVDA", "direction": "BUY", "confidence": 0.78},
            "approval": {"approved": True, "notes": "Approved by risk team"},
            "mode": "simulated",
        })
    assert resp.status_code == 200
    data = resp.json()
    assert data["execution_id"].startswith("exec_")
    assert data["ticker"] == "NVDA"
    assert data["direction"] == "BUY"
    assert data["status"] == "filled"
    assert data["quantity"] > 0
    assert data["price"] > 0


@pytest.mark.anyio
async def test_execute_sell():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/execute", json={
            "signal": {"ticker": "AMD", "direction": "SELL", "confidence": 0.65},
            "approval": {"approved": True, "notes": ""},
            "mode": "simulated",
        })
    assert resp.status_code == 200
    data = resp.json()
    assert data["direction"] == "SELL"
    assert data["quantity"] > 0


@pytest.mark.anyio
async def test_execute_rejects_unapproved():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/execute", json={
            "signal": {"ticker": "NVDA", "direction": "BUY", "confidence": 0.78},
            "approval": {"approved": False, "notes": "Rejected"},
            "mode": "simulated",
        })
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_execute_rejects_hold():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/execute", json={
            "signal": {"ticker": "NVDA", "direction": "HOLD", "confidence": 0.5},
            "approval": {"approved": True, "notes": ""},
            "mode": "simulated",
        })
    assert resp.status_code == 400


@pytest.mark.anyio
async def test_list_orders():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/orders")
    assert resp.status_code == 200
    data = resp.json()
    assert "orders" in data
    assert data["total"] > 0
