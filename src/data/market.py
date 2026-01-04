from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta
import time
import pandas as pd
from typing import Dict, List, Optional
from src.data.finnhub_client import FinnhubClient

@dataclass
class PriceHistory:
    symbol: str
    df: pd.DataFrame

def _to_unix(dt: datetime) -> int:
    return int(time.mktime(dt.timetuple()))

def fetch_daily_history(client: FinnhubClient, symbol: str, lookback_days: int = 120) -> Optional[PriceHistory]:
    end = datetime.utcnow()
    start = end - timedelta(days=lookback_days + 10)
    data = client.candles(symbol=symbol, resolution="D", _from=_to_unix(start), to=_to_unix(end))

    if not data or data.get("s") != "ok":
        return None

    df = pd.DataFrame({
        "t": pd.to_datetime(data["t"], unit="s", utc=True),
        "o": data["o"],
        "h": data["h"],
        "l": data["l"],
        "c": data["c"],
        "v": data["v"],
    }).sort_values("t")

    df = df.drop_duplicates(subset=["t"], keep="last").reset_index(drop=True)
    if len(df) < 30:
        return None
    return PriceHistory(symbol=symbol, df=df)

def fetch_quotes(client: FinnhubClient, symbols: List[str]) -> Dict[str, Dict]:
    out: Dict[str, Dict] = {}
    for s in symbols:
        try:
            out[s] = client.quote(s)
        except Exception:
            out[s] = {}
    return out
