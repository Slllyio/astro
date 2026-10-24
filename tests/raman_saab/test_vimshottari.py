"""Vimshottari Dasha timeline — validated against the canonical pin + Raman's dated deaths.

The Mahadasha running at the death date reproduces Raman's stated period for every dated
death golden; the canonical chart's birth Mahadasha is Mercury (CLAUDE.md test pin).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData
from app.raman_saab.primitives import vimshottari as vd

_GOLDENS = Path(__file__).resolve().parents[1] / "fixtures" / "raman_goldens.jsonl"

# Raman's stated death Mahadasha/Bhukti for the dated death goldens (from the verdict prose).
_STATED_DEATH_DASHA = {
    "HTJAH-II.chart_35": ("Rahu", "Sun"),
    "HTJAH-II.chart_73": ("Saturn", "Mercury"),   # Lincoln
    "HTJAH-II.chart_74": ("Jupiter", "Sun"),       # Gandhi
    "HTJAH-II.chart_78": ("Rahu", "Moon"),         # Hitler
}


def _canonical_chart():
    return cast_chart(BirthData(name="c", year=1990, month=7, day=15, hour=12, minute=0,
                                tz_offset=5.5, latitude=12.97, longitude=77.59), ayanamsa="raman")


def _golden_chart(cid: str):
    for ln in _GOLDENS.read_text(encoding="utf-8").splitlines():
        s = ln.strip()
        if not s or s.startswith("#"):
            continue
        r = json.loads(s)
        if r["id"] != cid:
            continue
        b = r["birth"]
        dp, _, tp = str(b["dt"]).partition("T")
        y, mo, d = (int(x) for x in dp.split("-"))
        hh, mm = int(tp.split(":")[0]), int(tp.split(":")[1])
        chart = cast_chart(BirthData(name="g", year=y, month=mo, day=d, hour=hh, minute=mm,
                                     tz_offset=float(b["tz"]), latitude=float(b["lat"]),
                                     longitude=float(b["lon"])), ayanamsa="raman")
        el = r.get("expected_longevity") or {}
        return chart, el.get("death_date")
    raise KeyError(cid)


def test_canonical_birth_mahadasha_is_mercury():
    """CLAUDE.md pin: Bangalore 1990-07-15 -> Mercury Mahadasha at birth."""
    ch = _canonical_chart()
    period = vd.dasha_on(ch, ch.jd_ut)
    assert period is not None and period.maha == "Mercury"


def test_timeline_is_contiguous_and_covers_a_full_cycle():
    """The Mahadasha periods are contiguous (no gaps/overlaps) and one cycle sums to 120y."""
    ch = _canonical_chart()
    tl = vd.mahadasha_timeline(ch)
    for a, b in zip(tl, tl[1:]):
        assert a.end_jd == pytest.approx(b.start_jd)            # contiguous
    nine = tl[:9]
    span_years = (nine[-1].end_jd - nine[0].start_jd) / 365.2425
    assert span_years == pytest.approx(120.0, abs=0.01)         # a full cycle


@pytest.mark.parametrize("cid", list(_STATED_DEATH_DASHA))
def test_death_mahadasha_matches_raman(cid: str):
    """The Mahadasha running at the death date reproduces Raman's stated MD for every
    dated death golden (the core timing validation)."""
    chart, death_date = _golden_chart(cid)
    dy, dmo, dd = (int(x) for x in death_date.split("-"))
    period = vd.dasha_on(chart, vd.date_to_jd(dy, dmo, dd))
    assert period is not None
    assert period.maha == _STATED_DEATH_DASHA[cid][0], \
        f"{cid}: engine MD {period.maha!r} != Raman {_STATED_DEATH_DASHA[cid][0]!r}"


def test_death_bhukti_matches_raman_for_clean_births():
    """For the two precisely-timed births, the Bhukti also matches exactly (Lincoln
    Saturn/Mercury, Hitler Rahu/Moon)."""
    for cid in ("HTJAH-II.chart_73", "HTJAH-II.chart_78"):
        chart, death_date = _golden_chart(cid)
        dy, dmo, dd = (int(x) for x in death_date.split("-"))
        period = vd.dasha_on(chart, vd.date_to_jd(dy, dmo, dd))
        assert (period.maha, period.antar) == _STATED_DEATH_DASHA[cid]


@pytest.mark.parametrize("cid", list(_STATED_DEATH_DASHA))
def test_death_falls_in_a_maraka_period(cid: str):
    """The strong, robust death-timing claim: the death's Mahadasha lord is a maraka, and the
    death falls in a maraka period, for every dated death golden (the engine recognises the
    death period as death-dealing — incl. the functional Rahu/Jupiter marakas)."""
    chart, death_date = _golden_chart(cid)
    dy, dmo, dd = (int(x) for x in death_date.split("-"))
    jd = vd.date_to_jd(dy, dmo, dd)
    ms = vd.maraka_set(chart)
    assert vd.dasha_on(chart, jd).maha in ms.all()        # death-MD lord is a maraka
    assert vd.is_maraka_period(chart, jd)                 # death falls in a maraka period


def test_death_window_returns_maraka_periods_near_span():
    """death_window yields maraka periods in the alloted-span region; for a near-span death
    (Gandhi, died ~78 ≈ ayurdaya span) the death falls inside one. (Premature/violent deaths
    strike a strong EARLIER maraka the engine does not isolate — a documented limit.)"""
    chart, death_date = _golden_chart("HTJAH-II.chart_74")
    dy, dmo, dd = (int(x) for x in death_date.split("-"))
    jd = vd.date_to_jd(dy, dmo, dd)
    windows = vd.death_window(chart)
    assert windows and all(w.score > 0 for w in windows)
    assert any(w.start_jd <= jd < w.end_jd for w in windows)


def test_significator_windows_catch_relative_death_mds():
    """General event-timing soft claim (death-class): the stated relative-death Mahadasha lord
    is among the matter's significators (here the maraka set), so it appears as an active window.
    Validated for the relative-death goldens; gains/career events that fall in a yoga-specific
    Dasha are a documented partial (see DOCTRINE_BACKLOG)."""
    for cid, sig_key, event_md in (("HTJAH-I.h4_01", "mother", "Mars"),
                                   ("HTJAH-II.h7_13", "coverture", "Mars"),
                                   ("HTJAH-II.h7_12", "coverture", "Saturn")):
        chart, _ = _golden_chart(cid)
        grahas = {"maraka": vd.maraka_set(chart).all()}
        windows = vd.significator_dasha_windows(chart, grahas)
        assert event_md in {w.graha for w in windows}, f"{cid}: {event_md} not an active window"


# Non-death dated events: (id, primary event-house(s), stated Mahadasha lord). These are the
# matters the death-biased layer scored ~0% on; the general "Time of Fructification" timer-set
# must recognise the event-MD as a significator of the event house.
_NONDEATH_EVENTS = [
    ("HTJAH-I.chart_40", (2, 11), "Ketu"), ("HTJAH-I.chart_44", (2, 11), "Ketu"),
    ("HTJAH-II.h11_14", (11,), "Venus"), ("HTJAH-II.h11_17", (11,), "Saturn"),
    ("HTJAH-II.h11_18", (11,), "Mercury"), ("HTJAH-II.h10_01", (10,), "Rahu"),
    ("HTJAH-I.h4_05", (4,), "Jupiter"), ("HTJAH-I.h4_06", (4,), "Jupiter"),
    ("HTJAH-II.h9_15", (9, 12), "Ketu"), ("HTJAH-II.h9_17", (9, 12), "Sun"),
]


@pytest.mark.parametrize("cid,houses,event_md", _NONDEATH_EVENTS)
def test_nondeath_event_md_in_timer_set(cid: str, houses: tuple, event_md: str):
    """The general 'Time of Fructification' timer-set (HTJAH-I:4303/5315; HTJAH-II:9910/14496)
    recognises the stated event-MD as a significator of the event house — gains/career/
    acquisition/travel, NOT just death. (h10_05 Napoleon's Rahu needs the deeper Kujavad-Ketu
    constellation-chaining and is a documented edge, not in this set.)"""
    chart, _ = _golden_chart(cid)
    timers: set[str] = set()
    for h in houses:
        timers |= vd.timer_set(chart, h)
    assert event_md in timers, f"{cid}: {event_md} missing from timer_set{houses}"


def test_timer_set_discriminates_not_universal():
    """The timer-set must DISCRIMINATE — not every graha times every house (else the metric is
    vacuous). On the canonical chart, at least one graha is NOT an 11th-house timer."""
    assert len(vd.timer_set(_canonical_chart(), 11)) < 9


def test_timing_primitives_noop_on_track_b():
    """Track-B (stated-position) charts have no birth_jd -> timing primitives degrade cleanly."""
    from app.raman_saab.chart.model import RamanChart
    tb = RamanChart.from_stated_positions(
        {"Sun": {"lon": 10.0, "bhava": 1}, "Moon": {"lon": 40.0, "bhava": 2}},
        asc_lon=5.0, ayanamsa="raman")
    assert vd.death_window(tb) == ()
    assert vd.significator_dasha_windows(tb, {"maraka": frozenset({"Saturn"})}) == ()


def test_date_to_jd_and_dasha_on_outside_timeline():
    ch = _canonical_chart()
    assert vd.date_to_jd(2000, 1, 1) > vd.date_to_jd(1990, 1, 1)
    assert vd.dasha_on(ch, ch.jd_ut - 100 * 365.2425) is None   # before the timeline start


class TestTimerRoles:
    """Wave-2 (2026-08-18): the role-preserving `timer_roles` variant — the SAME six-factor
    logic as `timer_set` (HTJAH-I:1586-1596), decomposed so renderers can DERIVE the tier
    ("H2 par excellence [MD owns; AD aspects lord]") instead of asserting it."""

    def test_timer_roles_flattens_to_timer_set_for_every_house(self):
        """THE critical pin: for all 12 houses of the canonical chart, the planets carrying
        any role are EXACTLY timer_set — the two implementations can never drift (timer_set
        feeds the live verdict machinery and stays untouched)."""
        ch = _canonical_chart()
        for house in range(1, 13):
            roles = vd.timer_roles(ch, house)
            assert frozenset(roles) == vd.timer_set(ch, house), house
            assert all(tags for tags in roles.values()), house   # no planet without a role

    def test_timer_roles_flattens_to_timer_set_on_golden_charts(self):
        """The same equivalence on dated golden nativities (Lincoln, Hitler) — the pin is
        not an artifact of one chart's geometry."""
        for cid in ("HTJAH-II.chart_73", "HTJAH-II.chart_78"):
            chart, _dd = _golden_chart(cid)
            for house in range(1, 13):
                assert (frozenset(vd.timer_roles(chart, house))
                        == vd.timer_set(chart, house)), (cid, house)

    def test_role_tags_are_from_the_documented_vocabulary(self):
        """Every emitted tag is one of TIMER_ROLE_TAGS — the vocabulary Raman's factor list
        licenses (HTJAH-I:1586-1596 + the nodal dispositor rule, HTJAH-I:2764/8566)."""
        ch = _canonical_chart()
        for house in range(1, 13):
            for planet, tags in vd.timer_roles(ch, house).items():
                assert set(tags) <= set(vd.TIMER_ROLE_TAGS), (house, planet, tags)

    def test_structural_roles_are_assigned_correctly(self):
        """The house lord carries 'owns', the bhava karaka 'karaka', an occupant 'occupies'
        — spot-checked structurally on the canonical chart (Virgo Lagna pin)."""
        from app.raman_saab.chart.constants import SIGN_LORDS
        ch = _canonical_chart()
        for house in (1, 2, 7, 10):
            roles = vd.timer_roles(ch, house)
            lord = SIGN_LORDS[((ch.asc_sign - 1) + (house - 1)) % 12 + 1]
            assert "owns" in roles[lord], house
            # timing gap check fix 1 (HTJAH-I:8272): only the 7th of these prints a karaka
            karaka = vd.TIMER_KARAKA.get(house)
            if karaka is not None:
                assert "karaka" in roles[karaka], house
            else:
                assert not any("karaka" in tags for tags in roles.values()), house
            for name, p in ch.planets.items():
                if p.rasi_house == house:
                    assert "occupies" in roles[name], (house, name)

    def test_node_role_names_the_dispositor_rule(self):
        """A node in the set carries the 'node of a timer's sign' tag when its sign lord is a
        timer — the HTJAH-I:8566-8567 rule made visible."""
        ch = _canonical_chart()
        seen = False
        for house in range(1, 13):
            roles = vd.timer_roles(ch, house)
            for node in ("Rahu", "Ketu"):
                if node in roles and "node of a timer's sign" in roles[node]:
                    seen = True
        assert seen        # the canonical chart has nodal timers via dispositor


