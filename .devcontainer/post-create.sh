#!/usr/bin/env bash
# Runs once when the Codespace (or local dev container) is created: the pinned environment is already
# installed by the Dockerfile, so this goes straight to the quick reproduction and prints the result.
set -uo pipefail
cd "$(dirname "$0")/.."
echo
echo "== dose-response-ma-reproducible: quick reproduction (3 datasets, about a minute) =="
python reproduce.py --quick
rc=$?
echo
if [ $rc -eq 0 ]; then echo "QUICK RUN: ALL PASS  (report: outputs/quick/reproduction_report.md)"; else echo "QUICK RUN FAILED (exit $rc); see the output above and outputs/quick/reproduction_report.md"; fi
cat <<'EOF'

Next:
  python reproduce.py            # full run: every number in the paper (a few minutes)
  results land in outputs/full/  (reproduction_report.md = expected vs reproduced, PASS/FAIL per number)
  the app itself: open app/dose-response-ma/index.html (or the live app linked in README.md)
EOF
exit $rc
