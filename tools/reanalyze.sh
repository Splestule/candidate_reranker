#!/usr/bin/env bash
# Rebuild every per-utterance table from the dumps, then the aggregates, tables and figure.
#
# aggregate.py only sums what analysis.py wrote, so a fix inside compose.py or analysis.py
# needs this, not `aggregate` alone. k_main is per model in run_config.json but the analysis
# CLI takes one number, so the jobs are driven one at a time with the right value.
#
#   bash tools/reanalyze.sh results/campaign-2026-09-20
set -euo pipefail
R="${1:?usage: bash tools/reanalyze.sh <campaign root>}"
export PYTHONPATH=src

python3 - "$R" > /tmp/campaign_jobs.txt <<'PY'
import json, pathlib, sys
root = pathlib.Path(sys.argv[1])
k_main = json.load(open(root / "run_config.json", encoding="utf-8")).get("k_main", {})
done = {p.stem for p in (root / "state" / "done").glob("*.json")}
for j in json.load(open(root / "plan.json", encoding="utf-8")):
    if j["id"] in done:
        print(j["id"], k_main.get(j["model"], 32))
PY

total=$(wc -l < /tmp/campaign_jobs.txt | tr -d ' ')
i=0; failed=0
while read -r job k; do
    i=$((i + 1))
    printf '\r  [%3d/%s] %-52s' "$i" "$total" "${job:0:52}"
    if ! python3 -m campaign.analysis --root "$R" --job "$job" --k_main "$k" --redo >/dev/null 2>&1; then
        printf '\n  FAILED: %s\n' "$job"; failed=$((failed + 1))
    fi
done < /tmp/campaign_jobs.txt
printf '\r  %d jobs analysed, %d failed%-40s\n' "$total" "$failed" ""

python3 -m campaign.aggregate --root "$R"
python3 tools/paper_tables.py "$R"
python3 tools/fig_cost_quality.py "$R"
echo "done"
