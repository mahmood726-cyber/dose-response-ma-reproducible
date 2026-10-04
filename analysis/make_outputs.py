"""Compare the app's engine with dosresmeta and build every table, figure and number in the paper.

  python analysis/make_outputs.py --results results/full --outputs outputs/full --expected expected/paper_values.json

Two engines are compared with the same dosresmeta reference fits:
  before  the version first validated (allmeta ac5435b): linear trend and 3/4-knot splines, judged
          against the tolerances that version claimed on its page (absolute 1e-6 linear, 1e-5 spline)
  after   the corrected app: every case of the reference grid, judged as in allmeta's parity test
          (hub/shared/tests/_dr_parity_check.mjs; same scales and tolerances, mirrored below)
Exit code 0 only if every number in the expected file is reproduced (after rounding to its stated decimals).
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
    return {"coef": 1e-6, "vcov": 1e-6, "Psi": 1e-6, "logLik": 1e-6, "Q": 1e-9, "Qp": 1e-9, "wald": 1e-5, "waldNonlin": 1e-5, "gof": 1e-9, "pred": 1e-6}


def key(f):
    return (f["model"], f["covariance"], f["proc"], f["method"], f.get("mod") or "")


def corpus_info(path):
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    by = defaultdict(lambda: defaultdict(list))
    for r in rows:
        by[r["dataset"]][r["id"]].append(r)
    info = {}
    for ds, studies in by.items():
        ok = {i: s for i, s in studies.items() if all(x["cases"] not in ("NA", "") and x["n"] not in ("NA", "") for x in s)}
        nonref = [sum(1 for x in s if x["se"] not in ("NA", "") and float(x["se"]) != 0) for s in ok.values()]
        info[ds] = {"studies": len(studies), "with_counts": len(ok), "lt": {q: sum(1 for v in nonref if v < q) for q in (2, 3, 4)}}
    return info, len(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", required=True); ap.add_argument("--outputs", required=True); ap.add_argument("--expected", required=True)
    a = ap.parse_args()
    res, out = Path(a.results), Path(a.outputs)
    out.mkdir(parents=True, exist_ok=True)
    R, E = jl(res / "dosresmeta.jsonl"), jl(res / "engine.jsonl")
    info, n_rows = corpus_info(res / "corpus.csv")
    DS = [ds for ds in R if R[ds]["fits"]]
    st = {"datasets": len(R), "studies_total": sum(v["studies"] for v in info.values()), "dose_levels_total": n_rows,
          "datasets_analysed": len(DS), "studies_excluded_missing_counts": sum(R[ds]["excluded_studies"] for ds in R),
          "studies_analysed": sum(R[ds]["k"] for ds in DS)}

    # ================= before (allmeta ac5435b) =================
    def rfit(ds, model, method="reml", cov="gl", proc="2stage"):
        return next(f for f in R[ds]["fits"] if key(f) == (model, cov, proc, method, ""))
    B = []
    for ds in DS:
        e, L = E[ds]["before"], rfit(ds, "linear")
        rb, rse, rt = L["coef"][0], math.sqrt(L["vcov"][0]), L["Psi"][0]
        row = {"dataset": ds, "label": LABEL[ds], "k": R[ds]["k"], "nonzero_ref": E[ds]["studies_nonzero_reference"],
               "R_slope": rb, "before_slope": e["linear"]["b"], "before_centred_slope": e["linear_centred"]["b"],
               "after_slope": E[ds]["after"]["linear_fit"]["b"],
               "lin_before_match": max(abs(e["linear"]["b"] - rb), abs(e["linear"]["se"] - rse), abs(e["linear"]["tau2"] - rt)) <= TOL_LIN,
               "lin_centred_match": max(abs(e["linear_centred"]["b"] - rb), abs(e["linear_centred"]["se"] - rse), abs(e["linear_centred"]["tau2"] - rt)) <= TOL_LIN,
               "lin_before_absdiff": abs(e["linear"]["b"] - rb), "lin_before_se_units": abs(e["linear"]["b"] - rb) / rse}
        for nk in (3, 4):
            rs, es = rfit(ds, f"rcs{nk}"), e[f"spline{nk}"]
            if rs["ok"]:
                dm = max(maxdiff(es["beta"], rs["coef"]), maxdiff(es["cov"], rs["vcov"]), maxdiff(es["Psi"], rs["Psi"]))
                dp = maxdiff(es.get("pred"), rs["pred"]["pred"]) if rs.get("pred") and es.get("pred") else 0.0
                row[f"s{nk}"] = "fit"; row[f"s{nk}_match"] = max(dm, dp) <= TOL_SPL; row[f"s{nk}_absdiff"] = max(dm, dp)
                n = len(rs["coef"]); row[f"s{nk}_se_units"] = max(abs(x - y) / math.sqrt(rs["vcov"][i * n + i]) for i, (x, y) in enumerate(zip(es["beta"], rs["coef"])))
            else:
                row[f"s{nk}"] = "refused"; row[f"s{nk}_returned"] = bool(es.get("ok"))
                row[f"s{nk}_maxabs"] = max(abs(x) for x in es["beta"]) if es.get("beta") else None
                row[f"s{nk}_too_few"] = info[ds]["lt"][nk - 1]
        B.append(row)
    fitted = lambda nk: [r for r in B if r[f"s{nk}"] == "fit"]
    refused = lambda nk: [r for r in B if r[f"s{nk}"] == "refused"]
    st.update({
        "before_linear_match": sum(r["lin_before_match"] for r in B), "before_linear_centred_match": sum(r["lin_centred_match"] for r in B),
        "linear_datasets_with_nonzero_reference": sum(1 for r in B if r["nonzero_ref"] > 0),
        "before_linear_max_absdiff": max(r["lin_before_absdiff"] for r in B),
        "before_linear_worst_dataset": max(B, key=lambda r: r["lin_before_absdiff"])["dataset"],
        "spline3_fitted_by_R": len(fitted(3)), "spline4_fitted_by_R": len(fitted(4)),
        "spline3_refused_by_R": len(refused(3)), "spline4_refused_by_R": len(refused(4)),
        "before_spline3_match": sum(r["s3_match"] for r in fitted(3)), "before_spline4_match": sum(r["s4_match"] for r in fitted(4)),
        "before_spline4_max_se_units": max(r["s4_se_units"] for r in fitted(4)),
        "before_refused_but_returned": sum(r["s3_returned"] for r in refused(3)) + sum(r["s4_returned"] for r in refused(4)),
        "before_refused_coef_exceeds_1e12": int(max((r["s4_maxabs"] or 0) for r in refused(4)) > 1e12),
    })

    # ================= after (corrected app): full grid =================
    rows, groups = [], defaultdict(list)
    for ds in DS:
        app = {key(f): f for f in E[ds]["after"]["fits"]}
        for f in R[ds]["fits"]:
            g = app[key(f)]
            r = {"dataset": ds, "model": f["model"], "covariance": f["covariance"], "proc": f["proc"], "method": f["method"], "mod": f.get("mod") or "",
                 "R_ok": f["ok"], "app_ok": g["ok"], "status_agrees": f["ok"] == g["ok"]}
            if f["ok"] and g["ok"]:
                m, tol = compare(g, f), tolerance(f)
                r.update({k: m.get(k) for k in ("coef", "vcov", "Psi", "logLik", "Q", "wald", "gof", "pred")})
                r["within_tolerance"] = all(m[k] <= tol[k] for k in m)
                r["R_converged"] = f.get("converged")
            else:
                r["within_tolerance"] = r["status_agrees"]
            rows.append(r); groups[(f["model"], f["covariance"], f["proc"], f["method"], f.get("mod") or "")].append(r)
    both = [r for r in rows if r["R_ok"] and r["app_ok"]]
    iterative = [r for r in both if r["proc"] == "2stage" and r["method"] in ("reml", "ml")]
    direct = [r for r in both if r not in iterative]
    ok = lambda r: r["within_tolerance"]
    def after_ok(model):
        return sum(1 for r in both if (r["model"], r["covariance"], r["proc"], r["method"], r["mod"]) == (model, "gl", "2stage", "reml", "") and ok(r))
    st.update({
        "grid_fits": len(rows), "grid_R_fitted": sum(r["R_ok"] for r in rows), "grid_R_refused": sum(not r["R_ok"] for r in rows),
        "grid_refusals_matched": sum(1 for r in rows if not r["R_ok"] and not r["app_ok"]),
        "grid_app_refused_R_fitted": sum(1 for r in rows if r["R_ok"] and not r["app_ok"]),
        "grid_within_tolerance": sum(ok(r) for r in rows),
        "after_iterative_max_coef_se": max(r["coef"] for r in iterative), "after_iterative_max_loglik_rel": max(r["logLik"] for r in iterative),
        "after_direct_max_coef_se": max(r["coef"] for r in direct),
        "after_direct_max_pred": max(r["pred"] for r in direct if r["pred"] is not None),
        "R_one_stage_not_converged": sum(1 for r in both if r["proc"] == "1stage" and r.get("R_converged") is False),
        "after_linear_match": after_ok("linear"), "after_spline3_match": after_ok("rcs3"), "after_spline4_match": after_ok("rcs4"),
        "after_refused_but_returned": sum(1 for r in rows if not r["R_ok"] and r["app_ok"]),
        "grid_all_within_tolerance": int(all(ok(r) for r in rows)),
        "after_iterative_coef_below_1e-4_SE": int(max(r["coef"] for r in iterative) < 1e-4),
        "after_iterative_loglik_below_1e-7": int(max(r["logLik"] for r in iterative) < 1e-7),
        "after_direct_coef_below_1e-6_SE": int(max(r["coef"] for r in direct) < 1e-6),
        "after_linear_fit_max_se_units": max(abs(E[ds]["after"]["linear_fit"]["b"] - rfit(ds, "linear")["coef"][0]) / math.sqrt(rfit(ds, "linear")["vcov"][0]) for ds in DS),
    })

    # ---- tables ----
    def write(name, rws):
        with open(out / f"{name}.csv", "w", newline="", encoding="utf-8") as fh:
            fields = list(dict.fromkeys(k for r in rws for k in r))
            w = csv.DictWriter(fh, fieldnames=fields, restval=""); w.writeheader(); w.writerows(rws)
    T1 = [
        {"check": "Linear trend agrees with dosresmeta (16 datasets)", "before": f"{st['before_linear_match']}/{len(B)}", "after": f"{st['after_linear_match']}/{len(B)}",
         "cause_and_fix": "doses were not measured from each study's reference dose; now centred as in dosresmeta"},
        {"check": "3-knot spline agrees", "before": f"{st['before_spline3_match']}/{st['spline3_fitted_by_R']}", "after": f"{st['after_spline3_match']}/{st['spline3_fitted_by_R']}",
         "cause_and_fix": "stage-2 optimiser replaced by mixmeta's (RIGLS start, BFGS with analytic gradient)"},
        {"check": "4-knot spline agrees", "before": f"{st['before_spline4_match']}/{st['spline4_fitted_by_R']}", "after": f"{st['after_spline4_match']}/{st['spline4_fitted_by_R']}",
         "cause_and_fix": "Nelder-Mead from a clamped start, fixed step, 600-iteration cap stopped far from the REML optimum; replaced as above"},
        {"check": "Fits dosresmeta refuses that the app returned", "before": str(st["before_refused_but_returned"]), "after": str(st["after_refused_but_returned"]),
         "cause_and_fix": "studies with fewer non-reference doses than coefficients were not checked; two-stage fits now refuse, naming them"},
    ]
    write("table1_found_and_fixed", T1)
    T2 = []
    for g, rs in groups.items():
        b = [r for r in rs if r["R_ok"] and r["app_ok"]]
        mx = lambda k: max((r[k] for r in b if r.get(k) is not None), default=None)
        T2.append({"model": MODEL_LABEL[g[0]], "covariance": COV_LABEL[g[1]], "approach": "two-stage" if g[2] == "2stage" else "one-stage",
                   "method": METHOD_LABEL[g[3]], "meta_regression": g[4] or "", "datasets": len(rs), "fitted_by_R": sum(r["R_ok"] for r in rs),
                   "refused_by_R": sum(not r["R_ok"] for r in rs), "refusals_matched": sum(1 for r in rs if not r["R_ok"] and not r["app_ok"]),
                   "max_coef_diff_SE": mx("coef"), "max_vcov_diff_rel": mx("vcov"), "max_Psi_diff_rel": mx("Psi"), "max_loglik_diff_rel": mx("logLik"),
                   "max_pred_diff_SE": mx("pred"), "all_within_tolerance": all(ok(r) for r in rs)})
    write("table2_parity_by_configuration", T2)
    write("table3_parity_all_fits", rows)
    write("table4_before_by_dataset", [{k: v for k, v in r.items()} for r in B])

    # ---- figures ----
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "figure.facecolor": "white", "savefig.facecolor": "white"})
    meta = {"Software": None}
    C = {"before": "#c0392b", "after": "#1b6ca8", "ref": "#555555", "s3": "#2e8b57"}
    lg = lambda x: math.log10(max(x, 1e-16))
    # Figure 2: before vs after, per dataset, in standard-error units
    bs = sorted(B, key=lambda r: r["lin_before_se_units"])
    aft = {(r["dataset"], r["model"]): r["coef"] for r in both if (r["covariance"], r["proc"], r["method"], r["mod"]) == ("gl", "2stage", "reml", "")}
    fig, axs = plt.subplots(1, 3, figsize=(10.5, 0.30 * len(bs) + 1.9), sharey=True)
    for ax, (model, bk, title) in zip(axs, (("linear", "lin_before_se_units", "A. Linear trend"), ("rcs3", "s3_se_units", "B. Spline, 3 knots"), ("rcs4", "s4_se_units", "C. Spline, 4 knots"))):
        for i, r in enumerate(bs):
            if model == "linear" or r[f"s{model[-1]}"] == "fit":
                b, af = r[bk], aft.get((r["dataset"], model))
                ax.plot([lg(b), lg(af)], [i, i], color="#bbbbbb", lw=0.8, zorder=1)
                ax.scatter([lg(b)], [i], color=C["before"], s=22, zorder=2, label="Before (allmeta ac5435b)" if i == 0 else None)
                ax.scatter([lg(af)], [i], color=C["after"], s=22, marker="s", zorder=3, label="After (corrected)" if i == 0 else None)
            else:
                ax.text(-15.5, i, "dosresmeta refuses; before: " + ("estimate returned" if r[f"s{model[-1]}_returned"] else "refused") + "; after: refused", fontsize=6.3, va="center", color="#7a1f1f")
        ax.axvline(-3, color=C["ref"], ls="--", lw=0.8)
        ax.set_xlim(-16, 3); ax.set_title(title, fontsize=9.5); ax.grid(axis="x", color="#eeeeee", lw=0.6)
        ax.set_xlabel("log10 largest coefficient difference\n(in dosresmeta standard errors)", fontsize=8)
    axs[0].set_yticks(range(len(bs)), [r["label"] for r in bs])
    fig.legend(*axs[0].get_legend_handles_labels(), loc="lower center", ncol=2, fontsize=8, frameon=False)
    fig.suptitle("Figure 2. Agreement with dosresmeta before and after the corrections (two-stage, REML, GL covariance; dashed: 1/1000 SE)", fontsize=9.5)
    fig.tight_layout(rect=(0, 0.04, 1, 1)); fig.savefig(out / "figure2_before_after.png", dpi=200, metadata=meta); plt.close(fig)
    with open(out / "figure2_before_after.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh); w.writerow(["dataset", "linear_before_SE", "linear_after_SE", "rcs3_before_SE", "rcs3_after_SE", "rcs4_before_SE", "rcs4_after_SE"])
        for r in bs:
            w.writerow([r["dataset"], r["lin_before_se_units"], aft.get((r["dataset"], "linear")), r.get("s3_se_units", ""), aft.get((r["dataset"], "rcs3"), ""),
                        r.get("s4_se_units", ""), aft.get((r["dataset"], "rcs4"), "")])
    # Figure 3: worked example, coffee and mortality
    ex = "coffee_mort"
    if ex in DS:
        L, s3 = rfit(ex, "linear"), rfit(ex, "rcs3")
        a3 = next(f for f in E[ex]["after"]["fits"] if key(f) == ("rcs3", "gl", "2stage", "reml", ""))
        eb = next(r for r in B if r["dataset"] == ex)
        g = s3["pred"]["dose"]; xs = [g[0], g[-1]]
        fig, axs = plt.subplots(1, 2, figsize=(8.6, 3.5))
        ax = axs[0]
        for lab, b, col, ls in (("dosresmeta", L["coef"][0], C["ref"], "-"), ("Before", eb["before_slope"], C["before"], "--"), ("After", eb["after_slope"], C["after"], ":")):
            ax.plot(xs, [math.exp(b * x) for x in xs], ls, color=col, lw=1.9, label=f"{lab} (slope {b:+.4f})")
        ax.set_title("A. Linear trend", fontsize=9.5); ax.set_xlabel("Coffee (cups/day)"); ax.set_ylabel("Relative risk of death"); ax.legend(fontsize=7, frameon=False)
        ax = axs[1]
        rp, rse, ap_ = s3["pred"]["pred"], s3["pred"]["se"], a3["pred"]["pred"]
        ax.fill_between(g, [math.exp(p - 1.959963984540054 * s) for p, s in zip(rp, rse)], [math.exp(p + 1.959963984540054 * s) for p, s in zip(rp, rse)], color="#dddddd", label="dosresmeta 95% CI")
        ax.plot(g, [math.exp(p) for p in rp], "-", color=C["ref"], lw=2.2, label="dosresmeta")
        ax.plot(g, [math.exp(p) for p in ap_], "o", color=C["after"], ms=4.5, label="App (after)")
        ax.set_title("B. Restricted cubic spline, 3 knots", fontsize=9.5); ax.set_xlabel("Coffee (cups/day)"); ax.legend(fontsize=7, frameon=False)
        fig.suptitle(f"Figure 3. Worked example: coffee and all-cause mortality ({R[ex]['k']} studies)", fontsize=10); fig.tight_layout()
        fig.savefig(out / "figure3_coffee_mortality.png", dpi=200, metadata=meta); plt.close(fig)
        with open(out / "figure3_coffee_mortality.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh); w.writerow(["dose", "R_logrr", "R_se", "app_after_logrr"])
            for row in zip(g, rp, rse, ap_): w.writerow(row)
        i3 = min(range(len(g)), key=lambda i: abs(g[i] - 3))
        st.update({"ex_k": R[ex]["k"], "ex_nonzero_ref": eb["nonzero_ref"], "ex_R_slope": L["coef"][0], "ex_before_slope": eb["before_slope"],
                   "ex_after_slope": eb["after_slope"], "ex_spline_max_diff": maxdiff(ap_, rp), "ex_grid_dose": g[i3], "ex_rr_R": math.exp(rp[i3]), "ex_rr_app": math.exp(ap_[i3])})
    # Figure 4: parity over the whole grid
    cats = [("Two-stage REML/ML", iterative), ("Two-stage fixed/MM", [r for r in direct if r["proc"] == "2stage"]), ("One-stage", [r for r in direct if r["proc"] == "1stage"])]
    fig, ax = plt.subplots(figsize=(7.4, 3.3))
    import random
    rng = random.Random(1)
    for i, (lab, rs) in enumerate(cats):
        ax.scatter([lg(r["coef"]) for r in rs], [i + rng.uniform(-0.28, 0.28) for _ in rs], s=7, alpha=0.55, color=C["after"])
        ax.text(1.2, i, f"n = {len(rs)}", va="center", fontsize=8)
    ax.axvline(-3, color=C["ref"], ls="--", lw=0.8); ax.axvline(-6, color=C["ref"], ls=":", lw=0.8)
    ax.set_yticks(range(len(cats)), [c[0] for c in cats]); ax.set_xlim(-16.5, 2.5); ax.set_ylim(-0.6, len(cats) - 0.4)
    ax.set_xlabel("log10 largest coefficient difference from dosresmeta (in its standard errors)")
    ax.set_title(f"Figure 4. Corrected app versus dosresmeta: all {len(both)} fits both programs return\n(dashed: tolerance 1e-3 SE for iterative two-stage fits; dotted: 1e-6 for the rest)", fontsize=9.5)
    ax.grid(axis="x", color="#eeeeee", lw=0.6); fig.tight_layout(); fig.savefig(out / "figure4_parity_grid.png", dpi=200, metadata=meta); plt.close(fig)
    with open(out / "figure4_parity_grid.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh); w.writerow(["group", "dataset", "model", "covariance", "proc", "method", "mod", "coef_diff_SE"])
        for lab, rs in cats:
            for r in rs: w.writerow([lab, r["dataset"], r["model"], r["covariance"], r["proc"], r["method"], r["mod"], r["coef"]])
    # Visual abstract
    fig = plt.figure(figsize=(11, 4.6)); fig.patch.set_facecolor("white")
    boxes = [("Problem", "Dose-response meta-analysis\nof published studies is\nusually run in R or Stata."),
             ("Tool", "allmeta dose-response app:\noffline, in the browser.\nLinear, quadratic and spline\ncurves; GL or Hamling\ncovariance; one- or two-stage."),
             ("Validation", f"Engine run against R dosresmeta\non {len(DS)} datasets ({st['studies_analysed']} studies):\n{st['grid_fits']} model/option combinations.\nFirst run found 3 estimation\ndefects; all were fixed."),
             ("Result", f"{st['grid_within_tolerance']}/{st['grid_fits']} combinations agree\n(including all {st['grid_refusals_matched']} refusals).\nLinear {st['before_linear_match']}→{st['after_linear_match']}/{len(B)}; 4-knot spline\n{st['before_spline4_match']}→{st['after_spline4_match']}/{st['spline4_fitted_by_R']}; unwarranted\nestimates {st['before_refused_but_returned']}→{st['after_refused_but_returned']}.")]
    for i, (h, txt) in enumerate(boxes):
        x = 0.02 + i * 0.245
        fig.patches.append(matplotlib.patches.FancyBboxPatch((x, 0.22), 0.22, 0.60, boxstyle="round,pad=0.01", transform=fig.transFigure, facecolor=["#f4ece8", "#e8f0f7", "#eaf4ec", "#fdf6e3"][i], edgecolor="#999"))
        fig.text(x + 0.11, 0.75, h, ha="center", fontsize=13, weight="bold")
        fig.text(x + 0.11, 0.48, txt, ha="center", va="center", fontsize=10.5, linespacing=1.4)
        if i < 3: fig.text(x + 0.2325, 0.52, "→", ha="center", va="center", fontsize=18)
    fig.text(0.5, 0.09, "Validated against the reference implementation across a corpus, not one example: the single-dataset test the app shipped with had missed all three defects.",
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
