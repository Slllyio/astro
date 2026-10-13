"""``app.empirical.natal`` — the Western tropical natal-decode surface.

Given a birth (date, time, latitude, longitude, timezone offset) this package
computes the planets in the sky at that moment (via ``app.empirical.western``)
and decodes them into seven trait facets: personality, characteristics,
attitude, aptitude, intelligence, work style, and work area.

Epistemic position (inherited from ``app.empirical`` and non-negotiable): the
decode reports what the mainstream Western tropical *tradition* associates with
the placements. It is not a validated measurement — this project's own
tournament found natal-chart features carry no predictive advantage over
birthplace and birth date (``docs/empirical/TIME_BASIS_CONFOUND.md``), and
every rendered surface here discloses that.

Modules:

* ``chart``   — birth input → :class:`~app.empirical.natal.chart.NatalChart`
  (positions, houses or an honest ``None``, aspects, balances, dominants).
* ``lexicon`` — the interpretation vocabulary: sign/planet/house/aspect tables
  under the ``WESTERN_TRADITION`` provenance banner.
* ``decoder`` — deterministic composition into the seven facets, every
  statement carrying its source placement.
* ``render``  — JSON dict + markdown, framing first, nothing computed omitted.
"""

from __future__ import annotations

__all__ = ["chart", "lexicon", "decoder", "render"]
