# KP engine rulings

The KP engine (`app/kp/`) encodes K. S. Krishnamurti's KP Readers 1, 3, 4, 5 and 6 (library
sources, OCR). Reader 3 rules cite a line range as `KPR3:<lines>`; the other Readers cite a page
marker as `KPR<n>:p.N`. The quotes live in `app/kp/citations.py` (82 of them) and
`tests/kp/test_citations.py` checks each one against its file wherever the library is present.

Where Reader 3 is silent, ambiguous, or contradicts itself, the engine makes one named choice
below. Each ruling says what was chosen, why, and what the alternative was. **These rulings are
frozen before any real-people test.** Changing one after seeing outcomes is overfitting.

KP is a separate system from the Raman and Parashari engines. Its own doctrine requires the
Krishnamurti ayanamsa and Placidus cusps. The repo-wide Lahiri lock (CLAUDE.md) still governs
every other engine, and the KP caster restores Lahiri as swisseph's global mode after every call.

## Sources held and not held

| Source | Library id | Used for |
|---|---|---|
| Reader 1, Casting the Horoscope | `kp_reader1_casting` (OCR 2026-11-01) | Placidus, ayanamsa table (pinned) |
| Reader 2, Fundamental Principles | `kp_reader2_fundamentals` | not cited |
| Reader 3, Predictive Stellar Astrology | `kp_reader3_predictive` | **general authority** |
| Reader 4, Marriage, Married Life & Children | `kp_reader4_marriage` (OCR 2026-11-01) | marriage, children |
| Reader 5, Transits | `kp_reader5_transits` (OCR 2026-11-01) | transits; significator table (pinned) |
| Reader 6, Horary Astrology | `kp_reader6_horary` (OCR 2026-11-01) | horary, ruling-planet timing and birth-time correction |
| KP E-zine 2015-2020 | `kp_readers_complete` (**mislabelled**: later authors, not KSK) | R10 only, flagged |

The other books in `kp-readers/` (KP E-zine 2020-21, *KP Navratnamala*, *Sublord Speaks*,
*Astro Secrets & KP* 1-6, *Astrology for Beginners*) are by later authors. They are encoded only
in the walled `app/kp/later/` layer (rulings LR1-LR7 below), OCR'd 2026-11-01 to
`kp_later_<id>` in the library, and never feed Krishnamurti's verdicts.

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

**R1. Authority.** Reader 3, and Reader 4 for marriage. Where later KP practice (4-step theory, cuspal interlinks,
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

**R6a. A planet in a node's star takes only the node's occupied house.** The node's agent
houses (from the planet it represents) belong to the node alone. Krishnamurti's significator
table for the Alibag chart (KPR5:p.152-154) gives Sun and Jupiter, both in Ketu's star, only
Ketu's house 7, not Ketu's agent houses 4 and 8. With this ruling all nine planets in that table
are reproduced exactly (`tests/kp/test_reader5.py`). *Changed 2026-11-01*; the first build passed
the agent houses through.

**R7. Marriage = 7th cusp sub-lord against 2, 7, 11 and 4, 6, 10 (status: cited, Reader 4).**
"Note the sub-lord of the 7th cusp. If it is a significator of house 7 or 2 or 11, marriage is
promised" (KPR4:p.121). "The simple rule is, note the sublord of the 7th Cusp; if the sub lord is
connected with 4, 6, 10th houses, one will be denied of marriage" (KPR4:p.106; reason given at
p.105: these are the 12th houses to 5, 7 and 11). *Changed 2026-11-01*: the first build used
1, 6, 10, 12 from a horary passage of Reader 3 (KPR3:21495-21497), because Reader 4 was not yet
held. Reader 4 also says "if the sub is lord of 1, 6, 10 and is the significator of 12 houses,
marriage cannot take place" (KPR4:p.118), but there it is choosing among significators for
timing, not judging the 7th cusp, so it is not used for the promise verdict. Reader 3's 26
alternative Hindu and Western conditions (KPR3:14329-14401) remain unencoded.

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

