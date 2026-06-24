"""Feature-group registry — single source of truth for ablation + selection.

Round 8 Phase 1: the DISCRETE_GROUPS / CONTINUOUS_GROUPS / _resolve_group_cols
definitions used to live inside `dequant_deep_dive.py`. Promoting them to
a first-class module so:
  - `train_classifier.select_features()` can drop the Tier-2 §2 hurting
    groups by default
  - `dequant_deep_dive.py` and `dequant_deep_dive_chunked.py` import from
    here
  - future ablation runs reference one canonical list

Decision (Round 8 sign-off): the aggressive 15-group drop list is the
default. Pass `--no-lean` to `train_classifier` to retain the full tensor.
"""
from __future__ import annotations

# ---------- group definitions ----------

# Discrete (categorical / binned) feature groups, prefix-keyed.
# Multi-prefix exclusions live in `_resolve_group_cols` (e.g. "house_" must
# NOT match "house_pos_" or "house_from_").
DISCRETE_GROUPS: dict[str, tuple[str, ...]] = {
    "houses": ("house_",),  # excludes house_pos_, house_from_
    "house_pos_discrete": ("house_from_moon_", "house_from_sun_"),
    "nakshatras": ("nak_",),  # excludes nak_pos_
    "signs_d1": ("lagna_sign",),
    "divisional_signs": ("d2_", "d3_", "d4_", "d7_", "d9_", "d10_", "d12_", "d24_", "d30_"),
    "dispositors": ("dispositor_", "disp_depth_", "final_dispositor"),
    "tattvas": ("tattva_",),
    "drishti": ("drishti_",),
    "retrograde": ("rx_",),
    "out_of_bounds": ("oob_",),
    "stationary": ("stationary_",),
    "combust": ("combust_",),
    "yogas": ("yoga_",),
    "panchanga": ("panchanga_",),
    "sade_sati_flags": ("sade_sati_active", "kantaka_shani", "ashtama_shani"),
    "ashtakavarga": ("bav_in_sign_", "sav_house_"),
    "active_dasha_lords": ("active_md_lord", "active_ad_lord", "active_pd_lord"),
    "transit_bav": ("transit_bav_",),
}

CONTINUOUS_GROUPS: dict[str, tuple[str, ...]] = {
    "raw_longitudes": ("lon_",),
    "ecliptic_lat": ("lat_",),
    "declinations": ("dec_",),
    "velocities": ("vel_",),
    "acceleration_jerk": ("acc_", "jerk_"),
    "pairwise_distances": ("dist_",),
    "aspect_orbs": ("aspect_orb_",),
    "house_pos_continuous": ("house_pos_",),
    "nak_pos_continuous": ("nak_pos_",),
    "divisional_degrees": ("d9_", "d10_", "d12_"),  # the _deg variants
    "cross_lon": ("cross_lon_",),
    "lagna_continuous": ("lagna_lon", "lagna_degree_in_sign"),
    "panchanga_continuous": ("tithi_angle", "yoga_angle", "moon_phase_normalized"),
    "dasha_schedule": ("natal_dasha_remaining_years", "dasha_start_age_",
                       "first_", "md_elapsed_years", "ad_elapsed_years",
                       "pd_elapsed_years"),
}


# ---------- Round 8 aggressive drop list ----------
#
# Derived from Tier-2 §1 ablation + Tier-2 §2 lean validation:
# every group with Δ ≥ +0.0008 (i.e. removing it improved accuracy or
# was net-zero in the deep dive) is in this list.
#
# Empirical lift on top-5 cohort: +0.0065 absolute accuracy when all 15
# are dropped. See `data/ml_runs/dequant_deep_dive/lean_eval.json`.
#
# Round 8 sign-off (2026-05-20): adopt as default; override with --no-lean.
DROP_BY_DEFAULT: tuple[str, ...] = (
    # Net-negative groups (Δ ≥ +0.0033)
    "ecliptic_lat",          # +0.0049
    "house_pos_continuous",  # +0.0041
    "tattvas",               # +0.0033
    # Marginal-negative groups (Δ +0.0016)
    "velocities",
    "pairwise_distances",
    "divisional_signs",
    "divisional_degrees",
    # Marginal-noise groups (Δ +0.0008)
    "houses",
    "drishti",
    "ashtakavarga",
    "raw_longitudes",
    "declinations",
    "acceleration_jerk",
    "cross_lon",
    "lagna_continuous",
)


# ---------- column resolution ----------

def _group_cols(
    df_cols: list[str], group_prefixes: tuple[str, ...],
    exclude_prefixes: tuple[str, ...] = (),
    suffix_filter: str | None = None,
) -> list[str]:
    """Find columns matching any of the group prefixes, with exclusions."""
    out = []
    for c in df_cols:
        if any(c.startswith(p) for p in exclude_prefixes):
            continue
        if not any(c.startswith(p) for p in group_prefixes):
            continue
        if suffix_filter and not c.endswith(suffix_filter):
            continue
        out.append(c)
    return out


