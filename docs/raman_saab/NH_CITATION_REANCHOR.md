# NH citation re-anchoring — proposal (2026-10-13, NOT APPLIED)

Status: **proposal for review. No fixture, rule, or code line has been edited.**
Machine-readable map: `nh_citation_reanchor_map.json` (per record: old, new, method, both texts).

## What changed on 2026-08-23 ~02:10

| Book | Live vs `sources_backup_20260823` | Line numbers |
|---|---|---|
| HTJAH-I | LF normalisation + 1 front-matter line (`scraped_at`) | **unchanged** |
| HTJAH-II | LF + title/book/heading strings in front matter | **unchanged** |
| 3HC (`three_hundred_combinations_raman`) | LF + `scraped_at` | **unchanged** |
| **NH** | re-OCR: 14,272 -> 17,062 lines, 8,392 lines differ | **shifted throughout** |
| GBB ch.9 | 339 -> 337 lines | shifted by -2 near the end |

The rewrite WAS registered: `d945a84` (2026-08-23 02:34) re-locked `source_lock.json` to the live
files, stating the citations "point at precisely the text they were verified against, zero
remapping". That holds for HTJAH/3HC/HPA/etc. It does **not** hold for NH: the lock hashes
*files*, never what a cited line *says*, so it stayed green while NH citations shifted.

## (1) Measurement — fixture `tests/fixtures/raman_goldens.jsonl` (325 citations, all in `citations`)

Resolution test = cited line falls inside the record's own chart presentation block
(`golden_pipeline/sources.chart_header`, header + birth-date / "No. N.- NAME" disambiguation).

