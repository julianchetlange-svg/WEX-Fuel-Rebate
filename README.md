# McCoy's WEX Fuel Rebate Analysis

Interactive dashboard (`index.html`) that applies the WEX Fleet Business Charge Card rebate terms to monthly card transactions:

- **Early pay rebate** — 0.20% for tri-monthly billing & payment
- **Consumption rebate** — tier rate based on total program gallons for the month

| Monthly gallons | Rate |
|---|---|
| 70,000 – 89,999 | 0.90% |
| 90,000 – 109,999 | 1.05% |
| 110,000 + | 1.10% |

Tabs: **Monthly Rebate Summary** (early pay vs. consumption by month, tier ladder) and **Rebate by Location** (location × month matrix, single-month detail, CSV copy).

## Updating with a new export

```bash
pip install pandas openpyxl
python build/build_rebate.py exports/Transactions_JanSep.xlsx exports/Transactions_Oct.xlsx
```

Pass every export for the year; files are combined (identical rows dropped) and the months shown on the page follow the data. This regenerates `index.html` from `build/template.html` and `build/logo.png`.

Raw exports contain driver names and card details — keep them in `exports/` (git-ignored), never commit them.
