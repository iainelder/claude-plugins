"""Report which phrasings in trigger_eval.json loaded the skill.

    ./run_triggers.sh /tmp/triggers
    python3 grade_triggers.py /tmp/triggers

A false negative is a skill that never fires, which is silent rather than
broken. A false positive is worse over time: it loads the skill, and its
tokens, into sessions that had no use for it.
"""
import json
import pathlib
import sys

from grade import SKILL, transcript


def main() -> None:
    here = pathlib.Path(__file__).parent
    cases = json.loads((here / "trigger_eval.json").read_text())
    results = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")

    wrong = []
    for i, case in enumerate(cases):
        path = results / f"trigger{i}.jsonl"
        if not path.exists():
            print(f"[{i:2d}] NOT RUN  {case['query'][:64]}")
            wrong.append(i)
            continue
        tools, _ = transcript(path)
        fired = any(name == "Skill" and SKILL in arg for name, arg in tools)
        want = case["should_trigger"]
        ok = fired == want
        if not ok:
            wrong.append(i)
        label = "fired" if fired else "quiet"
        kind = "" if ok else ("  <- FALSE POSITIVE" if fired else "  <- MISSED")
        print(f"[{i:2d}] {'ok ' if ok else 'NO '} want={'fire ' if want else 'quiet'} "
              f"got={label}{kind}\n         {case['query'][:88]}")

    total = len(cases)
    print(f"\n{total - len(wrong)}/{total} phrasings behaved as expected")
    sys.exit(1 if wrong else 0)


if __name__ == "__main__":
    main()
