"""Regenerate data/raw/monthly_stats_SAMPLE.csv — Mini #12 sample data.

Fictional shop "Noor Electronics" (Lahore), 24 months Jan 2024–Dec 2025.
SAMPLE / DEMO data only — never real client or real business data.

Three relationships are PLANTED in the generated data (seeded, seed 131,
fully deterministic — re-running this script reproduces the file exactly):

1. Ad spend -> revenue: revenue is built as 0.85 * ad-spend driver + noise,
   so Pearson r(ad_spend, revenue) comes out strong (~0.86).
2. Discount -> units sold: units are built as 0.60 * discount driver + noise,
   so r(avg_discount_pct, units_sold) comes out moderate-positive (~0.61).
   Discounts RAISE units here — the naive "discounts hurt sales" reading
   is wrong, and the data shows it.
3. Footfall -> revenue: footfall is built as 0.94 * the same ad-spend driver
   as revenue, so r(footfall, revenue) comes out strong (~0.82).

One CONTROL pair is deliberately near-zero: avg_discount_pct and footfall
are built from independent drivers, so r(discount, footfall) is ~0.08 —
a weak correlation is a FINDING, not a failure, and it is the pack's
"correlation is not causation" lesson.

Generation model (all drivers are independent standard normals from one
random.Random(131) stream, consumed in the fixed order a, d, eR, eF, eU
per month, so the file is byte-for-byte reproducible):

    ad_spend_pkr    = 300,000 + 60,000 * a            (rounded to PKR 1,000)
    footfall        = 5,200 + 900 * (0.94*a + 0.341*eF)
    avg_discount_%  = 12 + 3.5 * d                    (clamped to 4–20, 1 dp)
    units_sold      = 620 + 90 * (0.60*d + 0.80*eU)
    revenue_pkr     = 5,200,000 + 800,000 * (0.85*a + 0.527*eR)
                      (rounded to PKR 100)

Quirk, stated honestly: revenue is NOT exactly units_sold x a fixed price.
The implied average realised price (revenue / units) varies month to month
(PKR 6,115–10,935) because the product mix and discount mix vary — that is
realistic for a shop, and it is why revenue is modelled on its own driver
instead of being forced to equal units x price. See data/README.md.
"""

import csv
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "raw" / "monthly_stats_SAMPLE.csv"

SEED = 131
MONTHS = [f"{y}-{m:02d}" for y in (2024, 2025) for m in range(1, 13)]


def build_rows():
    rng = random.Random(SEED)
    rows = []
    for month in MONTHS:
        a = rng.gauss(0, 1)    # ad-spend driver (shared by footfall, revenue)
        d = rng.gauss(0, 1)    # discount driver (shared by units)
        eR = rng.gauss(0, 1)   # revenue noise
        eF = rng.gauss(0, 1)   # footfall noise
        eU = rng.gauss(0, 1)   # units noise
        ad_spend = round((300000 + 60000 * a) / 1000) * 1000
        footfall = int(round(5200 + 900 * (0.94 * a + 0.341 * eF)))
        discount = round(max(4.0, min(20.0, 12 + 3.5 * d)), 1)
        units = int(round(620 + 90 * (0.60 * d + 0.80 * eU)))
        revenue = round((5200000 + 800000 * (0.85 * a + 0.527 * eR)) / 100) * 100
        rows.append({
            "month": month,
            "ad_spend_pkr": ad_spend,
            "footfall": footfall,
            "avg_discount_pct": discount,
            "units_sold": units,
            "revenue_pkr": revenue,
        })
    return rows


def main():
    rows = build_rows()
    assert len(rows) == 24, len(rows)
    assert [r["month"] for r in rows] == MONTHS
    assert sum(r["revenue_pkr"] for r in rows) == 124817600
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {OUT} (24 months, revenue PKR 124,817,600)")


if __name__ == "__main__":
    main()
