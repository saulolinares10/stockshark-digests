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

    def bullets(items: List[str]) -> str:
        if not items:
            return "<p><em>None</em></p>"
        return "<ul style='margin:8px 0 0 18px'>" + "".join([f"<li>{x}</li>" for x in items]) + "</ul>"

    # --- Market Pulse ---
    market_rows = [["Symbol", "Last", "1D %", "Notes"]]
    for item in sections.get("market_pulse", []):
        market_rows.append([item["symbol"], item["last"], item["chg"], item["note"]])

    # --- Top Focus ---
    top_focus = sections.get("top_focus", [])
    if top_focus:
        top_focus_html = "<ul style='margin:8px 0 0 18px'>" + "".join(
            [
                f"<li><strong>{x.get('symbol','')}</strong> — <strong>{x.get('risk','')}</strong> — {x.get('reason','')}</li>"
                for x in top_focus
            ]
        ) + "</ul>"
    else:
        top_focus_html = "<p><em>No high-priority alerts today.</em></p>"

    # --- Holdings ---
    holdings_rows = [["Symbol", "Close", "Risk", "Summary"]]
    for s in sections.get("holdings", []):
        holdings_rows.append([s.get("symbol", ""), s.get("close", ""), s.get("risk", ""), s.get("reason", "")])

    # --- Risky Watchlist ---
    risky_rows = [["Symbol", "Close", "Risk", "Summary"]]
    for s in sections.get("risky", []):
        risky_rows.append([s.get("symbol", ""), s.get("close", ""), s.get("risk", ""), s.get("reason", "")])

    # --- Research Pack ---
    research_symbols = sections.get("research_symbols", [])
    links_by_symbol = sections.get("links_by_symbol", {})
    news_by_symbol = sections.get("news_by_symbol", {})
    fundamentals_by_symbol = sections.get("fundamentals_by_symbol", {})
    instagram_handle = sections.get("instagram_handle", "")

    cards = []
    for sym in research_symbols:
        links = links_by_symbol.get(sym, {}) or {}
        f = fundamentals_by_symbol.get(sym, {}) or {}
        n = news_by_symbol.get(sym, {}) or {}
        cnbc_items = n.get("cnbc", []) or []
        buzz_items = n.get("buzz", []) or []

        links_html = " | ".join(
            [f"<a href='{url}' target='_blank' rel='noopener noreferrer'>{name}</a>" for name, url in links.items()]
        ) or "<em>No links</em>"

        fundamentals_html = f"""
          <div style="font-size:13px;color:#ddd;margin-top:8px">
            <div><strong>{f.get('name', sym)}</strong> {('— ' + f.get('industry','')) if f.get('industry') else ''}</div>
            <div style="margin-top:6px"><strong>Fundamental stance:</strong> {f.get('stance','n/a')}
              <span style="color:#aaa"> — {f.get('stance_reason','')}</span>
            </div>
            <div style="margin-top:6px">
              <strong>Valuation:</strong> P/E {f.get('pe','n/a')}, P/S {f.get('ps','n/a')}, EV/EBITDA {f.get('ev_ebitda','n/a')}
            </div>
            <div style="margin-top:4px">
              <strong>Margins:</strong> Op {f.get('op_margin','n/a')}, Net {f.get('net_margin','n/a')}
            </div>
            <div style="margin-top:4px">
              <strong>Growth:</strong> Rev {f.get('rev_growth','n/a')}, EPS {f.get('eps_growth','n/a')}
            </div>
            <div style="margin-top:4px">
              <strong>Leverage:</strong> Debt/Equity {f.get('debt_eq','n/a')}
            </div>
          </div>
        """

        def news_list(items: List[Dict[str, str]]) -> str:
            if not items:
                return "<p style='margin:6px 0 0 0;color:#888'><em>No items found.</em></p>"
            lis = []
            for it in items[:5]:
                t = it.get("title", "")
                url = it.get("link", "")
                src = it.get("source", "")
                src_txt = f" <span style='color:#888'>({src})</span>" if src else ""
                if t and url:
                    lis.append(f"<li><a href='{url}' target='_blank' rel='noopener noreferrer'>{t}</a>{src_txt}</li>")
            return "<ul style='margin:6px 0 0 18px'>" + "".join(lis) + "</ul>"

        cards.append(f"""
          <div style="margin-bottom:14px;padding:12px;border:1px solid #222;border-radius:10px">
            <div style="font-size:16px;font-weight:bold">{sym}</div>
            <div style="font-size:13px;margin-top:6px">{links_html}</div>
            {fundamentals_html}

            <div style="margin-top:10px"><strong>CNBC mentions</strong></div>
            {news_list(cnbc_items)}

            <div style="margin-top:10px"><strong>Web buzz</strong></div>
            {news_list(buzz_items)}
          </div>
        """)

    research_section_html = "".join(cards) if cards else "<p><em>No research pack today.</em></p>"

    # --- Triggered alerts ---
    triggered = sections.get("triggered", [])
    if triggered:
        triggered_html = "<ul style='margin:8px 0 0 18px'>" + "".join(
            [f"<li><strong>{a['symbol']}</strong>: {a['risk']} — {a['reason']}</li>" for a in triggered]
        ) + "</ul>"
    else:
        triggered_html = "<p><em>No alerts triggered.</em></p>"

    instagram_note = ""
    if instagram_handle:
        instagram_note = f"<p style='margin-top:10px;font-size:12px;color:#888'>Instagram source link: @{instagram_handle}</p>"

    html = f"""
    <div style="font-family:Arial,sans-serif;line-height:1.45;max-width:980px;margin:0 auto">
      <h2 style="margin-bottom:6px">{title}</h2>
      <p style="margin-top:0;color:#aaa;font-size:13px">
        Automated digest using rule-based signals + fundamentals + news. This may be wrong. Not investment advice.
      </p>

      <h3 style="margin-top:18px">Top focus today</h3>
      {top_focus_html}

      <h3 style="margin-top:18px">Market pulse</h3>
      {table(market_rows)}

      <h3 style="margin-top:18px">Research pack (fundamentals + links + news)</h3>
      {research_section_html}
      {instagram_note}

      <h3 style="margin-top:18px">Your holdings</h3>
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
