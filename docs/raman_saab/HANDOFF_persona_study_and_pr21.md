# Handoff — persona study run 2, and PR #21

Written 2026-08-21 at the end of a remote session, so the work can be picked up on a local
machine. Everything below is **committed and pushed**; nothing of value lives only in the
container.

- **Branch**: `claude/empirical-engine-lag-vrxsau`
- **Head**: `0732a21` (local tree was clean and identical to the remote)
- **PR**: [#21](https://github.com/Slllyio/astro/pull/21), base `main-aug`, marked ready for review

```bash
git fetch origin claude/empirical-engine-lag-vrxsau
git checkout claude/empirical-engine-lag-vrxsau     # or: git reset --hard origin/<branch>
```

---

## The one thing still open

**PR #21 is not merged.** CI (`pytest (Python 3.12)`) was still running on `0732a21` when the
session ended — it had not reported a result either way, so *do not assume it is green*.

```bash
# check, then merge if green
gh pr checks 21
gh pr merge 21 --merge          # or via the web UI
```

If it is red, the failure is most likely environmental rather than a regression: the same
suite runs clean locally at **5,527 passed, 0 failed** (`PYTHONPATH=.:tests python3.12 -m
pytest tests/raman_saab tests/test_feedback_instrument_endpoint.py -q`). Diagnose before
re-pushing.

Two non-blocking notes on the PR, both already explained in a comment there:

- CodeRabbit's **merge-risk banner still reads "High"** — it is stamped `up to 78aad` and
  names exactly the four issues fixed after that commit. It has not recomputed, because auto
  reviews are disabled on any base branch other than the default.
- Its **docstring-coverage check fails at 68.95%** against an 80% threshold. This was measured
  rather than guessed: of the 27 public undocumented functions this PR *adds*, 26 are nested
  local closures inside already-documented functions plus three argparse `main` dispatchers
  whose modules carry the mandated `Usage:` block; the other 27 in scope are pre-existing in
  files the PR happens to touch. One genuine module-level helper (`sha256_of`) was documented.
  The rest were deliberately left — writing them moves a number without helping a reader.

---

## The persona study is finished and re-derivable

Run 2, engine `baed614`. **Both arms collected, 46 answer files committed** under
`tests/fixtures/persona_study/` — this is the fix for what run 1 lost, and it is why every
figure can now be reproduced.

```bash
python -m tools.raman_saab.persona_study verify        # hashes both arms, names stray tokens
python -m tools.raman_saab.persona_study score --permutations 5000
# acceptance test: this reproduces tests/fixtures/persona_study/results.json exactly
```

Headline numbers (full write-up: `docs/raman_saab/PERSONA_STUDY_RESULTS.md`):

| arm | forced choice | cross-chart contrast |
|---|---|---|
| coin flip (sham gate) | 132/267 = 0.494 | +0.0339 ← **the floor; read contrasts against this, never against zero** |
| **blind** | **134/267 = 0.502**, p = 1.00 | +0.0166, p = .30 — *below* the floor |
| **contaminated** (reading read first) | **142/267 = 0.532** | **+0.0704, p = .010** |

Paired (McNemar, same personas and items): 8 blind-only vs **18 contaminated-only** hits,
p = .076. Confidence gap flips from **−0.140 blind to +0.103 contaminated**, and the confident
pool grows 135 → 148.

The blind arm is null and replicates run 1. The contaminated arm is elevated on all three of
its measures and significant on one — the curation asymmetry reproduced inside our own
harness. It is reported as **directionally unanimous but short of significance on three of the
four measures**; at n = 23 this cannot size the effect, only its direction.

`PERSONA_STUDY_PREREG.md` Deviation 5 records the one file re-encoded (formatting only,
content untouched, originals kept verbatim under `raw_events_as_given`) and the one stray
token deliberately left standing. The rule it sets: **formatting may be normalised, content
may not.**

---

## What this branch changed beyond the study

All of it is tested, and the **golden ratchet is byte-identical throughout —
exact 259/293 · within-1 283/293 · real-errors 10**. Nothing here touches the verdict path.

**Three readings asserted more than they knew** (each looked like a measurement):

- `career_frames` named a "strongest" centre on charts with no strength measure at all — every
  centre ties at 0.0, `max` returns whichever was appended first, and the reading printed
  "Lagna carries 0.0 rupas …, the highest of the three centres".
- `marriage_timing`, the same bug for "the strongest of these lords".
- `simple_summary` labelled a house **"mixed" when nothing was read either way**, which the
  renderer prints as "reads both ways at once". Silence is not a contradiction.

**Data integrity:** a free-text-only row skipped instrument validation and was stored under a
client-chosen qid; `medical_astrology`'s six HPA-29 anchors were enumerated nowhere, so the
source lock could not see the chapter at all; `_body_bytes` treated any line starting `---` as
a front-matter delimiter.

**The lock was regenerated, and here is why that was safe rather than convenient:** the
delimiter fix moves all 25 cited bodies by exactly one byte, and `old_body == b"\n" +
new_body` holds 25/25 — the leading newline the old parser left attached, nothing else.
`line_count` is unchanged. No corpus text moved and no citation shifted. HPA-29 is genuinely
new coverage, taking the lock 25 → 26 entries.

**Six tests could not fail**, three of them badly: the template contract truncated `HTJAH-I`
to `HTJAH` and skipped 12 of 18 citations; four verdict-authority guards pointed at
`judges/total.py` and `judges/conditions.py`, neither of which exists; the Kemadruma
extended-branch test never called the function it guards. Plus one time bomb —
`test_detailed_report` pinned `**Saturn AD**` inside a wall-clock-anchored window, so it would
have failed on a future date with no code change.

---

## Regenerating what is not committed

The scorecard HTML is derived and was written to a scratch directory, not the repo:

```bash
python -m tools.raman_saab.persona_study score \
  --html data/persona_study/scorecard.html --permutations 5000
```

`roster.json`, `payloads/`, `verdicts/`, `questions/`, `readings/` and `results.json` **are**
committed under `tests/fixtures/persona_study/`. The answers are primary data and can never be
rebuilt — that is the whole lesson of run 1 — so treat that directory as irreplaceable.
