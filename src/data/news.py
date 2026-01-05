from __future__ import annotations

from dataclasses import dataclass
from typing import List
from urllib.parse import quote_plus

import feedparser

@dataclass
class Headline:
    title: str
    link: str
    source: str

def google_news_rss(query: str) -> str:
    return f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=en-US&gl=US&ceid=US:en"

def fetch_google_news(query: str, max_items: int = 5) -> List[Headline]:
    feed = feedparser.parse(google_news_rss(query))
    out: List[Headline] = []
    for entry in feed.entries[:max_items]:
        title = (entry.get("title") or "").strip()
        link = (entry.get("link") or "").strip()
        source = ""
        if "source" in entry and isinstance(entry["source"], dict):
            source = (entry["source"].get("title") or "").strip()
        if title and link:
            out.append(Headline(title=title, link=link, source=source))
    return out

def fetch_cnbc_mentions(symbol: str, max_items: int = 5) -> List[Headline]:
    # CNBC itself blocks many automated requests; this uses Google News RSS as the aggregator.
    return fetch_google_news(f"{symbol} stock site:cnbc.com", max_items=max_items)

def fetch_web_buzz(symbol: str, max_items: int = 5) -> List[Headline]:
    return fetch_google_news(f"{symbol} stock", max_items=max_items)
