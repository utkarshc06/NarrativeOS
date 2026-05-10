
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    apify_api_token: str = ""
    apify_webhook_url: str = ""

    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_user_agent: str = "NarrativeOS/1.0"

    subreddits: list[str] = ["wallstreetbets", "investing", "stocks"]
    tracked_tickers: list[str] = [
        "NVDA", "AMD", "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA",
        "JPM", "GS", "SPY", "QQQ", "PLTR", "AVGO", "TSM", "ARM",
    ]

    news_sources: list[str] = [
        "https://feeds.content.dowjones.io/public/rss/markets",
        "https://www.investing.com/rss/news.rss",
        "https://finance.yahoo.com/news/rssindex",
    ]

    sec_user_agent: str = "NarrativeOS/1.0 (contact@narrativeos.dev)"
    sec_base_url: str = "https://www.sec.gov/cgi-bin/browse-edgar"

    max_posts_per_source: int = 50
    dedup_window_hours: int = 24

    event_stream_url: str = "http://localhost:8000/api/v1/webhooks/apify-event"

    model_config = {"env_prefix": "NARRATIVEOS_", "env_file": ".env"}


settings = Settings()
