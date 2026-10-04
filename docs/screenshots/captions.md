# Figure 1: using the app, step by step

Google Chrome, 1400 × 900, light theme. Data: dosresmeta::coffee_mort (coffee and all-cause mortality, 22 studies), doses as published.
App: allmeta commit 0f8b86d.

Captured by `docs/screenshots/capture.mjs`. Steps 4–6 are labelled composites built by `docs/screenshots/compose.py`. Each one shows regions (A, B, C) of a single page state, cropped from a full-page screenshot at its original resolution.

- **step1.png: Data entry.** The coffee mortality data pasted in, one row per dose level (`study, dose, cases, n, logRR, SE, type`). Each study's reference level has a blank SE.
- **step2.png: Choosing the model.**
  - Curve: restricted cubic spline, 3 knots. The default knots are Harrell's percentiles; knots can also be set by hand.
  - Within-study covariance: Greenland–Longnecker.
  - Approach: two-stage.
  - Pooling method (τ² estimator): random effects, REML.
  - The prediction settings appear below.
- **step3.png: Linear-trend results.**
  - Pooled slope −0.03256 log RR per cup/day (SE 0.00503), the same as dosresmeta.
  - RR per cup/day 0.968 (95% CI 0.959 to 0.978).
  - Coefficient table and heterogeneity tests.
- **step4.png: Restricted cubic spline (composite).**
  - (A) Headline: knots at 0, 2 and 6.5 cups/day; test for non-linearity χ² = 24.45, 1 df, p < 0.0001. Coefficient table below.
  - (B) Pooled relative risk curve on a log scale, with its 95% confidence band, each study's reported estimates and the knots.
- **step5.png: Heterogeneity, goodness of fit and residuals (composite).**
  - (A) Q test (Q = 101.4, 42 df) and I² = 58.6%; per-coefficient Q; between-study covariance Ψ.
  - Wald tests for any association and for non-linearity; deviance; R² 0.68.
  - (B) Decorrelated residuals against dose.
- **step6.png: Predictions and export (composite).**
  - (A) Reference dose 0 and the doses to report (1–6 cups/day).
  - (B) Predicted relative risks with 95% CIs, e.g. 0.868 (0.836 to 0.901) at 2 cups/day.
  - (C) Export buttons: Methods + Results (Markdown), text, JSON, CSV, and data (Markdown).
