from __future__ import annotations

from agents.models import NarrativeEvent, SentimentVector


class SentimentReasoningAgent:
    POSITIVE_WORDS = {
        "bullish", "surge", "soar", "beat", "growth", "profit", "upgrade", "outperform",
        "positive", "strong", "momentum", "breakout", "rally", "gain", "rising", "boom",
        "record", "exceed", "expansion", "opportunity", "breakthrough", "innovation",
        "partnership", "launch", "accelerate", "dominant", "leader", "ahead",
    }
    NEGATIVE_WORDS = {
        "bearish", "plunge", "crash", "miss", "loss", "decline", "downgrade", "underperform",
        "negative", "weak", "selloff", "breakdown", "slump", "drop", "falling", "bust",
        "debt", "lawsuit", "investigation", "risk", "volatile", "uncertainty", "fear",
        "recession", "inflation", "slowdown", "layoff", "restructuring", "default",
    }
    INTENSITY_WORDS = {
        "huge", "massive", "extreme", "panic", "euphoria", "crash", "surge", "meltdown",
        "skyrocket", "tank", "devastating", "unprecedented", "historic", "catastrophic",
        "explosive", "moon", "dump", "frenzy", "turmoil",
    }
    UNCERTAINTY_WORDS = {
        "uncertain", "unclear", "maybe", "perhaps", "unknown", "speculation", "rumor",
        "could", "might", "possible", "unpredictable", "volatile", "ambiguous",
        "mixed", "conflicting", "unstable", "doubt", "uncertainty",
    }

    def analyze(self, events: list[NarrativeEvent]) -> SentimentVector:
        if not events:
            return SentimentVector()

        combined = " ".join(f"{e.title} {e.body}" for e in events).lower()
        words = combined.split()

        pos_count = sum(1 for w in words if w in self.POSITIVE_WORDS)
        neg_count = sum(1 for w in words if w in self.NEGATIVE_WORDS)
        int_count = sum(1 for w in words if w in self.INTENSITY_WORDS)
        unc_count = sum(1 for w in words if w in self.UNCERTAINTY_WORDS)
        total = len(words)

        net = (pos_count - neg_count) / max(pos_count + neg_count, 1)
        polarity = max(-1.0, min(1.0, net))

        intensity = min(1.0, int_count / max(total * 0.05, 1))
        uncertainty = min(1.0, unc_count / max(total * 0.05, 1))

        instability = (intensity + uncertainty) / 2.0

        pre_scored = [e.sentiment_score for e in events if e.sentiment_score is not None]
        blended_polarity = (
            (polarity + (sum(pre_scored) / len(pre_scored))) / 2.0
            if pre_scored
            else polarity
        )

        event_count_confidence = min(1.0, len(events) / 15.0)
        word_count_confidence = min(1.0, total / 500.0)
        confidence = (event_count_confidence * 0.4 + word_count_confidence * 0.6 - uncertainty * 0.3)

        return SentimentVector(
            polarity=round(max(-1.0, min(1.0, blended_polarity)), 4),
            confidence=round(max(0.0, min(1.0, confidence)), 4),
            emotional_intensity=round(intensity, 4),
            instability_score=round(instability, 4),
            uncertainty=round(uncertainty, 4),
        )
