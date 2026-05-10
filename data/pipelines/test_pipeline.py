"""
Quick test for the data pipeline — entity extraction + normalization.
Run: python -m data.pipelines.test_pipeline
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from data.pipelines.entity_extractor import KNOWN_COMPANIES, extract_entities, extract_tickers
from data.pipelines.normalize import normalize_article, normalize_reddit_post, normalize_sec_filing


def test_ticker_extraction():
    text = "NVDA earnings beat expectations! AMD also up. What about AAPL? $TSLA is volatile."
    tickers = extract_tickers(text)
    assert "NVDA" in tickers, f"Missing NVDA in {tickers}"
    assert "AMD" in tickers, f"Missing AMD in {tickers}"
    assert "AAPL" in tickers, f"Missing AAPL in {tickers}"
    assert "TSLA" in tickers, f"Missing TSLA in {tickers}"
    assert len(tickers) == 4, f"Expected 4 tickers, got {tickers}"
    print(f"  [PASS] ticker extraction: {tickers}")


def test_entity_extraction():
    entities = extract_entities("NVDA is leading the AI race")
    assert len(entities) == 1
    assert entities[0]["ticker"] == "NVDA"
    assert entities[0]["name"] == KNOWN_COMPANIES["NVDA"]
    print(f"  [PASS] entity extraction: {entities}")


def test_reddit_normalization():
    raw = {
        "title": "NVDA is going to the moon!",
        "selftext": "Their data center revenue doubled. AMD is also looking strong.",
        "url": "https://reddit.com/r/wallstreetbets/123",
        "permalink": "/r/wallstreetbets/123/nvda_moon/",
        "author": "stonks_trader",
        "created_utc": 1715200000,
        "ups": 1500,
        "score": 1500,
        "num_comments": 89,
        "subreddit": "wallstreetbets",
        "link_flair_text": "DD",
    }
    event = normalize_reddit_post(raw)
    assert event["source"] == "reddit"
    assert "NVDA" in event["ticker_mentions"]
    assert "AMD" in event["ticker_mentions"]
    assert event["metadata"]["post_type"] == "DD"
    assert event["metadata"]["upvotes"] == 1500
    assert event["id"].startswith("evt_reddit_")
    print(f"  [PASS] reddit normalization: {event['id']} — {event['title'][:40]}")


def test_article_normalization():
    raw = {
        "title": "Microsoft Reports Strong Cloud Growth",
        "body": "MSFT announced 20% growth in Azure revenue. GOOGL and AMZN also reported.",
        "summary": "Microsoft Azure growth",
        "url": "https://reuters.com/article/msft-earnings",
        "author": "Jane Doe",
        "published_parsed": None,
        "published": "2026-05-09T10:00:00Z",
        "source_name": "reuters",
    }
    event = normalize_article(raw)
    assert event["source"] == "news"
    assert "MSFT" in event["ticker_mentions"]
    assert "GOOGL" in event["ticker_mentions"]
    assert event["id"].startswith("evt_news_")
    print(f"  [PASS] article normalization: {event['id']} — {event['title'][:40]}")


def test_sec_normalization():
    raw = {
        "company_name": "NVIDIA Corporation",
        "form_type": "10-K",
        "url": "https://sec.gov/archives/edgar/data/1045810/000104581026000012/nvda-10k.htm",
        "description": "Annual report for fiscal year 2026",
        "filing_date": "2026-03-15",
        "cik": "1045810",
        "tickers": ["NVDA"],
        "period": "FY2026",
    }
    event = normalize_sec_filing(raw)
    assert event["source"] == "sec_filing"
    assert "NVDA" in event["ticker_mentions"]
    assert event["metadata"]["form_type"] == "10-K"
    assert "NVIDIA" in event["title"]
    assert event["id"].startswith("evt_sec_filing_")
    print(f"  [PASS] sec normalization: {event['id']} — {event['title'][:40]}")


if __name__ == "__main__":
    print("Testing NarrativeOS data pipeline...\n")
    test_ticker_extraction()
    test_entity_extraction()
    test_reddit_normalization()
    test_article_normalization()
    test_sec_normalization()
    print(f"\nAll {5}/{5} tests passed!")
