"""Round-8 unification wiring — yoga/sphuta/lookup layers into the per-signification judge.

TDD spec for:
  * ``SignificationVerdict.metadata`` / ``HouseProforma.metadata`` (frozen-safe
    key-value pairs, deterministic order);
  * the H5 Beeja/Kshetra fertility GATE (HTJAH-I:5517-5527) — both barren sphutas deny;
  * the yoga modifier (HTJAH-I consideration #4, :480-482) — dhana/arishta/raja
    kind-scoped modulation of a borderline 'mixed' only;
  * lookup-grid metadata surfacing (H8 decanate cause, H11 source of gains,
    H12 Bhavartha inversion + confinement mode, H6 organ/tridosha);
  * the §9 chart_overview pre-pass surface.

Synthetic Track-B charts are pinned by construction (whole-sign arithmetic is
checked in each docstring); the canonical Bangalore chart exercises Track A.
"""
from __future__ import annotations

import dataclasses

import pytest

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData, RamanChart, ShadbalaBreakdown
from app.raman_saab.doctrine.significations import Signification, significations_of
from app.raman_saab.doctrine.sources import Citation
from app.raman_saab.doctrine.yogas import FiredYoga, detect_yogas
from app.raman_saab.judges import chart_overview as co
from app.raman_saab.judges import house_template as ht

# ---------------------------------------------------------------------------
# Chart builders
# ---------------------------------------------------------------------------

_BANGALORE = BirthData("X", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)
#: Same BirthData as golden HTJAH-I.chart_33 (1910-10-31 13:41 IST, Bangalore).
_CHART_33 = BirthData("chart_33", 1910, 10, 31, 13, 41, 5.5, 13.0, 77.5833)


def _track_b(lons: dict[str, float], asc_lon: float = 0.0) -> RamanChart:
    return RamanChart.from_stated_positions(
        {p: {"lon": l, "bhava": 1} for p, l in lons.items()},
        asc_lon=asc_lon, ayanamsa="raman")


def _with_shadbala(chart: RamanChart, totals: dict[str, float]) -> RamanChart:
    """Immutable copy of `chart` with synthetic total Shadbala (Shashtiamsas)."""
    planets = dict(chart.planets)
    for name, total in totals.items():
        planets[name] = dataclasses.replace(
            planets[name],
            shadbala_rupas=ShadbalaBreakdown(0, 0, 0, 0, 0, 0, total))
    return dataclasses.replace(chart, planets=planets)


def _dhana_chart() -> RamanChart:
    """Taurus lagna (asc 40deg): Mercury (H2 lord) in Pisces=H11, Jupiter (H11 lord
    + H2 wealth karaka) in Gemini=H2 -> the 2-11 parivartana fires Y.DHANA.EXCH.
    Mercury strong / Jupiter weak by synthetic Shadbala -> weak-pillar borderline
    'mixed' on H2 wealth (lone benefic H2.P.Jupiter; H2.L.11 neutral; D9 neutral).

    Venus in Leo (H4, a kendra from Lagna) grants NeechaBhanga to Mercury in
    Pisces (Venus is the planet exalted in Pisces → condition 2 of cancellation
    of debilitation), preventing H2.C.24 (debilitated 2nd lord) from firing."""
    chart = _track_b({"Mercury": 330.5, "Jupiter": 63.83, "Moon": 310.0,
                      "Venus": 130.0},
                     asc_lon=40.0)
    return _with_shadbala(chart, {"Mercury": 480.0, "Jupiter": 200.0, "Moon": 250.0})


def _kemadruma_chart() -> RamanChart:
    """Aries lagna, a lone Moon in Taurus (house 2): no planet flanks the Moon and
    no bhanga branch (kendra-from-Lagna/Moon, conjunction, benefic drishti) holds
    -> Y.KEMADRUMA (uncancelled) fires."""
    return _track_b({"Moon": 40.0}, asc_lon=0.0)


