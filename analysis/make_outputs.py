"""Compare the app's engine with dosresmeta and build every table, figure and number in the paper.

  python analysis/make_outputs.py --results results/full --outputs outputs/full --expected expected/paper_values.json

Every case of the dosresmeta reference grid is judged as in allmeta's own parity test
(hub/shared/tests/_dr_parity_check.mjs; same scales and tolerances, mirrored below). Exit code 0 only if
every number in the expected file is reproduced (after rounding to its stated decimals).
"""
import argparse
import csv
import json
import math
import random
import sys
from collections import defaultdict
from pathlib import Path

LABEL = {"alcohol_crc": "Alcohol, colorectal cancer", "alcohol_cvd": "Alcohol, CVD", "alcohol_esoph": "Alcohol, oesophageal cancer",
         "alcohol_lc": "Alcohol, lung cancer", "bmi_rc": "BMI, renal cancer", "coffee_cancer": "Coffee, cancer",
         "coffee_cvd": "Coffee, CVD", "coffee_mort": "Coffee, mortality", "coffee_mort_add": "Coffee, mortality (additional)",
         "coffee_stroke": "Coffee, stroke", "fish_ra": "Fish, rheumatoid arthritis", "milk_mort": "Milk, mortality",
         "milk_ov": "Milk, ovarian cancer", "oc_breast": "Oral contraceptives, breast cancer",
         "process_bc": "Processed meat, bladder cancer", "red_bc": "Red meat, bladder cancer", "sim_os": "Simulated (sim_os)"}
MODEL_LABEL = {"linear": "Linear", "quadratic": "Quadratic", "rcs3": "Spline, 3 knots", "rcs4": "Spline, 4 knots", "rcs5": "Spline, 5 knots"}
COV_LABEL = {"gl": "GL", "h": "Hamling", "indep": "Independent"}
METHOD_LABEL = {"reml": "REML", "ml": "ML", "fixed": "Fixed", "mm": "MM"}


def jl(p):
    return {json.loads(l)["dataset"]: json.loads(l) for l in open(p, encoding="utf-8") if l.strip()}


def maxdiff(a, b):
    return max(abs(x - y) for x, y in zip(a, b)) if a and b else float("nan")


# ---- mirror of allmeta hub/shared/tests/_dr_parity_check.mjs ----
def _maxdiag(f):
    n = round(math.sqrt(len(f)))
    return max(abs(f[i * n + i]) for i in range(n))


def _rel(a, b):
    return abs(a - b) / max(abs(b), 1e-300)


def compare(app, ref):
    n = len(ref["coef"]); se = [math.sqrt(ref["vcov"][i * n + i]) for i in range(n)]; vs = _maxdiag(ref["vcov"])
    m = {"coef": max(abs(a - b) / s for a, b, s in zip(app["coef"], ref["coef"], se)),
         "vcov": max(abs(a - b) for a, b in zip(app["vcov"], ref["vcov"])) / vs}
    if ref.get("Psi"):
        s = max(_maxdiag(ref["Psi"]), vs); m["Psi"] = max(abs(a - b) for a, b in zip(app["Psi"], ref["Psi"])) / s
    if ref.get("logLik") is not None: m["logLik"] = _rel(app["logLik"], ref["logLik"])
    if ref.get("qtest"):
        m["Q"] = max(_rel(a, b) for a, b in zip(app["qtest"]["Q"], ref["qtest"]["Q"]))
        m["Qp"] = max(abs(a - b) for a, b in zip(app["qtest"]["p"], ref["qtest"]["p"]))
    m["wald"] = _rel(app["wald"][0], ref["wald"][0])
    if ref.get("waldNonlin"): m["waldNonlin"] = _rel(app["waldNonlin"][0], ref["waldNonlin"][0])
    if ref.get("gof"):
        g, h = app["gof"], ref["gof"]
        m["gof"] = max([_rel(g["D"], h["D"]), abs(g["R2"] - h["R2"]), abs(g["R2adj"] - h["R2adj"])] + [abs(a - b) for a, b in zip(g["resid"], h["resid"])])
    if ref.get("pred"):
        p, q = app["pred"], ref["pred"]
        m["pred"] = max(((abs(a - b) + abs(sa - sb)) / sb) if sb > 0 else abs(a - b) for a, b, sa, sb in zip(p["pred"], q["pred"], p["se"], q["se"]))
    return m


