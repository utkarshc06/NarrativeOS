import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import feedparser
import httpx
from apify import Actor
from bs4 import BeautifulSoup
from src.normalize import normalize_article


async def main() -> None:
    async with Actor:
        Actor.log.info("NarrativeOS News Scraper — starting")

        inp = await Actor.get_input() or {}
        rss_sources: list[str] = inp.get("rss_sources", [
            "https://feeds.content.dowjones.io/public/rss/markets",
            "https://finance.yahoo.com/news/rssindex",
        ])
        web_sources: list[str] = inp.get("web_sources", [])
        max_articles: int = inp.get("max_articles", 50)

        articles: list[dict] = []

        for rss_url in rss_sources:
            try:
                feed = feedparser.parse(rss_url)
                for entry in feed.entries[:max_articles // max(len(rss_sources), 1)]:
                    articles.append({
                        "title": entry.get("title", ""),
                        "body": _clean_html(entry.get("description", "")),
                        "summary": entry.get("summary", ""),
                        "url": entry.get("link", ""),
                        "author": _get_author(entry),
                        "published_parsed": entry.get("published_parsed"),
                        "published": entry.get("published", ""),
                        "source_name": _source_name_from_url(rss_url),
                    })
                Actor.log.info("RSS %s: %d articles", rss_url, len(feed.entries))
            except Exception as e:
                Actor.log.warning("RSS parse failed for %s: %s", rss_url, e)

        for web_url in web_sources:
            try:
                async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
                    resp = await client.get(web_url, headers={"User-Agent": "NarrativeOS/1.0"})
                    soup = BeautifulSoup(resp.text, "lxml")
                    for article_tag in soup.select("article, [class*=article], [class*=post]")[:20]:
                        title_el = article_tag.select_one("h1, h2, h3, [class*=title], [class*=headline]")
                        link_el = article_tag.select_one("a[href]")
                        body_el = article_tag.select_one("p, [class*=content], [class*=summary]")
                        if title_el:
                            articles.append({
                                "title": title_el.get_text(strip=True),
                                "body": body_el.get_text(strip=True) if body_el else "",
                                "summary": "",
                                "url": _resolve_url(link_el.get("href", ""), web_url) if link_el else "",
                                "author": "",
                                "published_parsed": None,
                                "published": "",
                                "source_name": _source_name_from_url(web_url),
                            })
                Actor.log.info("Web %s: scraped", web_url)
            except Exception as e:
                Actor.log.warning("Web scrape failed for %s: %s", web_url, e)

        articles = articles[:max_articles]
        Actor.log.info("Collected %d articles total", len(articles))

        for article in articles:
            event = normalize_article(article)
            await Actor.push_data(event)

        Actor.log.info("News scrape complete — %d events pushed", len(articles))


def _clean_html(raw: str) -> str:
    if not raw:
        return ""
    return BeautifulSoup(raw, "lxml").get_text(separator=" ", strip=True)


def _get_author(entry: dict) -> str:
    author = entry.get("author", "")
    if not author:
        for detail in entry.get("authors", []):
            author = detail.get("name", "")
            if author:
                break
    return author


def _source_name_from_url(url: str) -> str:
    from urllib.parse import urlparse
    domain = urlparse(url).netloc.lower()
    domain = domain.replace("www.", "").replace("feeds.", "")
    return domain.split(".")[0] if domain else "news"


def _resolve_url(href: str, base: str) -> str:
    from urllib.parse import urljoin
    return urljoin(base, href)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
