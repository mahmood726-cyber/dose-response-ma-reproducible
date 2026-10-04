"""Write expected/*.json from a run's stats.json (used once, to record the canonical Docker run).

  python analysis/set_expected.py outputs/full/stats.json expected/paper_values.json full
  python analysis/set_expected.py outputs/quick/stats.json expected/quick_values.json quick
Each number is stored rounded to the precision at which the paper prints it.
"""
import json
import sys

# quantity -> decimals (negative = round to tens/hundreds/...; "str" = exact string)
FULL = {"datasets": 0, "studies_total": 0, "dose_levels_total": 0, "datasets_analysed": 0, "studies_excluded_missing_counts": 0,
        "studies_analysed": 0, "grid_fits": 0, "grid_R_fitted": 0, "grid_R_refused": 0, "grid_refusals_matched": 0,
        "grid_app_refused_R_fitted": 0, "grid_app_fitted_R_refused": 0, "grid_within_tolerance": 0, "grid_all_within_tolerance": 0,
        "iterative_fits": 0, "direct_fits": 0, "iterative_coef_below_1e-4_SE": 0, "iterative_loglik_below_1e-7": 0,
        "direct_coef_below_1e-6_SE": 0, "R_one_stage_not_converged": 0, "linear_fitted_by_R": 0, "linear_agree": 0,
        "spline3_fitted_by_R": 0, "spline3_agree": 0, "spline3_refused_by_R": 0, "spline3_refusals_matched": 0,
        "spline4_fitted_by_R": 0, "spline4_agree": 0, "spline4_refused_by_R": 0, "spline4_refusals_matched": 0,
        "spline5_fitted_by_R": 0, "spline5_agree": 0, "spline5_refused_by_R": 0, "spline5_refusals_matched": 0,
        "linear_datasets_with_nonzero_reference": 0, "ex_k": 0, "ex_nonzero_ref": 0, "ex_R_slope": 4, "ex_app_slope": 4,
        "ex_R_slope_se": 4, "ex_knots": "str", "ex_nonlin_chi2": 1, "ex_nonlin_p_below_1e-4": 0, "ex_I2": 0, "ex_grid_dose": 0,
        "ex_rr_R": 2, "ex_rr_lo": 2, "ex_rr_hi": 2, "ex_spline_below_1e-8": 0}
QUICK = {"datasets": 0, "grid_fits": 0, "grid_all_within_tolerance": 0, "grid_refusals_matched": 0, "linear_agree": 0,
         "spline4_fitted_by_R": 0, "spline4_agree": 0, "ex_R_slope": 4, "ex_app_slope": 4}

stats, out, mode = sys.argv[1:4]
st = json.load(open(stats))
spec = FULL if mode == "full" else QUICK
vals = {}
for k, d in spec.items():
    if d == "str":
        vals[k] = {"value": st[k], "decimals": 0}
    else:
        v = round(float(st[k]), d)
        vals[k] = {"value": int(v) if d <= 0 else v, "decimals": d}
json.dump({"source": f"Canonical run ({mode} mode): values as printed in the paper.", "values": vals}, open(out, "w"), indent=1)
print(f"wrote {len(vals)} expected values to {out}")
