# Addendum to BRIEF.md for hold-out round 2

Everything in /tmp/claude-0/holdout/BRIEF.md applies. In addition:

1. SKIP any chart whose birth date (YYYY-MM-DD) is listed in /tmp/claude-0/holdout/skip_birth_dates.txt
   (those natives are already used). If a chart has no birth date, keep it.
2. If a chart prints planetary POSITIONS (a Rasi table or a list of longitudes), record them as
   "stated_positions": {"Sun": {"sign": "Leo", "deg": 12.5 or null}, ... for all of Sun, Moon, Mars,
   Mercury, Jupiter, Venus, Saturn, Rahu, Ketu}, plus "lagna_sign_printed" (the Lagna/Ascendant sign
   as printed, from the table or the text). Use sign names. Flag uncertain readings in `uncertain`.
   For charts WITHOUT birth data this is required, otherwise the chart cannot be used.
3. Give each chart a stable `chart_no` as printed (e.g. 37) and, for Notable Horoscopes, the native's
   name in a `name` field.
4. Signification keys: same vocabulary as BRIEF.md. The same confirmation rule applies: Raman's
   CONCLUSIONS about this native's life only, never observations about single factors.
