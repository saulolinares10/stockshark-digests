from __future__ import annotations
from urllib.parse import quote_plus

def research_links(symbol: str) -> dict[str, str]:
    sym = symbol.upper()
    return {
        "Yahoo": f"https://finance.yahoo.com/quote/{sym}",
        "TradingView": f"https://www.tradingview.com/symbols/{sym}/",
        "Google News": f"https://news.google.com/search?q={quote_plus(sym)}",
        "SEC EDGAR": f"https://www.sec.gov/edgar/search/#/q={quote_plus(sym)}",
    }
