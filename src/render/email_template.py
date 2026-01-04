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
        th = "".join([f"<th style='text-align:left;padding:6px;border-bottom:1px solid #333'>{h}</th>" for h in header])
        trs = []
        for r in body:
            tds = "".join([f"<td style='padding:6px;border-bottom:1px solid #222'>{c}</td>" for c in r])
            trs.append(f"<tr>{tds}</tr>")
        return f"""
        <table style="border-collapse:collapse;width:100%;font-family:Arial,sans-serif;font-size:14px">
          <thead><tr>{th}</tr></thead>
          <tbody>{''.join(trs)}</tbody>
        </table>
        """

    market_rows = [["Symbol", "Last", "1D % (approx)", "Notes"]]
    for item in sections.get("market_pulse", []):
        market_rows.append([item["symbol"], item["last"], item["chg"], item["note"]])

    holdings_rows = [["Symbol", "Close", "Risk", "Reason"]]
    for s in sections.get("holdings", []):
        holdings_rows.append([s["symbol"], s["close"], s["risk"], s["reason"]])

    risky_rows = [["Symbol", "Close", "Risk", "Reason"]]
    for s in sections.get("risky", []):
        risky_rows.append([s["symbol"], s["close"], s["risk"], s["reason"]])

    triggered = sections.get("triggered", [])

    html = f"""
    <div style="font-family:Arial,sans-serif;line-height:1.4">
      <h2>{title}</h2>

      <h3>Market pulse</h3>
      {table(market_rows)}

      <h3>Your holdings (watchlist-based)</h3>
      {table(holdings_rows)}

      <h3>Risky watchlist</h3>
      {table(risky_rows)}

      <h3>Alerts triggered</h3>
      <ul>
        {''.join([f"<li><strong>{a['symbol']}</strong>: {a['risk']} — {a['reason']}</li>" for a in triggered]) or "<li><em>No alerts triggered</em></li>"}
      </ul>

      <p style="margin-top:18px;font-size:12px;color:#aaa">
        Automated digest using rule-based signals. Not investment advice.
      </p>
    </div>
    """

    subject = f"Stockshark Digest — {subject_dt.strftime('%a %b %d')}"
    return {"subject": subject, "html": html}
