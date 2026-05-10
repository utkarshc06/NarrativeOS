from __future__ import annotations

from typing import Literal

from agents.consensus.aggregator import SignalAggregator
from agents.debate.engine import DebateEngine
from agents.models import AgentState, AnalysisSignal, NarrativeEvent, SentimentVector
from agents.narrative_intelligence import NarrativeIntelligenceAgent
from agents.sentiment import SentimentReasoningAgent

try:
    from langgraph.graph import END, StateGraph
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False


def narrative_intelligence_node(state: AgentState) -> dict:
    agent = NarrativeIntelligenceAgent()
    clusters = agent.analyze(state.events)
    return {"topic_clusters": clusters}


def sentiment_reasoning_node(state: AgentState) -> dict:
    agent = SentimentReasoningAgent()
    sentiment = agent.analyze(state.events)
    return {"sentiment": sentiment}


def debate_node(state: AgentState) -> dict:
    ticker = state.ticker or (state.topic_clusters[0].label.split(": ")[0] if state.topic_clusters else "UNKNOWN")
    engine = DebateEngine(rounds=3)
    history, summary = engine.conduct_debate(ticker, state.topic_clusters, state.sentiment or SentimentVector())
    return {"debate_history": history, "debate_summary": summary}


def signal_generation_node(state: AgentState) -> dict:
    ticker = state.ticker or (state.topic_clusters[0].label.split(": ")[0] if state.topic_clusters else "UNKNOWN")
    aggregator = SignalAggregator()
    signal = aggregator.generate_signal(
        ticker=ticker,
        clusters=state.topic_clusters,
        sentiment=state.sentiment or SentimentVector(),
        debate_summary=state.debate_summary,
        events=state.events,
    )
    return {"signal": signal}


def should_debate(state: AgentState) -> Literal["debate", "signal"]:
    if state.sentiment and state.topic_clusters:
        return "debate"
    return "debate"


def create_workflow() -> StateGraph:
    if not LANGGRAPH_AVAILABLE:
        raise ImportError("langgraph is required to create workflows. Install with: pip install langgraph")

    workflow = StateGraph(AgentState)

    workflow.add_node("narrative_intelligence", narrative_intelligence_node)
    workflow.add_node("sentiment_reasoning", sentiment_reasoning_node)
    workflow.add_node("debate", debate_node)
    workflow.add_node("signal_generation", signal_generation_node)

    workflow.set_entry_point("narrative_intelligence")

    workflow.add_edge("narrative_intelligence", "sentiment_reasoning")
    workflow.add_conditional_edges("sentiment_reasoning", should_debate, {"debate": "debate", "signal": "signal_generation"})
    workflow.add_edge("debate", "signal_generation")
    workflow.add_edge("signal_generation", END)

    return workflow.compile()


def run_analysis(events: list[NarrativeEvent], ticker: str | None = None) -> AnalysisSignal:
    if LANGGRAPH_AVAILABLE:
        app = create_workflow()
        initial_state = AgentState(events=events, ticker=ticker)
        result = app.invoke(initial_state)
        return result["signal"]
    else:
        return _run_sequential(events, ticker)


def _run_sequential(events: list[NarrativeEvent], ticker: str | None = None) -> AnalysisSignal:
    narrative = NarrativeIntelligenceAgent()
    sentiment = SentimentReasoningAgent()
    debate = DebateEngine(rounds=3)
    aggregator = SignalAggregator()

    clusters = narrative.analyze(events)
    sentiment_vector = sentiment.analyze(events)
    resolved_ticker = ticker or (clusters[0].label.split(" — ")[0] if clusters else "UNKNOWN")
    _, debate_summary = debate.conduct_debate(resolved_ticker, clusters, sentiment_vector)
    signal = aggregator.generate_signal(resolved_ticker, clusters, sentiment_vector, debate_summary, events)

    return signal
