# Mainpuri chart: the 10th and 11th houses, audited rule by rule

Date: 2026-10-28. Chart: 12 Oct 1989, 10:02 IST, Mainpuri (27N14, 79E02), Raman ayanamsa.
Branch `claude/project-thread-yj2a5g`. Nothing here is my opinion: every line is a printed Raman
rule, a computed position, or one of Raman's own worked conclusions from the scored goldens.

## 1. The positions the two houses depend on (computed, Raman ayanamsa)

| Planet | Sign (Rasi house) | Bhava | Dignity | Shadbala (rupas) | Note |
|---|---|---|---|---|---|
| Sun (10th lord) | Virgo (11) | 11 | Virgo, enemy (compound) | 5.99 | own sign Leo in the Navamsa |
| Mars (Lagna lord) | Virgo (11) | 11 | enemy | 3.98 | combust (0.76), debilitated in the Navamsa |
| Mercury (8th + 11th lord) | Virgo (11) | 11, **in the sandhi** | exalted | 8.99 | 0.84 deg from the Bhava-sandhi; debilitated in the Navamsa |
| Jupiter (2nd + 5th lord, karaka of gains) | Gemini (8) | 8 | neutral | 8.32 | own sign Pisces in the Navamsa |
| Saturn (3rd + 4th lord) | Sagittarius (2) | 2 | enemy | 5.11 | aspects Aquarius, Gemini, Virgo |
| Rahu | Aquarius (4) | **3** | | | 0 deg 28' Aquarius |
| Ketu | Leo (10) | **9** | | | |

## 2. The main engine (the scored judge): every rule that fired

The judge reads each matter of the house from Raman's printed rules (HTJAH-II, chapters on the
10th and 11th), then weighs them by `house_template._decide_clauses`.

### 10th house: verdict **favourable** for all six matters

| Rule | Polarity | Citation | Raman's text (as encoded) | Condition holds? |
|---|---|---|---|---|
| H10.L.11 | benefic | HTJAH-II:9556 | 10th lord in the 11th: "earns immense riches; fortunate in every respect … gives employment to hundreds … high sense of honour; many friends" | Yes: Sun in the 11th sign and 11th Bhava |
| H10.C.33 | benefic (status) | HTJAH-II:11064 | "benefics in the 10th from the Ascendant or the Moon: a noble-minded native" | Yes: Venus in Scorpio, the 10th from the Moon |
| H10.P.Ketu | malefic | HTJAH-II:9900 | Ketu in the 10th: "strong, bold and well-known … faces many obstacles" | **Doubtful**: Ketu is in Leo but in the **9th Bhava**; Raman frees a house of a planet in another Bhava (HTJAH-I:1945-1946) |
| H10.C.33m | malefic (status) | HTJAH-II:11064 | "malefics in the 10th from the Ascendant or the Moon" | Same Ketu, same doubt |
| H10.L.11a | not counted | HTJAH-II:9560 | 10th lord in the 11th with the 11th afflicted | Named, not counted |

How it is weighed. Benefic and malefic rules both fire, so the clause-2 preponderance decides on
the strength pillars. The 10th lord, the Sun, is strong; the karaka is the Sun again, strong; the
Navamsa confirms (the Sun in his own Leo). Two strong pillars and no weakening: **favourable**.
**Robustness.** Drop the doubtful Ketu rules and no malefic fires. Clause 5 then gives
favourable outright. The verdict does not depend on them.

### 11th house: verdict **favourable** for all five matters

| Rule | Polarity | Citation | Raman's text (as encoded) | Condition holds? |
|---|---|---|---|---|
| H11.L.11 | benefic | HTJAH-II:14330 | 11th lord in the 11th: "many friends and elder brothers who help throughout life; happy life …" | Yes |
| H11.C.53 | benefic (elder siblings) | HTJAH-II:14709 | 11th lord in the 11th: "succeeds without effort … a famous elder brother; business keyed to the lord (Mercury: writing, teaching, research)" | Yes |
| H11.C.42 | benefic | HTJAH-II:14617 | "the 11th lord related to the 10th lord: a successful career; merit recognised" | Yes: Mercury with the Sun |
| H11.P.Sun | benefic | HTJAH-II:14442 | Sun in the 11th: "wealthy … royal/governmental favours; success without much effort" | Yes |
| H11.C.4 | benefic | HTJAH-II:14362 | "fortified planets in the 11th" | Yes: exalted Mercury |
| H11.C.8 | benefic | HTJAH-II:14392 | "11th lord in a kendra/trikona, OR malefics strong in the 11th: immensely wealthy" | Yes, by the second arm |
| H11.P.Mercury, H11.C.1 | benefic | HTJAH-II:14459, 14357 | Mercury in the 11th; "a benefic in the 11th Bhava" | **Doubtful**: Mercury is in the Bhava-sandhi, which Raman says gives no Bhava result (HPA-24:98-100) |
| H11.C.31, H11.C.37 | benefic (elder siblings) | HTJAH-II:14348, 14745 | 11th favourably disposed / benefic association | Yes |
| H11.C.5 | malefic | HTJAH-II:14367 | "the 11th occupied by a weak planet (eclipsed, depressed …): even one born affluent loses everything" | Yes: Mars, combust |
| H11.C.23 | malefic | HTJAH-II:15185 | "the 5th lord in the 8th: losses can occur" | Yes: Jupiter in the 8th |
| H11.C.38 | malefic (elder siblings) | HTJAH-II:14747 | "malefic aspects on both the 11th and its lord" | Yes: Saturn's 10th aspect |

