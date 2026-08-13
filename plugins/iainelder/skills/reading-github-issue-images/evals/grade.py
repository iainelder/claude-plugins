"""Grade the evaluations in cases.json.

Run each case in a fresh Claude Code process, then grade the transcripts:

    cd /tmp/some-empty-dir
    claude -p '<query from the json>' \
        --plugin-dir /home/isme/Repos/claude-plugins/plugins/iainelder \
        --output-format stream-json --verbose \
        --allowedTools Bash Read Skill Glob Grep \
        --disallowed-tools Edit Write NotebookEdit > /tmp/evals/case1.jsonl
    python3 grade.py /tmp/evals

A fresh process is necessary, and it must start outside any repository. Started
inside a checkout, Claude can reach the issue through repository context and
never needs the skill. A subagent is worse: a subagent receives its skills
preloaded, so it cannot measure whether the description made Claude choose the
skill.

Behavior is graded from the tool calls, and content from the final answer. Both
matter. A case that describes the right image but never invokes the skill is
correct by luck, and that is the failure this file exists to catch.
"""
import json
import pathlib
import re
import sys

SKILL = "reading-github-issue-images"

# The two attachments on the fixture issue: body, then comment.
BODY_ASSET = "9304d376"
COMMENT_ASSET = "bfa2b2d0"


def transcript(path: pathlib.Path):
    """Return the tool calls and the final answer from one stream-json file."""
    tools, final = [], ""
    for line in path.read_text().splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        message = event.get("message")
        if not isinstance(message, dict):
            message = {}
        content = message.get("content")
        if not isinstance(content, list):
            content = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                arg = block.get("input") or {}
                tools.append((block["name"], str(arg.get("command") or arg.get("skill")
                                                or arg.get("file_path") or "")))
        if event.get("type") == "result":
            final = event.get("result") or ""
    return tools, final


def grade(case_id: int, tools: list, final: str) -> dict:
    commands = " ".join(arg for _, arg in tools)
    # Match the asset UUID anywhere in the command. A run may loop over the
    # UUIDs in a shell variable, which puts them nowhere near "assets/".
    downloads = re.findall(
        r"\b([0-9a-f]{8})-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", commands)
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
        checks["described no image content"] = not re.search(
            r"the image shows|screenshot shows|depicts|it shows a", final, re.I)
        # Bonus, reported but not required: the durable way to detect the failure.
        checks_optional["verified with file"] = bool(
            re.search(r"\bfile\s+\S+\.(png|jpg|jpeg|gif|webp)", commands))
    return checks


checks_optional: dict = {}


def names_of(tools: list) -> list:
    return [name for name, _ in tools]


def main() -> None:
    here = pathlib.Path(__file__).parent
    spec = json.loads((here / "cases.json").read_text())
    results = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")

    failed = 0
    for case in spec["cases"]:
        checks_optional.clear()
        path = results / f"case{case['id']}.jsonl"
        if not path.exists():
            print(f"case {case['id']}: NOT RUN ({path} is missing)\n")
            failed += 1
            continue
        tools, final = transcript(path)
        checks = grade(case["id"], tools, final)
        passed = all(checks.values())
        failed += not passed
        print(f"case {case['id']}: {'PASS' if passed else 'FAIL'}  ({case['name']})")
        for label, ok in checks.items():
            print(f"    {'ok ' if ok else 'NO '} {label}")
        for label, ok in checks_optional.items():
            print(f"    {'ok ' if ok else '-- '} {label} (bonus)")
        if any(n == "Read" and "SKILL.md" in a for n, a in tools):
            print("    note: read SKILL.md as a file, which is not discovery")
        print(f"    tools: {names_of(tools)}\n")

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