**R12. Raw verdict.** The cusp sub-lord (CSL) signifies a set of houses (levels A-D).
PROMISED if it hits the favourable group only; DENIED if it hits the denial group only; MIXED if
both; NOT_SIGNIFIED if neither. Reader 3 leaves the weighing of MIXED to the astrologer ("calmly
judge what it can do", KPR3:6918-6919). The raw verdict is always reported.

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

**R18. Settling MIXED (user decision 2026-11-01: "Find Reader 4 first").** Reader 4 shows how
Krishnamurti settles a 7th sub-lord tied to both groups. In his denial case the sub-lord Rahu
occupies the 6th and, conjoined with Venus, stands for the lord of 7: "Rahu occupying Venus sign
and conjoined with it shows that 6th house result is stronger than 7. Further Rahu is in the sub
of Saturn in the 12th house" (KPR4:p.106). The engine follows that order:
(1) the group the CSL reaches at the stronger ladder level wins (A > B > C > D; "occupants are
stronger than owners. Constellations are stronger than signs", KPR4:p.118); (2) if both groups are
reached at the same strongest level, the CSL's own sub-lord decides ("it is the sub lord which is
mainly responsible", KPR4:p.106); (3) if the sub-lord also touches both or neither, the verdict
stays MIXED. Every verdict records `raw_verdict` and `resolution` (direct / level / sub_lord /
unresolved). The same procedure is applied to health, wealth and service, which extends a
marriage example to other matters. Saturn as a significator "will not deny but will cause delay"
(KPR4:p.109) is noted in the citations but not encoded as a separate output.

**R19. Children and timed events (status: cited).** Children: 5th cusp sub-lord against 2, 5, 11
and 1, 4, 10 (KPR3:21258-21262; Reader 4 pp.106, 216). Seventeen events Reader 3 times by the
conjoined periods of a house group (marriage, engagement, childbirth, getting and ending service,
business, money, building, disposal, studies, study abroad, scholarship, transfer, deputation,
overseas, regaining position, imprisonment) are in `app/kp/events.py`, each with its citation.
They have no cusp or denial group in the text, so they are timing rules only. Where Krishnamurti
adds a condition on the same significators (3 and 9 for engagement, 6 or 10 for transfer), each
window reports which lords meet it; windows are not dropped for it.

**R20. Longevity and maraka are not encoded.** Reader 3 judges houses 1, 8, 3 against 2, 7, 12
(KPR3:7966-7970). The engine does not time death, matching the project rule for every engine.

**R21. Transits (Reader 5).** A transiting planet brings the matters of the houses its star lord
signifies, through the matters it signifies itself, and the sub lord shows whether it
materialises (KPR5:p.159). The sensitive points of a dasa-bhukti-antara are the positions whose
sign, star and sub lords are those three planets in any order (KPR5:p.160); the engine's table
reproduces his printed points for Mars/Saturn/Mercury, Mars/Venus/Venus and Mars/Venus/Sun.
`transit_hits` reports when the Sun, the Moon and the period lords pass those points inside the
period. The Ascendant's pass is computed for where the native lives (KPR5:p.160).

**R8a. Level E (opt-in).** "(5) Very weak but yet those connected with a bhava are those planets
conjoined with or aspected by the significators found out already" (KPR5:p.153; KPR6:p.197).
`planet_significations(chart, level_e=True)` adds, for each planet, the houses it does not already
hold at A-D, when it shares a sign with, or receives a Hindu sign aspect from, a planet that
signifies them. Aspects are the ones Krishnamurti names (Saturn "by its 10th aspect", Jupiter "by
its 5th aspect", KPR6:p.288): every planet the 7th, Mars 4 and 8, Jupiter 5 and 9, Saturn 3 and
10; the nodes cast none. Off by default, and verdicts never use it: he calls it "very weak", and
his worked tables (Alibag, KPR5:p.154) list A-D only.

**R22. Natal indications.** `app/kp/indications.py` holds 59 one-line rules of the form "If the
sub-lord of the Nth cusp ..." from Reader 3 (ascendant CSL signifying 1 and N; 2nd CSL signifying
2 and N; 2nd CSL by planet; ascendant CSL in the star of a planet in each sign; and others) and
Reader 4 (ascendant CSL signifying N, career partner, more than one marriage, second marriage via
the 2nd cusp). "And"/"or" are kept as printed (RH7). They are descriptive and never timed. Left
out: every death, lifespan or partner-death rule; rules whose cusp is not named (KPR4:p.69);
rules resting on an undefined "connected in any manner"; rules needing a second person's chart
(KPR4:p.177); and "chaste wife" (KPR4:p.100), whose "occupying" clause has no single reading.

**R23. Descriptive tables.** The partner table (KPR4:pp.86-97, 7 planets x 12 signs) is read for
the 7th CSL and, as each heading says, for its star lord, each in the sign it occupies; a node is
read through its conjoined planet, else an aspecting planet, else its star lord (KPR4:p.97). "Love
and life" (KPR4:pp.156-170) is read by the sign of the 5th CSL. The text is parsed from the OCR
file at run time and never committed.

## Selecting the useful significators (`app/kp/selection.py`, added 2026-11-02)

The A-D ladder names many planets for any matter. Krishnamurti then asks "how to eliminate the
useless ones and select the useful ones" (KPR4:p.118). R17 timing used every ladder significator;
R24-R26 encode his three further steps. None of them changes a verdict.

**R24. Strong significators (ranking, not a filter).** For each occupant of a house, the planets
in its stars give the house's results (KPR5:p.208); "if there is no planet in any of the 3 stars
of the occupant, then the occupant offers the results ... and it is stronger than the lord"
(KPR5:p.209). An empty house goes to the planets in its lord's stars, else to the lord (KPR5:p.147).
A node standing for a strong significator is taken (KPR6:p.162), and so are planets in that
node's star (KPR4:p.190). Pinned on two printed examples: KPR5 pp.208-209 (Kethu and Venus in
Sun's star give 2nd-house results; Moon, with no planet in its stars, is strong for the 4th) and
KPR4 p.190 ("Rahu, Kethu, Sani, Jupiter are the significators", with Mercury for the 2nd).
It ranks and does not filter, because his own worked periods use ladder lords that R24 would
pass over (a "lord of 6" bhukti when 6 is occupied, KPR5:p.150).

**R25. Fruitful significators (filter).** "Further the sub lord of each of the significators. If a
planet is in such a position that its sub lord is connected with the houses 2, 7 and 11 then this
planet is useful" (KPR4:p.118); "in unfavourable sub ... will suffer" (KPR5:p.147). A significator
is kept when its own sub-lord signifies (A-D) a favourable house of the matter. A sub-lord that
also signifies a denial house is flagged, not dropped (as R12 keeps MIXED visible). Stated for
marriage; applied to every matter, which is an extension.

**R26. Ruling planets (filter, only with a moment of judgment).** "Ruling planets at the moment of
judgement must agree" (KPR4:p.118); they "are the real benefactors" (KPR4:p.189). Given the
moment and place of judgment, only significators among the five ruling planets and their node
agents are kept. This makes the answer depend on when it is asked, as his method does. The
pre-flight measures how much.

Flags, never filters: Saturn among the selected ("will not deny but will cause delay",
KPR4:p.109); selected planets that are retrograde or in a retrograde planet's star (failure "when
the significator ... is retrograde", KPR6:p.280).

`selected_windows` returns the R17 periods whose three lords all survive R25 (and R26 when
given), each labelled with how many of its lords are strong (R24). Pre-flight
(`docs/kp/KP_SELECTION_PREFLIGHT_2026-11-02.md`, 2,000 charts, ages 20-40, marriage): R17
covers a median 53% of those years, R25 27%, R26 2%. With R26, 41% of charts get no window at
all, and for 81% the selected planets change if the question is judged one day later.

**R27. Day-fixing by transit (`day_fix`).** "Sun, lord of 2, to fix the day must transit in Venus
sign, Moon star Saturn or Ketu sub" (KPR4:p.133); "the date of marriage will be on the day when
Sun transits in Venus sign, Moon star, Rahu sub" (KPR4:p.189). A day point is any of the 249
divisions whose sign, star and sub lords are all R25 significators of the matter. The R26 cut is
not applied: at p.189 the sign lord Venus is a strongest significator but not a ruling planet.
`day_fix` lists when the Sun (or the Moon, if asked) passes those divisions inside a window,
normally an R17/R25 period. It narrows a period to days; it does not prove the period right.

**R28. The traditional marriage conditions (`marriage_conditions.py`, descriptive only).** Reader 4
lists, "according to Hindu system", when "Marriage is celebrated in youth or in proper age"
(KPR4:pp.70-71, conditions (a)-(w), then (x)-(z) "according to Western System") and when
"Marriage is Promised but it comes off late in life" (KPR4:pp.72-73, (a)-(g)). He gives them as
the tradition, not as his method, so they never touch a KP verdict, window or selection. Readings:
houses by sign from the Lagna sign, "conjoined" = same sign, aspects = full sign aspects (Saturn
3/7/10, Mars 4/7/8, Jupiter 5/7/9, others 7); condition (b) alone uses the KP 7th cusp, because
it names the cusp. Benefics are Jupiter, Venus, Mercury and the Moon. A "favourable" or
"beneficial" house is the 2nd, 7th or 11th ("houses 2, 7 and 11 are examined", KPR4:p.70).
Condition (q) follows KPR4 ("exalted"); KPR3 prints "strong". Left out, each with its reason in
`EXCLUDED`: youth (f), (j), (k), (r) (undefined strength or "favourable connection"), (s) (reads
two ways), (x)-(z) and late (b), (e), (g) (Western aspects, Uranus, orbs).

Pre-flight (`docs/kp/kp_marriage_condition_rates_2026-11-02.json`, 2,000 random births): 94.7%
of charts meet at least one "youth" condition, 48.5% at least one "late" one, and 46.8% meet both.
Because the list is joined by "or", it says little about any one chart.

## Horary (Reader 6), walled in `app/kp/horary/`

Natal KP code never imports the horary package (tested). Death, lifespan and self-harm questions
are refused in code.

**RH1. Horary cusps.** The number gives the Ascendant at the start of its sub; add the
Krishnamurti ayanamsa of the day of judgment, find the Placidus cusps for the latitude of the
place of judgment, deduct the ayanamsa; planets are for the moment judgment starts
(KPR6:p.99-103). Krishnamurti read Raphael's tables and interpolated; the engine computes the
same Placidus cusps exactly. His Madras example (number 48) is reproduced within 30' on every
printed cusp, and exactly on the 10th. His Delhi example (number 74) prints cusps 7-8° from any
Placidus value for that latitude; the OCR of that page is poor, so it is not pinned.

**RH2. Ruling planets for timing.** The five RPs plus node agents (KPR6:p.123), minus any in the
star of a retrograde planet (KPR6:p.123). Fruitful planets are the RPs that also signify the
matter's houses (KPR6:p.126). The body to move: Ascendant for hours, Moon within a month, Sun
beyond a month, Jupiter for years (KPR6:p.131).

**RH3. Which position (reconstructed).** Krishnamurti picks the position by judgment. The engine
takes the first position whose sign, star and sub lords are all fruitful and as many different
planets as possible (three, or all if fewer). This one rule reproduces all three of his printed
answers: the trunk call (Libra 29°20', engine 9:39 against his 9:41), the servant (Taurus, Sun
star, Saturn sub; engine 15:59 against his 4 P.M.) and the friend's arrival (Rohini, Sun sub;
the position matches, but the engine's clock time is 13:29 against his 1:48 P.M.).

**RH4. Sub-sub (reconstructed).** The first fruitful planet not already used; if all are used,
the Ascendant lord at judgment. This matches all three cases and his second birth-time case.

**RH5. Retrograde star lord.** "If the lord of the constellation in which third cusp sub-lord is
deposited is retrograde, the call will not materialise" (KPR6:p.124; again for the child's
return, p.130). He states it for those questions, so the engine reports it as a flag on every
horary verdict and does not change the verdict.

**RH6. Birth-time correction by ruling planets.** "The ruling planets at the time of judgment
will rule (a) the sign, star sub and sub sub of the position of lagna" (KPR6:p.141). Inside the
stated birth window the engine lists every Ascendant position meeting RH3/RH4 and when it rises.
His second case leaves one candidate, Virgo 23°10' at 3:36 A.M. (engine 23°05' at 3:36:19). In
his first case several remain; he chose among them by judgment (a number the native gave) and
his choice is among the engine's candidates. The engine never picks; it is a candidate list,
separate from the event-based rectifier on the rectification branch.

