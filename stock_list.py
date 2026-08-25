"""
stock_list.py
Friendly company name -> NSE ticker mapping, used by app.py's
"Manual Entry (Live Prices)" dropdown.

This file didn't exist yet anywhere in the project, so it's a starter
set pulled from tickers already used elsewhere in the codebase
(Mark1.py's dropdown, README_Samarpan.md's test list, sample_data.py).
Extend this dict freely — no other file needs to change.
"""

STOCK_TICKERS = {
    "Reliance Industries": "RELIANCE.NS",
    "Tata Consultancy Services": "TCS.NS",
    "Infosys": "INFY.NS",
    "HDFC Bank": "HDFCBANK.NS",
    "ICICI Bank": "ICICIBANK.NS",
    "State Bank of India": "SBIN.NS",
    "Wipro": "WIPRO.NS",
    "ITC": "ITC.NS",
    "Oil & Natural Gas Corp": "ONGC.NS",
    "Sun Pharmaceutical": "SUNPHARMA.NS",
    "Tata Motors": "TATAMOTORS.NS",
    "Nifty 50 ETF (NiftyBees)": "NIFTYBEES.NS",
}
