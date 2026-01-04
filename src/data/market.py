from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import pandas as pd
from pandas_datareader import data as pdr

from src.data.finnhub_client import FinnhubClient

@dataclass
class PriceHistory:
    symbol: str
    df: pd.DataFrame  # columns: t, o, h, l, c, v

def _to_stooq_symbol(symbol: str) -> str:
    # Stooq uses ".us" for US stocks/ETFs
    # Example: AMZN -> amzn.us
    return f"{symbol.lower()}.us"

def fetch_daily_history(_client: FinnhubClient, symbol: str, lookback_days: int = 120) -> Optional[PriceHistory]:
    end = datetime.utcnow().date()
    start = (datetime.utcnow() - timedelta(days=lookback_days + 30)).date()

    stooq_symbol = _to_stooq_symbol(symbol)

    try:
        df = pdr.DataReader(stooq_symbol, "stooq", start, end)
    except Exception:
        return None

    if df is None or df.empty:
        return None

    # Stooq returns newest-first; reverse it
    df = df.sort_index().reset_index()

    # Normalize columns to match our pipeline
    # Stooq columns: Date, Open, High, Low, Close, Volume
    df = df.rename(columns={
        "Date": "t",
        "Open": "o",
        "High": "h",
        "Low": "l",
        "Close": "c",
        "Volume": "v",
    })

    df["t"] = pd.to_datetime(df["t"], utc=True, errors="coerce")
    df = df.dropna(subset=["c"]).reset_index(drop=True)

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

