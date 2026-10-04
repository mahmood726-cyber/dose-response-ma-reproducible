"""Compare full runs from different machines.

STRICT (must be bit-identical, compared with ==):
  corpus.csv (the input) and engine.jsonl (every number produced by the app's JavaScript engine).
REPORTED (not required to be identical):
  dosresmeta.jsonl, the R reference values. R uses the operating system's maths library and BLAS,
  so its last bits differ between Linux, Windows and macOS; the largest relative difference is
  printed for every platform. The printed paper numbers are checked separately, exactly, on every
  platform by reproduce.py.
  python analysis/compare_runs.py runA/results/full runB/results/full [...]
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


runs = sys.argv[1:]
if len(runs) < 2: sys.exit(__doc__)
strict_bad = 0
for other in runs[1:]:
    print(f"== {runs[0]}  vs  {other}")
    for f in ("corpus.csv", "engine.jsonl"):
        a, b = load(runs[0], f), load(other, f)
        keys = set(a) | set(b); diff = sorted(k for k in keys if a.get(k, "<missing>") != b.get(k, "<missing>"))
        print(f"   STRICT   {f}: {len(keys)} values, {len(diff)} differ")
        for k in diff[:10]: print(f"      {k}: {a.get(k)!r} != {b.get(k)!r}")
        strict_bad += len(diff)
    a, b = load(runs[0], "dosresmeta.jsonl"), load(other, "dosresmeta.jsonl")
    nd, worst = 0, (0.0, "")
    for k in set(a) | set(b):
        x, y = a.get(k), b.get(k)
        if x != y:
            nd += 1
            if isinstance(x, float) and isinstance(y, float):
                r = abs(x - y) / max(abs(x), abs(y), 1e-300)
                if r > worst[0]: worst = (r, k)
            else:
                worst = (float("inf"), k)
    print(f"   REPORTED dosresmeta.jsonl (R): {len(a)} values, {nd} differ in the last bits; largest relative difference {worst[0]:.1e} ({worst[1]})")
print("STRICT CHECK: corpus and app engine BIT-IDENTICAL across all runs" if strict_bad == 0 else "STRICT CHECK FAILED: corpus or app engine differ")
sys.exit(0 if strict_bad == 0 else 1)