def _h5_chart(*, weak: bool) -> RamanChart:
    """Aries lagna (asc 10deg), Jupiter in Leo=H5 (benefic H5.P.Jupiter), Sun (H5
    lord) in Sagittarius=H9 (benefic H5.L.9) -> H5 children reads 'favourable' on
    the Track-B polarity fallback (lone-benefic evidence, no malefic).

    The two longitude sets differ only enough to flip the sphuta verdicts and are
    pinned through :func:`beeja_kshetra` itself in test_sphuta_pins_hold below:
      weak   -> beeja_strong=False AND kshetra_strong=False (gate engages);
      strong -> beeja_strong=True  AND kshetra_strong=True  (metadata only)."""
    if weak:
        lons = {"Sun": 245.0, "Venus": 200.0, "Mars": 280.0, "Moon": 305.0,
                "Jupiter": 125.0}
    else:
        lons = {"Sun": 240.0, "Venus": 183.0, "Mars": 270.0, "Moon": 303.0,
                "Jupiter": 125.0}
    return _track_b(lons, asc_lon=10.0)


def _sig(house: int, key: str) -> Signification:
    s = next((s for s in significations_of(house) if s.key == key), None)
    assert s is not None, f"no signification {key!r} for house {house}"
    return s


def _fired_yoga(id_: str, kind: str) -> FiredYoga:
    return FiredYoga(id=id_, name=id_, kind=kind, effect="",
                     source=Citation("HTJAH-I", 480))


def _fired_rule(polarity: str):
    """A synthetic FiredRule carrying only the polarity the modulators read."""
    from app.raman_saab.doctrine.rules import RuleRecord
    from app.raman_saab.judges import rule_firing as rf
    rule = RuleRecord(
        id=f"TEST.{polarity}", house=1, signification="self", group="combination",
        kind="evaluable", condition=None, fortified="ok", afflicted="bad",
        frame="LAGNA", varga="D1", polarity=polarity,
        source=Citation("HTJAH-I", 1))
    return rf.FiredRule(rule=rule, branch="fortified", text="ok")


def _clean_mixed_ledger(**over) -> ht.FrameLedger:
    """A borderline-mixed ledger: weak lord, strong karaka, neutral-only evidence."""
    base = dict(
        frame="lagna", lord="Mars", lord_strong=False, karaka="Sun",
        karaka_strong=True, bhava_bala=None, bhava_bala_strong=None,
        navamsa_status="neutral", karaka_intact=True, maraka_active=False,
        parivartana_resilient=False, lord_karaka_identical=False,
        fired_benefic=(), fired_malefic=(), fired_neutral=(), flags=())
    base.update(over)
    return ht.FrameLedger(**base)


# ---------------------------------------------------------------------------
# 1. Metadata plumbing
# ---------------------------------------------------------------------------

class TestMetadata:
    """SignificationVerdict/HouseProforma carry frozen-safe (key, value) metadata."""

    def test_metadata_default_is_empty_tuple(self):
        """A signification with no wired layer active carries metadata == ()."""
        chart = _track_b({"Saturn": 220.0})   # sparse: no yoga scope, no sphutas
        sv = ht.judge_signification(chart, 3, _sig(3, "courage"))
        assert sv.metadata == ()

    def test_metadata_pairs_are_string_tuples(self):
        """Every metadata entry is a (str, str) pair on every house of a real chart."""
        chart = cast_chart(_BANGALORE, ayanamsa="raman")
        for pf in ht.judge_all_houses(chart):
            assert isinstance(pf.metadata, tuple)
            for sv in pf.significations:
                for pair in sv.metadata:
                    assert isinstance(pair, tuple) and len(pair) == 2
                    assert isinstance(pair[0], str) and isinstance(pair[1], str)

    def test_metadata_deterministic_same_chart_twice(self):
        """Judging the same chart twice yields identical metadata and verdicts."""
        chart = cast_chart(_BANGALORE, ayanamsa="raman")
        for h in range(1, 13):
            a, b = ht.judge_house(chart, h), ht.judge_house(chart, h)
            assert a.metadata == b.metadata
            assert [sv.metadata for sv in a.significations] == \
                   [sv.metadata for sv in b.significations]
            assert [sv.verdict for sv in a.significations] == \
                   [sv.verdict for sv in b.significations]

    def test_house_proforma_metadata_unions_significations(self):
        """HouseProforma.metadata is the deduplicated union of its significations'."""
        chart = cast_chart(_BANGALORE, ayanamsa="raman")
        for h in (8, 11):
            pf = ht.judge_house(chart, h)
            for sv in pf.significations:
                for pair in sv.metadata:
                    assert pair in pf.metadata


# ---------------------------------------------------------------------------
# 2. H5 Beeja/Kshetra fertility GATE (HTJAH-I:5517-5527).
# ---------------------------------------------------------------------------

