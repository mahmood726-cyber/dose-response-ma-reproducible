"""Write expected/*.json from a run's stats.json (used once, to record the canonical Docker run).

  python analysis/set_expected.py outputs/full/stats.json expected/paper_values.json full
  python analysis/set_expected.py outputs/quick/stats.json expected/quick_values.json quick
Each number is stored rounded to the precision at which the paper prints it.
"""
import json
import sys

# quantity -> decimals (negative = round to tens/hundreds/...; "str" = exact string)
FULL = {"datasets": 0, "studies_total": 0, "dose_levels_total": 0, "datasets_with_reference": 0,
        "studies_excluded_missing_counts": 0, "studies_analysed": 0, "linear_match_shipped": 0, "linear_match_centred": 0,
        "linear_datasets_with_nonzero_reference": 0, "linear_max_absdiff_slope_shipped": 3, "linear_worst_dataset_shipped": "str",
        "linear_max_absdiff_slope_centred": 7, "linear_max_absdiff_se_centred": 7, "spline3_fitted_by_R": 0, "spline3_match": 0,
        "spline3_max_absdiff": 7, "spline3_max_absdiff_fitted": 6, "spline4_fitted_by_R": 0, "spline4_match": 0,
        "spline3_refused_by_R": 0, "spline4_refused_by_R": 0, "refused_but_app_returned": 0, "spline4_refused_app_coef_exceeds_1e12": 0,
        "ex_k": 0, "ex_nonzero_ref": 0, "ex_R_slope": 4, "ex_app_slope": 4, "ex_app_centred_slope": 4, "ex_spline_max_diff_fitted": 8,
        "ex_grid_dose_near3": 2, "ex_rr_at_3cups_R": 2}
QUICK = {"datasets": 0, "linear_match_shipped": 0, "linear_match_centred": 0, "spline3_fitted_by_R": 0, "spline3_match": 0,
         "spline4_fitted_by_R": 0, "spline4_match": 0, "spline4_refused_by_R": 0, "ex_R_slope": 4, "ex_app_slope": 4}

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