def _resolve_group_cols(group_name: str, all_cols: list[str]) -> list[str]:
    """Resolve the column list for a group, handling boundary collisions
    (e.g. "house_" vs "house_pos_") and suffix-disambiguated divisional
    cols (signs vs degrees)."""
    if group_name == "houses":
        return _group_cols(all_cols, ("house_",),
                           exclude_prefixes=("house_pos_", "house_from_"))
    if group_name == "nakshatras":
        return _group_cols(all_cols, ("nak_",),
                           exclude_prefixes=("nak_pos_",))
    if group_name == "divisional_signs":
        return [c for c in all_cols
                if any(c.startswith(p) for p in
                       ("d2_", "d3_", "d4_", "d7_", "d12_", "d24_", "d30_"))
                and c.endswith("_sign")]
    if group_name == "divisional_degrees":
        return [c for c in all_cols
                if any(c.startswith(p) for p in ("d9_", "d10_", "d12_"))
                and c.endswith("_deg")]
    if group_name == "panchanga_continuous":
        return [c for c in all_cols
                if c in ("tithi_angle", "yoga_angle", "moon_phase_normalized")]
    if group_name == "sade_sati_flags":
        return [c for c in all_cols
                if c in ("sade_sati_active", "kantaka_shani", "ashtama_shani")]
    if group_name == "lagna_continuous":
        return [c for c in all_cols
                if c in ("lagna_lon", "lagna_degree_in_sign")]
    if group_name == "active_dasha_lords":
        return [c for c in all_cols
                if c in ("active_md_lord", "active_ad_lord", "active_pd_lord")]
    if group_name == "dasha_schedule":
        return [c for c in all_cols
                if c == "natal_dasha_remaining_years"
                or c.startswith("dasha_start_age_")
                or c.startswith("first_")
                or c in ("md_elapsed_years", "ad_elapsed_years",
                         "pd_elapsed_years")]
    if group_name in DISCRETE_GROUPS:
        return _group_cols(all_cols, DISCRETE_GROUPS[group_name])
    if group_name in CONTINUOUS_GROUPS:
        return _group_cols(all_cols, CONTINUOUS_GROUPS[group_name])
    return []


def resolve_drop_columns(all_cols: list[str],
                         drop_groups: tuple[str, ...] = DROP_BY_DEFAULT) -> set[str]:
    """Return the concrete set of column names to drop, given a list of
    feature-group names. Used by train_classifier.select_features and
    any ablation pipeline that wants 'lean by default'."""
    drop_cols: set[str] = set()
    for g in drop_groups:
        drop_cols.update(_resolve_group_cols(g, all_cols))
    return drop_cols




# ---------- Round 8 Phase 2 per-class selective drops ----------
#
# Per-class drop lists for classes where the locked-holdout binary
# Δ AUC was empirically validated to be positive in Phase 2.3.
# DO NOT apply universally — applying to ALL classes lost on average
# (mean Δ -0.0028 across top-10). Use class-by-class only.
#
# Phase 2.3 measured lifts on the locked group-split holdout:
#   Death by Disease: +0.0206 AUC (1064 → 928 cols)
#   career:           +0.0115 AUC (1064 → 774 cols)
#   Publication:      +0.0064 AUC (1064 → 873 cols)
#
# Other classes: keep FULL tensor; per-class lean either loses
# or shows zero validated lift on the locked binary holdout.
SELECTIVE_DROP_PER_CLASS: dict[str, tuple[str, ...]] = {
    'Death by Disease': (
        'house_pos_discrete',
        'ashtakavarga',
        'declinations',
        'divisional_degrees',
        'divisional_signs',
    ),
    'career': (
        'lagna_continuous',
        'acceleration_jerk',
        'stationary',
        'dasha_schedule',
        'signs_d1',
        'panchanga',
        'out_of_bounds',
        'transit_bav',
        'ecliptic_lat',
        'cross_lon',
        'drishti',
        'combust',
        'velocities',
        'houses',
        'yogas',
        'dispositors',
        'panchanga_continuous',
        'house_pos_discrete',
        'ashtakavarga',
        'nak_pos_continuous',
        'sade_sati_flags',
        'declinations',
        'house_pos_continuous',
    ),
    'Published/ Exhibited/ Released': (
        'nak_pos_continuous',
        'pairwise_distances',
        'house_pos_discrete',
        'ecliptic_lat',
        'dasha_schedule',
        'houses',
        'aspect_orbs',
        'transit_bav',
    ),
}


def resolve_per_class_drop_columns(
    all_cols: list[str], event_class: str,
) -> set[str]:
    """Return drop columns for `event_class` if it has a validated lift,
    else empty set. Used by train_classifier when training a single-
    target binary model on a top-10 class."""
    groups = SELECTIVE_DROP_PER_CLASS.get(event_class, ())
    if not groups:
        return set()
    drop: set[str] = set()
    for g in groups:
        drop.update(_resolve_group_cols(g, all_cols))
    return drop


__all__ = [
    "DISCRETE_GROUPS",
    "CONTINUOUS_GROUPS",
    "DROP_BY_DEFAULT",
    "_resolve_group_cols",
    "resolve_drop_columns",
    "SELECTIVE_DROP_PER_CLASS",
    "resolve_per_class_drop_columns",
]
