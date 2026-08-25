"""
sample_data.py
Fake/sample portfolio data — used to build and test calculation
functions before market_data.py (yfinance) / db.py are wired in.

Kept at 6 holdings across 4 sectors deliberately: this will trigger
the "under-diversified" flag (< 8 holdings) but NOT the "low sector
spread" flag (4 sectors is the minimum, not below it) — useful for
demoing that flags trigger independently and correctly.
"""

sample_holdings = [
    {"ticker": "TCS.NS",       "quantity": 5,  "purchase_price": 3600, "price": 3800, "sector": "IT"},
    {"ticker": "INFY.NS",      "quantity": 8,  "purchase_price": 1400, "price": 1500, "sector": "IT"},
    {"ticker": "HDFCBANK.NS",  "quantity": 12, "purchase_price": 1550, "price": 1650, "sector": "Banking"},
    {"ticker": "ICICIBANK.NS", "quantity": 15, "purchase_price": 900,  "price": 980,  "sector": "Banking"},
    {"ticker": "RELIANCE.NS",  "quantity": 10, "purchase_price": 2400, "price": 2550, "sector": "Energy"},
    {"ticker": "SUNPHARMA.NS", "quantity": 6,  "purchase_price": 1050, "price": 1150, "sector": "Healthcare"},
]

# Edge-case dataset for testing later: heavily concentrated in one
# sector, and fewer than 4 sectors — should trigger MOST flags at once.
concentrated_holdings = [
    {"ticker": "TCS.NS",      "quantity": 20, "purchase_price": 3600, "price": 3800, "sector": "IT"},
    {"ticker": "INFY.NS",     "quantity": 20, "purchase_price": 1400, "price": 1500, "sector": "IT"},
    {"ticker": "WIPRO.NS",    "quantity": 20, "purchase_price": 400,  "price": 420,  "sector": "IT"},
    {"ticker": "RELIANCE.NS", "quantity": 2,  "purchase_price": 2400, "price": 2550, "sector": "Energy"},
]

# Edge case with missing/blank sector and invalid quantity —
# for testing your validation logic, not for the main demo.
edge_case_holdings = [
    {"ticker": "UNKNOWN.NS", "quantity": 3, "purchase_price": 500, "price": 500, "sector": None},
    {"ticker": "ZEROQTY.NS", "quantity": 0, "purchase_price": 100, "price": 100, "sector": "IT"},
]