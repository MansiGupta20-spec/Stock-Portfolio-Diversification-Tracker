"""
risk_engine.py

Implements Sections 4.5, 4.6, 4.7 from the teammate's spec:
  4.5  Diversification risk flags
  4.6  Herfindahl-Hirschman Index (HHI) — concentration metric
  4.7  Diversification Score (0-100)

Every flag and score deduction is explainable — traceable to a
number and a stated rule, matching the risk_flags table shape
(flag_type, detail, severity).
"""

# --- 4.5 Rule thresholds (from teammate's spec) ---
STOCK_OVERWEIGHT_THRESHOLD = 10     # % — single stock allocation
SECTOR_OVERWEIGHT_THRESHOLD = 25    # % — single sector allocation
MIN_HOLDINGS = 8                    # under-diversified if fewer holdings
MIN_SECTORS = 4                     # low sector spread if fewer sectors

# --- 4.6 HHI thresholds (standard interpretation bands) ---
HHI_MODERATE_MIN = 1500
HHI_HIGH_MIN = 2500


def calculate_hhi(weights_percent):
    """
    4.6  HHI = sum(w_i^2) x 10000, where w_i = value_i / total_value (fraction)

    weights_percent: list of allocation percentages (e.g. [35.24, 31.66, ...])
    Returns the HHI as a number roughly between 0 and 10000.
    """
    if not weights_percent:
        return 0.0
    hhi = sum((w / 100) ** 2 for w in weights_percent) * 10000
    return round(hhi, 2)


def classify_hhi(hhi):
    """
    Standard interpretation bands from the teammate's spec:
        < 1500        : Well diversified
        1500 - 2500   : Moderate concentration
        > 2500        : Highly concentrated (risky)
    """
    if hhi > HHI_HIGH_MIN:
        return "Highly concentrated"
    elif hhi >= HHI_MODERATE_MIN:
        return "Moderate concentration"
    else:
        return "Well diversified"


def generate_flags(holdings, sector_data):
    """
    4.5  Applies all four rule-based flags.

    holdings:    the "holdings" list from calculate_allocation()
                 (each item needs "ticker" and "allocation_percent")
    sector_data: the "sectors" list from calculate_sector_allocation()
                 (each item needs "sector" and "allocation_percent")

    Returns a list of flag dicts matching the risk_flags table shape:
        {"flag_type": str, "detail": str, "severity": "Low"|"Medium"|"High"}
    """
    flags = []

    # Rule 1: Single stock overweight (> 10%)
    for h in holdings:
        if h["allocation_percent"] > STOCK_OVERWEIGHT_THRESHOLD:
            flags.append({
                "flag_type": "STOCK_OVERWEIGHT",
                "detail": (
                    f"{h['ticker']} makes up {h['allocation_percent']}% of the "
                    f"portfolio, above the {STOCK_OVERWEIGHT_THRESHOLD}% single-stock guideline."
                ),
                "severity": "Medium",
            })

    # Rule 2: Single sector overweight (> 25%)
    for s in sector_data:
        if s["allocation_percent"] > SECTOR_OVERWEIGHT_THRESHOLD:
            flags.append({
                "flag_type": "SECTOR_OVERWEIGHT",
                "detail": (
                    f"{s['sector']} sector makes up {s['allocation_percent']}% of the "
                    f"portfolio, above the {SECTOR_OVERWEIGHT_THRESHOLD}% single-sector guideline."
                ),
                "severity": "High",
            })

    # Rule 3: Under-diversified (fewer than 8 holdings)
    if len(holdings) < MIN_HOLDINGS:
        flags.append({
            "flag_type": "UNDER_DIVERSIFIED",
            "detail": (
                f"Portfolio holds only {len(holdings)} stock(s), below the "
                f"{MIN_HOLDINGS}-holding guideline for adequate diversification."
            ),
            "severity": "Low",
        })

    # Rule 4: Low sector spread (fewer than 4 sectors)
    if len(sector_data) < MIN_SECTORS:
        flags.append({
            "flag_type": "LOW_SECTOR_SPREAD",
            "detail": (
                f"Portfolio spans only {len(sector_data)} sector(s), below the "
                f"{MIN_SECTORS}-sector guideline for adequate sector spread."
            ),
            "severity": "Medium",
        })

    return flags