| Book | n | in own chart, **backup** | in own chart, **live** |
|---|---|---|---|
| NH | 153 | 152 (+1: chart_38 Ford, header undetected in backup but line is Ford's positions) | **0** |
| HTJAH-I | 76 | 19 | 19 (identical) |
| HTJAH-II | 96 | 50 | 50 (identical) |

HTJAH "in own block" is low in BOTH files because many verdict citations sit in Raman's
discussion chapters, not under the chart header — that is the citation style, not staleness.
Line text at every HTJAH citation is byte-identical (modulo CRLF) between backup and live.

## (2) Proposed NH re-anchoring (153 citations, 60 records)

- **146** auto: the backup line's text (>=5, usually 9-15 words, extended over following lines)
  found uniquely in the live file, preferring the record's own live chart block.
- **6** hand-verified by reading both texts (OCR drift `11 th`->`1 1 th`, `282D`->`282`;
  one 4-word fragment; one auto match that had picked another chart — chart_76).
- **1 unresolvable — needs your call:** `NH.chart_31` (George Bernard Shaw) `NH:5445` cites his
  Planetary Positions line. **The live OCR dropped Shaw's header, birth details and positions
  entirely**; his section now opens at line 7280 ("Balance of the Moon Dasa"). Options:
  (a) point at 7280 (nearest surviving text of the chart), (b) leave `NH:5445` and record it as
  a known-dead anchor, (c) restore the dropped lines into the live source (changes the NH lock).
- Every remapped line lands inside its own chart's live block (Shaw excepted: no live header).
- Example: `NH.chart_38` Henry Ford `NH:6361` -> `NH:8480` (Ford's planetary positions, block 8475-8617).

Full per-record table: see the JSON map (or the table appended below).

## Scope beyond the fixture — other consumers of NH / changed-book line numbers

| Consumer | Stale? | Detail |
|---|---|---|
| Engine `Citation(...)` objects (rules, synthesis, yogas, lookups, walled anchors) — 1,423 via `source_lock.iter_citations()` | **2 of 1,321** in rewritten books | `SYN_R14` `Citation("NH", 9580)` -> **12777** (Bhavartha Ratnakara Libra/Saturn dictum; live 9580 is Pius XII's positions). `SYN` `Citation("GBB-9", 332)` -> **330** ("134. Concluding Remarks"). All 1,319 others (HTJAH-I/II, HPA, 3HC, ASP, MUHURTHA, PRASNA, VARSHA, JAIMINI) read identical text. |
| `app/raman_saab/yoga_deep_read.py` `NH_EXAMPLES` (13 lines, rendered via `passage()`) | **13 of 13** | Not enumerated by `iter_citations()`, so the lock cannot see them. All remap by content (e.g. `NH:3099`->`4238` Akbar's Sasa/Malavya/Ruchaka). Table below. |
| `tests/fixtures/golden_attention.json`, `analogy_index.json` | copies (120 NH each) | Derived from the fixture by `build_golden_attention.py` / `build_analogy_index.py`; the analogy citations are printed in the report (`detailed_report.py:4549`, `report_html.py:2647`). Regenerate after the fixture fix. |
## Fixture NH citations — proposed old -> new (153)

auto content match: 146; manual: 6; unresolvable: 1; new line outside own live chart block (excl. chart_31, whose live header is gone): 0

| record | old | new | method | old text (backup) | new text (live) |
|---|---|---|---|---|---|
| NH.chart_25 | NH:4777 | NH:6391 | content11 | and warm-heartedness. His poetic greatness is due to the position of | and warm-heartedness. His poetic greatness is due to the position of |
| NH.chart_25 | NH:4787 | NH:6401 | content12 | was so keenly aware. The Kahala Yoga was also responsible for his | was so keenly aware. The Kahala Yoga was also responsible for his |
| NH.chart_25 | NH:4801 | NH:6416 | content14 | Dasa Saturn's Bhukti. Saturn is a yogakaraka and is in the 7th or | Dasa Saturn's Bhukti. Saturn is a yogakaraka and is in the 7th or |
| NH.chart_26 | NH:4859 | NH:6521 | content9 | debilitation.    These combinations no doubt gave him a robust | debilitation. These combinations no doubt gave him a robust |
| NH.chart_26 | NH:4872 | NH:6532 | content14 | yogakaraka and he is exalted in the 2nd or house of speech while the | yogakaraka and he is exalted in the 2nd or house of speech while the |
| NH.chart_26 | NH:4900 | NH:6561 | content13 | statesman or as a ruler. The 10th house is rendered null and void | statesman or as a ruler. The 10th house is rendered null and void |
| NH.chart_26 | NH:4976 | NH:6636 | content5 | Jupiter, Mercury or unadulterated Rahu. All the malefics aspect the 9th | Jupiter, Mercury or unadulterated Rahu. All the maiefics aspect the 9th |
| NH.chart_28 | NH:5143 | NH:6894 | content12 | Lagna Saturn is exalted in the 9th being aspected powerfully by Jupiter. | Lagna Saturn is exalted in the 9th being aspected powerfully by Jupiter. |
| NH.chart_28 | NH:5156 | NH:6907 | content12 | yogakaraka for Aquarius, is in the second exalted. Venus is not subject | yogakaraka for Aquarius, is in the second exalted. Venus is not subject |
| NH.chart_28 | NH:5161 | NH:6912 | content10 | accounts for the complete absence of passions and sensual feelings | accounts for the complete absence of passions and sensual feelings |
| NH.chart_32 | NH:5543 | NH:7419 | content13 | nature. The lord of Lagna Venus is exalted and free from any affliction | nature. The lord of Lagna Venus is exalted and free from any affliction |
| NH.chart_32 | NH:5552 | NH:7427 | content13 | Mars occupies the 2nd or house of speech, the house being his own, | Mars occupies the 2nd or house of speech, the house being his own, |
| NH.chart_32 | NH:5555 | NH:7430 | content12 | making him at the same time a bit short-tempered. The Moon is | making him at the same time a bit short-tempered. The Moon is |
| NH.chart_32 | NH:5566 | NH:7441 | content10 | classes of people. Saturn the yogakaraka occupies the 10th house | classes of people. Saturn the yogakaraka occupies the 10th house |
| NH.chart_33 | NH:5655 | NH:7580 | content12 | Special Features.—The Lagna is strong as Venus, its lord, is in | Special Features. — The Lagna is strong as Venus, its lord, is in |
| NH.chart_33 | NH:5687 | NH:7612 | content13 | the 6th from the Moon is  mainly responsible for this.   Bose's Paper | the 6th from the Moon is mainly responsible for this. Bose's Paper |
| NH.chart_33 | NH:5700 | NH:7625 | content13 | shade of vanity of learning. The house of profession is very well fortified | shade of vanity of learning. The house of profession is very well fortified |
| NH.chart_33 | NH:5702 | NH:7627 | content13 | contributed not a little to his inventive genius. Jupiter in the 2nd house | contributed not a little to his inventive genius. Jupiter in the 2nd house |
| NH.chart_34 | NH:5770 | NH:7749 | content13 | his own way. Yogakaraka Venus, the planet of sex, is actually in the | his own way. Yogakaraka Venus, the planet of sex, is actually in the |
| NH.chart_34 | NH:5777 | NH:7756 | content11 | in the 12th aspected by Saturn is an unfortunate combination which | in the 12th aspected by Saturn is an unfortunate combination which |
| NH.chart_34 | NH:5804 | NH:7781 | content13 | Ellis himself was not molested. Jupiter is in the constellation of the 6th | Ellis himself was not molested. Jupiter is in the constellation of the 6th |
| NH.chart_35 | NH:5860 | NH:7887 | content11 | was a poet, painter, politician and philosopher. The position of Jupiter | was a poet, painter, politician and philosopher. The position of Jupiter |
| NH.chart_35 | NH:5870 | NH:7897 | content13 | and the 8th. Domestically the poet was not happy, on account of the | and the 8th. Domestically the poet was not happy, on account of the |
| NH.chart_35 | NH:5877 | NH:7904 | content14 | exaltation of the divine planet Jupiter as Lagna lord in the 5th or house | exaltation of the divine planet Jupiter as Lagna lord in the 5th or house |
| NH.chart_35 | NH:5890 | NH:7915 | content11 | combinations reveal the mystic quality of his writings. The affliction of | combinations reveal the mystic quality of his writings. The affliction of |
| NH.chart_35 | NH:5913 | NH:7939 | content13 | Lagna is aspected by exalted Jupiter lord of the 10th or house of | Lagna is aspected by exalted Jupiter lord of the 10th or house of |
| NH.chart_36 | NH:6013 | NH:8084 | content15 | Lagna. There is no other benefic aspect on this. This gave him a lot of | Lagna. There is no other benefic aspect on this. This gave him a lot of |
| NH.chart_36 | NH:6026 | NH:8097 | content10 | conceptions. The 7th house ruling  sensual passions is free from | conceptions. The 7th house ruling sensual passions is free from |
| NH.chart_36 | NH:6046 | NH:8117 | content9 | 8th with Ayushkaraka,  did not give him good longevity. | 8th with Ayushkaraka, did not give him good longevity. |
| NH.chart_36 | NH:6125 | NH:8195 | content13 | in the 12th is a powerful factor while the dispositions of Jupiter and | in the 12th is a powerful factor while the dispositions of Jupiter and |
| NH.chart_36 | NH:6127 | NH:8197 | content9 | successful ascetic. As Jupiter is in Karmasthana, Vivekananda became | successful ascetic. As Jupiter is in Karmasthana, Vivekananda became |
| NH.chart_37 | NH:6224 | NH:8342 | content12 | this horoscope that they account for the immense wealth and power the | this horoscope that they account for the immense wealth and power the |
| NH.chart_37 | NH:6233 | NH:8351 | content14 | Yoga. Even in the Navamsa, the 5th house is spoiled with the result the | Yoga. Even in the Navamsa, the 5th house is spoiled with the result the |
| NH.chart_37 | NH:6241 | NH:8359 | content17 | being exalted in Rasi As a result, he lost his first wife and had to marry a | being exalted in Rasi As a result, he lost his first wife and had to marry a |
| NH.chart_37 | NH:6327 | NH:8445 | content12 | always shown where the influences exercised by the 2nd, 1st, 9th, 10th | always shown where the influences exercised by the 2nd, 1st, 9th, 10th |
| NH.chart_37 | NH:6331 | NH:8449 | content11 | and Jupiter and Mercury and Saturn coupled with the yogas already | and Jupiter and Mercury and Saturn coupled with the yogas already |
| NH.chart_39 | NH:6561 | NH:8720 | content13 | 5th from Karakamsa and that Venus and the Sun are associated in the | 5th from Karakamsa and that Venus and the Sun are associated in the |
| NH.chart_39 | NH:6572 | NH:8731 | content13 | strength to make the native what he was. The house of children is | strength to make the native what he was. The house of children is |
| NH.chart_39 | NH:6583 | NH:8743 | content10 | The second   event that profoundly influenced the native was his | The second event that profoundly influenced the native was his |
| NH.chart_39 | NH:6606 | NH:8764 | content15 | with his elevation to the Bench. Rahu's position in the 6th from Lagna is | with his elevation to the Bench. Rahu’s position in the 6th from Lagna is |
| NH.chart_39 | NH:6614 | NH:8772 | content14 | Jupiter owns the 8th from Lagna and occupies the 7th from the Moon. In | Jupiter owns the 8th from Lagna and occupies the 7th from the Moon. In |
| NH.chart_42 | NH:7020 | NH:9325 | manual: 'The blending of martian' (1-line fragment, too short to auto-match) | The blending of martian | The blending of martian |
| NH.chart_42 | NH:7028 | NH:9331 | content10 | Moon. The subject's remarkable organising capacity and powers of | Moon. The subject's remarkable organising capacity and powers of |
| NH.chart_42 | NH:7034 | NH:9337 | content9 | from Chandra Lagna. These combinations conferred on him legal | from Chandra Lagna. These combinations conferred on him legal |
| NH.chart_42 | NH:7037 | NH:9340 | content13 | practice. Lord of the 2nd Jupiter aspecting the 2nd and Mars the 2nd | practice. Lord of the 2nd Jupiter aspecting the 2nd and Mars the 2nd |
| NH.chart_43 | NH:7124 | NH:9465 | content10 | Balance of Ketu Dasa at birth :    Years 3-2-22. Special   Features.— | Balance of Ketu Dasa at birth : Years 3-2-22. Special Features. — |
| NH.chart_43 | NH:7144 | NH:9483 | content11 | Mars, Jupiter and Venus influencing the house of education and culture | Mars, Jupiter and Venus influencing the house of education and culture |
| NH.chart_43 | NH:7158 | NH:9497 | content15 | lord of the 9th Jupiter is exalted and is within 3° from the rising degree. | lord of the 9th Jupiter is exalted and is within 3° from the rising degree. |
| NH.chart_45 | NH:7352 | NH:9788 | content13 | observed. Lord of Lagna ideally placed and not involved in any sort of | observed. Lord of Lagna ideally placed and not involved in any sort of |
| NH.chart_45 | NH:7372 | NH:9808 | content14 | simplify his life. Mark the situation of Jupiter, the planet of wisdom, in the | simplify his life. Mark the situation of Jupiter, the planet of wisdom, in the |
| NH.chart_45 | NH:7375 | NH:9811 | content14 | scientist as well as saint. Mark the ideal disposition of the Sun in the | scientist as well as saint. Mark the ideal disposition of the Sun in the |
| NH.chart_45 | NH:7389 | NH:9823 | content11 | being made. Dhanakaraka is well placed but Dhanadhipati (2nd lord) is | being made. Dhanakaraka is well placed but Dhanadhipati (2nd lord) is |
| NH.chart_45 | NH:7421 | NH:9856 | content15 | with a price of 20,000 marks on his head. That a malefic like Mars | with a price of 20,000 marks on his head. That a malefic like Mars |
| NH.chart_45 | NH:7437 | NH:9872 | content14 | Jupiter Dasa commenced. It will be seen that Jupiter is a maraka as he | Jupiter Dasa commenced. It will be seen that Jupiter is a maraka as he |
| NH.chart_47 | NH:7605 | NH:10131 | content9 | The horoscope becomes significant by the Chandramangala Yoga in | The horoscope becomes significant by the Chandramangala Yoga in |
| NH.chart_47 | NH:7622 | NH:10148 | content17 | The Sun, lord of Lagna, who is also the planet of vitality, is in the 6th or | The Sun, lord of Lagna, who is also the planet of vitality, is in the 6th or |
| NH.chart_47 | NH:7629 | NH:10155 | content13 | enabled Roosevelt to reach the highest position in life that is possible in | enabled Roosevelt to reach the highest position in life that is possible in |
| NH.chart_47 | NH:7637 | NH:10164 | content12 | American life. Saturn Dasa commenced in 1904. Saturn, lord of the 7th, | American life. Saturn Dasa commenced in 1904. Saturn, lord of the 7th, |
| NH.chart_47 | NH:7694 | NH:10221 | content14 | rights of man. Saturn, the planet of democracy in the 9th house, is an | rights of man. Saturn, the planet of democracy in the 9th house, is an |
| NH.chart_51 | NH:8151 | NH:10887 | content17 | the Sun ruling political power is in the 8th or a house of death, This may expla | the Sun ruling political power is in the 8th or a house of death, This may expla |
| NH.chart_51 | NH:8152 | NH:10888 | content14 | the fact that Truman reached power through a death. Jupiter exalted is actually  | the fact that Truman reached power through a death. Jupiter exalted is actually  |
| NH.chart_51 | NH:8157 | NH:10893 | content14 | augmented by the disposition of Venus, lord of the 2nd and 9th—wealth and | augmented by the disposition of Venus, lord of the 2nd and 9th — wealth and |
| NH.chart_51 | NH:8181 | NH:10918 | content11 | opinion are the exchange of houses between the 9th and 10th | opinion are the exchange of houses between the 9th and 10th |
| NH.chart_53 | NH:8410 | NH:11245 | content10 | contented. The checkered financial career is due to the obviously | contented. The checkered financial career is due to the obviously |
| NH.chart_53 | NH:8417 | NH:11252 | content11 | appropriate directional influences. The 4th lord Jupiter is actually in the | appropriate directional influences. The 4th lord Jupiter is actually in the |
| NH.chart_53 | NH:8430 | NH:11263 | content12 | Kalatrabhava is well fortified as Kalatrakaraka Venus is in his own sign | Kalatrabhava is well fortified as Kalatrakaraka Venus is in his own sign |
| NH.chart_53 | NH:8432 | NH:11265 | content12 | private life. The horoscope belongs to the category of purnayu or long | private life. The horoscope belongs to the category of purnayu or long |
| NH.chart_53 | NH:8434 | NH:11267 | content13 | Moon being exalted. It is the 10th or Karma-sthana that is of the | Moon being exalted. It is the 10th or Karma-sthana that is of the |
| NH.chart_54 | NH:8563 | NH:11442 | content11 | The ascendant or Lagna is weak as it occupied by debilitated | The ascendant or Lagna is weak as it occupied by debilitated |
| NH.chart_54 | NH:8583 | NH:11464 | content13 | obsessed with curious fancies. Lord of the 4th Venus in the 4th Bhava | obsessed with curious fancies. Lord of the 4th Venus in the 4th Bhava |
| NH.chart_54 | NH:8585 | NH:11466 | content11 | Houses of finance (2nd), fortune (9th) and profession (10th) have all | Houses of finance (2nd), fortune (9th) and profession (10th) have all |
| NH.chart_54 | NH:8586 | NH:11467 | content15 | been afflicted in some way or other. The Sun as lord of the 2nd and | been afflicted in some way or other. The Sun as lord of the 2nd and |
| NH.chart_54 | NH:8588 | NH:11469 | content12 | association with Rahu. Lord of the 10th Mars is neecha in Lagna, | association with Rahu. Lord of the 10th Mars is neecha in Lagna, |
| NH.chart_54 | NH:8595 | NH:11476 | content11 | of Rahu Dasa, misfortune dogged him. The 7th house is equally | of Rahu Dasa, misfortune dogged him. The 7th house is equally |
| NH.chart_55 | NH:8663 | NH:11591 | content12 | Rajayoga  justifying   his being the ruler of a premier  Indian State.    The | Rajayoga justifying his being the ruler of a premier Indian State. The |
| NH.chart_55 | NH:8664 | NH:11592 | content15 | Nizam is noted for his fabulous wealth  and  this  is  shown  by a number of | Nizam is noted for his fabulous wealth and this is shown by a number of |
| NH.chart_55 | NH:8688 | NH:11616 | content12 | The major lord owns the 3rd and 6th houses and occupies the | The major lord owns the 3rd and 6th houses and occupies the |
| NH.chart_55 | NH:8720 | NH:11649 | content10 | religious  faith,   calm   resignation   and serenity, the affliction of Lagna | religious faith, calm resignation and serenity, the affliction of Lagna |
| NH.chart_55 | NH:8731 | NH:11658 | content14 | view of Kalatrabhava. Mark the fact that the 7th lord Mars is subject to | view of Kalatrabhava. Mark the fact that the 7th lord Mars is subject to |
| NH.chart_57 | NH:8939 | NH:11961 | content10 | Special Features.—Lagna lord the Moon occupying the tenth a | Special Features. — Lagna lord the Moon occupying the tenth a |
| NH.chart_57 | NH:8984 | NH:12004 | content14 | aim of life. The 7th house is considerably afflicted as lord of the 7th | aim of life. The 7th house is considerably afflicted as lord of the 7th |
| NH.chart_57 | NH:8988 | NH:12008 | content14 | 5th house is equally afflicted as the lord Mars is with Rahu and Saturn. | 5th house is equally afflicted as the lord Mars is with Rahu and Saturn. |
| NH.chart_57 | NH:8992 | NH:12013 | content9 | Important Events.—The Moon and Mars aspecting the 4th | Important Events. — The Moon and Mars aspecting the 4th |
| NH.chart_57 | NH:9004 | NH:12026 | content15 | India. The important position of Jupiter is to be noted. He is lord of the | India. The important position of Jupiter is to be noted. He is lord of the |
| NH.chart_57 | NH:9048 | NH:12070 | content10 | lord neechabhanga in Lagna is another Rajayoga. Amala Yoga, Virinchi | lord neechabhanga in Lagna is another Rajayoga. Amala Yoga , Virinchi |
| NH.chart_61 | NH:9559 | NH:12755 | content12 | of natural hastiness of temper and impetuosity. Mars, lord of the 2nd | of natural hastiness of temper and impetuosity. Mars, lord of the 2nd |
| NH.chart_61 | NH:9563 | NH:12759 | content11 | combination is the complete absence of malefic aspects either on Mars | combination is the complete absence of malefic aspects either on Mars |
| NH.chart_61 | NH:9565 | NH:12761 | content11 | fortified by the powerful aspect of Jupiter on the 10th, Saturn | fortified by the powerful aspect of Jupiter on the 10th, Saturn |
| NH.chart_62 | NH:9666 | NH:12913 | content13 | fortune. The 10th lord Jupiter, who is the natural Dhanakaraka, is in the | fortune. The 10th lord Jupiter, who is the natural Dhanakaraka, is in the |
| NH.chart_62 | NH:9668 | NH:12915 | content14 | Mercury's disposition is ideal while Venus exalted in the 10th in a kendra | Mercury's disposition is ideal while Venus exalted in the 10th in a kendra |
| NH.chart_62 | NH:9680 | NH:12925 | content23 | th—all ideal combinations denoting "immense wealth". | th — all ideal combinations denoting "immense wealth". |
| NH.chart_62 | NH:9694 | NH:12941 | content13 | Mark the affliction of the Kalatra Bhave. 7th lord Jupiter is in the | Mark the affliction of the Kalatra Bhave. 7th lord Jupiter is in the |
| NH.chart_63 | NH:9763 | NH:13052 | content9 | subject to a powerful Papakarthari Yoga being hemmed inbetween | subject to a powerful Papakarthari Yoga being hemmed inbetween |
| NH.chart_63 | NH:9775 | NH:13064 | content10 | association of Venus, yogakaraka for Capricorn Lagna, with the Sun, | association of Venus, yogakaraka for Capricorn Lagna, with the Sun, |
| NH.chart_63 | NH:9777 | NH:13066 | content12 | man of impulsiveness and emotions. The Dhana Yoga is well marked by | man of impulsiveness and emotions. The Dhana Yoga is well marked by |
| NH.chart_65 | NH:10004 | NH:13387 | content12 | common sign, and the lord Mercury is exalted in Lagna itself thus | common sign, and the lord Mercury is exalted in Lagna itself thus |
| NH.chart_65 | NH:10038 | NH:13420 | content11 | for a superficial observer the Dhanabhava is not at all strong. | for a superficial observer the Dhanabhava is not at all strong. |
| NH.chart_65 | NH:10049 | NH:13429 | content13 | equally afflicted so that the married life cannot be as happy as one | equally afflicted so that the married life cannot be as happy as one |
| NH.chart_65 | NH:10064 | NH:13445 | content11 | important inasmuch as the family expanded by the birth of children | important inasmuch as the family expanded by the birth of children |
| NH.chart_65 | NH:10070 | NH:13452 | content11 | from the Moon—the 10th house is immensely   fortified   by being | from the Moon — the 10th house is immensely fortified by being |
| NH.chart_67 | NH:10251 | NH:13736 | content13 | Jupiter is exalted and in conjunction with the Moon in his own house. | Jupiter is exalted and in conjunction with the Moon in his own house. |
| NH.chart_67 | NH:10281 | NH:13763 | content10 | influence denotes property, wealth and prosperity, a happy home and | influence denotes property, wealth and prosperity, a happy home and |
| NH.chart_67 | NH:10291 | NH:13773 | content14 | native's fifth   Bhava is fairly well  disposed  while the hand of Mars may | native's fifth Bhava is fairly well disposed while the hand of Mars may |
| NH.chart_67 | NH:10292 | NH:13774 | content15 | cause an abortion or two to the wife. Mars aspecting the 7th  and the 7th | cause an abortion or two to the wife. Mars aspecting the 7th and the 7th |
| NH.chart_67 | NH:10337 | NH:13818 | content5 | (wealth) Saturn is exalted in the 11th (gains). In the 2nd are placed the | (wealth) Saturn is exalted in the 1 1th (gains). In the 2nd are placed the |
| NH.chart_67 | NH:10355 | NH:13836 | manual: OCR '11 th' -> '1 1 th', same sentence | in the 11 th promises gain through co-operation. Since Saturn is | in the 1 1 th promises gain through co-operation. Since Saturn is |
| NH.chart_67 | NH:10376 | NH:13857 | content13 | Yoga. Jupiter, lord of Lagna, powerfully aspects the Sun, lord of the 9th | Yoga. Jupiter, lord of Lagna, powerfully aspects the Sun, lord of the 9th |
| NH.chart_69 | NH:10565 | NH:14141 | content11 | The Lagna being Cancer, a movable sign occupied by Mars and | The Lagna being Cancer, a movable sign occupied by Mars and |
| NH.chart_69 | NH:10574 | NH:14148 | content14 | long. The Moon, karaka for the mind, is in Leo in association with Jupiter | long. The Moon, karaka for the mind, is in Leo in association with Jupiter |
| NH.chart_69 | NH:10579 | NH:14153 | content11 | finds expression in sublimal ways. Venus, the planet of poetry, who | finds expression in sublimal ways. Venus, the planet of poetry, who |
| NH.chart_69 | NH:10598 | NH:14172 | content13 | influence of Jupiter. On the contrary, the 7th house has the influences of | influence of Jupiter. On the contrary, the 7th house has the influences of |
| NH.chart_71 | NH:10829 | NH:14497 | content14 | that is subjected to certain afflictions. The Lagna lord is in his own sign | that is subjected to certain afflictions. The Lagna lord is in his own sign |
| NH.chart_71 | NH:10842 | NH:14508 | content12 | temper. The 9th house from Chandra Lagna has some of the most | temper. The 9th house from Chandra Lagna has some of the most |
| NH.chart_71 | NH:10856 | NH:14522 | content11 | Mark Bhratrukaraka Mars in the 3rd and Bhratrusthana from the Moon | Mark Bhratrukaraka Mars in the 3rd and Bhratrusthana from the Moon |
| NH.chart_71 | NH:10888 | NH:14554 | content12 | Powerful afflictions to the lord of the 7th and Venus—the Kalatrakaraka. | Powerful afflictions to the lord of the 7th and Venus — the Kalatrakaraka. |
| NH.chart_71 | NH:10892 | NH:14558 | content10 | idealistic and imaginative. The house of intelligence is well fortified. | idealistic and imaginative. The house of intelligence is well fortified. |
| NH.chart_75 | NH:11313 | NH:15157 | manual: old line was the printed page number '397' after the 'Ex-King Farouk' ru | 397 |  |
| NH.chart_75 | NH:11351 | NH:15193 | content12 | observe that whilst Jupiter's exaltation in the 10th would no doubt | observe that whilst Jupiter's exaltation in the 10th would no doubt |
| NH.chart_75 | NH:11354 | NH:15196 | content10 | aspect, involving the 7th and 8th houses, emphasises the unhappiness | aspect, involving the 7th and 8th houses, emphasises the unhappiness |
| NH.chart_75 | NH:11385 | NH:15229 | content12 | controversy. Besides, lord of the 9th is spoilt by his association, rather | controversy. Besides, lord of the 9th is spoilt by his association, rather |
| NH.chart_18 | NH:3587 | NH:4840 | content10 | Planetary Positions.—The Sun 323° 56' ; the Moon 178° 48' ; | Planetary Positions. — The Sun 323° 56' ; the Moon 178° 48' ; |
| NH.chart_20 | NH:4043 | NH:5386 | content9 | Planetary Positions.—The Sun 136°; the Moon 323°; Mars | Planetary Positions. — The Sun 136°; the Moon 323°; Mars |
| NH.chart_21 | NH:4216 | NH:5604 | content11 | Planetary Positions.-The Sun 229° 54' ; the Moon 24° 24' ; Mars | Planetary Positions. -The Sun 229° 54' ; the Moon 24° 24' ; Mars |
| NH.chart_23 | NH:4499 | NH:5974 | content11 | Planetary Positions.—The Sun 23° 9' ; the Moon 96° 41'; Mars | Planetary Positions. — The Sun 23° 9' ; the Moon 96° 41'; Mars |
| NH.chart_24 | NH:4629 | NH:6159 | content11 | Planetary Positions.-The Sun 304° 6'; the Moon 275° 20'; Mars | Planetary Positions.-The Sun 304° 6'; the Moon 275° 20'; Mars |
| NH.chart_27 | NH:5031 | NH:6692 | content11 | Planetary Positions.—The Sun 42° 13'; the Moon 43° 40' ; Mars | Planetary Positions. — The Sun 42° 13’; the Moon 43° 40' ; Mars |
| NH.chart_29 | NH:5226 | NH:6979 | content5 | Planetary Positions.—The Sun 301° 12'; the Moon 18° 29' ; Mars | Planetary Positions. — The Sun 301 0 12'; the Moon 18° 29' ; Mars |
| NH.chart_30 | NH:5322 | NH:7123 | content11 | Planetary Positions.—The Sun 99° 55' ; the Moon 349° 15'; Mars | Planetary Positions. — The Sun 99° 55' ; the Moon 349° 15'; Mars |
| NH.chart_31 | NH:5445 | **—** | TEXT ABSENT IN LIVE: Shaw's header, birth details and planetary positions were d | Planetary Positions.—The Sun 103° 36'; the Moon 44° |  |
| NH.chart_38 | NH:6361 | NH:8480 | content11 | Planetary Positions.-The Sun 106° 34' ; the Moon 290° 12'; Mars | Planetary Positions.-The Sun 106° 34’ ; the Moon 290° 12'; Mars |
| NH.chart_40 | NH:6675 | NH:8839 | content10 | Planetary Positions.—The Sun 157° 52' ; the Moon 300° 3' ; | Planetary Positions. — The Sun 157° 52' ; the Moon 300° 3' ; |
| NH.chart_41 | NH:6870 | NH:9080 | content10 | Planetary Positions.—The Sun 168° 22' ; the Moon 120° 10'; | Planetary Positions. — The Sun 168° 22' ; the Moon 120° 10'; |
| NH.chart_44 | NH:7237 | NH:9578 | content11 | Planetary Positions.—The Sun 321° 6'; the Moon 32° 42'; Mars | Planetary Positions. — The Sun 321 ° 6'; the Moon 32° 42'; Mars |
| NH.chart_46 | NH:7465 | NH:9901 | content11 | Planetary Positions.—The Sun 257° 4' ; the Moon 89° 58' ; Mars | Planetary Positions. — The Sun 257° 4' ; the Moon 89° 58’ ; Mars |
| NH.chart_49 | NH:7859 | NH:10452 | content11 | Planetary Positions.—The Sun 46° 10'; the Moon 304° 28'; Mars | Planetary Positions. — The Sun 46° 10'; the Moon 304° 28'; Mars |
| NH.chart_52 | NH:8239 | NH:10978 | content11 | Planetary Positions.—The Sun 53° 9'; the Moon 182° 56'; Mars | Planetary Positions. — The Sun 53° 9'; the Moon 182° 56'; Mars |
| NH.chart_56 | NH:8743 | NH:11672 | content10 | Planetary Positions.—The Sun 113° 38' ; the Moon 332° 46'; | Planetary Positions. — The Sun 113° 38' ; the Moon 332° 46'; |
| NH.chart_59 | NH:9245 | NH:12312 | manual: Planetary Positions line, OCR '211' -> '21 1' | Planetary Positions —The Sun 211° 43'; the Moon 109° 20'; Mars | Planetary Positions — The Sun 21 1 °43'; the Moon 109° 20'; Mars |
| NH.chart_60 | NH:9410 | NH:12514 | content11 | Planetary Positions.-The Sun 180° 2'; the Moon 192° 44': Mars | Planetary Positions. -The Sun 180° 2'; the Moon 192° 44': Mars |
| NH.chart_64 | NH:9871 | NH:13161 | content10 | Planetary Positions.— The Sun 71° 24'; the Moon 313°; Mars | Planetary Positions. — The Sun 71° 24’; the Moon 313°; Mars |
| NH.chart_66 | NH:10134 | NH:13520 | content10 | Planetary Positions.—The Sun 239° 56'; the Moon 213° 56'; | Planetary Positions. — The Sun 239° 56'; the Moon 213° 56'; |
| NH.chart_70 | NH:10636 | NH:14213 | content10 | Planetary Positions.—The Sun 218° 44'; the Moon 137° 22'; | Planetary Positions. — The Sun 218° 44'; the Moon 137° 22’; |
| NH.chart_72 | NH:10970 | NH:14640 | content11 | Planetary Positions.-The Sun 36° 41' ; the Moon 160° 43'; Mars | Planetary Positions.-The Sun 36° 41' ; the Moon 160° 43'; Mars |
| NH.chart_74 | NH:11144 | NH:14890 | content11 | Planetary Positions.—The Sun 180° 54'; the Moon 34°17'; Mars | Planetary Positions. — The Sun 180° 54'; the Moon 34°17'; Mars |
| NH.chart_76 | NH:11440 | NH:15286 | manual: auto match 11672 was a DIFFERENT chart's positions; 15286 is this chart' | *Planetary Positions.—The Sun 113°0'; the Moon 56° 38'; Mars | ‘Planetary Positions. — The Sun 1 1 3 °0'; the Moon 56° 38'; Mars |
| NH.chart_58 | NH:9073 | NH:12097 | content11 | Planetary Positions.—The Sun 9° 56' ; the Moon 255° 46' ; Mars | Planetary Positions. — The Sun 9° 56' ; the Moon 255° 46’ ; Mars |
| NH.chart_68 | NH:10395 | NH:13876 | manual: Planetary Positions line, OCR '282D' -> '282' | Planetary Positions.—The Sun 282D 23' ; the Moon 159° 16'; | Planetary Positions. — The Sun 282° 23' ; the Moon 159° 16'; |
| NH.chart_73 | NH:11044 | NH:14754 | content11 | Planetary Positions —The Sun 196° 2'; the Moon 175° 31'; Mars | Planetary Positions — The Sun 196° 2'; the Moon 175° 31'; Mars |
| NH.chart_16 | NH:3130 | NH:4272 | content9 | Planetary Positions —The Sun 251 ° 48' ; the Moon 42° | Planetary Positions — The Sun 251 ° 48' ; the Moon 42° |
| NH.chart_17 | NH:3375 | NH:4572 | content11 | Planetary Positions.—The Sun 203° 50' ; the Moon 35° 14'; Mars | Planetary Positions. — The Sun 203°50’ ; the Moon 35° 14'; Mars |
| NH.chart_19 | NH:3902 | NH:5194 | content9 | Planetary Positions.—The Sun 237° 24' ; the Moon 227° | Planetary Positions. — The Sun 237° 24' ; the Moon 227° |
| NH.chart_22 | NH:4327 | NH:5757 | content10 | Planetary Positions.—The Sun 201°; the Moon 182°; Mars 87° ; | Planetary Positions. — The Sun 201°; the Moon 182°; Mars 87° ; |
| NH.chart_48 | NH:7709 | NH:10238 | content10 | Planetary Positions.—The Sun 342° 17' ;   the Moon 165° 20'; | Planetary Positions. — The Sun 342° 17' ; the Moon 165° 20'; |

## yoga_deep_read.NH_EXAMPLES — proposed old -> new (13)

| old | new | method | old text | new text |
|---|---|---|---|---|
| NH:1181 | NH:1591 | content9 | Vasumathi, Gajakesari, Mahabhagya and Parijata. It will be seen | Vasumathi, Gajakesari, Mahabhagya and Parijata. It will be seen |
| NH:1189 | NH:1600 | content10 | similarly aspected by Jupiter. Mark the position of Gajakesari in | similarly aspected by Jupiter. Mark the position of Gajakesari in |
| NH:1330 | NH:1804 | content11 | Hamsa Yoga, he had the confidence that every step is divinely | Hamsa Yoga, he had the confidence that every step is divinely |
| NH:1346 | NH:1821 | content10 | According to classical texts, the person born in Hamsa Yoga | According to classical texts, the person born in Hamsa Yoga |
| NH:1369 | NH:1845 | content9 | From Chandra Lagna, a powerful Adhi Yoga operates by | From Chandra Lagna, a powerful Adhi Yoga operates by |
| NH:1441 | NH:1922 | content9 | debaucheries filled Rome with horror. Hamsa Yoga, the powerful | debaucheries filled Rome with horror. Hamsa Yoga, the powerful |
| NH:1442 | NH:1923 | content13 | Adhi Yoga plus the Parijata Yoga made him "one of the world's | Adhi Yoga plus the Parijata Yoga made him "one of the world's |
| NH:1778 | NH:2381 | content10 | having caused Hamsa Yoga and Gajakesari Yoga. This is a | having caused Hamsa Yoga and Gajakesari Yoga. This is a |
| NH:1993 | NH:2667 | content9 | There are of course several yogas, such as Gajakesari, | There are of course several yogas, such as Gajakesari, |
| NH:2484 | NH:3374 | content12 | the six planets the 12th from the Moon have caused Anapha Yoga | the six planets the 12th from the Moon have caused Anapha Yoga |
| NH:2580 | NH:3533 | content8 | Hamsa and Malavya, the former indicating "distinction, righteous | Hamsa and Malavya, the former indicating "distinction, righteous |
| NH:2626 | NH:3579 | content10 | Venus has caused Malavya Yoga in the 9th or Dharmasthana | Venus has caused Malavya Yoga in the 9th or Dharmasthana |
| NH:3099 | NH:4238 | content9 | Akber's horoscope, viz., Sasa, Malavya and Ruchaka—Sasa | Akber's horoscope, viz., Sasa, Malavya and Ruchaka — Sasa |
