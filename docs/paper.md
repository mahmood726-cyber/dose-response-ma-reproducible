# Dose-response meta-analysis in the browser: a tool validated against the R package dosresmeta

**Mahmood Ahmad**¹ [AUTHOR TO COMPLETE: ORCID, corresponding-author e-mail]

¹ [AUTHOR TO COMPLETE: affiliation]

## Abstract

**Background:** Dose-response meta-analysis is usually run in R or Stata. We describe a browser tool and its validation against the reference R package.

**Methods:** The allmeta dose-response app fits linear, quadratic and spline curves with Greenland–Longnecker, Hamling or no within-study covariance, by two-stage or one-stage approaches. We compared it with dosresmeta on every multi-study binary dataset that package distributes (16 datasets; 187 studies) across 724 model and option combinations, in one containerised analysis run on four platforms.

**Results:** A first validation found three defects: the linear trend ignored non-zero reference doses (4 of 16 datasets agreed), four-knot splines were pooled at the wrong optimum (0 of 3 agreed), and 14 fits that dosresmeta refuses were returned. After correction, all 724 combinations agreed, including 148 refusals.

**Conclusions:** The app reproduces dosresmeta across its options. Corpus-wide testing found defects a single-example test had missed.

**Keywords:** dose-response meta-analysis; restricted cubic splines; Greenland–Longnecker; multivariate meta-analysis; software validation; reproducibility; browser-based software

## Introduction

Dose-response meta-analysis pools relative risks reported at several doses against a common reference, so estimates within a study are correlated. The Greenland–Longnecker [1,2] and Hamling [3] methods reconstruct this covariance from reported counts. Non-linear curves use restricted cubic splines pooled by multivariate meta-analysis [4–6]. The reference implementation is the R package dosresmeta [7], which builds on mixmeta [8].

allmeta is a collection of offline browser tools for evidence synthesis [9]. Its dose-response app claimed to match dosresmeta on the strength of one dataset. We tested that claim on every suitable dataset, corrected what failed, and extended the app to dosresmeta's main options.

## Methods

### Implementation

