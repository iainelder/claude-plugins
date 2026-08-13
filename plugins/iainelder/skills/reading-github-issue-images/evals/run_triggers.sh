#!/usr/bin/env bash
# Run every phrasing in trigger_eval.json and record whether the skill loaded.
#
#     ./run_triggers.sh <output-dir>
#     python3 grade_triggers.py <output-dir>
#
# Bash, Edit, Write and the Agent tool are removed. Only skill selection is
# being measured, and several negative phrasings ("Open a new issue with this
# screenshot attached") would otherwise act on a real repository.
set -euo pipefail

OUT="${1:?usage: run_triggers.sh <output-dir>}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN="$(cd "$HERE/../../.." && pwd)"

mkdir -p "$OUT" "$OUT/cwd"
cd "$OUT/cwd"

count=$(python3 -c "import json;print(len(json.load(open('$HERE/trigger_eval.json'))))")
for i in $(seq 0 $((count - 1))); do
  query=$(python3 -c "import json;print(json.load(open('$HERE/trigger_eval.json'))[$i]['query'])")
  timeout 300 claude -p "$query" --plugin-dir "$PLUGIN" \
    --output-format stream-json --verbose \
    --disallowed-tools Bash Edit Write NotebookEdit Agent Task \
    > "$OUT/trigger$i.jsonl" 2>"$OUT/trigger$i.err" &
  # Four at a time keeps the wall time down without flooding the API.
  if (( (i + 1) % 4 == 0 )); then wait; fi
done
wait
echo "ran $count phrasings into $OUT"
