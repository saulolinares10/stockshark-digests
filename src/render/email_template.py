from __future__ import annotations

from typing import List, Dict, Any
from datetime import datetime


def render_email(subject_dt: datetime, tz_name: str, sections: Dict[str, Any]) -> Dict[str, str]:
    title = f"Stockshark Digest — {subject_dt.strftime('%a %b %d, %Y %I:%M %p')} ({tz_name})"

    def table(rows: List[List[str]]) -> str:
        if not rows:
            return "<p><em>No data</em></p>"
        header = rows[0]
        body = rows[1:]
        th = "".join(
            [
                f"<th style='text-align:left;padding:8px;border-bottom:1px solid #333;white-space:nowrap'>{h}</th>"
                for h in header
            ]
        )
        trs = []
        for r in body:
            tds = "".join(
                [f"<td style='padding:8px;border-bottom:1px solid #222;vertical-align:top'>{c}</td>" for c in r]
            )
            trs.append(f"<tr>{tds}</tr>")
        return f"""
        <table style="border-collapse:collapse;width:100%;font-family:Arial,sans-serif;font-size:14px">
          <thead><tr>{th}</tr></thead>
          <tbody>{''.join(trs)}</tbody>
        </table>
        """

    # --- Market Pulse table ---
    market_rows = [["Symbol", "Last", "1D %", "Notes"]]
    for item in sections.get("market_pulse", []):
        market_rows.append([item["symbol"], item["last"], item["chg"], item["note"]])

    # --- Top Focus (bullets) ---
    top_focus = sections.get("top_focus", [])
    if top_focus:
        top_focus_html = "<ul>" + "".join(
            [
                f"<li><strong>{x['symbol']}</strong> — <strong>{x['risk']}</strong> — {x['reason']}</li>"
                for x in top_focus
            ]
        ) + "</ul>"
    else:
        top_focus_html = "<p><em>No high-priority alerts today.</em></p>"

    # --- Holdings table ---
    holdings_rows = [["Symbol", "Close", "Risk", "Summary"]]
    for s in sections.get("holdings", []):
        # Shorten a bit for readability
        summary = s.get("reason", "")
        holdings_rows.append([s.get("symbol", ""), s.get("close", ""), s.get("risk", ""), summary])

    # --- Risky Watchlist table ---
    risky_rows = [["Symbol", "Close", "Risk", "Summary"]]
    for s in sections.get("risky", []):
        summary = s.get("reason", "")
        risky_rows.append([s.get("symbol", ""), s.get("close", ""), s.get("risk", ""), summary])

    # --- Triggered alerts list (all) ---
    triggered = sections.get("triggered", [])
    triggered_html = ""
    if triggered:
        triggered_html = "<ul>" + "".join(
            [
                f"<li><strong>{a['symbol']}</strong>: {a['risk']} — {a['reason']}</li>"
                for a in triggered
            ]
        ) + "</ul>"
    else:
        triggered_html = "<p><em>No alerts triggered.</em></p>"

    html = f"""
    <div style="font-family:Arial,sans-serif;line-height:1.45;max-width:980px;margin:0 auto">
      <h2 style="margin-bottom:6px">{title}</h2>
      <p style="margin-top:0;color:#aaa;font-size:13px">
        Automated digest using rule-based signals. This may be wrong. Not investment advice.
      </p>

      <h3 style="margin-top:18px">Top focus today</h3>
      {top_focus_html}

      <h3 style="margin-top:18px">Market pulse</h3>
      {table(market_rows)}

      <h3 style="margin-top:18px">Your holdings (watchlist-based)</h3>
      {table(holdings_rows)}

      <h3 style="margin-top:18px">Risky watchlist</h3>
      {table(risky_rows)}

      <h3 style="margin-top:18px">All alerts triggered</h3>
      {triggered_html}

      <hr style="margin-top:22px;border:0;border-top:1px solid #222" />
      <p style="margin-top:10px;font-size:12px;color:#888">
        Tip: Add a Gmail filter to prevent these from landing in Spam.
      </p>
    </div>
    """

    subject = f"Stockshark Digest — {subject_dt.strftime('%a %b %d')}"
    return {"subject": subject, "html": html}

