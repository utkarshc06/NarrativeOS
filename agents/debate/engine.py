from __future__ import annotations

import logging
import os

from agents.models import (
    DebatePosition,
    DebateRound,
    DebateSummary,
    SentimentVector,
    TopicCluster,
)

try:
    from openai import OpenAI
    openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))
except ImportError:
    openai_client = None

logger = logging.getLogger(__name__)


class BullAgent:
    def __init__(self):
        self.role = "bull"

    def build_case(
        self,
        ticker: str,
        clusters: list[TopicCluster],
        sentiment: SentimentVector,
        round_number: int = 1,
        counter_arguments: list[str] | None = None,
    ) -> DebatePosition:
        cluster = next((c for c in clusters if ticker in c.label), None)
        momentum = cluster.momentum_score if cluster else 0.5

        if openai_client and os.environ.get("OPENAI_API_KEY"):
            try:
                cluster_info = f"Topic: {cluster.label}, Momentum: {cluster.momentum_score}" if cluster else "General Market"
                prompt = f"You are a Bullish Financial Agent. Build a strong bull case for {ticker}. Context: {cluster_info}, Sentiment Polarity: {sentiment.polarity:.2f}. Round {round_number}."
                if counter_arguments:
                    prompt += f"\nRebut these bear arguments: {counter_arguments}"

                response = openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a professional financial debate agent arguing the bull case. Be concise and data-driven."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7
                )
                argument = response.choices[0].message.content
                confidence = min(1.0, (momentum * 0.4 + max(0, sentiment.polarity) * 0.3 + (1 - sentiment.uncertainty) * 0.3))
                return DebatePosition(agent_role="bull", argument=argument, evidence=[f"Narrative momentum: {momentum:.0%}", "LLM Analysis"], confidence=round(confidence, 4))
            except Exception as e:
                logger.error(f"OpenAI call failed in BullAgent: {e}")

        # Fallback to heuristics
        argument_parts = [f"Bull Case for {ticker} (Round {round_number}):"]
        if momentum > 0.6:
            argument_parts.append(f"Strong narrative momentum detected at {momentum:.0%}, indicating growing market interest.")
        elif momentum > 0.3:
            argument_parts.append(f"Moderate narrative momentum at {momentum:.0%}, potential for acceleration.")
        if sentiment.polarity > 0.2:
            argument_parts.append(f"Positive sentiment polarity at {sentiment.polarity:.2f} supports bullish outlook.")
        if sentiment.emotional_intensity < 0.7:
            argument_parts.append("Emotional intensity is controlled, suggesting rational optimism rather than euphoria.")
        if counter_arguments:
            for arg in counter_arguments:
                argument_parts.append(f"Addressing concern: {arg}")
        confidence = min(1.0, (momentum * 0.4 + max(0, sentiment.polarity) * 0.3 + (1 - sentiment.uncertainty) * 0.3))
        return DebatePosition(
            agent_role="bull",
            argument="\n".join(argument_parts),
            evidence=[f"Narrative momentum: {momentum:.0%}", f"Sentiment polarity: {sentiment.polarity:.2f}"],
            confidence=round(confidence, 4),
        )


class BearAgent:
    def __init__(self):
        self.role = "bear"

    def build_case(
        self,
        ticker: str,
        clusters: list[TopicCluster],
        sentiment: SentimentVector,
        round_number: int = 1,
        counter_arguments: list[str] | None = None,
    ) -> DebatePosition:
        cluster = next((c for c in clusters if ticker in c.label), None)
        momentum = cluster.momentum_score if cluster else 0.5

        if openai_client and os.environ.get("OPENAI_API_KEY"):
            try:
                cluster_info = f"Topic: {cluster.label}, Momentum: {cluster.momentum_score}" if cluster else "General Market"
                prompt = f"You are a Bearish Financial Agent. Build a strong bear case for {ticker}. Context: {cluster_info}, Sentiment Polarity: {sentiment.polarity:.2f}. Round {round_number}."
                if counter_arguments:
                    prompt += f"\nRebut these bull arguments: {counter_arguments}"

                response = openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a professional financial debate agent arguing the bear case. Be concise and highlight risks."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7
                )
                argument = response.choices[0].message.content
                confidence = min(1.0, (momentum * 0.2 + max(0, -sentiment.polarity) * 0.4 + sentiment.instability_score * 0.4))
                return DebatePosition(agent_role="bear", argument=argument, evidence=[f"Narrative instability: {sentiment.instability_score:.0%}", "LLM Analysis"], confidence=round(confidence, 4))
            except Exception as e:
                logger.error(f"OpenAI call failed in BearAgent: {e}")

        # Fallback to heuristics
        argument_parts = [f"Bear Case for {ticker} (Round {round_number}):"]
        if sentiment.instability_score > 0.5:
            argument_parts.append(f"High narrative instability at {sentiment.instability_score:.0%} — sentiment could reverse sharply.")
        else:
            argument_parts.append("Market complacency may be underestimating downside risks.")
        if momentum > 0.7:
            argument_parts.append("Excessive narrative momentum suggests crowded positioning and potential for mean reversion.")
        if sentiment.emotional_intensity > 0.6:
            argument_parts.append(f"Elevated emotional intensity at {sentiment.emotional_intensity:.0%} is a warning sign of irrational exuberance.")
        if sentiment.uncertainty > 0.4:
            argument_parts.append(f"Uncertainty level at {sentiment.uncertainty:.0%} creates vulnerability to negative surprises.")
        if counter_arguments:
            for arg in counter_arguments:
                argument_parts.append(f"Rebuttal to: {arg}")
        confidence = min(1.0, (momentum * 0.2 + max(0, -sentiment.polarity) * 0.4 + sentiment.instability_score * 0.4))

        return DebatePosition(
            agent_role="bear",
            argument="\n".join(argument_parts),
            evidence=[f"Narrative instability: {sentiment.instability_score:.0%}", f"Uncertainty: {sentiment.uncertainty:.0%}"],
            confidence=round(confidence, 4),
        )


