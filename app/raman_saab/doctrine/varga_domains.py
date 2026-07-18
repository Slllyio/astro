"""The Shodasavarga domain table — which life-matter each divisional chart studies.

CITATION POLICY (the doctrine-strategy resolution, recorded here per the Prime
Directive's no-silent-approximation rule):

1. The six SHADVARGA members Raman teaches in full (D1 Rasi, D2 Hora, D3 Drekkana,
   D9 Navamsa, D12 Dwadasamsa, D30 Thrimsamsa) — plus the Saptamsa he "casually"
   defines — cite their own HPA-11 definition lines.
2. The remaining divisions cite RAMAN'S OWN POINTER at HPA-11:195-201: "In fact
   according to Parasara there are sixteen divisions (shodasavargas) to be considered.
   Each division is made use of studying certain aspects of the horoscope — e.g.,
   Dwadasamsa for parents, Saptamsa for children, etc." Raman names the scheme, gives
   two domain examples explicitly, and defers the rest to Parashara.
3. Domain strings for the divisions Raman does not detail follow the classical
   Parashari scheme, referenced ONLY in ``notes`` (BPHS ch.6 and Phaladeepika ch.3 are
   on disk but NON-citable under the strictly-Raman registry). DEFERRED v2 POLICY
   ITEM: admit BPHS/Phaladeepika under a `corroboration`-tier registry status and
   re-ingest the missing chapters (BPHS per-varga domain slokas, Vimsopaka) before any
   varga RULES are authored beyond the general-principles judge.

Usage:
    from app.raman_saab.doctrine.varga_domains import DOMAINS, domain_for
    d10 = domain_for(10)      # VargaDomain(name="Dasamsa", domain="profession...", ...)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from app.raman_saab.chart.varga import SUPPORTED_VARGAS
from app.raman_saab.doctrine.sources import Citation


@dataclass(frozen=True)
class VargaDomain:
    """One division's identity: what matter it studies, through which karakas."""
    n: int
    name: str                            # Raman's spelling (HPA-11)
    domain: str
    related_houses: tuple[int, ...]      # D1 house(s) whose matter this varga refines
    karakas: tuple[str, ...]             # domain karakas (subset of the seven grahas)
    source: Citation
    notes: str = ""


