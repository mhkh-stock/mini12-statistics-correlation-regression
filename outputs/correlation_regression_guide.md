# Mini #12 — Correlation & Regression Guide (SAMPLE data)

Fictional shop **Noor Electronics (Lahore)**, 24 months, Jan 2024–Dec 2025.
All numbers below are computed from `data/raw/monthly_stats_SAMPLE.csv`
by `src/analyze.py` (Python standard library only) — nothing is typed in.
Reproduce them with `python3 src/analyze.py`, then check them with
`python3 src/checks.py`.

## The data at a glance

| Total (24 months) | Value |
|---|---|
| Revenue | PKR 124,817,600 |
| Ad spend | PKR 7,034,000 |
| Footfall | 121,657 visitors |
| Units sold | 14,649 |
| Average discount | 11.81% |

Average month: revenue PKR 5,200,733, ad spend
PKR 293,083, footfall 5,069,
610 units at an average discount of
11.81%.

## The four correlations that matter

| Pair | Pearson r | What it means in plain English |
|---|---|---|
| Ad spend vs revenue | 0.8624 | Very strong positive. Months with more ad spend almost always had more revenue. |
| Footfall vs revenue | 0.8247 | Strong positive. Busier months earned more — footfall and revenue move together. |
| Discount vs units sold | 0.6108 | Moderate positive. Deeper discounts went with MORE units sold, not fewer. |
| Discount vs footfall (control) | 0.0763 | Near zero. Discounts did not bring more people through the door. |

### How to read an r

- **r near +1 or −1:** the two numbers move together (or exactly opposite).
  Here 0.8624 and 0.8247 are strong; 0.6108 is moderate.
- **r near 0:** no straight-line relationship. Here 0.0763 means
  discount and footfall are essentially unrelated in these 24 months.
- **r is not a percent.** r = 0.8624 does NOT mean "86% caused by ads".
  The percent version is R², below.

### The control pair is the lesson

Discount vs footfall r = 0.0763 is a **finding, not a failure**.
Discounts lifted units sold (r = 0.6108) but did NOT lift footfall.
So the discount worked on the people who were already in the shop —
it converted browsers into buyers — instead of attracting new visitors.
A weak r that answers a business question is worth more than a strong r
that answers nothing.

## Regression 1: revenue ~ ad spend

    revenue = 2,109,508 + 10.55 x ad_spend

- **Slope 10.5473:** every extra PKR 10,000 of ad spend predicts
  about **PKR 105,473 more revenue** that month
  (10.55 x 10,000). That is the single most useful sentence
  in this pack — it turns a correlation into a budgeting rule.
- **Intercept PKR 2,109,508:** the model's revenue at zero
  ad spend. Do not over-read it — zero ad spend is outside the data
  (ad spend ranged PKR 187,000–
  PKR 445,000), so the intercept is an
  extrapolation, not a promise.
- **R² = 0.7437:** about 74.4%
  of the month-to-month variation in revenue is explained by ad spend
  alone. The other 25.6% is everything
  else — season, product mix, luck.
- **Standard error of the slope = 1.3201, t = 7.99,
  p ≈ 1.33e-15** (normal approximation): the slope is far
  from zero. With 24 months, a t of 7.99 leaves no
  reasonable doubt that the relationship is real *in this data*.
- **Spearman rho = 0.8615** (rank correlation, same pair): nearly the
  same as Pearson r = 0.8624, so the relationship is not being driven
  by one or two extreme months — the ranks agree with the raw numbers.

### Worked prediction

Ad spend PKR 350,000 in a month predicts revenue of about
PKR 5,801,048.
Ad spend PKR 250,000 predicts about
PKR 4,746,322.
The PKR 100,000 gap in spend predicts a PKR 1,054,730 gap in
revenue — that is the slope, doing its job.

## Regression 2: units sold ~ average discount

    units_sold = 427.6 + 15.48 x avg_discount_pct

- **Slope 15.4822:** each extra 1 percentage point of
  discount predicts about **15.48 more units sold** that month.
  A 5-point deeper discount (say 10% -> 15%) predicts about
  77 extra units.
- **R² = 0.3731:** discount explains about
  37.3% of the variation in units sold —
  real, but far from the whole story. Footfall, season and product mix
  explain the rest.