**RH7. Question rules.** `app/kp/horary/questions.py` encodes the 35 question rules Reader 6
prints (appeal, exchange, love affair, lottery, passport, servant, start a business, and so on).
Each judges one cusp's sub-lord, either through the planet whose star it sits in or itself, as the
rule says. Houses joined by "and" are separate groups that must each be hit; "or" is one group.
Where he says failing gives "no" (children, lottery, promotion, going abroad, second marriage) the
engine says NO; elsewhere a failed condition is NOT_SIGNIFIED, not NO. Retrograde and dual-sign
conditions are applied as printed. Extra conditions resting on "connected in any manner" are
reported as not evaluated. Death, lifespan, suicide, murder and the vehicle rule are left out.

**R17. Timing.** Candidate periods are dasa-bhukti-antaras whose three lords all signify a
favourable house (KPR3:8741-8742, 9447-9449). Krishnamurti picks the "strongest" among
significators by judgment; the engine lists every candidate and flags lords that also signify
denial houses. It does not rank them.

## Later authors, walled in `app/kp/later/`

The user chose (2026-11-01) to encode the KP books written after Krishnamurti as a separate,
labelled layer. Nothing else in `app/kp/` imports it (tested). It holds 132 rules from eight
books: *Astro Secrets & KP* 1-6 (M. P. Shanmugam; K. Subramaniam and contributors), *Astrology for
Beginners* (K. Subramaniam), *Sublord Speaks* (K. M. Subramaniam), the KP E-zine 2020-21 (various
authors, ed. Kanak Bosmia), and the Gulbarga yes/no horary rule. Every quote is checked against
its page in `tests/kp/test_later.py`. Every result names its author and book and says "A later
author's rule, not Krishnamurti's; ... not a validated prediction."

