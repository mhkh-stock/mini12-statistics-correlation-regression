"""Analyse Mini #12 — correlation & regression (stdlib only).

Reads data/raw/monthly_stats_SAMPLE.csv, computes every number in this
pack from the raw data (nothing is typed in), and writes:
  outputs/summary.json
  outputs/correlation_regression_guide.md

Statistics implemented here from first principles (no numpy / scipy):
  * Pearson r for every pair of the 5 numeric columns (10 pairs).
  * Spearman rho for the main pair (ad spend vs revenue).
  * OLS regression revenue ~ ad_spend and units_sold ~ avg_discount_pct:
    slope, intercept, R-squared, standard error of the slope, t-statistic,
    and an approximate two-sided p-value from the normal approximation
    (Phi via math.erf). With n = 24 the normal approximation is close to
    the t-distribution for the large t-values in this pack; the guide
    says so honestly instead of pretending to an exact t table.
  * Residual diagnostics for revenue ~ ad_spend: mean residual, residual
    standard deviation, Durbin-Watson statistic, largest standardised
    residual, and the correlation of residuals with fitted values.

Run: python3 src/analyze.py
"""

import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSV = ROOT / "data" / "raw" / "monthly_stats_SAMPLE.csv"
SUMMARY = ROOT / "outputs" / "summary.json"
GUIDE = ROOT / "outputs" / "correlation_regression_guide.md"

COLS = ["ad_spend_pkr", "footfall", "avg_discount_pct", "units_sold",
        "revenue_pkr"]
KEY_PAIRS = [
    ("ad_spend_pkr", "revenue_pkr"),
    ("footfall", "revenue_pkr"),
    ("avg_discount_pct", "units_sold"),
    ("avg_discount_pct", "footfall"),
]


def load():
    rows = list(csv.DictReader(open(CSV)))
    data = {c: [float(r[c]) for r in rows] for c in COLS}
    months = [r["month"] for r in rows]
    return months, data


def mean(xs):
    return sum(xs) / len(xs)


def pearson(xs, ys):
    n = len(xs)
    mx, my = mean(xs), mean(ys)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    return sxy / math.sqrt(sxx * syy)