class ArbiterAgent:
    def __init__(self):
        self.role = "arbiter"

    def arbitrate(
        self,
        ticker: str,
        rounds: list[DebateRound],
        sentiment: SentimentVector,
    ) -> DebateSummary:
        last_round = rounds[-1] if rounds else None
        if not last_round:
            return DebateSummary(bull_case="No debate conducted", bear_case="No debate conducted", arbiter_ruling="Insufficient data", debate_rounds=0)

        bull = last_round.bull_position
        bear = last_round.bear_position

        bull_score = bull.confidence
        bear_score = bear.confidence

        if openai_client and os.environ.get("OPENAI_API_KEY"):
            try:
                prompt = f"You are the Arbiter. Evaluate the debate for {ticker}.\nBull Case:\n{bull.argument}\n\nBear Case:\n{bear.argument}\n\nSentiment Polarity: {sentiment.polarity:.2f}\nProvide a concise ruling on which side prevails and why."
                response = openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a professional financial debate arbiter. Synthesize the arguments and provide a clear, objective ruling."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.4
                )
                ruling = response.choices[0].message.content
                return DebateSummary(
                    bull_case=bull.argument,
                    bear_case=bear.argument,
                    arbiter_ruling=ruling,
                    debate_rounds=len(rounds),
                )
            except Exception as e:
                logger.error(f"OpenAI call failed in ArbiterAgent: {e}")

        # Fallback to heuristics
        if bull_score > bear_score + 0.1:
            ruling = "Bull case prevails — narrative momentum and sentiment support continued upside."
            ruling_detail = f"Bull confidence {bull_score:.0%} vs Bear confidence {bear_score:.0%}. "
            if sentiment.instability_score > 0.5:
                ruling_detail += "However, elevated instability warrants monitoring for reversal signals."
            elif sentiment.uncertainty > 0.4:
                ruling_detail += "Moderate uncertainty suggests position sizing should be conservative."
        elif bear_score > bull_score + 0.1:
            ruling = "Bear case prevails — risk factors and instability outweigh optimistic positioning."
            ruling_detail = f"Bear confidence {bear_score:.0%} vs Bull confidence {bull_score:.0%}. "
        else:
            ruling = "Balanced — both cases have merit. Awaiting additional catalysts for directional conviction."
            ruling_detail = f"Bull {bull_score:.0%} vs Bear {bear_score:.0%} — near parity. "

        ruling += " " + ruling_detail

        return DebateSummary(
            bull_case=bull.argument,
            bear_case=bear.argument,
            arbiter_ruling=ruling,
            debate_rounds=len(rounds),
        )


class DebateEngine:
    def __init__(self, rounds: int = 3):
        self.rounds = rounds
        self.bull = BullAgent()
        self.bear = BearAgent()
        self.arbiter = ArbiterAgent()

    def conduct_debate(
        self,
        ticker: str,
        clusters: list[TopicCluster],
        sentiment: SentimentVector,
    ) -> tuple[list[DebateRound], DebateSummary]:
        debate_rounds: list[DebateRound] = []
        bull_counter: list[str] = []
        bear_counter: list[str] = []

        for r in range(1, self.rounds + 1):
            bull_pos = self.bull.build_case(ticker, clusters, sentiment, r, bear_counter)
            bear_pos = self.bear.build_case(ticker, clusters, sentiment, r, bull_counter)

            debate_rounds.append(DebateRound(round_number=r, bull_position=bull_pos, bear_position=bear_pos))

            bull_counter = [f"Bear argued: {bear_pos.argument[:200]}"]
            bear_counter = [f"Bull argued: {bull_pos.argument[:200]}"]

        summary = self.arbiter.arbitrate(ticker, debate_rounds, sentiment)
        return debate_rounds, summary
