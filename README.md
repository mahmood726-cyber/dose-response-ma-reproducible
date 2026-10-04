# dose-response-ma-reproducible

[![reproduce](https://github.com/mahmood726-cyber/dose-response-ma-reproducible/actions/workflows/reproduce.yml/badge.svg)](https://github.com/mahmood726-cyber/dose-response-ma-reproducible/actions/workflows/reproduce.yml)
[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/mahmood726-cyber/dose-response-ma-reproducible?quickstart=1)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23135712.svg)](https://doi.org/10.5281/zenodo.23135712)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

The [allmeta](https://github.com/mahmood726-cyber/allmeta) **dose-response app** runs dose-response meta-analysis offline in the browser
([live](https://mahmood726-cyber.github.io/allmeta/dose-response-ma/)). It offers:

- **Curves:** linear, quadratic, or restricted cubic splines with 3–5 knots or knots you choose.
- **Within-study covariance:** Greenland–Longnecker, Hamling, or none.
- **Two-stage pooling:** REML, ML, method of moments or fixed effect, with optional meta-regression on one study-level covariate.
- **One-stage pooling:** REML, ML or fixed effect.
- **Outputs:** Q, I², Wald tests for association and non-linearity, goodness of fit, predictions at any reference dose, and the curve with a residual plot.

This repository validates the app against the R package **dosresmeta** on every multi-study binary dataset that dosresmeta ships. It checks every number in the accompanying F1000Research article.

## Quick start

```bash
git clone https://github.com/mahmood726-cyber/dose-response-ma-reproducible && cd dose-response-ma-reproducible
docker build -t drma . && docker run --rm -v "$PWD/outputs:/work/outputs" drma        # canonical
```

Without Docker you need R 4.6.0, Node 24.15.0 and Python 3.12 or 3.13:

1. `Rscript bench/install_r_packages.R`
2. `python -m pip install -r requirements.txt`
3. `python reproduce.py` (or `--quick`)

`make setup` and `make reproduce` do the same. **To use the app**, open `app/dose-response-ma/index.html` in a browser.

## What it shows

The app is validated at **allmeta commit [`0f8b86d`](https://github.com/mahmood726-cyber/allmeta/commit/0f8b86d984e4cba36f4f517f674a233d205e5e22)**. `app/` is byte-identical to that commit.

| | Result |
|---|---|
| Full grid: 724 model × covariance × approach × method combinations on 16 datasets (187 studies) | All 724 agree with dosresmeta. 576 fits agree within tolerance, and the app refuses the same 148 fits as unidentifiable. |
| Two-stage REML, by dataset | Linear trend 16/16; 3-knot spline 15/15 (1 refused by both); 4-knot 3/3 (13 refused by both); 5-knot 2/2 (14 refused by both). |
| Worked example: coffee and all-cause mortality | Linear slope −0.0326 per cup/day from both. 3-knot spline: RR 0.87 (0.84 to 0.90) at 2 cups/day; non-linearity χ² 24.5, p < 0.0001. |

Earlier versions of the app had known issues, fixed in [allmeta PR #76](https://github.com/mahmood726-cyber/allmeta/pull/76). See [CHANGELOG.md](CHANGELOG.md).

Tolerances follow allmeta's own parity test (`hub/shared/tests/_dr_parity_check.mjs`, mirrored in `analysis/make_outputs.py`):

- Coefficients within 1e-6 standard errors, and Wald statistics and predictions within 1e-5. These apply to fixed effect, method of moments and one-stage fits.
- Coefficients within 1e-3 standard errors and log-likelihoods within 1e-6 for two-stage REML and ML. The observed maxima are 9e-5 SE and 8e-8.

dosresmeta's one-stage optimiser stops at 100 Nelder–Mead evaluations. In 120 of its fits it had not converged; the app reproduces those estimates and warns, as dosresmeta does.

## Layout

| Path | Contents |
|---|---|
| `app/` | The app, byte-identical to allmeta commit `0f8b86d` |
| `bench/build_corpus.R` | Builds the 17-dataset corpus from dosresmeta |
| `bench/reference_dosresmeta.R` | dosresmeta reference fits over the option grid |
| `bench/run_engine.mjs` | Runs the app's JavaScript engine on the same data |
| `analysis/make_outputs.py` | Tables, figures, statistics, PASS/FAIL |
| `analysis/compare_runs.py` | Cross-platform comparison |
| `expected/` | Every number as printed in the paper |
| `docs/` | Paper, `numbers.json`, Figure 1 screenshots and their capture script |

## Outputs and how they map to the paper

`python reproduce.py` writes to `outputs/full/`:

| File | Paper |
|---|---|
| `docs/screenshots/step1.png` … `step6.png` | Figure 1: using the app, step by step (`captions.md`) |
| `table1_parity_by_configuration.csv` | Table 1: agreement by model, covariance, approach and method |
| `table2_by_dataset.csv` | Table 2: results by dataset |
| `table3_parity_all_fits.csv` | Every fit (extended data) |
| `figure2_by_dataset.png` (+ `.csv`) | Figure 2: agreement by dataset |
| `figure3_coffee_mortality.png` (+ `.csv`) | Figure 3: worked example (coffee and mortality) |
| `figure4_parity_grid.png` (+ `.csv`) | Figure 4: all fits, by approach and method |
| `visual_abstract.png` | Visual abstract |
| `stats.json` | Every number quoted in the text |
| `reproduction_report.md` | Expected versus reproduced, PASS/FAIL per number |

## Environment and determinism

- **R 4.6.0.** The image is `rocker/r-ver:4.6.0`. dosresmeta 2.2.0, rms 8.1-1, mvmeta 1.0.3, mixmeta 1.2.2 and their dependencies come from the Posit Package Manager snapshot of 2026-10-01.
- **Node 24.15.0** (`.nvmrc`) runs the app's JavaScript engine. There are no npm dependencies.
- **Python** builds the tables and figures (numpy and matplotlib, pinned in `requirements.txt`).
- **Docker is the canonical environment.** CI runs the full validation on every push on Linux, Windows, macOS and Docker. `analysis/compare_runs.py` then requires the corpus and the engine's output to be bit-identical across the x86-64 runs. macOS on ARM is reported but not required to match: V8 there can differ in the last bit.
- **R's own values** differ between operating systems in the last bits. The printed numbers are chosen to be robust to this, and are checked on every platform.

Run time: a few minutes, mostly the 724 R fits.

## Data

The data are not redistributed here. `bench/build_corpus.R` builds them at run time from the datasets shipped with dosresmeta (GPL-2 | GPL-3), which cites each original source.

Datasets used: `alcohol_crc`, `alcohol_cvd`, `alcohol_esoph`, `alcohol_lc`, `bmi_rc`, `coffee_cancer`, `coffee_cvd`, `coffee_mort`, `coffee_mort_add`, `coffee_stroke`, `fish_ra`, `milk_mort`, `milk_ov`, `oc_breast`, `process_bc`, `red_bc` and `sim_os`.

Left out:

- `ari`, a continuous outcome.
- The single-study examples (`cc_ex`, `ci_ex`, `ir_ex`).

Studies without case and total counts are excluded, because the covariance reconstruction needs them. `coffee_mort_add` has fewer than 2 studies with counts.

## Cite

Ahmad M. Dose-response meta-analysis in the browser: a tool validated against the R package dosresmeta [software], v1.0.0. Zenodo; 2026. doi:[10.5281/zenodo.23135712](https://doi.org/10.5281/zenodo.23135712). Machine-readable metadata: `CITATION.cff`.

## Licence

MIT, the same as allmeta.