def _house_lord(ch, house: int) -> str:
    from app.raman_saab.chart.constants import SIGN_LORDS
    return SIGN_LORDS[((ch.asc_sign - 1) + (house - 1)) % 12 + 1]


class TestPrintedTimerLists:
    """Timing gap check fix 1 (USER DECISION 2026-10-24): the timer set follows Raman's
    printed per-house factor lists (HTJAH-I:1586-1588, 2584-2586, 3521-3526, 4306-4310,
    5318-5323, 6273-6275, 8268-8272, 12733-12738, 14071-14075, 16390-16395, 17730-17734)."""

    def test_karaka_only_where_raman_prints_one(self):
        """H1, H2, H8, H10, H11 print no karaka; H9's karaka is the Sun, not Jupiter
        (HTJAH-I:12737-12738)."""
        assert set(vd.TIMER_KARAKA) == {3, 4, 5, 6, 7, 9, 12}
        assert vd.TIMER_KARAKA[9] == "Sun"
        assert vd.TIMER_KARAKA[12] == "Saturn"

    def test_karaka_role_appears_only_on_printed_houses(self):
        """No planet carries the 'karaka' tag in a house whose printed list names none."""
        for cid in ("HTJAH-II.chart_73", "HTJAH-II.chart_78"):
            chart, _ = _golden_chart(cid)
            for house in range(1, 13):
                carriers = {p for p, t in vd.timer_roles(chart, house).items() if "karaka" in t}
                expected = {vd.TIMER_KARAKA[house]} if house in vd.TIMER_KARAKA else set()
                assert carriers == expected, (cid, house)

    def test_lord_from_moon_starts_at_the_second_house(self):
        """The 1st-house list stops at (e); '(f) lord of the 2nd from the Moon' starts with the
        2nd house (HTJAH-I:2586)."""
        ch = _canonical_chart()
        assert not any("lord from Moon" in t for t in vd.timer_roles(ch, 1).values())
        from app.raman_saab.chart.constants import SIGN_LORDS
        moon = ch.planets["Moon"]
        for house in range(2, 13):
            lfm = SIGN_LORDS[(moon.sign - 1 + house - 1) % 12 + 1]
            assert "lord from Moon" in vd.timer_roles(ch, house)[lfm], house

    def test_third_house_adds_the_karakas_associates(self):
        """H3: 'the Karaka, and the planets in association with or aspecting Karaka'
        (HTJAH-I:3526) — every planet conjoining or aspecting Mars is a 3rd-house timer."""
        from app.raman_saab.doctrine import drishti
        for cid in ("HTJAH-II.chart_73", "HTJAH-II.chart_78"):
            chart, _ = _golden_chart(cid)
            ts = vd.timer_set(chart, 3)
            mars = chart.planets["Mars"]
            for name, p in chart.planets.items():
                if name != "Mars" and (p.rasi_house == mars.rasi_house
                                       or drishti.aspects_planet(name, "Mars", chart)):
                    assert name in ts, (cid, name)