class TestFertilityGate:
    """Mandatory H5 fertility pre-pass: a single weak sphuta is weighed, but BOTH
    barren (Stage-3 'O1') is decisive progeny DENIAL -> afflicted."""

    def test_sphuta_pins_hold(self):
        """The two _h5_chart longitude sets really produce both-weak / both-strong
        sphutas (the premise every other gate test builds on)."""
        from app.raman_saab.primitives.sphutas import beeja_kshetra
        weak = beeja_kshetra(_h5_chart(weak=True))
        strong = beeja_kshetra(_h5_chart(weak=False))
        assert (weak.beeja_strong, weak.kshetra_strong) == (False, False)
        assert (strong.beeja_strong, strong.kshetra_strong) == (True, True)

    def test_weak_sphutas_deny_children_afflicted(self):
        """Both sphutas weak (beeja even-sign, kshetra odd-sign) DENY a favourable
        children verdict to afflicted (Stage-3 'O1': both seed and field barren),
        with ('beeja_kshetra','weak') recorded."""
        chart = _h5_chart(weak=True)
        sv = ht.judge_signification(chart, 5, _sig(5, "children"))
        assert sv.verdict == "afflicted"
        assert ("beeja_kshetra", "weak") in sv.metadata

    def test_weak_sphutas_set_fertility_gate_flag(self):
        """The engaged gate marks the lead ledger with FERTILITY_GATE."""
        chart = _h5_chart(weak=True)
        sv = ht.judge_signification(chart, 5, _sig(5, "children"))
        assert "FERTILITY_GATE" in sv.ledger.flags

    def test_gate_denies_on_both_barren_sphutas(self):
        """Stage-3 'O1' doctrinal shift: when BOTH sphutas are barren the gate DOES
        deny (afflicted) — the strongest classical progeny signal. (A single weak
        sphuta is still only weighed, via the 'numeric_partial' branch.)"""
        chart = _h5_chart(weak=True)
        sv = ht.judge_signification(chart, 5, _sig(5, "children"))
        assert sv.verdict == "afflicted"

    def test_strong_sphutas_metadata_only(self):
        """Beeja odd/odd + kshetra even/even -> 'numeric_strong' metadata (the
        HTJAH-I:5524-5527 aspect/Rahu clauses are NOT checked here), verdict untouched."""
        chart = _h5_chart(weak=False)
        sv = ht.judge_signification(chart, 5, _sig(5, "children"))
        assert sv.verdict == "favourable"
        assert ("beeja_kshetra", "numeric_strong") in sv.metadata
        assert "FERTILITY_GATE" not in sv.ledger.flags

    def test_gate_scoped_to_children_not_intellect(self):
        """The fertility gate touches children/progeny only: H5 intellect on the same
        weak-sphuta chart keeps its favourable verdict (no doctrinal basis to clamp)."""
        chart = _h5_chart(weak=True)
        sv = ht.judge_signification(chart, 5, _sig(5, "intellect"))
        assert sv.verdict == "favourable"

    def test_gate_none_safe_on_sparse_chart(self):
        """A chart missing a sphuta planet (no Venus) skips the gate without error."""
        chart = _track_b({"Sun": 245.0, "Mars": 280.0, "Moon": 305.0,
                          "Jupiter": 125.0}, asc_lon=10.0)
        sv = ht.judge_signification(chart, 5, _sig(5, "children"))
        assert all(k != "beeja_kshetra" for k, _ in sv.metadata)
        assert "FERTILITY_GATE" not in sv.ledger.flags


# ---------------------------------------------------------------------------
# 3. Yoga modifier — consideration #4 (HTJAH-I:480-482).
# ---------------------------------------------------------------------------

