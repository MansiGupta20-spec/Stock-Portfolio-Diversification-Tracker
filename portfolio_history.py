"""
portfolio_history.py
Calculates the WHOLE portfolio's total value for each of the last
~22 trading days (1 month), by combining historical prices for
every holding.

ASSUMPTION (label this clearly in your demo/report):
  Quantities are assumed CONSTANT across the month — this does not
  account for the user buying/selling mid-month. That's a reasonable
  MVP simplification; tracking quantity changes over time would need
  DB snapshots (portfolio_snapshots table), which is a bigger feature.
"""

import yfinance as yf
import pandas as pd


def portfolio_value_trend(holdings, period="1mo"):
    """
    holdings: list of dicts like [{"ticker": "TCS.NS", "quantity": 5}, ...]
    period: "1mo", "5d", "6mo", "1y" etc. (yfinance format)

    Returns: [{"date": "2026-07-24", "value": 97500.0}, ...]
    """
    tickers = [h["ticker"] for h in holdings]
    quantities = {h["ticker"]: h["quantity"] for h in holdings}

    # Downloads Close price for ALL tickers at once — much faster
    # than fetching one at a time.
    raw = yf.download(tickers, period=period, progress=False)["Close"]

    # yfinance returns a Series (not DataFrame) if there's only 1 ticker
    if isinstance(raw, pd.Series):
        raw = raw.to_frame(name=tickers[0])

    raw = raw.ffill().dropna(how="all")  # fill small gaps, drop empty rows

    portfolio_value = pd.Series(0.0, index=raw.index)
    for ticker in tickers:
        if ticker in raw.columns:
            portfolio_value += raw[ticker].fillna(0) * quantities.get(ticker, 0)

    return [
        {"date": str(date.date()), "value": round(value, 2)}
        for date, value in portfolio_value.items()
    ]


if __name__ == "__main__":
    # Run locally (needs internet): python portfolio_history.py
    from sample_data import sample_holdings

    trend = portfolio_value_trend(sample_holdings)

    print(f"Portfolio value — last {len(trend)} trading days:")
    for row in trend:
        print(f"  {row['date']}: Rs.{row['value']}")

    if trend:
        change = trend[-1]["value"] - trend[0]["value"]
        change_pct = round((change / trend[0]["value"]) * 100, 2) if trend[0]["value"] else 0
        print(f"\nChange over the month: Rs.{round(change,2)} ({change_pct}%)")