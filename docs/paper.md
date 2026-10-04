# Dose-response meta-analysis in the browser: validation of the allmeta dose-response app against R dosresmeta

**Mahmood Ahmad**¹ [AUTHOR TO COMPLETE: ORCID, corresponding-author e-mail]

¹ [AUTHOR TO COMPLETE: affiliation]

## Abstract

**Background:** Dose-response meta-analysis is usually run in R or Stata. We tested a browser implementation against the reference R package.

**Methods:** The allmeta dose-response app fits two-stage Greenland–Longnecker models with a linear trend or restricted cubic splines. We ran its shipped engine, unchanged, on every multi-study binary dataset distributed with the R package dosresmeta (17 datasets; 203 studies) and compared results with dosresmeta in a one-command, containerised analysis run on four platforms.

**Results:** Three-knot splines agreed with dosresmeta in 14 of 15 datasets (largest coefficient difference 1.0 × 10⁻⁶). The linear trend agreed in only 4 of 16, because the app ignores non-zero reference doses (largest slope difference 0.056); with reference-relative doses all 16 agreed. Four-knot splines disagreed in all 3 fittable datasets, and the app returned estimates without warning for 14 fits that dosresmeta refuses.

**Conclusions:** The app reproduces dosresmeta for three-knot splines and, with reference-relative doses, for linear trends. Its four-knot option and its handling of studies with too few doses need correction.

**Keywords:** dose-response meta-analysis; restricted cubic splines; Greenland–Longnecker; software validation; reproducibility; browser-based software

## Introduction

Dose-response meta-analysis pools relative risks reported at several doses against a common reference. Estimates within a study share that reference and are correlated; the Greenland–Longnecker method reconstructs the covariance from reported cases and totals [1,2]. Non-linear curves use restricted cubic splines pooled by multivariate meta-analysis [3–5], and dosresmeta is the reference R implementation [6].

allmeta is a collection of offline browser tools for evidence synthesis [7]. Its dose-response app states that it matches dosresmeta, but this rested on one dataset. We tested it on every suitable dataset distributed with dosresmeta.

## Methods

### Implementation

The app is a static web page with two JavaScript modules (`dose-response.js`, `ma-core.js`). Users enter one row per dose level (`study, dose, cases, n, logRR, SE, type`). The linear trend fits each study's slope by generalised least squares and pools slopes by REML. Splines use three or four knots at Harrell's percentiles [5], and pool coefficient vectors by multivariate REML.

We froze the app at allmeta commit ac5435b (identical to the live site). From the 17 multi-study binary datasets in dosresmeta 2.2.0 [8] (203 studies, 890 dose levels) we excluded 16 studies lacking counts, leaving 16 datasets and 187 studies. For each, we fitted linear, three-knot and four-knot models with dosresmeta (splines via `rms` [9]) and ran the shipped engine on the same data. Agreement was judged against the app's own stated tolerances (10⁻⁶ linear; 10⁻⁵ splines) on coefficients, standard errors, τ², covariances and fitted log relative risks.

One command (`python reproduce.py`) runs everything. The canonical environment is a Docker image (R 4.6.0, a dated package snapshot, Node 24.15.0). Continuous integration runs the analysis on Linux, Windows, macOS and Docker and checks every number reported here.

### Operation

The app needs only a modern browser and works offline: users paste data, choose the trend shape and τ² estimator, and export results as Markdown, JSON or CSV (Figure 1). The validation needs Docker, or R 4.6.0, Node 24 and Python 3.12+.

## Results

**Linear trend.** As shipped, the app agreed with dosresmeta in 4 of 16 datasets (Table 1, Figure 2). In 12, some study's reference dose was not zero: dosresmeta uses dose relative to each study's reference, whereas the app uses raw dose. The largest slope difference was 0.056 (BMI and renal cancer). With reference-relative doses, all 16 agreed (differences ≤ 2 × 10⁻⁷).

**Splines.** Three-knot splines agreed in 14 of 15 fittable datasets (largest coefficient, covariance or Ψ difference 1.0 × 10⁻⁶; the exception differed by 1.3 × 10⁻⁵ in one fitted log relative risk; Table 2). Four-knot splines disagreed in all 3 fittable datasets.

**Unidentifiable fits.** dosresmeta refused 1 three-knot and 13 four-knot fits where studies had fewer non-reference doses than spline coefficients. The app returned estimates for all 14 without warning, with coefficients exceeding 10¹² in one dataset (Figure 4).

**Worked example.** For coffee and all-cause mortality (22 studies, 12 with a non-zero reference) [10], dosresmeta's linear slope was −0.0326 per cup/day; the app gave −0.0313 as shipped and −0.0326 with reference-relative doses. The three-knot curve matched within 3 × 10⁻⁸ (relative risk 0.84 at 2.81 cups/day; Figure 3).

