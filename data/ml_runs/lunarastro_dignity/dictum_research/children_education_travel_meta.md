# Children / Education / Travel + the META-RULES of Vimshottari — verse-level dictums

> Research pass 2026-06-10. Worked from the full **Sanskrit texts with verse
> numbers** (GitHub corpus `Rupali59/Sanskrit-texts`, `/Hora/`): complete BPHS
> (97-ch. recension matching Santhanam's chapter order), Phaladeepika (28 ch.),
> Jataka Parijata (18 ch.), Brihat Jataka. Quotes taken from the Sanskrit verse
> itself (the repo's English glosses drift); translations are close renderings.
> Caveats: verse numbers can shift ±1–3 between editions; Saravali, Sarvartha
> Chintamani, Uttara Kalamrita, Prasna Marga not in corpus — flagged when cited.
> Foundational anchor: **BPHS 46.14** — *kalau viṁśottarī tasmād daśā mukhyā* —
> "in Kali-yuga, Vimshottari is the chief dasha."

## D. META-RULES (govern everything)

### D1. What a dasha lord delivers — the five-factor hierarchy
- **BPHS 47.2–3**: "Dasha results are twofold, general and specific; they accord with the planets' **nature** and with their **placement and condition**; results are to be known according to planetary **strength**." (*sādhāraṇaṁ viśiṣṭañ ca … graha-vīryānusāreṇa*)
- **BPHS 48.1**: "the ancients told results by placement; now I tell results from the mutual relations of the **house lords**" — then 48.2–7 lord-by-lord (D3).
- **Association**: BPHS 47.9 — Sun's dasha joined with 5th lord → *putra-lābham*; 47.10 — with 2nd lord → elephant-rank wealth; with 4th lord → vehicles.
- **PD 20.21**: declare dasha results by combining karaka significations, livelihood, disease, yogas, **lordship and occupancy**. **PD 20.43–44**: planets give results *ātma-bhāvānurūpataḥ* (per houses owned/occupied); planets **related to the dasha lord** reproduce its results in their sub-periods.
- ⇒ `dasha_result(P) = f(karakatva, house_occupied, houses_owned, associations, dignity, strength)`.

### D2. Dignity/strength gating
- **BPHS 47.5–6**: dasha lord in Lagna with benefic aspect, exalted/own/friend's sign → auspicious; in 6/8/12, debilitated, combust, enemy sign → adverse. Repeated per planet 47.7–15.
- **PD 20.30** (graded): "Exaltation → **full** result, trine → **¾**, own → **½**, friend → **¼**, enemy → **little**, debilitation → **zero**; for bad results reverse; a **combust planet equals a debilitated one**."
- Ārohī/avarohī (toward exaltation = better): Uttara Kalamrita dasa section [chapter-level, UNVERIFIED]; cognate PD 20.56 (ārohiṇī/avarohiṇī/madhyā/adhamā dashas).
- ⇒ dignity multiplier {1, ¾, ½, ¼, ε, 0}; combust → 0-class.

### D3. Lordship dictums — dasha of the lord of house N (BPHS 48.2–7)
Lagnesha → fame & health; **2L → distress/death-danger (maraka)**; 3L → bad; **4L → home & land happiness**; **5L → *vidyāptiḥ putra-jaṁ sukham* (learning + children)**; 6L → disease & enemies; **7L → trouble to spouse, death-danger**; 8L → death-fear, wealth loss; **9L → abundant gains, fame**; **10L → honor in the king's assembly**; 11L → obstructed gains; **12L → much suffering**.
- Refinements 48.8–20: malefic in a good house still gives good at dasha start (48.8); 10L joined 5L/9L, kendra-lords joined kona-lords → highly auspicious (48.9–13; lagnesha↔10L exchange → rājya-lābha 48.17–18); even 6/8/12 lords give good if joined a kona lord (48.14); planets in 3/6/11 or with their lords → bad dashas "even if benefics"; planets in maraka places/with maraka lords/in 8th → inauspicious (48.19–20). Closing: "thus infer dasha results from house-lord relations."
- **PD 20.41–49** (quoting Parashara): benefic kendra-lords lose benefice, malefic kendra-lords lose malefice; trikona lords always auspicious; **kendra×trikona yoga fructifies in their mutual dasha–bhukti** (20.42, 20.49); even malefics related to a yogakaraka give yoga results in their bhuktis (20.48); **PD 20.54**: *ārambho rāja-yogasya bhaven māraka-bhuktiṣu* — "a Raja-yoga often *begins* in maraka bhuktis."

### D4. AD position FROM the dasha lord (dāyeśa) — the core meta-formula (~70× in BPHS 52–60)
- Favorable: **BPHS 54.17** — AD lord "in a kendra, trikona or 11th **from the dasha lord**, joined with 9th/10th lords" → fortune. Same formula at 53.19, 54.30/41/57, 55.15/34/54/66/71, 56.15 (*putra-lābha-sukham*), 56.23/45/67, 57.19/30/49/76, 58.31.
- Unfavorable: **BPHS 55.36** — "in the 6th, 12th or 8th **from the dasha lord**, or joined with malefics → evil"; ~35 more instances incl. 54.33 (*tad-bhuktau maraṇaṁ jñeyam*).
- **PD 20.29 (single-verse codification — THE quotable verse):** "Whatever house the bhukti lord occupies **counted from the dasha lord**, it gives the results born of that house; if in the **6th, 12th or 8th from the dasha lord** it produces sorrow, elsewhere happiness."
- AD of dasha lord's enemy: PD 20.28; **JP 18.56** — "in the bhukti of the dasha lord's enemy comes a death-like time."
- Own bhukti: BPHS 47.88a — "in its own bhukti the result is as stated; in other bhuktis according to their strengths."
- ⇒ `AD_tone = pos(AD from MD) ∈ {kendra/kona/11:+, 6/8/12:−}`; AD lord delivers the bhāva-results of its house counted from the MD lord.

### D5. Maraka meta-rule
- BPHS 44.2–4 (2nd & 7th = maraka, 2nd stronger); fallback 44.6–7; **44.8**: "a maraka does not kill in benefic bhuktis even if related; it kills in malefic bhuktis even if unrelated"; 44.9 Saturn override; 44.19 (6L dasha; ADs of 6/8/12 lords). AD refrain ≈60×: *dvitīya-dyūna-nāthe tu apamṛtyur bhaviṣyati* + remedy. **PD 20.40** condenses.

### D6. WHEN within a dasha results ripen — three classical rules
1. **Drekkana rule — BPHS 47.3–4**: planet in first drekkana (0–10°) of a sign → results at dasha **start**; middle → **middle**; third → **end**; **retrograde → reversed**.
2. **JP 18.82**: dasha beginning → results of the **house** occupied; middle → of the **sign**; end → of the **aspects**. (Malefic/benefic elaboration JP 18.57–58.)
3. **PD 20.33**: pṛṣṭhodaya signs → fruit in **last** third; ubhayodaya → middle; śīrṣodaya → first.
- Dasha-entry chart: JP 18.14–15 (dasha begun with lord in lagna/friend's varga/with benefics is auspicious; Moon's position at dasha start counted from the dasha lord seeds the period).
- Phase exemplars: BPHS 47.42–43 (Rahu: trouble→prosperity→loss), PD 19.16 (Rahu in Virgo/Scorpio/Pisces: fine dasha, *daśāvasāne sakalasya nāśaḥ* — at the end, loss of everything).

### D7. Dasha–gochara samanvaya — CLASSICAL, verse-attested
- **PD 20.34**: "Whatever house the **dasha lord occupies in transit** while exalted/friendly, **that house it nourishes at that time** — provided it was strong at birth."
- PD 20.35: dasha lord weak at birth destroys whatever bhāva it transits. PD 20.36: results good when the **transit Moon** reaches the dasha lord's exaltation sign or 3/6/10/11/trine/7th **from the dasha lord**. PD 20.37: dasha lord transiting debilitation/combustion/enemy → distress; own/exaltation/retro → happiness. **PD 20.38**: "When the **Sun or Jupiter in transit** enters the exaltation/own sign of a benefic dasha lord, **its promised result fructifies**." PD 20.60–62: judge each dasha year by the lord's transit from natal Moon.
- The strict symmetric "no event unless BOTH promise" is a 20th-c. hardening (Raman/KP); classically transit is **modulator and trigger** of dasha promise.

### D8. Sandhi / chhidra dangers
- **JP 18.27**: "the dasha of a planet at a **sign-junction** inflicts grief and disease; of one having traversed the full 30° gives death-like results." (Also JP 18.5.)
- **PD 15.13–14**: even an exalted planet "gives no result standing in a sandhi"; full at bhāva-madhya, zero at junction, proportional between.
- **MD-to-MD junction danger ("dasha-chhidra"): no BPHS/PD/JP verse found.** Seeds: PD 20.39 (Rahu-joined planet troubles "especially at dasha-end"), PD 19.16. Full chhidra doctrine = later/modern (Phalita Martanda; K.N. Rao school). FLAG.

### D9. Strength scaling & two-lordship resolution
- **BPHS 24.145–148**: judge by strength; a planet owning two houses — contradictory results cancel, different results both obtain; "full strength → full result, half → half, weak → quarter."
- **PD 15.11**: of two owned signs the **mūlatrikoṇa** gives the chief result; first-encountered sign fruits in the dasha's first half, the other in the second.

### D10. Bhavat-bhavam family
- **PD 15.20**: "treating the bhāva under judgment as the lagna, declare the results of the twelve houses counted from it"; PD 15.21–24 extend to karakas (father from the Sun's houses, etc.). Timing application = PD 20.29 (D4). BPHS 16.27–29 (children from 5th-from-Jupiter and 5th-from-5th); JP 13.49.

### D11. Rahu/Ketu proxy rule
- **PD 20.39**: "Rahu gives the good and bad results **of the planet it is conjoined with**." BPHS 47.35–36 give nodes' exaltation/mūlatrikoṇa, so dignity machinery applies.

### D12. Graha-maturity ages (Jup 16, Sun 22, Moon 24, Ven 25, Mars 28, Merc 32, Sat 36, Rahu 42, Ketu 48)
- **UNSOURCED IN CLASSICS** — no verse in BPHS/PD/JP/BJ. Modern oral tradition (C.S. Patel / Sanjay Rath lineage); sites even disagree on Sun (21 vs 22). Classical substitute: **BPHS 16.18–23 fixed-age verses** (son at 32–33 / 30 or 36 / 40; child-death at 32; grief at 56) and JP ch. 9 year-by-year results.

## A. CHILDREN (santāna)

### A1. Promise
- **BPHS 16.1–2**: lagnesha in 5th / 5L in 5th / 5L in kendra-trikona → full child-happiness; **5L in 6/8/12 → childlessness**; 16.3: 5L combust/weak → "no child is born, or born it surely dies."
- **PD 12.1**: children assured when Lagna lord, Moon, 5L and Jupiter well placed; 1L↔5L exchange → putra-siddhi. **PD 12.2** (denial): 5th **from Lagna, Jupiter AND Moon** all afflicted → "children are in no way born."
- Jupiter = putra-kāraka: PD 15.16–17; BPHS 16.19.
- **D7**: BPHS 7.2 "judge children and grandchildren from the Saptāṁśa" (computation 6.10). NOTE: no explicit "D7-lord dasha" timing verse — derived tradition, FLAG.

### A2. Timing — childbirth in the dasha/AD of…
- **PD 12.27 (master verse)**: "birth of children occurs in the **dashas and ADs of planets occupying the 5th, aspecting the 5th, and of the 5th lord**" (MD derived from lords of Lagna, 7th, 5th). PD 12.25 adds: dashas of **L1, L7, 5L, Jupiter**; and when **Jupiter transits the 5th house or the sign/navamsa of the 5th lord**.
- **PD 12.28 (navamsa-dispositor verse)**: "obtaining of a child in the dasha or AD of the strong 5L or Jupiter, **or of the lords of the signs and navāṁśas occupied by them**."
- **JP 13.49**: 5th from Jupiter, Moon and Lagna child-giving — son in the **dasha-bhukti of its lord**; also dasha of the nakshatra-lord from 5L+7L longitudes summed; and dashas of planets joined/aspecting them. JP 13.14: 5L in kendra/trikona in benefic sign → child early in life.
- BPHS instances: 48.4; 47.9; **52.52** (Venus AD in Sun MD: *vivāhaḥ putra-sambhavaḥ*), 56.15, 54.3/49/51/58, 56.47/53, 58.27/38, 59.21, 60.61; pratyantara 61.16.
- Transit triggers: PD 12.26; **PD 12.29**: "birth of a son when **Jupiter transits the trines of the sign/navamsa of the 5th lord**"; PD 12.30.

### A3. Age-fixed fruition (BPHS 16.18–23)
Son at 32–33 (Jup in 5th + lord with Venus); at 30/36 (5L kendra with kāraka); at 40 (Jup in 9th…). Dark: death of son at 32 (Rahu in 5th + afflictions); losses at 33/36/40; grief through sons at 56.

### A4. Denial, delay, dosha & curses
- BPHS 16.4 (kāka-bandhyā), 16.5–7, 16.9/16.11 (adopted children), 24.54/24.60; PD 12.3 (alpa-suta signs in 5th), 12.6–9.
- **Curses**: BPHS ch. 83 (Pūrvajanma-śāpa, 111 vv.); PD 12.19–24 (occupant of 5th identifies curse: Rahu=serpent, Ketu=Brahmin, Sun=ancestors…), remedies 12.16–18; Santāna-tithi PD 12.15 (5×Moon−Sun).
- **Fertility**: PD 12.14 — Beeja-sphuṭa (Sun+Ven+Jup) / Kshetra-sphuṭa (Moon+Mars+Jup); odd sign & odd navamsa → potent.

## B. EDUCATION (vidyā)

- **BPHS 48.4**: 5L dasha → *vidyāptiḥ* — "attainment of learning" (cleanest classical timing verse).
- 4L: BPHS 24.37 (*vidyā-guṇa-vibhūṣitaḥ*), 24.43; 2nd house covers vidyā per PD 1.10. Counter: BPHS 24.137 — 12L in 5th → "bereft of children and learning."
- Kārakas: Mercury = vidyā/buddhi (PD 2.4, 15.15); Jupiter = jñāna (PD 15.16).
- Dasha/AD: BPHS 47.22 (strong Moon: *vidyā-lābham*), 47.62–63 & 47.69 (Mercury); **57.8** (Mercury AD in Saturn MD, Merc in kendra/trikona → *vidyā-lābhaṁ dhanāgamam*); 55.31, 58.1/8/28 (*śāstra-vidyā-pariśramam*), 56.66 (Venus AD in Jup MD: *vidyā-vivāha-kāryāṇi*); negative 55.73 (*vidyā-hāniḥ*). Pratyantara/sūkṣma: 61.8/16/40/42, 62.40/48/64, 63.6/40/63.
- **JP 18.110**: Jupiter AD in Jupiter MD → "attains learning and science"; 18.73, 18.78, 18.139, 18.153.
- Sarvartha Chintamani ch. 5 (intelligence/education) [chapter-level, UNVERIFIED].

## C. TRAVEL / FOREIGN

### C1. House anchors (BPHS ch. 11)
- **11.8**: 7th → *adhva-prayāṇam* — **travel on roads** (+ commerce, wife).
- **11.10**: 9th → *tīrtha-yātrādikam* — **pilgrimage/long sacred journeys**.
- **11.11**: 10th → *pravāsasya* — **residence away from home**.
- **12th = foreign settlement is NOT in BPHS ch. 11** (12th = expenditure, 11.13); indirect link 24.137 (12L → wandering to tīrthas). FLAG as late convention.

### C2. Movable signs → wandering
- **Brihat Jataka 12.11** (Rajju yoga, all planets in chara signs): "devoted to dwelling in foreign lands, fond of the road"; **BPHS 35.7, 35.18** (*aṭana-priyāḥ … para-deśa-svāsthya-bhāginaḥ*); BJ 24.8; BJ 5.1/5.7.

### C3. Dasha/AD dictums
- MD: 47.13 (afflicted Sun: *pravāsaḥ*), 47.30 (strong Mars: position **in a foreign land**), **47.40 (Rahu: *yavana-prabhu-sanmānam* — honor from a foreign lord — the classical seed of "Rahu dasha → foreign")**, 47.50, 47.57 (Saturn in 6/8/12: wandering abroad), 47.66, 47.73, 47.76; PD 19.13 (Saturn: sudden exile), 19.17 (Ketu: banishment), 19.12 (Venus: sea voyages).
- AD (dāyeśa-relative): 53.19 (kendra/kona/3/11 from MD lord → pilgrimage fruits); 55.66 (→ royal honor in foreign land); 54.11, 56.75, 57.10/19, 58.31/32 (*videśa-dhana-lābha-kṛt*), 58.69 (*tīrtha-vāsam* when in 8/12 from lagna or dāyeśa), 52.61, 54.31/40/66, 55.63, 56.26/62, 57.18/60/64/76, 59.19/33/41 (death while wandering abroad)/62/78, 60.26/50; sūkṣma 62.13/16/39/45/67, 63.18/68; 52.14 ("he will go from country to country").
- JP 18.96 (Rahu/Rahu: painful roaming), **18.98 (Saturn AD in Rahu MD: residence in a distant land)**, 18.101, 18.113, 18.147, 18.152 (*deśa-tyāgam*), 18.73.
- The modern package "12L+9L+7L+Rahu = foreign settlement" — components classical, package modern. FLAG.

## Verdict table

| Claim | Verdict |
|---|---|
| AD kendra/trikona vs 6-8-12 from MD lord | **Classical** — BPHS 52–60 passim; PD 20.29 |
| Maraka 2/7 in dasha/AD | **Classical** — BPHS 44.2–9 |
| Begin/middle/end-of-dasha rules | **Classical** — BPHS 47.3–4; JP 18.82; PD 20.33 |
| Dasha + transit | **Classical in substance** — PD 20.34–38, 12.25–30; strict AND = modern |
| Dasha-sandhi/chhidra | **Partially classical** — JP 18.27, PD 15.13–14; full doctrine modern |
| Graha maturity ages | **Unsourced** — modern oral tradition |
| D7-lord dasha for childbirth | **Derived** — D7 promise is BPHS 7.2; dasha use is inference |
| 12th house = foreign settlement | **Late convention** — BPHS: travel=7th, pilgrimage=9th, pravāsa=10th |

Corpus: GitHub `Rupali59/Sanskrit-texts` /Hora/ (BPHS chs. 11,16,24,32,44,46,47,48,51–63; PD 12,15,19,20; JP 13,18; Brihat Jataka).
