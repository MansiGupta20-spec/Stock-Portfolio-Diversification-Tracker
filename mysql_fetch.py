"""
mysql_fetch.py
MySQL data source for the Streamlit app — pulls a saved portfolio's
holdings straight from the team's MySQL database (built by Member A).

ASSUMED SCHEMA (from README_Samarpan.md — confirm with Member A if
their actual table/column names differ, only this file needs to change):

    portfolios
        portfolio_id  INT PK
        user_name     TEXT
        created_at    DATETIME

    holdings
        holding_id     INT PK
        portfolio_id   INT   (FK -> portfolios.portfolio_id)
        ticker         TEXT
        quantity       DECIMAL
        sector         TEXT
        current_price  DECIMAL
        value          DECIMAL
        fetched_at     DATETIME

Output shape matches what allocation.py / risk_engine.py already expect:
    [{"ticker": str, "quantity": ..., "price": ..., "sector": ...}, ...]

Credentials are NEVER hardcoded here (unlike Mark1.py's DB connection,
which had the password baked into the source — don't repeat that).
They come from st.secrets when deployed, and from sidebar text inputs
for local prototype testing on the leader's laptop.
"""

import streamlit as st
import mysql.connector


def get_connection(host, user, password, database, port=3306):
    """Opens a fresh MySQL connection. Streamlit reruns the whole script
    on every interaction, so a new lightweight connection per action is
    simplest for a local prototype. Once this moves off localhost, wrap
    the portfolio list/fetch calls in @st.cache_data(ttl=60) instead of
    caching the connection itself (raw connections don't survive Streamlit's
    cache serialization well)."""
    return mysql.connector.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        auth_plugin="mysql_native_password",
    )


def list_portfolios(host, user, password, database, port=3306):
    """Returns [(portfolio_id, user_name), ...] for the sidebar dropdown."""
    conn = None
    try:
        conn = get_connection(host, user, password, database, port)
        cursor = conn.cursor()
        cursor.execute("SELECT portfolio_id, user_name FROM portfolios ORDER BY created_at DESC")
        rows = cursor.fetchall()
        cursor.close()
        return rows
    except Exception as e:
        st.sidebar.error(f"Could not list portfolios: {e}")
        return []
    finally:
        if conn is not None and conn.is_connected():
            conn.close()


def fetch_portfolio_from_mysql(portfolio_id, host, user, password, database, port=3306):
    """
    Reads every holding row for one portfolio_id and returns it in the
    shape allocation.py's calculate_allocation() expects.
    """
    conn = None
    try:
        conn = get_connection(host, user, password, database, port)
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT ticker, quantity, sector, current_price "
            "FROM holdings WHERE portfolio_id = %s",
            (portfolio_id,),
        )
        rows = cursor.fetchall()
        cursor.close()

        holdings = [
            {
                "ticker": r["ticker"],
                "quantity": r["quantity"],
                "price": r["current_price"],
                "sector": r["sector"] or "Uncategorized",
            }
            for r in rows
            if r.get("ticker") and r.get("quantity") and r.get("current_price")
        ]
        return holdings
    except Exception as e:
        st.sidebar.error(f"Could not fetch holdings: {e}")
        return []
    finally:
        if conn is not None and conn.is_connected():
            conn.close()


if __name__ == "__main__":
    # Quick manual test (needs local MySQL running + real credentials):
    #   python mysql_fetch.py
    portfolios = list_portfolios("localhost", "root", "yourpassword", "portfolio_db")
    print("Portfolios:", portfolios)
    if portfolios:
        pid = portfolios[0][0]
        holdings = fetch_portfolio_from_mysql(pid, "localhost", "root", "yourpassword", "portfolio_db")
        print(f"Holdings for portfolio {pid}:", holdings)
