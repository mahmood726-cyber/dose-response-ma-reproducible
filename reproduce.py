#!/usr/bin/env python3
"""Re-run the dose-response validation and check every number in the paper.

  python reproduce.py            # full run: all 17 dosresmeta datasets (about 1 minute)
  python reproduce.py --quick    # 3 datasets, a few seconds

Steps: check tool versions -> build the corpus from the R package dosresmeta -> dosresmeta
reference fits (R) -> the app's shipped engine on the same data (Node) -> tables, figures,
statistics -> expected vs reproduced, PASS/FAIL per number. Exit code 0 only if all pass.
"""
import argparse

import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
R_PINS = {"dosresmeta": "2.2.0", "rms": "8.1.1", "mvmeta": "1.0.3"}
QUICK = ["alcohol_cvd", "alcohol_crc", "coffee_mort"]


def sh(cmd, **kw):
    p = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, **kw)
    if p.returncode:
        sys.exit(f"command failed ({p.returncode}): {' '.join(map(str, cmd))}\n{p.stdout}\n{p.stderr}")
    return p.stdout


def check_versions(strict):
    problems = []
    rscript = shutil.which("Rscript") or sys.exit("Rscript not found on PATH (R 4.6.0 needed; see README or use Docker)")
    node = shutil.which("node") or sys.exit("node not found on PATH (Node 24.15.0 needed)")
    rv = sh([rscript, "-e", "cat(as.character(getRversion()), sapply(c('dosresmeta','rms','mvmeta'), function(p) tryCatch(as.character(packageVersion(p)), error=function(e) 'missing')))"]).split()
    nv = sh([node, "--version"]).strip().lstrip("v")
    if rv[0] != "4.6.0": problems.append(f"R {rv[0]} (pinned 4.6.0)")
    for (p, want), got in zip(R_PINS.items(), rv[1:]):
        if got == "missing": sys.exit(f"R package {p} missing: run  Rscript bench/install_r_packages.R")
        if got != want: problems.append(f"{p} {got} (pinned {want})")
    want_node = (ROOT / ".nvmrc").read_text().strip()
    if nv != want_node: problems.append(f"node {nv} (pinned {want_node})")
    from importlib.metadata import version
    for line in (ROOT / "requirements.txt").read_text().splitlines():
        line = line.split("#")[0].split(";")[0].strip()
        if "==" in line:
            k, v = line.split("==", 1)
            try:
                if version(k) != v: problems.append(f"{k} {version(k)} (pinned {v})")
            except Exception:
                sys.exit(f"python package {k} missing: run  python -m pip install -r requirements.txt")
    print(f"environment: R {rv[0]} (dosresmeta {rv[1]}, rms {rv[2]}, mvmeta {rv[3]}), Node {nv}, Python {platform.python_version()}, {platform.system()} {platform.machine()}")
    if problems:
        msg = "version mismatch: " + "; ".join(problems)
        if strict: sys.exit(msg + "\n(use --allow-version-mismatch to run anyway)")
        print("WARNING: " + msg)
    return rscript, node


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--allow-version-mismatch", action="store_true")
    a = ap.parse_args()
    mode = "quick" if a.quick else "full"
    res, out = ROOT / "results" / mode, ROOT / "outputs" / mode
    t0 = time.time()
    rscript, node = check_versions(strict=not a.allow_version_mismatch)
    if res.exists(): shutil.rmtree(res)
    res.mkdir(parents=True)
    env = {**os.environ, "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"}
    print(sh([rscript, "bench/build_corpus.R", str(res / "corpus.csv")], env=env).strip().splitlines()[0])
    if a.quick:
        lines = (res / "corpus.csv").read_text(encoding="utf-8").splitlines(keepends=True)
        keep = [lines[0]] + [l for l in lines[1:] if l.split(",", 1)[0].strip('"') in QUICK]
        (res / "corpus.csv").write_text("".join(keep), encoding="utf-8", newline="")
        print("quick mode: datasets", ", ".join(QUICK))
    print(sh([rscript, "bench/reference_dosresmeta.R", str(res / "corpus.csv"), str(res / "dosresmeta.jsonl")], env=env).strip().splitlines()[-1])
    print(sh([node, "bench/run_engine.mjs", str(res / "corpus.csv"), str(res / "dosresmeta.jsonl"), str(res / "engine.jsonl")], env=env).strip())
    expected = "expected/quick_values.json" if a.quick else "expected/paper_values.json"
    rc = subprocess.run([sys.executable, "analysis/make_outputs.py", "--results", str(res), "--outputs", str(out), "--expected", expected], cwd=ROOT).returncode
    print(f"total time {time.time() - t0:.0f} s; outputs in {out.relative_to(ROOT)}")
    sys.exit(rc)


if __name__ == "__main__":
    main()
