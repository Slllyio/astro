# How Raman times events: dasa, bhukti and transit (2026-10-24)

Extracted from Raman's printed books only, by two research agents, at the user's request ("he always
checks the MD, AD and transits; extract how he does it with utmost precision"). Full records with
every line citation and 63 worked cases:
`/mnt/project-files/astro/research/raman-dasa-method.md` (30 cases) and
`/mnt/project-files/astro/research/raman-transit-method.md` (33 cases; the HPA vedha table was
re-read from the page images because the OCR is garbled).

## The order he works in

1. **Promise first, from the birth chart.** A period or a transit cannot give what the chart does
   not promise (AV13:254-260).
2. **Lifespan.** Decide which dasas fall inside the life. A planet whose dasa comes too late acts
   only through its bhukti (HTJAH:1578-1583, 1620-1623; HPA-15:21-37).
3. **Which planets can deliver a house.** The lord, occupants, planets aspecting the house, planets
   aspecting or joining the lord, and from the 2nd house on the lord counted from the Moon, and the
   karaka for some houses (HTJAH:1585-1589). "A planet influences a house if it owns, occupies or
   aspects the said house or its lord" (HTJAH:1628). Doing two of these jobs counts most
   (HTJAH:1624-1628).
4. **Grade of the period for that house.** Both dasa and bhukti lords in the set gives "par
   excellence" (associated) or "ordinary" (not associated, printed only for the 1st house,
   HTJAH:1635-1640). Only the bhukti lord gives "limited". Only the dasa lord gives the weakest grade
   ("feeble" printed for houses 2, 11 and 12; "limited", "nominal" or "small" elsewhere).
   "Association" includes aspect (HTJAH:4321-4323).
5. **Good or bad.** Functional nature for the Lagna, yogakaraka or maraka role (HTJAH:1642-1648),
   dignity, Navamsa and shadbala (HPA-24:80-86), and the other houses the lord owns, occupies or
   aspects. A planet in bhava sandhi gives weak results (HPA-24). The **nakshatra lord is "of
   paramount importance"** (HTJAH:4512-4520).
6. **Bhukti read through the dasa.** The two lords 6/8 or 2/12 from each other is bad (HPA-24:150-153);
   3/11 is "ideal" (HTJAH:14116); mutual kendra or aspect is good; 5th and 9th lords in each other's
   periods are good (HPA-24:155-157); Saturn and Venus in each other's periods damage raja yogas
   (HTJAH:16106).
7. **Rahu and Ketu** give the results of their sign lord, associates, star lord, and act like Saturn
   and Mars respectively (HTJAH:11740-11741, 4477, 12763).
8. **Halves.** No general rule; three applied cases only (NH:10759-10763, 15264-15268, 12259-12263).
   Antara is used ("quite sufficient", HPA-13:603-609); pratyantara is named but never applied.
9. **Transit last, as the trigger.** "Transits are always secondary in importance. They are like
   catalytic agents. All conclusions must be primarily drawn on the basis of Dasha-vichara"
   (HTJAH:11037-11039). Bad dasa plus bad transit makes the event serious (AFB-12:39-53); good dasa
   plus bad transit is "still favourable" (HPA-33:280-292); bad dasa with harmless transits, he
   withholds the verdict (Subhas Bose, NH:14074-14078).
10. **Transit mechanics.** Counted from the natal Moon by whole sign, with the classical good houses
    per planet; the matter affected is the transit sign's house from the Lagna (AV13:394-420).
    Vedha cancels a good or bad result, except Sun-Saturn and Moon-Mercury (HPA-34:141-181). Own
    Ashtakavarga bindus scale the result (fewer than 4 minimum, 4 average, more maximum; AV13:261-288);
    kakshya sub-divisions of 3°45' decide where in the sign it acts (AV13:421-612). Sun and Mars act in
    the first 10° of a sign, Jupiter and Venus in the middle 10°, Rahu throughout.
11. **What his worked charts actually use.** Sade sati and its round (first heavy, second mild, third
    with a maraka dasa fatal; AFB-12:155-176); Saturn crossing natal planets, the Lagna or a natal
    Navamsa sign; Jupiter over the Lagna + 7th-house longitude point for marriage; Mars-Saturn or
    Saturn-Rahu on the Moon sign or the 8th from it. He never works vedha or bindus in NH or HTJAH.
12. **Death timing.** Marakas act only inside the lifespan; the planet joined with the 2nd or 7th lord
    is strongest (HTJAH:783-785); transits come last.

## Points to know before coding

- Badhaka never appears in these books, so it is not Raman doctrine.
- The engine's four-tier bhukti grading is a fair synthesis of step 4, but the books print the full
  split only for the 1st house; the record should say so.
- Unresolved contradictions in the books: HPA-26 scores transits as (benefic - malefic) / 8, while
  the later Ashtakavarga book uses bindus / 8; his marriage rule says lords' longitudes while his
  examples add house longitudes; one HPA example applies a "mitigation" with no stated rule.
- No retrograde rule and no transit orb are printed anywhere; about 10° counts as conjunct (NH:12266).
- Positions are sidereal with Raman's ayanamsa, which the engine now defaults to.

## Next step (not started)

Compare this procedure step by step with the engine's timing layer (`vimshottari.bhukti_tier`,
`timer_set`, the gochara outlook) and list each gap, with its citation, as candidate fixes.
