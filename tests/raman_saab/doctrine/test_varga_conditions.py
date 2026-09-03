"""The varga gate: opening it to eight divisions must add capability and change nothing.

`_SUPPORTED_VARGAS` was `{"D9"}`. The engine has always CAST all sixteen Shodashavarga
divisions (`chart/varga.py`); what was missing was the ability for a Raman *rule* to say
that something happens in one. Widening the gate is therefore a semantic expansion of the
doctrine language, not new astronomy — and the risk it carries is not a wrong number but a
silently changed reading.

Three levels, because a predicate can return the same boolean and still change what the
reader sees:

* **primitive** — the cached `navamsa_sign` and the named varga API agree everywhere. This
  is what lets `_planet_varga_sign` treat D9 like every other division instead of keeping a
  special case that could drift.
* **predicate**  — the two generic varga conditions evaluate identically to the hand-written
  D9 logic they replaced, and now accept the other seven divisions.
* **report**     — nothing at all moved across the golden corpus (`doctrine_snapshot`).

D60 is asserted ABSENT on purpose: see `_SUPPORTED_VARGAS`.
"""
from __future__ import annotations

import pytest

from app.raman_saab.chart import varga as _v
from app.raman_saab.doctrine import conditions as C
from app.raman_saab.doctrine.conditions import EvalContext
from app.raman_saab.doctrine.rule_sets import ALL_RULES
from tools.raman_saab import doctrine_snapshot as ds


@pytest.fixture(scope="module")
def charts() -> list:
    """Every castable golden, built once."""
    out = []
    for rec in ds._h.load_goldens():
        try:
            out.append((ds._h._id(rec), ds._h.build_chart(rec)))
        except Exception:                      # test_goldens owns uncastable records
            continue
    assert len(out) > 300, "the golden corpus did not load"
    return out


class TestPrimitiveEquality:
    """Level A — the cached navamsa field and the named API are the same value."""

    def test_navamsa_sign_matches_the_named_api_for_every_golden_planet(self, charts) -> None:
        """`PlanetPos.navamsa_sign` is set to `varga.navamsa_sign(lon)` by both constructors
        and `_VARGA_FN[9]` is that same function, so this is exact by construction. Pinned
        because `_planet_varga_sign` relies on it to avoid special-casing D9."""
        checked = 0
        for cid, chart in charts:
            for name, p in chart.planets.items():
                assert p.navamsa_sign == _v.varga_sign_by_name(p.lon, "D9"), f"{cid}/{name}"
                checked += 1
        assert checked > 2000, "too few planets checked to be meaningful"

    def test_named_and_numbered_lookups_agree(self) -> None:
        """`varga_sign_by_name` must be a pure re-addressing of `varga_sign`, not a
        reimplementation — otherwise the two could diverge on a convention change."""
        for lon in (0.0, 7.3, 29.99, 123.456, 271.0, 359.99):
            for name, n in _v.VARGA_NUMBERS.items():
                assert _v.varga_sign_by_name(lon, name) == _v.varga_sign(lon, n), f"{name}@{lon}"

    def test_an_unknown_varga_name_raises(self) -> None:
        with pytest.raises(ValueError, match="unknown varga"):
            _v.varga_sign_by_name(10.0, "D11")


class TestTheGate:
    """What the doctrine language is now allowed to say."""

    def test_the_eight_admitted_divisions(self) -> None:
        assert C._SUPPORTED_VARGAS == {"D1", "D3", "D7", "D9", "D10", "D12", "D16", "D30"}

    def test_d60_is_absent_because_its_doctrine_has_no_citable_raman_source(self) -> None:
        """The shashtyamsa's named classes appear in no citable Raman source — GBB's
        "Shashtiamsa" hits are the UNIT of Shadbala (1/60 rupa), an unrelated meaning.
        Admitting D60 would invite encoding that table from a non-Raman classic. Seven
        rules stay parked on this deliberately."""
        assert "D60" not in C._SUPPORTED_VARGAS
        with pytest.raises(ValueError, match="unsupported varga"):
            C.VargaDignity("Sun", "D60", {"exalt"})

    def test_the_gate_is_narrower_than_what_the_engine_can_cast(self) -> None:
        """The gate is a doctrine decision, not a computational limit: every admitted varga
        is castable, and the engine can cast more than the gate admits."""
        castable = set(_v.VARGA_NUMBERS)
        assert C._SUPPORTED_VARGAS < castable
        assert all(v in castable for v in C._SUPPORTED_VARGAS)


