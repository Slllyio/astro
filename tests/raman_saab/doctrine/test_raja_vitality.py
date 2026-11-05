"""Raja yoga vitality (HTJAH-I:641-645): a raja yoga moves a verdict only when its causing
planets are within 12° of each other. One rule for the HTJAH lordship yogas and the 3HC ones."""
from __future__ import annotations

import dataclasses

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData
from app.raman_saab.doctrine.yogas import RAJA_VITALITY_ORB_DEG, detect_yogas, raja_yoga_vital

_BANGALORE = BirthData("X", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)


class TestRajaVitality:
    def test_orb_is_ramans_twelve_degrees(self):
        """HTJAH-I:643-644 — 'within 12° of each other'."""
        assert RAJA_VITALITY_ORB_DEG == 12.0

    def test_unmeasurable_raja_yogas_are_never_vital(self):
        """Exchange, aspect and positional raja yogas name no measurable causing pair."""
        chart = cast_chart(_BANGALORE, ayanamsa="raman")
        for yid in ("Y.RAJA.910X", "Y.RAJA.910A", "Y.VIPAREETA", "Y.CHAMARA", "Y.RAJA.263"):
            assert raja_yoga_vital(chart, yid) is False

    def test_association_vitality_follows_the_orb(self):
        """A kendra lord and a distinct trikona lord in one sign: vital at 5° apart, not at 20°."""
        from app.raman_saab.doctrine.yogas import _house_lord
        chart = cast_chart(_BANGALORE, ayanamsa="raman")
        k = _house_lord(10, chart)
        tl = next(_house_lord(h, chart) for h in (9, 5) if _house_lord(h, chart) != k)
        pk = chart.planets[k]
        base = (pk.sign - 1) * 30.0 + 2.0

        def placed(gap: float):
            planets = dict(chart.planets)
            planets[k] = dataclasses.replace(pk, lon=base)
            planets[tl] = dataclasses.replace(chart.planets[tl], lon=base + gap,
                                              sign=pk.sign, rasi_house=pk.rasi_house)
            return dataclasses.replace(chart, planets=planets)

        assert raja_yoga_vital(placed(5.0), "Y.RAJA.KT") is True
        # 20° apart, the pair itself fails; vital only if some OTHER pair qualifies.
        far = placed(20.0)
        assert raja_yoga_vital(far, "Y.RAJA.KT") == _other_pair_vital(far, {k, tl})


def _other_pair_vital(chart, exclude):
    from app.raman_saab.doctrine.yogas import _KENDRAS, _TRIKONAS, _house_lord
    ks = {_house_lord(h, chart) for h in _KENDRAS}
    ts = {_house_lord(h, chart) for h in _TRIKONAS}
    for a in ks:
        for b in ts:
            if a == b or {a, b} == exclude:
                continue
            pa, pb = chart.planets.get(a), chart.planets.get(b)
            if pa and pb and pa.rasi_house == pb.rasi_house:
                d = abs(pa.lon - pb.lon) % 360
                if min(d, 360 - d) <= 12.0:
                    return True
    return False
