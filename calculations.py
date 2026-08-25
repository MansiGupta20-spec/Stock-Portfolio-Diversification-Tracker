"""
calculations.py
(Corresponds to allocation.py in your teammate's module structure —
same file, kept under this name for consistency with earlier work.)

Implements Section 4.1-4.4 from the teammate's spec:
  4.1  Individual holding value
  4.2  Total portfolio value
  4.3  Stock-wise allocation %
  4.4  Sector-wise allocation %

Expected input shape per holding:
    {"ticker": str, "quantity": number, "price": number,
     "sector": str or None, "purchase_price": number (optional)}
"""

import pandas as pd


def calculate_allocation(holdings):
    """
    4.1 value_i = quantity_i x current_price_i
    4.2 total_value = sum(value_i)
    4.3 allocation_i (%) = (value_i / total_value) x 100

    Returns:
    {
        "total_value": float,
        "holdings": [ {..original fields.., "value": float, "allocation_percent": float}, ... ]
    }
    """
    if not holdings:
        return {"total_value": 0.0, "holdings": []}

    df = pd.DataFrame(holdings)

    # Defensive cleaning
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(0)
    df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0)
    df = df[(df["quantity"] > 0) & (df["price"] > 0)].copy()

    if "purchase_price" in df.columns:
        df["purchase_price"] = pd.to_numeric(df["purchase_price"], errors="coerce")

    df["value"] = df["quantity"] * df["price"]
    total_value = df["value"].sum()

    if total_value == 0:
        df["allocation_percent"] = 0.0
    else:
        df["allocation_percent"] = (df["value"] / total_value * 100).round(2)

    # Optional 4.8 gain/loss, only if purchase_price is present and valid
    if "purchase_price" in df.columns:
        has_pp = df["purchase_price"].notna() & (df["purchase_price"] > 0)
        df.loc[has_pp, "gain_loss"] = (
            (df.loc[has_pp, "price"] - df.loc[has_pp, "purchase_price"]) * df.loc[has_pp, "quantity"]
        ).round(2)
        df.loc[has_pp, "gain_loss_percent"] = (
            (df.loc[has_pp, "price"] - df.loc[has_pp, "purchase_price"])
            / df.loc[has_pp, "purchase_price"] * 100
        ).round(2)

    return {
        "total_value": round(float(total_value), 2),
        "holdings": df.to_dict(orient="records"),
    }


def calculate_sector_allocation(holdings):
    """
    4.4 For each unique sector S:
        sector_value(S)      = sum(value_i) where sector_i = S
        sector_allocation(S) = (sector_value(S) / total_value) x 100

    Returns:
    {
        "total_value": float,
        "sectors": [ {"sector": str, "value": float, "allocation_percent": float}, ... ]
    }
    """
    if not holdings:
        return {"total_value": 0.0, "sectors": []}

    df = pd.DataFrame(holdings)

    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(0)
    df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0)
    df = df[(df["quantity"] > 0) & (df["price"] > 0)].copy()

    # Missing/blank sector -> "Uncategorized" (never silently dropped —
    # dropping would understate total_value and skew every other
    # sector's percentage)
    df["sector"] = df["sector"].fillna("Uncategorized")
    df.loc[df["sector"].astype(str).str.strip() == "", "sector"] = "Uncategorized"

    df["value"] = df["quantity"] * df["price"]
    total_value = df["value"].sum()

    sector_totals = df.groupby("sector", as_index=False)["value"].sum()

    if total_value == 0:
        sector_totals["allocation_percent"] = 0.0
    else:
        sector_totals["allocation_percent"] = (
            sector_totals["value"] / total_value * 100
        ).round(2)

    sector_totals["value"] = sector_totals["value"].round(2)
    sector_totals = sector_totals.sort_values(
        "allocation_percent", ascending=False
    ).reset_index(drop=True)

    return {
        "total_value": round(float(total_value), 2),
        "sectors": sector_totals.to_dict(orient="records"),
    }


if __name__ == "__main__":
    # Quick manual test: python calculations.py
    from sample_data import sample_holdings

    print("=== calculate_allocation ===")
    allocation_result = calculate_allocation(sample_holdings)
    print("Total value:", allocation_result["total_value"])
    for h in allocation_result["holdings"]:
        gl = h.get("gain_loss", "n/a")
        print(f"  {h['ticker']:<14} value={h['value']:<10} allocation={h['allocation_percent']}%  gain_loss={gl}")

    print("\n=== calculate_sector_allocation ===")
    sector_result = calculate_sector_allocation(sample_holdings)
    print("Total value:", sector_result["total_value"])
    for s in sector_result["sectors"]:
        print(f"  {s['sector']:<12} value={s['value']:<10} allocation={s['allocation_percent']}%")