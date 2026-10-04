"""Write docs/numbers.json: every number printed in docs/paper.md, its value as printed, and the stats key it comes from.

  python docs/make_numbers.py outputs/full/stats.json "<source description>"
Fails if a printed value is not what the run gives after rounding as printed.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# (quantity, as printed, stats key, how the printed text is derived from the value)
N = [
    ("Multi-study binary datasets in dosresmeta", "17", "datasets", "int"),
    ("Studies in those datasets", "203", "studies_total", "int"),
    ("Dose levels", "890", "dose_levels_total", "int"),
    ("Studies excluded (missing counts)", "16", "studies_excluded_missing_counts", "int"),
    ("Datasets analysed", "16", "datasets_analysed", "int"),
    ("Studies analysed", "187", "studies_analysed", "int"),
    ("Model/option combinations", "724", "grid_fits", "int"),
    ("Combinations agreeing", "724", "grid_within_tolerance", "int"),
    ("Combinations dosresmeta fits", "576", "grid_R_fitted", "int"),
    ("Combinations dosresmeta refuses", "148", "grid_R_refused", "int"),
    ("Refusals the app matches", "148", "grid_refusals_matched", "int"),
    ("Fixed/MM/one-stage coefficients within 10^-6 SE", "yes", "direct_coef_below_1e-6_SE", "flag"),
    ("Two-stage REML/ML coefficients within 10^-4 SE", "yes", "iterative_coef_below_1e-4_SE", "flag"),
    ("Two-stage REML/ML log-likelihoods within 10^-7", "yes", "iterative_loglik_below_1e-7", "flag"),
    ("dosresmeta one-stage fits stopped at the evaluation limit", "120", "R_one_stage_not_converged", "int"),
    ("Linear trend: datasets agreeing", "16", "linear_agree", "int"),
    ("Linear trend: datasets with non-zero reference doses", "12", "linear_datasets_with_nonzero_reference", "int"),
    ("Three-knot spline: datasets agreeing", "15", "spline3_agree", "int"),
    ("Three-knot spline: refused by both", "1", "spline3_refusals_matched", "int"),
    ("Four-knot spline: datasets agreeing", "3", "spline4_agree", "int"),
    ("Four-knot spline: refused by both", "13", "spline4_refusals_matched", "int"),
    ("Five-knot spline: datasets agreeing", "2", "spline5_agree", "int"),
    ("Five-knot spline: refused by both", "14", "spline5_refusals_matched", "int"),
    ("Worked example: studies", "22", "ex_k", "int"),
    ("Worked example: linear slope (dosresmeta)", "−0.0326", "ex_R_slope", "4dp"),
    ("Worked example: linear slope (app)", "−0.0326", "ex_app_slope", "4dp"),
    ("Worked example: slope SE", "0.0050", "ex_R_slope_se", "4dp"),
    ("Worked example: knots (cups/day)", "0/2/6.5", "ex_knots", "0/2/6.5"),
    ("Worked example: non-linearity chi-squared", "24.5", "ex_nonlin_chi2", "1dp"),
    ("Worked example: non-linearity p < 0.0001", "yes", "ex_nonlin_p_below_1e-4", "flag"),
    ("Worked example: I-squared (%)", "59", "ex_I2", "int"),
    ("Worked example: dose of the reported RR (cups/day)", "2", "ex_grid_dose", "int"),
    ("Worked example: RR at 2 cups/day", "0.87", "ex_rr_R", "2dp"),
    ("Worked example: RR lower 95% limit", "0.84", "ex_rr_lo", "2dp"),
    ("Worked example: RR upper 95% limit", "0.90", "ex_rr_hi", "2dp"),
    ("Worked example: app and dosresmeta within 10^-8", "yes", "ex_spline_below_1e-8", "flag"),
]


def shown(v, how):
    if how == "int": return str(int(round(v)))
    if how == "flag": return "yes" if v == 1 else "no"
    if how.endswith("dp"): return f"{v:.{int(how[0])}f}".replace("-", "−")
    return how if v == how else f"MISMATCH {v}"


st = json.loads(Path(sys.argv[1]).read_text())
src = sys.argv[2]
out, bad = [], []
for q, printed, key, how in N:
    v = st[key]; s = shown(v, how)
    ok = s == printed or (isinstance(v, str) and v == printed)
    if not ok: bad.append(f"{q}: printed {printed!r}, run gives {s!r}")
    out.append({"quantity": q, "as_printed": printed, "canonical_value": v, "stats_key": key, "source": src,
                "checked_by": "expected/paper_values.json (reproduce.py PASS/FAIL on Docker, Linux, Windows, macOS)"})
(ROOT / "docs" / "numbers.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"wrote {len(out)} numbers to docs/numbers.json")
if bad: sys.exit("MISMATCH:\n  " + "\n  ".join(bad))
