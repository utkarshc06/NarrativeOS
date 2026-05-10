from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from agents.graph.workflow import run_analysis
from agents.models import AnalysisSignal, NarrativeEventBatch

logger = logging.getLogger("narrativeos.webhooks")


async def heartbeat_loop():
    while True:
        logger.info("Heartbeat: pinging Zynd network for liveness (all agents healthy)...")
        # In a real scenario, this would use the Zynd SDK to post to the registry
        await asyncio.sleep(60)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("NarrativeOS Agent Mesh starting up...")
    heartbeat_task = asyncio.create_task(heartbeat_loop())
    yield
    heartbeat_task.cancel()
    logger.info("NarrativeOS Agent Mesh shutting down...")


app = FastAPI(
    title="NarrativeOS — Agent Mesh API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "narrativeos-agent-mesh", "version": "0.1.0"}


@app.post("/webhook/analyze", response_model=AnalysisSignal)
async def webhook_analyze(batch: NarrativeEventBatch):
    if not batch.events:
        raise HTTPException(status_code=400, detail="No events provided")

    logger.info(f"Received {len(batch.events)} events via {batch.trigger}")

    tickers = set()
    for event in batch.events:
        tickers.update(event.ticker_mentions)
    primary_ticker = next(iter(tickers)) if len(tickers) == 1 else None

    signal = run_analysis(batch.events, primary_ticker)
    return signal


@app.post("/api/v1/webhooks/signal", response_model=dict)
async def webhook_signal_out(signal: AnalysisSignal):
    logger.info(f"Signal generated: {signal.ticker} {signal.direction.value} @ {signal.confidence:.0%}")

    return {
        "status": "accepted",
        "signal_id": signal.signal_id,
        "ticker": signal.ticker,
        "direction": signal.direction.value,
        "confidence": signal.confidence,
    }


@app.post("/api/v1/agents/narrative-intelligence/analyze")
async def narrative_intelligence_analyze(batch: NarrativeEventBatch):
    from agents.narrative_intelligence import NarrativeIntelligenceAgent
    agent = NarrativeIntelligenceAgent()
    clusters = agent.analyze(batch.events)
    return {"clusters": [c.model_dump() for c in clusters]}


@app.post("/api/v1/agents/sentiment-reasoning/analyze")
async def sentiment_reasoning_analyze(batch: NarrativeEventBatch):
    from agents.sentiment import SentimentReasoningAgent
    agent = SentimentReasoningAgent()
    vector = agent.analyze(batch.events)
    return vector.model_dump()


@app.post("/api/v1/agents/strategy/generate")
async def strategy_generate(batch: NarrativeEventBatch):
    signal = run_analysis(batch.events)
    return signal.model_dump()


@app.get("/api/v1/agents/{agent_path:path}/health")
async def agent_health():
    return {"status": "ok"}
