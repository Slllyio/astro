# Follow-up to the opposite-verdict study: what else can be fixed from the text

2026-11-05, after F2 and F5 shipped (main-local 04ecf784, ratchet 240/334/31 on 365).
Akkshay: "Do whatever improve system as u found out very deeply the causes of misses."

Every candidate below went through the same three steps. First, Raman's own words were read
(line numbers only; this repo is public, so no book text). Second, the candidate was measured
on the 365 scored conclusions and on all 19,665 sub-matter readings of Raman's charts.
Third, it was shipped only if the text supports it and no scored row gets worse. All
figures are in-sample, because every hold-out is already spent.

## Result

**No further engine change ships.** Of the eight candidates, one moves a scored row the right
way with nothing worse, and it rests on the very rule that Raman himself rejects for this
purpose. Every other candidate is flat or net worse. Two record errors in the answer key were
repaired, and neither changes a label or the score.

| # | Candidate | Text | Measured (exact / one step / opposite) | Decision |
|---|---|---|---|---|
| 1 | C1: weakness alone is not affliction (clause 6 without a fired malefic gives mixed) | 3HCC:877-881 | 237 / 97 / 31 | Held (net -3) |
| 2 | C2 obstructed carrier | NH:7196-7199 | 242 / 90 / 33 | Held (+2 exact but +2 opposite) |
| 3 | C4 karaka veto relief | 3HCC:11228-11230 | no change | Held |
| 4 | M1 maraka guard on all non-death matters | HTJAH-I:776-814 | 237 / 96 / 32 | Held |
| 5 | Y1 blemish tier | 3HC 10264-10267 | 239 / 91 / 35 | Held |
| 6 | Fertility gate read as Raman wrote it: each native's own sphuta (Beeja for a man, Kshetra for a woman), and a weak own sphuta reduces rather than denies | HTJAH-I:5497-5527, 5507-5509, 5967-5970 | denial form 238 / 94 / 33; reduction form 228 / 106 / 31 | Held, see below |
| 7 | Raman's positional dignity instead of Shadbala for "strong" and "weak" | HTJAH-I:474, 497 | dignity only 196 / 110 / 59; dignity where it decides, else Shadbala 238 / 95 / 32 | Held |
| 8 | Moon benefic only from the 8th day of the bright half to the 8th day of the dark half; Mercury benefic only when not joined by a malefic | GBB ch.5:162-170; HPA ch.6:121-131; 3HC 659-662 | band form: no scored row moves; 126 of 19,665 readings move, 111 of them harsher | Held, see below |

The marital-happiness misses (Marie Antoinette, H. G. Wells, Dalmia) are not a missing rule.
Raman's only general "unhappy marriage" rule, malefics in the 7th from Venus (HTJAH-II:376-377),
is already encoded as a karaka-frame rule. In these three charts he reasons from the 7th lord
with a node under a malefic aspect, a rule his own text files under character (HTJAH-II:447-449),
so they stay class A/E. The rule was tried as F1 and failed.

Roosevelt's career rests on "some sort of" Vipareeta Raja Yoga, which Raman improvises from the
Lagna lord in the 6th (NH:10151-10157). It does not fit the dusthana-lord pattern, and 3HC warns
that the Harsha/Sarala/Vimala yogas in practice "only somewhat modify" the evil (3HC 4774-4798).
So it is not encoded as a general lift.

## The fertility gate

The gate decides about 14 scored children verdicts. The 2026-08-29 doctrine review already found
it refuted as written: Raman tests the native's own sphuta only, and denial is read across the
couple (DOCTRINE_BACKLOG "Children cluster"). Re-measured today with the natives' sex taken from
Raman's own write-ups, the faithful versions cost 2 rows (denial on the own sphuta) or 12 rows
(reduction on the own sphuta).

The 12 rows are ones where Raman's conclusion (afflicted) is printed. The engine reaches it only
through the gate, because without it the placement evidence reads them favourable. In 12 of the
15 carried charts the reason is the same: H5.C.1 ("benefic associations or aspects on the
5th → there will be children", HTJAH-I:5183) fires, which opens a contradiction, and the
Shadbala pillars then lift the matter. Raman instead reads the 5th lord and karaka as
"considerably afflicted" by malefic contact.

The sanctioned recovery path is unchanged: encode Raman's printed afflicting drivers for those
charts first, then retire the gate. Sex is now known for 26 of the 35 scored children charts.
Male: HTJAH-I Charts 91, 92, 93, 95, 97, 98, 99, 101; NH 16, 18, 19, 20, 31, 35, 37, 39, 40, 48,
52, 57, 59, 67, 68. Female: NH 22, 27, 74. The other nine (HTJAH-I Charts 94, 96, 100, 102-106, 108) do not state the native's
sex, so it stays unknown.

## The conditional benefics

Raman's definitions agree across GBB, HPA and 3HC. The Moon is benefic from the 8th day of the
bright half to the 8th day of the dark half. Mercury is benefic when well associated and malefic
when badly associated. Raman never defines "associated". His worked lines support conjunction
with a malefic, the Sun included (HTJAH-I:5855, 5808-5809). He gives no case where aspect alone
is enough. He also never states that a waning Moon's aspect on a house is malefic, so applying
the band to house aspects is an inference.

Measured with the band (84° to 276° elongation), no scored row moves, and 126 unscored readings
move, 111 of them harsher. The second hold-out found the engine already over-calls affliction.
A change that only makes unscored readings harsher, on an inferred extension, does not meet the
bar. A full implementation would also touch about 90 sites that read `NATURAL_BENEFICS`. Re-open
if a scored conclusion ever turns on a waning Moon or a Mercury joined by a malefic.

## Answer-key repairs (no label or score change)

- NH No. 35 (Tagore), H5: the verdict words quoted the intelligence sentence (NH:7887-7889).
  They now quote the children sentence the label rests on (NH:7896-7898).
- HTJAH-I Chart 121 (`HTJAH-I.h6_12`): added the education passage HTJAH-I:4887-4907 to its
  citations. The record carried only the 6th-house citation.

Still open, each needing the owner: HTJAH-II Chart 35 (a longevity verdict filed under manner of
death); the NH No. 74 Moon misprint (34°17'), which changes no verdict; and the soft labels
listed in the study.

## What this says about the misses

The 31 opposite verdicts that remain are not waiting for a missing rule. They come from the
judge's weighing: Shadbala stands in for Raman's "strong" and "weak", and broad benefic rules
open a contradiction that the pillars then settle. Both were tested directly today, and each
alternative was worse. This matches the 2026-08 finding that the judge sits at a measured local
optimum. Moving further needs a new weighing mechanism, which is design work, not a fix.
