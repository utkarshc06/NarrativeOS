from typing import Optional

from pydantic import BaseModel


class Entity(BaseModel):
    name: str
    type: str
    ticker: str


class NarrativeEvent(BaseModel):
    id: str
    source: str
    source_actor: str
    title: str
    body: str
    url: str
    author: Optional[str] = None
    published_at: str
    collected_at: str
    ticker_mentions: list[str]
    entities: Optional[list[Entity]] = None
    sentiment_score: Optional[float] = None
    metadata: Optional[dict] = None


class DebateSummary(BaseModel):
    bull_case: str
    bear_case: str
    arbiter_ruling: str
    debate_rounds: int


class AnalysisSignal(BaseModel):
    signal_id: str
    ticker: str
    direction: str
    confidence: float
    narrative_summary: str
    sentiment_polarity: float
    emotional_intensity: float
    debate_summary: DebateSummary
    risk_score: float
    risk_factors: Optional[list[str]] = None
    reasoning_trace: list[str]
    supporting_events: list[str]
    generated_at: str
    agent_version: str


class CorrelationResult(BaseModel):
    ticker: str
    sector: str
    correlation_score: float
    impact_direction: str
    reasoning: str


class MarketCorrelationOutput(BaseModel):
    correlations: list[CorrelationResult]
    cross_market_impacts: list[dict]
    macro_relationships: list[dict]


class RiskOutput(BaseModel):
    risk_score: float
    risk_factors: list[str]
    anomaly_flags: list[dict]
    volatility_forecast: Optional[float] = None
    confidence_degradation: float


class StrategyOutput(BaseModel):
    ticker: str
    direction: str
    confidence: float
    reasoning_trace: list[str]
    position_size: Optional[float] = None
    allocation_pct: Optional[float] = None
