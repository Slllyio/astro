"""Vimsopaka end-to-end on a real chart (BPHS ch.7 + ch.3).

Uses the project's canonical baseline nativity (CLAUDE.md: Bangalore 1990-07-15 12:00 IST) so the
numbers can be compared against other engines on the same chart later. The assertions here are
about STRUCTURE and INVARIANTS — a hand-computed score for a real chart would just be restating
the implementation, whereas "every score lies on Parashara's scale" and "own-sign scores full
weight" are properties the doctrine actually guarantees.
"""
from __future__ import annotations

import pytest

from app.parashara.chart.vimsopaka_chart import viswa_by_varga, vimsopaka_all, vimsopaka_for
from app.parashara.primitives import relationships as rel
from app.parashara.primitives.vimsopaka import SCHEMES, VARGA_VISWA

#: Canonical baseline chart, sidereal longitudes (deg). Bangalore 1990-07-15 12:00 IST.
_CHART = {
    "Sun": 89.1, "Moon": 355.3, "Mars": 21.7, "Mercury": 111.4,
    "Jupiter": 96.8, "Venus": 62.5, "Saturn": 262.9,
}


class TestViswaByVarga:
    def test_covers_every_division_the_scheme_names(self):
        for scheme, weights in SCHEMES.items():
            got = viswa_by_varga("Jupiter", _CHART, scheme=scheme)
            assert set(got) == set(weights), scheme

    def test_every_key_is_on_parasharas_scale(self):
        for scheme in SCHEMES:
            for planet in rel.GRAHAS:
                for tag, key in viswa_by_varga(planet, _CHART, scheme=scheme).items():
                    assert key in VARGA_VISWA, f"{planet} {tag} -> {key!r}"

    def test_own_sign_is_reported_as_own(self):
        """A planet in its own sign in some division must score 'own' — checked by finding a real
        case in the chart rather than asserting one exists in the abstract."""
        found = False
        for planet in rel.GRAHAS:
            for tag, key in viswa_by_varga(planet, _CHART, scheme="shodasavarga").items():
                if key == "own":
                    n = int(tag[1:])
                    from app.raman_saab.chart import varga as V
                    assert rel.SIGN_LORDS[V.varga_sign(_CHART[planet], n)] == planet
                    found = True
        assert found, "expected at least one own-sign varga across 7 grahas x 16 divisions"

    def test_missing_planet_raises(self):
        with pytest.raises(ValueError, match="no longitude"):
            viswa_by_varga("Jupiter", {"Sun": 10.0}, scheme="shadvarga")

    def test_missing_sign_lord_raises_rather_than_half_computing(self):
        """The compound needs BOTH halves; if the division's sign-lord is absent from the chart the
        temporary half is unknowable, so it must refuse rather than silently degrade to naisargika
        (which would quietly overstate or understate every affected division)."""
        with pytest.raises(ValueError, match="no longitude"):
            viswa_by_varga("Sun", {"Sun": 89.1}, scheme="shadvarga")


class TestScores:
    def test_every_graha_scores_within_parasharas_range(self):
        """The scale runs 5..20: the floor is all-sworn-enemy (20 x 5/20), the ceiling all-own."""
        for scheme in SCHEMES:
            for planet, r in vimsopaka_all(_CHART, scheme=scheme).items():
                assert 5.0 - 1e-9 <= r.score <= 20.0 + 1e-9, f"{planet} {scheme} -> {r.score}"

    def test_contributions_sum_to_the_score(self):
        for planet, r in vimsopaka_all(_CHART, scheme="shodasavarga").items():
            assert sum(r.per_varga.values()) == pytest.approx(r.score), planet

    def test_all_seven_grahas_scored_and_nodes_skipped(self):
        got = vimsopaka_all({**_CHART, "Rahu": 300.0, "Ketu": 120.0})
        assert set(got) == set(rel.GRAHAS)
        assert "Rahu" not in got and "Ketu" not in got

    def test_band_agrees_with_the_score(self):
        from app.parashara.primitives.vimsopaka import band_for
        for planet, r in vimsopaka_all(_CHART, scheme="saptavarga").items():
            assert r.band == band_for(r.score)[0], planet

    def test_scheme_choice_changes_the_score(self):
        """The four schemes weight the divisions differently, so they should not all agree — if
        they did, the scheme parameter would be doing nothing."""
        scores = {s: vimsopaka_for("Saturn", _CHART, scheme=s).score for s in SCHEMES}
        assert len(set(round(v, 6) for v in scores.values())) > 1, scores

    def test_deterministic(self):
        a = vimsopaka_for("Mars", _CHART, scheme="dasavarga")
        b = vimsopaka_for("Mars", _CHART, scheme="dasavarga")
        assert a == b


class TestTemporaryUsesTheBirthChart:
    def test_distance_is_measured_in_the_rasi_not_the_division(self):
        """Sloka 56 counts house-distance between the two planets in the BIRTH chart. Moving a
        planet within a sign changes its DIVISION sign but not its rasi, so the temporary half
        must be unchanged — this is the mix-up the module docstring warns about."""
        base = dict(_CHART)
        moved = {**_CHART, "Saturn": 268.9}          # same sign (Sagittarius), different navamsa
        assert int(base["Saturn"] // 30) == int(moved["Saturn"] // 30)
        # Sun's relation to Saturn depends on Saturn's RASI, which did not change.
        a = viswa_by_varga("Sun", base, scheme="shadvarga")
        b = viswa_by_varga("Sun", moved, scheme="shadvarga")
        sat_signs_a = {t for t, k in a.items() if k != "own"}
        assert sat_signs_a, "expected some non-own divisions"
        # Any division where the Sun's sign-lord is Saturn must score identically in both.
        from app.raman_saab.chart import varga as V
        for tag in a:
            n = int(tag[1:])
            if rel.SIGN_LORDS[V.varga_sign(base["Sun"], n)] == "Saturn":
                assert a[tag] == b[tag], tag
