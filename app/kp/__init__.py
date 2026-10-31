"""``app.kp`` — Krishnamurti Paddhati engine, encoded from K. S. Krishnamurti's KP Reader 3.

A separate system from ``app.raman_saab`` and ``app.parashara``: it uses the Krishnamurti
ayanamsa and Placidus cusps because KP doctrine requires them, and restores swisseph's global
sidereal mode to Lahiri (the repo lock) after every cast. Nothing outside ``app.kp`` imports it.

Modules: ``subs`` (249 divisions), ``chart`` (cast), ``significators`` (A-D ladder),
``ruling`` (ruling planets), ``dasa`` (Vimshottari), ``judgment`` (cusp sub-lord verdicts,
stability, timing), ``citations`` (verbatim Reader 3 quotes).

Every choice the source leaves open is a named ruling in ``docs/kp/KP_RULINGS.md``. The engine
is a faithful instrument, not a validated predictor; see ``docs/kp/KP_PREFLIGHT_2026-10-31.md``.
"""