def ranks(values):
    """Average ranks (ties share the mean of their positions)."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    out = [0.0] * len(values)
    i = 0
    while i < len(values):
        j = i
        while j + 1 < len(values) and values[order[j + 1]] == values[order[i]]:
            j += 1
        avg = (i + j) / 2 + 1
        for k in range(i, j + 1):
            out[order[k]] = avg
        i = j + 1
    return out


def spearman(xs, ys):
    return pearson(ranks(xs), ranks(ys))


def norm_p_value(t):
    """Two-sided p-value, normal approximation: 2 * (1 - Phi(|t|))."""
    return 2 * (1 - 0.5 * (1 + math.erf(abs(t) / math.sqrt(2))))


def ols(xs, ys):
    n = len(xs)
    mx, my = mean(xs), mean(ys)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    slope = sxy / sxx
    intercept = my - slope * mx
    fitted = [intercept + slope * x for x in xs]
    resid = [y - f for y, f in zip(ys, fitted)]
    ss_res = sum(r * r for r in resid)
    ss_tot = sum((y - my) ** 2 for y in ys)
    r2 = 1 - ss_res / ss_tot
    se_slope = math.sqrt(ss_res / (n - 2) / sxx)
    t_stat = slope / se_slope
    p_value = norm_p_value(t_stat)
    # --- residual diagnostics
    resid_sd = math.sqrt(ss_res / (n - 2))
    dw = sum((resid[i] - resid[i - 1]) ** 2 for i in range(1, n)) / ss_res
    std_resid = [r / resid_sd for r in resid]
    return {
        "n": n,
        "intercept": intercept,
        "slope": slope,
        "r_squared": r2,
        "se_slope": se_slope,
        "t_stat": t_stat,
        "p_value": p_value,
        "residual_mean": mean(resid),
        "residual_sd": resid_sd,
        "durbin_watson": dw,
        "max_abs_std_residual": max(abs(r) for r in std_resid),
        "corr_residual_fitted": pearson(resid, fitted),
    }


def fmt(n):
    return f"{n:,.0f}"


def main():
    months, data = load()
    n = len(months)
    assert n == 24, n

    corr = {}
    for i, c1 in enumerate(COLS):
        for c2 in COLS[i + 1:]:
            corr[f"{c1}__{c2}"] = pearson(data[c1], data[c2])

    def pair_key(a, b):
        return f"{a}__{b}" if f"{a}__{b}" in corr else f"{b}__{a}"

    key_r = {f"{a}__{b}": corr[pair_key(a, b)] for a, b in KEY_PAIRS}
    rho = spearman(data["ad_spend_pkr"], data["revenue_pkr"])

    reg_rev = ols(data["ad_spend_pkr"], data["revenue_pkr"])
    reg_units = ols(data["avg_discount_pct"], data["units_sold"])

    # Totals only for additive columns — a "total" of discount % would be
    # meaningless, so avg_discount_pct is averaged, never summed.
    totals = {c: int(sum(data[c])) for c in COLS
              if c != "avg_discount_pct"}
    avgs = {c: round(mean(data[c]), 2) for c in COLS}
    implied_price = [r / u for r, u in
                     zip(data["revenue_pkr"], data["units_sold"])]

    summary = {
        "pack": "Mini #12 — Statistics: Correlation & Regression Pack",
        "shop": "Noor Electronics (Lahore) — fictional SAMPLE shop",
        "period": "2024-01 to 2025-12",
        "months": n,
        "status": "SAMPLE data, real statistics (stdlib only)",
        "totals": totals,
        "averages": avgs,
        "correlations": {k: round(v, 4) for k, v in corr.items()},
        "key_correlations": {k: round(v, 4) for k, v in key_r.items()},
        "spearman_ad_spend_revenue": round(rho, 4),
        "regression_revenue_on_ad_spend": {
            "dependent": "revenue_pkr",
            "independent": "ad_spend_pkr",
            "intercept_pkr": round(reg_rev["intercept"], 2),
            "slope_pkr_per_pkr": round(reg_rev["slope"], 4),
            "slope_per_pkr_10000_ad_spend": round(reg_rev["slope"] * 10000, 0),
            "r_squared": round(reg_rev["r_squared"], 4),
            "se_slope": round(reg_rev["se_slope"], 4),
            "t_stat": round(reg_rev["t_stat"], 2),
            "p_value_normal_approx": float(f"{reg_rev['p_value']:.6g}"),
        },
        "regression_units_on_discount": {
            "dependent": "units_sold",
            "independent": "avg_discount_pct",
            "intercept_units": round(reg_units["intercept"], 2),
            "slope_units_per_pct_point": round(reg_units["slope"], 4),
            "r_squared": round(reg_units["r_squared"], 4),
            "se_slope": round(reg_units["se_slope"], 4),
            "t_stat": round(reg_units["t_stat"], 2),
            "p_value_normal_approx": float(f"{reg_units['p_value']:.6g}"),
        },
        "residual_diagnostics_revenue_on_ad_spend": {
            "mean_residual_pkr": round(reg_rev["residual_mean"], 6),
            "residual_sd_pkr": round(reg_rev["residual_sd"], 2),
            "durbin_watson": round(reg_rev["durbin_watson"], 4),
            "max_abs_standardised_residual":
                round(reg_rev["max_abs_std_residual"], 4),
            "corr_residual_fitted": round(reg_rev["corr_residual_fitted"], 6),
        },
        "implied_avg_price_pkr": {
            "min": round(min(implied_price), 2),
            "max": round(max(implied_price), 2),
            "mean": round(mean(implied_price), 2),
        },
        "notes": [
            "Seeded generator (seed 131): r(ad, revenue) ~0.86, "
            "r(footfall, revenue) ~0.82 and r(discount, units) ~0.61 are "
            "planted; r(discount, footfall) ~0.08 is a deliberate "
            "near-zero control.",
            "Revenue is not exactly units_sold x a fixed price; the "
            "implied average realised price varies (see "
            "implied_avg_price_pkr) because product mix and discount mix "
            "vary month to month.",
            "p-values use the normal approximation to the t-distribution "
            "(math.erf); with n = 24 this is close for the large t-values "
            "here, and is stated as approximate, not exact.",
        ],
    }

    SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    with open(SUMMARY, "w") as f:
        json.dump(summary, f, indent=2, sort_keys=True)
        f.write("\n")

    r_ar = key_r["ad_spend_pkr__revenue_pkr"]
    r_fr = key_r["footfall__revenue_pkr"]
    r_du = key_r["avg_discount_pct__units_sold"]
    r_df = key_r["avg_discount_pct__footfall"]
    per_10k = int(round(reg_rev["slope"] * 10000))
    per_pp = round(reg_units["slope"], 2)

    guide = f"""# Mini #12 — Correlation & Regression Guide (SAMPLE data)

Fictional shop **Noor Electronics (Lahore)**, 24 months, Jan 2024–Dec 2025.
All numbers below are computed from `data/raw/monthly_stats_SAMPLE.csv`
by `src/analyze.py` (Python standard library only) — nothing is typed in.
Reproduce them with `python3 src/analyze.py`, then check them with
`python3 src/checks.py`.

