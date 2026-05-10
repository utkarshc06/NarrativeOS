import os
import re
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import feedparser
import httpx
from apify import Actor
from src.normalize import normalize_reddit_post

KNOWN_COMPANIES: dict[str, str] = {
    "NVDA": "NVIDIA", "AMD": "Advanced Micro Devices", "AAPL": "Apple",
    "MSFT": "Microsoft", "GOOGL": "Alphabet (Google)", "GOOG": "Alphabet (Google)",
    "AMZN": "Amazon", "META": "Meta Platforms", "TSLA": "Tesla",
    "JPM": "JPMorgan Chase", "GS": "Goldman Sachs", "SPY": "SPDR S&P 500 ETF",
    "QQQ": "Invesco QQQ Trust", "PLTR": "Palantir Technologies", "AVGO": "Broadcom",
    "TSM": "Taiwan Semiconductor", "ARM": "ARM Holdings", "NFLX": "Netflix",
    "DIS": "Walt Disney", "BA": "Boeing", "COIN": "Coinbase",
    "HOOD": "Robinhood Markets", "MSTR": "MicroStrategy",
}

TICKER_PATTERN = re.compile(r'\b[A-Z]{1,5}\b')

RSS_URL = "https://www.reddit.com/r/{subreddit}/{sort}/.rss"


async def main() -> None:
    async with Actor:
        Actor.log.info("NarrativeOS Reddit Scraper — starting (RSS mode)")

        inp = await Actor.get_input() or {}
        subreddits: list[str] = inp.get("subreddits", ["wallstreetbets", "investing", "stocks"])
        max_posts: int = inp.get("max_posts", 25)
        sort: str = inp.get("sort", "new")

        posts: list[dict] = []

        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            for sub_name in subreddits:
                url = RSS_URL.format(subreddit=sub_name, sort=sort)
                Actor.log.info("Fetching %s", url)

                try:
                    resp = await client.get(url, headers={
                        "User-Agent": "Mozilla/5.0 (compatible; NarrativeOS/1.0)",
                        "Accept": "application/rss+xml, application/xml, text/xml",
                    })
                    resp.raise_for_status()

                    feed = feedparser.parse(resp.text)
                    entries = feed.entries[:max_posts]

                    for entry in entries:
                        content = entry.get("summary", "") or entry.get("content", [{}])[0].get("value", "") if entry.get("content") else ""
                        author_detail = entry.get("author_detail", {})
                        author = author_detail.get("name", entry.get("author", "[deleted]")) if author_detail else entry.get("author", "[deleted]")

                        published_parsed = entry.get("published_parsed")
                        published_ts = datetime(*published_parsed[:6], tzinfo=timezone.utc).timestamp() if published_parsed else 0

                        link = entry.get("link", "")
                        flair = ""
                        for tag in entry.get("tags", []):
                            flair = tag.get("term", "")
                            if "flair" in (tag.get("label", "") or "").lower():
                                break

                        posts.append({
                            "title": entry.get("title", ""),
                            "selftext": _clean_html(content)[:5000],
                            "url": link if link.startswith("http") else f"https://reddit.com{link}",
                            "permalink": link,
                            "author": author,
                            "created_utc": published_ts,
                            "ups": 0,
                            "score": 0,
                            "num_comments": 0,
                            "subreddit": sub_name,
                            "link_flair_text": flair,
                        })

                    Actor.log.info("  → %d posts from r/%s", len(entries), sub_name)

                except Exception as e:
                    Actor.log.warning("Failed r/%s RSS: %s", sub_name, e)
                    continue

        Actor.log.info("Collected %d raw posts total", len(posts))

        for post in posts:
            event = normalize_reddit_post(post)
            await Actor.push_data(event)

        Actor.log.info("Reddit scrape complete — %d events pushed", len(posts))


def _clean_html(raw: str) -> str:
    if not raw:
        return ""
    clean = re.sub(r'<[^>]+>', ' ', raw)
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
