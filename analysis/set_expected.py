"""Write expected/*.json from a run's stats.json (used once, to record the canonical Docker run).

  python analysis/set_expected.py outputs/full/stats.json expected/paper_values.json full
  python analysis/set_expected.py outputs/quick/stats.json expected/quick_values.json quick
Each number is stored rounded to the precision at which the paper prints it.
"""
import json
import sys

# quantity -> decimals (negative = round to tens/hundreds/...; "str" = exact string)
FULL = {"datasets": 0, "studies_total": 0, "dose_levels_total": 0, "datasets_analysed": 0, "studies_excluded_missing_counts": 0,
        "studies_analysed": 0, "before_linear_match": 0, "before_linear_centred_match": 0, "linear_datasets_with_nonzero_reference": 0,
        "before_linear_max_absdiff": 3, "before_linear_worst_dataset": "str", "spline3_fitted_by_R": 0, "spline4_fitted_by_R": 0,
        "spline3_refused_by_R": 0, "spline4_refused_by_R": 0, "before_spline3_match": 0, "before_spline4_match": 0,
        "before_refused_but_returned": 0, "before_refused_coef_exceeds_1e12": 0, "grid_fits": 0, "grid_R_fitted": 0, "grid_R_refused": 0,
        "grid_refusals_matched": 0, "grid_app_refused_R_fitted": 0, "grid_within_tolerance": 0, "grid_all_within_tolerance": 0,
        "after_iterative_coef_below_1e-4_SE": 0, "after_iterative_loglik_below_1e-7": 0, "after_direct_coef_below_1e-6_SE": 0,
        "R_one_stage_not_converged": 0, "after_linear_match": 0, "after_spline3_match": 0, "after_spline4_match": 0,
        "after_refused_but_returned": 0, "ex_k": 0, "ex_nonzero_ref": 0, "ex_R_slope": 4, "ex_before_slope": 4, "ex_after_slope": 4,
        "ex_grid_dose": 2, "ex_rr_R": 2, "ex_spline_below_1e-8": 0}
QUICK = {"datasets": 0, "before_linear_match": 0, "after_linear_match": 0, "before_spline4_match": 0, "after_spline4_match": 0,
         "spline4_fitted_by_R": 0, "grid_fits": 0, "grid_all_within_tolerance": 0, "grid_refusals_matched": 0, "ex_R_slope": 4, "ex_after_slope": 4}

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
