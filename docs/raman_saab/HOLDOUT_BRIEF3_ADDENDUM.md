# Addendum for hold-out round 3 (Hindu Predictive Astrology)

Everything in BRIEF.md (same folder) applies. In addition:

1. Source: Hindu Predictive Astrology (HPA), two ranges:
   - chapter_035_practical-horoscopes.md (21 numbered horoscopes; chart_no = "35.<n>", e.g. "35.4")
   - chapter_014_ayurdaya-or-longevity.md, lines 270-440 only (Horoscope Nos. 1-3; chart_no = "14.<n>")
   Files are in /home/claude/astro/data/knowledge_library/sources/hindu_predictive_astrology_raman/
2. SKIP any chart whose birth date is in skip_birth_dates.txt (same folder). Record skipped ones
   with "skipped": true and no conclusions, so coverage is visible.
3. Raman prints the sign of every planet ("Planetary Positions") for ch.35 and a Rasi diagram for
   ch.14 (the ch.14 diagram OCR is scrambled; give positions only where you can read them with
   confidence, else omit stated_positions). Record "stated_positions": {"Sun": {"sign": "Leo",
   "deg": null}, ... all nine: Sun Moon Mars Mercury Jupiter Venus Saturn Rahu Ketu} and
   "lagna_sign_printed". Kethu = Ketu.
4. Coordinates: copy them exactly as printed; if only a place is named (e.g. "near Doria, Italy",
   "Bangalore"), put the place name in `place` and leave lat/lon null. Do NOT look up coordinates.
5. The "General Remarks" mix observations ("mark the position of Mars ...") with conclusions
   ("died in her 14th year", "two wives"). Only conclusions count, per the confirmation rule.
   "Mark how Venus is afflicted" is an observation. "Two wives" is a conclusion (H7: mixed only if
   Raman names both poles; a second marriage after the first wife's death is afflicted
   marital_happiness unless he says the second marriage was happy).
   Death in childhood / early death → H8 longevity afflicted. Long life stated → H8 longevity favourable.
6. Give a `name` if Raman names the native; otherwise null.
