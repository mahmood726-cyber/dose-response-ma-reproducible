// Screenshots of the dose-response app (Playwright 1.59.1 + installed Google Chrome).
// Data files: coffee_raw.txt / coffee_centred.txt are dosresmeta::coffee_mort written in the app format. (Chrome headless, 1400x900, light). usage: node drshots.mjs <work-dir> <app-file-url>
import { chromium } from "playwright";
import { readFileSync, writeFileSync } from "fs";
const [D, APP] = process.argv.slice(2);
const b = await chromium.launch({ channel: "chrome" });
const ctx = await b.newContext({ viewport: { width: 1400, height: 900 }, colorScheme: "light", deviceScaleFactor: 1, acceptDownloads: true });
const p = await ctx.newPage();
const errs = []; p.on("pageerror", (e) => errs.push(e.message)); p.on("console", (m) => { if (m.type() === "error") errs.push(m.text()); });
const log = {};
await p.goto(APP); await p.waitForTimeout(500);
const top = async () => { await p.evaluate(() => window.scrollTo(0, 0)); await p.waitForTimeout(300); };
const at = async (sel, off = 20) => { await p.evaluate(([s, o]) => { const e = document.querySelector(s); window.scrollTo(0, e.getBoundingClientRect().top + scrollY - o); }, [sel, off]); await p.waitForTimeout(300); };
const fill = async (txt) => { await p.fill("#f-data", txt); await p.dispatchEvent("#f-data", "input"); await p.waitForTimeout(500); await p.evaluate(() => { document.getElementById("f-data").scrollTop = 0; }); };
// 1 data entry
await fill(readFileSync(D + "/coffee_raw.txt", "utf8"));
await p.evaluate(() => { const t = document.getElementById("f-data"); t.scrollTop = 0; });
await top(); await p.screenshot({ path: `${D}/step1.png` });
// 2 linear result as shipped
await at("#headline", 70); await p.screenshot({ path: `${D}/step2.png` });
log.linear_raw = await p.evaluate(() => window._almLastDoseResponse());
// 3 workaround: doses relative to each study's reference
await fill(readFileSync(D + "/coffee_centred.txt", "utf8"));
await at("#headline", 70); await p.screenshot({ path: `${D}/step3.png` });
log.linear_centred = await p.evaluate(() => window._almLastDoseResponse());
// 4 3-knot spline curve
await fill(readFileSync(D + "/coffee_raw.txt", "utf8"));
await p.selectOption("#f-shape", "spline3"); await p.waitForTimeout(600);
await at("#headline", 70); await p.screenshot({ path: `${D}/step4.png` });
log.spline = await p.evaluate(() => window._almLastDoseResponse()); log.headline3 = await p.textContent("#headline");
// 5 the same data with 4 knots: dosresmeta refuses this fit (studies with too few dose levels); the app returns a curve
await p.selectOption("#f-shape", "spline4"); await p.waitForTimeout(600);
await at("#headline", 70); await p.screenshot({ path: `${D}/step5.png` });
log.spline4 = await p.evaluate(() => window._almLastDoseResponse());
log.headline4 = await p.textContent("#headline"); log.headline3 = null;
log.export_buttons = await p.$$eval("#alm-export-mount button, #alm-export-mount a", (els) => els.map((e) => e.textContent.trim()));
log.errors = errs;
writeFileSync(`${D}/shots_log.json`, JSON.stringify(log, null, 1));
console.log(JSON.stringify({ lin: log.linear_raw && [log.linear_raw.slope, log.linear_raw.se, log.linear_raw.k], cen: log.linear_centred && [log.linear_centred.slope, log.linear_centred.se], spline: log.spline && log.spline.shape, h4: log.headline4, b4: log.spline4 && log.spline4.beta, export: log.export_buttons, errors: errs }));
await b.close();
