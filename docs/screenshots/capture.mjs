// Figure 1 screenshots of the corrected dose-response app (Playwright + installed Google Chrome, headless,
// 1400 x 900, light theme). Data: coffee_raw.txt = dosresmeta::coffee_mort in the app's input format,
// with doses exactly as published (12 of the 22 studies have a non-zero reference dose).
//   node docs/screenshots/capture.mjs docs/screenshots http://localhost:8000/app/dose-response-ma/index.html
import { chromium } from "playwright";
import { readFileSync, writeFileSync } from "fs";
const [D, APP] = process.argv.slice(2);
const b = await chromium.launch({ channel: "chrome" });
const ctx = await b.newContext({ viewport: { width: 1400, height: 900 }, colorScheme: "light", deviceScaleFactor: 1 });
const p = await ctx.newPage();
const errs = []; p.on("pageerror", (e) => errs.push(e.message)); p.on("console", (m) => { if (m.type() === "error") errs.push(m.text()); });
const log = {};
await p.goto(APP); await p.waitForTimeout(500);
const at = async (sel, off = 20) => { await p.evaluate(([s, o]) => { const e = document.querySelector(s); window.scrollTo(0, e.getBoundingClientRect().top + scrollY - o); }, [sel, off]); await p.waitForTimeout(300); };
const set = async (o) => { for (const [id, v] of Object.entries(o)) { if (id === "f-data") { await p.fill("#f-data", v); await p.dispatchEvent("#f-data", "input"); }
  else if ((await p.getAttribute("#" + id, "type")) === "text") { await p.fill("#" + id, v); await p.dispatchEvent("#" + id, "input"); } else await p.selectOption("#" + id, v); } await p.waitForTimeout(600); };
const snap = async (name) => { const r = await p.evaluate(() => ({ last: window._almLastDoseResponse(), head: document.getElementById("headline").innerText, msgs: document.getElementById("msgs").innerText })); log[name] = r; await p.screenshot({ path: `${D}/${name}.png` }); };
// 1 data entry and options; linear trend (doses as published)
await set({ "f-data": readFileSync(D + "/coffee_raw.txt", "utf8") });
await p.evaluate(() => { document.getElementById("f-data").scrollTop = 0; window.scrollTo(0, 0); });
await snap("step1");
// 2 linear trend result: coefficients and tests
await at("#h-res", 16); await snap("step2");
// 3 three-knot spline, two-stage REML: results, then curve and residual plot
await set({ "f-shape": "spline3", "f-pdoses": "1, 2, 3, 4, 5, 6", "f-xref": "0" });
await at("#h-res", 16); await snap("step3");
await at("#curve-host", 60); await p.screenshot({ path: `${D}/step4.png` });
// 5 four-knot spline, two-stage: refused, as dosresmeta refuses it
await set({ "f-shape": "spline4" });
await at("#h-res", 16); await snap("step5");
// 6 four-knot spline, one-stage: fitted, with the predictions table
await set({ "f-proc": "1stage" });
await at("#h-res", 16); await snap("step6");
log.errors = errs;
writeFileSync(`${D}/shots_log.json`, JSON.stringify(log, null, 1));
console.log(JSON.stringify({ heads: ["step1", "step3", "step5", "step6"].map((k) => log[k].head + " || " + log[k].msgs), errors: errs }, null, 1));
await b.close();