class TestNodeChannels:
    """Timing gap check fix 2: a node gives the results of its sign lord, the planet it joins,
    its star lord, and Saturn (Sanivad Rahu) / Mars (Kujavad Ketu) — HTJAH-I:4478-4479,
    8566-8567, 11740-11741, 12762-12763."""

    def test_napoleon_rahu_now_times_the_tenth(self):
        """The documented edge h10_05 (Napoleon's Rahu, previously missed) is recovered by the
        full node channels."""
        chart, _ = _golden_chart("HTJAH-II.h10_05")
        assert "Rahu" in vd.timer_set(chart, 10)

    def test_dictum_channel_follows_saturn_and_mars(self):
        """Rahu joins every house whose set holds Saturn; Ketu every house whose set holds
        Mars (the dictum channel is tested against the set before node channels apply)."""
        for cid in ("HTJAH-II.chart_73", "HTJAH-II.chart_78"):
            chart, _ = _golden_chart(cid)
            for house in range(1, 13):
                roles = vd.timer_roles(chart, house)
                if "Saturn" in roles:
                    assert "Rahu" in roles, (cid, house)
                if "Mars" in roles:
                    assert "Ketu" in roles, (cid, house)

    def test_star_lord_channel_uses_the_vimshottari_lord(self):
        """The star lord of a node is the Vimshottari lord of the nakshatra it occupies."""
        ch = _canonical_chart()
        rahu = ch.planets["Rahu"]
        expected = vd._SEQUENCE[(rahu.nakshatra - 1) % 9]
        assert vd.nakshatra_lord_of(ch, "Rahu") == expected


