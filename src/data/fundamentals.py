from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from src.data.finnhub_client import FinnhubClient

@dataclass
class FundamentalSnapshot:
    symbol: str
    name: str
    industry: str
    market_cap: Optional[float]

    # Valuation
    pe_ttm: Optional[float]
    ps_ttm: Optional[float]
    ev_ebitda: Optional[float]

    # Profitability (may be missing for some)
    gross_margin: Optional[float]
    operating_margin: Optional[float]
    net_margin: Optional[float]

    # Growth
    revenue_growth_yoy: Optional[float]
    eps_growth_yoy: Optional[float]

    # Leverage
    debt_to_equity: Optional[float]

    stance: str
    stance_reason: str


def _get_num(metric: Dict[str, Any], keys: Tuple[str, ...]) -> Optional[float]:
    for k in keys:
        v = metric.get(k)
        if isinstance(v, (int, float)):
            return float(v)
    return None


def score_fundamentals(symbol: str, profile: Dict[str, Any], fin: Dict[str, Any]) -> FundamentalSnapshot:
    metric = (fin or {}).get("metric", {}) or {}

    name = profile.get("name") or symbol
    industry = profile.get("finnhubIndustry") or ""
    market_cap = profile.get("marketCapitalization")
    market_cap = float(market_cap) if isinstance(market_cap, (int, float)) else None

    pe_ttm = _get_num(metric, ("peTTM", "pe_ttm"))
    ps_ttm = _get_num(metric, ("psTTM", "ps_ttm"))
    ev_ebitda = _get_num(metric, ("evEbitdaTTM", "ev_ebitda_ttm", "evEbitdaAnnual"))

    gross_margin = _get_num(metric, ("grossMarginTTM", "grossMarginAnnual"))
    operating_margin = _get_num(metric, ("operatingMarginTTM", "operatingMarginAnnual"))
    net_margin = _get_num(metric, ("netMarginTTM", "netMarginAnnual"))

    revenue_growth_yoy = _get_num(metric, ("revenueGrowthTTM", "revenueGrowthAnnual", "revenueGrowth5Y"))
    eps_growth_yoy = _get_num(metric, ("epsGrowthTTM", "epsGrowthAnnual", "epsGrowth5Y"))

    debt_to_equity = _get_num(metric, ("totalDebtToEquityAnnual", "totalDebtToEquityTTM", "debtToEquity"))

    # ---- Simple rule-based scoring ----
    score = 0
    reasons = []

    # Profitability
    if operating_margin is not None:
        if operating_margin >= 0.15:
            score += 1
            reasons.append("Strong operating margin")
        elif operating_margin < 0.05:
            score -= 1
            reasons.append("Thin operating margin")

    if net_margin is not None:
        if net_margin >= 0.10:
            score += 1
            reasons.append("Healthy net margin")
        elif net_margin < 0.03:
            score -= 1
            reasons.append("Low net margin")

    # Growth
    if revenue_growth_yoy is not None:
        if revenue_growth_yoy >= 0.10:
            score += 1
            reasons.append("Solid revenue growth")
        elif revenue_growth_yoy < 0.03:
            score -= 1
            reasons.append("Weak revenue growth")

    if eps_growth_yoy is not None:
        if eps_growth_yoy >= 0.10:
            score += 1
            reasons.append("Solid EPS growth")
        elif eps_growth_yoy < 0.0:
            score -= 1
            reasons.append("Negative EPS growth")

    # Valuation (very rough; depends on sector)
    if pe_ttm is not None:
        if pe_ttm >= 45:
            score -= 1
            reasons.append("Stretched P/E")
        elif pe_ttm <= 18:
            score += 1
            reasons.append("Reasonable P/E")

    if ps_ttm is not None and ps_ttm >= 15:
        score -= 1
        reasons.append("High P/S (rich valuation)")

    # Leverage
    if debt_to_equity is not None and debt_to_equity >= 2.0:
        score -= 1
        reasons.append("High leverage (debt/equity)")

    # Map to stance
    if score >= 2:
        stance = "Healthy"
    elif score == 1:
        stance = "Mixed"
    elif score == 0:
        stance = "Neutral"
    else:
        stance = "Stretched/Weak"

    stance_reason = ", ".join(reasons) if reasons else "Limited fundamental metrics available"
    return FundamentalSnapshot(
        symbol=symbol,
        name=name,
        industry=industry,
        market_cap=market_cap,
        pe_ttm=pe_ttm,
        ps_ttm=ps_ttm,
        ev_ebitda=ev_ebitda,
        gross_margin=gross_margin,
        operating_margin=operating_margin,
        net_margin=net_margin,
        revenue_growth_yoy=revenue_growth_yoy,
        eps_growth_yoy=eps_growth_yoy,
        debt_to_equity=debt_to_equity,
        stance=stance,
        stance_reason=stance_reason,
    )


def fetch_fundamentals(client: FinnhubClient, symbol: str) -> Optional[FundamentalSnapshot]:
    try:
        profile = client.company_profile2(symbol)
        fin = client.company_basic_financials(symbol)
        return score_fundamentals(symbol, profile, fin)
    except Exception:
        return None
