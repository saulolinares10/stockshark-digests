from __future__ import annotations
import os
import requests
from typing import Any, Dict, Optional

FINNHUB_BASE = "https://finnhub.io/api/v1"

class FinnhubClient:
    def __init__(self, api_key: Optional[str] = None, timeout: int = 20):
        self.api_key = api_key or os.getenv("FINNHUB_API_KEY")
        if not self.api_key:
            raise RuntimeError("FINNHUB_API_KEY is not set")
        self.timeout = timeout

    def _get(self, path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        params = dict(params)
        params["token"] = self.api_key
        url = f"{FINNHUB_BASE}{path}"
        r = requests.get(url, params=params, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def quote(self, symbol: str) -> Dict[str, Any]:
        return self._get("/quote", {"symbol": symbol})

    def candles(self, symbol: str, resolution: str, _from: int, to: int) -> Dict[str, Any]:
        return self._get("/stock/candle", {
            "symbol": symbol,
            "resolution": resolution,
            "from": _from,
            "to": to,
        })
