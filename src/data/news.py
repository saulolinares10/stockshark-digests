from __future__ import annotations

from dataclasses import dataclass
from typing import List
from datetime import date, timedelta

from src.data.finnhub_client import FinnhubClient

@dataclass
class Headline:
    title: str
    link: str
    source: str

def fetch_company_news(client: FinnhubClient, symbol: str, days: int = 3, max_items: int = 5) -> List[Headline]:
    to_dt = date.today()
    from_dt = to_dt - timedelta(days=days)

    items = client.company_news(symbol, _from=from_dt.isoformat(), to=to_dt.isoformat())
    out: List[Headline] = []
    if not isinstance(items, list):
        return out

    for it in items[:max_items]:
        title = (it.get("headline") or "").strip()
        link = (it.get("url") or "").strip()
        source = (it.get("source") or "").strip()
        if title and link:
            out.append(Headline(title=title, link=link, source=source))
    return out