**LR1. "Connected to" a house** is read as "signifies" it on the A-D ladder. The authors use the
words interchangeably in their worked examples.

**LR2. House lists.** A hyphenated list ("4-5-11") or an "or" list is one group, any house of
which counts. Houses joined by "and" ("6 and 11") are separate groups, each needed. Same as RH7.

**LR3. Left out.** Death, its manner or timing, lifespan, "life threat", suicide and murder (as
everywhere in this engine); rules resting on an undefined "connection" with a planet or sign
(the vehicle rule AS6:p.1554, diabetes KNR:p.288, deaf-and-dumb KNR:p.226, spouse "connected to
Rahu" EZN:p.491, the Mercury/Jupiter arm of EZN:p.713, the "connected to Saturn" arm of
EZN:p.450); general method passages that name no cusp (AFB:pp.316-322, KNR:p.135, SPK:p.49);
and restatements of Krishnamurti's own rules that add nothing (7th CSL signifying 2, 7 or 11 at
AS6:p.1566, p.1694 and E-zine pp.217, 338, 924).

**LR4. The E-zine's "significator (in the star of the occupant or owner)"** is read as ladder
levels A and C only, the houses the CSL carries through its star lord (kind `signifies_ac`).
Two consequences, both recorded on the rule: at that level a planet carries at most three
houses, so a four-house "and" list could never be met; for the lawsuit rule (EZN:p.909) the
article's own worked example declares the win with the 4th CSL hitting 10 and 11 but not 2 or 6,
so the list is read as one group. The permanent/temporary job rule says "through its Starlord or
Sublord" (EZN:p.709): the star-lord route is levels A and C, the sub-lord route the houses the
CSL's own sub-lord occupies or owns (kind `signifies_ss`).