class TestOwnSetGrading:
    """Timing gap check fix 3: each house is graded on its OWN set, the MD lord's own bhukti
    grades "same lord" (HTJAH-I:1635, "the sub-period of another"), and the 2/11, 9/12 union is
    a labelled note only."""

    def test_own_bhukti_never_grades_par_excellence(self):
        """Over the canonical chart's first 60 years, no MD/MD bhukti grades par excellence."""
        ch = _canonical_chart()
        for md in vd.mahadasha_timeline(ch, 60.0):
            own = vd.bhuktis(md)[0]
            if own.end_jd <= ch.jd_ut:          # the birth MD's own bhukti ran before birth
                continue
            jd = max(own.start_jd + 1.0, ch.jd_ut)
            for a in vd.active_houses(ch, jd):
                assert a.grade == "same_lord", (md.maha, a)

    def test_grade_uses_the_house_own_set_only(self):
        """A lit house's grade agrees with membership in that house's own timer set."""
        ch = _canonical_chart()
        for md in vd.mahadasha_timeline(ch, 40.0):
            for bh in vd.bhuktis(md)[1:3]:
                for a in vd.active_houses(ch, bh.start_jd + 1.0):
                    ts = vd.timer_set(ch, a.house)
                    assert a.md_activates == (bh.maha in ts)
                    assert a.antar_activates == (bh.antar in ts)

    def test_period_tier_vocabulary(self):
        """The tiers are Raman's four plus 'same lord', strongest first."""
        assert vd.TIER_ORDER == ("par excellence", "ordinary", "same lord", "limited",
                                 "feeble")
        assert vd.running_top_tier("Moon", "Moon", True) == "same lord"
        assert vd.running_top_tier("Moon", "Mars", True) == "par excellence"
        assert vd.running_top_tier("Moon", "Mars", False) == "ordinary"