DOMAINS: Final[tuple[VargaDomain, ...]] = (
    VargaDomain(1, "Rasi", "the body and the whole horoscope", (1,), ("Sun",),
                Citation("HPA-11", 39),
                notes="'The arc of 30 degrees forming a zodiacal sign is called rasi.'"),
    VargaDomain(2, "Hora", "wealth", (2,), ("Jupiter",),
                Citation("HPA-11", 45),
                notes="Two-sign division (Sun/Moon horas) - no 12-house frame. Classical "
                      "domain (wealth) per the Parashari scheme; BPHS ch.6 concurs "
                      "(on disk, non-citable)."),
    VargaDomain(3, "Drekkana", "brothers and sisters, courage", (3,), ("Mars",),
                Citation("HPA-11", 61),
                notes="HPA-36 gives the full 36-drekkana iconography; the 22nd drekkana "
                      "rules the manner of death (HTJAH-I:10159-10194)."),
    VargaDomain(4, "Chaturthamsa", "houses, property and fortune", (4,), ("Mars",),
                Citation("HPA-11", 195),
                notes="Raman's pointer to Parashara's scheme; classical domain per BPHS "
                      "ch.6 / Phaladeepika ch.3 (non-citable commentary)."),
    VargaDomain(7, "Sapthamsa", "children and progeny", (5,), ("Jupiter",),
                Citation("HPA-11", 195),
                notes="EXPLICIT in Raman's pointer: 'Saptamsa for children' "
                      "(HPA-11:198-199); definition at HPA-11:187-193."),
    VargaDomain(9, "Navamsa", "wife and husband, marriage; the general strength check",
                (7,), ("Venus",),
                Citation("HPA-11", 77),
                notes="'The most important sub-division' (HPA-11:77). Raman's working "
                      "varga throughout HTJAH (wife HTJAH-II:402-413; children via the "
                      "navamsa lagna HTJAH-II:774-776; profession via the navamsa of the "
                      "10th lord HTJAH-II:9729-9811). The ONLY division that modulates "
                      "D1 verdicts in this engine."),
    VargaDomain(10, "Dasamsa", "profession, honours and public standing", (10,),
                ("Saturn", "Mercury", "Jupiter", "Sun"),
                Citation("HPA-11", 195),
                notes="Raman's own profession method is navamsa-of-the-10th-lord + "
                      "shadvarga strength (HTJAH-II:9729-9811), NOT a dasamsa chart; "
                      "the dasamsa domain is the classical scheme via his pointer. "
                      "Karakas = the H10 multi-karaka set (karakas.py)."),
    VargaDomain(12, "Dwadasamsa", "father and mother", (4, 9), ("Moon", "Sun"),
                Citation("HPA-11", 147),
                notes="EXPLICIT in Raman's pointer: 'Dwadasamsa for parents' "
                      "(HPA-11:198-199); definition at HPA-11:147-163; used as an "
                      "ear/throat aggravator at HTJAH-I:3468."),
    VargaDomain(16, "Shodasamsa", "vehicles, conveyances and comforts", (4,), ("Venus",),
                Citation("HPA-11", 195),
                notes="Classical domain via Raman's pointer; 'Vahana-Karaka is Venus and "
                      "Vahana-Sthana is fourth' (HTJAH-I:4934, the direct vehicles line; "
                      "shashtiamsa/thrimsamsa combinations at :4951-4952)."),
    VargaDomain(20, "Vimsamsa", "worship, religious practice and spiritual progress",
                (9,), ("Jupiter",),
                Citation("HPA-11", 195),
                notes="Classical domain via Raman's pointer (BPHS ch.6 upasana)."),
    VargaDomain(24, "Siddhamsa", "learning and education", (4,), ("Jupiter", "Mercury"),
                Citation("HPA-11", 195),
                notes="Classical domain via Raman's pointer; education is a 4th-house "
                      "matter in Raman with Jupiter 'the Vidyakaraka or lord of "
                      "education' (AFB-6:23-25, gate-corrected Jupiter-first) and "
                      "Mercury jointly (AFB-6:27-28)."),
    VargaDomain(27, "Bhamsa", "general strength and weakness", (), (),
                Citation("HPA-11", 195),
                notes="Classical domain via Raman's pointer (nakshatramsa)."),
    VargaDomain(30, "Thrimsamsa", "evils, misfortune and disease", (6,),
                ("Mars", "Saturn"),
                Citation("HPA-11", 165),
                notes="Definition at HPA-11:165-185; Raman uses it as an aggravator "
                      "(HTJAH-I:4952 own-thrimsamsa Vahana-karaka)."),
    VargaDomain(40, "Khavedamsa", "auspicious and inauspicious general effects", (), (),
                Citation("HPA-11", 195),
                notes="Classical domain via Raman's pointer."),
    VargaDomain(45, "Akshavedamsa", "general character and conduct", (), (),
                Citation("HPA-11", 195),
                notes="Classical domain via Raman's pointer."),
    VargaDomain(60, "Shashtiamsa", "all matters; the accumulated karma", (), (),
                Citation("HPA-11", 195),
                notes="Classical domain via Raman's pointer; HTJAH-I:4951 reads "
                      "Gopura/Mridwa/Simhasana shashtiamsas for vehicles."),
)

_BY_N: Final[dict[int, VargaDomain]] = {d.n: d for d in DOMAINS}
assert set(_BY_N) == set(SUPPORTED_VARGAS), "domain table out of sync with SUPPORTED_VARGAS"


def domain_for(n: int) -> VargaDomain:
    """The domain row for division ``n``; ValueError for an unsupported division."""
    try:
        return _BY_N[n]
    except KeyError:
        raise ValueError(f"no varga domain for D{n}; supported: {sorted(_BY_N)}") from None
