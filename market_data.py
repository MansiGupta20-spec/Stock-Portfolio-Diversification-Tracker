"""
data_fetch.py
(Corresponds to market_data.py in your teammate's module structure —
this is your REUSED yfinance wrapper from the old project, kept
under this filename for consistency with earlier work.)

Given a ticker, returns current price + sector using yfinance.
Output feeds directly into calculations.py — quantity/purchase_price
come from the user/DB, not from this function.
"""

import yfinance as yf
import time


def fetch_stock_info(ticker):
    """
    Fetches current price and sector for a single ticker.
    NSE tickers need the ".NS" suffix, e.g. "RELIANCE.NS", "TCS.NS".

    Returns:
        {"ticker": "TCS.NS", "price": 3800.5, "sector": "Technology"}
        or
        {"ticker": "BADTICKER.NS", "price": None, "sector": None, "error": "..."}
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        price = info.get("currentPrice") or info.get("regularMarketPrice")
        sector = info.get("sector")

        if price is None:
            return {
                "ticker": ticker,
                "price": None,
                "sector": None,
                "error": "No price data returned — check ticker symbol",
            }

        return {"ticker": ticker, "price": round(float(price), 2), "sector": sector or "Uncategorized"}

    except Exception as e:
        return {"ticker": ticker, "price": None, "sector": None, "error": str(e)}


def fetch_multiple(tickers, delay_seconds=0.5):
    """
    Fetches info for a list of tickers, one at a time with a small
    delay between calls — yfinance can rate-limit/fail if hammered
    with rapid back-to-back requests.
    """
    results = []
    for ticker in tickers:
        result = fetch_stock_info(ticker)
        results.append(result)
        time.sleep(delay_seconds)
    return results


if __name__ == "__main__":
    # Run locally (needs internet): python data_fetch.py
    sample_tickers = [
        "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS",
        "ICICIBANK.NS", "SUNPHARMA.NS", "ITC.NS",
        "NOTAREALTICKER.NS",  # deliberately invalid
    ]

    results = fetch_multiple(sample_tickers)

    print(f"{'Ticker':<20}{'Price':<12}{'Sector':<20}{'Error'}")
    print("-" * 70)
    for r in results:
        print(
            f"{r['ticker']:<20}"
            f"{str(r['price']) if r['price'] is not None else '-':<12}"
            f"{r['sector'] or '-':<20}"
            f"{r.get('error', '')}"
        )