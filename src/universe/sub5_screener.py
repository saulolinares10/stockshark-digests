from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import re

from src.data.market import fetch_daily_history
from src.data.fundamentals import fetch_fundamentals
from src.data.news import fetch_cnbc_mentions, fetch_web_buzz
from src.data.finnhub_client import FinnhubClient


INNOVATION_KEYWORDS = [
    "fda", "phase", "approval", "patent", "ai", "breakthrough", "partnership", "contract",
    "doe", "dod", "nasa", "chip", "semiconductor", "battery", "clinical", "trial",
    "launch", "new product", "acquisition", "merger",
]


def _kw_score(headlines: List[str]) -> int:
    text = " ".join(headlines).lower()
    score = 0
    for kw in INNOVATION_KEYWORDS:
        if kw in text:
            score += 1
    return score


def _fund_score(f: Optional[object]) -> Tuple[int, str]:
    # f is FundamentalSnapshot if present (from your fundamentals module)
    if not f:
        return (0, "No fundamentals data")

    s = 0
    reasons = []

    # Growth
    rg = getattr(f, "revenue_growth_yoy", None)
    if isinstance(rg, (int, float)):
        if rg >= 0.10:
            s += 2; reasons.append("Rev growth strong")
        elif rg >= 0.03:
            s += 1; reasons.append("Rev growth positive")
        else:
            s -= 1; reasons.append("Rev growth weak")

    # Profitability
    om = getattr(f, "operating_margin", None)
    if isinstance(om, (int, float)):
        if om >= 0.10:
            s += 1; reasons.append("Op margin healthy")
        elif om < 0.0:
            s -= 1; reasons.append("Op margin negative")

    # Leverage
    d2e = getattr(f, "debt_to_equity", None)
    if isinstance(d2e, (int, float)):
        if d2e >= 2.0:
            s -= 1; reasons.append("High leverage")
        elif d2e <= 0.8:
            s += 1; reasons.append("Leverage ok")

    return s, ", ".join(reasons) if reasons else "Limited fundamentals"


def build_sub5_candidates(
    client: FinnhubClient,
    symbols: List[str],
    max_out: int = 10,
) -> List[Dict[str, str]]:
    candidates: List[Dict[str, str]] = []

    for sym in symbols:
        # Fetch last ~30 days price from your existing source
        hist = fetch_daily_history(client, sym, lookback_days=45)
        if not hist or hist.df is None or hist.df.empty:
            continue

        close = hist.df["c"]
        price = float(close.iloc[-1])
        if price >= 5.0:
            continue

        # Momentum proxy (30 trading days-ish)
        if len(close) < 25:
            continue
        mom = (price / float(close.iloc[-25]) - 1.0)

        # Light liquidity proxy: need volume column? If you have volume in df, use it; otherwise skip.
        # If df has 'v', prefer it:
        vol_ok = True
        if "v" in hist.df.columns:
            avg_vol = float(hist.df["v"].tail(20).mean())
            vol_ok = avg_vol >= 300_000  # tunable
        if not vol_ok:
            continue

        # Fundamentals score
        f = fetch_fundamentals(client, sym)
        fund_s, fund_reason = _fund_score(f)

        # News score
        cnbc = fetch_cnbc_mentions(sym, max_items=5)
        buzz = fetch_web_buzz(sym, max_items=5)
        headlines = [h.title for h in (cnbc + buzz)]
        news_s = min(5, len(headlines))  # activity
        kw_s = _kw_score(headlines)

        # Total score (weights are intentionally simple)
        total = (2 * fund_s) + news_s + kw_s

        # Require at least some positive signal:
        if total < 3:
            continue

        reason_parts = []
        if mom > 0:
            reason_parts.append(f"{mom*100:.1f}% ~1M momentum")
        if fund_reason:
            reason_parts.append(fund_reason)
        if len(cnbc) > 0:
            reason_parts.append(f"CNBC:{len(cnbc)}")
        if len(buzz) > 0:
            reason_parts.append(f"News:{len(buzz)}")
        if kw_s > 0:
            reason_parts.append(f"Innovation keywords:{kw_s}")

        candidates.append({
            "symbol": sym,
            "price": f"{price:.2f}",
            "score": str(total),
            "reason": " | ".join(reason_parts),
        })

    # sort by score desc, then lowest price (optional)
    candidates.sort(key=lambda x: (int(x["score"]), -float(x["price"])), reverse=True)
    return candidates[:max_out]
