# KP engine rulings

The KP engine (`app/kp/`) encodes K. S. Krishnamurti's *KP Reader 3: Predictive Stellar
Astrology* (library source `kp_reader3_predictive`, OCR). Every rule cites its line range in
that file as `KPR3:<lines>`; the quotes live in `app/kp/citations.py` and
`tests/kp/test_citations.py` checks each one against the file wherever the library is present.

Where Reader 3 is silent, ambiguous, or contradicts itself, the engine makes one named choice
below. Each ruling says what was chosen, why, and what the alternative was. **These rulings are
frozen before any real-people test.** Changing one after seeing outcomes is overfitting.

KP is a separate system from the Raman and Parashari engines. Its own doctrine requires the
Krishnamurti ayanamsa and Placidus cusps. The repo-wide Lahiri lock (CLAUDE.md) still governs
every other engine, and the KP caster restores Lahiri as swisseph's global mode after every call.

## Sources held and not held

| Held | Not held |
|---|---|
| Reader 2, Fundamental Principles (`kp_reader2_fundamentals`) | Reader 1 (casting, sub tables) |
| Reader 3, Predictive Stellar Astrology (`kp_reader3_predictive`): **the engine's authority** | Reader 4, Marriage, Married Life and Children |
| KP E-zine 2015-2020 (`kp_readers_complete`, **mislabelled**: later authors, not KSK) | Reader 5 (Transits), Reader 6 (Horary) |

The E-zine is never cited as Krishnamurti. One ruling (R10) takes a convention from it and says so.

## Mechanical core (no choice involved)

| Item | Source | Verified against print |
|---|---|---|
| 27 stars x 9 subs in Vimshottari proportion = 243 subs; 6 straddle a sign edge = 249 divisions | KPR3:3402-3404 | Horary numbers 206 and 37 give exactly Capricorn 26°06'40" and Taurus 22°40' (KPR3:19551-19553, 19779-19780) |
| Placidus cusps, sayana minus Krishnamurti ayanamsa | KPR3:7664-7665, 19556-19559 | 1922 native: Ascendant Leo 12°09' vs printed 12°11' |
| Krishnamurti ayanamsa = Swiss Ephemeris `SIDM_KRISHNAMURTI` (true, with nutation) | KPR3:18871, 19559 | 22°41' vs printed 22°40' (1922); 23°20' vs 23°20' (1969) |
| Sign, star, sub, sub-sub lord of every planet and cusp | KPR3:3402-3404 | 1922 native: **all 18 printed star and sub lords reproduced** |
| House lord = lord of the sign on the cusp | KPR3:17845-17846 | 1922 native: lords of 1, 2, 5, 9, 11, 12 as stated in the text |
| Five ruling planets | KPR3:24916-24925 | 7 April 1966 07:35: Jupiter, Rahu, Venus as printed |

## Rulings

**R1. Authority.** Reader 3 only. Where later KP practice (4-step theory, cuspal interlinks,
sub-sub lord as final judge, KP New ayanamsa) differs, the engine follows Reader 3.

**R2. Ayanamsa.** `SIDM_KRISHNAMURTI`, not KP New (Khullar) or `SIDM_KRISHNAMURTI_VP291`. It
matches Krishnamurti's two printed values within 1'.

**R3. Cusps.** Placidus via Swiss Ephemeris, matching "Raphael's Table of Houses". At latitudes
where Placidus is undefined the cast raises `KPUndefined`; no other house system is substituted.

**R4. Nodes: mean node.** The 1922 chart prints Rahu at 10°28' Virgo. The mean node gives 10°30';
the true node gives 9°38'. `node_mode="true"` stays available for comparison.

**R5. Occupancy by Placidus bhava, not by sign.** A planet occupies the house whose cusp-to-cusp
arc contains it. Krishnamurti speaks of "Venus in the 6th Bhava", and the 1922 text's
occupancies (Sun in 11, Moon in 9, Mars in 4) all agree with bhava placement.

