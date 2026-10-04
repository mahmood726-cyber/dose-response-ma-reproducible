"""Compare the shipped engine with dosresmeta and build every table, figure and number in the paper.

  python analysis/make_outputs.py --results results/full --outputs outputs/full --expected expected/paper_values.json

Agreement is judged against the tolerances the app itself claims on its page:
linear model ~1e-6 and spline model ~1e-5 (absolute difference). Exit code 0 only if every
number in expected/paper_values.json is reproduced exactly (after rounding to its stated decimals).
"""
import argparse
import csv
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

TOL_LIN, TOL_SPL = 1e-6, 1e-5
LABEL = {"alcohol_crc": "Alcohol, colorectal cancer", "alcohol_cvd": "Alcohol, CVD", "alcohol_esoph": "Alcohol, oesophageal cancer",
         "alcohol_lc": "Alcohol, lung cancer", "bmi_rc": "BMI, renal cancer", "coffee_cancer": "Coffee, cancer",
         "coffee_cvd": "Coffee, CVD", "coffee_mort": "Coffee, mortality", "coffee_mort_add": "Coffee, mortality (additional)",
         "coffee_stroke": "Coffee, stroke", "fish_ra": "Fish, rheumatoid arthritis", "milk_mort": "Milk, mortality",
         "milk_ov": "Milk, ovarian cancer", "oc_breast": "Oral contraceptives, breast cancer",
         "process_bc": "Processed meat, bladder cancer", "red_bc": "Red meat, bladder cancer", "sim_os": "Simulated (sim_os)"}


def jl(p):
    return {json.loads(l)["dataset"]: json.loads(l) for l in open(p, encoding="utf-8") if l.strip()}


def maxdiff(a, b):
    return max(abs(x - y) for x, y in zip(a, b)) if a and b else float("nan")


