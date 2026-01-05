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
            [f"<th style='text-align:left;padding:8px;border-bottom:1px solid #ccc'>{h}</th>" for h in header]
        )
        trs = []
        for r in body:
            tds = "".join(
                [f"<td style='padding:8px;border-bottom:1px solid #eee;vertical-align:top'>{c}</td>" for c in r]
            )
            trs.append(f"<tr>{tds}</tr>")
        return f"""
        <table style="border-collapse:collapse;width:100%;font-family:Arial,sans-serif;font-size:14px;color:#000">
          <thead><tr>{th}</tr></thead>
          <tbody>{''.join(trs)}</tbody>
        </table>
        """

    # -------- Market pulse --------
    market_rows = [["Symbol", "Last", "1D %", "Notes"]]
    for item in sections.get("market_pulse", []):
        market_rows.append([item["symbol"], item["last"], item["chg"], item["note"]])

    # -------- Top focus --------
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

    # -------- Holdings --------
    holdings_rows = [["Symbol", "Close", "Risk", "Summary"]]
    for s in sections.get("holdings", []):
        holdings_rows.append([s["symbol"], s["close"], s["risk"], s["reason"]])

    # -------- Risky watchlist --------
    risky_rows = [["Symbol", "Close", "Risk", "Summary"]]
    for s in sections.get("risky", []):
        risky_rows.append([s["symbol"], s["close"], s["risk"], s["reason"]])

    # -------- Research pack --------
    research_symbols = sections.get("research_symbols", [])
    links_by_symbol = sections.get("links_by_symbol", {})
    fundamentals_by_symbol = sections.get("fundamentals_by_symbol", {})
    news_by_symbol = sections.get("news_by_symbol", {})

    cards = []
    for sym in research_symbols:
        links = links_by_symbol.get(sym, {})
        f = fundamentals_by_symbol.get(sym, {})
        news = news_by_symbol.get(sym, {})

        links_html = " | ".join(
            [f"<a href='{u}' target='_blank'>{k}</a>" for k, u in links.items()]
        )

        fundamentals_html = f"""
        <div style="margin-top:8px;font-size:14px;color:#000">
          <div><strong>{f.get('name', sym)}</strong> — {f.get('industry','')}</div>
          <div style="margin-top:6px">
            <strong>Fundamental stance:</strong> {f.get('stance','n/a')}
            <span style="color:#666"> — {f.get('stance_reason','')}</span>
          </div>
          <div style="margin-top:6px"><strong>Valuation:</strong>
            P/E {f.get('pe','n/a')}, P/S {f.get('ps','n/a')}, EV/EBITDA {f.get('ev_ebitda','n/a')}
          </div>
          <div><strong>Margins:</strong>
            Op {f.get('op_margin','n/a')}, Net {f.get('net_margin','n/a')}
          </div>
          <div><strong>Growth:</strong>
            Rev {f.get('rev_growth','n/a')}, EPS {f.get('eps_growth','n/a')}
          </div>
          <div><strong>Leverage:</strong>
            Debt/Equity {f.get('debt_eq','n/a')}
          </div>
        </div>
        """

        def news_list(items: List[Dict[str, str]]) -> str:
            if not items:
                return "<p style='color:#666'><em>No recent items.</em></p>"
            return "<ul>" + "".join(
                [f"<li><a href='{n['link']}' target='_blank'>{n['title']}</a></li>" for n in items[:5]]
            ) + "</ul>"

        cards.append(f"""
        <div style="margin-bottom:16px;padding:12px;border:1px solid #ddd;border-radius:8px">
          <div style="font-size:16px;font-weight:bold">{sym}</div>
          <div style="margin-top:6px;font-size:13px">{links_html}</div>
          {fundamentals_html}
          <div style="margin-top:10px"><strong>News</strong></div>
          {news_list(news.get("cnbc", []))}
        </div>
        """)

    research_html = "".join(cards) if cards else "<p><em>No research today.</em></p>"

    # -------- Sub-$5 stocks --------
    penny = sections.get("sub5", [])
    if penny:
        penny_html = table(
            [["Symbol", "Price", "Reason"]] +
            [[x["symbol"], x["price"], x["reason"]] for x in penny]
        )
    else:
        penny_html = "<p><em>No candidates today.</em></p>"

    html = f"""
    <div style="font-family:Arial,sans-serif;color:#000;max-width:980px;margin:0 auto">
      <h2>{title}</h2>
      <p style="color:#555;font-size:13px">
        Automated digest using technical + fundamental signals. Not investment advice.
      </p>

      <h3>Top focus today</h3>
      {top_focus_html}

      <h3>Market pulse</h3>
      {table(market_rows)}

      <h3>Research pack</h3>
      {research_html}

      <h3>Your holdings</h3>
      {table(holdings_rows)}

      <h3>Risky watchlist</h3>
      {table(risky_rows)}

      <h3>Sub-$5 stocks with potential</h3>
      {penny_html}
    </div>
    """

    return {
        "subject": f"Stockshark Digest — {subject_dt.strftime('%a %b %d')}",
        "html": html,
    }