**LR5. Gulbarga rule.** "If the sub lord of the Horary Number furnished happens to be either the
Moon star lord or the lagna star-lord among the ruling planets ... the affirmative" (AS6:p.1603).
The ruling planets are those of the moment of judgment with the Ascendant then rising, as both
worked examples do ("the Moon star lord of the day", p.1603; "the ruling planets at the moment",
p.1613). Pinned on the p.1603 example: number 245 is Jupiter-Mercury-Moon and the Moon's star lord
that evening was the Moon, so yes.

**LR6. "Strong signification"** (SPK:p.480, the 8th CSL diverting the 8th house's troubles) is
read as ladder levels A or B, the occupant levels, which Krishnamurti ranks strongest.

**LR7. Moral character and punishment are left out**: criminal mind, illicit affair, bad habits,
elopement, timidity (EZN:pp.750, 790, 881), court punishment (EZN:p.521) and criminal
prosecution (AFB:p.912). They are a choice, not a gap in the reading: the user can ask for them.

**Tin Win's House Grouping tables (`app/kp/later/tin_win.py`, added 2026-11-02).** KNR scans
151-172 (printed pp.70-91): all 457 rows transcribed by eye from the scans, because the book's own
OCR of these tables is unusable. Every row and what happened to it is in
`docs/kp/KP_TIN_WIN_ROWS_2026-11-02.md`; 316 are encoded, 141 left out. His method (KNR:p.172):
"if the cuspal sub lord of the house (mentioned in Column 1) is the significator (by occupation or
ownership at the planet, star and sub levels) of the house or houses (mentioned in Column 4), then
the event (shown in Column 3) is promised."

