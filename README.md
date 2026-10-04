# dose-response-ma-reproducible

[![reproduce](https://github.com/mahmood726-cyber/dose-response-ma-reproducible/actions/workflows/reproduce.yml/badge.svg)](https://github.com/mahmood726-cyber/dose-response-ma-reproducible/actions/workflows/reproduce.yml)
[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/mahmood726-cyber/dose-response-ma-reproducible?quickstart=1)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

The [allmeta](https://github.com/mahmood726-cyber/allmeta) **dose-response app** runs dose-response
meta-analysis offline in the browser. It uses the two-stage Greenland–Longnecker method with a
linear trend or restricted cubic splines (3 or 4 knots), pooled by REML.

This repository holds a frozen copy of the app (allmeta commit `ac5435b`, byte-identical to the
[live version](https://mahmood726-cyber.github.io/allmeta/dose-response-ma/)). It re-runs the
app's own engine, unchanged, against the R package **dosresmeta** on every multi-study binary
dataset shipped with dosresmeta. It then checks every number in the accompanying
F1000Research article.

## Quick start

```bash
git clone https://github.com/mahmood726-cyber/dose-response-ma-reproducible && cd dose-response-ma-reproducible
docker build -t drma . && docker run --rm -v "$PWD/outputs:/work/outputs" drma        # canonical
```

Without Docker you need R 4.6.0, Node 24.15.0 and Python 3.12 or 3.13. Run
`Rscript bench/install_r_packages.R`, then `python -m pip install -r requirements.txt`, then
`python reproduce.py` (or `--quick`). `make setup` and `make reproduce` do the same.

**To use the app**, open `app/dose-response-ma/index.html` in a browser.

## What it shows

| | Result |
|---|---|
| 3-knot spline vs dosresmeta | agrees on 14 of 15 datasets (within the app's stated 1e-5); the 15th differs by 1.3e-5 in one fitted log RR |
| Linear trend, **as shipped** | agrees on only 4 of 16 datasets: the app uses raw doses, whereas dosresmeta measures each study's doses relative to its reference level |
| Linear trend, doses entered relative to each study's reference | agrees on 16 of 16 (≤ 2e-7) |
| 4-knot spline | disagrees on all 3 datasets dosresmeta can fit |
| Data dosresmeta refuses (studies with too few dose levels) | the app returns estimates without warning (14 fits; coefficients up to about 3 × 10¹²) |

These are the *shipped* app's results, documented on purpose. Fixes are tracked in allmeta.
**Workaround for the linear model:** enter each study's doses relative to its own reference
dose (reference dose = 0).

## Outputs and how they map to the paper

`python reproduce.py` writes to `outputs/full/`:

| File | Paper |
|---|---|
| `docs/screenshots/step1.png` … | Figure 1: using the app |
| `table1_linear.csv` | Table 1: linear trend, app vs dosresmeta, by dataset |
| `table2_spline.csv`, `table3_spline_refused.csv` | Table 2: spline fits; fits dosresmeta refuses |
| `figure2_agreement.png` (+ `.csv`) | Figure 2: agreement with dosresmeta, by dataset |
| `figure3_coffee_mortality.png` (+ `.csv`) | Figure 3: worked example (coffee and mortality) |
| `figure4_refused_fits.png` (+ `.csv`) | Figure 4: fits dosresmeta refuses but the app returns |
| `visual_abstract.png` | Visual abstract |
| `stats.json` | Every number quoted in the text |
| `reproduction_report.md` | Expected vs reproduced, PASS/FAIL per number |

`expected/paper_values.json` holds the numbers as printed in the paper, recorded from the
canonical Docker run.

## Environment and determinism

- **R 4.6.0.** The Docker image is `rocker/r-ver:4.6.0`. `dosresmeta` 2.2.0, `rms` 8.1-1, `mvmeta` 1.0.3 and all their dependencies are installed from the Posit Package Manager snapshot of 2026-10-01 (`bench/install_r_packages.R`).
- **Node 24.15.0** (`.nvmrc`) runs the app's JavaScript engine. It uses no npm dependencies.
- **Python** builds the tables and figures, using `numpy` and `matplotlib` pinned in `requirements.txt`.
- **The Docker image is the canonical environment.** CI runs the full validation on every push on Linux, Windows, macOS and Docker. `analysis/compare_runs.py` then compares the four runs' raw results value by value.

Run time: the full validation takes about 15 s of computation. Installing the R packages takes most of the build time.

## Data

The data are not redistributed here. `bench/build_corpus.R` builds them at run time from the
datasets shipped with the R package dosresmeta (GPL-2 | GPL-3), which cites each original
source. Datasets used: `alcohol_crc`, `alcohol_cvd`, `alcohol_esoph`, `alcohol_lc`, `bmi_rc`,
`coffee_cancer`, `coffee_cvd`, `coffee_mort`, `coffee_mort_add`, `coffee_stroke`, `fish_ra`,
`milk_mort`, `milk_ov`, `oc_breast`, `process_bc`, `red_bc` and `sim_os`. Two kinds of data are left out:
- `ari`: a continuous outcome, which the app does not support.
- The single-study examples (`cc_ex`, `ci_ex`, `ir_ex`).

Studies without case and total counts are excluded, because the covariance reconstruction needs them.

## Cite

See `CITATION.cff`. The archived release DOI will be added after the first Zenodo release.

## Licence

MIT, the same as allmeta.
