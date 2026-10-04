# Dose-response meta-analysis in the browser: a tool validated against the R package dosresmeta

**Mahmood Ahmad**¹ [AUTHOR TO COMPLETE: ORCID, corresponding-author e-mail]

¹ [AUTHOR TO COMPLETE: affiliation]

## Abstract

**Background:** Dose-response meta-analysis is usually run in R or Stata, which many reviewers do not use. We describe a browser tool for it and its validation against the reference R package.

**Methods:** The allmeta dose-response app fits linear, quadratic and restricted cubic spline curves, with Greenland–Longnecker, Hamling or no within-study covariance, by two-stage or one-stage approaches. It reports heterogeneity, Wald and goodness-of-fit tests and predictions. We compared it with dosresmeta on every multi-study binary dataset that package distributes (16 datasets; 187 studies), across 724 model, covariance, approach and method combinations, in a containerised analysis run on four platforms.

**Results:** All 724 combinations agreed: 576 fits within numerical tolerance, and the same 148 fits refused as unidentifiable.

**Conclusions:** The app reproduces dosresmeta offline, without installation or programming.

**Keywords:** dose-response meta-analysis; restricted cubic splines; Greenland–Longnecker; multivariate meta-analysis; software validation; reproducibility; browser-based software

## Introduction

Dose-response meta-analysis pools relative risks reported at several doses against a common reference, so estimates within a study are correlated. The Greenland–Longnecker [1,2] and Hamling [3] methods reconstruct this covariance from reported counts. Non-linear curves use restricted cubic splines pooled by multivariate meta-analysis [4–6]. The reference implementation is the R package dosresmeta [7], built on mixmeta [8].

allmeta is a collection of offline browser tools for evidence synthesis [9]. We describe its dose-response app and validate it against dosresmeta on every suitable dataset that package distributes.

## Methods

### Implementation

