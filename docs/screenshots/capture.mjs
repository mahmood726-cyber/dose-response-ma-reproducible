// Figure 1: step-by-step workflow of the dose-response app (Playwright + installed Google Chrome, headless,
// 1400 x 900, light theme). Data: coffee_raw.txt = dosresmeta::coffee_mort in the app's input format, doses as
// published. Steps 1-3 are single viewport screenshots; steps 4-6 are composed by compose.py from regions of
// full-page screenshots taken here (element boxes saved to shots_log.json).
//   node docs/screenshots/capture.mjs docs/screenshots http://localhost:8000/app/dose-response-ma/index.html
import { chromium } from "playwright";
import { readFileSync, writeFileSync } from "fs";
const [D, APP] = process.argv.slice(2);
const b = await chromium.launch({ channel: "chrome" });
const ctx = await b.newContext({ viewport: { width: 1400, height: 900 }, colorScheme: "light", deviceScaleFactor: 1 });
const p = await ctx.newPage();
const errs = []; p.on("pageerror", (e) => errs.push(e.message)); p.on("console", (m) => { if (m.type() === "error" && !/frame-ancestors/.test(m.text())) errs.push(m.text()); });
const log = { boxes: {} };
await p.goto(APP); await p.waitForTimeout(500);
const at = async (sel, off = 20) => { await p.evaluate(([s, o]) => { const e = document.querySelector(s); window.scrollTo(0, e.getBoundingClientRect().top + scrollY - o); }, [sel, off]); await p.waitForTimeout(300); };
const set = async (o) => { for (const [id, v] of Object.entries(o)) { if (id === "f-data") { await p.fill("#f-data", v); await p.dispatchEvent("#f-data", "input"); }
  else if ((await p.getAttribute("#" + id, "type")) === "text") { await p.fill("#" + id, v); await p.dispatchEvent("#" + id, "input"); } else await p.selectOption("#" + id, v); } await p.waitForTimeout(600); };
const state = async (name) => (log[name] = await p.evaluate(() => ({ last: window._almLastDoseResponse(), head: document.getElementById("headline").innerText, msgs: document.getElementById("msgs").innerText })));
const box = async (name, sel) => { log.boxes[name] = await p.evaluate((s) => { const r = document.querySelector(s).getBoundingClientRect(); return { x: r.left + scrollX, y: r.top + scrollY, w: r.width, h: r.height }; }, sel); };

// 1 data entry: the coffee mortality data pasted in (one row per dose level)
await set({ "f-data": readFileSync(D + "/coffee_raw.txt", "utf8") });
await p.evaluate(() => { document.getElementById("f-data").scrollTop = 0; window.scrollTo(0, 0); });
await state("step1"); await p.screenshot({ path: `${D}/step1.png` });
// 2 choosing the model: 3-knot spline, Greenland-Longnecker covariance, two-stage, REML
await set({ "f-shape": "spline3", "f-cov": "gl", "f-proc": "2stage", "f-method": "REML" });
await at("label[for=f-data]", -140); await p.evaluate(() => window.scrollTo(0, document.querySelector("#f-shape").getBoundingClientRect().top + scrollY - 120)); await p.waitForTimeout(300);
await state("step2"); await p.screenshot({ path: `${D}/step2.png` });
// 3 linear-trend results
await set({ "f-shape": "linear" });
await at("#h-res", 16); await state("step3"); await p.screenshot({ path: `${D}/step3.png` });
// 4-6: 3-knot spline, reference dose 0, predictions at 1-6 cups/day; full page for composition
await set({ "f-shape": "spline3", "f-xref": "0", "f-pdoses": "1, 2, 3, 4, 5, 6" });
await state("spline3");
await p.evaluate(() => window.scrollTo(0, 0)); await p.waitForTimeout(300);
for (const [n, s] of [["headline", "#h-res"], ["coef", "#coef-body"], ["curve", "#curve-host"], ["resid", "#resid-host"], ["tests", "#tests-body"],
                      ["pred", "#pred-body"], ["export", "#alm-export-mount"], ["hTests", "h2:nth-of-type(3)"]]) await box(n, s);
log.boxes.headlineEnd = await p.evaluate(() => { const r = document.getElementById("msgs").getBoundingClientRect(); return r.bottom + scrollY; });
log.boxes.coefTable = await p.evaluate(() => { const r = document.getElementById("coef-body").closest("table").getBoundingClientRect(); return { x: r.left + scrollX, y: r.top + scrollY, w: r.width, h: r.height }; });
log.boxes.testsTable = await p.evaluate(() => { const r = document.getElementById("tests-body").closest("table").getBoundingClientRect(); return { x: r.left + scrollX, y: r.top + scrollY, w: r.width, h: r.height }; });
log.boxes.predTable = await p.evaluate(() => { const r = document.getElementById("pred-body").closest("table").getBoundingClientRect(); return { x: r.left + scrollX, y: r.top + scrollY, w: r.width, h: r.height }; });
log.boxes.predInputs = await p.evaluate(() => { const a = document.querySelector("label[for=f-xref]").getBoundingClientRect(), z = document.getElementById("f-pdoses").getBoundingClientRect(); return { x: a.left + scrollX, y: a.top + scrollY, w: z.right - a.left, h: z.bottom - a.top }; });
log.boxes.panel = await p.evaluate(() => { const r = document.getElementById("h-res").closest("section").getBoundingClientRect(); return { x: r.left + scrollX, y: r.top + scrollY, w: r.width, h: r.height }; });
await p.screenshot({ path: `${D}/_full_spline3.png`, fullPage: true });
log.errors = errs;
writeFileSync(`${D}/shots_log.json`, JSON.stringify(log, null, 1));
console.log(JSON.stringify({ heads: ["step1", "step2", "step3", "spline3"].map((k) => log[k].head + " || " + log[k].msgs), errors: errs }, null, 1));
await b.close();