class TestPredicateEquality:
    """Level B — the generalised conditions reproduce the D9 logic they replaced."""

    def test_varga_dignity_d9_matches_reading_the_cached_field(self, charts) -> None:
        """The pre-change implementation was `_varga_dignity(subj, p.navamsa_sign)`."""
        cond = C.VargaDignity("Sun", "D9", {"exalt", "debil", "own"})
        for cid, chart in charts[:80]:
            p = chart.planets.get("Sun")
            if p is None:
                continue
            expected = C._varga_dignity("Sun", p.navamsa_sign) in {"exalt", "debil", "own"}
            assert cond.evaluate(EvalContext(chart)) is expected, cid

    def test_in_varga_house_from_d9_matches_the_cached_field(self, charts) -> None:
        """The pre-change implementation counted `_house_from(p.navamsa_sign, origin)`."""
        cond = C.InVargaHouseFrom("Moon", "LAGNA", {6, 8, 12}, varga="D9")
        for cid, chart in charts[:80]:
            p = chart.planets.get("Moon")
            if p is None:
                continue
            origin = _v.navamsa_sign(chart.asc_lon)
            expected = C._house_from(p.navamsa_sign, origin) in {6, 8, 12}
            assert cond.evaluate(EvalContext(chart)) is expected, cid

    @pytest.mark.parametrize("varga", sorted({"D1", "D3", "D7", "D9", "D10", "D12", "D16", "D30"}))
    def test_every_admitted_varga_evaluates_without_error(self, varga, charts) -> None:
        """Constructing and evaluating in each division must be total — no division may
        raise, and none may silently return None where a boolean is required."""
        a = C.InVargaHouseFrom("Jupiter", "LAGNA", {1, 4, 7, 10}, varga=varga)
        b = C.VargaDignity("Jupiter", varga, {"exalt", "own"})
        for _cid, chart in charts[:40]:
            assert isinstance(a.evaluate(EvalContext(chart)), bool)
            assert isinstance(b.evaluate(EvalContext(chart)), bool)

    def test_both_endpoints_resolve_in_the_same_varga(self, charts) -> None:
        """Raman counts "in the Navamsha from the sign held by the 2nd lord"
        (HTJAH-I:1717-1718): the lord is identified in the RASI, then both it and the
        subject are located in the VARGA. Mixing a D1 origin with a D10 subject would be a
        different — and unsourced — claim, so the origin must move with the varga."""
        _cid, chart = charts[0]
        d9 = C._origin_varga_sign("LAGNA", chart, "D9")
        d10 = C._origin_varga_sign("LAGNA", chart, "D10")
        assert d9 == _v.varga_sign_by_name(chart.asc_lon, "D9")
        assert d10 == _v.varga_sign_by_name(chart.asc_lon, "D10")

    def test_d9_remains_the_default_so_existing_rules_read_unchanged(self) -> None:
        """The 50 shipped navamsa rules pass no `varga=`; the default is not a claim that
        D9 is privileged, only that those call sites keep their meaning."""
        c = C.InVargaHouseFrom("Sun", "LAGNA", 7)
        assert c.varga == "D9"

    def test_the_shipped_varga_rules_are_still_only_d9_and_d3(self) -> None:
        """Opening the gate must not have retagged any existing rule. D3's two rules reach
        the drekkana through their own local Condition subclasses, not through this gate."""
        used = {r.varga for r in ALL_RULES}
        assert used == {"D1", "D9", "D3"}, used


#: Level C — "nothing in the corpus moved" — is a STANDING guard, not a varga-specific one,
#: and lives in `tests/raman_saab/test_doctrine_snapshot.py`. It was written here first and
#: moved once a later deliberate change made it fail: a test whose name claims the varga
#: generalisation changed nothing must not be the thing that breaks when something else
#: deliberately does. It proved its worth on the way out — it caught both routing changes.