**LR8. "Planet, star and sub levels"** = the houses the CSL itself occupies or owns (levels B, D),
those its star lord occupies or owns (A, C), and those its own sub-lord occupies or owns.

**LR9. House groups.** A comma list needs any one house, as his own example reads "2,7,11" ("signifies
the required marriage houses 2 or 7 or 11", same page). "&" joins groups that must all be met. A
remark that the houses "should operate jointly, not separately" needs two or more. A remark "not
connected to ..." needs none of them. Bracketed houses are not required: he never says what the
brackets mean, and leaving them out can only drop a condition, never add one.

**LR10. Left out:** rows that read the Lagna lord rather than a CSL; alternatives ("or", several "&"
pairs); rows naming a planet, sign, Badhaka or Maraka; starred planet or sign conditions; death and
danger to life (LR3); moral character and punishment (LR7). Column 5 (the timing houses) is listed,
not used.

Pre-flight (`docs/kp/kp_tin_win_rates_2026-11-02.json`, 1,000 random births): the median chart meets
269 of the 310 natal rows, 220 rows fire on over 80% of charts, and opposite rows fire together
(good and ill health on the 1st cusp for 73% of charts; exam success and failure 83%; child and no
child 80%; gain and loss of money 80%). Read his way, a CSL carries most houses at three levels, so
the tables as written do not tell charts apart. They are kept as a faithful record of what he
wrote, not as a reader to trust.

Transcription check (2026-11-02): Column 4 of every row was read a second time by machine OCR from
column crops of the scans at full resolution, independent of the by-eye pass. 449 rows have a
Column 4; the two readings agree on 392. All 57 differences were checked against the scan: each is
an OCR misread ("/" for 7, "50r9" for "5 or 9", dropped brackets) or OCR pairing a cell with the
wrong row where two rows share a subject. No by-eye transcription error was found (spot check:
row 174, "Intelligent thinking", 5,11,3,9,10,1, matches the scan).

Pre-flight (`docs/kp/KP_LATER_PREFLIGHT_2026-11-01.md`): on 2,000 random charts the median chart
fires 28 of the 88 natal later rules; nine rules fire on over 80% of charts.

## What this engine is

A faithful instrument for "what would Krishnamurti's Readers say", with every step shown.
It is **not** a validated predictor. Nothing has been tested against real lives yet; see
`docs/kp/KP_PREFLIGHT_2026-10-31.md` (Reader 3 rules) and `KP_PREFLIGHT_2026-11-01.md` (Reader 4 rules, R18) for checks on ordinary charts.
