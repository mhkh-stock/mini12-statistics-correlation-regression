"""Checks for Mini #12 (run: python3 src/checks.py).

Every headline number is recomputed here from the raw CSV with
independent sum-based formulas (Sxy / sqrt(Sxx*Syy) for Pearson,
normal-equation OLS) and compared against outputs/summary.json and
outputs/correlation_regression_guide.md — nothing is trusted on the
word of analyze.py. The generator's determinism is checked by
re-running it and comparing file hashes.

A check fails loudly (AssertionError naming the check); the run prints
the pass count only when all checks pass.
"""

import csv
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSV = ROOT / "data" / "raw" / "monthly_stats_SAMPLE.csv"
SUMMARY = ROOT / "outputs" / "summary.json"
GUIDE = ROOT / "outputs" / "correlation_regression_guide.md"
MINI11 = (ROOT.parent / "mini11-excel-pivot-tables-charts" / "LICENSE")

PASSED = 0


def check(name, cond):
    global PASSED
    assert cond, f"FAIL: {name}"
    PASSED += 1


def close(a, b, tol):
    return abs(a - b) <= tol


# ------------------------------------------------- independent statistics
def pearson_ind(xs, ys):
    """Sum-based Pearson r: Sxy / sqrt(Sxx * Syy)."""
    n = len(xs)
    sx, sy = sum(xs), sum(ys)
    sxx = sum(x * x for x in xs) - sx * sx / n
    syy = sum(y * y for y in ys) - sy * sy / n
    sxy = sum(x * y for x, y in zip(xs, ys)) - sx * sy / n
    return sxy / math.sqrt(sxx * syy)


def ranks_ind(values):
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


def ols_ind(xs, ys):
    """Normal-equation OLS: slope = Sxy/Sxx, intercept = ybar - b*xbar."""
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    b = sxy / sxx
    a = my - b * mx
    fit = [a + b * x for x in xs]
    res = [y - f for y, f in zip(ys, fit)]
    ss_res = sum(r * r for r in res)
    ss_tot = sum((y - my) ** 2 for y in ys)
    se = math.sqrt(ss_res / (n - 2) / sxx)
    t = b / se
    p = 2 * (1 - 0.5 * (1 + math.erf(abs(t) / math.sqrt(2))))
    dw = sum((res[i] - res[i - 1]) ** 2 for i in range(1, n)) / ss_res
    return {"a": a, "b": b, "r2": 1 - ss_res / ss_tot, "se": se, "t": t,
            "p": p, "res_mean": sum(res) / n,
            "res_sd": math.sqrt(ss_res / (n - 2)), "dw": dw,
            "max_std_res": max(abs(r) / math.sqrt(ss_res / (n - 2))
                               for r in res),
            "corr_res_fit": pearson_ind(res, fit)}


# ------------------------------------------------------------------- data
rows = list(csv.DictReader(open(CSV)))
for r in rows:
    r["ad_spend_pkr"] = int(r["ad_spend_pkr"])
    r["footfall"] = int(r["footfall"])
    r["avg_discount_pct"] = float(r["avg_discount_pct"])
    r["units_sold"] = int(r["units_sold"])
    r["revenue_pkr"] = int(r["revenue_pkr"])

check("CSV has 24 monthly rows", len(rows) == 24)
check("CSV columns exact", list(rows[0].keys()) == [
    "month", "ad_spend_pkr", "footfall", "avg_discount_pct",
    "units_sold", "revenue_pkr"])
check("months are Jan 2024–Dec 2025, consecutive, no gaps",
      [r["month"] for r in rows]
      == [f"{y}-{m:02d}" for y in (2024, 2025) for m in range(1, 13)])
check("no missing or zero values",
      all(v not in (None, "", 0) for r in rows for v in r.values()
          if isinstance(v, (int, float))))
check("all money / count columns are positive",
      all(r[c] > 0 for r in rows
          for c in ("ad_spend_pkr", "footfall", "units_sold", "revenue_pkr")))
check("discounts inside the 4–20% clamp",
      all(4.0 <= r["avg_discount_pct"] <= 20.0 for r in rows))
check("revenue total PKR 124,817,600",
      sum(r["revenue_pkr"] for r in rows) == 124817600)
check("ad spend total PKR 7,034,000",
      sum(r["ad_spend_pkr"] for r in rows) == 7034000)
check("footfall total 121,657", sum(r["footfall"] for r in rows) == 121657)
check("units total 14,649", sum(r["units_sold"] for r in rows) == 14649)
check("implied avg price stays in a plausible PKR 6,000–12,000 band",
      all(6000 <= r["revenue_pkr"] / r["units_sold"] <= 12000
          for r in rows))

X = {c: [r[c] for r in rows] for c in
     ("ad_spend_pkr", "footfall", "avg_discount_pct", "units_sold",
      "revenue_pkr")}

