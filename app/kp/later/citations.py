"""Verbatim quotes for every later-author rule, keyed ``<SOURCE>-<rule key>``.

Each quote is the uncorrected OCR text of its book (see :mod:`app.kp.later.sources`)
with whitespace collapsed; OCR slips are kept as printed and glossed in ``note``.
``tests/kp/test_later.py`` checks each quote against its page (or its run-on into
the next page) when the book's text is present.

Usage:
    from app.kp.later.citations import LATER_CITATIONS
    LATER_CITATIONS["EZN-sixth_service_ac"].ref()   # 'EZN:p.507'
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True, slots=True)
class LaterCitation:
    """One verbatim passage of a later-author book, cited by page marker."""

    key: str
    source: str
    page: int
    quote: str
    note: str = ""

    def ref(self) -> str:
        """Short reference such as ``AS3:p.49``."""
        return f"{self.source}:p.{self.page}"


_C = LaterCitation
LATER_CITATIONS: Final[dict[str, LaterCitation]] = {c.key: c for c in (
    _C("KNR-tin_win_method", "KNR", 172,
       "In the House Grouping Tables, if the cuspal sub lord of the house (mentioned in Column 1) is the "
       "significator (by occupation or ownership at the planet, star and sub levels) of the house or houses "
       "(mentioned in Column 4), then the event (shown in Column 3) is promised.",
       note="Tin Win's own instructions after the tables (printed p.91). Same page: 'marriage is promised, "
            "if the 7th cuspal sub lord signifies the required marriage houses 2 or 7 or 11' (ruling LR9)."),
    _C("AS6-gulbarga", "AS6", 1603,
       "As per ‘Gulbarga Theory’ if the sub lord of the Horary Number furnished happens to be either the Moon "
       "star lord or the lagna star-lord among the ruling planets also, then the query is to be answered in the "
       "affirmative; otherwise, not.",
       note="Restated at AS6:p.1613 and p.1645 and in the KP E-zine (p.845)."),
    _C("AS6-gulbarga-moment", "AS6", 1613,
       "The ruling planets at the moment were Rahu, Venus, Saturn, Moon and Mars. Hence the sublford of the number, "
       "Rahu is the star lord of ascendant. The answer is YES."),
    _C('AS1-third_trade', 'AS1', 138, 'if the sublord of the third when connected to houses 3-2-6-10-11, one will do selling the same hawking way but in a dignified manner and earn good profits.'),
    _C('AS1-fourth_mercury_music', 'AS1', 148, 'If the sublord of the 4th is Mercury, the Native will learn to play Pipe type musical instruments'),
    _C('AS1-fourth_mars_martial', 'AS1', 148, 'if the sublord of the 4th is Mars, and connected to 4-5-11, the Native will learn the martial arls like Karathe, Judo and so on.'),
    _C('AS1-fourth_venus_tailoring', 'AS1', 148, 'If the sublord of the 4th is Venus and connected to 4-5-11, the Native will learn tailoring for a profession under the vocational training courses.'),
    _C('AS1-ninth_astrologer_research', 'AS1', 189, 'If the sublord of the 9th is either Mercury or Jupiter, signifying 10-2-9-11, one will be well versed in astrology, make further research and bring out new findings.'),
    _C('AS2-fourth_star_saturn_in_4', 'AS2', 6, 'If the sublord of the 4th cusp is in the constellation of Saturn in 4 native would, no doubt, receive education but not in good measure.'),
    _C('AS3-asc_star_in_6', 'AS3', 40, 'Sickly native: If the sub lord of the lagna cusp is in the constellation of a planet in VI, one will be sickly.'),
    _C('AS3-asc_star_in_1_11', 'AS3', 42, 'If the sub lord of the Ascendant is deposited in the constellation of the planet occupying houses | or XI, health is generally very good.'),
    _C('AS3-second_node_mute', 'AS3', 42, 'If the sub lord of the Il cusp is either Kethu or Rahu and found in a Mute sign, there is defect in speech'),
    _C('AS3-second_5_11', 'AS3', 43, 'If the sub lord of the Il nd cusp signifies 5 an 11, predict child birth;'),
    _C('AS3-second_7_11', 'AS3', 43, 'If the sub lord of the Il nd cusp signifies 5 an 11, predict child birth; 7 and 11 predict marriage;'),
    _C('AS3-second_6_11', 'AS3', 43, '6 and 11 success in litigation or getting promotion in service,'),
    _C('AS3-second_7_10', 'AS3', 43, '7 and 10 lucrative income through business;'),
    _C('AS3-second_to_7', 'AS3', 43, 'If the sub lord of the Il cusp is well connected to VII second marriage,'),
    _C('AS3-second_star_6_11', 'AS3', 43, 'If the sub lord of the II nd cusp is in the constellation of a depositor of 6 and 11, shows very good financial status;'),
    _C('AS3-second_star_2_10', 'AS3', 43, 'In houses 2 and 10, moderate affluence;'),
    _C('AS3-second_star_1_3', 'AS3', 43, 'In houses 1 and 3, just satisfactory financial condition.'),
    _C('AS3-second_jupiter_11', 'AS3', 44, 'If the sub lord of the Il cusp is Jupiter and signifies Xl house, whatever he speaks is true and will come to pass.'),
    _C('AS3-second_saturn', 'AS3', 44, 'If the sub lord of the Il cusp is Saturn, one will use hide and seek and jugglery of words,'),
    _C('AS3-second_2_12', 'AS3', 44, 'If the sub lord of the Il nd cusp is connected to II and XIl, one will get money through behind the screen matters (in a secret manner).'),
    _C('AS3-third_bold', 'AS3', 45, 'Boldness to undertake job: If the sub lord of the Ill rd cusp is the significator of 2 or 10 or 11, one will surely undertake and come out successful.'),
    _C('AS3-third_mars', 'AS3', 45, 'If the sub lord of the Ill cusp is Mars, one will never be contented.'),
    _C('AS3-third_letter', 'AS3', 45, 'If the sub lord of the Ill cusp signifying 3 and 11 tells receipt of letter.'),
    _C('AS3-third_appeal', 'AS3', 45, 'cusp is deposited in the constellation of the significators of 6 and 11, there will be success in Appeal'),
    _C('AS3-third_daring', 'AS3', 45, 'If the sub lord of the Ill cusp is the full significator of 1st bhava, he is a daring person.'),
    _C('AS3-fourth_adoption', 'AS3', 46, 'Will a particular Child go in adoption: If the IV cusp sub lord of the child is deposited in a Dual sign or if the sub lord itself is Mercury and if the sub lord is a significator of VIII house'),
    _C('AS3-fourth_treasure', 'AS3', 46, 'Any treasure in my building; If the sub lord of the IV cusp is deposited in the constellation of planets 2, 6 or 11 you will have treasure.'),
    _C('AS3-fourth_reach_home', 'AS3', 47, 'If the sub lord of the IV cusp is in the constellation of a pl anet signifying Xl and in a movable sign, we will reach home soon.'),
    _C('AS3-fourth_medical_exam', 'AS3', 47, 'If the sub lord of the IV cusp is a significator of X house and well connected to XI you will appear for medical examination and come out successful.'),
    _C('AS3-fourth_construct', 'AS3', 48, 'House: If the sub lord of the IV cusp signifies 4, 11 and 12, one will construct a house'),
    _C('AS3-fourth_residence_change', 'AS3', 48, 'If the sub lord of the IV cusp is in the star of a planet signifying 3 and 12, change in residence cannot be ruled out.'),
    _C('AS3-fifth_no_child', 'AS3', 49, 'Children denied: If the sub lord of the Vth cusp signifies 1, 4 and 10 one can never have a child.'),
    _C('AS3-fifth_cards_win', 'AS3', 49, 'If the sub lord of the vth cusp signifies 6 and 11, wins most satisfactory'),
    _C('AS3-fifth_cards_loss', 'AS3', 49, '12 and 5 loss.'),
    _C('AS3-fifth_music', 'AS3', 50, 'If the sub lord of the Vth cusp is deposited in the constellation of a planet situated in 1st house which may be either Leo or Aquarius one has musical talent.'),
    _C('AS3-fifth_love_marriage', 'AS3', 50, 'If the sub lord of the V cusp is deposited in the constellation of a planet signifying 7 and 11, materialisation of love affair into marriage is definite.'),
    _C('AS3-fifth_property_lost', 'AS3', 50, 'Ones property is lost if the sub lord of the 5* cusp is a significator of 4 and 12, through debauchery.'),
    _C('AS3-fifth_speculation', 'AS3', 51, 'Speculation; If the sub lord of the 5th cusp signifies 2, 6, 5 and 11 one gains in speculation.'),
    _C('AS3-fifth_exchange', 'AS3', 52, 'In exchange business, if the sub lord of the 5th cusp signifies 6 & 11 you gain and if 5 & 12 you stand to loose.'),
    _C('AS3-sixth_litigation', 'AS3', 52, 'If the sub lord of the 6th cusp signifies 1, 6 and 11 success in litigation is promised.'),
    _C('AS3-seventh_stopped', 'AS3', 53, 'Marriage stopped: If the sub lord of the 7th cusp is the significator of 1, 6, 10 or 12, marriage will not take place with the party in question'),
    _C('AS3-seventh_partner', 'AS3', 53, 'If the sub lord of the 7th cusp is in the constellation of a planet signifying 6 and 11, you can have a partner in business.'),
    _C('AS3-seventh_opponent', 'AS3', 53, 'If the sub lord of the VII cusp is the significator of 7, 8, 12 and 5, opponent is very powerful in all walks of life.'),
    _C('AS3-seventh_happy', 'AS3', 54, 'If the sub lord of the VII cusp is either Venus or Jupiter and signifies 2 and 11, very happy marital life.'),
    _C('AS3-eighth_borrow', 'AS3', 55, 'If the sub lord of the 8th cusp signifies 5, 6, 8 and 12 he will be borrowing from A to Z.'),
    _C('AS3-eighth_repay', 'AS3', 55, 'If the sub lord of the 8th cusp signifies 2, 10 or 11 he returns the borrowed money.'),
    _C('AS3-ninth_astrologer', 'AS3', 56, 'Who is an Astrologer: If the sub lord of the 9th cusp is deposited in the star of planets signifying 2, 9 and 11, one can become successful astrologer.'),
    _C('AS3-tenth_service', 'AS3', 57, 'If the sub lord of 10th connected to 6, one earns by service,'),
    _C('AS3-tenth_business', 'AS3', 196, 'If the sublord is connected with 7 one earns by business.'),
    _C('AS3-tenth_both', 'AS3', 57, 'If the sub lord of 10th cusp is connected with a dual sign and with both 6 and 7, one will earn by service as well as business'),
    _C('AS3-eleventh_water', 'AS3', 58, 'Will | tap water: If the sub lord of the XI cusp is deposited in the constellation of a planet in a watery sign you will tap water.'),
    _C('AS3-eleventh_interview', 'AS3', 59, 'Interview: If the sub lord of the XI cusp is Direct and signifies 3 and 9, Interview is successful,'),
    _C('AS3-eleventh_harmony', 'AS3', 60, 'If the sub lord of the XI cusp is a significator of houses 2, 5, 7 or 11 perfect harmony and happy matrimonial life is indicated.'),
    _C('AS3-twelfth_foreign_trip', 'AS3', 60, 'If the sub lord of the XII cusp is a significator of 3 or 9 or 12 and also a strong significator of VI th, trip is there on foreign assignment.'),
    _C('AS3-twelfth_left_eye', 'AS3', 61, 'If the sub lord of the XII cusp signifies 6, 8 and 12 and some way connected to Il nd house, major defect to left eye is shown.'),
    _C('AS3-seventh_marriage_star', 'AS3', 96, 'Marriage comes off only if the sub lord of the 7th cusp is deposited in the star of a planet which signifies the 2nd or 7th or 11th house.'),
    _C('AS3-twelfth_debts_repaid', 'AS3', 99, 'if the sublord of the 12th cusp is significator of houses 5, 8 or 12 debts will be repaid.'),
    _C('AS3-seventh_business_wound_up', 'AS3', 198, 'If the sublord of the 7th cusp is in the constellation of a planet in 5, 8 or 12 in an earthy sign winding up of business due to loss is a certainty.'),
    _C('AS5-sixth_star_retro', 'AS5', 18, 'If the sub-lord of the sixth cusp Is deposited in the constellation of a retrograde palnet, you cannot borrow.'),
    _C('AS5-sixth_direct_borrow', 'AS5', 18, 'If the sub-lord and the lord of the constellation in which the sub-lord is placed are in direct motion, you will be able to borrow.'),
    _C('AS5-ninth_mercury_pretender', 'AS5', 86, 'If the sublord of the 9" is Mercury, signifying 9-5-8, the native without any research, pretending fo know everything of Astrology'),
    _C('SPK-eighth_troubles_diverted', 'SPK', 480, 'But if the sub - lord gets a strong signification for any one house of 1,2,3,6,10,11 a person need not at all worry about, whatever may be the Dasa is on or tocome.'),
    _C('AS6-eleventh_ambition', 'AS6', 1449, 'One\'s ambition will be fulfilled if the sub lord of the 11" cusp is the significator of the 1% house.'),
    _C('AS6-twelfth_abroad_direct_star', 'AS6', 1502, 'If the sublord of the 12" cusp is not deposited in the star of retrograde planet and signifies the 3, 9" or 12" house, then travel abroad is certain.'),
    _C('AS6-twelfth_ninth_interlinked', 'AS6', 1572, 'If the sublord of the cusp of 12 is a significator of 9, and conversely , the sublord of the cusp of 9 is a significator of 12, that is to say, if the cusps of 9 and 12 are inter connected through their subs, one cannot but go abroad.'),
    _C('AS6-third_line_out_of_order', 'AS6', 1607, 'if the sublord of the 3rd cusp situated in the star of a retrograde planet, the telephone Office will say that line in out of order.',
       note='Telephone-call horary (1980s exchange).'),
    _C('AS6-third_call_pending', 'AS6', 1607, 'But if the sublord himself is retrograde, he will be asked to keep the call pending',
       note='Telephone-call horary (1980s exchange).'),
    _C('AS6-eleventh_cannot_hear', 'AS6', 1607, 'If the sublord of th 11th cusp is in the star, the lord of which its retrograde then in spite of the connection being given, neigther party will be able to hear.',
       note='Telephone-call horary (1980s exchange).'),
    _C('AS6-third_appeal_success', 'AS6', 1626, 'if the sub lord of the third cusp is deposited in the constellation of the planet which is significator of 6" and 11" house then one will have success.'),
    _C('AS6-third_appeal_fails', 'AS6', 1626, 'But if the sub lord of the third cusp is deposited the constellation of a planet who is significator of 5" and 12" house one cannot have success.'),
    _C('AS6-fifth_love_materialises', 'AS6', 1636, 'If the sublord of the 5 cusp is deposited in the constellation of a planet who is a significator of 7 and 11, the materialization of Love affairs is promised.'),
    _C('AS6-fifth_love_dropped', 'AS6', 1637, 'But if the sublord of the 5° cusp is in the constellation of a planet signifying the 12" house, then the consultant himself will drop the idea.'),
    _C('AS6-fourth_mars_land', 'AS6', 1683, 'Further if the sub lord of 4" cusp is Mars then it promises gain of house or fiat or land.'),
    _C('AS6-eleventh_water_tapped', 'AS6', 1700, 'one will tap water from the well if the sublord of the 11 cusp or the lord of the star in which the sub-lord of the 11 cusp is situated, is posited ina watery sign.'),
    _C('AS6-eleventh_water_quickly', 'AS6', 1700, 'Further if the sub-lord is posited in the constellation of Moon, Venus or Mercury one will tap water quickly.'),
    _C('AFB-fourth_construct_house', 'AFB', 316, 'If Ihe sub-lord of 4fh cusp is direct and is in the constellationof a_ planet in direct motion and if the sub-lord significes 4, 11, or 12, you will be able to construct a house.'),
    _C('AFB-fourth_construct_negative', 'AFB', 316, 'But if the sub-lord is retrograde and in lhe constellation of a retrograde planet the reply is negative.'),
    _C('AFB-seventh_marriage_conjoined', 'AFB', 326, 'if the sub-lord of this cusp is a significator of any of the houses 2, 7, 11 by lordship, occupation, constellation, sub or by being conjoined with the significators of the above houses, marriage is promised.'),
    _C('AFB-seventh_jupiter_aspect', 'AFB', 326, 'In the absence of any of these, if the sub-lord of the 7th cusp receives good aspect from the greater benefic, Jupiter, marriage is promised.'),
    _C('AFB-lagna_returned_home', 'AFB', 1056, 'If the sub-lord of the lagna is intimately connected to houses 2 and 4, take it that he has already returned home.'),
    _C('AFB-twelfth_overseas', 'AFB', 1078, 'Therefore if the sub lord of the 12th cusp signifies houses 3 and 9 overseas Travel is indicated.'),
    _C('EZN-tenth_election', 'EZN', 12, 'If the cuspal sublord of 10th house signifies 3-10-11, then one can win any election.',
       note='The article credits the rule to Kanak Kumar B. Bosmia.'),
    _C('EZN-eleventh_recovery', 'EZN', 42, 'If the sublord of the 11‘ cusp signifies 5 and 11 Recovery from illness is promised.'),
    _C('EZN-lagna_health_not_good', 'EZN', 80, 'If the sub lord of the Asc. be the significator of 6 or 8 or 12, it is not good for health',
       note="Credited in the article to C. R. Bhatt, Horoscope and Diseases. The same article finds the rule holds 'in almost all charts'."),
    _C('EZN-sixth_disease', 'EZN', 81, 'If the sub lord of the 6th cusp be the significator of 6 or 8 or 12 and connected with 1, the native may suffer from disease',
       note='Credited in the article to C. R. Bhatt, Horoscope and Diseases.'),
    _C('EZN-twelfth_cheated', 'EZN', 127, 'If the cuspal sub lord of the 12t* be the significator of 5 (Gain to opponent)- 8 (Unfair thing)- 12 (misfortune), there is a chance that one can be cheated.'),
    _C('EZN-lagna_accident_recovery', 'EZN', 158, 'If the sub lord of the Ascendant cusp be the significator of 1-5-11, the native may recover after accident or escape from accident during the joint period of the significator of 1-5-11.'),
    _C('EZN-third_rumour_false', 'EZN', 186, 'If the cuspal sub lord of 3 happens to be Saturn, the rumor is false.'),
    _C('EZN-second_second_marriage', 'EZN', 195, 'Second marriage is indicated if the sub-lord of the 2nd cusp is also a significator of either of the houses 7 or 11.',
       note="OCR 'Yor' is 7 (houses 2, 7 or 11)."),
    _C('EZN-ninth_second_marriage', 'EZN', 195, 'Second marriage is indicated if the sub-lord of the 9th cusp is a significator of either of the houses 2 or Yor 11.',
       note="OCR 'Yor' is 7 (houses 2, 7 or 11)."),
    _C('EZN-eleventh_lottery', 'EZN', 649, 'If the cuspal sublord of 11th be the significator (in the star of the occupant or owner) of 224 (monetary gain), 6th (gain), or 11th (success/fulfillment of desire) and also connected with 374 (lottery) and does not signify 5, 8 or 12, only then one can win a lottery prize.',
       note="OCR '224' is 2nd, '374' is 3rd."),
    _C('EZN-tenth_sell_property', 'EZN', 353, 'If the sublord of the 10th cusp be the significator of 3-5-10 houses, the native is able to sell immovable property during the joint period of the significators of 3-5-10.'),
    _C('EZN-sixth_service_ac', 'EZN', 507, 'If the cuspal sublord of the 6th or 10th be the significator (in the star of the occupant or owner) of 2, 6, or 10 service or earning is promised',
       note="The same rule is credited to Kanak Bosmia's Prashna Jyotish on E-zine pp.40 and 954."),
    _C('EZN-tenth_service_ac', 'EZN', 507, 'If the cuspal sublord of the 6th or 10th be the significator (in the star of the occupant or owner) of 2, 6, or 10 service or earning is promised',
       note="The same rule is credited to Kanak Bosmia's Prashna Jyotish on E-zine pp.40 and 954."),
    _C('EZN-third_lottery', 'EZN', 536, 'If the sub lord of the 3rd cusp is the significator of 2-6-11 and not connected with 1-5-9 gain through lottery is promised'),
    _C('EZN-eleventh_lottery_abroad', 'EZN', 536, 'If the sub lord of the 11th cusp is the significator of 9-12 along with 2-6-11 and not connected with 1-5-8 gain through lottery is promised in foreign'),
    _C('EZN-seventh_law_making', 'EZN', 668, 'If the cuspal sub lord of the 7 (view of parliament, /9t* = view/ from /11t = parliament/) be the significator of 9 (making something legal/ law), 11 (support to give or take), 10 (document granting authority), then law making in parliament is promised'),
    _C('EZN-third_courier', 'EZN', 641, 'If the cuspal sublord of 3 or 11t* be the significator of 3 (document like courier, letter, in- strument etc) or 11 (gain, fulfilment of desire ), then courier will be received'),
    _C('EZN-eleventh_courier', 'EZN', 641, 'If the cuspal sublord of 3 or 11t* be the significator of 3 (document like courier, letter, in- strument etc) or 11 (gain, fulfilment of desire ), then courier will be received'),
    _C('EZN-eleventh_visa', 'EZN', 666, 'If the sublord of the 11th cusp is in the constellation of the significator of the houses 3/ 9/11, then one will surely get visa.'),
    _C('EZN-sixth_permanent_job', 'EZN', 709, 'If the sublord of the 6 cusp becomes the significator of 2, 10 and 11 houses through its Starlord or Sublord, then it shows permanent job',
       note="'through its Starlord or Sublord': houses via the star lord (levels A, C) or the CSL's sub-lord's own occupation/ownership (LR4)."),
    _C('EZN-sixth_temporary_job', 'EZN', 709, 'but if it becomes significators along with houses of 5th or 9th house also denotes temporary job or native is not likely to stick to one job.',
       note="'through its Starlord or Sublord': houses via the star lord (levels A, C) or the CSL's sub-lord's own occupation/ownership (LR4)."),
    _C('EZN-eleventh_provident_fund', 'EZN', 713, 'If the cuspal sublord of 11 be the significator of 8 (long term income like provident fund, pension), 2 (money), 6 (earnings through service), 11 (success in under takings) or in connection with Mercury/Jupiter, getting money of provident fund, pension is assured',
       note="The arm 'or in connection with Mercury/Jupiter' is not encoded (an undefined connection, ruling LR3)."),
    _C('EZN-eighth_accident', 'EZN', 716, 'If the cuspal sublord of 8 or 12th signifies 8 or 12, the native may face accident'),
    _C('EZN-twelfth_accident', 'EZN', 716, 'If the cuspal sublord of 8 or 12th signifies 8 or 12, the native may face accident'),
    _C('EZN-tenth_leave_job', 'EZN', 720, 'If the cuspal sublord of the 10 or 6 be the significator of 1, 5 or 9, then the querent can leave the service'),
    _C('EZN-sixth_leave_job', 'EZN', 720, 'If the cuspal sublord of the 10 or 6 be the significator of 1, 5 or 9, then the querent can leave the service'),
    _C('EZN-ninth_higher_education', 'EZN', 780, 'If the sub lord of the 9th (Higher education) cusp be the significator (in the star of the occu- pant or owner) of 4, 9, 11, then higher education is assure.'),
    _C('EZN-third_marriage_negotiation', 'EZN', 785, 'If the sub lord of the 34 cusp be the significator of 3-7-9, the native undergoes negotiation for marriage'),
    _C('EZN-fifth_childbirth_female', 'EZN', 802, 'If the sub lord of the 5th cusp (female) or the 11th cusp (male) is the significator (in the star of the occupant or owner) of 2 (increase in family), 5 (conception, child) or 11 (Sth from 7) or connected with 2, 5 or 11, child birth is promised.',
       note='The rule names the 5th cusp for a woman and the 11th for a man.'),
    _C('EZN-eleventh_childbirth_male', 'EZN', 802, 'If the sub lord of the 5th cusp (female) or the 11th cusp (male) is the significator (in the star of the occupant or owner) of 2 (increase in family), 5 (conception, child) or 11 (Sth from 7) or connected with 2, 5 or 11, child birth is promised.',
       note='The rule names the 5th cusp for a woman and the 11th for a man.'),
    _C('EZN-fifth_not_pregnant', 'EZN', 802, 'If the cuspal sub lord of the 5th house occupies the barren sign Aries, Gemini, Leo or Virgo and is in the star of the planet in the barren sign, then the woman concerned is not pregnant.'),
    _C('EZN-fifth_no_child_female', 'EZN', 802, 'If the cuspal sub lord of the 5‘ (pregnancy) is the significator of 1 (barrenness), 4 (12t from 5th) or 8 (sterility), the woman never have child.'),
    _C('EZN-eleventh_no_cure', 'EZN', 810, 'If the sub lord of the 11t cusp be the significator of 6 and 12, there is no cure or recovery from illness.'),
    _C('EZN-fourth_discharge', 'EZN', 810, 'If the sub lord of the 4th cusp be the significator 4 or 11, the native will be discharged from hospital.'),
    _C('EZN-seventh_marriage_ac', 'EZN', 818, 'If the sub lord of 7tt CSL be the significator (in the star of the occupant or owner) of 2,7,11 marriage is promised.'),
    _C('EZN-eighth_theft_recovery', 'EZN', 848, 'If the cuspal sub lord of 8th be the significator (in the star of the occupant or owner) of 24, 6th (loss to the thief) & 11 (fulfillment of desire), and should not connected with 5, 8 & 12, then only the theft article recovery is promised',
       note="OCR '24' is 2nd."),
    _C('EZN-seventh_gain', 'EZN', 854, 'If the cuspal sub lord of the 74 be the significator (in the star of the occupant or owner) of 2, 10 or 11, gain is promised'),
    _C('EZN-eleventh_meeting', 'EZN', 866, 'If the cuspal sub lord of the 11 be the significator of 3 (Meeting, Interview), 9(meeting with person) or 11(Gain, Success, fulfill of desire), then a meeting is possible.'),
    _C('EZN-lagna_eleventh_exam', 'EZN', 907, 'If the cuspal sub lord of the Asc & 11** be the significator of 4, 6, 9 and 11 success in Profes- sional Examination is promised'),
    _C('EZN-fourth_lawsuit', 'EZN', 909, 'If the cuspal sub lord of 4t (result of lawsuit) be the significator (in the star of occupant or owner) of 2 (winning), 6 (loss to opponent / litigation), 10 (success) and 11 (gain), then one will be able to win lawsuit',
       note="Read as any of 2, 6, 10, 11 (LR4): at the star level a planet carries at most three houses, so all four could never be met, and the article's own worked example declares the win with the 4th CSL hitting 10 and 11 but not 2 or 6."),
    _C('EZN-lagna_normal_health', 'EZN', 927, 'If the sublord of the ASC cusp be in the star of the occupant or owner of the house 1 or 11, the health is normal.'),
    _C('EZN-twelfth_foreign_travel', 'EZN', 945, 'If the cuspal sub lord of the 12th be the significator of 3 (away from home), 9 (abroad/long journey) or 12 (abroad/ new environment), the foreign travel is promised'),
    _C('EZN-sixth_new_tenant', 'EZN', 959, 'In cases of tenant if the cuspal sub lord of the 6t (tenant) signifies through the star lord 11 (fulfilment of desire) or 4 (own building or home) or 6 (tenant) or 2 (money or income), then native will get a new tenant.'),
    _C('EZN-sixth_cured', 'EZN', 962, 'If the sub lord of the 6t or 8th or 12thor 11 cusp be the significator (in the star of the occupant or owner) of 1 or 5 or 11, disease is cured or the native is saved from any danger'),
    _C('EZN-eighth_cured', 'EZN', 962, 'If the sub lord of the 6t or 8th or 12thor 11 cusp be the significator (in the star of the occupant or owner) of 1 or 5 or 11, disease is cured or the native is saved from any danger'),
    _C('EZN-twelfth_cured', 'EZN', 962, 'If the sub lord of the 6t or 8th or 12thor 11 cusp be the significator (in the star of the occupant or owner) of 1 or 5 or 11, disease is cured or the native is saved from any danger'),
    _C('EZN-eleventh_cured', 'EZN', 962, 'If the sub lord of the 6t or 8th or 12thor 11 cusp be the significator (in the star of the occupant or owner) of 1 or 5 or 11, disease is cured or the native is saved from any danger'),
    _C('EZN-fifth_education_abroad', 'EZN', 968, 'If the cuspal sub lord of the 5 (9th from 9th) be the significator of 9-12 and connected with 4- 9-11 education in abroad is promised'),
    _C('EZN-fourth_own_property', 'EZN', 971, 'If the cuspal sub lord of 4 (land/house/building) be the significator (in the star of occupant or owner) of 11 (gain, fulfilment of desire, 12 (investment), one will have his own land or building (immovable property)'),
    _C('EZN-sixth_chronic', 'EZN', 450, 'If the sub-lord of the 6th cusp or the lord of the star in which the 68 cusp sub-lord is posited happens to be ‘SATURN’',
       note="The quote's next words, 'or in any manner connected to SATURN', are not encoded (an undefined connection, ruling LR3)."),
    _C('EZN-eleventh_sixth_match', 'EZN', 979, 'if the cuspal sub lord of the 11th (success) and that of the 6th (defeat to the rival) be the sig- nificator of houses 1, 2, 3, 6, 10 or 11, the team under query can win the match'),
)}

__all__ = ["LATER_CITATIONS", "LaterCitation"]
