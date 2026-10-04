"""Check that full runs from different machines are bit-identical.

Compares corpus.csv byte-for-byte and every value in dosresmeta.jsonl and engine.jsonl with ==.
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


def load(run):
    run = Path(run); vals = {"corpus.csv": (run / "corpus.csv").read_bytes().replace(b"\r\n", b"\n")}
    for f in ("dosresmeta.jsonl", "engine.jsonl"):
        for line in (run / f).read_text(encoding="utf-8").splitlines():
            if line.strip():
                o = json.loads(line); vals.update({f"{f}:{o['dataset']}:{k}": v for k, v in flat(o).items()})
    return vals


runs = sys.argv[1:]
if len(runs) < 2: sys.exit(__doc__)
ref, bad = load(runs[0]), 0
for other in runs[1:]:
    cur = load(other); keys = set(ref) | set(cur)
    diff = sorted(k for k in keys if ref.get(k, "<missing>") != cur.get(k, "<missing>"))
    print(f"{runs[0]} vs {other}: {len(keys)} values compared, {len(diff)} differ")
    for k in diff[:25]:
        a, b = ref.get(k, "<missing>"), cur.get(k, "<missing>")
        rel = abs(a - b) / max(abs(a), 1e-300) if isinstance(a, float) and isinstance(b, float) else ""
        print(f"   {k}: {a!r} != {b!r} {('rel ' + format(rel, '.1e')) if rel != '' else ''}")
    bad += len(diff)
print("BIT-IDENTICAL" if bad == 0 else "RUNS DIFFER")
sys.exit(0 if bad == 0 else 1)
