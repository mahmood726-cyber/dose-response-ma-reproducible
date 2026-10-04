"""Compare full runs from different machines.

STRICT (must be bit-identical, compared with ==):
  corpus.csv (the input) and engine.jsonl (every number produced by the app's JavaScript engine).
REPORTED (not required to be identical):
  dosresmeta.jsonl, the R reference values. R uses the operating system's maths library and BLAS,
  so its last bits differ between Linux, Windows and macOS; the largest relative difference is
  printed for every platform. The printed paper numbers are checked separately, exactly, on every
  platform by reproduce.py.
Runs listed after --report-only (e.g. macOS on ARM) are compared and reported, but not required to be
bit-identical: V8 on arm64 can differ from x86-64 in the last bit of floating-point results, and the
app's iterative optimisers (BFGS, Nelder-Mead) can amplify such differences.
  python analysis/compare_runs.py canonical strict1 strict2 --report-only arm_run
"""
import json
import sys
from pathlib import Path


def flat(o, p=""):
    if isinstance(o, dict):
        r = {}
        for k, v in o.items(): r.update(flat(v, f"{p}.{k}" if p else k))
        return r
    if isinstance(o, list):
        r = {}
        for i, v in enumerate(o): r.update(flat(v, f"{p}[{i}]"))
        return r
    return {p: o}


def load(run, f):
    run = Path(run)
    if f == "corpus.csv":
        return {"corpus.csv": (run / f).read_bytes().replace(b"\r\n", b"\n")}
    vals = {}
    for line in (run / f).read_text(encoding="utf-8").splitlines():
        if line.strip():
            o = json.loads(line); vals.update({f"{o['dataset']}:{k}": v for k, v in flat(o).items()})
    return vals


args = sys.argv[1:]
report_only = set(args[args.index("--report-only") + 1:]) if "--report-only" in args else set()
runs = [a for a in args if a != "--report-only"]
if len(runs) < 2: sys.exit(__doc__)
strict_bad = 0
for other in runs[1:]:
    strict = other not in report_only
    print(f"== {runs[0]}  vs  {other}" + ("" if strict else "   [report only]"))
    for f in ("corpus.csv", "engine.jsonl"):
        a, b = load(runs[0], f), load(other, f)
        keys = set(a) | set(b); diff = sorted(k for k in keys if a.get(k, "<missing>") != b.get(k, "<missing>"))
        rel = [abs(a[k] - b[k]) / max(abs(a[k]), abs(b[k]), 1e-300) for k in diff if isinstance(a.get(k), float) and isinstance(b.get(k), float)]
        print(f"   {'STRICT  ' if strict else 'REPORTED'} {f}: {len(keys)} values, {len(diff)} differ" + (f"; largest relative difference {max(rel):.1e}" if rel else ""))
        if strict:
            for k in diff[:10]: print(f"      {k}: {a.get(k)!r} != {b.get(k)!r}")
            strict_bad += len(diff)
    a, b = load(runs[0], "dosresmeta.jsonl"), load(other, "dosresmeta.jsonl")
    nd, worst, wabs = 0, (0.0, ""), (0.0, "")
    for k in set(a) | set(b):
        x, y = a.get(k), b.get(k)
        if x != y:
            nd += 1
            if isinstance(x, float) and isinstance(y, float):
                r = abs(x - y) / max(abs(x), abs(y), 1e-300)
                if r > worst[0]: worst = (r, k)
                if abs(x - y) > wabs[0]: wabs = (abs(x - y), k)
            else:
                worst = (float("inf"), k)
    print(f"   REPORTED dosresmeta.jsonl (R): {len(a)} values, {nd} differ in the last bits; largest absolute difference {wabs[0]:.1e} ({wabs[1]}); largest relative {worst[0]:.1e} ({worst[1]}, a value near zero)")
print("STRICT CHECK: corpus and app engine BIT-IDENTICAL across all strict runs" if strict_bad == 0 else "STRICT CHECK FAILED: corpus or app engine differ")
sys.exit(0 if strict_bad == 0 else 1)
