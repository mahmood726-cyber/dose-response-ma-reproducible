// Run the app's JavaScript engine (app/shared/dose-response.js, loaded unchanged) on every case of the
// dosresmeta reference grid: same data, model, knots, covariance, approach, method and covariate.
// The page dose-response-ma/index.html passes its parsed rows to the same function, fitDR().
// Also runs fit(), the page's linear-trend path for the Paule-Mandel and DerSimonian-Laird estimators,
// with REML. Output: one JSON object per dataset per line.
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
const CORE = join(ROOT, "app", "shared", "ma-core.js"), ENGINE = join(ROOT, "app", "shared", "dose-response.js");
require(CORE);                          // registers globalThis.AlmMaCore, used by fit()
const dr = require(ENGINE);

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
const lines = [];
for (const ds of [...new Set(corpus.map((r) => r.dataset))]) {
  const d = corpus.filter((r) => r.dataset === ds);
  const bad = new Set(d.filter((r) => NA(r.cases) || NA(r.n)).map((r) => r.id));
  const ids = [...new Set(d.map((r) => r.id))].filter((i) => !bad.has(i));
  const cov = ref[ds].covariate_by_study || {};
  const studies = ids.map((i) => ({ id: i, mod: cov[i], rows: d.filter((r) => r.id === i).map((r) => ({
    type: r.type, dose: +r.dose, cases: +r.cases, n: +r.n, logrr: +r.logrr, se: NA(r.se) ? null : +r.se })) }));
  const o = { dataset: ds, k: studies.length,
    studies_nonzero_reference: studies.filter((s) => s.rows.find((r) => r.se == null || r.se === 0).dose !== 0).length };
  if (studies.length >= 2) {
    const lf = dr.fit(studies.map((s) => s.rows), { method: "REML" });
    o.linear_fit = { b: lf.slope, se: lf.se, tau2: lf.tau2 };
    o.fits = ref[ds].fits.map((f) => {
      const r = dr.fitDR(studies, { model: f.model.startsWith("rcs") ? "rcs" : f.model, knots: f.model.startsWith("rcs") ? +f.model.slice(3) : undefined,
        covariance: f.covariance, proc: f.proc, method: f.method, mod: !!f.mod });
      const id = { model: f.model, covariance: f.covariance, proc: f.proc, method: f.method, mod: f.mod || null };
      if (!r.ok) return { ...id, ok: false, error: r.error };
      return { ...id, ok: true, knots: r.knots, coef: r.coef, vcov: flat(r.vcov), Psi: flat(r.Psi), logLik: r.logLik, converged: r.converged,
        qtest: r.qtest && { Q: r.qtest.Q, df: r.qtest.df, p: r.qtest.p }, I2: r.I2, wald: [r.wald.chi2, r.wald.df, r.wald.p],
        waldNonlin: r.waldNonlin ? [r.waldNonlin.chi2, r.waldNonlin.df, r.waldNonlin.p] : null,
        gof: { D: r.gof.D, df: r.gof.df, p: r.gof.p, R2: r.gof.R2, R2adj: r.gof.R2adj, resid: r.gof.residuals.map((x) => x.resid) },
        pred: f.pred ? (() => { const p = r.predict(f.pred.dose, f.pred.dose[0]); return { pred: p.map((x) => x.logRR), se: p.map((x) => x.se) }; })() : null };
    });
  }
  lines.push(JSON.stringify(o));
}
mkdirSync(dirname(out), { recursive: true });
writeFileSync(out, lines.join("\n") + "\n");
console.log(`engine (${process.version}): ${lines.length} datasets -> ${out}; dose-response.js sha256 ${sha(ENGINE).slice(0, 16)}, ma-core.js ${sha(CORE).slice(0, 16)}`);