**Reproducibility.** Every checked number reproduced on all four platforms. Engine output was bit-identical across x86-64 platforms; on ARM (macOS), and for R across operating systems, values differed only in the last bits.

## Discussion

The three-knot spline faithfully implements the dosresmeta model, and the linear trend is correct with reference-relative doses. Three defects limit the shipped app: the linear trend ignores non-zero reference doses, four-knot pooling misses dosresmeta's estimates, and neither spline option refuses studies with too few doses. The app's own tests missed these because they used a single dataset whose reference doses are all zero and covered only three-knot splines. The defects have been logged for correction in allmeta.

Limitations: the datasets are curated examples rather than a random sample, only binary outcomes were tested, and bit-identity holds only across x86-64 platforms.

## Conclusions

A browser tool can closely reproduce standard dose-response meta-analysis, but testing across a corpus rather than a single example revealed defects that the original test missed.

## Data availability

**Underlying data:** datasets distributed with the R package dosresmeta 2.2.0 [8] (GPL-2 | GPL-3), built at run time and not redistributed.

**Extended data:** frozen app, analysis code, expected values, tables, figures and screenshots: https://github.com/mahmood726-cyber/dose-response-ma-reproducible; archived at Zenodo [DOI — TO BE MINTED]. Licence: MIT.

## Software availability

- **Source code available from:** https://github.com/mahmood726-cyber/allmeta (`dose-response-ma/`; live: https://mahmood726-cyber.github.io/allmeta/dose-response-ma/)
- **Archived source code at time of publication:** [ZENODO DOI — TO BE MINTED for dose-response-ma-reproducible v1.0.0]
- **Licence:** MIT

## Competing interests

The author develops allmeta. [AUTHOR TO CONFIRM: no other competing interests.]

## Grant information

[AUTHOR TO COMPLETE]

## Acknowledgements

[AUTHOR TO COMPLETE.] Claude (Anthropic), an AI assistant, helped write the analysis code and draft this manuscript; the author checked all code, results and text.

## References

1. Greenland S, Longnecker MP. Methods for trend estimation from summarized dose-response data, with applications to meta-analysis. Am J Epidemiol. 1992;135(11):1301–9. doi:10.1093/oxfordjournals.aje.a116237
2. Orsini N, Bellocco R, Greenland S. Generalized least squares for trend estimation of summarized dose–response data. Stata J. 2006;6(1):40–57. doi:10.1177/1536867X0600600103
3. Orsini N, Li R, Wolk A, Khudyakov P, Spiegelman D. Meta-analysis for linear and nonlinear dose-response relations: examples, an evaluation of approximations, and software. Am J Epidemiol. 2012;175(1):66–73. doi:10.1093/aje/kwr265
4. Gasparrini A, Armstrong B, Kenward MG. Multivariate meta-analysis for non-linear and other multi-parameter associations. Stat Med. 2012;31(29):3821–39. doi:10.1002/sim.5471
5. Harrell FE. Regression modeling strategies. 2nd ed. Cham: Springer; 2015. doi:10.1007/978-3-319-19425-7
6. Crippa A, Orsini N. Multivariate dose-response meta-analysis: the dosresmeta R package. J Stat Softw. 2016;72(Code Snippet 1). doi:10.18637/jss.v072.c01
7. Ahmad M. allmeta — open browser-only tools for evidence synthesis [software]. Zenodo; 2026. doi:10.5281/zenodo.20516880
8. Crippa A. dosresmeta: Multivariate dose-response meta-analysis [R package and datasets], version 2.2.0. The R Foundation; 2013. doi:10.32614/CRAN.package.dosresmeta
9. Harrell FE Jr. rms: Regression modeling strategies [R package], version 8.1-1. The R Foundation; 2009. doi:10.32614/CRAN.package.rms
10. Crippa A, Discacciati A, Larsson SC, Wolk A, Orsini N. Coffee consumption and mortality from all causes, cardiovascular disease, and cancer: a dose-response meta-analysis. Am J Epidemiol. 2014;180(8):763–75. doi:10.1093/aje/kwu194

## Figure and table legends

**Figure 1.** Using the app. (A) Data entry, one row per dose level. (B) Linear trend as shipped. (C) The same data with doses relative to each study's reference. (D) Three-knot spline curve, with export buttons. (E) The four-knot option on the same data, which dosresmeta refuses; the app reports an implausible relative risk.
**Figure 2.** Largest absolute difference from dosresmeta, by dataset and model. Dashed and dotted lines: the app's stated tolerances.
**Figure 3.** Worked example, coffee and all-cause mortality: (A) linear trends; (B) three-knot spline, app versus dosresmeta with 95% confidence band.
**Figure 4.** Fits that dosresmeta refuses but the app returns: largest absolute spline coefficient.
**Table 1.** Linear trend by dataset: dosresmeta and app slopes, as shipped and with reference-relative doses.
**Table 2.** Spline fits: largest differences from dosresmeta, and fits refused by dosresmeta.