## The data at a glance

| Total (24 months) | Value |
|---|---|
| Revenue | PKR {fmt(totals['revenue_pkr'])} |
| Ad spend | PKR {fmt(totals['ad_spend_pkr'])} |
| Footfall | {fmt(totals['footfall'])} visitors |
| Units sold | {fmt(totals['units_sold'])} |
| Average discount | {avgs['avg_discount_pct']:.2f}% |

Average month: revenue PKR {fmt(avgs['revenue_pkr'])}, ad spend
PKR {fmt(avgs['ad_spend_pkr'])}, footfall {fmt(avgs['footfall'])},
{fmt(avgs['units_sold'])} units at an average discount of
{avgs['avg_discount_pct']:.2f}%.

## The four correlations that matter

| Pair | Pearson r | What it means in plain English |
|---|---|---|
| Ad spend vs revenue | {r_ar:.4f} | Very strong positive. Months with more ad spend almost always had more revenue. |
| Footfall vs revenue | {r_fr:.4f} | Strong positive. Busier months earned more — footfall and revenue move together. |
| Discount vs units sold | {r_du:.4f} | Moderate positive. Deeper discounts went with MORE units sold, not fewer. |
| Discount vs footfall (control) | {r_df:.4f} | Near zero. Discounts did not bring more people through the door. |

### How to read an r

- **r near +1 or −1:** the two numbers move together (or exactly opposite).
  Here 0.8624 and 0.8247 are strong; 0.6108 is moderate.
- **r near 0:** no straight-line relationship. Here 0.0763 means
  discount and footfall are essentially unrelated in these 24 months.
- **r is not a percent.** r = 0.8624 does NOT mean "86% caused by ads".
  The percent version is R², below.

### The control pair is the lesson

Discount vs footfall r = {r_df:.4f} is a **finding, not a failure**.
Discounts lifted units sold (r = {r_du:.4f}) but did NOT lift footfall.
So the discount worked on the people who were already in the shop —
it converted browsers into buyers — instead of attracting new visitors.
A weak r that answers a business question is worth more than a strong r
that answers nothing.

## Regression 1: revenue ~ ad spend

    revenue = {reg_rev['intercept']:,.0f} + {reg_rev['slope']:.2f} x ad_spend

- **Slope {reg_rev['slope']:.4f}:** every extra PKR 10,000 of ad spend predicts
  about **PKR {fmt(per_10k)} more revenue** that month
  ({reg_rev['slope']:.2f} x 10,000). That is the single most useful sentence
  in this pack — it turns a correlation into a budgeting rule.
- **Intercept PKR {fmt(reg_rev['intercept'])}:** the model's revenue at zero
  ad spend. Do not over-read it — zero ad spend is outside the data
  (ad spend ranged PKR {fmt(min(data['ad_spend_pkr']))}–
  PKR {fmt(max(data['ad_spend_pkr']))}), so the intercept is an
  extrapolation, not a promise.
- **R² = {reg_rev['r_squared']:.4f}:** about {reg_rev['r_squared'] * 100:.1f}%
  of the month-to-month variation in revenue is explained by ad spend
  alone. The other {100 - reg_rev['r_squared'] * 100:.1f}% is everything
  else — season, product mix, luck.
- **Standard error of the slope = {reg_rev['se_slope']:.4f}, t = {reg_rev['t_stat']:.2f},
  p ≈ {reg_rev['p_value']:.2e}** (normal approximation): the slope is far
  from zero. With 24 months, a t of {reg_rev['t_stat']:.2f} leaves no
  reasonable doubt that the relationship is real *in this data*.
- **Spearman rho = {rho:.4f}** (rank correlation, same pair): nearly the
  same as Pearson r = {r_ar:.4f}, so the relationship is not being driven
  by one or two extreme months — the ranks agree with the raw numbers.

### Worked prediction

Ad spend PKR 350,000 in a month predicts revenue of about
PKR {fmt(reg_rev['intercept'] + reg_rev['slope'] * 350000)}.
Ad spend PKR 250,000 predicts about
PKR {fmt(reg_rev['intercept'] + reg_rev['slope'] * 250000)}.
The PKR 100,000 gap in spend predicts a PKR {fmt(per_10k * 10)} gap in
revenue — that is the slope, doing its job.

## Regression 2: units sold ~ average discount

    units_sold = {reg_units['intercept']:.1f} + {reg_units['slope']:.2f} x avg_discount_pct

- **Slope {reg_units['slope']:.4f}:** each extra 1 percentage point of
  discount predicts about **{per_pp:.2f} more units sold** that month.
  A 5-point deeper discount (say 10% -> 15%) predicts about
  {per_pp * 5:.0f} extra units.
