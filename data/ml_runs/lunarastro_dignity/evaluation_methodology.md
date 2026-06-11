# Better evaluation metrics for astrological timing — beyond lift & z

> Deep-research synthesis, 2026-06-11. Four parallel research passes (forecast
> verification / proper scoring rules; survival + self-controlled epidemiology;
> ranking + information theory; prior astrology-test methodology + practitioner
> framing), cross-checked. Citations inline. Goal: an evaluation framework for
> within-person dasha-timing that is **forward/graded** (not retrospective/binary),
> measures **calibration + discrimination**, gives a **practitioner-interpretable
> effect size**, and reports **skill over an age base-rate** — while keeping the
> self-controlled (each-native-its-own-control) design.

## 0. Diagnosis — what lift/z gets right and wrong

Our statistic: within-person `lift = observed_hit / expected_hit`, expected =
duration-weighted share of in-band life the rule covers; significance from a
within-person permutation (redraw the event period ∝ duration).

**What it gets right — keep this.** It is a *self-controlled* design: each native
is their own control, so all fixed between-person confounders (cohort, recording
era, base longevity) cancel. In epidemiology terms our `lift` **is a Standardized
Incidence Ratio**, observed/expected events, which under a Poisson/rare-event model
**equals the incidence-rate ratio ≈ the hazard ratio**
([CDC SIR](https://www.cdc.gov/cancer-environment/media/pdfs/Standardized-Incidence-Ratio-Fact-Sheet-508.pdf);
[Mayo Poisson person-time](https://www.mayo.edu/research/documents/biostat-81pdf/doc-10026981)).
The permutation is the non-parametric twin of the **Self-Controlled Case Series**
conditional-Poisson model ([Farrington 1995](https://www.jstor.org/stable/2533320);
[Whitaker et al. 2006](https://onlinelibrary.wiley.com/doi/10.1002/sim.7536)).

**What it gets wrong — three gaps, each fixable.**
1. **Retrospective, not prospective.** We condition on the event and ask "was a
   rule active?" An astrologer works forward: chart → "marriage ~28–31, high
   confidence." Forecast skill is a different, harder thing.
2. **Binary, not graded.** Lift treats a period as rule-on/off. Practice grades
   confidence by weight-of-evidence and *ranks* a native's periods.
3. **No calibration.** Lift never asks "when you said 80% likely, did it happen
   80% of the time?" — the core of forecaster trustworthiness, and the exact
   thing prior astrology tests found astrologers *fail*
   ([McGrew & McFall 1990](https://www.astrology.co.uk/tests/mcgrew.htm):
   astrologers' confidence was **uncorrelated** with accuracy).

## 1. The mapping — each research strand → what it upgrades

| our current | upgrade | what it buys | source |
|---|---|---|---|
| `lift` (obs/exp) | **conditional-Poisson / SCCS incidence-rate ratio** (or Cox with a time-varying covariate, stratified by person) | same estimand, but a **hazard/rate ratio + CI**, practitioner-interpretable ("events 1.1× more frequent"), a *named gold-standard* self-controlled design, and clean adjustment for age | Farrington/Whitaker; [Cox time-varying, Therneau](https://cran.r-project.org/web/packages/survival/vignettes/timedep.pdf) |
| `z` / permutation p | conditional-Poisson **Wald/score test + 95% CI** (permutation kept as exact backup) | confidence interval, not just a p; bounds the effect size | Whitaker 2006 |
| Finding-13 within-person **percentile** of the event period | **concordance / C-index / AUC** + **MRR** + **top-k hit-rate** | "does the rule **rank** the true period high / point to it in the top-3?" — exactly the practitioner's act. (mean percentile rank **= AUC** for one true item) | [Harrell C-index](https://www.serdarbalci.com/ClinicoPathJamoviModule/reference/concordanceindex.html); AUC=Mann-Whitney |
| (nothing — we never made a forward forecast) | **probabilistic forecast over candidate periods + a strictly proper scoring rule**, reported as **skill vs an age base-rate**, **decomposed into calibration vs discrimination** | the prospective, graded, *calibration-testing* layer that matches how astrologers actually predict | Gneiting & Raftery 2007; Murphy 1973 |

## 2. The recommended framework (three layers)

### Layer A — Effect size & inference: self-controlled rate ratio (replaces lift/z)
Bin each native's life into the natural dasha sub-periods (person-period format)
and fit a **conditional Poisson (SCCS)** with the rule indicator as a time-varying
exposure, the event count as outcome, conditioning on each native's total events —
or equivalently **Cox with a (start, stop, event) time-varying covariate,
stratified by person**. Both yield a **rate/hazard ratio with CI**. This *is* our
lift, but as the estimand epidemiology uses for exactly this "is the rate elevated
during exposed person-time, each subject its own control" question
([discrete-time hazard ≈ Cox when intervals short & events rare, D'Agostino 1990](https://onlinelibrary.wiley.com/doi/abs/10.1002/sim.4780091214)).
*Why better than lift:* interpretable to a jyotishi and a statistician, gives a CI,
adjusts for age as a covariate, and names the design (SCCS) so it's citable and
unimpeachable on confounding.

### Layer B — Discrimination: does the rule rank the true period high?
For each native, score their candidate periods by the rule and ask where the true
event period lands. Report:
- **C-index / AUC** = P(true period scored above a random non-event period). Mean
  within-person percentile rank = AUC ([Hand & Till; AUC=Mann-Whitney U](https://en.wikipedia.org/wiki/Receiver_operating_characteristic)). 0.5 = no skill.
- **MRR** = mean of 1/rank of the true period — emphasises "is it #1?"
- **top-k hit-rate** ("true period in the astrologer's top-3 of N") — the most
  practitioner-legible number.
*Why better:* this is literally "the period an astrologer would point to," and it
upgrades Finding-13's percentile test into the standard discrimination language.

### Layer C — Calibration + overall skill: the prospective, graded layer
Convert each rule into a **forward probability forecast**: from the chart alone,
assign each candidate period a probability (∝ a confidence score — e.g. strength/
convergence/dignity weight — normalised to sum to 1). Then:
- **Score with a strictly proper rule** — the **logarithmic (ignorance) score**
  `−log₂ p(true period)` (bits of surprise;
  [Roulston & Smith 2002](https://journals.ametsoc.org/view/journals/mwre/130/6/1520-0493_2002_130_1653_epfuit_2.0.co_2.xml))
  for "which period," and the **Ranked Probability Score (RPS/CRPS)** if we exploit
  the time-ordering / age (penalises *near*-misses less than far ones —
  [Epstein 1969](https://www.degruyterbrill.com/document/doi/10.1515/jqas-2019-0089/html)).
  Strictly proper ⇒ honest probabilities win, and **both overconfidence and vague
  hedging are penalised** ([Gneiting & Raftery 2007](https://ideas.repec.org/a/bes/jnlasa/v102y2007p359-378.html)).
- **Report as a skill score over an age base-rate** — `RPSS = 1 − RPS/RPS_climatology`,
  reference = "predict the event by the population age distribution." **Beating the
  actuary is the real bar.** Reference must be **age-conditioned**, else skill is
  inflated ([using climatology as reference, MWR 2004](https://journals.ametsoc.org/view/journals/mwre/132/7/1520-0493_2004_132_1891_oucaar_2_0.co_2.xml)).
- **Decompose (Murphy) into reliability − resolution + uncertainty** and draw a
  **reliability diagram**: when the rule says "high confidence," does the event
  happen proportionally more? This directly tests the McGrew–McFall calibration
  failure and separates *calibration* (honest confidence) from *discrimination*
  (ranking power) ([Murphy 1973](https://en.wikipedia.org/wiki/Brier_score)).
- Express the headline as **bits of information gained over base-rate** (log-skill
  = mutual information about timing) — "knowing the dasha reduces uncertainty about
  *when* by X bits." Intuitive, and honest about magnitude.

## 3. How astrologers actually predict — so we score on their terms

Practitioner timing is **dasha promise + transit trigger ("double confirmation"):**
the dasha names a multi-year window; a transit (esp. the Jupiter/Saturn "double
transit," K.N. Rao) narrows it to ~1 year
([Aaskplanets](https://aaskplanets.com/rare-and-fine-tuned-technique-of-double-transit-to-time-events-vedic-astrology/);
Rao, *Timing of Events through Vimshottari Dasha*). Confidence is graded by
**convergence of significators** into tiers (~30% / ~60% / ~85%), and astrologers
**rank** a native's periods. This converts cleanly into Layer C: the convergence/
strength score → the per-period probability; the transit trigger → a sharper
(narrower-window) forecast we can score with RPS/CRPS. Scoring the *timing* task
this way also fixes the **task-mismatch** in the famous tests, which scored
chart–personality *matching* (Carlson 1985; Vernon Clark), not timing — a different
skill ([Carlson, Nature 1985](https://www.nature.com/articles/318419a0), null;
[Ertel 2009 reanalysis](https://journalofscientificexploration.org/index.php/jse/article/view/99)
disputed, marginal p≈.04–.05; [Dean & Kelly 2003](https://journalpsyche.org/articles/0xc062.pdf)
meta r≈0.05).

## 4. Honest expectation & pitfalls

- **Expected outcome on our data.** With lift≈1.1, discrimination AUC will be
  ≈0.51–0.52, MRR barely above baseline, and the RPS/log skill score ≈0 or slightly
  negative. These metrics will mostly *confirm the null* — but far more
  interpretably, and they add the **calibration** test and a **practitioner-grade
  effect size (rate ratio + CI)** we currently lack.
- **The confidence→probability map is a modelling choice — pre-register it.** A
  strictly proper rule keeps it honest, but the mapping (which strength/convergence
  score, how normalised) must be fixed before scoring or it's another researcher
  degree of freedom.
- **Censoring matters** (esp. death; never-married). Use survival-CRPS or restrict;
  don't silently drop censored cases (biases toward early events).
- **Base-rate must be age-conditioned** (and ideally duration-conditioned) or skill
  is inflated — the single most common error in timing-skill claims.
- **SCCS assumption**: the event must not change subsequent exposure (true here —
  dasha sequence is fixed at birth) and events should be rare/independent within a
  band (mostly true for first marriage/career/death).

## 5. Concrete recommendation (one line)

Replace `lift/z` with a **self-controlled forecast-skill report**:
(A) **SCCS / conditional-Poisson incidence-rate ratio + CI** as the effect size,
(B) **within-person C-index/AUC + top-k** as discrimination,
(C) a **pre-registered per-period probability forecast scored by RPS/ignorance as a
skill score over an age base-rate, Murphy-decomposed with a reliability diagram**,
as the prospective, calibration-testing, *astrologer's-own-terms* layer.
Layers A and B are near-free reframes of what we already compute; Layer C is the
genuinely new, practice-aligned evaluation.

### Key sources
- Gneiting & Raftery 2007, *Strictly Proper Scoring Rules* (JASA) — properness, CRPS.
- Murphy 1973 — reliability–resolution–uncertainty decomposition.
- Epstein 1969 — Ranked Probability Score; Roulston & Smith 2002 — ignorance/information score.
- Farrington 1995 / Whitaker et al. 2006 — Self-Controlled Case Series. Maclure 1991 — case-crossover.
- Andersen & Gill 1982; Therneau (survival vignette) — Cox time-varying covariates. Harrell — C-index.
- Carlson 1985 (Nature); Ertel 2009 (reanalysis); Dean & Kelly 2003; McGrew & McFall 1990 — astrology-test designs & the calibration finding.
- K.N. Rao, *Timing of Events through Vimshottari Dasha* — dasha+transit double confirmation.

*(Fetch note: many primary PDFs returned HTTP 403 in this environment; formulas and
definitions were triangulated across ≥2 open sources each. Claims flagged "disputed"
where the literature disagrees — Carlson/Ertel, Dean & Kelly vs McRitchie.)*