class TestYogaModulation:
    """Kind-scoped, one-step, borderline-only modulation; decisive never overturned."""

    def test_dhana_chart_fires_2_11_exchange(self):
        """The synthetic Taurus chart's Mercury<->Jupiter exchange fires Y.DHANA.EXCH."""
        assert "Y.DHANA.EXCH" in {y.id for y in detect_yogas(_dhana_chart())}

    def test_dhana_lifts_borderline_h2_mixed_to_favourable(self):
        """A fired dhana yoga lifts a borderline H2 wealth 'mixed' (no fired malefic)
        one step to favourable, recording ('yoga','Y.DHANA.EXCH:lift')."""
        chart = _dhana_chart()
        sv = ht.judge_signification(chart, 2, _sig(2, "wealth"))
        assert sv.verdict == "favourable"
        assert ("yoga", "Y.DHANA.EXCH:lift") in sv.metadata
        assert sv.borderline_shifted is True

    def test_dhana_never_overrides_contradiction(self):
        """A contradiction-mixed (benefic AND malefic fired) is NEVER lifted by dhana."""
        L = _clean_mixed_ledger(fired_benefic=(_fired_rule("benefic"),),
                                fired_malefic=(_fired_rule("malefic"),))
        fired = (_fired_yoga("Y.DHANA.EXCH", "dhana"),)
        v, shifted, _ = ht._yoga_modulate("mixed", L, _sig(2, "wealth"), fired)
        assert v == "mixed" and shifted is False

    def test_arishta_chart_fires_uncancelled_kemadruma(self):
        """The lone-Moon chart forms Kemadruma with no bhanga -> Y.KEMADRUMA fires."""
        assert "Y.KEMADRUMA" in {y.id for y in detect_yogas(_kemadruma_chart())}

    def test_arishta_drops_borderline_h1_mixed_to_afflicted(self):
        """A fired uncancelled Kemadruma weighs a borderline H1 self 'mixed' down one
        step to afflicted, recording ('yoga','Y.KEMADRUMA:drop')."""
        fired = detect_yogas(_kemadruma_chart())
        v, shifted, md = ht._yoga_modulate(
            "mixed", _clean_mixed_ledger(), _sig(1, "self"), fired)
        assert v == "afflicted" and shifted is True
        assert ("yoga", "Y.KEMADRUMA:drop") in md

    def test_arishta_never_overrides_contradiction(self):
        """A contradiction-mixed (benefic AND malefic both fired) is NEVER dropped by
        an arishta — dropping would hide live benefic testimony; ':noted' only."""
        L = _clean_mixed_ledger(fired_benefic=(_fired_rule("benefic"),),
                                fired_malefic=(_fired_rule("malefic"),))
        fired = (_fired_yoga("Y.KEMADRUMA", "arishta"),)
        v, shifted, md = ht._yoga_modulate("mixed", L, _sig(1, "self"), fired)
        assert v == "mixed" and shifted is False
        assert ("yoga", "Y.KEMADRUMA:noted") in md
        assert ("yoga", "Y.KEMADRUMA:drop") not in md

    def test_arishta_noted_not_dropped_under_longevity_guard(self):
        """The LONGEVITY_GUARD arm of the arishta branch (currently unreachable in
        production wiring: arishta scope = H1 self, guard = H8 longevity/death —
        disjoint) is pinned as defensive code: a guarded mixed stays mixed, ':noted'."""
        L = _clean_mixed_ledger(flags=("LONGEVITY_GUARD",))
        fired = (_fired_yoga("Y.KEMADRUMA", "arishta"),)
        v, shifted, md = ht._yoga_modulate("mixed", L, _sig(1, "self"), fired)
        assert v == "mixed" and shifted is False
        assert ("yoga", "Y.KEMADRUMA:noted") in md
        assert ("yoga", "Y.KEMADRUMA:drop") not in md

    def test_chart33_h1_drop_is_sakata_not_kemadruma(self):
        """Golden-adjacent pin of the chart_33 mechanism: fresh-cast HTJAH-I.chart_33
        (1910-10-31 13:41 IST Bangalore) forms Y.SAKATA — Moon Virgo is 12th from
        Jupiter Libra (3HC:2984, no cancellation cited) — while Kemadruma does NOT
        form (the Moon has planets in the 2nd from it). The H1 'self' flip to
        afflicted is therefore driven by ('yoga','Y.SAKATA:drop'), benefic-only
        strength-split ledger, untouched by the contradiction guard."""
        chart = cast_chart(_CHART_33, ayanamsa="raman")
        fired_ids = {y.id for y in detect_yogas(chart)}
        assert "Y.SAKATA" in fired_ids and "Y.KEMADRUMA" not in fired_ids
        pf = ht.judge_house(chart, 1)
        sv = next(s for s in pf.significations if s.signification == "self")
        assert sv.verdict == "afflicted"
        assert ("yoga", "Y.SAKATA:drop") in sv.metadata
        assert all(not v.startswith("Y.KEMADRUMA")
                   for k, v in sv.metadata if k == "yoga")

    def test_navamsa_then_yoga_order(self):
        """Order pin: _decide runs the navamsa modulation BEFORE the yoga layer.
        A borderline H2 wealth mixed (weak lord, strong karaka, neutral-only
        evidence) confirmed by D9 is already 'favourable' when a fired dhana yoga
        sees it -> the yoga records ':noted', NOT ':lift' (decisive never re-shifted)."""
        L = _clean_mixed_ledger(navamsa_status="confirms",
                                fired_neutral=(_fired_rule("neutral"),))
        v, shifted = ht._decide(L)
        assert v == "favourable" and shifted is True
        fired = (_fired_yoga("Y.DHANA.EXCH", "dhana"),)
        v2, yoga_shifted, md = ht._yoga_modulate(v, L, _sig(2, "wealth"), fired)
        assert v2 == "favourable" and yoga_shifted is False
        assert ("yoga", "Y.DHANA.EXCH:noted") in md
        assert ("yoga", "Y.DHANA.EXCH:lift") not in md

    def test_raja_lifts_borderline_h10_mixed(self):
        """A fired raja yoga lifts a borderline H10 career 'mixed' to favourable."""
        fired = (_fired_yoga("Y.RAJA.KT", "raja"),)
        v, shifted, md = ht._yoga_modulate(
            "mixed", _clean_mixed_ledger(), _sig(10, "career"), fired)
        assert v == "favourable" and shifted is True
        assert ("yoga", "Y.RAJA.KT:lift") in md

    def test_raja_surfaces_metadata_on_h9_h10(self):
        """Bangalore fires raja yogas (Y.RAJA.KT / Y.RAJA.910X); H9 fortune and H10
        career significations surface them as ('yoga', ...) metadata."""
        chart = cast_chart(_BANGALORE, ayanamsa="raman")
        assert any(y.kind == "raja" for y in detect_yogas(chart))
        for house, key in ((9, "fortune"), (10, "career")):
            sv = ht.judge_signification(chart, house, _sig(house, key))
            assert any(k == "yoga" and v.startswith("Y.RAJA")
                       for k, v in sv.metadata)

    def test_decisive_favourable_never_dropped_by_arishta(self):
        """An arishta NEVER overturns a decisive favourable (one direction)."""
        fired = (_fired_yoga("Y.KEMADRUMA", "arishta"),)
        v, shifted, _ = ht._yoga_modulate(
            "favourable", _clean_mixed_ledger(), _sig(1, "self"), fired)
        assert v == "favourable" and shifted is False

    def test_decisive_afflicted_never_lifted_by_dhana(self):
        """A dhana yoga NEVER overturns a decisive afflicted (other direction)."""
        fired = (_fired_yoga("Y.DHANA.EXCH", "dhana"),)
        v, shifted, _ = ht._yoga_modulate(
            "afflicted", _clean_mixed_ledger(), _sig(2, "wealth"), fired)
        assert v == "afflicted" and shifted is False

    def test_out_of_scope_house_untouched(self):
        """A dhana yoga has no effect (verdict OR metadata) on an H5 children matter."""
        fired = (_fired_yoga("Y.DHANA.EXCH", "dhana"),)
        v, shifted, md = ht._yoga_modulate(
            "mixed", _clean_mixed_ledger(), _sig(5, "children"), fired)
        assert v == "mixed" and shifted is False and md == ()

    def test_non_mixed_verdict_still_surfaces_noted_metadata(self):
        """On the Kemadruma chart H1 reads insufficient-evidence (no fired rules);
        the relevant arishta is surfaced as ':noted' without shifting the verdict."""
        chart = _kemadruma_chart()
        sv = ht.judge_signification(chart, 1, _sig(1, "self"))
        assert sv.verdict == "insufficient-evidence"
        assert ("yoga", "Y.KEMADRUMA:noted") in sv.metadata


