"""The later-author rules: one cusp sub-lord (CSL), a list of conditions, a cited indication.

Rules are written as the authors wrote them; the condition kinds are defined in
:mod:`app.kp.later.rules`. House groups are tuples of tuples: each inner tuple
is one group, any house of which counts, and every group must be met (ruling
LR2: "4-5-11" is one group, "6 and 11" two). ``context`` is ``"natal"`` or
``"horary"`` (the author's own setting); ``sex`` is set where the author ties a
rule to one sex.

Left out on purpose (rulings LR3, LR7): death, its manner or timing, lifespan,
"life threat", suicide, murder; moral-character readings (criminal mind, illicit
affair, bad habits, elopement, timidity); punishment; rules resting on an
undefined "connection" with a planet or sign; restatements of Krishnamurti's own
rules with nothing added; general method passages that name no cusp.

Usage:
    from app.kp.later.registry import LATER_RULES
    LATER_RULES["sixth_service_ac"].conds
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from app.kp.later.citations import LATER_CITATIONS
from app.kp.later.sources import SOURCES


@dataclass(frozen=True, slots=True)
class LaterRule:
    """One later author's rule: cusp ``cusp``'s sub-lord must meet every condition."""

    key: str
    cusp: int
    conds: tuple[tuple[str, object], ...]
    indicates: str
    context: str
    citation: str
    sex: str | None = None

    @property
    def source(self) -> str:
        return LATER_CITATIONS[self.citation].source

    @property
    def author(self) -> str:
        return SOURCES[self.source].author


_r = LaterRule
_RULES: Final[tuple[LaterRule, ...]] = (
    _r('third_trade', 3, (('signifies', ((2, 3, 6, 10, 11),)),), 'selling (hawking) in a dignified way, good profits', 'natal', 'AS1-third_trade'),
    _r('fourth_mercury_music', 4, (('is', ('Mercury',)),), 'learns wind instruments (flute, clarinet, saxophone)', 'natal', 'AS1-fourth_mercury_music'),
    _r('fourth_mars_martial', 4, (('is', ('Mars',)), ('signifies', ((4, 5, 11),)),), 'learns martial arts', 'natal', 'AS1-fourth_mars_martial'),
    _r('fourth_venus_tailoring', 4, (('is', ('Venus',)), ('signifies', ((4, 5, 11),)),), 'learns tailoring as a vocation', 'natal', 'AS1-fourth_venus_tailoring'),
    _r('ninth_astrologer_research', 9, (('is', ('Mercury', 'Jupiter')), ('signifies', ((2, 9, 10, 11),)),), 'well versed in astrology; research', 'natal', 'AS1-ninth_astrologer_research'),
    _r('fourth_star_saturn_in_4', 4, (('star_is', ('Saturn',)), ('star_occupies', (4,)),), 'education, but not in good measure', 'natal', 'AS2-fourth_star_saturn_in_4'),
    _r('asc_star_in_6', 1, (('star_occupies', (6,)),), 'sickly', 'natal', 'AS3-asc_star_in_6'),
    _r('asc_star_in_1_11', 1, (('star_occupies', (1, 11)),), 'health generally very good', 'natal', 'AS3-asc_star_in_1_11'),
    _r('second_node_mute', 2, (('is', ('Rahu', 'Ketu')), ('sign_in', (3, 7, 11)),), 'defect in speech', 'natal', 'AS3-second_node_mute'),
    _r('second_5_11', 2, (('signifies', ((5,), (11,))),), 'child birth', 'natal', 'AS3-second_5_11'),
    _r('second_7_11', 2, (('signifies', ((7,), (11,))),), 'marriage', 'natal', 'AS3-second_7_11'),
    _r('second_6_11', 2, (('signifies', ((6,), (11,))),), 'success in litigation or promotion', 'natal', 'AS3-second_6_11'),
    _r('second_7_10', 2, (('signifies', ((7,), (10,))),), 'lucrative income through business', 'natal', 'AS3-second_7_10'),
    _r('second_to_7', 2, (('signifies', ((7,),)),), 'second marriage', 'natal', 'AS3-second_to_7'),
    _r('second_star_6_11', 2, (('star_signifies', ((6,), (11,))),), 'very good financial status', 'natal', 'AS3-second_star_6_11'),
    _r('second_star_2_10', 2, (('star_signifies', ((2,), (10,))),), 'moderate affluence', 'natal', 'AS3-second_star_2_10'),
    _r('second_star_1_3', 2, (('star_signifies', ((1,), (3,))),), 'just satisfactory finances', 'natal', 'AS3-second_star_1_3'),
    _r('second_jupiter_11', 2, (('is', ('Jupiter',)), ('signifies', ((11,),)),), 'what one says is true and comes to pass', 'natal', 'AS3-second_jupiter_11'),
    _r('second_saturn', 2, (('is', ('Saturn',)),), 'juggles words while speaking', 'natal', 'AS3-second_saturn'),
    _r('second_2_12', 2, (('signifies', ((2,), (12,))),), 'money through behind-the-screen matters', 'natal', 'AS3-second_2_12'),
    _r('third_bold', 3, (('signifies', ((2, 10, 11),)),), 'bold to undertake work; succeeds', 'natal', 'AS3-third_bold'),
    _r('third_mars', 3, (('is', ('Mars',)),), 'never contented', 'natal', 'AS3-third_mars'),
    _r('third_letter', 3, (('signifies', ((3,), (11,))),), 'receipt of a letter', 'horary', 'AS3-third_letter'),
    _r('third_appeal', 3, (('star_signifies', ((6,), (11,))),), 'success in an appeal', 'horary', 'AS3-third_appeal'),
    _r('third_daring', 3, (('signifies', ((1,),)),), 'a daring person', 'natal', 'AS3-third_daring'),
    _r('fourth_adoption', 4, (('dual_or_mercury', None), ('signifies', ((8,),)),), 'the child may go in adoption', 'natal', 'AS3-fourth_adoption'),
    _r('fourth_treasure', 4, (('star_signifies', ((2, 6, 11),)),), 'treasure in the building', 'horary', 'AS3-fourth_treasure'),
    _r('fourth_reach_home', 4, (('star_signifies', ((11,),)), ('sign_in', (0, 3, 6, 9)),), 'will reach home soon', 'horary', 'AS3-fourth_reach_home'),
    _r('fourth_medical_exam', 4, (('signifies', ((10,), (11,))),), 'passes a medical examination', 'horary', 'AS3-fourth_medical_exam'),
    _r('fourth_construct', 4, (('signifies', ((4,), (11,), (12,))),), 'constructs a house', 'natal', 'AS3-fourth_construct'),
    _r('fourth_residence_change', 4, (('star_signifies', ((3,), (12,))),), 'change of residence', 'natal', 'AS3-fourth_residence_change'),
    _r('fifth_no_child', 5, (('signifies', ((1,), (4,), (10,))),), 'children denied', 'natal', 'AS3-fifth_no_child'),
    _r('fifth_cards_win', 5, (('signifies', ((6,), (11,))),), 'wins at cards or races', 'natal', 'AS3-fifth_cards_win'),
    _r('fifth_cards_loss', 5, (('signifies', ((5,), (12,))),), 'loses at cards or races', 'natal', 'AS3-fifth_cards_loss'),
    _r('fifth_music', 5, (('star_occupies', (1,)), ('star_sign_in', (4, 10)),), 'musical talent', 'natal', 'AS3-fifth_music'),
    _r('fifth_love_marriage', 5, (('star_signifies', ((7,), (11,))),), 'love affair turns into marriage', 'natal', 'AS3-fifth_love_marriage'),
    _r('fifth_property_lost', 5, (('signifies', ((4,), (12,))),), 'property lost through debauchery', 'natal', 'AS3-fifth_property_lost'),
    _r('fifth_speculation', 5, (('signifies', ((2,), (5,), (6,), (11,))),), 'gains in speculation', 'natal', 'AS3-fifth_speculation'),
    _r('fifth_exchange', 5, (('signifies', ((6,), (11,))),), 'gains in exchange business', 'natal', 'AS3-fifth_exchange'),
    _r('sixth_litigation', 6, (('signifies', ((1,), (6,), (11,))),), 'success in litigation', 'natal', 'AS3-sixth_litigation'),
    _r('seventh_stopped', 7, (('signifies', ((1, 6, 10, 12),)),), 'marriage with the party in question will not take place', 'horary', 'AS3-seventh_stopped'),
    _r('seventh_partner', 7, (('star_signifies', ((6,), (11,))),), 'a business partner', 'natal', 'AS3-seventh_partner'),
    _r('seventh_opponent', 7, (('signifies', ((5,), (7,), (8,), (12,))),), 'a very powerful opponent', 'natal', 'AS3-seventh_opponent'),
    _r('seventh_happy', 7, (('is', ('Venus', 'Jupiter')), ('signifies', ((2,), (11,))),), 'very happy married life', 'natal', 'AS3-seventh_happy'),
    _r('eighth_borrow', 8, (('signifies', ((5,), (6,), (8,), (12,))),), 'borrows heavily', 'natal', 'AS3-eighth_borrow'),
    _r('eighth_repay', 8, (('signifies', ((2, 10, 11),)),), 'returns borrowed money', 'natal', 'AS3-eighth_repay'),
    _r('ninth_astrologer', 9, (('star_signifies', ((2,), (9,), (11,))),), 'a successful astrologer', 'natal', 'AS3-ninth_astrologer'),
    _r('tenth_service', 10, (('signifies', ((6,),)),), 'earns by service', 'natal', 'AS3-tenth_service'),
    _r('tenth_business', 10, (('signifies', ((7,),)),), 'earns by business', 'natal', 'AS3-tenth_business'),
    _r('tenth_both', 10, (('sign_in', (2, 5, 8, 11)), ('signifies', ((6,), (7,))),), 'earns by service and business', 'natal', 'AS3-tenth_both'),
    _r('eleventh_water', 11, (('star_sign_in', (3, 7, 11)),), 'will strike water', 'horary', 'AS3-eleventh_water'),
    _r('eleventh_interview', 11, (('direct', None), ('signifies', ((3,), (9,))),), 'interview succeeds', 'horary', 'AS3-eleventh_interview'),
    _r('eleventh_harmony', 11, (('signifies', ((2, 5, 7, 11),)),), 'harmony and happy married life', 'natal', 'AS3-eleventh_harmony'),
    _r('twelfth_foreign_trip', 12, (('signifies', ((3, 9, 12), (6,))),), 'trip on a foreign assignment', 'natal', 'AS3-twelfth_foreign_trip'),
    _r('twelfth_left_eye', 12, (('signifies', ((2,), (6,), (8,), (12,))),), 'defect of the left eye', 'natal', 'AS3-twelfth_left_eye'),
    _r('seventh_marriage_star', 7, (('star_signifies', ((2, 7, 11),)),), 'marriage comes off', 'natal', 'AS3-seventh_marriage_star'),
    _r('twelfth_debts_repaid', 12, (('signifies', ((5, 8, 12),)),), 'debts will be repaid', 'natal', 'AS3-twelfth_debts_repaid'),
    _r('seventh_business_wound_up', 7, (('star_occupies', (5, 8, 12)), ('star_sign_in', (1, 5, 9)),), 'business wound up through loss', 'natal', 'AS3-seventh_business_wound_up'),
    _r('sixth_star_retro', 6, (('star_retro', None),), 'cannot borrow', 'horary', 'AS5-sixth_star_retro'),
    _r('sixth_direct_borrow', 6, (('both_direct', None),), 'able to borrow', 'horary', 'AS5-sixth_direct_borrow'),
    _r('ninth_mercury_pretender', 9, (('is', ('Mercury',)), ('signifies', ((5, 8, 9),)),), 'pretends to know astrology', 'natal', 'AS5-ninth_mercury_pretender'),
    _r('eighth_troubles_diverted', 8, (('signifies_ab', ((1, 2, 3, 6, 10, 11),)),), "the 8th house's troubles are diverted, whatever dasa runs", 'natal', 'SPK-eighth_troubles_diverted'),
    _r('eleventh_ambition', 11, (('signifies', ((1,),)),), 'ambition fulfilled', 'natal', 'AS6-eleventh_ambition'),
    _r('twelfth_abroad_direct_star', 12, (('not_star_retro', None), ('signifies', ((3, 9, 12),)),), 'travel abroad', 'natal', 'AS6-twelfth_abroad_direct_star'),
    _r('twelfth_ninth_interlinked', 12, (('signifies', ((9,),)), ('cusp_signifies', (9, ((12,),))),), 'goes abroad', 'natal', 'AS6-twelfth_ninth_interlinked'),
    _r('third_line_out_of_order', 3, (('star_retro', None),), 'the line is reported out of order', 'horary', 'AS6-third_line_out_of_order'),
    _r('third_call_pending', 3, (('retro', None),), 'the call is kept pending, connected later', 'horary', 'AS6-third_call_pending'),
    _r('eleventh_cannot_hear', 11, (('star_retro', None),), 'connected, but neither party can hear', 'horary', 'AS6-eleventh_cannot_hear'),
    _r('third_appeal_success', 3, (('star_signifies', ((6,), (11,))),), 'the appeal succeeds', 'horary', 'AS6-third_appeal_success'),
    _r('third_appeal_fails', 3, (('star_signifies', ((5,), (12,))),), 'the appeal fails', 'horary', 'AS6-third_appeal_fails'),
    _r('fifth_love_materialises', 5, (('star_signifies', ((7,), (11,))),), 'the love affair materialises', 'horary', 'AS6-fifth_love_materialises'),
    _r('fifth_love_dropped', 5, (('star_signifies', ((12,),)),), 'the consultant drops the idea', 'horary', 'AS6-fifth_love_dropped'),
    _r('fourth_mars_land', 4, (('is', ('Mars',)),), 'gain of house, flat or land', 'natal', 'AS6-fourth_mars_land'),
    _r('eleventh_water_tapped', 11, (('either_sign_in', (3, 7, 11)),), 'water is struck', 'horary', 'AS6-eleventh_water_tapped'),
    _r('eleventh_water_quickly', 11, (('either_sign_in', (3, 7, 11)), ('star_is', ('Moon', 'Venus', 'Mercury')),), 'water is struck quickly', 'horary', 'AS6-eleventh_water_quickly'),
    _r('fourth_construct_house', 4, (('both_direct', None), ('signifies', ((4, 11, 12),)),), 'able to construct a house', 'horary', 'AFB-fourth_construct_house'),
    _r('fourth_construct_negative', 4, (('both_retro', None),), 'house construction: the reply is negative', 'horary', 'AFB-fourth_construct_negative'),
    _r('seventh_marriage_conjoined', 7, (('signifies_e', ((2, 7, 11),)),), 'marriage promised', 'natal', 'AFB-seventh_marriage_conjoined'),
    _r('seventh_jupiter_aspect', 7, (('not_signifies_e', (2, 7, 11)), ('aspected_by', ('Jupiter',)),), 'marriage promised', 'natal', 'AFB-seventh_jupiter_aspect'),
    _r('lagna_returned_home', 1, (('signifies', ((2,), (4,))),), 'the missing person has already returned home', 'horary', 'AFB-lagna_returned_home'),
    _r('twelfth_overseas', 12, (('signifies', ((3,), (9,))),), 'overseas travel', 'natal', 'AFB-twelfth_overseas'),
    _r('tenth_election', 10, (('signifies', ((3, 10, 11),)),), 'can win an election', 'natal', 'EZN-tenth_election'),
    _r('eleventh_recovery', 11, (('signifies', ((5,), (11,))),), 'recovery from illness', 'horary', 'EZN-eleventh_recovery'),
    _r('lagna_health_not_good', 1, (('signifies', ((6, 8, 12),)),), 'not good for health', 'natal', 'EZN-lagna_health_not_good'),
    _r('sixth_disease', 6, (('signifies', ((6, 8, 12), (1,))),), 'may suffer from disease', 'natal', 'EZN-sixth_disease'),
    _r('twelfth_cheated', 12, (('signifies', ((5, 8, 12),)),), 'a chance of being cheated', 'natal', 'EZN-twelfth_cheated'),
    _r('lagna_accident_recovery', 1, (('signifies', ((1, 5, 11),)),), 'recovers after or escapes an accident', 'horary', 'EZN-lagna_accident_recovery'),
    _r('third_rumour_false', 3, (('is', ('Saturn',)),), 'the rumour is false', 'horary', 'EZN-third_rumour_false'),
    _r('second_second_marriage', 2, (('signifies', ((7, 11),)),), 'second marriage', 'natal', 'EZN-second_second_marriage'),
    _r('ninth_second_marriage', 9, (('signifies', ((2, 7, 11),)),), 'second marriage', 'natal', 'EZN-ninth_second_marriage'),
    _r('eleventh_lottery', 11, (('signifies_ac', ((2, 6, 11),)), ('signifies', ((3,),)), ('not_signifies', (5, 8, 12)),), 'can win a lottery prize', 'natal', 'EZN-eleventh_lottery'),
    _r('tenth_sell_property', 10, (('signifies', ((3, 5, 10),)),), 'able to sell immovable property', 'natal', 'EZN-tenth_sell_property'),
    _r('sixth_service_ac', 6, (('signifies_ac', ((2, 6, 10),)),), 'service or earning promised', 'natal', 'EZN-sixth_service_ac'),
    _r('tenth_service_ac', 10, (('signifies_ac', ((2, 6, 10),)),), 'service or earning promised', 'natal', 'EZN-tenth_service_ac'),
    _r('third_lottery', 3, (('signifies', ((2, 6, 11),)), ('not_signifies', (1, 5, 9)),), 'gain through lottery', 'natal', 'EZN-third_lottery'),
    _r('eleventh_lottery_abroad', 11, (('signifies', ((9, 12), (2, 6, 11))), ('not_signifies', (1, 5, 8)),), 'gain through lottery abroad', 'natal', 'EZN-eleventh_lottery_abroad'),
    _r('seventh_law_making', 7, (('signifies', ((9, 10, 11),)),), 'law making in parliament', 'horary', 'EZN-seventh_law_making'),
    _r('third_courier', 3, (('signifies', ((3, 11),)),), 'the courier will be received', 'horary', 'EZN-third_courier'),
    _r('eleventh_courier', 11, (('signifies', ((3, 11),)),), 'the courier will be received', 'horary', 'EZN-eleventh_courier'),
    _r('eleventh_visa', 11, (('star_signifies', ((3, 9, 11),)),), 'gets the visa', 'horary', 'EZN-eleventh_visa'),
    _r('sixth_permanent_job', 6, (('signifies_ss', ((2,), (10,), (11,))), ('not_signifies_ss', (5, 9)),), 'a permanent job', 'natal', 'EZN-sixth_permanent_job'),
    _r('sixth_temporary_job', 6, (('signifies_ss', ((2,), (10,), (11,), (5, 9))),), 'a temporary job, or not sticking to one job', 'natal', 'EZN-sixth_temporary_job'),
    _r('eleventh_provident_fund', 11, (('signifies', ((2, 6, 8, 11),)),), 'provident fund or pension money received', 'natal', 'EZN-eleventh_provident_fund'),
    _r('eighth_accident', 8, (('signifies', ((8, 12),)),), 'may face an accident', 'natal', 'EZN-eighth_accident'),
    _r('twelfth_accident', 12, (('signifies', ((8, 12),)),), 'may face an accident', 'natal', 'EZN-twelfth_accident'),
    _r('tenth_leave_job', 10, (('signifies', ((1, 5, 9),)),), 'can leave the service', 'horary', 'EZN-tenth_leave_job'),
    _r('sixth_leave_job', 6, (('signifies', ((1, 5, 9),)),), 'can leave the service', 'horary', 'EZN-sixth_leave_job'),
    _r('ninth_higher_education', 9, (('signifies_ac', ((4, 9, 11),)),), 'higher education assured', 'natal', 'EZN-ninth_higher_education'),
    _r('third_marriage_negotiation', 3, (('signifies', ((3, 7, 9),)),), 'undergoes negotiation for marriage', 'natal', 'EZN-third_marriage_negotiation'),
    _r('fifth_childbirth_female', 5, (('signifies', ((2, 5, 11),)),), 'childbirth promised', 'natal', 'EZN-fifth_childbirth_female', sex='female'),
    _r('eleventh_childbirth_male', 11, (('signifies', ((2, 5, 11),)),), 'childbirth promised', 'natal', 'EZN-eleventh_childbirth_male', sex='male'),
    _r('fifth_not_pregnant', 5, (('sign_in', (0, 2, 4, 5)), ('star_sign_in', (0, 2, 4, 5)),), 'the woman is not pregnant', 'horary', 'EZN-fifth_not_pregnant', sex='female'),
    _r('fifth_no_child_female', 5, (('signifies', ((1, 4, 8),)),), 'the woman never has a child', 'natal', 'EZN-fifth_no_child_female', sex='female'),
    _r('eleventh_no_cure', 11, (('signifies', ((6,), (12,))),), 'no cure or recovery from the illness', 'horary', 'EZN-eleventh_no_cure'),
    _r('fourth_discharge', 4, (('signifies', ((4, 11),)),), 'discharged from hospital', 'horary', 'EZN-fourth_discharge'),
    _r('seventh_marriage_ac', 7, (('signifies_ac', ((2, 7, 11),)),), 'marriage promised', 'natal', 'EZN-seventh_marriage_ac'),
    _r('eighth_theft_recovery', 8, (('signifies_ac', ((2, 6, 11),)), ('not_signifies', (5, 8, 12)),), 'the stolen article is recovered', 'horary', 'EZN-eighth_theft_recovery'),
    _r('seventh_gain', 7, (('signifies_ac', ((2, 10, 11),)),), 'gain promised (business query)', 'horary', 'EZN-seventh_gain'),
    _r('eleventh_meeting', 11, (('signifies', ((3, 9, 11),)),), 'a meeting is possible', 'horary', 'EZN-eleventh_meeting'),
    _r('lagna_eleventh_exam', 1, (('signifies', ((4,), (6,), (9,), (11,))), ('cusp_signifies', (11, ((4,), (6,), (9,), (11,)))),), 'success in a professional examination', 'natal', 'EZN-lagna_eleventh_exam'),
    _r('fourth_lawsuit', 4, (('signifies_ac', ((2, 6, 10, 11),)),), 'wins the lawsuit', 'horary', 'EZN-fourth_lawsuit'),
    _r('lagna_normal_health', 1, (('signifies_ac', ((1, 11),)),), 'health is normal', 'natal', 'EZN-lagna_normal_health'),
    _r('twelfth_foreign_travel', 12, (('signifies', ((3, 9, 12),)),), 'foreign travel', 'natal', 'EZN-twelfth_foreign_travel'),
    _r('sixth_new_tenant', 6, (('signifies_ac', ((2, 4, 6, 11),)),), 'gets a new tenant', 'horary', 'EZN-sixth_new_tenant'),
    _r('sixth_cured', 6, (('signifies_ac', ((1, 5, 11),)),), 'disease cured, or saved from danger', 'horary', 'EZN-sixth_cured'),
    _r('eighth_cured', 8, (('signifies_ac', ((1, 5, 11),)),), 'disease cured, or saved from danger', 'horary', 'EZN-eighth_cured'),
    _r('twelfth_cured', 12, (('signifies_ac', ((1, 5, 11),)),), 'disease cured, or saved from danger', 'horary', 'EZN-twelfth_cured'),
    _r('eleventh_cured', 11, (('signifies_ac', ((1, 5, 11),)),), 'disease cured, or saved from danger', 'horary', 'EZN-eleventh_cured'),
    _r('fifth_education_abroad', 5, (('signifies', ((9, 12), (4, 9, 11))),), 'education abroad', 'natal', 'EZN-fifth_education_abroad'),
    _r('fourth_own_property', 4, (('signifies_ac', ((11,), (12,))),), 'owns land or a building', 'natal', 'EZN-fourth_own_property'),
    _r('sixth_chronic', 6, (('is_or_star_is', ('Saturn',)),), 'the disease will be chronic', 'natal', 'EZN-sixth_chronic'),
    _r('eleventh_sixth_match', 11, (('signifies', ((1, 2, 3, 6, 10, 11),)), ('cusp_signifies', (6, ((1, 2, 3, 6, 10, 11),))),), 'the team can win the match', 'horary', 'EZN-eleventh_sixth_match'),
)
LATER_RULES: Final[dict[str, LaterRule]] = {r.key: r for r in _RULES}

__all__ = ["LaterRule", "LATER_RULES"]
