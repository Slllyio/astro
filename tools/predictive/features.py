"""Feature building for the learned predictive test (docs/predictive/PREDICTIVE_PREREG_2026-11-02.md).

Builds, for development people only (quality tiers A and B):
  * the person table and the confound baseline;
  * Track G natal geometry (Lahiri sidereal, mean node, Swiss Ephemeris);
  * Track T natal text rules (Raman rule fires, Parashara house verdicts, KP indications and verdicts);
  * Task A targets (tags) and Task B case-crossover sets with their timing features.

Tier C (the sealed sets C1 and C2) is dropped on load and never touched. data/private is never read.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import swisseph as swe

BODIES = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu")
_SWE = {"Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS, "Mercury": swe.MERCURY,
        "Jupiter": swe.JUPITER, "Venus": swe.VENUS, "Saturn": swe.SATURN, "Rahu": swe.MEAN_NODE}
DASA_ORDER = ("Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury")
DASA_YEARS = dict(zip(DASA_ORDER, (7, 20, 6, 10, 7, 18, 16, 19, 17)))
LORD_CODE = {l: i for i, l in enumerate(DASA_ORDER)}
YEAR = 365.2425
DEV_TIERS = ("A", "B")
SEED = 20261102

TARGETS: dict[str, tuple[str, ...]] = {
    "A1_actor": (r"^Vocation : Entertainment : Actor/ Actress$",),
    "A2_public_office": (r"^Vocation : Politics : Public office$",),
    "A3_writer": (r"^Vocation : Writers : (?!Astrology$).+",),
    "A4_sports": (r"^Vocation : Sports : .+",),
    "A5_military": (r"^Vocation : Military : .+",),
    "A6_music": (r"^Vocation : Entertain/Music : .+",),
    "A7_law": (r"^Vocation : Law : .+",),
    "A8_divorces": (r"^Family : Relationship : Number of Divorces$",),
    "A9_kids_gt3": (r"^Family : Parenting : Kids more than 3$",),
    "A10_cancer": (r"^Diagnoses : Major Diseases : Cancer$",),
    "A11_homicide_victim": (r"^Passions : Criminal Victim : Homicide victim$",),
    "A12_short_life": (r"^Personal : Death : Short Life less than 29 Yrs$",),
}
AREA_OF_TARGET = {"A1_actor": "career", "A2_public_office": "career", "A3_writer": "career",
                  "A4_sports": "career", "A5_military": "career", "A6_music": "career", "A7_law": "career",
                  "A8_divorces": "marriage", "A9_kids_gt3": "children", "A10_cancer": "health",
                  "A11_homicide_victim": "lifespan", "A12_short_life": "lifespan"}


# ----------------------------------------------------------------------------- people

def load_people(derived: Path) -> pd.DataFrame:
    """Development people (tiers A+B) with a full birth date, time, place and tz. Tier C is dropped."""
    m = pd.read_parquet(Path(derived) / "raman" / "person_master.parquet")
    m = m[m.quality_tier.isin(DEV_TIERS)]
    m = m[m.birth_date.str.match(r"^\d{4}-\d\d-\d\d$", na=False)
          & m.birth_time.str.match(r"^\d{1,2}:\d\d", na=False)
          & m.latitude.notna() & m.longitude.notna() & m.tz_offset.notna()].copy()
    ymd = m.birth_date.str.split("-", expand=True).astype(int)
    hm = m.birth_time.str.split(":", expand=True)
    m["year"], m["month"], m["day"] = ymd[0], ymd[1], ymd[2]
    m["hour"] = hm[0].astype(int)
    m["minute"] = hm[1].astype(int)
    m["jd_ut"] = [swe.julday(y, mo, d, h + mi / 60 - tz, swe.GREG_CAL)
                  for y, mo, d, h, mi, tz in zip(m.year, m.month, m.day, m.hour, m.minute, m.tz_offset)]
    m["doy"] = pd.to_datetime(m.birth_date, errors="coerce").dt.dayofyear
    m = m[m.doy.notna()].copy()
    m["half_month"] = (m.month - 1) * 2 + (m.day > 15)
    hemi = np.where(m.latitude >= 0, "N", "S")
    band = pd.cut(m.latitude.abs(), [-1, 30, 45, 91], labels=["lo", "mid", "hi"]).astype(str)
    m["lat_band"] = [f"{h}{b}" for h, b in zip(hemi, band)]
    m["tags"] = m.categories_raw.fillna("").str.split(";")
    return m.set_index("person_id", drop=False)


def baseline_natal(p: pd.DataFrame) -> pd.DataFrame:
    a = 2 * np.pi * p.doy / 365.25
    return pd.DataFrame({"b_year": p.year, "b_doy_sin": np.sin(a), "b_doy_cos": np.cos(a),
                         "b_lat": p.latitude, "b_lon": p.longitude,
                         "b_tierA": (p.quality_tier == "A").astype(int),
                         "b_app_user": (p.population == "app_user").astype(int)}, index=p.index)


def targets(p: pd.DataFrame) -> pd.DataFrame:
    out = {}
    for name, pats in TARGETS.items():
        rx = [re.compile(x) for x in pats]
        out[name] = [int(any(r.search(t.strip()) for t in tags for r in rx)) for tags in p.tags]
    t = pd.DataFrame(out, index=p.index)
    dead = p.tags.apply(lambda ts: any(re.match(r"^\d{4} deaths$", x.strip()) for x in ts))
    t.loc[~dead, "A12_short_life"] = -1          # -1 = not eligible (alive or death unknown)
    return t


# ----------------------------------------------------------------------------- geometry

def _setup() -> None:
    swe.set_sid_mode(swe.SIDM_LAHIRI)


def natal_positions(jd: float, lat: float, lon: float) -> dict:
    """Sidereal longitudes, speeds, Lagna, MC, and Placidus house positions for one moment."""
    flg = swe.FLG_SWIEPH | swe.FLG_SPEED
    out = {}
    eps = swe.calc_ut(jd, swe.ECL_NUT)[0][0]
    hsys = b"P"
    try:
        cusps, ascmc = swe.houses(jd, lat, lon, hsys)
    except swe.Error:                       # Placidus undefined near the poles: Porphyry instead
        hsys = b"O"
        cusps, ascmc = swe.houses(jd, lat, lon, hsys)
    armc = ascmc[2]
    ay = swe.get_ayanamsa_ut(jd)
    for b in BODIES:
        xx = swe.calc_ut(jd, _SWE[b], flg)[0]
        try:
            hp = swe.house_pos(armc, lat, eps, (xx[0], xx[1]), hsys)
        except swe.Error:
            hp = float("nan")
        out[b] = ((xx[0] - ay) % 360.0, xx[3], hp)
    out["Lagna"] = (ascmc[0] - ay) % 360.0
    out["MC"] = (ascmc[1] - ay) % 360.0
    return out


def natal_G_row(pos: dict) -> dict:
    r = {}
    lag_sign = int(pos["Lagna"] // 30)
    for b in BODIES:
        L, spd, hp = pos[b]
        s = int(L // 30)
        r[f"g_{b}_sin"] = math.sin(math.radians(L))
        r[f"g_{b}_cos"] = math.cos(math.radians(L))
        r[f"g_{b}_sign"] = s
        r[f"g_{b}_nak"] = int(L // (360 / 27))
        r[f"g_{b}_retro"] = int(spd < 0) if b != "Rahu" else 0
        r[f"g_{b}_wsh"] = (s - lag_sign) % 12 + 1
        r[f"g_{b}_plac"] = hp
    for k in ("Lagna", "MC"):
        r[f"g_{k}_sin"] = math.sin(math.radians(pos[k]))
        r[f"g_{k}_cos"] = math.cos(math.radians(pos[k]))
    r["g_Lagna_sign"] = lag_sign
    for i, a in enumerate(BODIES):
        for b in BODIES[i + 1:]:
            r[f"g_pair_{a}_{b}"] = (int(pos[b][0] // 30) - int(pos[a][0] // 30)) % 12 + 1
    return r


def natal_G(p: pd.DataFrame, jd: np.ndarray | None = None) -> tuple[pd.DataFrame, dict]:
    """Track G natal features; `jd` overrides the birth moments (null N1). Returns (features, positions)."""
    _setup()
    jds = p.jd_ut.to_numpy() if jd is None else jd
    rows, poss = [], {}
    for pid, j, la, lo in zip(p.index, jds, p.latitude.to_numpy(), p.longitude.to_numpy()):
        pos = natal_positions(float(j), float(la), float(lo))
        poss[pid] = pos
        rows.append(natal_G_row(pos))
    return pd.DataFrame(rows, index=p.index), poss


def natal_families(cols) -> dict[str, list[str]]:
    fam: dict[str, list[str]] = {}
    for c in cols:
        if c.startswith("g_pair_"):
            k = "G_pairs"
        elif c.startswith("g_Lagna") or c.startswith("g_MC"):
            k = "G_lagna_mc"
        elif c.startswith("g_"):
            k = "G_" + c.split("_")[1]
        elif c.startswith("t_raman_"):
            k = "T_raman_rules"
        elif c.startswith("t_par_"):
            k = "T_parashara_verdicts"
        elif c.startswith("t_kp_"):
            k = "T_kp"
        else:
            continue
        fam.setdefault(k, []).append(c)
    return fam


# ----------------------------------------------------------------------------- text rules (natal)

def raman_rules(derived: Path, ids: pd.Index) -> pd.DataFrame:
    r = pd.read_parquet(Path(derived) / "raman" / "rule_fires.parquet")
    r = r[r.person_id.isin(ids)]
    x = pd.crosstab(r.person_id, r.rule_id).clip(upper=1).reindex(ids, fill_value=0)
    share = x.mean()
    x = x.loc[:, (share >= 0.01) & (share <= 0.99)]
    x.columns = [f"t_raman_{c}" for c in x.columns]
    return x.astype(np.int8)


def parashara_verdicts(derived: Path, ids: pd.Index) -> pd.DataFrame:
    v = pd.read_parquet(Path(derived) / "parashara" / "verdicts.parquet")
    v = v[v.person_id.isin(ids)]
    v["k"] = "t_par_h" + v.house.astype(str) + "_" + v.verdict.astype(str)
    x = pd.crosstab(v.person_id, v.k).clip(upper=1).reindex(ids, fill_value=0)
    return x.astype(np.int8)


def kp_natal(p: pd.DataFrame, jd: np.ndarray | None = None):
    """KP indications fired and cusp sub-lord verdicts; also returns each chart's per-planet house sets."""
    from app.kp.chart import Birth, cast
    from app.kp.indications import indications
    from app.kp.judgment import MATTERS, _core
    from app.kp.significators import houses_signified, planet_significations
    rows, sig = [], {}
    jds = p.jd_ut.to_numpy() if jd is None else jd
    for pid, j, la, lo in zip(p.index, jds, p.latitude.to_numpy(), p.longitude.to_numpy()):
        y, mo, d, h = swe.revjul(float(j), swe.GREG_CAL)
        hh = int(h)
        mi = (h - hh) * 60
        b = Birth(y, mo, d, hh, int(mi), 0.0, float(la), float(lo), second=(mi - int(mi)) * 60)
        r = {}
        try:
            c = cast(b)
            for f in indications(c):
                key = getattr(f.indication, "key", None) or str(f.indication)
                r[f"t_kp_ind_{key}"] = 1
            for k, m in MATTERS.items():
                v = _core(c, m)[0]
                r[f"t_kp_{k}_{v}"] = 1
            s = planet_significations(c)
            sig[pid] = {pl: frozenset(houses_signified(c, pl, s)) for pl in c.planets}
            sig[pid]["_chart"] = c
        except Exception:                                   # noqa: BLE001 - polar / odd charts
            sig[pid] = None
        rows.append(r)
    x = pd.DataFrame(rows, index=p.index).fillna(0).astype(np.int8)
    return x, sig