**R6. Node agency.** A node gives the results of planets conjoined with it, then of planets
aspecting it, then of its sign lord (KPR3:2571-2573). "Conjoined" = same sign (Krishnamurti's
examples use rasi-chart conjunction). The node's agent houses are the occupied and owned houses
of the planets it represents, and they are tagged `agent` in every output.

**R7. Marriage = 7th cusp sub-lord against 2, 7, 11 and 1, 6, 10, 12 (status: extended).** The
favourable houses 2, 7, 11 are Krishnamurti's (KPR3:14306-14307). The denial houses come from
his answer to a horary marriage question (KPR3:21495-21497). The engine applies that horary test
to the natal chart. Reader 3's own natal marriage chapter lists 26 alternative Hindu and Western
conditions (KPR3:14329-14401) that are not encoded, because they are alternatives with no stated
rule for combining them. Reader 4, which Reader 3 points to for detail, is not held.

**R8. Level E (conjunction and aspect) is not encoded.** The ladder's last level, "planets
conjoined with or aspected by them", needs a definition of aspect, and Krishnamurti mixes
Hindu drishti, Western aspects with orbs (he lets a 108° aspect pass where 90° would block) and
Uranus. Encoding any one of these would be our choice, not his. The node-aspect step in R6 is
dropped for the same reason.

**R9. Five ruling planets.** Reader 3 lists four at KPR3:24764-24766 and five at
KPR3:24916-24925; its worked example also adds a planet aspecting the Moon. The engine returns
the five and reports nodes standing for any of them separately (`node_agents`), never merged.

**R10. Weekday runs sunrise to sunrise.** Reader 3 does not say. The KP E-zine does ("For
calculating Day Lord, Sun nse [rise] to Sun rise is taken as one day", `kp_readers_complete`
chapter 15, line 34310). Flagged as a non-KSK source.

**R11. Year length 365.2425 days.** Reader 3 does not state one. The repo's locked
`DAYS_PER_VEDIC_YEAR` is used. Over a 20-year dasa the difference from 365.25 is about 5 days.

**R12. Verdicts are not weighed.** The cusp sub-lord (CSL) signifies a set of houses (levels A-D).
PROMISED if it hits the favourable group only; DENIED if it hits the denial group only; MIXED if
both; NOT_SIGNIFIED if neither. Reader 3 gives no tie-break for MIXED and leaves weighing to the
astrologer ("calmly judge what it can do", KPR3:6918-6919). The engine does not invent one. The
CSL's own sub-lord (the "sub decides" rule, KPR3:6704-6706) is reported beside the verdict but
does not change it, because Reader 3 does not say how the two levels combine.

**R13. Health (status: extended).** Ascendant CSL against favourable 1, 11 (KPR3:6814-6815) and
denial 6, 8, 12 (KPR3:6663-6664, 6774-6776). The 6/8/12 rule is stated for "the significator of
the ascendant"; the engine applies it to the ascendant's sub-lord.

**R14. Wealth (status: cited).** 2nd CSL against favourable 2, 6, 11 (KPR3:8742). Reader 3 gives
no denial houses for the 2nd cusp: its cusp chapter treats 2 with 12 as a kind of earning, not a
loss. So wealth can come out PROMISED or NOT_SIGNIFIED only, and that limit is part of the result.

**R15. Service (status: extended).** Service houses 2, 6, 10 and their negations 1, 5, 9
(KPR3:9425-9426). Reader 3 states these for timing; the engine applies them to the 10th CSL.

**R16. Any house (status: general).** For house H, favourable H and denial 6, 8, 12 counted from
H, Krishnamurti's "general principle" (KPR3:6671-6677).

**R17. Timing.** Candidate periods are dasa-bhukti-antaras whose three lords all signify a
favourable house (KPR3:8741-8742, 9447-9449). Krishnamurti picks the "strongest" among
significators by judgment; the engine lists every candidate and flags lords that also signify
denial houses. It does not rank them.

## What this engine is

A faithful instrument for "what would Krishnamurti's Reader 3 rules say", with every step shown.
It is **not** a validated predictor. Nothing has been tested against real lives yet; see
`docs/kp/KP_PREFLIGHT_2026-10-31.md` for the first checks on ordinary charts.
