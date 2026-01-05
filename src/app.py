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

from src.data.fundamentals import fetch_fundamentals
from src.data.news import fetch_cnbc_mentions, fetch_web_buzz
from src.render.research_links import research_links


def _safe_pct_change(quote: Dict[str, Any]) -> float:
    try:
        c = float(quote.get("c"))
        pc = float(quote.get("pc"))
        if pc > 0:
            return (c / pc) - 1.0
    except Exception:
        pass
    return 0.0


def _action_label(risk_level: str) -> str:
    if risk_level == "CRITICAL":
        return "Trim candidate"
    if risk_level == "WARN":
        return "Watch closely"
    return "No action"


def _sort_focus(items: List[Dict[str, str]]) -> List[Dict[str, str]]:
    priority = {"CRITICAL": 0, "WARN": 1, "OK": 2}
    return sorted(items, key=lambda x: priority.get(x.get("risk", "OK"), 9))


def main() -> None:
    watchlists = load_yaml("configs/watchlists.yml")
    settings = load_yaml("configs/settings.yml")

    tz_name = settings["digest"]["timezone"]
    lookback_days = int(settings["digest"]["lookback_days"])
    th = settings["thresholds"]
    wording = settings["wording"]

    # Optional: put an instagram handle in settings.yml:
    # social:
    #   instagram_handle: "stocksharknews"
    instagram_handle = (settings.get("social", {}) or {}).get("instagram_handle", "")

    core = watchlists.get("core", [])
    conviction = watchlists.get("conviction", [])
    risky = watchlists.get("risky_watchlist", [])
    signal_etfs = watchlists.get("signals_etfs", [])

    market_symbols = list(dict.fromkeys(core + signal_etfs))
    client = FinnhubClient()

    # ------------------ Market pulse ------------------
    quotes = fetch_quotes(client, market_symbols)
    market_pulse: List[Dict[str, str]] = []
    for s in market_symbols:
        q = quotes.get(s, {})
        chg = _safe_pct_change(q)
        last = q.get("c", "")
        note = "Risk-on proxy" if s in signal_etfs else "Core index"
        market_pulse.append(
            {
                "symbol": s,
                "last": f"{float(last):.2f}" if isinstance(last, (int, float)) else str(last),
                "chg": f"{chg * 100:.2f}%",
                "note": note,
            }
        )

    # ------------------ Signals ------------------
    def run_bucket(symbols: List[str]) -> List[Dict[str, str]]:
        out: List[Dict[str, str]] = []
        for s in symbols:
            hist = fetch_daily_history(client, s, lookback_days=lookback_days)
            if not hist:
                out.append({"symbol": s, "close": "n/a", "risk": "n/a", "reason": "No price history returned"})
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

            action = _action_label(sig.risk_level)
            out.append(
                {
                    "symbol": s,
                    "close": f"{sig.last_close:.2f}",
                    "risk": sig.risk_level,
                    "reason": f"{sig.reason}. Suggested: {action}. {extra}",
                }
            )
        return out

    holdings = run_bucket(conviction)
    risky_out = run_bucket(risky)

    triggered = [x for x in (holdings + risky_out) if x.get("risk") in ("WARN", "CRITICAL")]
    top_focus = _sort_focus(triggered)[:5]

    # ------------------ Research pack symbols ------------------
    flagged_risky = [x["symbol"] for x in risky_out if x.get("risk") in ("WARN", "CRITICAL")]
    research_symbols = list(dict.fromkeys(conviction + flagged_risky))

    # ------------------ Fundamentals + News + Links ------------------
    fundamentals_by_symbol: dict[str, dict[str, str]] = {}
    links_by_symbol: dict[str, dict[str, str]] = {}
    news_by_symbol: dict[str, dict[str, list[dict[str, str]]]] = {}

    for sym in research_symbols:
        # Links (include Instagram profile link if set)
        links_by_symbol[sym] = research_links(sym, instagram_handle=instagram_handle or None)

        # Fundamentals (Finnhub)
        f = fetch_fundamentals(client, sym)
        if f:
            fundamentals_by_symbol[sym] = {
                "name": f.name,
                "industry": f.industry,
                "market_cap": f"{f.market_cap:.1f}B" if isinstance(f.market_cap, (int, float)) else "n/a",
                "pe": f"{f.pe_ttm:.1f}" if f.pe_ttm is not None else "n/a",
                "ps": f"{f.ps_ttm:.1f}" if f.ps_ttm is not None else "n/a",
                "ev_ebitda": f"{f.ev_ebitda:.1f}" if f.ev_ebitda is not None else "n/a",
                "op_margin": f"{f.operating_margin*100:.1f}%" if f.operating_margin is not None else "n/a",
                "net_margin": f"{f.net_margin*100:.1f}%" if f.net_margin is not None else "n/a",
                "rev_growth": f"{f.revenue_growth_yoy*100:.1f}%" if f.revenue_growth_yoy is not None else "n/a",
                "eps_growth": f"{f.eps_growth_yoy*100:.1f}%" if f.eps_growth_yoy is not None else "n/a",
                "debt_eq": f"{f.debt_to_equity:.2f}" if f.debt_to_equity is not None else "n/a",
                "stance": f.stance,
                "stance_reason": f.stance_reason,
            }
        else:
            fundamentals_by_symbol[sym] = {
                "name": sym,
                "industry": "",
                "market_cap": "n/a",
                "pe": "n/a",
                "ps": "n/a",
                "ev_ebitda": "n/a",
                "op_margin": "n/a",
                "net_margin": "n/a",
                "rev_growth": "n/a",
                "eps_growth": "n/a",
                "debt_eq": "n/a",
                "stance": "n/a",
                "stance_reason": "No fundamentals returned",
            }

        # News buckets (Google News RSS)
        # - CNBC-only
        # - General web buzz
        try:
            cnbc = fetch_cnbc_mentions(sym, max_items=int((settings.get("news", {}) or {}).get("max_items", 4)))
        except Exception:
            cnbc = []
        try:
            buzz = fetch_web_buzz(sym, max_items=int((settings.get("news", {}) or {}).get("max_items", 4)))
        except Exception:
            buzz = []

        news_by_symbol[sym] = {
            "cnbc": [{"title": h.title, "link": h.link, "source": h.source} for h in cnbc],
            "buzz": [{"title": h.title, "link": h.link, "source": h.source} for h in buzz],
        }

    # ------------------ Render + send ------------------
    now_dt = now_in_tz(tz_name)
    email = render_email(
        subject_dt=now_dt,
        tz_name=tz_name,
        sections={
            "market_pulse": market_pulse,
            "top_focus": top_focus,
            "holdings": holdings,
            "risky": risky_out,
            "triggered": triggered,
            "research_symbols": research_symbols,
            "links_by_symbol": links_by_symbol,
            "news_by_symbol": news_by_symbol,
            "fundamentals_by_symbol": fundamentals_by_symbol,
            "instagram_handle": instagram_handle,
        },
    )

    if os.getenv("DRY_RUN", "0") == "1":
        print(email["subject"])
        print(email["html"][:3000])
        return

    send_email(subject=email["subject"], html=email["html"])


if __name__ == "__main__":
    main()
