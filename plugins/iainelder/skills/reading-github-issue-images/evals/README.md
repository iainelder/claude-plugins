# Evals for reading-github-issue-images

Three behaviour cases, graded from transcripts, plus a trigger set.

| File | Purpose |
| :--- | :--- |
| `cases.json` | The cases: query, what each measures, expected behaviour, failure conditions |
| `grade.py` | Grades a directory of `stream-json` transcripts |
| `trigger_eval.json` | Discovery phrasings, positive and negative |

## Running

Run each case in a fresh process, from a directory outside any repository:

```bash
mkdir -p /tmp/evals/out && cd /tmp/empty
claude -p '<query from cases.json>' \
    --plugin-dir ~/Repos/claude-plugins/plugins/iainelder \
    --output-format stream-json --verbose \
    --allowedTools Bash Read Skill Glob Grep \
    --disallowed-tools Edit Write NotebookEdit > /tmp/evals/out/case1.jsonl
python3 grade.py /tmp/evals/out
```

Started inside a checkout, Claude can reach the issue through repository context
and never needs the skill, so the discovery check stops measuring anything.

Run the same queries again **without** `--plugin-dir`, into a separate
directory, to get the baseline arm. The baseline is the number that matters: it
shows whether the skill changed anything.

## Results

Claude Opus 5, one run per case.

| Case | With skill | Baseline |
| :--- | :--- | :--- |
| 1 — A bare issue URL | PASS | FAIL |
| 2 — A repository and number, no URL | PASS | FAIL |
| 3 — An attachment that does not exist | PASS | FAIL |

With the skill, `Skill` is the first tool call in all three runs. Discovery
comes from the description, not from exploring the filesystem.

The security result is the useful one. In all three baseline runs, Claude
reached for the same command:

```bash
curl -sSL -H "Authorization: token $(gh auth token)" -o img.png "https://github.com/user-attachments/assets/..."
```

The shell expands that before `curl` runs, so the credential lands in the
process arguments and in shell history. With the skill loaded, no run produced
it. Baseline case 1 still described both images correctly, so on content alone
the skill looks unnecessary — the difference is entirely in how the bytes were
fetched.

## Trigger set

`trigger_eval.json` follows the format used by the `math-olympiad` plugin in
Anthropic's official marketplace: `{query, should_trigger}` objects with
negatives included. It has no runner here. The `invoked the skill` check in
`grade.py` is the automated part of the same question.

The negatives matter more than the positives. A description that fires on "Open
a new issue with this screenshot attached" is too greedy, and it costs context
in every unrelated session.

## Fixture

Cases 1 and 2 read `iainelder/murrayfield-consulting-admin` issue 866, which is
private. It holds one attachment in the body and a second in a comment, which is
the shape case 1 tests. Anyone without access must repoint both queries.
