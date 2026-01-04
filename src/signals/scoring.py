def compute_signals(
    symbol: str,
    df: pd.DataFrame,
    trend_ma_days: int,
    momentum_days: int,
    drawdown_days: int,
    drawdown_warn_pct: float,
    drawdown_critical_pct: float,
    vol_spike_multiplier: float,
    require_conditions_for_warn: int = 2,
    vol_spike_is_info_only: bool = True,
    momentum_warn_pct: float = -0.06,
) -> Optional[SignalResult]:
    if df is None or df.empty:
        return None

    close = df["c"]
    last_close = float(close.iloc[-1])

    ma = sma(close, trend_ma_days)
    last_ma = float(ma.iloc[-1]) if not pd.isna(ma.iloc[-1]) else last_close
    above = last_close >= last_ma
    ma_s = slope(ma.dropna(), window=min(12, len(ma.dropna())))

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

    # Conditions
    conds = []
    if (not above) and (ma_s < 0):
        conds.append("trend_break")
    if dd >= drawdown_warn_pct:
        conds.append("drawdown")
    if momentum <= momentum_warn_pct:
        conds.append("momentum")
    if vol_spike:
        conds.append("vol_spike")

    # Risk determination
    reasons = []
    risk = "OK"

    if dd >= drawdown_critical_pct:
        risk = "CRITICAL"
        reasons.append(f"Drawdown {dd:.1%} from recent {drawdown_days}D high (critical)")
        if "trend_break" in conds:
            reasons.append("Trend is weakening (below MA + negative slope)")
        if momentum <= momentum_warn_pct:
            reasons.append(f"Momentum {momentum:.1%} over {momentum_days}D")
        if vol_spike:
            reasons.append("Volatility spike vs recent average")
        reason = "; ".join(reasons)
        return SignalResult(symbol=symbol, last_close=last_close, risk_level=risk, reason=reason)

    # WARN only if enough conditions (reduces noise)
    warn_conds = [c for c in conds if not (vol_spike_is_info_only and c == "vol_spike")]
    if len(warn_conds) >= require_conditions_for_warn:
        risk = "WARN"
        if "trend_break" in warn_conds:
            reasons.append("Trend weakening (below MA + negative slope)")
        if "drawdown" in warn_conds:
            reasons.append(f"Drawdown {dd:.1%} from recent {drawdown_days}D high")
        if "momentum" in warn_conds:
            reasons.append(f"Momentum {momentum:.1%} over {momentum_days}D")

    # INFO note (vol spike alone)
    if risk == "OK" and vol_spike:
        risk = "OK"
        reasons.append("Volatility spike (info)")

    reason = "; ".join(reasons) if reasons else "No major risk flags from the configured rules"
    return SignalResult(symbol=symbol, last_close=last_close, risk_level=risk, reason=reason)