def corpus_info(path):
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    by = defaultdict(lambda: defaultdict(list))
    for r in rows:
        by[r["dataset"]][r["id"]].append(r)
    info = {}
    for ds, studies in by.items():
        ok = {i: s for i, s in studies.items() if all(x["cases"] not in ("NA", "") and x["n"] not in ("NA", "") for x in s)}
        nonref = [sum(1 for x in s if x["se"] not in ("NA", "") and float(x["se"]) != 0) for s in ok.values()]
        info[ds] = {"rows": sum(len(s) for s in studies.values()), "studies": len(studies), "with_counts": len(ok),
                    "lt2": sum(1 for v in nonref if v < 2), "lt3": sum(1 for v in nonref if v < 3)}
    return info, len(rows), sum(len(s) for s in by.values())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", required=True); ap.add_argument("--outputs", required=True); ap.add_argument("--expected", required=True)
    a = ap.parse_args()
    res, out = Path(a.results), Path(a.outputs)
    out.mkdir(parents=True, exist_ok=True)
    R, E = jl(res / "dosresmeta.jsonl"), jl(res / "engine.jsonl")
    info, n_rows, _ = corpus_info(res / "corpus.csv")
    T1, T2, T3 = [], [], []
    st = {"datasets": len(R), "studies_total": sum(v["studies"] for v in info.values()), "dose_levels_total": n_rows}
    for ds in R:
        r, e = R[ds], E[ds]
        if not r["linear"]["ok"]:
            continue
        L, el, ec = r["linear"], e["linear"], e["linear_centred"]
        d_ship, d_cent = abs(el["b"] - L["b"]), abs(ec["b"] - L["b"])
        dse_ship, dse_cent = abs(el["se"] - L["se"]), abs(ec["se"] - L["se"])
        T1.append({"dataset": ds, "label": LABEL[ds], "k": r["k"], "nonzero_ref": e["studies_nonzero_reference"],
                   "R_slope": L["b"], "R_se": L["se"], "app_slope": el["b"], "app_se": el["se"], "app_centred_slope": ec["b"],
                   "absdiff_slope_shipped": d_ship, "absdiff_se_shipped": dse_ship, "absdiff_slope_centred": d_cent, "absdiff_se_centred": dse_cent,
                   "match_shipped": max(d_ship, dse_ship, abs(el["tau2"] - L["tau2"])) <= TOL_LIN,
                   "match_centred": max(d_cent, dse_cent, abs(ec["tau2"] - L["tau2"])) <= TOL_LIN})
        for nk in (3, 4):
            rs, es = r["spline%d" % nk], e.get("spline%d" % nk, {})
            if rs["ok"]:
                dm = max(maxdiff(es["beta"], rs["beta"]), maxdiff(es["cov"], rs["cov"]), maxdiff(es["Psi"], rs["Psi"]))
                dp = maxdiff(es.get("pred"), rs.get("pred")) if rs.get("pred") else float("nan")
                T2.append({"dataset": ds, "label": LABEL[ds], "knots": nk, "k": r["k"], "max_absdiff_coef_cov_psi": dm,
                           "max_absdiff_fitted_logrr": dp, "match": max(dm, 0 if math.isnan(dp) else dp) <= TOL_SPL})
            else:
                T3.append({"dataset": ds, "label": LABEL[ds], "knots": nk, "k": r["k"],
                           "studies_too_few_doses": info[ds]["lt2" if nk == 3 else "lt3"],
                           "R_result": "refused (too few dose levels per study)" if "two-stage" in rs["error"] else rs["error"][:60],
                           "app_returned_estimate": bool(es.get("ok")), "app_max_abs_coef": max(abs(x) for x in es["beta"]) if es.get("beta") else None})
    lin_k = len(T1)
    st.update({
        "datasets_with_reference": lin_k,
        "datasets_excluded_no_counts": sum(1 for ds in R if not R[ds]["linear"]["ok"]),
        "studies_excluded_missing_counts": sum(R[ds]["excluded_studies"] for ds in R),
        "studies_analysed": sum(R[ds]["k"] for ds in R if R[ds]["linear"]["ok"]),
        "linear_match_shipped": sum(t["match_shipped"] for t in T1), "linear_match_centred": sum(t["match_centred"] for t in T1),
        "linear_datasets_with_nonzero_reference": sum(1 for t in T1 if t["nonzero_ref"] > 0),
        "linear_max_absdiff_slope_shipped": max(t["absdiff_slope_shipped"] for t in T1),
        "linear_max_absdiff_slope_centred": max(t["absdiff_slope_centred"] for t in T1),
        "linear_max_absdiff_se_centred": max(t["absdiff_se_centred"] for t in T1),
        "linear_worst_dataset_shipped": max(T1, key=lambda t: t["absdiff_slope_shipped"])["dataset"],
        "spline3_fitted_by_R": sum(1 for t in T2 if t["knots"] == 3), "spline3_match": sum(t["match"] for t in T2 if t["knots"] == 3),
        "spline3_max_absdiff": max(t["max_absdiff_coef_cov_psi"] for t in T2 if t["knots"] == 3),
        "spline3_max_absdiff_fitted": max(t["max_absdiff_fitted_logrr"] for t in T2 if t["knots"] == 3 and not math.isnan(t["max_absdiff_fitted_logrr"])),
        "spline4_fitted_by_R": sum(1 for t in T2 if t["knots"] == 4), "spline4_match": sum(t["match"] for t in T2 if t["knots"] == 4),
        "spline4_max_absdiff": max([t["max_absdiff_coef_cov_psi"] for t in T2 if t["knots"] == 4] or [float("nan")]),
        "spline3_refused_by_R": sum(1 for t in T3 if t["knots"] == 3), "spline4_refused_by_R": sum(1 for t in T3 if t["knots"] == 4),
        "refused_but_app_returned": sum(1 for t in T3 if t["app_returned_estimate"]),
        "spline4_refused_app_max_abs_coef": max((t["app_max_abs_coef"] or 0) for t in T3 if t["knots"] == 4),
    })
    # ---- tables ----
    def write(name, rows, fmt=None):
        with open(out / f"{name}.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    write("table1_linear", T1); write("table2_spline", T2); write("table3_spline_refused", T3)
    # ---- figures ----
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "figure.facecolor": "white", "savefig.facecolor": "white"})
    meta = {"Software": None}
    C = {"ship": "#c0392b", "cent": "#1b6ca8", "spl": "#2e8b57", "ref": "#555555"}
    lg = lambda x: math.log10(max(x, 1e-16))
    # Figure 2: agreement per dataset
    t1 = sorted(T1, key=lambda t: t["absdiff_slope_shipped"])
    y = list(range(len(t1)))
    s3 = {t["dataset"]: t["max_absdiff_coef_cov_psi"] for t in T2 if t["knots"] == 3}
    fig, ax = plt.subplots(figsize=(7.2, 0.33 * len(t1) + 1.5))
    ax.scatter([lg(t["absdiff_slope_shipped"]) for t in t1], [v + 0.18 for v in y], color=C["ship"], s=24, label="Linear, as shipped (raw doses)")
    ax.scatter([lg(t["absdiff_slope_centred"]) for t in t1], y, color=C["cent"], s=24, label="Linear, doses relative to study reference")
    ax.scatter([lg(s3[t["dataset"]]) for t in t1 if t["dataset"] in s3], [v - 0.18 for v, t in zip(y, t1) if t["dataset"] in s3], color=C["spl"], marker="s", s=22, label="3-knot spline (coefficients, covariance, Ψ)")
    ax.axvline(math.log10(TOL_LIN), color=C["ref"], ls="--", lw=0.8); ax.axvline(math.log10(TOL_SPL), color=C["ref"], ls=":", lw=0.8)
    ax.text(math.log10(TOL_LIN), -0.9, " 1e-6", fontsize=7, color=C["ref"]); ax.text(math.log10(TOL_SPL), -0.9, " 1e-5", fontsize=7, color=C["ref"]); ax.set_ylim(-1.2, len(t1) - 0.4)
    ax.set_yticks(y, [t["label"] for t in t1]); ax.set_xlabel("log10 |app − dosresmeta| (largest absolute difference)")
    ax.set_title("Figure 2. Agreement with dosresmeta, by dataset", fontsize=10); ax.grid(axis="x", color="#e5e5e5", lw=0.6)
    ax.legend(loc="lower right", fontsize=7.5, frameon=True); fig.tight_layout(); fig.savefig(out / "figure2_agreement.png", dpi=200, metadata=meta); plt.close(fig)
    with open(out / "figure2_agreement.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["dataset", "absdiff_linear_shipped", "absdiff_linear_centred", "absdiff_spline3"])
        for t in t1: w.writerow([t["dataset"], t["absdiff_slope_shipped"], t["absdiff_slope_centred"], s3.get(t["dataset"], "")])
    # Figure 3: worked example, coffee and mortality
    ex = "coffee_mort"; r, e = R[ex], E[ex]
    g = r["spline3"]["grid"]; xs = [0, max(g)]
    fig, axs = plt.subplots(1, 2, figsize=(8.6, 3.5))
    ax = axs[0]
    for lab, b, col, ls in (("dosresmeta", r["linear"]["b"], C["ref"], "-"), ("App, as shipped", e["linear"]["b"], C["ship"], "--"), ("App, centred doses", e["linear_centred"]["b"], C["cent"], ":")):
        ax.plot(xs, [math.exp(b * x) for x in xs], ls, color=col, lw=1.8, label=f"{lab} (slope {b:+.4f})")
    ax.set_title("A. Linear trend", fontsize=9.5); ax.set_xlabel("Coffee (cups/day)"); ax.set_ylabel("Relative risk of mortality"); ax.legend(fontsize=7, frameon=False)
    ax = axs[1]
    rp, rse, ep = r["spline3"]["pred"], r["spline3"]["pred_se"], e["spline3"]["pred"]
    ax.fill_between(g, [math.exp(p - 1.959963984540054 * s) for p, s in zip(rp, rse)], [math.exp(p + 1.959963984540054 * s) for p, s in zip(rp, rse)], color="#dddddd", label="dosresmeta 95% CI")
    ax.plot(g, [math.exp(p) for p in rp], "-", color=C["ref"], lw=2.2, label="dosresmeta")
    ax.plot(g, [math.exp(p) for p in ep], "o", color=C["spl"], ms=4, label="App (3-knot spline)")
    ax.set_title("B. Restricted cubic spline (3 knots)", fontsize=9.5); ax.set_xlabel("Coffee (cups/day)"); ax.legend(fontsize=7, frameon=False)
    fig.suptitle("Figure 3. Worked example: coffee and all-cause mortality (22 studies)", fontsize=10); fig.tight_layout()
    fig.savefig(out / "figure3_coffee_mortality.png", dpi=200, metadata=meta); plt.close(fig)
    with open(out / "figure3_coffee_mortality.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["dose", "R_logrr", "R_se", "app_logrr"])
        for row in zip(g, rp, rse, ep): w.writerow(row)
    st.update({"ex_k": r["k"], "ex_R_slope": r["linear"]["b"], "ex_app_slope": e["linear"]["b"], "ex_app_centred_slope": e["linear_centred"]["b"],
               "ex_nonzero_ref": e["studies_nonzero_reference"], "ex_spline_max_diff_fitted": maxdiff(ep, rp),
               "ex_rr_at_3cups_R": math.exp(rp[min(range(len(g)), key=lambda i: abs(g[i] - 3))]), "ex_grid_dose_near3": g[min(range(len(g)), key=lambda i: abs(g[i] - 3))]})
    # Figure 4: unidentifiable splines
    t3 = [t for t in T3 if t["app_max_abs_coef"] is not None]
    fig, ax = plt.subplots(figsize=(7.2, 0.33 * len(t3) + 1.5))
    t3s = sorted(t3, key=lambda t: t["app_max_abs_coef"])
    ax.barh(range(len(t3s)), [lg(t["app_max_abs_coef"]) for t in t3s], color=C["ship"])
    ax.set_yticks(range(len(t3s)), [f"{t['label']} ({t['knots']} knots; {t['studies_too_few_doses']} {'study' if t['studies_too_few_doses'] == 1 else 'studies'} with too few doses)" for t in t3s], fontsize=7)
    ax.axvline(0, color=C["ref"], lw=0.8); ax.set_xlabel("log10 of the app's largest |spline coefficient|")
    ax.set_title("Figure 4. Fits dosresmeta refuses, but the app returns", fontsize=10); fig.tight_layout()
    fig.savefig(out / "figure4_refused_fits.png", dpi=200, metadata=meta); plt.close(fig)
    with open(out / "figure4_refused_fits.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["dataset", "knots", "studies_too_few_doses", "app_max_abs_coef"])
        for t in t3s: w.writerow([t["dataset"], t["knots"], t["studies_too_few_doses"], t["app_max_abs_coef"]])
    # Visual abstract
    fig = plt.figure(figsize=(11, 5.6)); fig.patch.set_facecolor("white")
    boxes = [("Problem", "Dose-response meta-analysis\nof published studies is\nusually run in R or Stata\n(two-stage Greenland-\nLongnecker method)."),
             ("Tool", "allmeta dose-response app:\noffline, in the browser.\nLinear trend and restricted\ncubic splines (3 or 4 knots),\nREML pooling."),
             ("Validation", f"Shipped code run unchanged\nagainst R dosresmeta on\n{lin_k} datasets ({st['studies_analysed']} studies)\nbundled with dosresmeta."),
             ("Key results", f"3-knot spline: {st['spline3_match']}/{st['spline3_fitted_by_R']} match\n(max diff {st['spline3_max_absdiff']:.0e}).\nLinear, as shipped: {st['linear_match_shipped']}/{lin_k} match;\nwith doses relative to the\nreference: {st['linear_match_centred']}/{lin_k}.")]
    for i, (h, txt) in enumerate(boxes):
        x = 0.02 + i * 0.245
        fig.patches.append(matplotlib.patches.FancyBboxPatch((x, 0.30), 0.22, 0.55, boxstyle="round,pad=0.01", transform=fig.transFigure, facecolor=["#f4ece8", "#e8f0f7", "#eaf4ec", "#fdf6e3"][i], edgecolor="#999"))
        fig.text(x + 0.11, 0.80, h, ha="center", fontsize=12, weight="bold")
        fig.text(x + 0.11, 0.56, txt, ha="center", va="center", fontsize=9.2)
        if i < 3: fig.text(x + 0.2325, 0.575, "→", ha="center", va="center", fontsize=18)
    fig.text(0.5, 0.17, f"Caveats: the linear model ignores non-zero reference doses ({st['linear_datasets_with_nonzero_reference']}/{lin_k} datasets affected); the 4-knot spline matched on {st['spline4_match']}/{st['spline4_fitted_by_R']};\n"
             f"{st['refused_but_app_returned']} fits that dosresmeta refuses (too few doses per study) are returned without warning. Workaround and fixes are described in the paper.",
             ha="center", fontsize=9, color="#7a1f1f")
    fig.text(0.5, 0.93, "A browser tool for dose-response meta-analysis, validated against R dosresmeta", ha="center", fontsize=13.5, weight="bold")
    fig.savefig(out / "visual_abstract.png", dpi=200, metadata=meta); plt.close(fig)
    (out / "stats.json").write_text(json.dumps(st, indent=1, default=float))
    # ---- PASS/FAIL ----
    exp = json.loads(Path(a.expected).read_text())
    rep = []
    for k, spec in exp["values"].items():
        g = st.get(k)
        if isinstance(spec["value"], str):
            ok = g == spec["value"]; shown = g
        else:
            d = spec["decimals"]
            ok = g is not None and round(float(g), d) == round(float(spec["value"]), d)
            shown = None if g is None else (int(round(float(g), d)) if d <= 0 else round(float(g), d + 2))
        rep.append((k, spec["value"], shown, "PASS" if ok else "FAIL"))
    npass = sum(r[3] == "PASS" for r in rep)
    md = ["| Quantity | Expected | Reproduced | Result |", "|---|--:|--:|---|"] + [f"| {a_} | {b} | {c} | {d} |" for a_, b, c, d in rep]
    (out / "reproduction_report.md").write_text(f"# Reproduction report\n\n{npass}/{len(rep)} numbers reproduced\n\n" + "\n".join(md) + "\n", encoding="utf-8")
    w = max(len(r[0]) for r in rep)
    for a_, b, c, d in rep: print(f"{a_.ljust(w)}  {str(b):>14}  {str(c):>16}  {d}")
    print(f"\n{npass}/{len(rep)} numbers reproduced: {'ALL PASS' if npass == len(rep) else 'FAILURES PRESENT'}")
    sys.exit(0 if npass == len(rep) else 1)


if __name__ == "__main__":
    main()
