// Figure 1: step-by-step workflow of the dose-response app, high resolution (Playwright + installed Google Chrome,
// headless). Viewport 1106 x 900 CSS px (results panel 600 px wide: wide enough that tables do not wrap much,
// narrow enough that text stays large relative to each panel), light theme, device scale factor 6: every region is captured as a page clip at
// 6 device pixels per CSS pixel. compose.py lays the regions out (tight crops, labelled sub-panels) and checks
// legibility from the font sizes recorded here. Data: coffee_raw.txt = dosresmeta::coffee_mort in the app's input
// format, doses as published (12 of the 22 studies have a non-zero reference dose).
//   node docs/screenshots/capture.mjs <work-dir> http://localhost:8000/app/dose-response-ma/index.html
//   python docs/screenshots/compose.py <work-dir> docs/screenshots
import { chromium } from "playwright";
import { readFileSync, writeFileSync, mkdirSync } from "fs";
import { dirname, join } from "path";
import { fileURLToPath } from "url";
const [D, APP] = process.argv.slice(2);
const HERE = dirname(fileURLToPath(import.meta.url));
const OUT = `${D}/regions`; mkdirSync(OUT, { recursive: true });
const DPR = 6;
const b = await chromium.launch({ channel: "chrome" });
const ctx = await b.newContext({ viewport: { width: 1106, height: 900 }, colorScheme: "light", deviceScaleFactor: DPR });
const p = await ctx.newPage();
const errs = []; p.on("pageerror", (e) => errs.push(e.message));
const meta = { dpr: DPR, viewport: [1106, 900], regions: {}, states: {} };
await p.goto(APP); await p.waitForTimeout(500);
await p.addStyleTag({ content: "#hub-back{display:none!important}" });
const set = async (o) => { for (const [id, v] of Object.entries(o)) { if (id === "f-data") { await p.fill("#f-data", v); await p.dispatchEvent("#f-data", "input"); }
  else if ((await p.getAttribute("#" + id, "type")) === "text") { await p.fill("#" + id, v); await p.dispatchEvent("#" + id, "input"); } else await p.selectOption("#" + id, v); } await p.waitForTimeout(600); };
const state = async (name) => (meta.states[name] = await p.evaluate(() => ({ head: document.getElementById("headline").innerText, msgs: document.getElementById("msgs").innerText })));
// page rectangle of an element, or of the h2 whose text starts with `h2:<text>`
const rect = (sel, opt = {}) => p.evaluate(([sel, opt]) => {
  let e = sel.startsWith("h2:") ? [...document.querySelectorAll("h2")].find((h) => h.textContent.trim().startsWith(sel.slice(3))) : document.querySelector(sel);
  if (!e) throw new Error("missing " + sel);
  if (opt.table) e = e.closest("table") || e.closest(".scroll") || e;
  if (opt.up) for (let i = 0; i < opt.up; i++) e = e.parentElement;
  const r = e.getBoundingClientRect(); return { x: r.left + scrollX, y: r.top + scrollY, w: r.width, h: r.height };
}, [sel, opt]);
const union = (...rs) => { const x = Math.min(...rs.map((r) => r.x)), y = Math.min(...rs.map((r) => r.y));
  return { x, y, w: Math.max(...rs.map((r) => r.x + r.w)) - x, h: Math.max(...rs.map((r) => r.y + r.h)) - y }; };
async function region(name, r, pad = 6) {
  const c = { x: Math.max(0, Math.floor(r.x - pad)), y: Math.max(0, Math.floor(r.y - pad)), width: Math.ceil(r.w + 2 * pad), height: Math.ceil(r.h + 2 * pad) };
  await p.screenshot({ path: `${OUT}/${name}.png`, clip: c, fullPage: true });
  const fonts = await p.evaluate((c) => {
    const out = [];
    const inside = (rr) => rr.width > 0 && rr.height > 0 && rr.left + scrollX >= c.x - 1 && rr.right + scrollX <= c.x + c.width + 1 && rr.top + scrollY >= c.y - 1 && rr.bottom + scrollY <= c.y + c.height + 1;
    const tw = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    for (let n = tw.nextNode(); n; n = tw.nextNode()) {
      const t = n.textContent.trim(); if (t.length < 2) continue;
      const el = n.parentElement; const cs = getComputedStyle(el); if (cs.visibility === "hidden" || cs.display === "none") continue;
      if (el.tagName === "TEXTAREA" || el.tagName === "SCRIPT" || el.tagName === "STYLE") continue;
      const range = document.createRange(); range.selectNodeContents(n); const rr = range.getBoundingClientRect(); if (!inside(rr)) continue;
      let px = parseFloat(cs.fontSize);
      if (el.closest("svg") && el.getScreenCTM) { const m = el.getScreenCTM(); if (m) px = px * Math.hypot(m.a, m.b); }
      out.push([Math.round(px * 100) / 100, t.length]);
    }
    // text inside form fields (textarea content, input values) is not a text node: record those fields too
    document.querySelectorAll("textarea, input[type=text], select").forEach((f) => { const rr = f.getBoundingClientRect(); if (inside(rr)) out.push([parseFloat(getComputedStyle(f).fontSize), 10]); });
    return out;
  }, c);
  meta.regions[name] = { clip: c, fonts };
}

// 1 data entry: the coffee mortality data pasted in (one row per dose level)
await set({ "f-data": readFileSync(join(HERE, "coffee_raw.txt"), "utf8") });
await p.evaluate(() => { document.getElementById("f-data").scrollTop = 0; });
await state("step1");
await region("d1_data", union(await rect("#h-input"), await rect("#f-data")));
// 2 choosing the model: 3-knot spline, Greenland-Longnecker covariance, two-stage, REML
await set({ "f-shape": "spline3", "f-cov": "gl", "f-proc": "2stage", "f-method": "REML" });
await region("d2_model", union(await rect("h2:Model"), await rect("#f-mod", { up: 1 })));
// 3 linear-trend results
await set({ "f-shape": "linear" }); await state("step3");
await region("d3_linear", union(await rect("#h-res"), await rect("#tests-body", { table: true })));
// 4-6: 3-knot spline, reference dose 0, predictions at 1-6 cups/day
await set({ "f-shape": "spline3", "f-xref": "0", "f-pdoses": "1, 2, 3, 4, 5, 6" }); await state("spline3");
await region("d4_head", union(await rect("#h-res"), await rect("#coef-body", { table: true })));
await region("d4_curve", union(await rect("#curve-host svg"), await rect("#curve-host p.note")), 3);   // the plot and its note (not the export buttons)
await region("d5_tests", union(await rect("h2:Heterogeneity"), await rect("#tests-body", { table: true })));
{ const r = await rect("#resid-host svg"); await region("d5_resid", { x: r.x, y: r.y + 2, w: r.w, h: r.h - 2 }, 1); }   // the plot only (its note is in the caption)
await region("d6_settings", union(await rect("h2:Predictions"), await rect("#f-pdoses")));
await region("d6_pred", union(await rect("h2:Predicted"), await rect("#pred-body", { table: true })));
await region("d6_export", await rect("#alm-export-mount"));
meta.errors = errs;
writeFileSync(`${D}/regions_meta.json`, JSON.stringify(meta, null, 1));
console.log(JSON.stringify({ states: meta.states, regions: Object.keys(meta.regions), errors: errs }, null, 1));
await b.close();