# ---------------------------------------------------------------------------
# 4. Lookup-grid metadata surfacing (None-safe, metadata-only).
# ---------------------------------------------------------------------------

class TestLookupMetadata:
    """Doctrine grids ride along as metadata; they never change a verdict."""

    def test_h8_decanate_cause_on_track_a(self):
        """Bangalore (Virgo lagna 175.43deg): 22nd drekkana falls in Taurus decanate 1
        -> lord Venus, cause 'asses, horses, mules' (HTJAH-II:3745) on H8 longevity."""
        chart = cast_chart(_BANGALORE, ayanamsa="raman")
        sv = ht.judge_signification(chart, 8, _sig(8, "longevity"))
        assert ("drekkana22_lord", "Venus") in sv.metadata
        assert any(k == "decanate_cause" and "asses, horses, mules" in v
                   for k, v in sv.metadata)

    def test_h8_decanate_skipped_on_track_b(self):
        """Track-B charts carry no maraka_points -> the decanate fallback is skipped."""
        chart = _track_b({"Saturn": 220.0})
        sv = ht.judge_signification(chart, 8, _sig(8, "longevity"))
        assert all(k not in ("drekkana22_lord", "decanate_cause")
                   for k, _ in sv.metadata)

    def test_h8_scoped_to_death_and_longevity_keys(self):
        """H8 sudden_gains is not a death matter -> no decanate metadata."""
        chart = cast_chart(_BANGALORE, ayanamsa="raman")
        sv = ht.judge_signification(chart, 8, _sig(8, "sudden_gains"))
        assert all(k not in ("drekkana22_lord", "decanate_cause")
                   for k, _ in sv.metadata)

    def test_h11_source_of_gains_for_occupants(self):
        """Bangalore has Sun/Mercury/Jupiter (and Ketu) in the 11th: each printed
        planet's income channel is attached; the node (unprinted) is skipped."""
        chart = cast_chart(_BANGALORE, ayanamsa="raman")
        sv = ht.judge_signification(chart, 11, _sig(11, "gains"))
        channels = [v for k, v in sv.metadata if k == "source_of_gains"]
        assert any(v.startswith("Sun:") for v in channels)
        assert any(v.startswith("Jupiter:") for v in channels)
        assert not any(v.startswith("Ketu:") for v in channels)

    def test_h11_no_occupants_no_metadata(self):
        """An empty 11th house attaches no source_of_gains rows."""
        chart = _track_b({"Saturn": 220.0})   # Saturn in H8 only
        sv = ht.judge_signification(chart, 11, _sig(11, "gains"))
        assert all(k != "source_of_gains" for k, _ in sv.metadata)

    def test_h12_karaka_in_12_inversion(self):
        """Saturn in the 12th (Aries lagna, Pisces) -> Bhavartha Ratnakara inversion:
        fortunate re the 6th/8th/12th indications (HTJAH-II:16554...)."""
        chart = _track_b({"Saturn": 340.0})   # Pisces = house 12 from Aries
        sv = ht.judge_signification(chart, 12, _sig(12, "loss_moksha"))
        rows = [v for k, v in sv.metadata if k == "karaka_in_12"]
        assert rows and rows[0].startswith("Saturn:")

    def test_h12_mercury_inversion_is_skipped(self):
        """Mercury in the 12th has NO printed bhava (source-faithful None) -> no row."""
        chart = _track_b({"Mercury": 340.0})
        sv = ht.judge_signification(chart, 12, _sig(12, "loss_moksha"))
        assert all(k != "karaka_in_12" for k, _ in sv.metadata)

    def test_h12_confinement_mode_when_incarceration_rules_fire(self):
        """Aries lagna + Saturn in the 12th fires malefic H12.P.Saturn on the
        incarceration matter -> Bandhana mode 'bound by ropes' (HTJAH-II:16431)."""
        chart = _track_b({"Saturn": 340.0})
        sv = ht.judge_signification(chart, 12, _sig(12, "incarceration"))
        assert ("confinement_mode", "bound by ropes") in sv.metadata

    def test_h12_confinement_skipped_without_fired_malefic(self):
        """No malefic evidence on the incarceration matter -> no confinement row.
        (Saturn in Virgo=H6 is not the 12th lord and fires nothing on H12.)"""
        chart = _track_b({"Saturn": 160.0})
        sv = ht.judge_signification(chart, 12, _sig(12, "incarceration"))
        assert all(k != "confinement_mode" for k, _ in sv.metadata)

    def test_h6_organ_and_tridosha_for_afflicting_occupants(self):
        """Saturn occupying the 6th (Virgo, Aries lagna) attaches its printed organ
        (legs/tibia/fibula, HTJAH-I:6439-6441) and tridosha (vatha+pitta, :6458)."""
        chart = _track_b({"Saturn": 160.0})   # Virgo = house 6 from Aries
        sv = ht.judge_signification(chart, 6, _sig(6, "enemies_disease"))
        assert any(k == "organ_of" and v.startswith("Saturn:")
                   for k, v in sv.metadata)
        assert any(k == "tridosha_of" and v.startswith("Saturn:")
                   for k, v in sv.metadata)

    def test_h6_benefic_occupant_not_treated_as_afflictor(self):
        """Jupiter in the 6th is not an afflicting (natural-malefic) occupant -> no
        organ/tridosha rows are attached for it."""
        chart = _track_b({"Jupiter": 160.0})
        sv = ht.judge_signification(chart, 6, _sig(6, "enemies_disease"))
        assert all(k not in ("organ_of", "tridosha_of") for k, _ in sv.metadata)


