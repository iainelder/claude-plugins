#!/usr/bin/env bash
# Run the cases in cases.json, with and without the plugin.
#
#     ./run_cases.sh <output-dir> [runs]
#
# Writes <output-dir>/skill/caseN-runM.jsonl and <output-dir>/baseline/... .
# Grade with:  python3 grade.py <output-dir>/skill
#
# Each run starts in an empty directory. Started inside a checkout, Claude can
# reach the issue through repository context and never needs the skill.
set -euo pipefail

OUT="${1:?usage: run_cases.sh <output-dir> [runs]}"
RUNS="${2:-3}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN="$(cd "$HERE/../../.." && pwd)"

mkdir -p "$OUT/skill" "$OUT/baseline" "$OUT/cwd"
python3 -c "
import json
for c in json.load(open('$HERE/cases.json'))['cases']:
    print(f\"{c['id']}\t{c['query']}\")
" > "$OUT/queries.tsv"

cd "$OUT/cwd"
for run in $(seq 1 "$RUNS"); do
  for arm in skill baseline; do
    [ "$arm" = skill ] && plugin=(--plugin-dir "$PLUGIN") || plugin=()
    while IFS=$'\t' read -r id query; do
      timeout 420 claude -p "$query" "${plugin[@]}" \
        --output-format stream-json --verbose \
        --allowedTools Bash Read Skill Glob Grep \
        --disallowed-tools Edit Write NotebookEdit \
        > "$OUT/$arm/case$id-run$run.jsonl" 2>"$OUT/$arm/case$id-run$run.err" &
    done < "$OUT/queries.tsv"
    wait
    echo "run $run, arm $arm: done"
  done
done