# ------------------------------------------------- correlations (recompute)
r_ar = pearson_ind(X["ad_spend_pkr"], X["revenue_pkr"])
r_fr = pearson_ind(X["footfall"], X["revenue_pkr"])
r_du = pearson_ind(X["avg_discount_pct"], X["units_sold"])
r_df = pearson_ind(X["avg_discount_pct"], X["footfall"])
check("r(ad, revenue) is strong: 0.80–0.90", 0.80 <= r_ar <= 0.90)
check("r(footfall, revenue) is strong: 0.75–0.85", 0.75 <= r_fr <= 0.85)
check("r(discount, units) is moderate-positive: 0.50–0.70",
      0.50 <= r_du <= 0.70)
check("control r(discount, footfall) is near zero: |r| <= 0.20",
      abs(r_df) <= 0.20)
check("r(ad, footfall) is very strong (>= 0.90) — shared driver",
      pearson_ind(X["ad_spend_pkr"], X["footfall"]) >= 0.90)
check("all 10 pairwise correlations are inside [-1, 1]",
      all(-1 <= pearson_ind(X[a], X[b]) <= 1
          for i, a in enumerate(X) for b in list(X)[i + 1:]))

rho = pearson_ind(ranks_ind(X["ad_spend_pkr"]),
                  ranks_ind(X["revenue_pkr"]))
check("Spearman rho(ad, revenue) agrees with Pearson (|diff| < 0.05)",
      abs(rho - r_ar) < 0.05)

# --------------------------------------------------- regressions (recompute)
reg1 = ols_ind(X["ad_spend_pkr"], X["revenue_pkr"])
reg2 = ols_ind(X["avg_discount_pct"], X["units_sold"])
check("rev~ad slope is positive and near 10.55 PKR per PKR",
      10.0 <= reg1["b"] <= 11.0)
check("rev~ad R² is in [0, 1] and near 0.74", 0.70 <= reg1["r2"] <= 0.78)
check("rev~ad R² equals r² (simple OLS identity)",
      close(reg1["r2"], r_ar ** 2, 0.001))
check("rev~ad t-stat is large (> 5)", reg1["t"] > 5)
check("rev~ad p-value is tiny (< 1e-10)", reg1["p"] < 1e-10)
check("rev~ad fitted mean equals mean revenue (OLS passes through means)",
      close(reg1["a"] + reg1["b"] * (sum(X["ad_spend_pkr"]) / 24),
            sum(X["revenue_pkr"]) / 24, 0.01))
check("rev~ad residual mean is ~0 (|mean| < 1e-6)",
      abs(reg1["res_mean"]) < 1e-6)
check("rev~ad Durbin-Watson near 2 (1.5–2.5, no autocorrelation)",
      1.5 <= reg1["dw"] <= 2.5)
check("rev~ad no extreme outlier (|std residual| < 3)",
      reg1["max_std_res"] < 3)
check("units~disc slope is positive: ~15.5 units per point",
      12.0 <= reg2["b"] <= 19.0)
check("units~disc R² is in [0, 1] and near 0.37",
      0.30 <= reg2["r2"] <= 0.45)
check("units~disc R² equals r² (simple OLS identity)",
      close(reg2["r2"], r_du ** 2, 0.001))
check("units~disc t-stat is significant (> 3)", reg2["t"] > 3)
check("units~disc p-value is small (< 0.01)", reg2["p"] < 0.01)

# ------------------------------------------------------- summary.json match
S = json.loads(SUMMARY.read_text())
check("summary months = 24", S["months"] == 24)
check("summary period is 2024-01 to 2025-12",
      S["period"] == "2024-01 to 2025-12")
check("summary totals match recompute",
      S["totals"] == {"ad_spend_pkr": 7034000, "footfall": 121657,
                      "units_sold": 14649, "revenue_pkr": 124817600})
check("summary key correlations match recompute (within 0.001)",
      close(S["key_correlations"]["ad_spend_pkr__revenue_pkr"], r_ar, 0.001)
      and close(S["key_correlations"]["footfall__revenue_pkr"], r_fr, 0.001)
      and close(S["key_correlations"]["avg_discount_pct__units_sold"],
                r_du, 0.001)
      and close(S["key_correlations"]["avg_discount_pct__footfall"],
                r_df, 0.001))
check("summary holds all 10 pairwise correlations",
      len(S["correlations"]) == 10)
check("summary Spearman matches recompute (within 0.001)",
      close(S["spearman_ad_spend_revenue"], rho, 0.001))
R1 = S["regression_revenue_on_ad_spend"]
check("summary rev~ad slope/intercept/R²/SE/t match recompute",
      close(R1["slope_pkr_per_pkr"], reg1["b"], 0.001)
      and close(R1["intercept_pkr"], reg1["a"], 0.01)
      and close(R1["r_squared"], reg1["r2"], 0.001)
      and close(R1["se_slope"], reg1["se"], 0.001)
      and close(R1["t_stat"], reg1["t"], 0.01))
