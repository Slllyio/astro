# Phase 4.1 results: Gauquelin Mars-sector positive control

Per `docs/validation/PHASE4_1_GAUQUELIN_PREREG.md`. Gauquelin holdout, AstroDatabank overlaps and un-geocoded rows excluded. Key sectors {36,1,2,3,9,10,11,12}; expected rate from 100 date/time/place shuffles.

| group | n | observed key-sector share | expected (shuffle) | excess (pts) | 95% CI (pts) |
|---|---|---|---|---|---|
| sports_champion | 1285 | 0.2732 | 0.2263 | +4.68 | +2.04..+7.20 |
| painter | 933 | 0.2036 | 0.2255 | -2.18 | -4.78..+0.08 |
| writer | 635 | 0.2504 | 0.2296 | +2.08 | -1.25..+5.38 |
| actor | 698 | 0.2106 | 0.2246 | -1.40 | -4.68..+1.36 |

**Positive control: PASS** (pass bar: sports-champion CI excludes 0 and excess >= +2.0 pts; Gauquelin printed about +4.5).

Deviation (pre-result): rows with a missing tz offset / latitude / longitude are excluded alongside
`needs_geocoding` (11 rows lacked tz without the flag; the first run crashed on them before any result).

**Reading.** This is a machinery check, not an astrology finding. The pipeline reproduces Gauquelin's
printed sports-champion Mars excess (+4.7 vs ~+4.5 points) on his own civil-register file, while
painters, writers and actors sit near 0. So a real-data effect of a few points IS visible to this kind
of pipeline: the Vedic nulls are not blindness. Whether the Gauquelin effect itself is real (as opposed
to sample selection in how he chose champions, the long-running Ertel/CSICOP debate) is outside this
project. It is not cited as support for any astrological doctrine, Vedic or Western.
