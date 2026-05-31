"""Yoga name alias map for cross-engine matching.

Track A and Track B name the same yogas differently. Without aliasing,
the symmetric set-difference in ``compare_yoga_detection`` reports near-
zero intersections even for charts where both engines detect the same
classical yogas.

This module holds the curated alias map. Each alias group is a
canonical name + the set of variations that should be treated as
equivalent. Both engines' names are normalised (lowercased, namespace
stripped, " yoga"/" dosha" trailing words stripped) before lookup.

DOCTRINE: aliases are CONSERVATIVE — two yogas are aliased only when
they share both:
1. Classical name (Adhi / Lakshmi / Vipareeta Raja / etc.)
2. Detection rule (the geometric condition is equivalent across schools)

Yogas that share a name but have substantively different detection
rules (e.g. PVR's "raja yoga" vs Sanjay-Rath's "rajyoga formed by lord
of trine + lord of kendra") are kept SEPARATE so the comparator can
still surface that engine-divergence.
"""

from __future__ import annotations


# Canonical name -> set of equivalent variants (all lowercase, namespace-stripped).
# Both Track A and Track B names are normalised before lookup.
_ALIAS_GROUPS: tuple[tuple[str, frozenset[str]], ...] = (
    # Adhi (planets in 6/7/8 from Moon) — single canonical detection
    ("adhi", frozenset({"adhi", "adhi yoga"})),

    # Lakshmi (Venus in lagna kendra/trikona + 9L strong)
    ("lakshmi", frozenset({"lakshmi", "lakshmi yoga"})),

    # Gajakesari (Jupiter in kendra from Moon)
    ("gajakesari", frozenset({"gajakesari", "gajakesari yoga"})),

    # Vipareeta Raja (lord of 6/8/12 in another dusthana)
    ("vipareeta raja", frozenset({
        "vipareeta raja", "vipareeta_raja", "vipareeta raja yoga",
        "vipareeta_raja_yoga", "vipareeta raja positional",
        "vipareeta raja yoga positional",
    })),

    # Mangal Dosha (Mars in 1/4/7/8/12 from lagna or Venus)
    ("mangal", frozenset({"mangal", "mangal dosha"})),

    # Sarpa Dosha (Rahu/Ketu axis through 1H/7H or other configs)
    ("sarpa", frozenset({"sarpa", "sarpa dosha", "kala sarpa"})),

    # Sunapha (planet in 2nd from Moon, excluding Sun)
    ("sunapha", frozenset({"sunapha", "sunapha yoga"})),

    # Anapha (planet in 12th from Moon, excluding Sun)
    ("anapha", frozenset({"anapha", "anapha yoga"})),

    # Kemadruma (no planet in 2nd/12th from Moon, no kendra Jupiter)
    ("kemadruma", frozenset({"kemadruma", "kemadruma yoga"})),

    # Saraswati (Venus, Mercury, Jupiter in kendra/trikona/2nd)
    ("saraswati", frozenset({"saraswati", "saraswati yoga"})),

    # Budha-Aditya (Sun + Mercury within 14 degrees)
    ("budha-aditya", frozenset({
        "budha-aditya", "budha aditya", "budhaditya", "budha aditya yoga",
    })),

    # Chandra-Mangal (Moon + Mars conjunction or sign-mutual aspect)
    ("chandra-mangal", frozenset({
        "chandra-mangal", "chandra mangal", "chandra mangal yoga",
    })),

    # Pitra Dosha (Sun/Saturn/Rahu afflicting 9th house)
    ("pitra", frozenset({"pitra", "pitra dosha"})),

    # Matr Dosha (Moon afflicted by malefics or 4th house affliction)
    ("matr", frozenset({"matr", "matr dosha"})),

    # Daridra (lord of 11 in 12, or other "poverty" configs)
    ("daridra", frozenset({"daridra", "daridra yoga"})),

    # Amala (benefic in 10H from lagna or Moon — "spotless" reputation yoga)
    ("amala", frozenset({"amala", "amala yoga", "amala kirti"})),

    # Hamsa Pancha-mahapurusha (Jupiter in own/exalted in kendra)
    ("hamsa", frozenset({"hamsa", "hamsa yoga"})),

    # Malavya (Venus in own/exalted in kendra)
    ("malavya", frozenset({"malavya", "malavya yoga"})),

    # Ruchaka (Mars in own/exalted in kendra)
    ("ruchaka", frozenset({"ruchaka", "ruchaka yoga"})),

    # Bhadra (Mercury in own/exalted in kendra)
    ("bhadra", frozenset({"bhadra", "bhadra yoga"})),

    # Sasa (Saturn in own/exalted in kendra)
    ("sasa", frozenset({"sasa", "sasa yoga"})),

    # Neecha Bhanga Raja (debilitation cancellation -> raja yoga)
    ("neecha bhanga raja", frozenset({
        "neecha bhanga raja", "neech_bhanga", "neech bhanga",
        "neecha bhanga", "neech_bhanga_raja",
    })),

    # Parijata (lord of 9 in 9 strong, OR lagna lord exalted/own)
    ("parijata", frozenset({"parijata", "parijata yoga"})),

    # Akhanda Samrajya (lord of 9 + lord of 10 in kendra from each other)
    ("akhanda samrajya", frozenset({
        "akhanda samrajya", "akhanda_samrajya",
        "akhanda samrajya yoga",
    })),

    # Dharma-Karma-Adhipati (9L + 10L combine or aspect)
    ("dharma karma adhipati", frozenset({
        "dharma karma adhipati", "dharma_karma_adhipati", "dka",
        "dharma-karma-adhipati",
    })),

    # Raja (PVR's lord-of-trine + lord-of-kendra association) — kept
    # SEPARATE from "rajyoga formed" because the detection rules
    # differ across schools.
    ("raja", frozenset({"raja", "raja yoga"})),
)


# Reverse-index: variant -> canonical name. Built once at import time.
_VARIANT_TO_CANONICAL: dict[str, str] = {}
for canonical, variants in _ALIAS_GROUPS:
    for v in variants:
        _VARIANT_TO_CANONICAL[v] = canonical


def alias_canonical(normalised_name: str) -> str:
    """Map a normalised yoga name to its canonical form.

    If the name is not in any alias group, it is returned unchanged
    (so non-aliased yogas still participate in the symmetric diff).
    """
    return _VARIANT_TO_CANONICAL.get(normalised_name, normalised_name)


def all_canonical_names() -> tuple[str, ...]:
    """All canonical names recognised by the alias map."""
    return tuple(c for c, _ in _ALIAS_GROUPS)
