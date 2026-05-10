import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


import httpx
from apify import Actor
from bs4 import BeautifulSoup
from src.normalize import normalize_sec_filing

CIK_MAP: dict[str, str] = {
    "NVDA": "1045810",
    "AMD": "0002488",
    "AAPL": "320193",
    "MSFT": "789019",
    "GOOGL": "1652044",
    "AMZN": "1018724",
    "META": "1326801",
    "TSLA": "1318605",
    "JPM": "19617",
    "GS": "886982",
    "PLTR": "1321655",
    "AVGO": "1730168",
    "TSM": "1046179",
    "ARM": "1973239",
    "DIS": "1744489",
    "NFLX": "1065280",
    "BA": "12927",
    "COIN": "1679788",
    "HOOD": "1783879",
    "MSTR": "1581647",
}

SEC_HEADERS = {
    "User-Agent": "NarrativeOS/1.0 (contact@narrativeos.dev)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate",
}


async def main() -> None:
    async with Actor:
        Actor.log.info("NarrativeOS SEC Filing Scraper — starting")

        inp = await Actor.get_input() or {}
        tickers: list[str] = inp.get("tickers", list(CIK_MAP.keys()))
        form_types: list[str] = inp.get("form_types", ["10-K", "10-Q", "8-K"])
        max_filings: int = inp.get("max_filings", 5)

        filings: list[dict] = []

        async with httpx.AsyncClient(timeout=30, headers=SEC_HEADERS, follow_redirects=True) as client:
            for ticker in tickers:
                cik = CIK_MAP.get(ticker)
                if not cik:
                    Actor.log.warning("No CIK mapping for %s — skipping", ticker)
                    continue

                cik_padded = cik.zfill(10)
                url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik_padded}&type=&dateb=&owner=exclude&count={max_filings * 3}"

                try:
                    resp = await client.get(url)
                    resp.raise_for_status()
                    soup = BeautifulSoup(resp.text, "lxml")
                except Exception as e:
                    Actor.log.warning("Failed to fetch SEC page for %s: %s", ticker, e)
                    continue

                table = soup.select_one("table.tableFile2")
                if not table:
                    Actor.log.debug("No filing table found for %s", ticker)
                    continue

                rows = table.select("tr")[1:]
                for row in rows:
                    cols = row.select("td")
                    if len(cols) < 4:
                        continue

                    form_type = cols[0].get_text(strip=True)
                    if form_type not in form_types:
                        continue

                    link = cols[1].select_one("a")
                    filing_url = f"https://www.sec.gov{link.get('href')}" if link else ""

                    desc = cols[2].get_text(strip=True) if len(cols) > 2 else ""
                    date = cols[3].get_text(strip=True) if len(cols) > 3 else ""

                    company_name = _get_company_name(soup)
                    filings.append({
                        "company_name": company_name,
                        "form_type": form_type,
                        "url": filing_url,
                        "description": desc,
                        "filing_date": date,
                        "cik": cik,
                        "tickers": [ticker],
                        "period": "",
                    })

                    if len([f for f in filings if ticker in f.get("tickers", [])]) >= max_filings:
                        break

        Actor.log.info("Collected %d SEC filings", len(filings))

        for filing in filings:
            event = normalize_sec_filing(filing)
            await Actor.push_data(event)

        Actor.log.info("SEC scrape complete — %d events pushed", len(filings))


def _get_company_name(soup: BeautifulSoup) -> str:
    tag = soup.select_one("span.companyName")
    if tag:
        raw = tag.get_text(strip=True)
        return raw.split("CIK")[0].strip().rstrip(",")
    return ""


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
