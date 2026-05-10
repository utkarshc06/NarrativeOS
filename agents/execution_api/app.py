"""Execution API — handles simulated trade execution for the execution canvas."""

import uuid
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Execution API", version="0.1.0")

ORDER_BOOK: list[dict] = []


class Approval(BaseModel):
    approved: bool
    notes: str | None = None


class ExecuteRequest(BaseModel):
    signal: dict
    approval: Approval
    executed_at: str | None = None
    mode: str = "simulated"


class ExecutionResult(BaseModel):
    execution_id: str
    ticker: str
    direction: str
    confidence: float
    quantity: int
    price: float
    total_value: float
    mode: str
    executed_at: str
    status: str
    message: str


ASSET_PRICES: dict[str, float] = {
    "NVDA": 875.50, "AMD": 145.30, "AAPL": 210.45,
    "MSFT": 425.10, "GOOGL": 178.90, "AMZN": 198.75,
    "META": 525.60, "TSLA": 245.80, "JPM": 205.30,
    "GS": 485.20, "PLTR": 78.40, "AVGO": 1650.00,
    "TSM": 168.50, "ARM": 135.20, "SPY": 545.30,
    "QQQ": 475.80,
}

POSITION_SIZES: dict[str, int] = {
    "BUY": 100, "SELL": 100, "HOLD": 0, "WATCHLIST": 0,
}


def compute_slippage(confidence: float) -> float:
    return round(1.0 - (confidence * 0.005), 4)


@app.get("/health")
def health():
    return {"status": "ok", "service": "execution-api", "version": "0.1.0", "orders_executed": len(ORDER_BOOK)}


@app.get("/orders")
def list_orders():
    return {"orders": ORDER_BOOK, "total": len(ORDER_BOOK)}


@app.get("/orders/{execution_id}")
def get_order(execution_id: str):
    for order in ORDER_BOOK:
        if order["execution_id"] == execution_id:
            return order
    raise HTTPException(status_code=404, detail="Order not found")


@app.post("/execute", response_model=ExecutionResult)
def execute(req: ExecuteRequest):
    if not req.approval.approved:
        raise HTTPException(status_code=403, detail="Trade not approved")

    signal = req.signal
    ticker = signal.get("ticker", "UNKNOWN")
    direction = signal.get("direction", "HOLD")
    confidence = float(signal.get("confidence", 0.0))

    if direction in ("HOLD", "WATCHLIST"):
        raise HTTPException(status_code=400, detail=f"No execution needed for {direction} signal")

    base_price = ASSET_PRICES.get(ticker, 100.0)
    slippage = compute_slippage(confidence)
    fill_price = round(base_price * (1 + slippage) if direction == "BUY" else base_price * (1 - slippage), 2)
    quantity = POSITION_SIZES.get(direction, 100)
    total_value = round(quantity * fill_price, 2)

    execution_id = f"exec_{uuid.uuid4().hex[:12]}"
    now = req.executed_at or datetime.now(timezone.utc).isoformat()

    result = {
        "execution_id": execution_id,
        "ticker": ticker,
        "direction": direction,
        "confidence": confidence,
        "quantity": quantity,
        "price": fill_price,
        "total_value": total_value,
        "mode": req.mode,
        "executed_at": now,
        "status": "filled",
            "message": f"Executed {direction} {quantity} shares of {ticker} at ${fill_price} ({req.mode})",
    }
    ORDER_BOOK.append(result)

    return result
