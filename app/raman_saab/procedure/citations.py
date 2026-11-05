"""Verbatim HTJAH citations used by the procedure reader.

Every step the reader records carries one of these keys. Each entry is ``(first line, last
line, snippet)``: the line range in
``data/knowledge_library/sources/how_to_judge_a_horoscope_raman/chapter_001_full-text-unsplit.md``
(the unsplit OCR of both volumes; the line numbers of
``docs/raman_saab/RAMAN_READING_PROCEDURE_2026-10-25.md``), and a short verbatim snippet that
must occur inside that range. ``tests/raman_saab/test_procedure_reader.py`` checks every snippet
against the corpus, so a wrong line number fails a test instead of shipping (the corpus is
git-ignored; the check skips where it is absent).

Snippets keep the OCR spelling ("benefice", "hy" for "by").

Usage:
    from app.raman_saab.procedure.citations import cite, CITATIONS
    cite("two_of_three")    # -> "HTJAH:2111-2113"
"""
from __future__ import annotations

from typing import Final

#: key -> (first line, last line, verbatim snippet inside that range)
CITATIONS: Final[dict[str, tuple[int, int, str]]] = {
    # -- Stage 0 ---------------------------------------------------------------------------
    "functional_for_dasha": (519, 521, "useful when predicting the results of Dasha"),
    "functional_benefics": (575, 578, "The lord of the 9th is decidedly more benefice"),
    "functional_malefics": (583, 585, "the 11th lord is the"),
    "yogakaraka": (613, 613, "owning both a Kendra (quadrant) and a Trikona (trine)"),
    "yoga_orb": (643, 644, "within 12° of each other"),
    "stronger_reference": (644, 646, "either the ascendant or the Moon, whichever is"),
    "span_first": (763, 765, "whether the"),
    "dasa_within_span": (1578, 1580, "the longevity"),
    "minor_lord_only": (1621, 1623, "only as minor"),
    # -- the house template ------------------------------------------------------------------
    "lord_first_printed": (474, 474, "The strength, aspects, conjunctions and location of the lord"),
    "house_over_bad_lord": (503, 505, "evil results should not be predicted"),
    "house_lord_karaka_order": (3330, 3332, "(a) The strength or"),
    "navamsa_adjusts": (1806, 1808, "In the Navamsha, however, Saturn is"),
    "navamsa_relieving": (3849, 3850, "The only relieving feature is"),
    "rasi_over_navamsa": (4688, 4689, "more than"),
    "navamsa_alone_insufficient": (3807, 3809, "not sufficiently strong"),
    "star_lord_matters": (13239, 13242, "The asterism occupied by a"),
    "star_lord_longevity": (11796, 11798, "occupies his own"),
    "star_lord_father": (13344, 13344, "Jupiter had occupied Visakha"),
    "bhava_frees_house": (1945, 1946, "Ketu is actually in the 12th Bhava"),
    "bhava_sandhi_disqualifies": (13989, 13991, "Bhava-sandhi (junction point)"),
    "empty_house_stated": (16570, 16571, "neither"),
    "empty_house_good": (1801, 1803, "Lagna is occupied by no planet. This is good"),
    "malefic_afflicts": (8494, 8494, "Saturn's presence as a malefic is not good causing affliction"),
    "benefic_fortifies": (8565, 8567, "their aspects fortify the 7th house"),
    "kartari": (1184, 1184, "It is hemmed in between Rahu and Saturn"),
    "subhakartari": (1823, 1823, "hemmed in between benefices causing Subhakarthari"),
    "navamsa_house": (5690, 5691, "of the 5th house from"),
    "from_moon": (5690, 5691, "affliction of the 5th lord from Chandra Lagna"),
    "combust_powerless": (3788, 3790, "becoming combust and hence powerless"),
    "debility_combustion_destroys": (3436, 3437, "is debilitated, is in combustion"),
    # Round 2 (A3): Raman's sign words follow the natural relation.
    "inimical_sign_natural": (2930, 2931, "but placed in an inimical sign"),
    "enemy_sign_natural": (3811, 3812, "in the sign of an enemy"),
    "friendly_sign_natural": (3779, 3779, "occupies Gemini, a friendly sign"),
    # Round 2 (A8): an unoccupied, unaspected house is fairly strong.
    "empty_house_fairly_strong": (3669, 3670, "benefice or malefic. Hence it is fairly strong"),
    "empty_house_fairly_strong_2": (2809, 2810, "Hence it is fairly strong"),
    # Round 2 (B1): a lord in the 8th from its own house.
    "eighth_from_own_house": (3826, 3828, "his situation in the 8th from the 3rd"),
    # Round 2 (B2): a natural benefic owning the 6th afflicts by contact.
    "benefic_sixth_lord": (4405, 4406, "association with the Moon lord of the sixth"),
    "benefic_sixth_lord_blemish": (4472, 4473, "with Mercury lord of the third and sixth and hence blemished"),
    # -- functional over natural (4.3) -------------------------------------------------------
    "own_lord_defused": (8594, 8595, "as he happens to be the 7th lord himself"),
    "yogakaraka_defused": (8748, 8748, "because he is a Yoga Karaka"),
    "functional_malefic_no_help": (8930, 8931, "since he is a functional malefic"),
    "benefic_bad_lordship": (2218, 2220, "because Venus is lord of 6"),
    "dual_nature_named": (4405, 4405, "good as lord of Lagna and bad as a natural malefic"),
    # -- cancellation devices (4.6) ----------------------------------------------------------
    "neechabhanga": (1822, 1823, "neechabhanga or cancellation of debility"),
    # Round 2: Raman's printed conditions for the cancellation (A2), nothing more.
    "neechabhanga_conditions": (16178, 16181, "gets exalted in Amsa"),
    "neechabhanga_kendra": (16178, 16179, "is in Kendra from the Moon or Lagna"),
    "own_sign_cancels": (2740, 2741, "This blemish is cancelled because"),
    "exalted_benefic_cancels": (2743, 2744, "cancelled as Jupiter in exaltation aspects"),
    "dispositor_aspect_harmless": (7033, 7035, "his aspect will not cause much mischief"),
    # -- karaka in its own bhava ---------------------------------------------------------------
    "karaka_in_bhava_mother": (4424, 4425, "the Karaka for the mother in the appropriate Bhava"),
    "karaka_in_bhava_children": (5834, 5834, "PutraKaraka in the fifth house is not a good position"),
    "karaka_in_bhava_father": (12955, 12956, "Karaka Sun in"),
    # -- conclusion rules (4.1, 4.2, 4.4, 4.5) ----------------------------------------------
    "two_of_three": (2111, 2113, "at least two of the three factors"),
    "two_afflicted_ignore_karaka": (5729, 5730, "the Karaka's"),
    "lord_over_house_brothers": (3696, 3697, "whilst the third house is not good, the third lord"),
    "lord_karaka_over_house": (3854, 3855, "as the lord cum the Karaka is"),
    "mother_karaka_decides": (4435, 4436, "Matru-Karaka is definitely afflicted"),
    "mother_house_lord_duration": (4619, 4620, "strength of the fourth house and fourth lord"),
    "mother_longevity": (4394, 4397, "Matru-Karaka as the"),
    "education_karaka_vs_house": (4856, 4858, "VidyaKaraka's affliction"),
    "education_karaka_strong": (4903, 4904, "It is the Vidya-Karaka that is really strong"),
    "children_born_sorrow": (5795, 5798, "indicates the birth of children"),
    "children_not_surviving": (5839, 5841, "their survival is not"),
    "children_not_denied": (5879, 5879, "birth of children is not denied"),
    "father_karaka_decides": (13126, 13127, "Afflictions to the pitruKaraka"),
    "father_marakas": (12929, 12932, "Maraka planets with"),
    "longevity_lords": (11415, 11416, "8th lord stronger than Lagna lord"),
    "longevity_saturn": (11703, 11704, "the strength of Karaka Saturn pushes"),
    "gains_wider": (16930, 16931, "Financial gains depend not only on the"),
    "elder_brothers_lagna_moon": (16583, 16584, "both from Lagna and the Moon"),
    "benefic_floor": (8696, 8697, "has prevented a"),
    "benefic_floor_brothers": (16725, 16725, "prevents denial of elder co-horns"),
    "denial_no_benefic": (8669, 8670, "no redeeming beneficeial influences"),
    "blemish_quality": (8517, 8518, "result in a stable marriage"),
    "blemish_duration": (17246, 17251, "could not last long"),
    "jupiter_antidote": (2283, 2284, "acting as an antidote"),
    "twelfth_lord_dusthana": (17813, 17814, "If the 12th lord combines with the 6th and 8th lords"),
    # -- karakas actually used (section 6) ---------------------------------------------------
    "karakas_fourth": (4386, 4388, "the Moon and the fourth for mother"),
    "karaka_griha": (4970, 4970, "Mars Griha-Karaka"),
    "karaka_elder_brothers": (16554, 16556, "Mars who is the Karaka for 'brothers'"),
    "karaka_gains": (16791, 16792, "Jupiter, DhanaKaraka, can also be taken"),
    "karaka_twelfth_printed": (17733, 17735, "he is the"),
    "karaka_father_timing": (12737, 12738, "the Sun who is the"),
    # -- timing ------------------------------------------------------------------------------
    "influence_set": (1586, 1589, "planet or planets in"),
    "par_excellence_printed": (1592, 1596, "produce results predominantly of"),
    "gains_with_second": (16795, 16801, "the planet occupying"),
    "gains_yogas": (16809, 16811, "if they have mutually"),
    "raja_kendra_trikona": (622, 626, "Kendradhipati (angular lord) becomes associated with"),
    "raja_nine_ten": (630, 632, "When the 9th and 10th lords have exchanged their places"),
    "raja_nine_ten_aspect": (634, 634, "When the 9th and 10th lords fully aspect each other"),
    "association_defined": (4321, 4322, "connotes aspect"),
    "marriage_late_33": (8638, 8640, "after 33 years"),
    "raja_lord_times": (4324, 4325, "Where a lord is involved in a Raja yoga"),
    "maraka_primary": (776, 781, "Lord of the 2nd or 7th is a determinant of death"),
    "maraka_caveat": (818, 820, "Instances are wanting"),
    "maraka_associates_strongest": (783, 784, "planets in conjunction with lords of 2nd and"),
    "mother_death_marakas": (4478, 4482, "should give the"),
    "own_star_cannot_kill": (4515, 4516, "in his own constellation, he could not"),
    "spouse_death_loss_house": (9191, 9192, "in the house of loss from the 7th house"),
    "spouse_death_second_from_seventh": (9173, 9175, "becomes a Maraka to the husband"),
    "brother_death": (16589, 16591, "is in the 12th from the 11th house"),
    "marriage_seven_slots": (8524, 8527, "in respective order in their periods"),
    "marriage_age_prune": (8549, 8551, "Mercury Dasha ends in childhood"),
    "node_sign_lord": (2761, 2765, "Ketu must give the results of the Sun"),
    "node_star_lord": (4478, 4479, "whose star he occupies"),
    "node_delegation": (11707, 11709, "passes on his killing powers"),
    "md_ad_ideal": (14115, 14116, "an ideal combination"),
    "md_ad_bad": (11222, 11223, "dwirdwaDasha"),
    "md_ad_bad_brothers": (18583, 18584, "dwirdwaDasha (2/12 position)"),
    "saturn_transit_death": (11226, 11232, "the momentum of the last signal for death"),
    "transit_accelerator": (4462, 4463, "All these accelerated the death"),
    "children_dasa_in_span": (5310, 5313, "whether the native is likely to enjoy the"),
}


def cite(key: str) -> str:
    """The printable citation for ``key``: ``HTJAH:<first>`` or ``HTJAH:<first>-<last>``."""
    first, last, _ = CITATIONS[key]
    return f"HTJAH:{first}" if first == last else f"HTJAH:{first}-{last}"
