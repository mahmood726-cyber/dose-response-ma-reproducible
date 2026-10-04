# Figure 1 screenshots (Google Chrome, 1400 × 900, light theme; data: dosresmeta::coffee_mort, 22 studies, doses as published)

Captured by `docs/screenshots/capture.mjs` from the corrected app in `app/`.

- **step1.png**: Data entry (one row per dose level) and the model, covariance, approach, method, meta-regression and prediction options.
- **step2.png**: Linear trend, two-stage REML. The pooled slope is −0.03256 per cup/day (SE 0.00503), the same as dosresmeta, although 12 of the 22 studies use a non-zero reference dose.
- **step3.png**: Three-knot restricted cubic spline, two-stage REML. The page shows coefficients, the Q test and I², Ψ, Wald tests for any association and for non-linearity, goodness of fit, and predicted relative risks against 0 cups/day (RR 0.868 at 2 cups/day).
- **step4.png**: The same fit drawn as a pooled curve with its 95% band, study estimates and knots, next to the decorrelated-residual plot; per-study coefficients below.
- **step5.png**: Four-knot spline, two-stage. The app refuses the fit and names the two studies with too few dose levels, as dosresmeta does.
- **step6.png**: Four-knot spline, one-stage REML, which uses those studies. The page warns that the optimiser stopped at dosresmeta's 100-evaluation limit, the same warning dosresmeta gives.
