# Changelog

## Validated version

This repository validates the allmeta dose-response app at **allmeta commit `0f8b86d984e4cba36f4f517f674a233d205e5e22`**,
the merge of [allmeta PR #76](https://github.com/mahmood726-cyber/allmeta/pull/76). `app/` is byte-identical to that commit.

## Earlier versions of the app (history)

Versions of the app before PR #76 had known issues. All of them were found by this repository's first validation run, against allmeta `ac5435b`, and fixed in PR #76.

| Issue | Before PR #76 | Since PR #76 |
|---|---|---|
| Linear trend | Used raw doses rather than doses relative to each study's reference dose. It agreed with dosresmeta on 4 of 16 datasets. | Doses measured from each study's reference, as in dosresmeta: 16 of 16. |
| Four-knot spline pooling | Nelder–Mead from a clamped start, with a fixed step and an iteration cap, stopped far from the REML optimum. It agreed on 0 of 3 datasets. | mixmeta's algorithm, ported: RIGLS start, then BFGS with the analytic gradient. 3 of 3 agree. |
| Unidentifiable fits | Studies with fewer non-reference doses than spline coefficients were not checked. The app returned estimates for 14 fits that dosresmeta refuses, with coefficients up to about 10¹². | Two-stage fits are refused and the studies named, as in dosresmeta. |
| Example data | Labelled `dosresmeta::alcohol_cvd`, but 4 of its 6 studies differed from that dataset. | Replaced with the real `alcohol_cvd` data. |

PR #76 also added:
- quadratic and 5-knot or user-chosen-knot splines;
- Hamling and independent covariance;
- the one-stage approach;
- ML, method of moments and fixed-effect pooling;
- one-covariate meta-regression;
- Q and I²;
- Wald tests;
- goodness of fit and a residual plot;
- predictions at any reference dose.

PR #76 includes a regression test pinned to dosresmeta, `hub/shared/tests/dose-response-rcs4-regression.spec.mjs`. It failed on the earlier code (allmeta `511aa72`) and passes since. It also includes a parity test over the full grid used here, `dose-response-dosresmeta-parity.spec.mjs`.

## This repository

- **Unreleased:** validation of allmeta `0f8b86d` against dosresmeta 2.2.0 on 724 model × covariance × approach × method combinations. All 724 agree: 576 fits within tolerance and the same 148 refusals.