def add_hhi_flag(flags, sector_hhi):
    """
    Adds an HHI-based flag (stock/sector concentration metric) onto
    an existing flags list, IF concentration is moderate or high.
    Returns the updated flags list (does not mutate in place).
    """
    flags = list(flags)  # don't mutate caller's list

    if sector_hhi > HHI_HIGH_MIN:
        flags.append({
            "flag_type": "HIGH_CONCENTRATION_HHI",
            "detail": f"Sector-level HHI is {sector_hhi}, above 2500 — indicates high concentration.",
            "severity": "High",
        })
    elif sector_hhi >= HHI_MODERATE_MIN:
        flags.append({
            "flag_type": "MODERATE_CONCENTRATION_HHI",
            "detail": f"Sector-level HHI is {sector_hhi}, between 1500-2500 — indicates moderate concentration.",
            "severity": "Medium",
        })

    return flags


def calculate_diversification_score(flags, sector_hhi):
    """
    4.7  Simple, explainable 0-100 score.

    score = 100
    -15  if a STOCK_OVERWEIGHT flag exists
    -15  if a SECTOR_OVERWEIGHT flag exists
    -10  if an UNDER_DIVERSIFIED flag exists
    -10  if a LOW_SECTOR_SPREAD flag exists
    -20  if sector_hhi > 2500
    -10  if sector_hhi is between 1500-2500

    Each rule only deducts ONCE regardless of how many individual
    stocks/sectors triggered it — the flags list already contains
    the specific per-item detail for display.
    """
    score = 100
    deductions = []

    flag_types_present = {f["flag_type"] for f in flags}

    if "STOCK_OVERWEIGHT" in flag_types_present:
        score -= 15
        deductions.append({"reason": "One or more stocks exceed the single-stock overweight threshold", "points": -15})

    if "SECTOR_OVERWEIGHT" in flag_types_present:
        score -= 15
        deductions.append({"reason": "One or more sectors exceed the single-sector overweight threshold", "points": -15})

    if "UNDER_DIVERSIFIED" in flag_types_present:
        score -= 10
        deductions.append({"reason": f"Fewer than {MIN_HOLDINGS} holdings in the portfolio", "points": -10})

    if "LOW_SECTOR_SPREAD" in flag_types_present:
        score -= 10
        deductions.append({"reason": f"Fewer than {MIN_SECTORS} sectors represented", "points": -10})

    if sector_hhi > HHI_HIGH_MIN:
        score -= 20
        deductions.append({"reason": f"Sector HHI ({sector_hhi}) is above 2500 — highly concentrated", "points": -20})
    elif sector_hhi >= HHI_MODERATE_MIN:
        score -= 10
        deductions.append({"reason": f"Sector HHI ({sector_hhi}) is between 1500-2500 — moderate concentration", "points": -10})

    score = max(score, 0)
    return {"score": score, "deductions": deductions}


def classify_score(score):
    """Score bands from the teammate's spec."""
    if score >= 80:
        return "Well diversified"
    elif score >= 50:
        return "Moderate risk"
    else:
        return "High concentration risk"


if __name__ == "__main__":
    # Quick manual test: python rule_engine.py
    from sample_data import sample_holdings
    from allocation import calculate_allocation, calculate_sector_allocation

    allocation_result = calculate_allocation(sample_holdings)
    sector_result = calculate_sector_allocation(sample_holdings)

    flags = generate_flags(allocation_result["holdings"], sector_result["sectors"])

    stock_hhi = calculate_hhi([h["allocation_percent"] for h in allocation_result["holdings"]])
    sector_hhi = calculate_hhi([s["allocation_percent"] for s in sector_result["sectors"]])

    flags = add_hhi_flag(flags, sector_hhi)

    score_result = calculate_diversification_score(flags, sector_hhi)

    print("=== Flags ===")
    if not flags:
        print("  No flags triggered.")
    for f in flags:
        print(f"  [{f['severity']}] {f['flag_type']}: {f['detail']}")

    print(f"\n=== HHI ===")
    print(f"  Stock-level HHI:  {stock_hhi}  -> {classify_hhi(stock_hhi)}")
    print(f"  Sector-level HHI: {sector_hhi}  -> {classify_hhi(sector_hhi)}")

    print(f"\n=== Diversification Score ===")
    print(f"  Score: {score_result['score']}/100  -> {classify_score(score_result['score'])}")
    for d in score_result["deductions"]:
        print(f"    {d['points']:+d} - {d['reason']}")