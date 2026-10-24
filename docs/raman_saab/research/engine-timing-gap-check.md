# Engine timing layer vs Raman's timing method: gap check (2026-10-24)

Repo `/home/claude/astro` at HEAD 9ff238a. Reference: `docs/raman_saab/RAMAN_TIMING_METHOD_2026-10-24.md`
(12 steps), `docs/raman_saab/research/raman-dasa-method.md`, `docs/raman_saab/research/raman-transit-method.md`,
with key lines re-read in `data/knowledge_library/sources/`. Nothing in `app/` or `tests/` was modified.
Scratch probes: `/tmp/claude-0/-home-claude/0462ad3d-edef-5079-8a7a-8785976d2ea4/scratchpad/timing/`.

## 0. Bottom line

- **No timing gap moves a scored verdict.** Timing is metadata-only in the verdict path:
  `house_template._event_timing` (app/raman_saab/judges/house_template.py:1688-1745) returns the
  verdict "byte-for-byte unchanged". No judge imports `transits`. The golden ratchet cannot see
  any fix below. What these gaps touch: the report's timing sections (Life-narrative, life
  chapters, per-house tier line, Current transits, Gochara outlook, affliction calendar, marriage
  and children monographs, longevity/maraka section, synthesis insights). They also touch
  rectification scoring, which reads `active_houses` grades (rectification/scoring.py:16, 219-223).
- **The core machinery is sound.** The four-tier `bhukti_tier`, the gochara good-house table, the
  bindu proportion, kakshya transits and the eightfold dasa kakshya all match Raman. No badhaka
  appears anywhere (grep is empty), which is correct.
- **The largest fidelity gaps are in what the grading is fed, not in the grading.** The timer
  set does not follow Raman's printed per-house factor lists. The grade is computed on a union
  with "auxiliary" houses that has no citation. Nodes get only one of Raman's four result
  channels. The nakshatra lord, which Raman calls "of paramount importance", is never used for
  timing. Lifespan gating is missing.
- **Counts (28 rows):** 12 steps: 0 faithful, 10 different, 2 missing. 16 sub-rules: 3 faithful,
  8 different, 5 missing. Separately, 12 items are IMPLEMENTED BUT NOT RAMAN (section 3).

## 1. The 12 steps

