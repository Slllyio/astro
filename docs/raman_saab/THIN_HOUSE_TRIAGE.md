# Thin-house triage — where the engine's misses actually live (2026-07-24)

> The meta-finding that emerged from the Notable-Horoscopes corpus expansion (192 -> 225 charts),
> made **reproducible and corpus-wide** by `tools/raman_saab/discriminator_scan.py`. It answers the
> question the H10/H4 probing raised: *which* of the engine's residual misses are cleanly encodeable
> placement rules, and which are the B1 / karaka-frame frontier?

## The two kinds of gap

Every residual miss-signification falls into exactly one of:

1. **Harvestable — a clean placement discriminator exists.** A simple house-geometry predicate
   (benefic/malefic influence on the bhava, papakartari, the lord in a dusthana) fires on ONE verdict
   class only (purity 1.00), on >=2 charts, and closes >=1 current engine-miss. These become cited
   rules exactly like **H10.C.61** ('benefic-fortified, malefic-free 10th -> favourable career').

2. **Karaka-frame / B1 comparative-weighing — no clean placement rule.** The verdict is driven by the
   signification's KARAKA (Moon=mother, Mercury=education, Jupiter=children, Venus=spouse, Sun=father)
   and by Raman's comparative weighing of strong-vs-afflicted factors, which no single house predicate
   separates. These are deferred to the karaka-frame encodings (e.g. the unimplemented mother-from-Moon
   frame) or the B1 tuner track — NOT forced into an over-firing clause.

## The corpus-wide result (`discriminator_scan.py`)

Across the golden corpus, **35 significations carry >=1 engine-miss. Only 2 are harvestable; 33 are
karaka-frame / B1.** Critically, **every large miss cluster is B1:**

| signification | house | misses | clean discriminator? |
|---|---|---|---|
| children | 5 | 15 | — none (B1) |
| career | 10 | 14 | — none (B1; the one clean slice already shipped as H10.C.61) |
| self | 1 | 13 | — none (B1) |
| wealth | 2 | 12 | — none (B1) |
| father | 9 | 8 | — none (B1) |
| fortune | 9 | 7 | — none (B1) |
| marital_happiness | 7 | 6 | — none (B1) |
| **siblings** | 3 | 4 | **malefic-afflicted, benefic-free 3rd -> afflicted (1.00 / n=2 / closes Nehru)** |
| education | 4 | 4 | — none (karaka-frame: Mercury-Vidyakaraka) |
| **death** | 8 | 3 | **8th-lord in a dusthana -> afflicted (1.00 / n=3 / closes Marie Antoinette)** |
| mother | 4 | 3 | — none (karaka-frame: Moon-Matrukaraka) |
| … 24 more … | | 1–3 each | — none (B1) |

## What this means

- **The engine's ~89% plateau is B1-bound, not placement-gap-bound.** The placement-rule harvest is
  essentially complete: after H10.C.61, the *entire remaining corpus* yields only **2 more clean
  placement wins**, closing **2 misses** total. Every other residual miss needs the harder work.
- **The four house-based discriminators tested** — benefic-fortified/malefic-free, malefic-afflicted/
  benefic-free, papakartari-on-the-house, lord-in-dusthana — fail on the karaka-driven significations
  by construction: a mother's fate tracks the Moon (not the 4th house's benefics), a child's the
  PutraKaraka, a spouse's Venus. House geometry cannot separate them (proven per-signification: e.g.
  a *favourable* mother has papakartari on the 4th; a *favourable* happiness chart has its 4th lord
  in the 8th).
- **The real levers are therefore two, both bigger than clause-work:** (a) the **karaka-frame
  encodings** (mother-from-Moon, and the karaka-affliction readings the diagnostic points to), and
  (b) the **B1 comparative-weighing measure** (the tuner-gated effective-strength track the
  `NH_GAP_ANALYSIS` effort found un-improvable at the `_strong` seam — it needs the `_decide`
  re-derivation, not a placement clause).

## Reproducing / extending

`py -3.12 -m tools.raman_saab.discriminator_scan` prints the full table. To add a candidate
discriminator, extend `_CANDIDATES` (name -> (predicted_verdict, fires(chart, house))); the harness
recomputes purity/support/misses-closed against Raman's verdicts automatically. A candidate that
reaches purity 1.00 / support>=2 / closes>=1 is a harvest lead; anything less is left as B1.

## Status of the 2 harvest leads — BOTH FAILED the shippable bar (harvest confirmed exhausted)

On implementation, **neither** empirical lead yielded a shippable fidelity win — a crucial refinement
of the tool's output:

- **Death (8th-lord-in-dusthana):** doctrinally **spurious**. All 3 charts have the 8th lord in the
  8th (its OWN house) — a Vipareeta-adjacent placement that classically can be *favourable*; the
  corpus even says the dusthana-8th-lord *reduces* death-intensity (HTJAH-II:2923). The 3 violent
  deaths trace to the drekkana / Mars, not the lord placement. Rejected — "purity 1.00 / n=3" was a
  small-sample correlation against the doctrine, not a real signal.
- **Siblings (malefic-afflicted, benefic-free 3rd):** doctrinally sound (the afflicted mirror of
  HTJAH-I:3428) but **inert on the verdict path**. The benefic-3rd->brothers reading is ALREADY
  encoded (`_BeneficOccupiesOrAspects3rd`, rule #7), and adding the malefic mirror changed **zero**
  verdicts — Nehru stays *mixed* (the synthesis absorbs the malefic signal). His *mixed*-vs-Raman's
  *afflicted* is B1 comparative-weighing, not a missing clause. Reverted (an inert rule does not earn
  its place).

**Lesson (strengthens the meta-finding):** the discriminator scan's "purity 1.00 / support>=2 /
closes>=1" is a *lead*, not a green light — it counts the discriminator FIRING, not the judge
FLIPPING, and does not test doctrinal soundness. Passing it additionally requires: (a) the direction
is Raman-doctrinal (not a Vipareeta/upachaya-confounded correlation), and (b) the rule is DECISIVE
enough to move the synthesis (or the case is B1). After H10.C.61, **no residual miss in the corpus
clears all three bars** — the placement-rule harvest is complete. The remaining levers are the
karaka-frame encodings and the B1 tuner.
