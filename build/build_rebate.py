"""Rebuild index.html from a WEX transactions export.

Usage:
    python build/build_rebate.py path/to/Transactions.xlsx

Rebates (WEX Fleet Business Charge Card Agreement):
  - Early pay (tri-monthly billing & payment): 0.20% of monthly retail transactions
  - Consumption: tier rate set by program-wide monthly gallons
      70,000-89,999 -> 0.90% | 90,000-109,999 -> 1.05% | 110,000+ -> 1.10%
The page applies the rates in the browser; this script only aggregates
gallons / spend by location (Account Name) and month.
"""
import base64
import json
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def main(xlsx: str) -> None:
    df = pd.read_excel(xlsx, dtype={"Account Name": str})
    df["m"] = pd.to_datetime(df["Transaction Date"]).dt.month
    is_gal = df["Unit of Measure"] == "GA"
    df["gal"] = df["Units"].where(is_gal, 0)
    # "Fuel only" basis: gallon products excluding DEF
    df["fuelnet"] = df["Net Cost"].where(is_gal & (df["Product"] != "DEF"), 0)

    g = (
        df.groupby(["Account Name", "m"])
        .agg(g=("gal", "sum"), a=("Net Cost", "sum"), f=("fuelnet", "sum"), t=("Trans ID", "count"))
        .reset_index()
    )
    data: dict = {}
    for r in g.itertuples(index=False):
        data.setdefault(r[0], {})[int(r.m)] = [round(r.g, 1), round(r.a, 2), round(r.f, 2), int(r.t)]

    logo = "data:image/png;base64," + base64.b64encode((HERE / "logo.png").read_bytes()).decode()
    html = (
        (HERE / "template.html").read_text()
        .replace("__DATA__", json.dumps(data, separators=(",", ":")))
        .replace("__LOGO__", logo)
        .replace("__TXNS__", f"{len(df):,}")
    )
    (ROOT / "index.html").write_text(html)
    print(f"Wrote index.html: {len(df):,} transactions, {len(data)} locations")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