| # | Raman's step (cite) | Status | Engine evidence | What differs |
|---|---|---|---|---|
| 1 | Promise first: a period or transit cannot give what the chart does not promise (AV13:254-260) | DIFFERENTLY | reading_timeline.py:79-89 carries the unchanged natal verdict on every activated house; `plain_bhukti_summary` detailed_report.py:1892 | Dasa side is faithful: the natal promise travels with each activation and is never re-judged. Transit side is missing: no gochara row is gated by natal promise. The Gochara outlook and affliction calendar list transit windows with no promise check. |
| 2 | Lifespan: dasas outside the span act only as bhuktis (HTJAH:1578-1583, 1620-1623 "Venus can give the effects of first house only as minor lord"; HPA-15:21-37) | MISSING | `active_houses` vimshottari.py:508-536, `significator_dasha_windows` :457-486 (fixed 120-yr horizon), marriage givers marriage_timing.py:242-248 | No fructification, yoga or marriage-giver read asks whether the MD falls inside the span. Partial only for death: `death_window` (:397-426) anchors to the ayurdaya span, and theme_synthesis discloses windows past the span (theme_synthesis.py:2325-2347). |
| 3 | Which planets deliver a house: the printed factor lists per house (HTJAH:1585-1589, 2582-2585, 3525-3527, 4308-4311, 5318-5320, 6272-6274, 8268-8271, 12735-12738, 14071-14074, 16391-16394, 17730-17735); two functions count most (HTJAH:1624-1628) | DIFFERENTLY | `timer_set` vimshottari.py:205-238; `timer_roles` :250-294 | (a) A karaka is added for **every** house (:221, default "Sun"). Raman prints none for H1, H2, H10 or H11, and prints **the Sun** for H9 where the engine adds Jupiter. (b) The lord counted from the Moon is added for H1 (:233); Raman adds it only from H2 on. (c) H3: Raman adds the planets associated with or aspecting the karaka Mars (HTJAH:3525-3526); this is missing. (d) Two-function primacy: role tags are shown but never ranked. |
| 4 | Grade the period: par excellence / ordinary / limited / feeble; association includes aspect (HTJAH:1592-1596, 1635-1640, 2588-2599, 4321-4323) | DIFFERENTLY | `bhukti_tier` :595-614 (faithful on its own); `graded_buckets` detailed_report.py:1741; `active_houses` :522-534 | (a) The tier is computed on `timer_set(H) ∪ timer_set(aux)`, where `_EVENT_AUX_HOUSES` = {2:11, 11:2, 9:12, 12:9} (:299, :524-525). Raman grades each house on its own list. Probe: canonical chart, Moon/Moon on 2026-10-24: H2 grades par excellence only because Moon is an H11 timer; Moon is in neither MD nor AD role for H2's own set. (b) An MD lord's own bhukti counts as "associated" with itself, so it grades par excellence. Raman's H1 text says "the sub-period of **another**" (HTJAH:1635). (c) A legacy two-grade label (`ActiveHouse.grade`: "par_excellence" when both lords influence, regardless of association) is still read by render.py:155-227, sitting.py:264, plainspoken.py:501, synthesis.py:206 and rectification. So a bhukti Raman would call "ordinary" is printed as "par excellence" on those surfaces. (d) The `bhukti_tier` docstring presents the ordinary/par-excellence split as printed for every house. It is printed only for H1, and H3/H7 print "limited" for tier 3. CLAUDE.md locks the uniform scheme, so this is a documentation gap, not a code change. |
| 5 | Good or bad: functional role, yogakaraka/maraka, dignity, Navamsa, shadbala, other houses owned (HTJAH:1642-1648; HPA-24:80-86); sandhi weakens (HPA-24:98-100); nakshatra lord paramount (HTJAH:4512-4520) | DIFFERENTLY | `lord_quality` :565-577 (shadbala, dignity, combustion, vargottama); chapter narrative names functional nature detailed_report.py:3851-3853; R7 residential strength synthesis_rules.py:679-705 | Strength descriptors exist. Missing pieces: the nakshatra lord; Navamsa disposition beyond vargottama; maraka/yogakaraka role applied per bhukti; rule (iv), "results in relation to the other houses the lord owns, occupies, aspects"; sandhi for the AD lord. |
| 6 | Bhukti through dasa: 6/8 and 2/12 bad (HPA-24:150-153); 3/11 "ideal" (HTJAH:14116); kendra and aspect good; 5th/9th lords' mutual periods good (HPA-24:155-157); Saturn-Venus mutual periods fatal to raja yogas (HTJAH:16104-16111) | DIFFERENTLY | `_chk_n4` synthesis_rules.py:1070-1084 (cited to BPHS, not Raman); `_chk_r2` :585 | N4 reads 6/8/12 as adverse but the **2nd** as "neutral", and 3/11 as "neutral" (Raman: ideal). No 5/9-lord rule. No Saturn-Venus rule. |
| 7 | Nodes give results of sign lord, associate, star lord, and act like Saturn/Mars (HTJAH:8566, 11740-11741, 4477-4478, 12763; NH:12250-12252) | DIFFERENTLY | `timer_set` :234-237; chapter narrative detailed_report.py:3860-3880 | Only the sign dispositor is used. Conjoined planet, nakshatra lord, *Sanivad Rahu / Kujavad Ketu* and maraka delegation (HTJAH:11195-11206) are absent. The test file names the case this costs: "h10_05 Napoleon's Rahu needs the deeper Kujavad-Ketu constellation-chaining" (tests/raman_saab/test_vimshottari.py:149-150). |
| 8 | Halves (three applied cases only); antara used, "quite sufficient" (HPA-13:603-609); antara judged by position from MD/AD lords (HTJAH:6635-6650) | DIFFERENTLY | `pratyantars` :120-141 (named "pratyantar"; this is Raman's antara level); shown for the current bhukti, detailed_report.py:2586 | Antara dates are computed and shown, but no antara is judged: there is no 12th/2-12 relation from the MD and AD lords. Halves are absent, which is acceptable since Raman gives no general rule; if added, add only as the three applied criteria. |
| 9 | Transit last, as trigger. Bad dasa + bad transit = serious (AFB12:39-53). Good dasa + bad transit = still favourable (HPA33:280-292). Bad dasa + benign transit = withhold (NH:14074-14078). Transits "irrespective of directional influences" untenable (AV13:60-74) | DIFFERENTLY | SYN_R8 synthesis_rules.py:497-502, `_chk_r8` :730-738; confluence tables detailed_report.py:2052-2135; WeatherWindow framing theme_synthesis.py:431-450 | Subordination is honoured: transits never move a verdict or tier, and PREC-6 is quoted. Missing: the three-way combination, and any link from a transit to the house the running dasa activates. The "Slow-mover gochara" windows (theme_synthesis.py:2052-2089) and adverse transit windows are listed with **no dasa gate**, the reading Raman calls untenable. |
| 10 | Transit mechanics: from natal Moon; matter = transit sign's house from Lagna (AV13:394-420); vedha with two exempt pairs (HPA34:141-181); bindus scale (AV13:261-288); kakshya (AV13:421-612); sign parts (HPA34:83-85; AFB12:197-201) | DIFFERENTLY | transits.py:102-150 | Mostly faithful (see section 2). Deviations: the Mercury 10th vedha cell, node vedha, missing reverse vedha, missing sign parts. |
| 11 | What his worked charts use: sade sati + round; Saturn over natal planets, Lagna, natal Navamsa signs; Jupiter over the Lagna+7th point; Mars-Saturn / Saturn-Rahu on the Moon sign or the 8th from it (AFB12:155-176; NH, HTJAH cases) | MISSING (partial) | sade sati phases detailed_report.py:2527-2583; Saturn-on-natal-Saturn trine :2455-2496 | Sade sati is dated but has no round, and the text claims "no Sade-Sati x Moon result doctrine is on record" (detailed_report.py:2514) although AFB12:169-176 prints the round doctrine. The rest is absent (rows T7, T8 below). |
| 12 | Death: marakas only inside span; associate of 2nd/7th lord strongest, lords least (HTJAH:783-785); transits last | DIFFERENTLY | `maraka_points` primitives/maraka.py:124-229; `maraka_set` vimshottari.py:302-338; `death_window` :397-426; Saturn signal detailed_report.py:2455 | All primary marakas weigh 3 (vimshottari.py:170-178), so lords are ranked equal to associates, the opposite of HTJAH:783-785. Tertiary Saturn is only conjunct a 2nd/7th lord; Raman's "conjunction, association or aspect with the Maraka" is broader (HTJAH:793-794). "3rd/8th lord associated with 2nd/7th lord" is missing (HTJAH:790-791). No Navamsa marakas, no maraka delegation to nodes, no Saturn-over-8th/12th-lord-houses rule (HTJAH:10996-10999). The Saturn signal checks Rasi only, not Rasi **and** Amsa (HTJAH:11226-11229). |

## 2. Transit and dasa sub-rules

| Sub-rule (cite) | Status | Engine evidence | Note |
|---|---|---|---|
| T1 Good houses from the Moon per planet (HPA34 table, AFB12:219ff) | FAITHFUL | transits.py:31-41 | All 9 rows match, nodes 3/6/11. The report snapshot shows only Jupiter, Saturn, Rahu, Ketu and Mars (`SIGNIFICANT`, :66), but vedha checks all nine. |
| T2 Vedha pairs; Sun-Saturn and Moon-Mercury exempt (HPA34:141-181, PDF pp. 257-258) | DIFFERENTLY | transits.py:46-60, `_vedha` :141-150 | (a) **Mercury 10th: engine 8, Raman prints 7** (OCR at HPA34 also reads "5-3-9-1-7-12"; the classical Phaladeepika value is 8). (b) Rahu/Ketu are given Saturn's vedha points (:54-55); Raman gives none (NOT RAMAN). (c) Reverse vedha is missing: an evil transit is cancelled when another planet occupies its paired good house (HPA34:161-164, "Similarly the Vedhasthanas must be considered for all the planets"). The report text "vedha applies to favourable stations only" (detailed_report.py:1809) contradicts this. Exemptions are correct. |
| T3 Bindu scaling: <4 minimum, 4 optimum, >4 maximum; bindus/8; bad transits mitigated; before-reduction counts (AV13:261-288, 415-417) | FAITHFUL | `bav_proportion` transits.py:137; adverse windows with bindus detailed_report.py:2605-2633; `_chk_r11` synthesis_rules.py:775 | Minor gap: AV13 rule 5 (own or exaltation transited sign raises the result) is absent. |
| T4 Kakshya (AV13:421-512; ASP-12 dasa division) | FAITHFUL | kakshya.py; kakshya_timing.py; transits.py:129-131 | The order follows Raman's own table. Minor gaps: rule 3 (four or more planets in donor kakshyas) and rule 6 (kakshya lord's friendship) are absent. |
| T5 Sign-part activation: Sun/Mars first 10°, Jupiter/Venus middle 10°, Rahu whole sign (HPA34:83-85; AFB12:197-201) | MISSING | none | Nothing for the Moon, Mercury or Saturn, correctly; Raman is silent on them. |
| T6 Sade sati rounds: 1st heavy, 2nd mild, 3rd with maraka dasa fatal; dasa strength decides severity; SAV >30 mitigates (AFB12:155-176; HPA33:283-292; AV13:613-617) | MISSING | `sade_sati` transits.py:153-164; `_sade_sati_phases` detailed_report.py:2527 | Only the nearest episode is dated. There is no round count, no running-dasa strength qualifier and no SAV check. |
| T7 Saturn over natal points: planets, Lagna point, natal Navamsa signs of the dasa lords, 8th/12th lord houses (HTJ-U:6892, 10996-10999, 11226-11229; NH:10797-10800, 13784-13793) | DIFFERENTLY | `_maraka_saturn_confluences` detailed_report.py:2455; `_chk_r9` synthesis_rules.py:741 | Only Saturn over the trines of natal Saturn's rasi, Rasi half only, inside the death window. Every other target is absent. |
| T8 Jupiter over Lagna + 7th point for marriage (HTJ-U:8389-8411; practice adds the **bhava** longitudes, HTJ-U:18296-18299, 18424-18427; Jupiter's aspect accepted, case 10) | DIFFERENTLY | marriage_timing.py:310-321; Jupiter 7th-from-Moon windows monographs.py:271-276 | Uses the lords' longitudes (the stated rule) only. It names signs, gives no dated Jupiter windows over them, and does not test aspect. The bhava-longitude version Raman actually worked is absent. |
| T9 Nakshatra lord "of paramount importance", can veto (HTJAH:4512-4520; NH:15257-15260); tara of the AD lord (HPA-24:144-148) | MISSING | only the positions-table column, detailed_report.py:1831 | Never used in tiering, period quality, maraka or node results. |
| T10 Bhukti lord 6/8, 2/12, 3/11 from the dasa lord | DIFFERENTLY | synthesis_rules.py:1070-1084 | See step 6. |
| T11 Saturn-Venus mutual periods damage raja yogas unless the yoga is powerful (HTJAH:16104-16111) | MISSING | none | |
| T12 Nodes give dispositor/associate results | DIFFERENTLY | vimshottari.py:234-237 | See step 7. |
| T13 Bhava sandhi weakens a dasa (HPA-24:98-100; 3HC:892-896) | DIFFERENTLY | `_chk_r7` synthesis_rules.py:679-705 (GBB-1:203 residential strength) | Covers the running MD lord only, as a descriptor. Not applied to the AD lord, the tier or the yoga-timing rows. |
| T14 Lifespan gating of dasas | MISSING | see step 2 | Partial for death only. |
| T15 Maraka order | DIFFERENTLY | see step 12 | |
| T16 Dasa first, transit only triggers | DIFFERENTLY | see step 9 | |

## 3. Implemented but not Raman (no Raman citation, or contradicting his print)

1. **Aux-house union in fructification grading** (vimshottari.py:299, 524-525; detailed_report.py:1767-1785). There is no Raman citation for grading H2 on the H11 set (or H9 on H12). It inflates grades, as the probe in step 4 shows.
2. **Karaka added for H1/H2/H10/H11, and Jupiter as H9 karaka** (vimshottari.py:221, doctrine/karakas.py:18-31). Raman's printed lists differ (step 3).
3. **H1 lord-from-Moon** (vimshottari.py:233). Raman starts factor (f) at H2.
4. **Node vedha** (transits.py:54-55). Raman gives none.
5. **Mercury 10th vedha = 8** (transits.py:50). This is the classical value; Raman prints 7.
6. **Saturn-in-10th "Mrityu Yoga" as tertiary maraka** (vimshottari.py:331-334). No citation in code; not found in the extracted maraka doctrine.
7. **Self-bhukti counted as "associated"** (vimshottari.py:587-591 via `graded_buckets`). Contrary to "the sub-period of another" (HTJAH:1635).
8. **Legacy two-grade `ActiveHouse.grade`** (vimshottari.py:494-536), labelling "par_excellence" without the association test.
9. **Bhukti relation cited to BPHS** (SYN_N4) where Raman has his own, different reading (2/12 bad, 3/11 ideal).
10. **Laghu Parashari matrices** (SYN_N1/N2), **Patel AV dasa seat/antardasha** (SYN_N7), **Patel Shodhyapinda Saturn clock** (doctrine/av_pinda_timing.py) and **Phaladeepika transit void** (SYN_N11). All are labelled classical and disclosed, so this is acceptable as disclosure. But Raman has his own versions to cite first: AV11 rule 35 for the Shodhyapinda clock, which Raman also tested with Jupiter; AV13 rule 5 for the sign-dignity transit modifier.
11. **Death-window band widths** 5/8/10 years (vimshottari.py:394). An engine construct with no citation.
12. **Dasa x transit "confluence"** (MD/AD lord in its own favourable gochara, detailed_report.py:2030-2078). An engine construct. The nearest Raman case is NH:6929-6936 (MD lord Saturn transiting the 7th). It should be labelled as an engine overlap, not as Raman's rule.

Also found: `av_pinda_timing.bhava_saturn_markers` computes transit Saturn in **Lahiri** (av_pinda_timing.py:136) while the natal grid is cast in Raman's ayanamsa, the engine default. The frames are mixed, so the nakshatra can flip near a boundary (~1.5° offset). It also sets the global sidereal mode without restoring it; this is benign today because the global default is Lahiri.

## 4. Ranking (fidelity importance x effort)

Fidelity: H = changes what the timing layer says for most charts, or contradicts a "paramount"/explicit Raman rule. M = a cited Raman rule absent on some charts. L = a refinement. Effort: S < 1 day, M 1-3 days, L more.

| Rank | Gap | Fidelity | Effort | Scored verdicts? |
|---|---|---|---|---|
| 1 | Timer set per printed lists, plus full node channels (steps 3, 7) | H | S | No (report timing, rectification) |
| 2 | Grade each house on its own set; self-bhukti; retire legacy grade labels (step 4) | H | S-M | No |
| 3 | Nakshatra lord paramountcy, plus AD tara (T9) | H | M | No |
| 4 | Lifespan gating of MD/AD roles (T14) | H | M | No |
| 5 | Bhukti-from-dasa per Raman, 5/9 lords, Saturn-Venus (T10, T11) | M | S | No |
| 6 | Maraka ordering, Saturn tertiary breadth, Amsa half, node delegation (T15) | M | M | No |
| 7 | Sade sati round, dasa qualifier, SAV >30 (T6) | M | S | No |
| 8 | Vedha: reverse vedha, no node vedha, report sentence, Mercury cell (T2) | M | S (Mercury needs a user decision) | No |
| 9 | Dasa gate on standalone transit windows; combination matrix (T16) | M | M | No |
| 10 | Saturn over natal points and dasa-lord Navamsa signs; Mars-Saturn / Saturn-Rahu on Moon/8th (T7) | M | M | No |
| 11 | Marriage sum by bhava longitudes, dated Jupiter windows, aspect (T8) | M | S-M | No |
| 12 | Sign-part activation (T5) | L | S | No |
| 13 | av_pinda ayanamsa frame; re-cite to AV11 | L | S | No |
| 14 | Antara judged by position from MD/AD (step 8) | L | S-M | No |
| 15 | Sandhi for AD lord and yoga rows (T13) | L | S | No |

## 5. Proposed fix list

Each fix is additive to the report per REPORT COMPLETENESS (nothing removed or hidden). Each
needs its own doctrine review. Items marked (USER) touch a CLAUDE.md lock or need a ruling.

1. **(USER) Raman-printed timer set.** In `timer_set`/`timer_roles`, add a karaka only for H3,
   H4, H5, H6, H7, H9 (= **Sun**) and H12. Start "lord from the Moon" at H2. For H3 add the
   associates and aspecters of Mars. Cite HTJAH:1585-1589, 2582-2585, 3522-3527, 4308-4311,
   5318-5320, 6272-6274, 8268-8271, 12735-12738, 14071-14074, 16391-16394, 17730-17735.
   CLAUDE.md's lock forbids *narrowing to own/occupy/aspect*; this is not that, but it edits a
   locked definition, so it needs sign-off. **Scratch measurement**
   (`.../scratchpad/timing/raman_timer.py`): on the 10 pinned non-death events in
   `test_vimshottari.py`, the Raman-list set keeps **10/10**, with sets the same size or smaller.
2. **Full node channels** (with fix 1): a node joins a house's set when its sign lord, a
   conjoined planet, its nakshatra lord, or its dictum planet (Saturn for Rahu, Mars for Ketu) is
   in the set (HTJAH:8566, 11740-11741, 4477-4478, 12763). The same probe **recovers the
   documented Napoleon edge (HTJAH-II.h10_05 Rahu)**, which the current set misses.
3. **Grade on the house's own set.** Compute `bhukti_tier` from `timer_set(H)` only. Keep the
   2/11, 9/12 union as a separately labelled "allied house" note. When MD == AD, grade by the
   "another" wording: report "same lord; Raman's association test does not apply" rather than par
   excellence (HTJAH:1635). Replace reads of `ActiveHouse.grade` with `bhukti_tier`.
   Rectification scoring must be re-measured after this.
4. **Nakshatra-lord layer.** For each MD/AD lord, report its star lord, that lord's houses and
   maraka status, and a veto/boost note when the star lord contradicts the house delivery
   (HTJAH:4512-4520; NH:15257-15260, 14584-14586). Add the AD lord's tara from the janma
   nakshatra (3rd/5th/7th = trial in a malefic MD, HPA-24:144-148; HTJAH:1140-1145).
5. **Lifespan gate.** Using the existing ayurdaya span, tag each planet "MD within span" or
   "acts only as bhukti lord". Apply it to tier rows, yoga timing, marriage-giver ranking and
   maraka choice (HTJAH:1578-1583, 1620-1623; HPA-15:21-37; 3HC:970-972).
6. **Raman's bhukti relation.** Add a Raman-cited rule beside SYN_N4: 6/8 and 2/12 adverse
   (HPA-24:150-153); 3/11 ideal (HTJAH:14116); mutual kendra or aspect favourable
   (HTJAH:14120-14122, 16102-16103); 5th/9th lords in each other's periods good
   (HPA-24:155-157); Saturn-Venus mutual periods flagged against fired raja yogas, with the
   "powerful yoga survives" proviso (HTJAH:16104-16111). The 2nd and 7th from the MD lord are
   also read as maraka from the major lord (NH:13797-13798, 12230-12232).
7. **Maraka order.** Split the primary tier into associate > occupant > lord (HTJAH:783-785).
   Record HPA-15:39-52's 2nd-over-7th ordering as the variant. Widen tertiary Saturn to
   association or aspect with any maraka (HTJAH:793-794). Add the 3rd/8th lord associated with a
   2nd/7th lord (HTJAH:790-791). Add the Amsa half of the Saturn signal (HTJAH:11226-11229) and
   delegation to the node in a late maraka's sign (HTJAH:11195-11206). Add Saturn transiting the
   8th/12th lord's houses or their trines, degrading to "misfortune" outside a maraka dasa
   (HTJAH:10988-10999).
8. **Sade sati round.** Count episodes since birth; label 1st (most results), 2nd (mild),
   3rd ("with a maraka dasa" only). Attach the running-dasa strength qualifier and the SAV >30
   check on the 12th/1st/2nd from the Moon (AFB12:155-176; HPA33:283-292; AV13:613-617). Correct
   the "no doctrine on record" sentence (detailed_report.py:2514).
9. **Vedha.** Add reverse vedha (HPA34:161-166). Drop vedha points for transiting Rahu/Ketu and
   label node-caused obstruction "unspecified by Raman". Fix the "favourable stations only"
   sentence (detailed_report.py:1809). (USER) Mercury 10th: Raman prints 7 (PDF p. 258, OCR
   agrees), the classical value is 8. The directive says Raman wins; a misprint is possible, so
   record the choice either way.
10. **Dasa gate on transits.** On every standalone transit window, add which running MD/AD
    activates the transit sign's house from Lagna (AV13:394-420), and a combination label:
    "bad dasa + bad transit = serious" (AFB12:39-53), "good dasa + bad transit = still favourable"
    (HPA33:280-292), "bad dasa + benign transit = withheld" (NH:14074-14078). Add, never remove.
11. **Saturn/Rahu/Jupiter over natal points.** Saturn or Rahu over natal rasi **and** Navamsa
    signs of the MD/AD lords, marakas, Lagna and Moon (NH:13784-13793; HTJ-U:6892, 11227-11229).
    Mars-Saturn or Saturn-Rahu conjunction or mutual aspect on the Moon sign or the 8th from it as
    malefic, and on the 11th as favourable (HTJ-U:6716-6736; NH:10212, 12264-12269, 12795-12797).
    Use the ~10° conjunction hint (NH:12266) and disclose that no orb is printed for natal points.
12. **Marriage point.** Compute both the stated lords' sum (HTJ-U:8389-8411) and the practised
    Lagna-bhava + 7th-bhava sum (HTJ-U:18296-18299, 18424-18427). Date Jupiter's transits over each
    sign and its trines, and its aspects on the natal 7th and on the sum sign's lord (case at
    HTJ-U:18284-18299).
