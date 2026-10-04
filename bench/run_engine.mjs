// Run the app's JavaScript engine on every dataset in the corpus, in two versions:
//
//   before  app_before/shared/dose-response.js (allmeta ac5435b, the version first validated):
//           fit() linear trend, fitSpline() with 3 and 4 knots, plus the linear trend with each
//           study's doses entered relative to its reference dose (the workaround for that version)
//   after   app/shared/dose-response.js (the corrected app): fitDR() on every case of the
//           dosresmeta reference grid (same model, knots, covariance, approach, method and
//           covariate), and fit() for the linear trend
//
// Both files are loaded unchanged; the page dose-response-ma/index.html passes its parsed rows to
// the same functions. Output: one JSON object per dataset per line.
//
//   node bench/run_engine.mjs results/full/corpus.csv results/full/dosresmeta.jsonl results/full/engine.jsonl
import { readFileSync, writeFileSync, mkdirSync } from "fs";
import { createHash } from "crypto";
import { createRequire } from "module";
import { dirname, join } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, "..");
const require = createRequire(import.meta.url);
const sha = (f) => createHash("sha256").update(readFileSync(f)).digest("hex");
const B_CORE = join(ROOT, "app_before", "shared", "ma-core.js"), B_ENG = join(ROOT, "app_before", "shared", "dose-response.js");
const A_CORE = join(ROOT, "app", "shared", "ma-core.js"), A_ENG = join(ROOT, "app", "shared", "dose-response.js");

function parseCSV(text) {
  const rows = []; let row = [], cur = "", q = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (q) { if (c === '"') { if (text[i + 1] === '"') { cur += '"'; i++; } else q = false; } else cur += c; }
    else if (c === '"') q = true;
    else if (c === ",") { row.push(cur); cur = ""; }
    else if (c === "\n") { row.push(cur); rows.push(row); row = []; cur = ""; }
    else if (c !== "\r") cur += c;
  }
  if (cur.length || row.length) { row.push(cur); rows.push(row); }
  const h = rows.shift();
  return rows.filter((r) => r.length > 1).map((r) => Object.fromEntries(h.map((k, i) => [k, r[i]])));
}
const NA = (v) => v === "NA" || v === "";
const flat = (M) => (M ? M.flat() : null);

const [corpusFile, refFile, out] = process.argv.slice(2);
const corpus = parseCSV(readFileSync(corpusFile, "utf8"));
const ref = Object.fromEntries(readFileSync(refFile, "utf8").trim().split(/\r?\n/).map((l) => { const o = JSON.parse(l); return [o.dataset, o]; }));
const data = {};
for (const ds of [...new Set(corpus.map((r) => r.dataset))]) {
  const d = corpus.filter((r) => r.dataset === ds);
  const bad = new Set(d.filter((r) => NA(r.cases) || NA(r.n)).map((r) => r.id));
  const ids = [...new Set(d.map((r) => r.id))].filter((i) => !bad.has(i));
  const cov = ref[ds].covariate_by_study || {};
  data[ds] = ids.map((i) => ({ id: i, mod: cov[i], rows: d.filter((r) => r.id === i).map((r) => ({
    type: r.type, dose: +r.dose, cases: +r.cases, n: +r.n, logrr: +r.logrr, se: NA(r.se) ? null : +r.se })) }));
}

// ---- before: the originally validated engine ----
require(B_CORE);                       // registers globalThis.AlmMaCore, used by fit()
const before = require(B_ENG);
const res = {};
for (const [ds, studies] of Object.entries(data)) {
  const rows = studies.map((s) => s.rows);
  const centred = rows.map((rs) => { const r0 = rs.find((r) => r.se == null || r.se === 0); return rs.map((r) => ({ ...r, dose: r.dose - r0.dose })); });
  const nonzeroRef = rows.filter((rs) => rs.find((r) => r.se == null || r.se === 0).dose !== 0).length;
  const o = res[ds] = { dataset: ds, k: studies.length, studies_nonzero_reference: nonzeroRef, before: {}, after: {} };
  if (studies.length < 2) continue;
  const lin = (st) => { const f = before.fit(st, { method: "REML" }); return { ok: isFinite(f.se), b: f.slope, se: f.se, tau2: f.tau2 }; };
  o.before.linear = lin(rows);
  o.before.linear_centred = lin(centred);
  const g = ref[ds].fits.find((f) => f.model === "rcs3" && f.covariance === "gl" && f.proc === "2stage" && f.method === "reml");
  for (const nk of [3, 4]) {
    const f = before.fitSpline(rows, { nk });
    const r = { ok: !!f.beta, knots: f.knots, beta: f.beta, cov: flat(f.cov), Psi: flat(f.Psi) };
    if (f.beta && g && g.pred) { const p = g.pred.dose.map((x) => f.predict(x, g.pred.dose[0])); r.pred = p.map((x) => x.logRR); r.pred_se = p.map((x) => x.se); }
    o.before["spline" + nk] = r;
  }
}

// ---- after: the corrected engine ----
delete globalThis.AlmMaCore; delete globalThis.AlmDoseResponse;
require(A_CORE);
const after = require(A_ENG);
for (const [ds, studies] of Object.entries(data)) {
  const o = res[ds];
  if (studies.length < 2) continue;
  const lf = after.fit(studies.map((s) => s.rows), { method: "REML" });
  o.after.linear_fit = { b: lf.slope, se: lf.se, tau2: lf.tau2 };
  o.after.fits = ref[ds].fits.map((f) => {
    const r = after.fitDR(studies, { model: f.model.startsWith("rcs") ? "rcs" : f.model, knots: f.model.startsWith("rcs") ? +f.model.slice(3) : undefined,
      covariance: f.covariance, proc: f.proc, method: f.method, mod: !!f.mod });
    const id = { model: f.model, covariance: f.covariance, proc: f.proc, method: f.method, mod: f.mod || null };
    if (!r.ok) return { ...id, ok: false, error: r.error };
    return { ...id, ok: true, knots: r.knots, coef: r.coef, vcov: flat(r.vcov), Psi: flat(r.Psi), logLik: r.logLik, converged: r.converged,
      qtest: r.qtest && { Q: r.qtest.Q, df: r.qtest.df, p: r.qtest.p }, I2: r.I2, wald: r.wald && [r.wald.chi2, r.wald.df, r.wald.p],
      waldNonlin: r.waldNonlin ? [r.waldNonlin.chi2, r.waldNonlin.df, r.waldNonlin.p] : null,
      gof: { D: r.gof.D, df: r.gof.df, p: r.gof.p, R2: r.gof.R2, R2adj: r.gof.R2adj, resid: r.gof.residuals.map((x) => x.resid) },
      pred: f.pred ? (() => { const p = r.predict(f.pred.dose, f.pred.dose[0]); return { pred: p.map((x) => x.logRR), se: p.map((x) => x.se) }; })() : null };
  });
}
mkdirSync(dirname(out), { recursive: true });
writeFileSync(out, Object.values(res).map((o) => JSON.stringify(o)).join("\n") + "\n");
console.log(`engine (${process.version}): ${Object.keys(res).length} datasets -> ${out}; before dose-response.js sha256 ${sha(B_ENG).slice(0, 16)}, after ${sha(A_ENG).slice(0, 16)}`);
