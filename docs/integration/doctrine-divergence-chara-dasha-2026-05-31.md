# Chara Dasha Doctrine Divergence — Post-Mortem

**Date:** 2026-05-31
**Surfaced by:** `app.integration.compare_chara_dasha` (integration-v0.1.0,
commit `0496264`)
**Evidence basis:** Direct source reading by Phase-1 workflow agents
(workflow `wf_aac10037-d2f`), corroborated by manual re-read.

---

## Executive summary

Track A (`app/reading/sequences/chara_dasha.py`) and Track B
(`app/core/chara_dasha.py`) both purport to implement Jaimini Chara Dasha
but produce fundamentally different results. **Track A is doctrinally
correct** (implements the Sanjay-Rath D-17 variant; 84-year cycle).
**Track B has a latent bug** (docstring claims K.N. Rao formulation but
the code collapses to a uniform 12-years-per-MD, 144-year cycle).

The bug is not intentional simplification. It arises from a pathological
interaction between two helper functions — neither incorrect on its own —
that combine to make every sign select itself as its own "lord-sign"
distance-1 and therefore receive 12 years.

This post-mortem documents the exact code paths, cites file:line evidence,
explains why Track B's docstring promises ≠ Track B's code behaviour, and
outlines three remediation options.

---

## The evidence

The integration comparator (Bangalore baseline: lagna Virgo / sign 6,
birth_jd 2448088.2708333) produced the following per-MD diff:

| MD # | Track A sign | Track A years | Track B sign | Track B years |
|---|---|---|---|---|
| 1 | 2 Taurus | 7 | 6 Virgo | 12 |
| 2 | 3 Gemini | 11 | 7 Libra | 12 |
| 3 | 4 Cancer | 3 | 8 Scorpio | 12 |
| 4 | 5 Leo | 7 | 9 Sagittarius | 12 |
| 5 | 6 Virgo | 11 | 10 Capricorn | 12 |
| 6 | 7 Libra | 3 | 11 Aquarius | 12 |
| 7 | 8 Scorpio | 7 | 12 Pisces | 12 |
| 8 | 9 Sagittarius | 11 | 1 Aries | 12 |
| 9 | 10 Capricorn | 3 | 2 Taurus | 12 |
| 10 | 11 Aquarius | 7 | 3 Gemini | 12 |
| 11 | 12 Pisces | 11 | 4 Cancer | 12 |
| 12 | 1 Aries | 3 | 5 Leo | 12 |
| **Total** | | **84 yr** | | **144 yr** |

Both engines advance ONE sign per MD — that is the one structural
commonality. Both START at `birth_jd`. Everything else diverges.

---

## Divergence axis 1 — Starting sign

### Track A (correct, Sanjay-Rath rule)

