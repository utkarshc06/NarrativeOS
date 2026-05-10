import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any

from apify_client import ApifyClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from agents.graph.workflow import run_analysis
from agents.models import Entity, NarrativeEvent, SourceType
from data.pipelines.entity_extractor import extract_entities, extract_tickers
from data.stream.event_bus import EventBus

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

APIFY_TOKEN = os.environ.get("APIFY_API_TOKEN", "")
NEWS_RUN_ID = "QgROEyqZvSsukXh8e"
SEC_RUN_ID = "ldaLOgnrdLZXo1eam"
WEBHOOK_URL = os.environ.get("NARRATIVEOS_EVENT_STREAM_URL", "")


def enrich_event(event: dict[str, Any]) -> dict[str, Any]:
    text = f"{event.get('title', '')} {event.get('body', '')}"
    existing_tickers = event.get("ticker_mentions", []) or []
    if not existing_tickers:
        event["ticker_mentions"] = extract_tickers(text)
        event["entities"] = extract_entities(text)
    return event


def run_pipeline() -> list[dict[str, Any]]:
    client = ApifyClient(APIFY_TOKEN)
    bus = EventBus(webhook_url=WEBHOOK_URL)

    news_items = client.dataset(
        client.run(NEWS_RUN_ID).get()["defaultDatasetId"]
    ).list_items().items
    sec_items = client.dataset(
        client.run(SEC_RUN_ID).get()["defaultDatasetId"]
    ).list_items().items

    all_events = news_items + sec_items
    logger.info("Total raw events: %d (news=%d, sec=%d)", len(all_events), len(news_items), len(sec_items))

    enriched = [enrich_event(e) for e in all_events]
    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for e in enriched:
        eid = e.get("id", "")
        if eid not in seen:
            seen.add(eid)
            deduped.append(e)

    logger.info("After dedup: %d events", len(deduped))

    for event in deduped:
        bus.emit(event)

    flushed = bus.flush()
    bus.close()

    # E2E Agent Graph Execution
    narrative_events = []
    for e in deduped:
        try:
            ne = NarrativeEvent(
                id=e.get("id", ""),
                source=SourceType(e.get("source", "news")),
                source_actor=e.get("source_actor", "apify"),
                title=e.get("title", ""),
                body=e.get("body", ""),
                url=e.get("url", ""),
                author=e.get("author"),
                published_at=e.get("published_at", datetime.now(timezone.utc).isoformat()),
                collected_at=e.get("collected_at", datetime.now(timezone.utc).isoformat()),
                ticker_mentions=e.get("ticker_mentions", []),
                entities=[Entity(**ent) for ent in e.get("entities", [])],
                metadata=e.get("metadata", {})
            )
            narrative_events.append(ne)
        except Exception as err:
            logger.warning(f"Skipping event due to parsing error: {err}")

    signal = None
    if narrative_events:
        logger.info("Executing E2E agent graph on %d events...", len(narrative_events))
        signal = run_analysis(narrative_events)
        logger.info("Generated Signal: %s", signal)

    return flushed, signal


def main() -> None:
    events, signal = run_pipeline()
    print(f"\n{'='*60}")
    print(f"Pipeline complete: {len(events)} events emitted")
    print(f"{'='*60}")

    with_tickers = [e for e in events if e.get("ticker_mentions")]
    for e in with_tickers[:5]:
        tickers = ", ".join(e.get("ticker_mentions", []))
        print(f"  {e['id']} | {tickers} | {e['title'][:70]}")
    if len(with_tickers) > 5:
        print(f"  ... and {len(with_tickers) - 5} more with tickers")

    if signal:
        print(f"\n{'='*60}")
        print(f"Final E2E Signal Generated: {signal.direction.value} {signal.ticker} @ {signal.confidence:.0%}")
        print(f"Arbiter Ruling: {signal.debate_summary.arbiter_ruling if signal.debate_summary else 'N/A'}")
        print(f"{'='*60}")

if __name__ == "__main__":
    main()
