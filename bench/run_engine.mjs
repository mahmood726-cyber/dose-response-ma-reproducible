// Run the SHIPPED dose-response engine on every dataset in the corpus.
//
// app/shared/ma-core.js and app/shared/dose-response.js are loaded unchanged (both are dual
// browser/CommonJS modules); the page dose-response-ma/index.html passes its parsed rows
// straight to AlmDoseResponse.fit (linear) and .fitSpline (3 or 4 knots), as done here.
//
// Variants
//   linear          : fit(studies)               -- doses exactly as entered (the shipped behaviour)
//   linear_centred  : fit(studies with each study's doses minus its reference dose)
//                     (input transformation only; documents the defect and its workaround)
//   spline3/spline4 : fitSpline(studies, {nk})   -- plus fitted log-RR vs dose 0 on the same grid as R
//
//   node bench/run_engine.mjs data/corpus.csv results/dosresmeta.jsonl results/engine.jsonl
import { readFileSync, writeFileSync, mkdirSync } from "fs";
import { createHash } from "crypto";
import { createRequire } from "module";
import { dirname, join } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, "..");
const require = createRequire(import.meta.url);
const MACORE = join(ROOT, "app", "shared", "ma-core.js"), ENGINE = join(ROOT, "app", "shared", "dose-response.js");
require(MACORE);                      // registers globalThis.AlmMaCore, used by dose-response.js
const dr = require(ENGINE);
const sha = (f) => createHash("sha256").update(readFileSync(f)).digest("hex");

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

const [corpusFile, refFile, out] = process.argv.slice(2);
const corpus = parseCSV(readFileSync(corpusFile, "utf8"));
const ref = Object.fromEntries(readFileSync(refFile, "utf8").trim().split(/\r?\n/).map((l) => { const o = JSON.parse(l); return [o.dataset, o]; }));
const lines = [];
for (const ds of [...new Set(corpus.map((r) => r.dataset))]) {
  const d = corpus.filter((r) => r.dataset === ds);
  const bad = new Set(d.filter((r) => NA(r.cases) || NA(r.n)).map((r) => r.id));
  const ids = [...new Set(d.map((r) => r.id))].filter((i) => !bad.has(i));
  const studies = ids.map((i) => d.filter((r) => r.id === i).map((r) => ({
    type: r.type, dose: +r.dose, cases: +r.cases, n: +r.n, logrr: +r.logrr, se: NA(r.se) ? null : +r.se })));
  const centred = studies.map((rows) => {
    const refRow = rows.find((r) => r.se == null || r.se === 0);
    return rows.map((r) => ({ ...r, dose: r.dose - refRow.dose }));
  });
  const nonzeroRef = studies.filter((rows) => rows.find((r) => r.se == null || r.se === 0).dose !== 0).length;
  const res = { dataset: ds, k: ids.length, excluded_studies: bad.size, studies_nonzero_reference: nonzeroRef };
  const lin = (st) => { try { const f = dr.fit(st, { method: "REML" }); return { ok: isFinite(f.se), b: f.slope, se: f.se, tau2: f.tau2, k: f.k }; } catch (e) { return { ok: false, error: e.message }; } };
  if (ids.length >= 2) {
    res.linear = lin(studies);
    res.linear_centred = lin(centred);
    for (const nk of [3, 4]) {
      try {
        const f = dr.fitSpline(studies, { nk });
        const r = { ok: !!f.beta, knots: f.knots, beta: f.beta, cov: f.cov && f.cov.flat(), Psi: f.Psi && f.Psi.flat() };
        const g = ref[ds] && ref[ds]["spline" + nk] && ref[ds]["spline" + nk].grid;
        if (g && f.predict) { const p = g.map((x) => f.predict(x, 0)); r.grid = g; r.pred = p.map((x) => x.logRR); r.pred_se = p.map((x) => x.se); }
        res["spline" + nk] = r;
      } catch (e) { res["spline" + nk] = { ok: false, error: e.message }; }
    }
  }
  lines.push(JSON.stringify(res));
}
mkdirSync(dirname(out), { recursive: true });
writeFileSync(out, lines.join("\n") + "\n");
console.log(`engine (${process.version}): ${lines.length} datasets -> ${out}; dose-response.js sha256 ${sha(ENGINE).slice(0, 16)}, ma-core.js ${sha(MACORE).slice(0, 16)}`);
