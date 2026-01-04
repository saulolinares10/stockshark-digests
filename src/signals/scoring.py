from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import pandas as pd
from src.signals.indicators import sma, daily_range, drawdown_from_recent_high, slope

@dataclass
class SignalResult:
    symbol: str
    last_close: float
    risk_level: str
    reason: str

def compute_signals(
    symbol: str,
    df: pd.DataFrame,
    trend_ma_days: int,
    momentum_days: int,
    drawdown_days: int,
    drawdown_warn_pct: float,
    drawdown_critical_pct: float,
    vol_spike_multiplier: float,
) -> Optional[SignalResult]:
    if df is None or df.empty:
        return None

    close = df["c"]
    last_close = float(close.iloc[-1])

    ma = sma(close, trend_ma_days)
    last_ma = float(ma.iloc[-1]) if not pd.isna(ma.iloc[-1]) else last_close
    above = last_close >= last_ma
    ma_s = slope(ma.dropna(), window=min(12, len(ma.dropna())))

    # momentum: percent change over momentum_days
    momentum = 0.0
    if len(close) > momentum_days:
        momentum = (last_close / float(close.iloc[-1 - momentum_days]) - 1.0)

    dd = drawdown_from_recent_high(close, drawdown_days)

    rng = daily_range(df).tail(20)
    vol_spike = False
    if len(rng) >= 10:
        avg_rng = float(rng.mean())
        today_rng = float(rng.iloc[-1])
        vol_spike = avg_rng > 0 and (today_rng / avg_rng) >= vol_spike_multiplier

    reasons = []
    risk = "OK"

    if (not above) and (ma_s < 0):
        risk = "WARN"
        reasons.append("Price below trend MA and trend is weakening")

    if dd >= drawdown_warn_pct:
        risk = "WARN"
        reasons.append(f"Drawdown {dd:.1%} from recent {drawdown_days}D high")

    if dd >= drawdown_critical_pct:
        risk = "CRITICAL"
        reasons.append("Drawdown reached critical threshold")

    if vol_spike and risk != "CRITICAL":
        risk = "WARN"
        reasons.append("Volatility spike vs recent average")

    if risk == "OK" and momentum < -0.08:
        risk = "WARN"
        reasons.append("Short-term momentum is notably negative")

    reason = "; ".join(reasons) if reasons else "No major risk flags from the configured rules"
    return SignalResult(symbol=symbol, last_close=last_close, risk_level=risk, reason=reason)
