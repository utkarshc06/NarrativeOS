import pytest


@pytest.fixture
def sample_narrative_events():
    return [
        {
            "id": "evt_20260509_test_001",
            "source": "news",
            "source_actor": "narrativeos-news-scraper",
            "title": "NVDA announces new AI chip with 3x performance",
            "body": "NVIDIA today announced its next-generation Blackwell Ultra chip, boasting three times the AI inference performance of the previous generation. The semiconductor giant expects data center revenue to continue growing 200% year-over-year as hyperscalers increase AI infrastructure spending. Analysts are bullish on the sustained demand driven by large language model training and inference workloads.",
            "url": "https://example.com/nvda-ai-chip",
            "author": "Test Author",
            "published_at": "2026-05-09T14:00:00Z",
            "collected_at": "2026-05-09T14:01:00Z",
            "ticker_mentions": ["NVDA", "AMD"],
            "entities": [{"name": "NVIDIA", "type": "company", "ticker": "NVDA"}],
            "metadata": {"source_confidence": 0.95},
        }
    ]


@pytest.fixture
def sample_debate_result():
    return {
        "bull_case": "Data center revenue growing 200% YoY, new Blackwell architecture entering mass production, strong demand from hyperscalers",
        "bear_case": "Valuation at 35x forward earnings, potential export restriction escalation, increasing competition from AMD and custom ASICs",
        "arbiter_ruling": "Bull case stronger — growth fundamentals outweigh valuation concerns at this stage",
        "debate_rounds": 3,
    }


@pytest.fixture
def sample_sentiment():
    return {
        "polarity": 0.65,
        "confidence": 0.8,
        "intensity": 0.4,
        "instability_score": 0.2,
    }


@pytest.fixture
def sample_narrative():
    return {
        "summary": "Strong semiconductor demand driven by AI inference workloads at hyperscalers",
        "momentum_score": 0.72,
        "propagation_rate": 0.6,
        "thematic_category": "technology",
        "acceleration_metrics": {"velocity": 0.8, "acceleration": 0.5},
    }