class TestLifespanGateAndMarakaOrder:
    """Timing gap check fixes 5 and 7: lifespan gating of Mahadashas (HTJAH-I:1578-1580,
    1622-1623; HPA-15:21-37) and Raman's order inside the primary maraka tier
    (HTJAH-I:783-784), tertiary Saturn breadth (HTJAH-I:793-794) and delegation
    (HTJAH-I:11194-11203)."""

    def test_gate_marks_late_mahadashas(self):
        """With a 30-year span, a Mahadasha starting after year 30 acts only as a bhukti."""
        ch = _canonical_chart()
        gate = vd.lifespan_gate(ch, 30.0)
        for md in vd.mahadasha_timeline(ch, 120.0):
            if md.maha in gate and md.start_jd >= ch.jd_ut + 30 * 365.2425:
                assert gate[md.maha] is False, md.maha

    def test_primary_rank_conjunct_over_lord(self):
        """A planet conjunct a 2nd/7th lord outranks the lord itself (weight 5 > 3)."""
        ch = _canonical_chart()
        ms = vd.maraka_set(ch)
        ranks = dict(ms.primary_rank)
        assert set(ranks) == set(ms.primary)
        for g, rk in ranks.items():
            assert ms.weight(g) == 2 + rk
        assert all(ms.weight(g) > ms.weight(s) for g in ms.primary for s in ms.secondary)

    def test_delegation_goes_to_the_node_in_the_late_marakas_sign(self):
        """A maraka whose Mahadasha is outside the span hands its power to a node in its
        sign (Saturn to Rahu on the canonical chart, whose Saturn MD starts after the span)."""
        from app.raman_saab.chart.constants import SIGN_LORDS
        ch = _canonical_chart()
        for node, giver in vd.delegated_marakas(ch):
            assert SIGN_LORDS[ch.planets[node].sign] == giver
            assert vd.lifespan_gate(ch)[giver] is False
