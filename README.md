# dose-response-ma-reproducible

[![reproduce](https://github.com/mahmood726-cyber/dose-response-ma-reproducible/actions/workflows/reproduce.yml/badge.svg)](https://github.com/mahmood726-cyber/dose-response-ma-reproducible/actions/workflows/reproduce.yml)
[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/mahmood726-cyber/dose-response-ma-reproducible?quickstart=1)
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

| | Original app (allmeta `ac5435b`) | Corrected app (`app/`) |
|---|---|---|
| Linear trend agrees with dosresmeta | 4 of 16 datasets: doses were not measured from each study's reference dose | 16 of 16 |
| 3-knot spline | 14 of 15 (within its own claimed 1e-5) | 15 of 15 |
| 4-knot spline | 0 of 3: the pooling optimiser stopped far from the REML optimum | 3 of 3 |
| Fits dosresmeta refuses (too few doses per study) | 14 returned without warning | 0: refused, with the studies named |
| Full grid: 724 model × covariance × approach × method combinations | — | all 724 agree: 576 fits within tolerance, and the same 148 refusals |

Tolerances follow allmeta's own parity test (`hub/shared/tests/_dr_parity_check.mjs`, mirrored in `analysis/make_outputs.py`):

- Coefficients within 1e-6 standard errors, and Wald statistics and predictions within 1e-5. These apply to fixed effect, method of moments and one-stage fits.
- Coefficients within 1e-3 standard errors and log-likelihoods within 1e-6 for two-stage REML and ML. The observed maxima are 9e-5 SE and 8e-8.

dosresmeta's one-stage optimiser stops at 100 Nelder–Mead evaluations. In 120 of its fits it had not converged; the app reproduces those estimates and warns, as dosresmeta does.

## Layout

| Path | Contents |
|---|---|
| `app/` | Corrected app, byte-identical to allmeta (see `app/shared/dose-response.js` header) |
| `app_before/shared/` | Engine first validated, allmeta `ac5435b`, kept for the before/after comparison |
| `bench/build_corpus.R` | Builds the 17-dataset corpus from dosresmeta |
| `bench/reference_dosresmeta.R` | dosresmeta reference fits over the option grid |
| `bench/run_engine.mjs` | Runs both JavaScript engines on the same data |
| `analysis/make_outputs.py` | Tables, figures, statistics, PASS/FAIL |
| `analysis/compare_runs.py` | Cross-platform comparison |
| `expected/` | Every number as printed in the paper |
| `docs/` | Paper, `numbers.json`, Figure 1 screenshots and their capture script |

## Outputs and how they map to the paper

`python reproduce.py` writes to `outputs/full/`:

| File | Paper |
|---|---|
| `docs/screenshots/step1.png` … `step6.png` | Figure 1: using the app |
| `table1_found_and_fixed.csv` | Table 1: defects found, and agreement before and after correction |
| `table2_parity_by_configuration.csv` | Table 2: agreement by model, covariance, approach and method |
| `table3_parity_all_fits.csv`, `table4_before_by_dataset.csv` | Every fit, and the original engine by dataset (extended data) |
| `figure2_before_after.png` (+ `.csv`) | Figure 2: before and after, by dataset |
| `figure3_coffee_mortality.png` (+ `.csv`) | Figure 3: worked example (coffee and mortality) |
| `figure4_parity_grid.png` (+ `.csv`) | Figure 4: all fits, corrected app versus dosresmeta |
| `visual_abstract.png` | Visual abstract |
| `stats.json` | Every number quoted in the text |
| `reproduction_report.md` | Expected versus reproduced, PASS/FAIL per number |

## Environment and determinism

- **R 4.6.0.** The image is `rocker/r-ver:4.6.0`. dosresmeta 2.2.0, rms 8.1-1, mvmeta 1.0.3, mixmeta 1.2.2 and their dependencies come from the Posit Package Manager snapshot of 2026-10-01.
- **Node 24.15.0** (`.nvmrc`) runs the app's JavaScript engines. There are no npm dependencies.
- **Python** builds the tables and figures (numpy and matplotlib, pinned in `requirements.txt`).
- **Docker is the canonical environment.** CI runs the full validation on every push on Linux, Windows, macOS and Docker. `analysis/compare_runs.py` then requires the corpus and the engines' output to be bit-identical across the x86-64 runs. macOS on ARM is reported but not required to match: V8 there can differ in the last bit.
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

See `CITATION.cff`. The archived release DOI will be added after the first Zenodo release.

## Licence

MIT, the same as allmeta.
