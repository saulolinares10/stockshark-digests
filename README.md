# stockshark-digests

Automated email digests for US market pulse + your holdings + risky watchlist.

## What it does
- Scheduled GitHub Action runs on weekdays
- Pulls market/price data
- Computes simple risk flags (trend break, drawdown, volatility spike)
- Emails you an HTML digest

## Setup
You need these GitHub Secrets:
- FINNHUB_API_KEY
- SENDGRID_API_KEY
- TO_EMAIL
- FROM_EMAIL
