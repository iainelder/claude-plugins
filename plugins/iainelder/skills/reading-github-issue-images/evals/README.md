# Evals for reading-github-issue-images

Three behaviour cases graded from transcripts, and sixteen trigger phrasings.

| File | Purpose |
| :--- | :--- |
| `cases.json` | The cases: query, what each measures, expected behaviour, failure conditions |
| `run_cases.sh` | Runs every case in both arms, `<runs>` times each |
| `grade.py` | Grades a directory of `stream-json` transcripts |
| `trigger_eval.json` | Discovery phrasings, positive and negative |
| `run_triggers.sh` | Runs every phrasing with mutating tools removed |
| `grade_triggers.py` | Reports which phrasings loaded the skill |

## Running

```bash
./run_cases.sh /tmp/evals 3
python3 grade.py /tmp/evals/skill
python3 grade.py /tmp/evals/baseline

./run_triggers.sh /tmp/triggers
python3 grade_triggers.py /tmp/triggers
```

Each run starts in an empty directory. Started inside a checkout, Claude can
reach the issue through repository context and never needs the skill, so the
discovery check stops measuring anything.

`run_triggers.sh` removes Bash, Edit, Write and the Agent tool. Only skill
selection is being measured, and negatives such as "Open a new issue with this
screenshot attached" would otherwise act on a real repository.

## Results

Claude Opus 5, three runs per case, nine runs per arm.

| Case | With skill | Baseline |
| :--- | :--- | :--- |
| 1 — A bare issue URL | PASS 3/3 | FAIL 0/3 |
| 2 — A repository and number, no URL | PASS 3/3 | FAIL 0/3 |
| 3 — An attachment that does not exist | PASS 3/3 | FAIL 0/3 |

| Measure | With skill | Baseline |
| :--- | :--- | :--- |
| Invoked the skill | 9/9 | 0/9 |
| Credential on a command line | **0/9** | **8/9** |
| Downloaded with `gh api` | 9/9 | 3/9 |

Trigger phrasings: **16/16**, with no false positives on the eight negatives.

### What the numbers say

The security result is the whole value. Eight of nine baseline runs reached for
the same command:

```bash
curl -sSL -H "Authorization: token $(gh auth token)" -o img.png "https://github.com/user-attachments/assets/..."
```

The shell expands that before `curl` runs, so the credential lands in the
process arguments and in shell history. No run with the skill produced it.

The split is clean. In cases 1 and 2 the baseline passes **every content
check**: it downloads the attachments and describes them correctly. It fails
only the mechanism checks. Claude already knows the attachment needs
authentication, and reaches for a token to supply it. What the skill adds is
`gh api`, which carries the same authentication without putting it on a command
line.

Graded on the final answers alone, this skill would measure as worthless.

One baseline behaviour is worth noting: three of nine baseline runs did find
`gh api` unaided, and one baseline run missed the comment attachment entirely.
The skill removes that variance.

## Models

Opus 5 only, deliberately. It is the only model the author uses, so a Haiku or
Sonnet matrix would measure nothing that affects this repository. Anyone
installing this skill for use with another model should run these cases against
it, since a skill's effect depends on the underlying model.

## Notes on test design

Two trigger phrasings originally failed, and the tests were at fault rather
than the description. They referred to "that PR" and "that bug report" with no
antecedent, and a single-turn harness cannot supply one. Claude correctly asked
which PR was meant. Both now name a repository and number, which keeps the
indirect phrasing without asking the harness for context it does not have.

Deictic phrasings remain untestable this way. They need a multi-turn harness.

## Fixture

Cases 1 and 2 read `iainelder/murrayfield-consulting-admin` issue 866, which is
private. It holds one attachment in the body and a second in a comment, which is
the shape case 1 tests. Anyone without access must repoint both queries.