# ----------------------------------------------------------------------------- Vimshottari (Lahiri)

def vimshottari_lords(moon_lon: float, birth_jd: float, jd: float) -> tuple[str, str, str]:
    """MD, AD, PD lords at `jd` from the natal Moon (Lahiri), proportional subdivision."""
    span = 360 / 27
    nak = int(moon_lon // span)
    frac = (moon_lon % span) / span
    i = nak % 9
    t = (jd - birth_jd) / YEAR + frac * DASA_YEARS[DASA_ORDER[i]]     # years since the cycle start
    t %= 120.0
    lords = []
    seq = [DASA_ORDER[(i + k) % 9] for k in range(9)]
    total = 120.0
    for _level in range(3):
        for l in seq:
            d = DASA_YEARS[l] * total / 120.0
            if t < d:
                lords.append(l)
                total = d
                j = DASA_ORDER.index(l)
                seq = [DASA_ORDER[(j + k) % 9] for k in range(9)]
                break
            t -= d
        else:                                                  # numerical edge
            lords.append(seq[-1])
    return tuple(lords)  # type: ignore[return-value]


# ----------------------------------------------------------------------------- timing

def transit_G_row(pos: dict, birth_jd: float, jd: float) -> dict:
    _setup()
    r = {}
    moon_s = int(pos["Moon"][0] // 30)
    lag_s = int(pos["Lagna"] // 30)
    tr = {}
    for b in BODIES:
        L = (swe.calc_ut(jd, _SWE[b], swe.FLG_SWIEPH)[0][0] - swe.get_ayanamsa_ut(jd)) % 360.0
        tr[b] = L
        s = int(L // 30)
        r[f"x_{b}_from_moon"] = (s - moon_s) % 12 + 1
        r[f"x_{b}_from_lagna"] = (s - lag_s) % 12 + 1
    natal = {k: pos[k][0] for k in ("Sun", "Moon", "Mars", "Venus", "Jupiter", "Saturn")}
    natal["Lagna"], natal["MC"] = pos["Lagna"], pos["MC"]
    for b in ("Jupiter", "Saturn", "Rahu"):
        for k, v in natal.items():
            a = math.radians(tr[b] - v)
            r[f"x_{b}_to_{k}_sin"] = math.sin(a)
            r[f"x_{b}_to_{k}_cos"] = math.cos(a)
    md, ad, pd_ = vimshottari_lords(pos["Moon"][0], birth_jd, jd)
    r["x_dasa_md"], r["x_dasa_ad"], r["x_dasa_pd"] = LORD_CODE[md], LORD_CODE[ad], LORD_CODE[pd_]
    return r


def timing_families(cols) -> dict[str, list[str]]:
    fam: dict[str, list[str]] = {}
    for c in cols:
        if c.startswith("x_dasa_"):
            k = "G_dasa_lords"
        elif c.startswith("x_"):
            k = "G_transit_" + c.split("_")[1]
        elif c.startswith("s_par_"):
            k = "T_parashara_activation"
        elif c.startswith("s_ram_"):
            k = "T_raman_activation"
        elif c.startswith("k_"):
            k = "T_kp_dasa_significators"
        else:
            continue
        fam.setdefault(k, []).append(c)
    return fam


def kp_dasa_row(sig: dict | None, jd: float) -> dict:
    from app.kp.dasa import periods_on
    r = {f"k_{lv}_h{h}": 0 for lv in ("md", "ad", "an") for h in range(1, 13)}
    if not sig:
        return r
    try:
        ps = periods_on(sig["_chart"], jd, depth=3)
    except Exception:                                       # noqa: BLE001
        return r
    for lv, per in zip(("md", "ad", "an"), ps):
        for h in sig.get(per.lords[-1], ()):
            r[f"k_{lv}_h{h}"] = 1
    return r


@dataclass
class StoreLookup:
    """Activation tier rows (t1..t12, t_mk) for the 'real' variant, by person and age."""
    data: dict

    @classmethod
    def load(cls, path: Path, ids) -> "StoreLookup":
        df = pd.read_parquet(path, filters=[("variant", "==", "real")])
        df = df[df.person_id.isin(set(ids))]
        cols = [*(f"t{h}" for h in range(1, 13)), "t_mk"]
        data = {}
        for pid, g in df.sort_values("start_age").groupby("person_id", sort=False):
            data[pid] = (g.start_age.to_numpy(), g.end_age.to_numpy(), g[cols].to_numpy())
        return cls(data)

    def row(self, pid: str, age: float, prefix: str) -> dict:
        names = [*(f"{prefix}h{h}" for h in range(1, 13)), f"{prefix}mk"]
        rec = self.data.get(pid)
        if rec is None:
            return dict.fromkeys(names, -1)
        s, e, t = rec
        i = int(np.searchsorted(s, age, side="right")) - 1
        if i < 0 or age >= e[i]:
            return dict.fromkeys(names, -1)
        return dict(zip(names, (int(v) for v in t[i])))
