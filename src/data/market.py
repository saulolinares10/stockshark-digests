from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import pandas as pd
import yfinance as yf

from src.data.finnhub_client import FinnhubClient

@dataclass
class PriceHistory:
    symbol: str
    df: pd.DataFrame  # columns: t, o, h, l, c, v

def fetch_daily_history(_client: FinnhubClient, symbol: str, lookback_days: int = 120) -> Optional[PriceHistory]:
    # Use yfinance (more reliable for daily candles)
    end = datetime.utcnow()
    start = end - timedelta(days=lookback_days + 10)

    df = yf.download(
        tickers=symbol,
        start=start.date().isoformat(),
        end=end.date().isoformat(),
        interval="1d",
        auto_adjust=False,
        progress=False,
        threads=False,
    )

    if df is None or df.empty:
        return None

    # yfinance returns index as datetime
    df = df.reset_index()
    # normalize columns
    df = df.rename(columns={
        "Date": "t",
        "Open": "o",
        "High": "h",
        "Low": "l",
        "Close": "c",
        "Volume": "v",
    })

    # Some tickers may come with timezone-aware timestamps; keep it simple
    df["t"] = pd.to_datetime(df["t"], utc=True, errors="coerce")

    # Drop rows with missing close
    df = df.dropna(subset=["c"]).sort_values("t").reset_index(drop=True)

    if len(df) < 30:
        return None

    return PriceHistory(symbol=symbol, df=df[["t", "o", "h", "l", "c", "v"]])

def fetch_quotes(client: FinnhubClient, symbols: List[str]) -> Dict[str, Dict]:
    out: Dict[str, Dict] = {}
    for s in symbols:
        try:
            out[s] = client.quote(s)
        except Exception:
            out[s] = {}
    return out
