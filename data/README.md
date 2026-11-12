# Mini #12 — data dictionary (SAMPLE / DEMO only)

Fictional shop "Noor Electronics" (Lahore), 24 months, Jan 2024–Dec 2025.
The shop, the months and every number are invented for teaching — the
statistics are real, the business is not. Regenerate exactly with
`python3 src/generate_data.py` (seed 131, deterministic).

## data/raw/monthly_stats_SAMPLE.csv (24 rows + header)

| Column | Meaning |
|---|---|
| `month` | Month, `yyyy-mm`, Jan 2024–Dec 2025, consecutive, no gaps |
| `ad_spend_pkr` | Advertising spend that month, PKR (rounded to PKR 1,000) |
| `footfall` | Visitors through the door that month (count) |
| `avg_discount_pct` | Average discount given that month, % (1 decimal, clamped 4–20) |
| `units_sold` | Units sold that month (count) |
| `revenue_pkr` | Revenue that month, PKR (rounded to PKR 100) |

## How the data was planted (seed 131)

Three real relationships are built into the generator, so the techniques
have something true to find — and one control pair is deliberately
near-zero:

- **Ad spend -> revenue:** revenue = 5,200,000 + 800,000 x
  (0.85 x ad-driver + noise) → r(ad, revenue) = 0.8624.
- **Footfall -> revenue:** footfall shares the same ad-driver
  (0.94 loading) → r(footfall, revenue) = 0.8247.
- **Discount -> units:** units = 620 + 90 x (0.60 x discount-driver +
  noise) → r(discount, units) = 0.6108. Discounts raise units here.
- **Discount vs footfall (control):** independent drivers →
  r(discount, footfall) = 0.0763. A weak r is a finding, not a failure.

## Known quirks

- **Revenue is not units x a fixed price.** The implied average realised
  price (revenue / units) ranges PKR 6,115–10,935 (mean PKR 8,633)
  because product mix and discount mix vary month to month. That is
  realistic for a shop, and it is why revenue is modelled on its own
  driver instead of being forced to equal units x price.
- **Discounts are clamped to 4–20%.** The raw normal draw could in
  theory go outside that range; the clamp keeps every month plausible.
- **n = 24 months is small.** Every r and slope in this pack has a wide
  margin of error; one unusual month can move the numbers. The pack
  says so in the guide instead of hiding it.

## Totals (verified)

- Revenue PKR 124,817,600 · ad spend PKR 7,034,000 ·
  footfall 121,657 · units sold 14,649 · average discount 11.81%.
- Average month: revenue PKR 5,200,733 · ad spend PKR 293,083 ·
  footfall 5,069 · 610 units.