The app is a static web page (https://mahmood726-cyber.github.io/allmeta/dose-response-ma/). Its engine, `dose-response.js`, ports dosresmeta's and mixmeta's estimation to JavaScript:

- **Data.** One row per dose level. Doses are measured from each study's reference dose.
- **Two-stage approach.** Each study is fitted by generalised least squares. The pooling uses one of:
  - REML or ML (iterative start, then BFGS with the analytic gradient, as in mixmeta);
  - method of moments;
  - fixed effect.

  An optional meta-regression adds one study-level covariate. Studies with fewer non-reference doses than curve coefficients are refused, as in dosresmeta.
- **One-stage approach.** All points are fitted jointly (REML, ML or fixed effect).
- **Outputs.**
  - Q, I² and Wald tests for association and non-linearity;
  - deviance and R² [7];
  - predictions at any reference dose;
  - the pooled curve and a residual plot;
  - Markdown, JSON and CSV export.

### Operation

The app needs only a browser and works offline. A user (Figure 1):

1. pastes or types the data;
2. chooses the curve, knots, covariance, approach and pooling method;
3. reads the linear trend;
4. reviews the spline curve with its confidence band and the non-linearity test;
5. checks heterogeneity, goodness of fit and residuals;
6. reports predicted relative risks at chosen doses, then exports.

### Validation

We validated allmeta commit 0f8b86d. The corpus comprised the 17 multi-study binary datasets in dosresmeta 2.2.0 [10] (203 studies, 890 dose levels). Excluding 16 studies that lacked counts left 16 datasets and 187 studies.

dosresmeta (splines via rms [11]) fitted five curves (linear, quadratic, splines with 3–5 knots), each with seven approach/method combinations, plus Hamling, independent-covariance and meta-regression fits: 724 combinations in all. The app's engine ran on the same data.

Agreement required:
- coefficients within 10⁻⁶ standard errors;
- for two-stage REML/ML, coefficients within 10⁻³ standard errors and log-likelihoods within 10⁻⁶;
- identical refusals.

One command (`python reproduce.py`) runs everything. The canonical environment is a Docker image (R 4.6.0, dated package snapshot, Node 24.15.0). Continuous integration repeats the analysis on Linux, Windows, macOS and Docker and checks every reported number.

## Results

**Agreement.** dosresmeta fitted 576 combinations and refused 148. The app refused the same 148 and agreed on all 576 (Table 1, Figures 2 and 4):

- Fixed-effect, method-of-moments and one-stage coefficients agreed within 10⁻⁶ standard errors.
- Two-stage REML and ML coefficients agreed within 10⁻⁴ standard errors, and log-likelihoods within 10⁻⁷. The small differences arise where the likelihood is flat, so the two optimisers stop at slightly different points within tolerance.

dosresmeta's one-stage optimiser stopped at its 100-evaluation limit in 120 fits. The app reproduces these estimates and gives the same non-convergence warning.

**By dataset** (two-stage REML; Table 2):

| Curve | Agreed with dosresmeta | Refused by both |
|---|---|---|
| Linear trend | all 16 datasets (12 include studies with non-zero reference doses) | none |
| Three-knot spline | 15 datasets | 1 |
| Four-knot spline | 3 datasets | 13 |
| Five-knot spline | 2 datasets | 14 |

**Worked example.** For coffee and all-cause mortality (22 studies) [12], both programs gave a linear slope of −0.0326 per cup/day (SE 0.0050). A three-knot spline (knots 0, 2 and 6.5 cups/day) showed non-linearity (χ² = 24.5, 1 df, p < 0.0001; I² = 59%), with relative risk 0.87 (95% CI 0.84 to 0.90) at 2 cups/day. The two programs agreed within 10⁻⁸ (Figure 3).

**Reproducibility.** Every checked number reproduced on all four platforms.

## Discussion

The app gives reviewers dosresmeta's curves, covariances, approaches and estimators in a browser, without installation or programming, and with every result reproducible against the reference package.

Limitations:
- The test datasets are curated examples.
- Continuous outcomes are not supported.
- Meta-regression takes one covariate (two-stage only).
- One-stage fits inherit dosresmeta's iteration limit.

## Conclusions

A browser tool can reproduce standard dose-response meta-analysis, validated across a corpus of published datasets.

## Data availability

**Underlying data:** datasets distributed with the R package dosresmeta 2.2.0 [10] (GPL-2 | GPL-3), built at run time and not redistributed.

**Extended data:** the validated app, analysis code, expected values, tables, figures and screenshots are at https://github.com/mahmood726-cyber/dose-response-ma-reproducible, archived at Zenodo (https://doi.org/10.5281/zenodo.23135712). Licence: MIT.

## Software availability

- **Source code available from:** https://github.com/mahmood726-cyber/allmeta (`dose-response-ma/`, `shared/dose-response.js`); validated version: commit 0f8b86d984e4cba36f4f517f674a233d205e5e22
- **Archived source code at time of publication:** https://doi.org/10.5281/zenodo.23135712 (dose-response-ma-reproducible v1.0.0)
- **Licence:** MIT

## Competing interests

The author develops allmeta. [AUTHOR TO CONFIRM: no other competing interests.]

## Grant information

[AUTHOR TO COMPLETE]

## Acknowledgements

[AUTHOR TO COMPLETE.] Claude (Anthropic), an AI assistant, helped write the software, the analysis code and the draft of this manuscript. The author checked all code, results and text.

## References

1. Greenland S, Longnecker MP. Methods for trend estimation from summarized dose-response data, with applications to meta-analysis. Am J Epidemiol. 1992;135(11):1301–9. doi:10.1093/oxfordjournals.aje.a116237
2. Orsini N, Bellocco R, Greenland S. Generalized least squares for trend estimation of summarized dose–response data. Stata J. 2006;6(1):40–57. doi:10.1177/1536867X0600600103
3. Hamling J, Lee P, Weitkunat R, Ambühl M. Facilitating meta-analyses by deriving relative effect and precision estimates for alternative comparisons from a set of estimates presented by exposure level or disease category. Stat Med. 2008;27(7):954–70. doi:10.1002/sim.3013
4. Orsini N, Li R, Wolk A, Khudyakov P, Spiegelman D. Meta-analysis for linear and nonlinear dose-response relations: examples, an evaluation of approximations, and software. Am J Epidemiol. 2012;175(1):66–73. doi:10.1093/aje/kwr265
5. Gasparrini A, Armstrong B, Kenward MG. Multivariate meta-analysis for non-linear and other multi-parameter associations. Stat Med. 2012;31(29):3821–39. doi:10.1002/sim.5471
6. Harrell FE. Regression modeling strategies. 2nd ed. Cham: Springer; 2015. doi:10.1007/978-3-319-19425-7
7. Crippa A, Orsini N. Multivariate dose-response meta-analysis: the dosresmeta R package. J Stat Softw. 2016;72(Code Snippet 1). doi:10.18637/jss.v072.c01
8. Sera F, Armstrong B, Blangiardo M, Gasparrini A. An extended mixed-effects framework for meta-analysis. Stat Med. 2019;38(29):5429–44. doi:10.1002/sim.8362
9. Ahmad M. allmeta — open browser-only tools for evidence synthesis [software]. Zenodo; 2026. doi:10.5281/zenodo.20516880
10. Crippa A. dosresmeta: Multivariate dose-response meta-analysis [R package and datasets], version 2.2.0. The R Foundation; 2013. doi:10.32614/CRAN.package.dosresmeta
11. Harrell FE Jr. rms: Regression modeling strategies [R package], version 8.1-1. The R Foundation; 2009. doi:10.32614/CRAN.package.rms
12. Crippa A, Discacciati A, Larsson SC, Wolk A, Orsini N. Coffee consumption and mortality from all causes, cardiovascular disease, and cancer: a dose-response meta-analysis. Am J Epidemiol. 2014;180(8):763–75. doi:10.1093/aje/kwu194

## Figure and table legends

**Figure 1.** Using the app, step by step (coffee and all-cause mortality data; Google Chrome, light theme; high-resolution captures cropped to the relevant panels).
(1) Data entry, one row per dose level.
(2) Choosing the model: curve, knots, covariance, approach and pooling method.
(3) Linear-trend results.
(4) Three-knot spline: the non-linearity test and coefficients (A) and the pooled curve with 95% band, study estimates and knots (B).
(5) Heterogeneity and goodness-of-fit statistics (A) and the decorrelated-residual plot (B).
(6) Prediction settings (A), predicted relative risks at chosen doses (B) and export buttons (C).
Panels 4–6 are labelled composites of regions of one page; panels 1–3 are single crops.

**Figure 2.** Coefficient differences from dosresmeta (in its standard errors) for every fit, by dataset.

**Figure 3.** Worked example, coffee and all-cause mortality: (A) linear trend; (B) three-knot spline. Each panel shows the app against dosresmeta, with dosresmeta's 95% confidence band.

**Figure 4.** App versus dosresmeta for all 576 fits both programs return, grouped by approach and method.

**Table 1.** Agreement with dosresmeta by model, covariance, approach and method: fits, refusals and largest differences. Tolerances:
- coefficients: 10⁻⁶ standard errors (10⁻³ for two-stage REML/ML);
- log-likelihood: 10⁻⁶;
- Wald statistics and predictions: 10⁻⁵ (10⁻³ for two-stage REML/ML).

**Table 2.** Results by dataset: studies, combinations fitted and refused, largest coefficient difference, and the linear slope from each program.
