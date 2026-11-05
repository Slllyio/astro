"""Cited tools built on the Raman engine: a per-chart cited reading, a searchable classical
library, and a study view that sets the engine beside Raman's own worked readings.

All three are presentation and retrieval only. None of them changes a verdict, and none makes a
predictive claim: on 47k real lives no rule-based verdict beat chance
(docs/raman_saab/REAL_OUTCOME_GENERALIZATION.md). They answer "what do the books say, and why",
never "what will happen".

    python -m app.raman_saab.cited read  --name X --date 1989-10-12 --time 10:02 --tz 5.5 \
        --lat 27.23 --lon 79.03 --out reading.html
    python -m app.raman_saab.cited library build
    python -m app.raman_saab.cited library search "seventh lord in the eighth"
    python -m app.raman_saab.cited study --out data/study
    python -m app.raman_saab.cited serve            # all three in the browser, localhost only

See docs/raman_saab/CITED_TOOLS.md.
"""