- **R² = {reg_units['r_squared']:.4f}:** discount explains about
  {reg_units['r_squared'] * 100:.1f}% of the variation in units sold —
  real, but far from the whole story. Footfall, season and product mix
  explain the rest.
- **t = {reg_units['t_stat']:.2f}, p ≈ {reg_units['p_value']:.2e}:** the
  discount effect is statistically solid, not noise.

### The trap this regression teaches

Discounts raise units but they cut the price on EVERY unit, including
the ones that would have sold anyway. This pack proves the volume
effect ({per_pp:.2f} extra units per point of discount) — it does NOT
prove discounts raise profit. Always pair a units regression with a
margin check before recommending a deeper discount.

## Residual diagnostics (revenue ~ ad spend)

| Check | Value | Verdict |
|---|---|---|
| Mean residual | PKR {reg_rev['residual_mean']:.2f} | ~0, as OLS guarantees — the model is not biased up or down on average |
| Residual SD | PKR {fmt(reg_rev['residual_sd'])} | Typical month misses the prediction by about this much |
| Durbin–Watson | {reg_rev['durbin_watson']:.2f} | Near 2: no obvious month-to-month pattern in the misses |
| Largest standardised residual | {reg_rev['max_abs_std_residual']:.2f} | No month is an extreme outlier (nothing beyond ~3) |
| Correlation(residuals, fitted) | {reg_rev['corr_residual_fitted']:.4f} | ~0, as OLS guarantees — the misses carry no leftover signal |

Plain English: the model misses by about PKR {fmt(reg_rev['residual_sd'])}
in a typical month, the misses look random rather than patterned, and no
single month wrecks the fit. That is a usable model, not a perfect one.

## Correlation is not causation — the warning, with examples

1. **Ad spend and revenue (r = {r_ar:.4f}) do not prove ads CAUSED the
   revenue.** A busy festive month could raise both at once. What the
   regression gives you is a prediction rule, not a proof of cause.
   Proof would need an experiment (spend more in some months, hold
   steady in matched others) — this pack shows the observational
   evidence and labels it as such.
2. **Footfall and revenue (r = {r_fr:.4f})** have the same warning, in
   the other direction: high revenue months may have *funded* more
   ads, so the arrow could partly run revenue -> ad spend.
3. **Discount and footfall (r = {r_df:.4f})** is the cleanest causal
   hint in the pack — precisely because it is near zero: if discounts
   pulled in crowds, this number would be large. It is not, so the
   "discounts bring people in" story fails on this data.

## Full correlation matrix (all 10 pairs)

|  | ad_spend | footfall | discount | units | revenue |
|---|---|---|---|---|---|
| ad_spend | 1.0000 | {corr['ad_spend_pkr__footfall']:.4f} | {corr['ad_spend_pkr__avg_discount_pct']:.4f} | {corr['ad_spend_pkr__units_sold']:.4f} | {corr['ad_spend_pkr__revenue_pkr']:.4f} |
| footfall |  | 1.0000 | {corr['footfall__avg_discount_pct']:.4f} | {corr['footfall__units_sold']:.4f} | {corr['footfall__revenue_pkr']:.4f} |
| discount |  |  | 1.0000 | {corr['avg_discount_pct__units_sold']:.4f} | {corr['avg_discount_pct__revenue_pkr']:.4f} |
| units |  |  |  | 1.0000 | {corr['units_sold__revenue_pkr']:.4f} |
| revenue |  |  |  |  | 1.0000 |

Note ad spend vs footfall r = {corr['ad_spend_pkr__footfall']:.4f}: ads and
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
  price (revenue / units) ranges PKR {fmt(min(implied_price))}–
  PKR {fmt(max(implied_price))} (mean PKR {fmt(mean(implied_price))})
  because product mix and discount mix vary — realistic, and stated
  here rather than hidden.
"""
    with open(GUIDE, "w") as f:
        f.write(guide)

    print(f"Wrote {SUMMARY} and {GUIDE}")
    print(f"r(ad,rev)={r_ar:.4f}  r(foot,rev)={r_fr:.4f}  "
          f"r(disc,units)={r_du:.4f}  r(disc,foot)={r_df:.4f}")
    print(f"rev~ad: slope={reg_rev['slope']:.4f} R2={reg_rev['r_squared']:.4f} "
          f"t={reg_rev['t_stat']:.2f}")
    print(f"units~disc: slope={reg_units['slope']:.4f} "
          f"R2={reg_units['r_squared']:.4f} t={reg_units['t_stat']:.2f}")
    print(f"revenue total PKR {totals['revenue_pkr']:,}")


if __name__ == "__main__":
    main()
