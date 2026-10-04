# Figure 1: using the app, step by step

Data: dosresmeta::coffee_mort (coffee and all-cause mortality, 22 studies), doses as published. App: allmeta commit 0f8b86d.

## How the images were captured
- **Browser:** Google Chrome, driven by Playwright (`capture.mjs`), light theme.
- **Window:** 1106 × 900 CSS px.
- **Resolution:** 6 device pixels per CSS pixel, so no image is ever enlarged.
- **Cropping:** each image is cropped tightly to the panels it shows.
- **Composites:** steps 4–6 are labelled composites (A, B, C) of regions of one page state, stacked by `compose.py`. Steps 1–3 are single crops.
- **Formats:** final width 2400–3300 px, lossless PNG plus uncompressed TIFF at 359–493 dpi for a 170 mm print width.
- **Legibility:** text measured in the page prints at 8.7 pt or larger at 170 mm. See `legibility.json`.

## Steps
- **step1: Data entry.** The coffee mortality data pasted in, one row per dose level (`study, dose, cases, n, logRR, SE, type`). Each study's reference level has a blank SE.
- **step2: Choosing the model.**
  - Curve: restricted cubic spline, 3 knots. The default knots are Harrell's percentiles; knots can also be set by hand.
  - Within-study covariance: Greenland–Longnecker.
  - Approach: two-stage.
  - Pooling method (τ² estimator): random effects, REML.
  - Optional meta-regression.
- **step3: Linear-trend results.**
  - Pooled slope −0.03256 log RR per cup/day (SE 0.00503), the same as dosresmeta.
  - RR per cup/day 0.968 (95% CI 0.959 to 0.978).
  - Coefficient table, plus heterogeneity and goodness-of-fit statistics.
- **step4: Restricted cubic spline (composite).**
  - (A) Knots at 0, 2 and 6.5 cups/day; test for non-linearity χ² = 24.45, 1 df, p < 0.0001; coefficient table.
  - (B) Pooled relative risk curve on a log scale, with its 95% confidence band, each study's reported estimates and the knots.
- **step5: Heterogeneity, goodness of fit and residuals (composite).**
  - (A) Q test (Q = 101.4, 42 df) and I² = 58.6%; per-coefficient Q; between-study covariance Ψ.
  - Wald tests for any association and for non-linearity; deviance; R² 0.68.
  - (B) Decorrelated residuals against dose.
- **step6: Predictions and export (composite).**
  - (A) Reference dose 0 and the doses to report (1–6 cups/day).
  - (B) Predicted relative risks with 95% CIs, e.g. 0.868 (0.836 to 0.901) at 2 cups/day.
  - (C) Export buttons: Methods + Results (Markdown), text, JSON, CSV, and data (Markdown).

## To regenerate
Serve the repository root, for example `python -m http.server 8000`, then:

```bash
node docs/screenshots/capture.mjs work http://localhost:8000/app/dose-response-ma/index.html
python docs/screenshots/compose.py work docs/screenshots
```
