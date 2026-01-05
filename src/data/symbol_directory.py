from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional
import io
import urllib.request


NASDAQ_LISTED_URL = "ftp://ftp.nasdaqtrader.com/symboldirectory/nasdaqlisted.txt"
OTHER_LISTED_URL = "ftp://ftp.nasdaqtrader.com/symboldirectory/otherlisted.txt"


@dataclass
class ListedSymbol:
    symbol: str
    name: str
    exchange: str
    is_etf: Optional[bool]  # None if unknown
    is_test: bool


def _download_text(url: str) -> str:
    with urllib.request.urlopen(url, timeout=30) as resp:
        raw = resp.read()
    return raw.decode("utf-8", errors="replace")


def _parse_pipe_file(text: str) -> List[List[str]]:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    rows = []
    for ln in lines:
        if ln.startswith("File Creation Time"):
            continue
        if ln.startswith("Symbol|") or ln.startswith("ACT Symbol|"):
            continue
        parts = ln.split("|")
        if len(parts) > 1:
            rows.append(parts)
    return rows


def fetch_us_listed_symbols(include_etfs: bool = False) -> List[ListedSymbol]:
    out: List[ListedSymbol] = []

    # NASDAQ listed
    nasdaq_txt = _download_text(NASDAQ_LISTED_URL)
    rows = _parse_pipe_file(nasdaq_txt)
    # Format includes ETF field near the end on many versions; safest is by position:
    # Symbol|Security Name|Market Category|Test Issue|Financial Status|Round Lot Size|ETF|NextShares|...
    for r in rows:
        sym = (r[0] or "").strip()
        name = (r[1] or "").strip()
        test_issue = (r[3] or "").strip().upper() == "Y"
        # ETF field can be r[6] in typical format
        etf = None
        if len(r) > 6:
            etf = (r[6] or "").strip().upper() == "Y"
        if test_issue:
            continue
        if (etf is True) and not include_etfs:
            continue
        if sym and sym.isascii():
            out.append(ListedSymbol(symbol=sym, name=name, exchange="NASDAQ", is_etf=etf, is_test=test_issue))

    # Other listed
    other_txt = _download_text(OTHER_LISTED_URL)
    rows2 = _parse_pipe_file(other_txt)
    # Typical format:
    # ACT Symbol|Security Name|Exchange|CQS Symbol|ETF|Round Lot Size|Test Issue|NASDAQ Symbol|...
    for r in rows2:
        sym = (r[0] or "").strip()
        name = (r[1] or "").strip()
        exch = (r[2] or "").strip()
        # ETF usually r[4]
        etf = None
        if len(r) > 4:
            etf = (r[4] or "").strip().upper() == "Y"
        # Test issue often r[6]
        is_test = False
        if len(r) > 6:
            is_test = (r[6] or "").strip().upper() == "Y"

        if is_test:
            continue
        if (etf is True) and not include_etfs:
            continue
        if sym and sym.isascii():
            out.append(ListedSymbol(symbol=sym, name=name, exchange=exch or "OTHER", is_etf=etf, is_test=is_test))

    # De-dup by symbol, preserve order
    seen = set()
    dedup: List[ListedSymbol] = []
    for x in out:
        if x.symbol not in seen:
            dedup.append(x)
            seen.add(x.symbol)
    return dedup
