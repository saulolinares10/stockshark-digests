from __future__ import annotations
from typing import Dict, Any, List
import os

from src.utils.config import load_yaml
from src.utils.dates import now_in_tz
from src.data.finnhub_client import FinnhubClient
from src.data.market import fetch_daily_history, fetch_quotes
from src.signals.scoring import compute_signals
from src.render.email_template import render_email
from src.notify.sendgrid_email import send_email

def _safe_pct_change(quote: Dict[str, Any]) -> float:
    try:
        c = float(quote.get("c"))
        pc = float(quote.get("pc"))
        if pc > 0:
            return (c / pc) - 1.0
    except Exception:
        pass
    return 0.0

def main() -> None:
    watchlists = load_yaml("configs/watchlists.yml")
    settings = load_yaml("configs/settings.yml")

    tz_name = settings["digest"]["timezone"]
    lookback_days = int(settings["digest"]["lookback_days"])
    th = settings["thresholds"]
    wording = settings["wording"]

    core = watchlists.get("core", [])
    conviction = watchlists.get("conviction", [])
    risky = watchlists.get("risky_watchlist", [])
    signal_etfs = watchlists.get("signals_etfs", [])

    market_symbols = list(dict.fromkeys(core + signal_etfs))

    client = FinnhubClient()

    quotes = fetch_quotes(client, market_symbols)
    market_pulse = []
    for s in market_symbols:
        q = quotes.get(s, {})
        chg = _safe_pct_change(q)
        last = q.get("c", "")
        note = "Risk-on proxy" if s in signal_etfs else "Core index"
        market_pulse.append({
            "symbol": s,
            "last": f"{float(last):.2f}" if isinstance(last, (int, float)) else str(last),
            "chg": f"{chg*100:.2f}%",
            "note": note,
        })

    def run_bucket(symbols: List[str]) -> List[Dict[str, str]]:
        out = []
        for s in symbols:
            hist = fetch_daily_history(client, s, lookback_days=lookback_days)
            if not hist:
                out.append({"symbol": s, "close": "n/a", "risk": "n/a", "reason": "No data returned"})
                continue

            sig = compute_signals(
    symbol=s,
    df=hist.df,
    trend_ma_days=int(th["trend_ma_days"]),
    momentum_days=int(th["momentum_days"]),
    drawdown_days=int(th["drawdown_days"]),
    drawdown_warn_pct=float(th["drawdown_warn_pct"]),
    drawdown_critical_pct=float(th["drawdown_critical_pct"]),
    vol_spike_multiplier=float(th["vol_spike_multiplier"]),
    require_conditions_for_warn=int(th.get("require_conditions_for_warn", 2)),
    vol_spike_is_info_only=bool(th.get("vol_spike_is_info_only", True)),
    momentum_warn_pct=float(th.get("momentum_warn_pct", -0.06)),
)

            if not sig:
                out.append({"symbol": s, "close": "n/a", "risk": "n/a", "reason": "Signal computation failed"})
                continue

            if sig.risk_level == "WARN":
                extra = f"{wording['warn_label']}: {wording['suggested_action_warn']}"
            elif sig.risk_level == "CRITICAL":
                extra = f"{wording['critical_label']}: {wording['suggested_action_critical']}"
            else:
                extra = "OK"

            out.append({
                "symbol": s,
                "close": f"{sig.last_close:.2f}",
                "risk": sig.risk_level,
                "reason": f"{sig.reason}. {extra}",
            })
        return out

    holdings = run_bucket(conviction)
    risky_out = run_bucket(risky)
    triggered = [x for x in (holdings + risky_out) if x["risk"] in ("WARN", "CRITICAL")]

    now_dt = now_in_tz(tz_name)
    email = render_email(
        subject_dt=now_dt,
        tz_name=tz_name,
        sections={
            "market_pulse": market_pulse,
            "holdings": holdings,
            "risky": risky_out,
            "triggered": triggered,
        },
    )

    if os.getenv("DRY_RUN", "0") == "1":
        print(email["subject"])
        print(email["html"][:1000])
        return

    send_email(subject=email["subject"], html=email["html"])

if __name__ == "__main__":
    main()
