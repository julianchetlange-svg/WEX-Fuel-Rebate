"""Rebuild index.html from a WEX transactions export.

Usage:
    python build/build_rebate.py exports/*.xlsx

Pass every export covering the year (e.g. the Jan-Sep file plus each new
monthly file). Rows are combined and de-duplicated on identical rows, so
overlapping exports are safe.

Rebates (WEX Fleet Business Charge Card Agreement):
  - Early pay (tri-monthly billing & payment): 0.20% of monthly retail transactions
  - Consumption: tier rate set by program-wide monthly gallons
      70,000-89,999 -> 0.90% | 90,000-109,999 -> 1.05% | 110,000+ -> 1.10%
The page applies the rates in the browser; this script only aggregates
gallons / spend by location (Account Name) and month.
"""
import base64
import calendar
import datetime as dt
import json
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def main(files: list[str]) -> None:
    frames = [pd.read_excel(f, dtype={"Account Name": str, "Trans ID": str}) for f in files]
    raw = pd.concat(frames, ignore_index=True)
    # Trans ID repeats across product lines of one fill-up (e.g. diesel + DEF),
    # so only drop rows that are identical in every column.
    df = raw.drop_duplicates()
    dupes = len(raw) - len(df)
    df = df.assign(date=pd.to_datetime(df["Transaction Date"]))
    df["m"] = df["date"].dt.month
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

    first, last = df["date"].min(), df["date"].max()
    m0, m1 = calendar.month_abbr[first.month], calendar.month_abbr[last.month]
    period = f"{m0}\u2013{m1}" if m0 != m1 else m0
    end_day = calendar.monthrange(last.year, last.month)[1]
    rng = f"{m0} 1 \u2013 {m1} {end_day}, {last.year}"
    asof = dt.date.today().strftime("%b %-d, %Y")

    logo = "data:image/png;base64," + base64.b64encode((HERE / "logo.png").read_bytes()).decode()
    html = (
        (HERE / "template.html").read_text()
        .replace("__DATA__", json.dumps(data, separators=(",", ":")))
        .replace("__LOGO__", logo)
        .replace("__TXNS__", f"{len(df):,}")
        .replace("__PERIODUP__", period.upper())
        .replace("__PERIOD__", period)
        .replace("__RANGE__", rng)
        .replace("__ASOF__", asof)
    )
    (ROOT / "index.html").write_text(html)
    print(f"Wrote index.html: {len(df):,} transactions ({dupes} duplicates dropped), "
          f"{len(data)} locations, {rng}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1:])
