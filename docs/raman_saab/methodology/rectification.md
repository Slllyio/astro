# Birth-time rectification — RETIRED (2026-11-05)

The event-based rectifier that this page used to describe (`app/raman_saab/rectification/`,
the `tools/raman_saab/rectify` CLI, the `POST /rectify` endpoint and the older
`app/core/birth_time_rectification.py`) has been removed. `POST /rectify` now answers
410 Gone with the replacement policy.

Why, and what the engine does instead: [`../BIRTH_TIME_POLICY.md`](../BIRTH_TIME_POLICY.md).

The old text, its worked session and its golden fixture were taken out of the current
tree because the worked session was built from a real person's own life events. Earlier
versions remain in git history only.
