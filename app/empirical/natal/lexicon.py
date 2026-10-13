"""The Western tropical interpretation vocabulary.

Every trait phrase the natal decoder can emit lives in this module, under one
provenance banner. The shape is **base tables + generic composition + a small
bespoke core**: twelve sign profiles, ten planet roles and twelve house domains
compose into full 10 x 12 x 12 coverage through total accessor functions, while
hand-written bespoke entries override the composition only where the tradition
says more than role x sign (Sun/Moon/Mercury in each sign, and a handful of
classically emphasised aspect pairs).

Provenance: this is the mainstream Western tropical keyword vocabulary as
commonly taught — deliberately mainstream, deliberately uncited (there is no
single canonical Western source the way Raman is canonical for the Vedic
engine), and carrying no demonstrated predictive weight. The banner below
travels with every rendered statement; see ``docs/empirical/
TIME_BASIS_CONFOUND.md`` for the measurement that keeps it honest.

Usage:
    from app.empirical.natal.lexicon import planet_in_sign, SIGNS
    meanings = planet_in_sign("Mercury", "Gemini")   # {facet: (phrases, ...)}
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Mapping

__all__ = [
    "WESTERN_TRADITION",
    "TRADITION_BANNER",
    "FACETS",
    "SIGNS",
    "ELEMENTS",
    "MODALITIES",
    "SIGN_RULERS",
    "SignProfile",
    "SIGN_PROFILES",
    "PlanetRole",
    "PLANET_ROLES",
    "HouseDomain",
    "HOUSE_DOMAINS",
    "ELEMENT_TEMPERAMENT",
    "MODALITY_TEMPERAMENT",
    "ASPECT_TONES",
    "planet_in_sign",
    "planet_in_house",
    "aspect_meaning",
]

#: Provenance tag carried by every statement the decoder emits.
WESTERN_TRADITION: Final[str] = "WESTERN_TRADITION"

#: The banner rendered wherever this vocabulary surfaces. Mirrors the
#: ``MODERN_BANNER`` precedent in ``app/raman_saab/planet_biographies.py``:
#: non-doctrinal keyword content ships only under an explicit label.
TRADITION_BANNER: Final[str] = (
    "WESTERN_TRADITION — mainstream Western tropical keyword vocabulary "
    "(sign/planet/house/aspect symbolism as commonly taught). No citation to a "
    "measured result; this project's own tournament found natal-chart features "
    "have no predictive advantage over birthplace and birth date "
    "(docs/empirical/TIME_BASIS_CONFOUND.md)."
)

#: The seven decode facets, in the fixed order every surface uses.
FACETS: Final[tuple[str, ...]] = (
    "personality",
    "characteristics",
    "attitude",
    "aptitude",
    "intelligence",
    "work_style",
    "work_area",
)

SIGNS: Final[tuple[str, ...]] = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)

#: Elements repeat in zodiacal order fire-earth-air-water; modalities repeat
#: cardinal-fixed-mutable. Stored explicitly on each profile (and checked by
#: tests against the ``index % 4`` / ``index % 3`` arithmetic) so a typo in
#: one place cannot silently pass.
ELEMENTS: Final[tuple[str, ...]] = ("fire", "earth", "air", "water")
MODALITIES: Final[tuple[str, ...]] = ("cardinal", "fixed", "mutable")

#: Modern rulerships. Traditional co-rulers noted for the three outer signs:
#: Scorpio/Mars, Aquarius/Saturn, Pisces/Jupiter. The decoder uses the modern
#: set; the choice is data, disclosed here, not buried in code.
SIGN_RULERS: Final[dict[str, str]] = {
    "Aries": "Mars",
    "Taurus": "Venus",
    "Gemini": "Mercury",
    "Cancer": "Moon",
    "Leo": "Sun",
    "Virgo": "Mercury",
    "Libra": "Venus",
    "Scorpio": "Pluto",
    "Sagittarius": "Jupiter",
    "Capricorn": "Saturn",
    "Aquarius": "Uranus",
    "Pisces": "Neptune",
}


@dataclass(frozen=True, slots=True)
class SignProfile:
    """One zodiac sign's core vocabulary.

    Attributes:
      name: Sign name.
      element: fire | earth | air | water.
      modality: cardinal | fixed | mutable.
      keywords: Core adjectives, most characteristic first.
      attitude: Stance-toward-the-world phrases.
      aptitude: Skill-flavoured phrases.
      work: Vocational-flavoured phrases (fields the tradition assigns).
    """

    name: str
    element: str
    modality: str
    keywords: tuple[str, ...]
    attitude: tuple[str, ...]
    aptitude: tuple[str, ...]
    work: tuple[str, ...]


SIGN_PROFILES: Final[dict[str, SignProfile]] = {
    "Aries": SignProfile(
        "Aries", "fire", "cardinal",
        ("direct", "energetic", "pioneering", "impulsive", "competitive"),
        ("meets challenges head-on", "prefers action over deliberation"),
        ("quick initiation of new ventures", "leadership under pressure"),
        ("entrepreneurship", "athletics", "emergency services", "the military", "sales"),
    ),
    "Taurus": SignProfile(
        "Taurus", "earth", "fixed",
        ("steady", "patient", "practical", "sensual", "persistent"),
        ("changes course slowly and only for good reason", "values comfort and security"),
        ("sustained concentration", "handling money and material resources"),
        ("finance", "agriculture", "food", "construction", "music and craftsmanship"),
    ),
    "Gemini": SignProfile(
        "Gemini", "air", "mutable",
        ("curious", "versatile", "quick-witted", "talkative", "restless"),
        ("keeps several options open at once", "treats life as a stream of information"),
        ("verbal facility", "rapid learning across many topics"),
        ("writing", "journalism", "teaching", "commerce", "media and transport"),
    ),
    "Cancer": SignProfile(
        "Cancer", "water", "cardinal",
        ("sensitive", "protective", "tenacious", "intuitive", "home-loving"),
        ("tests for safety before advancing", "fiercely loyal to its own"),
        ("emotional attunement", "nurturing and provisioning"),
        ("hospitality", "caregiving", "real estate", "food", "family enterprises"),
    ),
    "Leo": SignProfile(
        "Leo", "fire", "fixed",
        ("warm", "proud", "dramatic", "generous", "self-assured"),
        ("leads from the front", "takes responsibility for the whole show"),
        ("performance and presentation", "inspiring loyalty in others"),
        ("entertainment", "management", "education", "luxury goods", "public life"),
    ),
    "Virgo": SignProfile(
        "Virgo", "earth", "mutable",
        ("precise", "analytical", "modest", "service-minded", "discriminating"),
        ("improves whatever is in front of it", "distrusts sloppiness"),
        ("detail work", "systematic analysis and quality control"),
        ("health care", "editing", "accountancy", "data work", "skilled trades"),
    ),
    "Libra": SignProfile(
        "Libra", "air", "cardinal",
        ("diplomatic", "fair-minded", "sociable", "aesthetic", "deliberate"),
        ("weighs both sides before committing", "seeks harmony in every room"),
        ("negotiation", "design sense and social judgment"),
        ("law", "diplomacy", "design", "counselling", "the arts and public relations"),
    ),
    "Scorpio": SignProfile(
        "Scorpio", "water", "fixed",
        ("intense", "strategic", "private", "resourceful", "unyielding"),
        ("commits totally or not at all", "watches carefully before acting"),
        ("research and investigation", "managing crises and shared resources"),
        ("investigation", "surgery", "psychology", "finance", "security and research"),
    ),
    "Sagittarius": SignProfile(
        "Sagittarius", "fire", "mutable",
        ("optimistic", "candid", "freedom-loving", "philosophical", "expansive"),
        ("aims at the far target", "says what it thinks"),
        ("grasping the big picture", "teaching and persuading"),
        ("higher education", "publishing", "travel", "law", "sport and religion"),
    ),
    "Capricorn": SignProfile(
        "Capricorn", "earth", "cardinal",
        ("ambitious", "disciplined", "pragmatic", "reserved", "enduring"),
        ("plays the long game", "takes duty seriously"),
        ("organisation and administration", "patient accumulation of mastery"),
        ("management", "government", "engineering", "business", "structural work"),
    ),
    "Aquarius": SignProfile(
        "Aquarius", "air", "fixed",
        ("independent", "inventive", "humanitarian", "detached", "unconventional"),
        ("questions the default settings", "sides with the future"),
        ("systems thinking", "innovation within groups and networks"),
        ("science", "technology", "social reform", "aviation", "collective enterprises"),
    ),
    "Pisces": SignProfile(
        "Pisces", "water", "mutable",
        ("imaginative", "compassionate", "adaptable", "impressionable", "visionary"),
        ("dissolves boundaries rather than defending them", "feels the room before reading it"),
        ("imagination and empathy", "artistic and spiritual sensibility"),
        ("the arts", "healing", "charity", "film", "marine and institutional work"),
    ),
}


@dataclass(frozen=True, slots=True)
class PlanetRole:
    """One planet's psychological function and how it composes.

    Attributes:
      name: Body name from ``DEFAULT_BODIES`` (nodes excluded — their
        symbolism is tradition-divergent, so they are computed and rendered
        but never trait-decoded).
      function: The faculty this planet stands for.
      facets: Which of :data:`FACETS` this planet's placements feed.
      in_sign_template: Composition template; ``{function}``, ``{sign}`` and
        ``{keywords}`` are substituted.
      in_house_template: Composition template; ``{function}`` and ``{domain}``
        are substituted.
    """

    name: str
    function: str
    facets: tuple[str, ...]
    in_sign_template: str = "{function} runs in the {sign} register: {keywords}"
    in_house_template: str = "{function} is invested chiefly in {domain}"


PLANET_ROLES: Final[dict[str, PlanetRole]] = {
    "Sun": PlanetRole("Sun", "the core identity and vitality", ("personality",)),
    "Moon": PlanetRole("Moon", "the instinctive feelings and habits", ("personality", "characteristics")),
    "Mercury": PlanetRole("Mercury", "the reasoning, language and learning", ("intelligence", "aptitude")),
    "Venus": PlanetRole("Venus", "the affections, taste and values", ("characteristics", "aptitude")),
    "Mars": PlanetRole("Mars", "the drive, assertion and stamina", ("attitude", "work_style")),
    "Jupiter": PlanetRole("Jupiter", "the sense of growth, confidence and opportunity", ("personality", "work_area")),
    "Saturn": PlanetRole("Saturn", "the discipline, limits and endurance", ("attitude", "work_style")),
    "Uranus": PlanetRole("Uranus", "the streak of independence and innovation", ("characteristics",)),
    "Neptune": PlanetRole("Neptune", "the imagination and ideals", ("characteristics",)),
    "Pluto": PlanetRole("Pluto", "the capacity for depth and transformation", ("characteristics",)),
}


@dataclass(frozen=True, slots=True)
class HouseDomain:
    """One house's life-domain and which facets a tenant planet feeds.

    Attributes:
      number: House 1..12.
      domain: The life area, as a phrase.
      facets: Which of :data:`FACETS` an occupant of this house speaks to.
      work_keywords: Vocational keywords — non-empty only for the working
        houses 2, 6 and 10.
    """

    number: int
    domain: str
    facets: tuple[str, ...]
    work_keywords: tuple[str, ...] = ()


HOUSE_DOMAINS: Final[dict[int, HouseDomain]] = {
    1: HouseDomain(1, "self-presentation, the body and first impressions", ("personality",)),
    2: HouseDomain(2, "income, possessions and material security", ("work_area",),
                   ("earning through one's own resources", "finance and valuation")),
    3: HouseDomain(3, "communication, learning and the immediate environment", ("intelligence", "aptitude")),
    4: HouseDomain(4, "home, roots and private life", ("characteristics",)),
    5: HouseDomain(5, "creativity, play and self-expression", ("personality", "aptitude")),
    6: HouseDomain(6, "daily work, routine, service and health", ("work_style",),
                   ("service and craft", "daily routines and health work")),
    7: HouseDomain(7, "partnership and one-to-one dealings", ("characteristics",)),
    8: HouseDomain(8, "shared resources, crisis and regeneration", ("characteristics",)),
    9: HouseDomain(9, "higher learning, belief and long journeys", ("intelligence", "aptitude")),
    10: HouseDomain(10, "career, reputation and public standing", ("work_area",),
                    ("public position and management", "the visible career")),
    11: HouseDomain(11, "friends, groups and long-range hopes", ("characteristics",)),
    12: HouseDomain(12, "solitude, the inner life and institutions", ("characteristics",)),
}

#: One temperament line per element, used for the chart-level balance reading.
ELEMENT_TEMPERAMENT: Final[dict[str, str]] = {
    "fire": "runs hot — enthusiasm and initiative arrive before deliberation",
    "earth": "runs practical — what is real is what can be used",
    "air": "runs mental — life is approached through ideas and exchange",
    "water": "runs deep — feeling is the first organ of knowledge",
}

#: One temperament line per modality.
MODALITY_TEMPERAMENT: Final[dict[str, str]] = {
    "cardinal": "initiates — starts things and pushes them into motion",
    "fixed": "sustains — holds course and finishes what it starts",
    "mutable": "adapts — bends with circumstances and adjusts on the move",
}


@dataclass(frozen=True, slots=True)
class AspectTone:
    """How one Ptolemaic aspect colours the two functions it joins."""

    name: str
    tone: str
    template: str


ASPECT_TONES: Final[dict[str, AspectTone]] = {
    "conjunction": AspectTone("conjunction", "fusing", "{fa} and {fb} fuse into a single drive"),
    "sextile": AspectTone("sextile", "stimulating", "{fa} and {fb} stimulate each other readily when called on"),
    "square": AspectTone("square", "frictional", "{fa} and {fb} grind against each other — friction that can become drive"),
    "trine": AspectTone("trine", "easing", "{fa} and {fb} flow together with little resistance"),
    "opposition": AspectTone("opposition", "polarizing", "{fa} and {fb} pull from opposite ends, demanding balance"),
}


#: Bespoke planet-in-sign entries, ONLY where the tradition says more than
#: role x sign: the Sun (identity), the Moon (temperament) and Mercury (mind)
#: each read distinctly in every sign. Everything else composes generically.
#: Shape: (planet, sign) -> {facet: (phrases, ...)}. Merged ON TOP of the
#: composed base, never replacing it.
PLANET_SIGN_BESPOKE: Final[dict[tuple[str, str], dict[str, tuple[str, ...]]]] = {
    ("Sun", "Aries"): {"personality": ("a self-starter — confidence comes from acting first",)},
    ("Sun", "Taurus"): {"personality": ("a builder — identity rests on what is made to last",)},
    ("Sun", "Gemini"): {"personality": ("a communicator — identity lives in exchange and variety",)},
    ("Sun", "Cancer"): {"personality": ("a protector — identity is rooted in belonging and care",)},
    ("Sun", "Leo"): {"personality": ("a natural centre of the room — identity seeks expression and recognition",)},
    ("Sun", "Virgo"): {"personality": ("a perfecter — identity is proven through useful, exact work",)},
    ("Sun", "Libra"): {"personality": ("a harmoniser — identity forms in relation to others",)},
    ("Sun", "Scorpio"): {"personality": ("an intense will — identity is forged through depth and testing",)},
    ("Sun", "Sagittarius"): {"personality": ("an explorer — identity needs a horizon and a meaning",)},
    ("Sun", "Capricorn"): {"personality": ("an achiever — identity is built by climbing, step over step",)},
    ("Sun", "Aquarius"): {"personality": ("an original — identity stands slightly apart from the crowd",)},
    ("Sun", "Pisces"): {"personality": ("a dreamer — identity is porous, imaginative and compassionate",)},
    ("Moon", "Aries"): {"characteristics": ("feelings flare fast and clear quickly",)},
    ("Moon", "Taurus"): {"characteristics": ("feelings settle slowly and hold steady — comfort matters",)},
    ("Moon", "Gemini"): {"characteristics": ("feelings are talked through — mood follows the conversation",)},
    ("Moon", "Cancer"): {"characteristics": ("feelings run tidal and deep — memory and home anchor the mood",)},
    ("Moon", "Leo"): {"characteristics": ("feelings are warm and theatrical — appreciation is emotional food",)},
    ("Moon", "Virgo"): {"characteristics": ("feelings are managed by usefulness — worry is the reflex under stress",)},
    ("Moon", "Libra"): {"characteristics": ("feelings seek fairness and company — discord is felt physically",)},
    ("Moon", "Scorpio"): {"characteristics": ("feelings run silent and absolute — trust is given rarely and fully",)},
    ("Moon", "Sagittarius"): {"characteristics": ("feelings need open air — optimism is the emotional default",)},
    ("Moon", "Capricorn"): {"characteristics": ("feelings are rationed and dutiful — composure is a point of honour",)},
    ("Moon", "Aquarius"): {"characteristics": ("feelings are observed from one step back — freedom is an emotional need",)},
    ("Moon", "Pisces"): {"characteristics": ("feelings absorb the surroundings — boundaries between self and other blur",)},
    ("Mercury", "Aries"): {"intelligence": ("a fast, decisive mind — thinks by acting, argues to win",)},
    ("Mercury", "Taurus"): {"intelligence": ("a deliberate, retentive mind — slow to conclude, hard to dislodge",)},
    ("Mercury", "Gemini"): {"intelligence": ("an agile, associative mind — collects, connects and relays",)},
    ("Mercury", "Cancer"): {"intelligence": ("a retentive, impression-led mind — memory and mood shape judgment",)},
    ("Mercury", "Leo"): {"intelligence": ("a confident, dramatising mind — thinks in narratives and speaks to persuade",)},
    ("Mercury", "Virgo"): {"intelligence": ("an exact, analytical mind — sorts, measures and corrects",)},
    ("Mercury", "Libra"): {"intelligence": ("a comparative, judicial mind — weighs alternatives before deciding",)},
    ("Mercury", "Scorpio"): {"intelligence": ("a probing, strategic mind — asks what is being concealed",)},
    ("Mercury", "Sagittarius"): {"intelligence": ("a synthesising mind — reaches for the principle behind the case",)},
    ("Mercury", "Capricorn"): {"intelligence": ("a structured, methodical mind — thinks in plans and consequences",)},
    ("Mercury", "Aquarius"): {"intelligence": ("an inventive, systematic mind — reasons from first principles",)},
    ("Mercury", "Pisces"): {"intelligence": ("an intuitive, imagistic mind — grasps wholes before parts",)},
}


#: Bespoke aspect notes among the classically emphasised pairs. Keys carry the
#: two bodies in ``DEFAULT_BODIES`` order plus the aspect name.
ASPECT_BESPOKE: Final[dict[tuple[str, str, str], dict[str, tuple[str, ...]]]] = {
    ("Sun", "Moon", "conjunction"): {"personality": ("will and feeling point the same way — a unified, self-consistent nature",)},
    ("Sun", "Moon", "square"): {"personality": ("will and feeling pull at cross purposes — inner tension that fuels growth",)},
    ("Sun", "Moon", "trine"): {"personality": ("will and feeling cooperate easily — an even, self-accepting temperament",)},
    ("Sun", "Moon", "opposition"): {"personality": ("will and feeling face off — life oscillates between self-assertion and accommodation",)},
    ("Sun", "Mars", "conjunction"): {"attitude": ("courage sits close to the surface — energy and identity act as one",)},
    ("Sun", "Mars", "square"): {"attitude": ("a combative streak — impatience with obstacles, quick to contend",)},
    ("Sun", "Mars", "trine"): {"attitude": ("confident, well-directed energy — assertion without strain",)},
    ("Sun", "Saturn", "conjunction"): {"attitude": ("a serious cast — self-worth is earned through duty and proof",)},
    ("Sun", "Saturn", "square"): {"attitude": ("authority is wrestled with — early doubt hardens into discipline",)},
    ("Sun", "Saturn", "trine"): {"attitude": ("patient self-command — ambition with a long, steady fuse",)},
    ("Moon", "Mercury", "conjunction"): {"intelligence": ("feeling and thought speak the same language — a fluent, retentive mind",)},
    ("Moon", "Mercury", "square"): {"intelligence": ("head and heart argue — judgment sharpens once the mood is named",)},
    ("Moon", "Mercury", "trine"): {"intelligence": ("easy access to one's own inner life — a natural storyteller's memory",)},
    ("Moon", "Mars", "square"): {"characteristics": ("a quick temper that passes quickly — feelings convert straight into action",)},
    ("Moon", "Saturn", "conjunction"): {"characteristics": ("emotional gravity — feelings are held privately and carried responsibly",)},
    ("Moon", "Saturn", "square"): {"characteristics": ("a guarded heart — warmth is real but rationed until safety is proven",)},
    ("Mercury", "Mars", "conjunction"): {"intelligence": ("a debater's mind — thought moves at attack speed",)},
    ("Mercury", "Saturn", "conjunction"): {"intelligence": ("a rigorous mind — few words, weighed twice",)},
    ("Mercury", "Saturn", "trine"): {"intelligence": ("methodical concentration — learning that compounds",)},
    ("Mars", "Saturn", "conjunction"): {"work_style": ("controlled force — effort is disciplined, sustained and deliberate",)},
    ("Mars", "Saturn", "square"): {"work_style": ("stop-go effort — drive fights restraint until pacing is learned",)},
}

#: Canonical body order for aspect keys (DEFAULT_BODIES order, nodes excluded).
_BODY_ORDER: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mercury", "Venus", "Mars",
    "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto",
)


def _merge(base: dict[str, tuple[str, ...]], extra: Mapping[str, tuple[str, ...]]) -> dict[str, tuple[str, ...]]:
    out = dict(base)
    for facet, phrases in extra.items():
        out[facet] = out.get(facet, ()) + tuple(phrases)
    return out


def planet_in_sign(planet: str, sign: str) -> dict[str, tuple[str, ...]]:
    """Facet phrases for a planet in a sign. Total over 10 planets x 12 signs.

    The composed base (role template + the sign's facet-relevant phrase lists)
    is always present; bespoke entries are merged on top, never replacing it —
    so the result is never empty and coverage is provable by iteration.

    Raises:
      KeyError: unknown planet (nodes are deliberately absent) or sign.
    """
    role = PLANET_ROLES[planet]
    profile = SIGN_PROFILES[sign]
    sentence = role.in_sign_template.format(
        function=role.function, sign=sign, keywords=", ".join(profile.keywords[:3]),
    )
    base: dict[str, tuple[str, ...]] = {facet: (sentence,) for facet in role.facets}
    if "attitude" in role.facets:
        base["attitude"] = base["attitude"] + profile.attitude
    if "aptitude" in role.facets:
        base["aptitude"] = base["aptitude"] + profile.aptitude
    if "work_area" in role.facets:
        base["work_area"] = base["work_area"] + tuple(f"an affinity for {w}" for w in profile.work[:3])
    return _merge(base, PLANET_SIGN_BESPOKE.get((planet, sign), {}))


def planet_in_house(planet: str, house: int) -> dict[str, tuple[str, ...]]:
    """Facet phrases for a planet occupying a house. Total over 10 x 12.

    The house decides which facets the tenancy speaks to (a planet in the 10th
    is a career statement whatever the planet); the planet supplies the
    function being invested there.

    Raises:
      KeyError: unknown planet or house number.
    """
    role = PLANET_ROLES[planet]
    domain = HOUSE_DOMAINS[house]
    sentence = role.in_house_template.format(function=role.function, domain=domain.domain)
    out: dict[str, tuple[str, ...]] = {facet: (sentence,) for facet in domain.facets}
    if domain.work_keywords:
        out["work_area"] = out.get("work_area", ()) + domain.work_keywords
    return out


def aspect_meaning(body_a: str, body_b: str, aspect: str) -> dict[str, tuple[str, ...]]:
    """Facet phrases for a Ptolemaic aspect between two trait planets.

    Bodies may be passed in either order; the bespoke table is keyed in
    ``DEFAULT_BODIES`` order. Composed fallback lands in the first shared facet
    of the two roles, or ``characteristics`` when they share none.

    Raises:
      KeyError: unknown body (nodes deliberately absent) or aspect name.
    """
    a, b = sorted((body_a, body_b), key=_BODY_ORDER.index)
    bespoke = ASPECT_BESPOKE.get((a, b, aspect))
    if bespoke is not None:
        return {facet: tuple(phrases) for facet, phrases in bespoke.items()}
    tone = ASPECT_TONES[aspect]
    fa, fb = PLANET_ROLES[a].function, PLANET_ROLES[b].function
    sentence = tone.template.format(fa=fa, fb=fb)
    shared = tuple(f for f in PLANET_ROLES[a].facets if f in PLANET_ROLES[b].facets)
    facet = shared[0] if shared else "characteristics"
    return {facet: (sentence,)}