def tolerance(f):
    if f["proc"] == "2stage" and f["method"] in ("reml", "ml"):
        return {"coef": 1e-3, "vcov": 1e-3, "Psi": 1e-3, "logLik": 1e-6, "Q": 1e-9, "Qp": 1e-9, "wald": 1e-3, "waldNonlin": 1e-3, "gof": 1e-9, "pred": 1e-3}
    # Derived quantities (Wald statistics, predictions at the extreme doses) amplify last-bit differences: the
    # Wald test inverts a near-singular vcov for 5-knot splines, and predictions at the largest dose scale the
    # coefficients by dose^2 for the quadratic. R's own values differ between operating systems in the last bits,
    # and along dosresmeta's unconverged one-stage Nelder-Mead path this reaches ~1.6e-6; hence 1e-5 for these.
    return {"coef": 1e-6, "vcov": 1e-6, "Psi": 1e-6, "logLik": 1e-6, "Q": 1e-9, "Qp": 1e-9, "wald": 1e-5, "waldNonlin": 1e-5, "gof": 1e-9, "pred": 1e-5}


def key(f):
    return (f["model"], f["covariance"], f["proc"], f["method"], f.get("mod") or "")


def corpus_info(path):
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    by = defaultdict(set)
    for r in rows:
        by[r["dataset"]].add(r["id"])
    return {ds: len(ids) for ds, ids in by.items()}, len(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", required=True); ap.add_argument("--outputs", required=True); ap.add_argument("--expected", required=True)
    a = ap.parse_args()
    res, out = Path(a.results), Path(a.outputs)
    out.mkdir(parents=True, exist_ok=True)
    R, E = jl(res / "dosresmeta.jsonl"), jl(res / "engine.jsonl")
    nstudies, n_rows = corpus_info(res / "corpus.csv")
    DS = [ds for ds in R if R[ds]["fits"]]
    st = {"datasets": len(R), "studies_total": sum(nstudies.values()), "dose_levels_total": n_rows,
          "datasets_analysed": len(DS), "studies_excluded_missing_counts": sum(R[ds]["excluded_studies"] for ds in R),
          "studies_analysed": sum(R[ds]["k"] for ds in DS)}

    def rfit(ds, model, method="reml", cov="gl", proc="2stage"):
        return next(f for f in R[ds]["fits"] if key(f) == (model, cov, proc, method, ""))

    # ---- every fit of the grid ----
    rows, groups = [], defaultdict(list)
    for ds in DS:
        app = {key(f): f for f in E[ds]["fits"]}
        for f in R[ds]["fits"]:
            g = app[key(f)]
            r = {"dataset": ds, "model": f["model"], "covariance": f["covariance"], "proc": f["proc"], "method": f["method"], "mod": f.get("mod") or "",
                 "R_ok": f["ok"], "app_ok": g["ok"]}
            if f["ok"] and g["ok"]:
                m, tol = compare(g, f), tolerance(f)
                r.update({k: m.get(k) for k in ("coef", "vcov", "Psi", "logLik", "Q", "wald", "gof", "pred")})
                r["within_tolerance"] = all(m[k] <= tol[k] for k in m)
                r["R_converged"] = f.get("converged")
            else:
                r["within_tolerance"] = f["ok"] == g["ok"]
            rows.append(r); groups[key(f)].append(r)
    both = [r for r in rows if r["R_ok"] and r["app_ok"]]
    iterative = [r for r in both if r["proc"] == "2stage" and r["method"] in ("reml", "ml")]
    direct = [r for r in both if r not in iterative]
    ok = lambda r: r["within_tolerance"]

    def dataset_level(model):  # two-stage REML, GL covariance: datasets dosresmeta fits / refuses, and app agreement
        rs = [r for r in rows if (r["model"], r["covariance"], r["proc"], r["method"], r["mod"]) == (model, "gl", "2stage", "reml", "")]
        return sum(r["R_ok"] for r in rs), sum(1 for r in rs if r["R_ok"] and r["app_ok"] and ok(r)), sum(not r["R_ok"] for r in rs), sum(1 for r in rs if not r["R_ok"] and not r["app_ok"])
    for model, tag in (("linear", "linear"), ("rcs3", "spline3"), ("rcs4", "spline4"), ("rcs5", "spline5")):
        fitted, agree, refused, ref_match = dataset_level(model)
        st.update({f"{tag}_fitted_by_R": fitted, f"{tag}_agree": agree, f"{tag}_refused_by_R": refused, f"{tag}_refusals_matched": ref_match})
    st.update({
        "grid_fits": len(rows), "grid_R_fitted": sum(r["R_ok"] for r in rows), "grid_R_refused": sum(not r["R_ok"] for r in rows),
        "grid_refusals_matched": sum(1 for r in rows if not r["R_ok"] and not r["app_ok"]),
        "grid_app_refused_R_fitted": sum(1 for r in rows if r["R_ok"] and not r["app_ok"]),
        "grid_app_fitted_R_refused": sum(1 for r in rows if not r["R_ok"] and r["app_ok"]),
        "grid_within_tolerance": sum(ok(r) for r in rows), "grid_all_within_tolerance": int(all(ok(r) for r in rows)),
        "iterative_fits": len(iterative), "direct_fits": len(direct),
        "iterative_max_coef_se": max(r["coef"] for r in iterative), "iterative_max_loglik_rel": max(r["logLik"] for r in iterative),
        "direct_max_coef_se": max(r["coef"] for r in direct), "direct_max_pred": max(r["pred"] for r in direct if r["pred"] is not None),
        "iterative_coef_below_1e-4_SE": int(max(r["coef"] for r in iterative) < 1e-4),
        "iterative_loglik_below_1e-7": int(max(r["logLik"] for r in iterative) < 1e-7),
        "direct_coef_below_1e-6_SE": int(max(r["coef"] for r in direct) < 1e-6),
        "R_one_stage_not_converged": sum(1 for r in both if r["proc"] == "1stage" and r.get("R_converged") is False),
        "linear_datasets_with_nonzero_reference": sum(1 for ds in DS if E[ds]["studies_nonzero_reference"] > 0),
        "linear_fit_max_se_units": max(abs(E[ds]["linear_fit"]["b"] - rfit(ds, "linear")["coef"][0]) / math.sqrt(rfit(ds, "linear")["vcov"][0]) for ds in DS),
    })

    # ---- tables ----
    def write(name, rws):
        with open(out / f"{name}.csv", "w", newline="", encoding="utf-8") as fh:
            fields = list(dict.fromkeys(k for r in rws for k in r))
            w = csv.DictWriter(fh, fieldnames=fields, restval=""); w.writeheader(); w.writerows(rws)
    T1 = []
    for g, rs in groups.items():
        b = [r for r in rs if r["R_ok"] and r["app_ok"]]
        mx = lambda k: max((r[k] for r in b if r.get(k) is not None), default=None)
        T1.append({"model": MODEL_LABEL[g[0]], "covariance": COV_LABEL[g[1]], "approach": "two-stage" if g[2] == "2stage" else "one-stage",
                   "method": METHOD_LABEL[g[3]], "meta_regression": g[4] or "", "datasets": len(rs), "fitted_by_R": sum(r["R_ok"] for r in rs),
                   "refused_by_R": sum(not r["R_ok"] for r in rs), "refusals_matched": sum(1 for r in rs if not r["R_ok"] and not r["app_ok"]),
                   "max_coef_diff_SE": mx("coef"), "max_vcov_diff_rel": mx("vcov"), "max_Psi_diff_rel": mx("Psi"), "max_loglik_diff_rel": mx("logLik"),
                   "max_pred_diff_SE": mx("pred"), "all_within_tolerance": all(ok(r) for r in rs)})
    write("table1_parity_by_configuration", T1)
    T2 = []
    for ds in DS:
        rs = [r for r in rows if r["dataset"] == ds]; b = [r for r in rs if r["R_ok"] and r["app_ok"]]
        L = rfit(ds, "linear"); al = next(f for f in E[ds]["fits"] if key(f) == ("linear", "gl", "2stage", "reml", ""))
        T2.append({"dataset": ds, "label": LABEL[ds], "studies": R[ds]["k"], "studies_nonzero_reference": E[ds]["studies_nonzero_reference"],
                   "combinations": len(rs), "fitted_by_R": sum(r["R_ok"] for r in rs), "refused_by_R": sum(not r["R_ok"] for r in rs),
                   "refusals_matched": sum(1 for r in rs if not r["R_ok"] and not r["app_ok"]), "all_within_tolerance": all(ok(r) for r in rs),
                   "max_coef_diff_SE": max(r["coef"] for r in b), "R_linear_slope": L["coef"][0], "app_linear_slope": al["coef"][0],
                   "linear_slope_SE": math.sqrt(L["vcov"][0]),
                   "spline3": "refused by both" if not rfit(ds, "rcs3")["ok"] else "agrees", "spline4": "refused by both" if not rfit(ds, "rcs4")["ok"] else "agrees"})
    write("table2_by_dataset", T2)
    write("table3_parity_all_fits", rows)

    # ---- figures ----
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "figure.facecolor": "white", "savefig.facecolor": "white"})
    meta = {"Software": None}
    C = {"app": "#1b6ca8", "iter": "#c27c0e", "ref": "#555555"}
    lg = lambda x: math.log10(max(x, 1e-16))
    # Figure 2: agreement by dataset
    t2 = sorted(T2, key=lambda t: t["max_coef_diff_SE"])
    fig, ax = plt.subplots(figsize=(9.4, 0.33 * len(t2) + 2.0))
    for i, t in enumerate(t2):
        it = [r["coef"] for r in iterative if r["dataset"] == t["dataset"]]; di = [r["coef"] for r in direct if r["dataset"] == t["dataset"]]
        ax.scatter([lg(v) for v in di], [i + 0.12] * len(di), s=9, color=C["app"], alpha=0.5, label="Fixed effect, MM, one-stage" if i == 0 else None)
        ax.scatter([lg(v) for v in it], [i - 0.12] * len(it), s=9, color=C["iter"], alpha=0.6, marker="D", label="Two-stage REML/ML" if i == 0 else None)
        ax.text(1.02, i, f"{t['fitted_by_R']} fits, {t['refused_by_R']} refusals", va="center", fontsize=7.5, transform=ax.get_yaxis_transform())
    ax.axvline(-3, color=C["ref"], ls="--", lw=0.8); ax.axvline(-6, color=C["ref"], ls=":", lw=0.8)
    ax.set_yticks(range(len(t2)), [f"{t['label']} (k = {t['studies']})" for t in t2]); ax.set_xlim(-16.5, 0.5); ax.set_ylim(-0.7, len(t2) - 0.3)
    ax.set_xlabel("log10 coefficient difference from dosresmeta (in its standard errors)")
    ax.set_title("Figure 2. Agreement with dosresmeta by dataset, all model and option combinations\ndashed: tolerance 1e-3 SE (two-stage REML/ML); dotted: 1e-6 SE (all other fits)", fontsize=9.5)
    ax.grid(axis="x", color="#eeeeee", lw=0.6)
    fig.legend(*ax.get_legend_handles_labels(), loc="lower center", ncol=2, fontsize=8, frameon=False)
    fig.tight_layout(rect=(0, 0.04, 0.88, 1)); fig.savefig(out / "figure2_by_dataset.png", dpi=200, metadata=meta); plt.close(fig)
    with open(out / "figure2_by_dataset.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh); w.writerow(["dataset", "model", "covariance", "proc", "method", "mod", "group", "coef_diff_SE"])
        for r in both: w.writerow([r["dataset"], r["model"], r["covariance"], r["proc"], r["method"], r["mod"], "two-stage REML/ML" if r in iterative else "other", r["coef"]])
    # Figure 3: worked example, coffee and mortality
    ex = "coffee_mort"
    if ex in DS:
        L, s3 = rfit(ex, "linear"), rfit(ex, "rcs3")
        al = next(f for f in E[ex]["fits"] if key(f) == ("linear", "gl", "2stage", "reml", ""))
        a3 = next(f for f in E[ex]["fits"] if key(f) == ("rcs3", "gl", "2stage", "reml", ""))
        g = s3["pred"]["dose"]; rp, rse, ap_ = s3["pred"]["pred"], s3["pred"]["se"], a3["pred"]["pred"]
        fig, axs = plt.subplots(1, 2, figsize=(8.6, 3.5))
        ax = axs[0]; xs = [g[0] + (g[-1] - g[0]) * i / 40 for i in range(41)]
        b, se = L["coef"][0], math.sqrt(L["vcov"][0])
        ax.fill_between(xs, [math.exp((b - 1.959963984540054 * se) * x) for x in xs], [math.exp((b + 1.959963984540054 * se) * x) for x in xs], color="#dddddd", label="dosresmeta 95% CI")
        ax.plot(xs, [math.exp(b * x) for x in xs], "-", color=C["ref"], lw=2.2, label=f"dosresmeta (slope {b:+.4f})")
        ax.plot(xs[::5], [math.exp(al["coef"][0] * x) for x in xs[::5]], "o", color=C["app"], ms=4.5, label=f"App (slope {al['coef'][0]:+.4f})")
        ax.set_title("A. Linear trend", fontsize=9.5); ax.set_xlabel("Coffee (cups/day)"); ax.set_ylabel("Relative risk of death"); ax.legend(fontsize=7, frameon=False)
        ax = axs[1]
        ax.fill_between(g, [math.exp(p - 1.959963984540054 * s) for p, s in zip(rp, rse)], [math.exp(p + 1.959963984540054 * s) for p, s in zip(rp, rse)], color="#dddddd", label="dosresmeta 95% CI")
        ax.plot(g, [math.exp(p) for p in rp], "-", color=C["ref"], lw=2.2, label="dosresmeta")
        ax.plot(g, [math.exp(p) for p in ap_], "o", color=C["app"], ms=4.5, label="App")
        ax.set_title("B. Restricted cubic spline, 3 knots", fontsize=9.5); ax.set_xlabel("Coffee (cups/day)"); ax.legend(fontsize=7, frameon=False)
        fig.suptitle(f"Figure 3. Worked example: coffee and all-cause mortality ({R[ex]['k']} studies; two-stage REML)", fontsize=10); fig.tight_layout()
        fig.savefig(out / "figure3_coffee_mortality.png", dpi=200, metadata=meta); plt.close(fig)
        with open(out / "figure3_coffee_mortality.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh); w.writerow(["dose", "R_logrr", "R_se", "app_logrr"])
            for row in zip(g, rp, rse, ap_): w.writerow(row)
        i2 = min(range(len(g)), key=lambda i: abs(g[i] - 2))
        nl = a3["waldNonlin"]
        st.update({"ex_k": R[ex]["k"], "ex_nonzero_ref": E[ex]["studies_nonzero_reference"], "ex_R_slope": L["coef"][0], "ex_app_slope": al["coef"][0],
                   "ex_spline_max_diff": maxdiff(ap_, rp), "ex_spline_below_1e-8": int(maxdiff(ap_, rp) < 1e-8), "ex_grid_dose": g[i2],
                   "ex_rr_R": math.exp(rp[i2]), "ex_rr_app": math.exp(ap_[i2]), "ex_rr_lo": math.exp(rp[i2] - 1.959963984540054 * rse[i2]), "ex_rr_hi": math.exp(rp[i2] + 1.959963984540054 * rse[i2]), "ex_R_slope_se": math.sqrt(L["vcov"][0]), "ex_nonlin_chi2": nl[0], "ex_nonlin_p_below_1e-4": int(nl[2] < 1e-4),
                   "ex_I2": a3["I2"], "ex_knots": "/".join(f"{k:g}" for k in a3["knots"])})
    # Figure 4: all fits by approach and method
    cats = [("Two-stage REML/ML", iterative), ("Two-stage fixed/MM", [r for r in direct if r["proc"] == "2stage"]), ("One-stage", [r for r in direct if r["proc"] == "1stage"])]
    fig, ax = plt.subplots(figsize=(7.4, 3.3))
    rng = random.Random(1)
    for i, (lab, rs) in enumerate(cats):
        ax.scatter([lg(r["coef"]) for r in rs], [i + rng.uniform(-0.28, 0.28) for _ in rs], s=7, alpha=0.55, color=C["app"])
        ax.text(1.2, i, f"n = {len(rs)}", va="center", fontsize=8)
    ax.axvline(-3, color=C["ref"], ls="--", lw=0.8); ax.axvline(-6, color=C["ref"], ls=":", lw=0.8)
    ax.set_yticks(range(len(cats)), [c[0] for c in cats]); ax.set_xlim(-16.5, 2.5); ax.set_ylim(-0.6, len(cats) - 0.4)
    ax.set_xlabel("log10 largest coefficient difference from dosresmeta (in its standard errors)")
    ax.set_title(f"Figure 4. App versus dosresmeta: all {len(both)} fits both programs return\n(dashed: tolerance 1e-3 SE for two-stage REML/ML; dotted: 1e-6 for the rest)", fontsize=9.5)
    ax.grid(axis="x", color="#eeeeee", lw=0.6); fig.tight_layout(); fig.savefig(out / "figure4_parity_grid.png", dpi=200, metadata=meta); plt.close(fig)
    with open(out / "figure4_parity_grid.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh); w.writerow(["group", "dataset", "model", "covariance", "proc", "method", "mod", "coef_diff_SE"])
        for lab, rs in cats:
            for r in rs: w.writerow([lab, r["dataset"], r["model"], r["covariance"], r["proc"], r["method"], r["mod"], r["coef"]])
    # Visual abstract
    fig = plt.figure(figsize=(11, 4.6)); fig.patch.set_facecolor("white")
    boxes = [("Problem", "Dose-response meta-analysis\nof published studies is\nusually run in R or Stata."),
             ("Tool", "allmeta dose-response app:\noffline, in the browser.\nLinear, quadratic and spline\ncurves; GL or Hamling\ncovariance; one- or two-stage."),
             ("Validation", f"Against R dosresmeta on\n{len(DS)} datasets ({st['studies_analysed']} studies):\n{st['grid_fits']} model, covariance,\napproach and method\ncombinations."),
             ("Result", f"{st['grid_within_tolerance']}/{st['grid_fits']} agree, including\nall {st['grid_refusals_matched']} fits dosresmeta\nrefuses. Linear {st['linear_agree']}/{st['linear_fitted_by_R']},\n3-knot {st['spline3_agree']}/{st['spline3_fitted_by_R']}, 4-knot {st['spline4_agree']}/{st['spline4_fitted_by_R']} datasets.")]
    for i, (h, txt) in enumerate(boxes):
        x = 0.02 + i * 0.245
        fig.patches.append(matplotlib.patches.FancyBboxPatch((x, 0.22), 0.22, 0.60, boxstyle="round,pad=0.01", transform=fig.transFigure, facecolor=["#f4ece8", "#e8f0f7", "#eaf4ec", "#fdf6e3"][i], edgecolor="#999"))
        fig.text(x + 0.11, 0.75, h, ha="center", fontsize=13, weight="bold")
        fig.text(x + 0.11, 0.48, txt, ha="center", va="center", fontsize=10.5, linespacing=1.4)
        if i < 3: fig.text(x + 0.2325, 0.52, "→", ha="center", va="center", fontsize=18)
    fig.text(0.5, 0.09, "One command reproduces every number on Linux, Windows, macOS and Docker: github.com/mahmood726-cyber/dose-response-ma-reproducible",
             ha="center", fontsize=9, color="#333333")
    fig.text(0.5, 0.91, "A browser tool for dose-response meta-analysis, validated against R dosresmeta", ha="center", fontsize=13.5, weight="bold")
    fig.savefig(out / "visual_abstract.png", dpi=200, metadata=meta); plt.close(fig)
    (out / "stats.json").write_text(json.dumps(st, indent=1, default=float))
    # ---- PASS/FAIL ----
    exp = json.loads(Path(a.expected).read_text())
    rep = []
    for k, spec in exp["values"].items():
        g = st.get(k)
        if isinstance(spec["value"], str):
            okv = g == spec["value"]; shown = g
        else:
            d = spec["decimals"]
            okv = g is not None and round(float(g), d) == round(float(spec["value"]), d)
            shown = None if g is None else (int(round(float(g), d)) if d <= 0 else round(float(g), d + 2))
        rep.append((k, spec["value"], shown, "PASS" if okv else "FAIL"))
    npass = sum(r[3] == "PASS" for r in rep)
    md = ["| Quantity | Expected | Reproduced | Result |", "|---|--:|--:|---|"] + [f"| {a_} | {b} | {c} | {d} |" for a_, b, c, d in rep]
    (out / "reproduction_report.md").write_text(f"# Reproduction report\n\n{npass}/{len(rep)} numbers reproduced\n\n" + "\n".join(md) + "\n", encoding="utf-8")
    w = max(len(r[0]) for r in rep) if rep else 0
    for a_, b, c, d in rep: print(f"{a_.ljust(w)}  {str(b):>14}  {str(c):>16}  {d}")
    print(f"\n{npass}/{len(rep)} numbers reproduced: {'ALL PASS' if npass == len(rep) else 'FAILURES PRESENT'}")
    sys.exit(0 if rep and npass == len(rep) else 1)


if __name__ == "__main__":
    main()