check("summary rev~ad p-value matches recompute (rel. tol. 0.1%)",
      close(R1["p_value_normal_approx"], reg1["p"], reg1["p"] * 0.001))
check("summary rev~ad per-PKR-10,000 slope is slope x 10,000",
      close(R1["slope_per_pkr_10000_ad_spend"], reg1["b"] * 10000, 1.0))
R2 = S["regression_units_on_discount"]
check("summary units~disc slope/intercept/R²/SE/t match recompute",
      close(R2["slope_units_per_pct_point"], reg2["b"], 0.001)
      and close(R2["intercept_units"], reg2["a"], 0.01)
      and close(R2["r_squared"], reg2["r2"], 0.001)
      and close(R2["se_slope"], reg2["se"], 0.001)
      and close(R2["t_stat"], reg2["t"], 0.01))
check("summary units~disc p-value matches recompute (rel. tol. 0.1%)",
      close(R2["p_value_normal_approx"], reg2["p"], reg2["p"] * 0.001))
D = S["residual_diagnostics_revenue_on_ad_spend"]
check("summary residual diagnostics match recompute",
      close(D["durbin_watson"], reg1["dw"], 0.001)
      and close(D["max_abs_standardised_residual"], reg1["max_std_res"],
                0.001)
      and close(D["residual_sd_pkr"], reg1["res_sd"], 0.01)
      and abs(D["mean_residual_pkr"]) < 1e-6)
check("summary implied-price band matches recompute",
      close(S["implied_avg_price_pkr"]["min"],
            min(r["revenue_pkr"] / r["units_sold"] for r in rows), 0.01)
      and close(S["implied_avg_price_pkr"]["max"],
                max(r["revenue_pkr"] / r["units_sold"] for r in rows), 0.01))
check("summary labels the data SAMPLE",
      "SAMPLE" in S["status"])

# ------------------------------------------------------------- guide content
g = GUIDE.read_text()
check("guide contains all 4 headline r values",
      all(f"{v:.4f}" in g for v in (r_ar, r_fr, r_du, r_df)))
check("guide contains the per-PKR-10,000 prediction",
      f"{reg1['b'] * 10000:,.0f}" in g)
check("guide contains the revenue total",
      "124,817,600" in g)
check("guide contains both R² values",
      f"{reg1['r2']:.4f}" in g and f"{reg2['r2']:.4f}" in g)
check("guide contains the Spearman rho",
      f"{rho:.4f}" in g)
check("guide contains the worked predictions for PKR 350k / 250k ad spend",
      f"{reg1['a'] + reg1['b'] * 350000:,.0f}" in g
      and f"{reg1['a'] + reg1['b'] * 250000:,.0f}" in g)
check("guide states the causation warning",
      "correlation is not causation" in g.lower())
check("guide labels the data SAMPLE", "SAMPLE" in g)
check("guide names the control pair as a finding, not a failure",
      "finding, not a failure" in g)

# ------------------------------------------------------- determinism (re-run)
def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


csv_before, sum_before = sha(CSV), sha(SUMMARY)
subprocess.run([sys.executable, str(ROOT / "src" / "generate_data.py")],
               check=True, capture_output=True)
check("generate_data.py is deterministic (CSV hash unchanged)",
      sha(CSV) == csv_before)
subprocess.run([sys.executable, str(ROOT / "src" / "analyze.py")],
               check=True, capture_output=True)
check("analyze.py is deterministic (summary hash unchanged)",
      sha(SUMMARY) == sum_before)

# ------------------------------------------------------------ labels & files
readme = (ROOT / "README.md").read_text()
check("README labels the data SAMPLE", "SAMPLE" in readme)
check("README states the data is never real client work",
      "never claimed as real client work" in readme.lower())
check("README contains the 4 headline r values",
      all(f"{v:.4f}" in readme for v in (r_ar, r_fr, r_du, r_df)))
check("README contains the revenue total", "124,817,600" in readme)
check("README contains the per-PKR-10,000 prediction",
      f"{reg1['b'] * 10000:,.0f}" in readme)
check("data README exists and documents all 6 columns",
      (ROOT / "data" / "README.md").exists()
      and all(c in (ROOT / "data" / "README.md").read_text()
              for c in ("month", "ad_spend_pkr", "footfall",
                        "avg_discount_pct", "units_sold", "revenue_pkr")))
check("requirements.txt states standard-library-only",
      "standard library only" in (ROOT / "requirements.txt").read_text().lower())
check("LICENSE exists and is identical to Mini #11's MIT license",
      (ROOT / "LICENSE").exists()
      and (ROOT / "LICENSE").read_bytes() == MINI11.read_bytes())
check("guide file exists", GUIDE.exists())
check("summary file exists", SUMMARY.exists())

print(f"\n{PASSED} checks passed, 0 failed.")
