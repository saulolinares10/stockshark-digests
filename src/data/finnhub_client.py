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
        
    def company_profile2(self, symbol: str) -> Dict[str, Any]:
        return self._get("/stock/profile2", {"symbol": symbol})

    def company_basic_financials(self, symbol: str) -> Dict[str, Any]:
        # Contains "metric" dict with many ratios + per-share metrics, etc.
        return self._get("/stock/metric", {"symbol": symbol, "metric": "all"})

    def company_news(self, symbol: str, _from: str, to: str) -> Any:
        # _from, to format YYYY-MM-DD
        return self._get("/company-news", {"symbol": symbol, "from": _from, "to": to})

    def quote(self, symbol: str) -> Dict[str, Any]:
        return self._get("/quote", {"symbol": symbol})

    def candles(self, symbol: str, resolution: str, _from: int, to: int) -> Dict[str, Any]:
        return self._get("/stock/candle", {
            "symbol": symbol,
            "resolution": resolution,
            "from": _from,
            "to": to,
        })