How it is weighed. Both kinds fire, so the pillars decide. The 11th lord Mercury is strong (8.99
rupas, the strongest in the chart); the karaka Jupiter is strong (8.32 rupas); the Navamsa is
neutral; the lord is not combust or debilitated in the Rasi. Two strong pillars: **favourable**.
**Robustness.** Drop the two doubtful Mercury rules and nine benefic rules still fire. The pillars
are unchanged, so the verdict is unchanged.

## 3. Raman's own conclusions on charts with the same features

These are his printed verdicts on the 10th and 11th, taken from the scored goldens, for every
chart that shares a feature with Mainpuri. They are not a causal test. They show whether Raman
ever reads one of these features as making the house afflicted.

| Feature (as in Mainpuri) | Raman's 10th/11th conclusions | Favourable | Mixed | Afflicted |
|---|---|---|---|---|
| 11th lord in the 11th | 9 | 6 | 2 | 1 (NH.chart_26; he gives the debilitated 10th lord as the reason) |
| 10th lord in the 11th | 8 | 7 | 1 | 0 |
| 10th and 11th lords together | 12 | 10 | 2 | 0 |
| Saturn aspecting the 11th | 19 | 15 | 3 | 1 (NH.chart_64; he gives the 10th lord's placement as the reason) |
| Saturn aspecting the 10th lord | 9 | 7 | 2 | 0 |
| A node in the 10th sign | 9 | 6 | 3 | 0 |

In none of these 66 conclusions does Raman call the 10th or 11th afflicted because of Saturn's
aspect or a node in the 10th sign. Those are exactly the two testimonies that make the template
tally read "afflicted" on Mainpuri.

## 4. Why the two-of-three template disagrees, and why it does not lead

The procedure reader (the "template tally") gives every testimony one equal step. On Mainpuri:

- **10th.** Rahu's sign-aspect costs one step, although Rahu is in the 3rd Bhava. Saturn's aspect
  on the Sun costs another. The Moon view costs one more, because the 10th-from-Moon lord, Mars,
  is 8th from the Moon.
- **11th.** Saturn's one aspect costs a step on the house. Jupiter costs three steps (the 8th
  house, Gemini, Saturn's aspect). Mercury, exalted, is pulled to "moderate" by his Navamsa fall.

Three facts settle which instrument leads:

1. **Fidelity.** On Raman's 389 printed conclusions the judge matches 260 (66.8%) and the template
   154 (39.6%).
2. **Stability.** Over birth times from 09:42 to 10:22 the judge reads both houses favourable at
   every step. The template moves between afflicted and mixed as Mercury crosses the sandhi:
   10:00 reads mixed for the 11th, 10:02 afflicted.
3. **Precedent.** Raman's own 10th/11th conclusions (section 3) never treat these two
   testimonies as decisive.

## 5. Conclusion

**10th: favourable. 11th: favourable.** This rests on:

- the rules Raman prints for these houses (eleven benefic rules against three malefic for the
  11th, and two against one doubtful for the 10th);
- the strength of their lords and karakas;
- his verdicts on every comparable chart in the goldens.

Two qualifications Raman would print beside it:

1. Mars, the Lagna lord, is combust in the 11th (H11.C.5 "a weak planet in the 11th"). So gains
   come with some loss or expense through him.
2. Jupiter, lord of the 5th, in the 8th (H11.C.23) "losses can occur".

The engine records both as malefic rules. Neither outweighs the strong lord and karaka.

## 6. What this changes in the engine

Nothing in the judge's verdicts. Two rule-firing questions are recorded for a pre-registered pass,
because they are general, not specific to this chart:

- (a) whether `planet_in_house` rules such as H10.P.Ketu should fire on a planet whose Bhava
  differs from its sign;
- (b) whether rules on an 11th-Bhava benefic should fire on a planet in the Bhava-sandhi.

Neither changes this chart's verdicts (section 2, robustness).
