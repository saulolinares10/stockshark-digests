from __future__ import annotations
from urllib.parse import quote_plus

def research_links(symbol: str, instagram_handle: str | None = None) -> dict[str, str]:
    sym = symbol.upper()
    links = {
        "Yahoo": f"https://finance.yahoo.com/quote/{sym}",
        "TradingView": f"https://www.tradingview.com/symbols/{sym}/",
        "SEC EDGAR": f"https://www.sec.gov/edgar/search/#/q={quote_plus(sym)}",
        "Google News": f"https://news.google.com/search?q={quote_plus(sym + ' stock')}",
        "CNBC search": f"https://news.google.com/search?q={quote_plus(sym + ' stock site:cnbc.com')}",
    }
    if instagram_handle:
        links["Instagram"] = f"https://www.instagram.com/{instagram_handle.strip().lstrip('@')}/"
    return links
