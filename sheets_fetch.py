"""
sheets_fetch.py
Reads price/sector data from a Google Sheet — used as an
alternative or backup to market_data.py (yfinance).

Output shape matches what allocation.py already expects:
    [{"ticker": str, "quantity": ..., "price": ..., "sector": ...}, ...]
"""

import gspread
from google.oauth2.service_account import Credentials
import streamlit as st


def get_sheet(sheet_name="Portfolio_Data", worksheet_name="Holdings"):
    """Connects to the Google Sheet using credentials from Streamlit secrets."""
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"]
    )
    client = gspread.authorize(credentials)
    return client.open(sheet_name).worksheet(worksheet_name)


def fetch_from_sheet(sheet_name="Portfolio_Data", worksheet_name="Holdings"):
    """
    Reads rows from the sheet and returns them in the same shape
    calculations expect. Sheet columns should be:
        Ticker | Quantity | Price | Sector
    """
    sheet = get_sheet(sheet_name, worksheet_name)
    records = sheet.get_all_records()  # list of dicts, keys = column headers

    holdings = []
    for row in records:
        holdings.append({
            "ticker": row.get("Ticker"),
            "quantity": row.get("Quantity"),
            "price": row.get("Price"),
            "sector": row.get("Sector"),
        })
    return holdings