# ---------------------------------------------------------------------------
# 5. chart_overview — the §9 pre-pass surface.
# ---------------------------------------------------------------------------

class TestChartOverview:
    """ChartOverview gathers frame strength, natures, yogas, and special points."""

    def test_bangalore_overview_fields(self):
        """Track A: every field is populated with the expected shapes/domains."""
        chart = cast_chart(_BANGALORE, ayanamsa="raman")
        ov = co.chart_overview(chart)
        assert ov.stronger_frame in ("lagna", "moon")
        names = [n for n, _ in ov.functional_natures]
        assert "Sun" in names and "Saturn" in names
        assert all(nat in ("benefic", "malefic", "neutral", "yogakaraka", "maraka")
                   for _, nat in ov.functional_natures)
        assert ov.fired_yogas and all(isinstance(y, FiredYoga) for y in ov.fired_yogas)
        assert ov.dhana_lagna_sign in range(1, 13)
        assert isinstance(ov.beeja_strong, bool) and isinstance(ov.kshetra_strong, bool)

    def test_bangalore_overview_matches_detect_yogas(self):
        """The overview's fired_yogas is exactly detect_yogas(chart)."""
        chart = cast_chart(_BANGALORE, ayanamsa="raman")
        assert co.chart_overview(chart).fired_yogas == detect_yogas(chart)

    def test_track_b_overview_none_safe(self):
        """A sparse Track-B chart (lone Saturn): lead defaults to lagna; the Moon-less
        sphuta/dhana-lagna specials are None; only Saturn carries a nature."""
        chart = _track_b({"Saturn": 220.0})
        ov = co.chart_overview(chart)
        assert ov.stronger_frame == "lagna"
        assert ov.dhana_lagna_sign is None
        assert ov.beeja_strong is None and ov.kshetra_strong is None
        assert [n for n, _ in ov.functional_natures] == ["Saturn"]

    def test_overview_is_frozen(self):
        """ChartOverview is immutable (frozen dataclass)."""
        ov = co.chart_overview(_track_b({"Saturn": 220.0}))
        with pytest.raises(dataclasses.FrozenInstanceError):
            ov.stronger_frame = "moon"  # type: ignore[misc]

    def test_overview_deterministic(self):
        """Two overviews of the same chart are equal (deterministic pre-pass)."""
        chart = cast_chart(_BANGALORE, ayanamsa="raman")
        assert co.chart_overview(chart) == co.chart_overview(chart)


# ---------------------------------------------------------------------------
# 6. Legacy compatibility — the back-compat shim stays green.
# ---------------------------------------------------------------------------

class TestLegacyShim:
    """as_house_verdict keeps its legacy shape with the new layers wired in."""

    def test_as_house_verdict_still_legacy_shaped(self):
        """The dhana chart's H2 proforma still collapses to a legacy HouseVerdict
        with the lagna-frame lord and tuple evidence."""
        from app.raman_saab.judges.house_judge import HouseVerdict
        pf = ht.judge_house(_dhana_chart(), 2)
        hv = pf.as_house_verdict()
        assert isinstance(hv, HouseVerdict)
        assert hv.lord == "Mercury"
        assert isinstance(hv.benefic, tuple)

    def test_metadata_absent_from_legacy_verdict(self):
        """HouseVerdict (legacy) has no metadata attribute — the shim adds nothing."""
        pf = ht.judge_house(_dhana_chart(), 2)
        assert not hasattr(pf.as_house_verdict(), "metadata")