[`app/reading/sequences/chara_dasha.py:298-311`](../../app/reading/sequences/chara_dasha.py#L298-L311)

```python
def _starting_md_sign(asc_sign: int) -> int:
    """D-17 starting-sign rule.

    Movable lagna -> lagna sign itself.
    Fixed lagna   -> 5th from lagna.
    Dual lagna    -> 9th from lagna.
    """
    category = _sign_category(asc_sign)
    if category == "movable":
        return asc_sign
    if category == "fixed":
        return _sign_forward(asc_sign, 5)
    # dual
    return _sign_forward(asc_sign, 9)
```

For Virgo (dual sign 6) → 9th-from-Virgo = Taurus (sign 2). Matches observed MD #1.

**Doctrine reference:** Jaimini Sutras Adhyaya 2 + Sanjay-Rath *Crux of
Vedic Astrology* Ch. 16. Sentinel constant at
[`app/reading/sequences/chara_dasha.py:114-116`](../../app/reading/sequences/chara_dasha.py#L114-L116)
stamps every Finding with `doctrine=Jaimini Sutras Adhyaya 2 + Sanjay-Rath Crux Ch.16 — D-17`.

**Doctrine lockfile entry:** D-17 in [`docs/doctrine-decisions.md`](../doctrine-decisions.md).

The module docstring at lines 12-43 explicitly notes the *competing*
PVR Narasimha Rao variant exists and "differs in both starting-sign rule
and years-per-sign rule" — the project consciously locks to Sanjay-Rath.

### Track B (starts at lagna unconditionally)

[`app/core/chara_dasha.py:120-133`](../../app/core/chara_dasha.py#L120-L133)

```python
def chara_sequence(lagna_sign: int) -> tuple[tuple[int, int], ...]:
    direction = direction_for(lagna_sign)
    result: list[tuple[int, int]] = []
    current = lagna_sign
    for _ in range(12):
        years = period_for(current, direction)
        result.append((current, years))
        current = _step_sign(current, direction)
    return tuple(result)
```

`current = lagna_sign` then append on first iteration → first MD is
ALWAYS the lagna sign itself, regardless of category.

For Virgo lagna → first MD = sign 6 (Virgo).

**Docstring claim** (lines 8-23): "Iyer / K.N. Rao / Narasimha Rao
formulation." But under that formulation, only MOVABLE lagnas start at
the lagna sign — fixed/dual lagnas use 7th/9th rules (depending on
sub-variant). Track B's code uses the lagna unconditionally, which is
neither K.N. Rao nor Sanjay-Rath.

---

## Divergence axis 2 — Period length

### Track A (variable 3/7/11, total 84y)

[`app/reading/sequences/chara_dasha.py:314-328`](../../app/reading/sequences/chara_dasha.py#L314-L328)

```python
def _years_for_sign(sign: int) -> int:
    """D-17 years-per-sign rule.

    Years = 12 - (distance to co-lord), where co-lord offset is:
      - Movable: 9 (years = 3)
      - Fixed:   5 (years = 7)
      - Dual:    1 (years = 11)
    """
    category = _sign_category(sign)
    if category == "movable":
        return 12 - 9  # 3
    if category == "fixed":
        return 12 - 5  # 7
    # dual
    return 12 - 1  # 11
```

Pure category dispatch — no lord-strength modifier, no exceptions. Each
of the 4 movable signs gets 3y, each of 4 fixed gets 7y, each of 4 dual
gets 11y. Total: 4×3 + 4×7 + 4×11 = **84 years**.

### Track B (uniform 12y, total 144y — THE BUG)

The pathology is in the interaction between two helper functions, neither
broken on its own.

**Helper 1** — `_pick_lord_sign` at
[`app/core/chara_dasha.py:90-106`](../../app/core/chara_dasha.py#L90-L106):

```python
def _pick_lord_sign(sign: int, direction: int) -> int:
    """For dual-ruler planets, return whichever owned sign is *closer*
    to the dasha sign in the chosen direction (Narasimha Rao rule)."""
    lord = _SIGN_LORDS[sign]
    owned = _PLANET_OWNS[lord]
    if len(owned) == 1:
        return owned[0]
    a, b = owned
    da = _inclusive_distance(sign, a, direction)
    db = _inclusive_distance(sign, b, direction)
    return a if da <= db else b
```

**Helper 2** — `period_for` at
[`app/core/chara_dasha.py:109-117`](../../app/core/chara_dasha.py#L109-L117):

```python
def period_for(sign: int, direction: int) -> int:
    """If the lord-sign equals the sign itself (distance 1, lord IS the
    sign), classical rule returns 12; otherwise (distance − 1)."""
    lord_sign = _pick_lord_sign(sign, direction)
    d = _inclusive_distance(sign, lord_sign, direction)
    return 12 if d == 1 else d - 1
```

### Why this collapses to uniform 12y

For any sign `S` whose lord owns two signs (Mars→1,8; Mercury→3,6;
Venus→2,7; Jupiter→9,12; Saturn→10,11):

1. One of those two owned signs IS `S` itself.
2. `_inclusive_distance(S, S, direction)` = 1.
3. `_pick_lord_sign(S, direction)` compares distance-1 (S→S) vs
   distance-N (S→other-owned-sign). Distance 1 always wins.
4. Therefore `_pick_lord_sign` returns `S`.
5. `period_for` sees `d == 1` and returns 12.

This affects 10 of the 12 signs (every dual-ruler sign). The remaining
two — Cancer (Moon, single owner) and Leo (Sun, single owner) — happen
to also produce `d == 1` because for Cancer Moon's only owned sign is
Cancer itself, and same for Leo+Sun. So 12y applies to ALL 12 signs.

### Worked example — Virgo

- `_SIGN_LORDS[6]` = Mercury
- `_PLANET_OWNS[Mercury]` = (3, 6)
- Distance forward 6→3: `((3-6) % 12) + 1 = 10`
- Distance forward 6→6: `1`
- `_pick_lord_sign(6, +1)` = 6 (picks self)
- `period_for(6, +1)` = 12

Every Virgo-lagna MD in Track B = 12 years. 12 × 12 = 144 years.

### Why this is a bug, not a variant

1. **No docstring or constant acknowledges or justifies 144 years.** The
   classical Jaimini cycle is 84 years (Sanjay-Rath, Iranganti Rangacharya,
   K.N. Rao, PVR Narasimha Rao all agree on 84y total — they differ on
   *which* sign gets *how many* years, not on the total).
2. **The docstring claims K.N. Rao formulation**, which produces variable
   periods. The code produces uniform periods. Code ≠ docstring.
3. **The pathological interaction is not classically justified.** The
   classical "lord-in-own-sign → 12 years" rule applies as a *correction
   for lords WHO HAPPEN TO RESIDE IN THEIR OWN SIGN in the natal chart*,
   not as a structural property of the lord-sign relationship itself.
   Track B treats every sign as if its lord IS in its own sign, which is
   never universally true.
4. **No external authority defends uniform-12y.** Iranganti Rangacharya's
   "Sthira" Chara variant has variable periods; "Mandook" / "Saral" Chara
   uses variable periods; no published Jaimini Chara variant produces 144y
   total.

---

## Why this matters

Predictions that depend on Chara Dasha are **fundamentally different**
across the two engines. For Virgo lagna:

- At age 11, Track A says Cancer MD; Track B says Virgo MD. Different
  significations, different planets, different timing.
- Track A's cycle completes at age 84 and repeats; Track B's at age 144,
  meaning Track B effectively never repeats within a human lifetime.
- Track B's modulo-wrap at
  [`app/core/chara_dasha.py:165-169`](../../app/core/chara_dasha.py#L165-L169)
  wraps `target_jd` against the natal 144y cycle. After age 84, this
  produces SILENTLY WRONG sign assignments (classical doctrine says the
  cycle should have wrapped at 84).

Any downstream computation in Track B's `app.core.reading_composer` that
consults Chara Dasha state (e.g. `chara_md_at_target` field in the
`Reading` dataclass) carries this error forward.

---

## Three remediation options

### Option 1 — Align Track B to Track A (recommended)

Rewrite `app/core/chara_dasha.py` to use the Sanjay-Rath D-17 rule
(matching Track A). Concretely:

- Replace `direction_for` + `_pick_lord_sign` + `period_for` with the
  category-dispatch rule from Track A's `_years_for_sign`.
- Replace `chara_sequence` initialisation with Track A's
  `_starting_md_sign` rule (movable=self / fixed=5th / dual=9th).
- Update module docstring to cite Sanjay-Rath Crux Ch.16.
- Add regression test pinning the 84y cycle total for Virgo lagna.

**Cost:** ~50 LOC change in 1 file; ~200 LOC of new tests; doctrine
lockfile already exists (D-17). Low risk because Track A is already
the authoritative project doctrine.

**Pro:** Project converges on one Chara Dasha variant. Downstream
`reading_composer` becomes correct. Comparator tests in
`tests/integration/test_chara_compare.py` flip from "documents
divergence" to "asserts agreement."

**Con:** Touches Track B code — out of scope for the "untouched"
integration constraint.

### Option 2 — Align Track A to Track B

NOT recommended. Track A is the project's doctrine-locked implementation
(D-17 lockfile, Sanjay-Rath citation, 4 referenced authorities). Track B
is the variant with no defensible documentation.

### Option 3 — Keep both, expose variant choice

Parameterise both engines on a `chara_variant` enum
(`SANJAY_RATH_84Y` / `KN_RAO_84Y_VARIANT_B` / `BUG_LITERAL_TRACK_B`).
Let callers pick which variant they want.

**Pro:** Honest about the existence of competing schools. Useful for
historical comparison.

**Con:** Complicates the API; only the SANJAY_RATH path is doctrinally
defended; the "BUG_LITERAL" path is morally indistinguishable from
shipping a known wrong implementation.

---

## Recommendation

Adopt **Option 1**. The integration layer was built explicitly to
surface this kind of question; the answer is now clear; ship a Track B
fix as commit `fix(core): align Chara Dasha to D-17 Sanjay-Rath
(corrects 144y → 84y bug surfaced by integration comparator)`.

After the fix, the comparator's `test_chara_compare.py::TestKnownDivergence`
class should be flipped: replace the "documents divergence" assertions
with "asserts full agreement" assertions. Keep the per-MD diff
infrastructure — it remains useful for future doctrine work.

---

## Audit trail

- Phase-1 deep-read agent reports preserved at
  `C:\Users\S.C.C\.claude\projects\e--astro\07af71d0-4c6b-4374-bfcb-0cd442453b79\subagents\workflows\wf_aac10037-d2f\`
  (agents `a626e60e027a07662` for Track A, `a35d715463abfa5a9` for Track B).
- Comparator integration tests at
  [`tests/integration/test_chara_compare.py`](../../tests/integration/test_chara_compare.py)
  classes `TestKnownDivergence` and `TestCurrentMDCrossCheck`.
- Bangalore baseline fixture: DOB 1990-07-15 12:00 IST, lat 12.97, lon
  77.59, lagna Virgo (sign 6), birth_jd 2448088.2708333.
