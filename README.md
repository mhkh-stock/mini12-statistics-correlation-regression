# Mini #12 — Statistics: Correlation & Regression Pack

**Status:** built and verified locally; GitHub publish pending.

**SAMPLE / DEMO data only.** Fictional shop, fictional months, fictional
numbers. Never claimed as real client work.

The statistics companion to the SQL and Excel packs: the same fictional
shop family as Mini #11's "Noor Electronics" — 24 months, Jan 2024–Dec
2025, revenue PKR 124,817,600 — now taught as correlation and
regression. Three relationships are planted in the seeded data, one
control pair is deliberately near-zero, and every number is computed
from the raw CSV with Python's standard library only — no numpy, no
scipy, no typed-in results.

## Business question

"Which numbers actually move with revenue — and which ones only look
like they do?" Ad spend, footfall and discounts are the three levers a
shop owner can pull. This pack measures each lever honestly: how
strong the link is (Pearson r), what it predicts in rupees (OLS
regression), and where the evidence stops short of proof (correlation
is not causation).

## What is inside

| File | What it does |
|---|---|
| `outputs/correlation_regression_guide.md` | Plain-English interpretation: what each r means, what the regressions predict, the causation warning |
| `outputs/summary.json` | Every verified number, machine-readable |
| `data/raw/monthly_stats_SAMPLE.csv` | The 24 SAMPLE months the analysis reads |
| `data/README.md` | Data dictionary + how the relationships were planted + known quirks |
| `src/generate_data.py` | Regenerates the sample CSV (seed 131, deterministic) |
| `src/analyze.py` | Stdlib-only statistics — Pearson r, Spearman rho, two OLS regressions, residual diagnostics |
| `src/checks.py` | Checks as code — 67 checks, all passing |
| `requirements.txt` | No dependencies — standard library only |

## Key findings (real numbers, recomputed from the CSV)

| Finding | Value |
|---|---|
| Ad spend vs revenue | r = 0.8624 — very strong |
| Footfall vs revenue | r = 0.8247 — strong |
| Discount vs units sold | r = 0.6108 — moderate positive (discounts RAISE units) |
| Discount vs footfall (control) | r = 0.0763 — near zero, a finding not a failure |
| Revenue ~ ad spend | slope 10.5473 — every extra PKR 10,000 of ad spend predicts ~PKR 105,473 more revenue; R² = 0.7437, t = 7.99 |
| Units ~ discount | slope 15.4822 — each extra 1 point of discount predicts ~15.48 more units; R² = 0.3731, t = 3.62 |
| Revenue total (24 months) | PKR 124,817,600 |
| Spearman rho (ad spend vs revenue) | 0.8615 — ranks agree with raw values, no outlier month drives the result |
| Residual check | Mean residual ~PKR 0, Durbin–Watson 1.8017, no standardised residual beyond 1.83 — the misses look random |

## What the pack teaches

1. **Read r before you act.** 0.8624 and 0.8247 are strong, 0.6108 is
   moderate, 0.0763 is nothing — and each of those four readings is a
   different business answer.
2. **Turn a correlation into rupees.** The regression slope is the
   budgeting sentence: PKR 10,000 more ad spend → ~PKR 105,473 more
   revenue. R² = 0.7437 says ad spend alone explains 74.37% of the
   month-to-month revenue variation — and the other 25.63% is
   everything else.
3. **A weak r is a finding.** Discounts lifted units (r = 0.6108) but
   did NOT lift footfall (r = 0.0763): the discount converted people
   already in the shop instead of attracting new visitors.
4. **Correlation is not causation.** A festive month could raise ads
   and revenue together; revenue could partly fund the ads. The pack
   gives prediction rules, not proof of cause — proof would need an
   experiment.
5. **Discounts raise units, not necessarily profit.** Each discount
   point predicts ~15.48 extra units, but the discount also cuts the
   price on units that would have sold anyway. Pair any units
   regression with a margin check.

## Verified numbers

| KPI | Value |
|---|---|
| Months | 24 (Jan 2024–Dec 2025, SAMPLE) |
| Revenue total | PKR 124,817,600 |
| Ad spend total | PKR 7,034,000 |
| Footfall total | 121,657 visitors |
| Units sold total | 14,649 |
| Average discount | 11.81% |
| Checks | 67 passing (`python3 src/checks.py`) |

Verification: `python3 src/checks.py` — every headline number is
recomputed from the raw CSV with independent sum-based formulas and
compared against `outputs/summary.json` and the guide within 0.001;
the generator and analyser are re-run and hash-checked for
determinism (see `outputs/summary.json`).

## How to run it

1. Nothing to install — standard library only (see `requirements.txt`).
2. Read `outputs/correlation_regression_guide.md` — that is the
   deliverable.
3. To regenerate the sample data: `python3 src/generate_data.py`.
4. To re-run the analysis: `python3 src/analyze.py`.
5. To check it: `python3 src/checks.py`.
6. To practise on your own data: replace the CSV (same columns)
   and re-run steps 4–5 only — do NOT re-run step 3, it regenerates
   the sample data and would overwrite your file.

## Two traps this pack teaches

- **r is not a percent.** r = 0.8624 does NOT mean "86% caused by
  ads". The percent version is R² = 0.7437 — and even that is
  "explained variation", not "caused by".
- **Strong r, wrong direction.** Footfall and revenue correlate at
  0.8247, but ads drive footfall (r = 0.9684) — the three strong
  relationships share one driver. Reading any single r as "the"
  cause misses the structure underneath.

## Limits

- **SAMPLE data only.** The shop and the numbers are fictional; the
  relationships are planted by the seeded generator so the techniques
  can be taught. The methods are real.
- **n = 24 months.** Small sample: every r and slope has a wide
  margin of error, and one unusual month can move the numbers.
- **Observational, not experimental.** No causal claim is made
  anywhere in this pack.
- **p-values are approximate.** They use the normal approximation to
  the t-distribution (`math.erf`), stated as approximate in
  `summary.json` — close for the large t-values here, not exact.
- **Revenue is not units x a fixed price.** The implied average
  realised price ranges PKR 6,115–10,935 (mean PKR 8,633) because
  product mix and discount mix vary — realistic, and stated in
  `data/README.md` rather than hidden.

## Published

Not yet published on GitHub — local build only.