- **t = 3.62, p ≈ 2.96e-04:** the
  discount effect is statistically solid, not noise.

### The trap this regression teaches

Discounts raise units but they cut the price on EVERY unit, including
the ones that would have sold anyway. This pack proves the volume
effect (15.48 extra units per point of discount) — it does NOT
prove discounts raise profit. Always pair a units regression with a
margin check before recommending a deeper discount.

## Residual diagnostics (revenue ~ ad spend)

| Check | Value | Verdict |
|---|---|---|
| Mean residual | PKR -0.00 | ~0, as OLS guarantees — the model is not biased up or down on average |
| Residual SD | PKR 418,086 | Typical month misses the prediction by about this much |
| Durbin–Watson | 1.80 | Near 2: no obvious month-to-month pattern in the misses |
| Largest standardised residual | 1.83 | No month is an extreme outlier (nothing beyond ~3) |
| Correlation(residuals, fitted) | -0.0000 | ~0, as OLS guarantees — the misses carry no leftover signal |

Plain English: the model misses by about PKR 418,086
in a typical month, the misses look random rather than patterned, and no
single month wrecks the fit. That is a usable model, not a perfect one.

## Correlation is not causation — the warning, with examples

1. **Ad spend and revenue (r = 0.8624) do not prove ads CAUSED the
   revenue.** A busy festive month could raise both at once. What the
   regression gives you is a prediction rule, not a proof of cause.
   Proof would need an experiment (spend more in some months, hold
   steady in matched others) — this pack shows the observational
   evidence and labels it as such.
2. **Footfall and revenue (r = 0.8247)** have the same warning, in
   the other direction: high revenue months may have *funded* more
   ads, so the arrow could partly run revenue -> ad spend.
3. **Discount and footfall (r = 0.0763)** is the cleanest causal
   hint in the pack — precisely because it is near zero: if discounts
   pulled in crowds, this number would be large. It is not, so the
   "discounts bring people in" story fails on this data.

## Full correlation matrix (all 10 pairs)

|  | ad_spend | footfall | discount | units | revenue |
|---|---|---|---|---|---|
| ad_spend | 1.0000 | 0.9684 | 0.1121 | 0.4116 | 0.8624 |
| footfall |  | 1.0000 | 0.0763 | 0.3197 | 0.8247 |
| discount |  |  | 1.0000 | 0.6108 | 0.1714 |
| units |  |  |  | 1.0000 | 0.3395 |
| revenue |  |  |  |  | 1.0000 |

Note ad spend vs footfall r = 0.9684: ads and
footfall move together, which is exactly why footfall also correlates
with revenue — the three strong relationships share one driver (ad
spend). That shared driver is also why you cannot read any single r
as "the" cause.

## Methods (so you can check the maths)

- **Pearson r:** covariance of the two columns divided by the product
  of their standard deviations, computed from the 24 monthly rows.
- **Spearman rho:** Pearson r computed on the ranks instead of the raw
  values (average ranks for ties).
- **OLS:** slope = covariance(x, y) / variance(x); intercept =
  mean(y) − slope x mean(x). R² = 1 − (residual sum of squares /
  total sum of squares). Standard error of the slope =
  sqrt(SS_res / (n − 2) / SS_x). t = slope / SE.
- **p-values** use the normal approximation (via `math.erf`), not an
  exact t table — stated as approximate in `summary.json`.
- **Durbin–Watson:** sum of squared month-to-month changes in residuals
  divided by the sum of squared residuals; ~2 means no autocorrelation.

## Limits

- **SAMPLE data only.** Noor Electronics is fictional; the relationships
  are planted by the seeded generator so the techniques can be taught.
  The methods are real; the shop is not.
- **n = 24 months.** Small sample: every r and slope here has a wide
  margin of error, and one unusual month can move the numbers. Do not
  present these as precise business facts.
- **Observational, not experimental.** No causal claim is made anywhere
  in this pack.
- **Revenue is not units x a fixed price.** The implied average realised
  price (revenue / units) ranges PKR 6,115–
  PKR 10,935 (mean PKR 8,633)
  because product mix and discount mix vary — realistic, and stated
  here rather than hidden.
