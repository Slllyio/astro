"""Vimsopaka bala — pinned against Parashara's own arithmetic (BPHS ch.7).

The load-bearing test is `test_every_scheme_totals_twenty`: Vimsopaka IS a 20-point scale, so a
scheme that does not total 20 is wrong by definition. That check is what recovered the two values
the OCR dropped (Dasavarga's per-division 1½, Shodasavarga's Trimsamsa 1) — and it is what will
catch a future re-OCR or a careless edit that shifts them.
"""
from __future__ import annotations

import pytest

from app.parashara.doctrine.sources import verify
from app.parashara.primitives import vimsopaka as V


class TestSchemes:
    def test_every_scheme_totals_twenty(self):
        """Vimsopaka is the TWENTY-point strength; each of Parashara's four schemes sums to 20."""
        for name, weights in V.SCHEMES.items():
            assert sum(weights.values()) == pytest.approx(20.0), (
                f"{name} totals {sum(weights.values())}, not 20 — a scheme that does not total 20 "
                f"is not Vimsopaka")

    def test_scheme_sizes_match_their_names(self):
        """Shad=6, Sapta=7, Dasa=10, Shodasa=16 divisions — the names ARE the counts."""
        assert len(V.SHADVARGA) == 6
        assert len(V.SAPTAVARGA) == 7
        assert len(V.DASAVARGA) == 10
        assert len(V.SHODASAVARGA) == 16

    def test_shadvarga_weights_are_the_sloka_verbatim(self):
        """BPHS-7:220 — 'Rasi, Hora, decanate, Navamsa, Dvadasamsa and Trimsamsa ... the full
        strength for each of the divisions respectively are 6, 2, 4, 5, 2 and 1.' Hand-copied from
        the sloka, in its order, so a table edit cannot quietly drift from the text."""
        assert [V.SHADVARGA[d] for d in ("D1", "D2", "D3", "D9", "D12", "D30")] == [6, 2, 4, 5, 2, 1]

    def test_saptavarga_weights_are_the_sloka_verbatim(self):
        """BPHS-7:224 — '5, 2, 3, 2½, 4½, 2 and 1' (the OCR renders the halves as '2{' and '4i')."""
        assert [V.SAPTAVARGA[d] for d in ("D1", "D2", "D3", "D7", "D9", "D12", "D30")] == \
            [5.0, 2.0, 3.0, 2.5, 4.5, 2.0, 1.0]

    def test_dasavarga_recovers_the_value_the_ocr_dropped(self):
        """BPHS-7:238 gives '3 for Rasi, 5 for Shashtiamsa and [ ] for the other 8 divisions' —
        the scan lost the third figure. 20 - 3 - 5 = 12 over 8 divisions = 1.5 each, and the
        chapter's own table confirms 1.5. Pinned so the recovery is explicit, not incidental."""
        assert V.DASAVARGA["D1"] == 3.0
        assert V.DASAVARGA["D60"] == 5.0
        others = [v for k, v in V.DASAVARGA.items() if k not in ("D1", "D60")]
        assert len(others) == 8 and all(v == 1.5 for v in others)

    def test_shodasavarga_recovers_the_trimsamsa_value(self):
        """BPHS-7:265 scans Trimsamsa as 'V'. The named seven plus nine halves must total 20,
        which forces Trimsamsa = 1."""
        named = ("D1", "D2", "D3", "D9", "D16", "D30", "D60")
        assert V.SHODASAVARGA["D30"] == 1.0
        halves = [v for k, v in V.SHODASAVARGA.items() if k not in named]
        assert len(halves) == 9 and all(v == 0.5 for v in halves)


class TestVargaViswa:
    def test_the_six_tier_scale_is_parasharas(self):
        """BPHS-7:268 — 'declines to 18 in extreme friends Vargas, to 15 in friendly Vargas, to 10
        in equal's divisions, to 7 in enemy's Vargas and to 5 in sworn enemy's Vargas', from 20 in
        own. Six tiers, no 'exalted', and a floor of 5 — never zero."""
        assert V.VARGA_VISWA == {
            "own": 20.0, "adhi_mitra": 18.0, "mitra": 15.0,
            "sama": 10.0, "shatru": 7.0, "adhi_shatru": 5.0,
        }

    def test_no_tier_is_zero(self):
        """Even a sworn enemy's varga yields 5/20 — Vimsopaka never bottoms out at nothing, which
        is why it cannot be modelled with a coarse exalt/debilitated scale."""
        assert min(V.VARGA_VISWA.values()) == 5.0