13. **Sign-part activation.** Flag whether Sun/Mars are in the first 10° and Jupiter/Venus in
    the middle 10° of the transited sign; Rahu throughout (HPA34:83-85; AFB12:197-201). Nothing for
    the Moon, Mercury or Saturn.
14. **av_pinda frame.** Cast transit Saturn in the natal chart's ayanamsa via `sidereal_mode`.
    Add Raman's own AV11 rule 35 citation and his Jupiter-transit observation beside Patel.
15. **Antara judgment.** For the current bhukti's antaras, report each antara lord's position
    from the MD and AD lords (12th, 2/12) and its maraka/8th/karaka role (HTJAH:6635-6650,
    4476-4483).
16. **Sandhi for the AD lord.** Extend the R7 residential-strength line to the bhukti lord and to
    yoga-timing rows (HPA-24:98-100; 3HC:892-896).

## 6. Verification notes

- Book lines re-read directly: HTJAH:1584-1648, 2580-2600, 3522-3535, 4306-4324, 5306-5322,
  6272-6290, 8268-8285, 12733-12750, 14068-14083, 16390-16406, 17730-17748, 780-800,
  10985-11000; HPA34:140-232 (vedha OCR, Mercury row "5-3-9-1-7-12").
- Probe `probe.py` (canonical Bangalore chart, Raman ayanamsa): over 72 bhuktis x 12 houses,
  33% grade par excellence, 23% ordinary, 16% limited, 15% feeble, 13% none (the grading is
  broad by design). Average timer-set size is 6.5.
- No test was run against modified code, because nothing was modified. Fixes 1-3 will break
  pinned expectations in tests/raman_saab/test_vimshottari.py (timer_roles == timer_set stays
  true) and in tests of `active_houses`/report tiers. Those pins must be updated deliberately.
