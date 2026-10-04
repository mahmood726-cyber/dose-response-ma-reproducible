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
    ("Original app: linear trend agrees (of 16)", "4", "before_linear_match", "int"),
    ("Datasets with a non-zero reference dose", "12", "linear_datasets_with_nonzero_reference", "int"),
    ("Original app: largest linear slope error", "0.056", "before_linear_max_absdiff", "3dp"),
    ("Dataset with the largest slope error", "BMI and renal cancer (bmi_rc)", "before_linear_worst_dataset", "bmi_rc"),
    ("Four-knot spline fits dosresmeta can make", "3", "spline4_fitted_by_R", "int"),
    ("Original app: four-knot spline agrees", "0", "before_spline4_match", "int"),
    ("Original app: refused fits returned", "14", "before_refused_but_returned", "int"),
    ("Original app: coefficients above 10^12 in a refused fit", "yes", "before_refused_coef_exceeds_1e12", "flag"),
    ("Combinations dosresmeta fits", "576", "grid_R_fitted", "int"),
    ("Combinations dosresmeta refuses", "148", "grid_R_refused", "int"),
    ("Refusals the corrected app matches", "148", "grid_refusals_matched", "int"),
    ("Combinations agreeing after correction (abstract: 'all 724')", "724", "grid_within_tolerance", "int"),
    ("Fixed/MM/one-stage coefficients within 10^-6 SE", "yes", "after_direct_coef_below_1e-6_SE", "flag"),
    ("Two-stage REML/ML coefficients within 10^-4 SE", "yes", "after_iterative_coef_below_1e-4_SE", "flag"),
    ("Two-stage REML/ML log-likelihoods within 10^-7", "yes", "after_iterative_loglik_below_1e-7", "flag"),
    ("dosresmeta one-stage fits not converged", "120", "R_one_stage_not_converged", "int"),
    ("Worked example: studies", "22", "ex_k", "int"),
    ("Worked example: studies with a non-zero reference", "12", "ex_nonzero_ref", "int"),
    ("Worked example: dosresmeta linear slope", "−0.0326", "ex_R_slope", "4dp"),
    ("Worked example: original app slope", "−0.0313", "ex_before_slope", "4dp"),
    ("Worked example: corrected app slope", "−0.0326", "ex_after_slope", "4dp"),
    ("Worked example: dose of the reported RR (cups/day)", "2", "ex_grid_dose", "int"),
    ("Worked example: three-knot spline RR at that dose", "0.87", "ex_rr_R", "2dp"),
    ("Worked example: spline matches within 10^-8", "yes", "ex_spline_below_1e-8", "flag"),
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
    ok = s == printed or (how == "bmi_rc" and v == "bmi_rc")
    if not ok: bad.append(f"{q}: printed {printed!r}, run gives {s!r}")
    out.append({"quantity": q, "as_printed": printed, "canonical_value": v, "stats_key": key, "source": src,
                "checked_by": "expected/paper_values.json (reproduce.py PASS/FAIL on Docker, Linux, Windows, macOS)"})
(ROOT / "docs" / "numbers.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"wrote {len(out)} numbers to docs/numbers.json")
if bad: sys.exit("MISMATCH:\n  " + "\n  ".join(bad))