class TestComputation:
    def test_all_own_vargas_scores_the_full_twenty(self):
        """'The Vimsopaka strength remains as 20 ... only when the planet is in own house Vargas'
        (BPHS-7:266). The strongest possible reading, in every scheme."""
        for scheme, weights in V.SCHEMES.items():
            r = V.vimsopaka("Jupiter", {d: "own" for d in weights}, scheme=scheme)
            assert r.score == pytest.approx(20.0), scheme
            assert r.band == "wholly-favourable"

    def test_all_sworn_enemy_vargas_scores_the_floor(self):
        """Worst case = 20 x (5/20) = 5.0 — and 5.0 sits in the LOWEST band, since Parashara says
        'above 5', not 'from 5'."""
        r = V.vimsopaka("Saturn", {d: "adhi_shatru" for d in V.SAPTAVARGA}, scheme="saptavarga")
        assert r.score == pytest.approx(5.0)
        assert r.band == "inauspicious"

    def test_proportional_evaluation_matches_the_sloka(self):
        """BPHS-7:283 — 'multiply the full strength for the division by the Varga Viswa and divide
        by 20'. Hand-computed: Shadvarga with Rasi own(20) and everything else equal(10) is
        6*20/20 + (2+4+5+2+1)*10/20 = 6 + 7 = 13.0."""
        viswa = {d: "sama" for d in V.SHADVARGA}
        viswa["D1"] = "own"
        r = V.vimsopaka("Mars", viswa, scheme="shadvarga")
        assert r.score == pytest.approx(13.0)
        assert r.per_varga["D1"] == pytest.approx(6.0)
        assert r.band == "mediocre"

    def test_contributions_sum_to_the_score(self):
        viswa = {d: "mitra" for d in V.SHODASAVARGA}
        r = V.vimsopaka("Venus", viswa, scheme="shodasavarga")
        assert sum(r.per_varga.values()) == pytest.approx(r.score)
        assert r.score == pytest.approx(15.0)      # 20 * 15/20


class TestBands:
    def test_the_floor_is_reachable_so_the_bottom_boundary_is_inclusive(self):
        """The scale's minimum IS exactly 5.0 (all divisions sworn-enemy). Reading Parashara's
        'below 5' strictly would make his own lowest band unreachable for any chart ever cast, so
        5.0 must fall INSIDE it. This is the one boundary the scale settles rather than taste."""
        assert V.MINIMUM_POSSIBLE_SCORE == 5.0
        assert V.band_for(5.0)[0] == "inauspicious"

    def test_remaining_boundaries_follow_the_sloka_wording(self):
        """'above 5 but below 10' -> 10 is not some-good; 'upto 15' is inclusive -> 15 is still
        mediocre; 'above 15' starts strictly after."""
        assert V.band_for(5.01)[0] == "some-good"
        assert V.band_for(9.99)[0] == "some-good"
        assert V.band_for(10.0)[0] == "mediocre"
        assert V.band_for(15.0)[0] == "mediocre"
        assert V.band_for(15.01)[0] == "wholly-favourable"

    def test_verdict_is_parasharas_own_phrasing(self):
        r = V.vimsopaka("Sun", {d: "own" for d in V.SHADVARGA}, scheme="shadvarga")
        assert r.verdict == "will yield wholly favourable effects"


class TestFailsLoudly:
    def test_missing_division_raises(self):
        """Silently defaulting a missing division to `sama` would understate a strong planet and
        no one would ever see it — so it raises."""
        with pytest.raises(ValueError, match="missing"):
            V.vimsopaka("Moon", {"D1": "own"}, scheme="saptavarga")

    def test_unknown_viswa_key_raises(self):
        with pytest.raises(ValueError, match="Varga Viswa"):
            V.vimsopaka("Moon", {d: "exalted" for d in V.SHADVARGA}, scheme="shadvarga")

    def test_unknown_scheme_raises(self):
        with pytest.raises(ValueError, match="scheme"):
            V.vimsopaka("Moon", {}, scheme="navavarga")


class TestCitations:
    def test_every_scheme_citation_resolves(self):
        """Each scheme points at the sloka that defines it, and that line must exist on disk."""
        for scheme, cite in V.SCHEME_SOURCE.items():
            assert verify(cite), f"{scheme}: {cite.work}:{cite.line} does not resolve"

    def test_viswa_and_band_citations_resolve(self):
        assert verify(V.VISWA_SOURCE)
        assert verify(V.BANDS_SOURCE)

    def test_citations_point_at_the_right_text(self):
        """A citation that resolves to the wrong line is worse than none — it looks verified."""
        from app.parashara.doctrine.sources import passage
        assert "VIMSOPAKA STRENGTH" in passage("BPHS-7:220")["text"]
        assert "PROPORTIONAL" in passage("BPHS-7:283")["text"].upper()