The app is a static web page (https://mahmood726-cyber.github.io/allmeta/dose-response-ma/) whose engine, `dose-response.js`, ports dosresmeta's and mixmeta's estimation to JavaScript:

- **Data.** One row per dose level; doses are measured from each study's reference dose.
- **Two-stage approach.** Per-study generalised least squares, then pooling by REML or ML (iterative start, then BFGS with the analytic gradient, as in mixmeta), method of moments or fixed effect, with optional meta-regression.
- **One-stage approach.** All points fitted jointly (REML, ML or fixed effect).
- **Outputs.** Q, I², Wald tests for association and non-linearity, deviance and R² [7], predictions at any reference dose, the curve and a residual plot.

### Validation

The corpus comprised the 17 multi-study binary datasets in dosresmeta 2.2.0 [10] (203 studies, 890 dose levels); 16 studies lacking counts were excluded, leaving 16 datasets and 187 studies. dosresmeta (splines via rms [11]) fitted five curves (linear, quadratic, splines with 3–5 knots) with seven approach/method combinations each, plus Hamling, independent-covariance and meta-regression fits: 724 combinations, which the app's engine ran on the same data. Agreement required coefficients within 10⁻⁶ standard errors (10⁻³ for iterative two-stage REML/ML, with log-likelihoods within 10⁻⁶) and identical refusals.

One command (`python reproduce.py`) runs everything; the canonical environment is a Docker image (R 4.6.0, dated package snapshot, Node 24.15.0). Continuous integration repeats the analysis on Linux, Windows, macOS and Docker and checks every reported number.

### Operation

The app needs only a browser and works offline (Figure 1); the validation needs Docker, or R, Node and Python.

## Results

**Defects found.** The original engine (allmeta ac5435b), judged against its own claimed tolerances, showed three defects (Table 1, Figure 2):

- **Linear trend.** Raw doses were used, so only 4 of 16 datasets agreed; 12 contain studies with a non-zero reference dose (largest slope error 0.056, BMI and renal cancer).
- **Four-knot splines.** None of 3 fittable datasets agreed: per-study estimates were correct, but the pooling optimiser (Nelder–Mead from a clamped start, fixed step, iteration cap) stopped far from the REML optimum.
- **Unwarranted estimates.** In 14 fits some studies had fewer non-reference doses than spline coefficients; dosresmeta refuses these, but the app returned estimates (coefficients above 10¹² in one).

Doses are now measured from each study's reference, mixmeta's optimiser is ported, and two-stage fits refuse, naming the offending studies.

**Validation after correction.** dosresmeta fitted 576 combinations and refused 148; the corrected app refused the same 148 and agreed on all 576 (Table 2, Figure 4):

- Fixed-effect, method-of-moments and one-stage coefficients agreed within 10⁻⁶ standard errors.
- Two-stage REML and ML coefficients agreed within 10⁻⁴ standard errors and log-likelihoods within 10⁻⁷; residual differences arise where the likelihood is flat, so the optimisers stop at slightly different points within tolerance.

dosresmeta's one-stage optimiser hit its 100-evaluation limit in 120 fits; the app reproduces these and, like dosresmeta, warns.

**Worked example.** For coffee and all-cause mortality (22 studies, 12 with a non-zero reference dose) [12], dosresmeta's linear slope was −0.0326 per cup/day; the original app gave −0.0313, the corrected app −0.0326. The three-knot spline (relative risk 0.87 at 2 cups/day) matched within 10⁻⁸ (Figure 3).

**Reproducibility.** Every checked number reproduced on all four platforms.

## Discussion

The corrected app reproduces dosresmeta offline, without installation. Corpus-wide testing exposed defects in reference-dose handling, optimisation and input checking that one dataset could not reveal.

Limitations: the datasets are curated examples; continuous outcomes are unsupported; meta-regression takes one covariate (two-stage only); one-stage fits inherit dosresmeta's iteration limit.

## Conclusions

A browser tool can reproduce standard dose-response meta-analysis when validated across a corpus, not one example.

## Data availability

**Underlying data:** datasets distributed with the R package dosresmeta 2.2.0 [10] (GPL-2 | GPL-3), built at run time and not redistributed.

**Extended data:** original and corrected engines, analysis code, expected values, tables, figures and screenshots: https://github.com/mahmood726-cyber/dose-response-ma-reproducible; archived at Zenodo [DOI — TO BE MINTED]. Licence: MIT.

## Software availability

- **Source code available from:** https://github.com/mahmood726-cyber/allmeta (`dose-response-ma/`, `shared/dose-response.js`)
- **Archived source code at time of publication:** [ZENODO DOI — TO BE MINTED for dose-response-ma-reproducible v1.0.0]
- **Licence:** MIT

## Competing interests

The author develops allmeta. [AUTHOR TO CONFIRM: no other competing interests.]

## Grant information

[AUTHOR TO COMPLETE]

## Acknowledgements

[AUTHOR TO COMPLETE.] Claude (Anthropic), an AI assistant, helped write the software, the analysis code and the draft of this manuscript; the author checked all code, results and text.

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

**Figure 1.** Using the app (coffee and mortality data). (A) Data entry and options. (B) Linear trend. (C) Three-knot spline: coefficients, tests and predictions. (D) Pooled curve and residual plot. (E) Four-knot two-stage fit refused, naming the studies with too few doses. (F) The same curve fitted by the one-stage approach.
**Figure 2.** Largest coefficient difference from dosresmeta (in its standard errors) for each dataset, before and after correction: linear trend and three- and four-knot splines (two-stage REML, Greenland–Longnecker covariance).
**Figure 3.** Worked example, coffee and all-cause mortality: (A) linear trends from dosresmeta and the original and corrected app; (B) three-knot spline, corrected app versus dosresmeta with 95% confidence band.
**Figure 4.** Corrected app versus dosresmeta for all 576 fits both programs return, grouped by approach and method.
**Table 1.** Defects found by the first validation, their causes, and agreement before and after correction.
**Table 2.** Agreement with dosresmeta by model, covariance, approach and method: fits, refusals, and largest differences. Tolerances: coefficients 10⁻⁶ standard errors (10⁻³ for two-stage REML/ML, log-likelihood 10⁻⁶); Wald statistics and predictions 10⁻⁵ (10⁻³ for two-stage REML/ML).
