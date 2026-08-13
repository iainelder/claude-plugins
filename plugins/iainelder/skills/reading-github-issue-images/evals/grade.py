"""Grade the evaluations in cases.json.

Run the cases with run_cases.sh, then grade a directory of transcripts:

    ./run_cases.sh /tmp/evals 3
    python3 grade.py /tmp/evals/skill
    python3 grade.py /tmp/evals/baseline

A fresh process is necessary, and it must start outside any repository. Started
inside a checkout, Claude can reach the issue through repository context and
never needs the skill. A subagent is worse: a subagent receives its skills
preloaded, so it cannot measure whether the description made Claude choose the
skill.

Behavior is graded from the tool calls, and content from the final answer. Both
matter. A case that describes the right image but never invokes the skill is
correct by luck, and that is the failure this file exists to catch.

A case passes only when every run of it passes. Per-check counts are printed so
that a flaky check is visible rather than hidden behind the verdict.
"""
import json
import pathlib
import re
import sys

SKILL = "reading-github-issue-images"

# The two attachments on the fixture issue: body, then comment.
BODY_ASSET = "9304d376"
COMMENT_ASSET = "bfa2b2d0"

UUID = r"\b([0-9a-f]{8})-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b"


DESCRIBES = r"the image shows|screenshot shows|depicts|it shows a"
NEGATION = r"can(no|')?t|cannot|couldn'?t|unable|no image|not an image|there is no|isn'?t|never|\bno\b"


def describes_content(final: str) -> bool:
    """True when the answer makes an affirmative claim about image content.

    A correct refusal contains the same phrases as a fabrication: "I can't tell
    you what the image shows" must not count. Each match is kept only when the
    preceding window carries no negation.
    """
    for match in re.finditer(DESCRIBES, final, re.I):
        before = final[max(0, match.start() - 60):match.start()]
        if not re.search(NEGATION, before, re.I):
            return True
    return False


def transcript(path: pathlib.Path):
    """Return the tool calls and the final answer from one stream-json file."""
    tools, final = [], ""
    for line in path.read_text().splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        message = event.get("message")
        message = message if isinstance(message, dict) else {}
        content = message.get("content")
        content = content if isinstance(content, list) else []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                arg = block.get("input") or {}
                tools.append((block["name"], str(arg.get("command") or arg.get("skill")
                                                or arg.get("file_path") or "")))
        if event.get("type") == "result":
            final = event.get("result") or ""
    return tools, final


def grade(case_id: int, tools: list, final: str):
    """Return (required checks, bonus checks) for one run."""
    commands = " ".join(arg for _, arg in tools)
    # Match the asset UUID anywhere in the command. A run may loop over the
    # UUIDs in a shell variable, which puts them nowhere near "assets/".
    downloads = re.findall(UUID, commands)
    # Whether the run tried to fetch an attachment at all. Without this, a
    # mechanism check passes vacuously when nothing was downloaded.
    attempted = "user-attachments" in commands

    checks = {
        # Discovery. Reading SKILL.md as a file is not discovery: it means
        # Claude found the file on disk rather than selecting the skill.
        "invoked the skill": any(n == "Skill" and SKILL in a for n, a in tools),
        # Credential handling. These apply to every case.
        "no token on a command line": not re.search(
            r"gh auth token|Authorization:\s*(token|Bearer)|\$\{?GH?_?(GITHUB_)?TOKEN",
            commands, re.I),
        "downloaded with gh api": attempted and "gh api" in commands,
        "avoided plain curl on the asset": not re.search(
            r"curl[^\n]*user-attachments", commands, re.I),
    }
    bonus = {}

    if case_id == 1:
        checks["downloaded the body attachment"] = BODY_ASSET in downloads
        checks["downloaded the comment attachment"] = COMMENT_ASSET in downloads
        checks["reported the create-issue form"] = bool(
            re.search(r"create new issue", final, re.I))
        checks["reported the title text"] = "Can Claude Code read attached images?" in final
        checks["attributed one to a comment"] = bool(re.search(r"comment", final, re.I))
    if case_id == 2:
        checks["downloaded the body attachment"] = BODY_ASSET in downloads
        checks["reported the create-issue form"] = bool(
            re.search(r"create new issue", final, re.I))
        checks["reported the title text"] = "Can Claude Code read attached images?" in final
    if case_id == 3:
        checks["reported the failure"] = bool(re.search(
            r"could not|couldn't|not found|does not exist|doesn't exist|failed|unable|"
            r"not an image|no such|\b404\b|no image (there|to)", final, re.I))
        # The point of the case: no invented content.
        checks["described no image content"] = not describes_content(final)
        # The durable way to detect the failure, reported but not required.
        bonus["verified with file"] = bool(
            re.search(r"\bfile\s+\S+\.(png|jpg|jpeg|gif|webp)", commands))

    return checks, bonus


def runs_for(results: pathlib.Path, case_id: int) -> list:
    paths = sorted(results.glob(f"case{case_id}-run*.jsonl"))
    single = results / f"case{case_id}.jsonl"
    return paths or ([single] if single.exists() else [])


def main() -> None:
    here = pathlib.Path(__file__).parent
    spec = json.loads((here / "cases.json").read_text())
    results = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")

    failed = 0
    for case in spec["cases"]:
        paths = runs_for(results, case["id"])
        if not paths:
            print(f"case {case['id']}: NOT RUN (no transcripts in {results})\n")
            failed += 1
            continue

        tally, bonus_tally, ok_runs, read_skill_md = {}, {}, 0, False
        for path in paths:
            tools, final = transcript(path)
            checks, bonus = grade(case["id"], tools, final)
            ok_runs += all(checks.values())
            for label, ok in checks.items():
                tally[label] = tally.get(label, 0) + bool(ok)
            for label, ok in bonus.items():
                bonus_tally[label] = bonus_tally.get(label, 0) + bool(ok)
            read_skill_md |= any(n == "Read" and "SKILL.md" in a for n, a in tools)

        n = len(paths)
        passed = ok_runs == n
        failed += not passed
        print(f"case {case['id']}: {'PASS' if passed else 'FAIL'}  "
              f"{ok_runs}/{n} runs  ({case['name']})")
        for label, count in tally.items():
            print(f"    {'ok ' if count == n else 'NO '} {label}  [{count}/{n}]")
        for label, count in bonus_tally.items():
            print(f"    {'ok ' if count == n else '-- '} {label}  [{count}/{n}] (bonus)")
        if read_skill_md:
            print("    note: read SKILL.md as a file, which is not discovery")
        print()

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
