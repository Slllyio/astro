"""Doctrine Translation Engine — read classical shlokas through modern desh-kaal-paristhiti.

## Load-bearing epistemic stance

Classical Vedic shlokas (BPHS, Phaladeepika, Saravali, Jaimini Sutras) are
**axiomatic** for this framework. The sages applied multi-generational
empirical observation modern statistics cannot replicate. This engine's
job is NOT to validate doctrine but to **translate its manifestation**
across the desh-kaal-paristhiti shifts from ~3000 BCE Vedic India to
2026 globally.

## Meta-principle

The shloka encodes the **karmic signature** (invariant). The
desh-kaal-paristhiti provides the **substrate** (variable). Translation
= reading the signature through the current substrate, not validating
the signature against current outcomes.

| Domain | Ancient substrate | Modern substrate |
|---|---|---|
| Kinship | structural binary (married/widowed/sukhi-duhkhi) | trajectory arc (delayed/serial/internalized) |
| Career | king's-favor → varna-vocation | network-mesh → portfolio careers |
| Dharma | parampara (gurukula-shishya) | self-directed seeker (Substack/podcast/Vipassana) |
| Health | acute single-cause death | chronic multi-decade illness management |

## How the engine plugs in

For each ACTIVE yoga in a Reading + key bhava-planet configurations, the
engine emits a TranslationRecord with all 5 layers (shloka, ancient
manifestation, DKP shift, modern manifestation, invariant mechanism).
``reading_composer`` consumes these and adds a "Doctrine Translation"
section to the structured Reading.

Source: synthesized 2026-05-29 from 4 multi-disciplinary research agents
(kinship/marriage, career/wealth, dharma/spirituality, health/mortality)
grounded in classical Vedic + anthropology + economic history +
sociology of religion + medical anthropology.

## Module versioning

The translation records are v1 — 27 entries. Add to ``_TRANSLATIONS``
to extend; never edit in place without classical re-grounding. Each
record cites its classical anchor; modern references cite books/concepts
that map the equivalent manifestation today.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final, Iterable, Mapping


# ─── Domain tags ──────────────────────────────────────────────────────


class Domain:
    """Translation-record domain tags. Single source of truth."""
    KINSHIP = "kinship"
    CAREER_WEALTH = "career_wealth"
    DHARMA = "dharma"
    HEALTH = "health"


@dataclass(frozen=True)
class TranslationRecord:
    """One classical-to-modern translation record.

    Each record encodes the 5-layer translation an astrologer would
    apply when reading a chart in a modern context, with the shloka's
    karmic signature preserved as invariant.
    """
    key: str                          # yoga name or "bhava_X_planet_Y" key
    classification: str               # "yoga" | "bhava_placement"
    domain: str                       # Domain.KINSHIP, etc.
    shloka: str                       # one-line classical claim
    classical_references: tuple[str, ...]
    ancient_manifestation: str        # what the sage observed
    desh_shift: str                   # geographic/cultural changes
    kaal_shift: str                   # era/yuga changes
    paristhiti_shift: str             # lifestyle/circumstance changes
    modern_manifestation: str         # how it expresses today
    invariant_mechanism: str          # underlying karmic structure
    modern_references: tuple[str, ...]  # books/concepts mapping equivalence
    lagna_specific_notes: Mapping[int, str] = field(default_factory=dict)
    # Optional per-Lagna nuance — sparse coverage. The same yoga reads
    # differently when the Lagna confers Yogakaraka status on a planet
    # involved in the yoga (Cancer Mars, Taurus Saturn, etc.). Keys are
    # asc_sign 1..12; values are short modifier notes.


# ─── Meta-principles per domain ───────────────────────────────────────


DOMAIN_META_PRINCIPLES: Final[dict[str, str]] = {
    Domain.KINSHIP: (
        "Kali-Yuga Individuation Principle: As Rahu (individual ambition) "
        "gains cultural primacy over Jupiter (dharmic role-acceptance), "
        "kinship effects migrate from STRUCTURAL expression (marriage made/"
        "unmade, widowhood, property) to TRAJECTORY+PSYCHOLOGICAL expression "
        "(delayed marriage, serial relationships, internalized affect, "
        "fragmented commitment). Yogas predict the SHAPE of the arc, not "
        "binary state."
    ),
    Domain.CAREER_WEALTH: (
        "Rajya Decentralization Principle: 'Kingship' has decentralized "
        "from one king's favor to many distributed reputational and "
        "economic networks. Same yogas now produce multi-stream income, "
        "scaled public influence, portable reputation-capital. Read the "
        "karmic signature (what flows toward the native, through what "
        "mechanism, at what cadence), not the surface artifact (job title, "
        "asset class, status marker)."
    ),
    Domain.DHARMA: (
        "Decoupled Transmission Principle: Dharma has decoupled from "
        "inherited transmission. Same yogas that once produced guru-shishya "
        "parampara now produce self-directed seeker-paths via Substack, "
        "podcasts, Vipassana retreats rather than physical lineages. "
        "Pitr-rin migrates from ancestor-ritual to psychological "
        "lineage-work."
    ),
    Domain.HEALTH: (
        "Chronic-Trajectory Principle: Mortality has decoupled from acute "
        "single-cause death to chronic multi-decade illness-management. "
        "Yoga death-markers now indicate likely CAUSE of eventual death and "
        "SHAPE of decline curve, not age-of-death. Mental health has "
        "emerged as a major Bhava-1/4/6/12/Moon domain that ancient "
        "doctrine compressed into graha-baadha / unmada / dainyam."
    ),
}


# ─── Translation records ──────────────────────────────────────────────


_TRANSLATIONS: Final[tuple[TranslationRecord, ...]] = (

    # ╔════ KINSHIP / MARRIAGE ════════════════════════════════════════╗

    TranslationRecord(
        key="Mangal Dosha",
        lagna_specific_notes={
            4: ("Cancer Lagna: Mars is YOGAKARAKA here (rules 5H+10H), "
                "so Mangal Dosha softens into career-relationship-tension "
                "rather than dissolution. Native often marries someone "
                "from professional context."),
            5: ("Leo Lagna: Mars rules 4H+9H — both Kendra+Trikona — "
                "Yogakaraka softens Dosha; modern manifestation is "
                "career-driven late marriage rather than divorce risk."),
            1: ("Aries Lagna: Mars rules 1H+8H (Lagna lord and 8L). "
                "Mars-7H here is reading 7H from Lagna-lord's own house — "
                "intensifies the energy. Modern: dominant-partner attraction, "
                "high-conflict-but-passionate relationship patterns."),
            8: ("Scorpio Lagna: Mars is Lagna lord. Mars-7H is from one of "
                "its own signs into the partnership axis — magnifies the "
                "intensity. Modern: relationship as identity-battleground, "
                "frequent intense-then-broken cycles."),
        },
        classification="yoga",
        domain=Domain.KINSHIP,
        shloka="Mars in 1/2/4/7/8/12 from Lagna or Moon causes kalatra-pida "
               "(spouse-affliction) and vivaha-vighna (marriage obstacles).",
        classical_references=("Mansagari Ch.6.43-46", "Phaladeepika Ch.6.17",
                              "Saravali Ch.10.43", "BPHS Ch.80"),
        ancient_manifestation=(
            "Bride 14-16, groom 18-22 (Manusmriti 9.94). Parental "
            "arrangement with mandatory guna-milana. Mars-7H natives "
            "rejected at matching stage (visible vivaha-vighna), or "
            "if married suffered joint-family co-residential conflict "
            "(dowry disputes, in-law violence). Widowhood was civil "
            "death (Manusmriti 5.157-158)."
        ),
        desh_shift=(
            "Urban India arranged-marriage share fell from ~95% (1970) "
            "to ~62% (2018 IHDS). Diaspora intercultural marriage routine; "
            "guna-milana often ritual not veto."
        ),
        kaal_shift=(
            "Kali emphasis on Rahu (individuation, ambition) over "
            "Jupiter-dharma (sacramental commitment). Marriage reframed "
            "from samskara to contract."
        ),
        paristhiti_shift=(
            "Female mean marriage age India 22.1 (NFHS-5 2021); urban "
            "graduate women 27-30. Female labor force participation "
            "creates exit options. Divorce legalized + socially survivable. "
            "Widowhood no longer 'civil death'."
        ),
        modern_manifestation=(
            "Serial dating, commitment ambivalence, broken engagements "
            "(modern vivaha-vighna). Marriage delayed past 32; Mars-energy "
            "diverted to 10H career starves 7H. Two-career conflict, "
            "geographic separation. Divorce when Mars also afflicts 7L. "
            "Attraction to high-stakes app-dating chase. Mutual Mars Dosha "
            "cancellation statistically MORE common now."
        ),
        invariant_mechanism=(
            "Mars on partnership-axis injects friction, separation-pressure, "
            "action-orientation, heat (ushna). The PRESSURE is invariant; "
            "its outlet — agrarian honor-conflict, career-vs-relationship "
            "tension, app-dating volatility — is contextual. Reframe: "
            "Mars-7H prevents comfortable conventional partnership, not "
            "necessarily partnership altogether."
        ),
        modern_references=("Tambiah 1973 on Kanyadana economics",
                           "Trautmann 1981 on Dravidian kinship",
                           "NFHS-5 spousal violence data",
                           "IHDS 2018 arranged-marriage trend"),
    ),

    TranslationRecord(
        key="bhava_4_planet_Saturn",
        classification="bhava_placement",
        domain=Domain.KINSHIP,
        shloka="Saturn in 4H damages matr-sukha (mother-happiness) and "
               "produces grhakleshe (domestic friction) and emotional "
               "coldness.",
        classical_references=("BPHS Ch.24", "Phaladeepika Ch.13.30"),
        ancient_manifestation=(
            "Mother in joint family was co-resident primary caregiver "
            "until child entered gurukula (~8 years). Matr-viyoga meant "
            "literal mother's death (high maternal mortality), or distance "
            "through father's remarriage / co-wife conflict. Sukha meant "
            "the literal home — house, land, livestock."
        ),
        desh_shift=(
            "Maternal mortality dramatically reduced. Nuclear-family "
            "isolation of mother-child dyad. Daycare/nannies fragment "
            "caregiving."
        ),
        kaal_shift=(
            "Attachment theory, parenting-styles literature, intergenerational-"
            "trauma discourse NAME what doctrine compressed into "
            "matr-sukha-bhanga."
        ),
        paristhiti_shift=(
            "Geographic mobility separates adults from mothers (diaspora, "
            "urban migration). Home ownership delayed to 35+. Renting "
            "normalized."
        ),
        modern_manifestation=(
            "Emotionally distant or austere mother. Late home-ownership. "
            "Chronic dissatisfaction with domestic life. Depression linked "
            "to early home-environment. Immigrant/refugee patterns. "
            "Therapy-discourse allows the matr-sukha-bhanga to be "
            "NAMED and worked, modifying downstream 7H partner-selection."
        ),
        invariant_mechanism=(
            "4H is the interior-base — felt-sense of belonging, safety, "
            "rootedness. Saturn there cools, restricts, delays this "
            "felt-sense regardless of era. Vedic context = property/mother "
            "loss; modern context = attachment injury, housing instability, "
            "diasporic dislocation, ripple into 7H partner-selection where "
            "the native seeks repair."
        ),
        modern_references=("Bowlby attachment theory",
                           "Bowen family systems",
                           "Wuthnow on diasporic spirituality"),
    ),

    TranslationRecord(
        key="Chandra-Mangal",
        classification="yoga",
        domain=Domain.KINSHIP,
        shloka="Moon-Mars conjunction yields dhana-yoga (wealth) but "
               "emotional volatility and mata-virodha (mother-conflict).",
        classical_references=("BPHS Ch.36", "Phaladeepika Ch.6.17"),
        ancient_manifestation=(
            "Moon = mother (matr-karaka) and manas (mind). Mars-Moon in "
            "joint-family meant saas-bahu conflict, maternal aggression, "
            "or in male charts conflict with mother bleeding into wife-"
            "relationship. Dhana aspect manifested via Mars-drive applied "
            "to Moon's household economy."
        ),
        desh_shift=(
            "Nuclear families dominant urban India (~70%). Joint-family "
            "co-residence with in-laws now ~25% urban vs ~60% rural."
        ),
        kaal_shift=(
            "Mother-figure psychologized — Freudian/Jungian frames "
            "imported via Bollywood and therapy."
        ),
        paristhiti_shift=(
            "Therapy normalized in metros. Mother-attachment patterns "
            "named (mama's boy, helicopter mother)."
        ),
        modern_manifestation=(
            "Anxiety, anger-management issues, emotional reactivity. "
            "Conflict with mother surfacing as therapy-content rather "
            "than household-warfare. Dhana-yoga now expresses as "
            "risk-tolerant entrepreneurship (Mars-drive on Moon-public/"
            "needs). Indian founders often show this combination."
        ),
        invariant_mechanism=(
            "Mars on Moon heats the emotional body. Manas-ushna — mental "
            "heat — is invariant. Joint-family co-residence amplified its "
            "interpersonal expression; nuclear-family + therapy displaces "
            "it inward as anxiety/anger while preserving dhana drive."
        ),
        modern_references=("Murray Bowen family systems",
                           "Bollywood saas-bahu trope evolution"),
    ),

    # ╔════ CAREER / WEALTH ═══════════════════════════════════════════╗

    TranslationRecord(
        key="Gajakesari",
        classification="yoga",
        domain=Domain.CAREER_WEALTH,
        shloka="Jupiter in Kendra (1/4/7/10) from Moon yields fame (kirti), "
               "wealth, intelligence, royal favor, and enduring posthumous "
               "reputation.",
        classical_references=("BPHS Ch.36.36", "Phaladeepika Ch.6.40",
                              "Saravali Ch.40"),
        ancient_manifestation=(
            "Kirti meant fame in a 50-km radius — name carried through "
            "bardic recitation, temple inscriptions, royal grants "
            "(tamrapatra). Court-pandit / rajaguru / Chanakya archetype. "
            "Wealth = land-grants (agrahara), cattle (go-dhana), "
            "rice-tribute. Elephant (gaja) metaphor literal: only "
            "royalty/favored owned elephants."
        ),
        desh_shift=(
            "No king. Audience is global, asymmetric, mediated. 'Court' "
            "is LinkedIn, podcast circuits, conference keynotes, X, "
            "board seats."
        ),
        kaal_shift=(
            "Kali Mercury-Rahu amplification decouples reach from "
            "physical proximity. Single tweet hits 10M. Fame no longer "
            "rare; DURABLE fame is."
        ),
        paristhiti_shift=(
            "'Dear to the king' → dear to the algorithm, VC, institutional "
            "gatekeeper. Wealth is equity, IP, brand capital (Piketty's "
            "r>g world rewards capital-holders)."
        ),
        modern_manifestation=(
            "Public intellectuals with durable reach (Yuval Harari, "
            "Esther Perel, Ramit Sethi). Professor-turned-founder "
            "(Andrew Ng, Fei-Fei Li). Senior partner whose name IS the "
            "deal flow. Spiritual teacher with global following + "
            "ashram-as-foundation wealth (Sadhguru pattern). "
            "Author-investor-advisor portfolios."
        ),
        invariant_mechanism=(
            "Wisdom-amplified-by-popularity that converts to wealth "
            "without coercive labor. Native is GIVEN resources because "
            "their reputation reduces others' risk. Whether substrate is "
            "Mauryan court or Sequoia partnership, the mechanism — "
            "guru-recognition compounding into patronage — is identical."
        ),
        modern_references=("Piketty r>g capital dynamics",
                           "Kevin Kelly 1000 True Fans",
                           "Reid Hoffman network=net-worth"),
    ),

    TranslationRecord(
        key="bhava_10_planet_Saturn",
        lagna_specific_notes={
            2: ("Taurus Lagna: Saturn is YOGAKARAKA (rules 9H+10H). "
                "Saturn-10H here is the karaka-in-its-own-bhava — "
                "exceptionally favorable. Modern: long-arc institutional "
                "leadership, central bank governor / chief justice / "
                "Tata-Sons-chairman type trajectories."),
            7: ("Libra Lagna: Saturn is YOGAKARAKA (rules 4H+5H — Kendra+"
                "Trikona). Saturn-10H here gains immense karmic weight. "
                "Modern: high-stakes professional roles requiring quiet "
                "competence — surgeon, judge, infrastructure architect."),
        },
        classification="bhava_placement",
        domain=Domain.CAREER_WEALTH,
        shloka="Saturn in 10H in own/exaltation produces leader of men "
               "and great works, but the rise is preceded by long labor "
               "(shrama) and obstacles in youth.",
        classical_references=("Phaladeepika 6.30", "Saravali 41"),
        ancient_manifestation=(
            "Kshatriya: long frontier service before promotion to general. "
            "Vaishya: decades of caravan trade before becoming sreshthin. "
            "Shudra: lifetime artisan-mastery (silpin). Mauryan "
            "administrative system rewarded long tenure with rank. "
            "Late-bloom was signature of legitimate earned authority."
        ),
        desh_shift=(
            "Industrial era invented career ladder (1880-1980). Knowledge "
            "era replacing it with portfolio careers (Charles Handy). "
            "Indian IT services (TCS, Infosys, Wipro) is archetypal "
            "Saturnine 10H structure."
        ),
        kaal_shift=(
            "Kali impatience makes Saturnine slow-mastery culturally "
            "undervalued but ECONOMICALLY REWARDED. 40-year-old senior "
            "engineer out-earns 25-year-old influencer over a lifetime."
        ),
        paristhiti_shift=(
            "10,000-hour rule (Ericsson). Cal Newport's So Good They "
            "Can't Ignore You. Rise of 'operator' archetype in VC. All "
            "describe Saturn-10H in modern language."
        ),
        modern_manifestation=(
            "IT services lifer becoming Delivery Head at 45. COO / Chief "
            "of Staff archetype (the one who runs the actual machine). "
            "Civil servant reaching Secretary rank at 55. PhD → Professor "
            "→ Department Head. Manufacturing/supply-chain executive "
            "(Tim Cook pre-CEO). Infrastructure entrepreneur (Adani-style). "
            "Risk: HR/middle-management churn, layoffs at 50."
        ),
        invariant_mechanism=(
            "Authority earned through time, attrition, structural mastery. "
            "Native carries weight because they survived what others quit. "
            "Whether structure is Mauryan revenue district or SAP rollout, "
            "the karmic signature — TIME ITSELF becomes the native's "
            "competitive moat — is unchanged."
        ),
        modern_references=("Ericsson 10000-hour rule",
                           "Cal Newport So Good They Can't Ignore You",
                           "Charles Handy portfolio careers"),
    ),

    TranslationRecord(
        key="Lakshmi",
        classification="yoga",
        domain=Domain.CAREER_WEALTH,
        shloka="9L dignified in Kendra/Trikona + Venus or Jupiter in "
               "Kendra/Trikona = Lakshmi Yoga. Native enjoys wealth, sons, "
               "comforts, vehicles, fame, royal honor.",
        classical_references=("BPHS Ch.36", "Phaladeepika Ch.6.28"),
        ancient_manifestation=(
            "Wealth was visible, immobile, lineage-bound: ancestral land, "
            "multiple wives + sons (dynastic compounding), elephants and "
            "horses, public honor by king (birudavali — titles), explicit "
            "divine favor via temple endowments returning to household."
        ),
        desh_shift=(
            "Wealth has dematerialized. Piketty: top 1% wealth in "
            "2020+ economies is overwhelmingly capital-asset (equity, "
            "real estate, IP) not income."
        ),
        kaal_shift=(
            "Bhagya now expresses as cap-table luck — being early at the "
            "right company, born into right zip code (Raj Chetty mobility "
            "data), inheriting equity not land."
        ),
        paristhiti_shift=(
            "'Sons' → durable beneficiaries (kids, trusts, foundations, "
            "employee equity pools). Mechanism is same: one's prosperity "
            "becomes vehicle for others' prosperity, compounds back."
        ),
        modern_manifestation=(
            "Early-employee equity at unicorn → generational wealth "
            "(Google #50 pattern). Inherited family business compounding "
            "across 2-3 generations (Marwari/Chettiar archetype). Real "
            "estate portfolio across cities. Brand-as-asset: founders "
            "whose name is collateral (Tata trust). Philanthropic "
            "foundations conferring durable status (Gates, Premji)."
        ),
        invariant_mechanism=(
            "Grace-flavored accumulation — wealth that arrives partly "
            "through effort, partly through unearned-but-deserved fortune, "
            "compounding across time and persons. Native is a NODE "
            "through which prosperity flows and multiplies."
        ),
        modern_references=("Piketty Capital in the 21st Century",
                           "Raj Chetty mobility data",
                           "Tirthankar Roy India economic history"),
    ),

    TranslationRecord(
        key="Vipareeta Raja",
        classification="yoga",
        domain=Domain.CAREER_WEALTH,
        shloka="Lords of 6/8/12 mutually placed in 6/8/12 from Lagna, "
               "without benefic association, give kingship through "
               "REVERSAL — rising through enemies' fall, gaining through "
               "others' losses, prospering in adversity.",
        classical_references=("BPHS Ch.36",),
        ancient_manifestation=(
            "Minister who survives king's purge and becomes regent. "
            "Trader whose competitors die in famine. Frontier general "
            "promoted because senior died in battle. Temple administrator "
            "inheriting role after scandal removes predecessor. Karma of "
            "navigating dushtana environments and emerging stronger."
        ),
        desh_shift=(
            "Modern dushtana environments: litigation, bankruptcy/"
            "restructuring, cybersecurity, oncology, addiction-treatment, "
            "insurance, geopolitical-risk consulting, distressed-asset "
            "investing, hedge funds shorting failures."
        ),
        kaal_shift=(
            "Capitalism INDUSTRIALIZED dushtana-monetization. Entire "
            "industries exist to profit from others' 6/8/12."
        ),
        paristhiti_shift=(
            "Taleb's antifragile concept is the modern articulation of "
            "Vipareeta Raja — systems and people that GAIN from disorder."
        ),
        modern_manifestation=(
            "Restructuring lawyer / distressed-debt fund manager "
            "(Howard Marks). Bankruptcy trustee, forensic accountant, "
            "crisis-PR firm. Short-seller / volatility trader in market "
            "crashes. Litigation finance. Cybersecurity founder growing "
            "with breach frequency. Oncologist, addiction therapist, ICU "
            "specialist — thriving through others' suffering while "
            "genuinely healing. Second-place becomes first after CEO "
            "fired."
        ),
        invariant_mechanism=(
            "Prosperity through navigation of decay-environments others "
            "cannot tolerate. Native has karmic capacity to operate in "
            "6/8/12 territory and convert it to rajya. Mechanism — gain "
            "emerges from well-managed encounter with loss — is invariant."
        ),
        modern_references=("Taleb Antifragile",
                           "Howard Marks distressed-debt thesis"),
    ),

    # ╔════ DHARMA / SPIRITUALITY ═════════════════════════════════════╗

    TranslationRecord(
        key="bhava_9_planet_Jupiter",
        classification="bhava_placement",
        domain=Domain.DHARMA,
        shloka="Jupiter in 9H exalted = native learned in shastras, "
               "dharma-paro, possibly a king. Param Bhagya — fortune "
               "through past-life merit, dharma-acharya destiny.",
        classical_references=("BPHS Ch.34", "Phaladeepika 6.34",
                              "Saravali 35.51"),
        ancient_manifestation=(
            "Native received upanayana into a parampara, studied Vedas "
            "in gurukula under brahmana acharya, either became one or "
            "remained householder-yajamana funding yajnas. Father was "
            "Vedic scholar or kingly patron of dharma. Fortune (bhagya) "
            "accrued through poorva-punya, manifesting as access to "
            "sacred knowledge. Pilgrimage to Kashi/Prayag was operational."
        ),
        desh_shift=(
            "Gurukula extinct; replaced by universities, MOOCs, podcasts. "
            "Parampara now horizontal (peer networks, citation graphs) "
            "rather than vertical (guru→shishya)."
        ),
        kaal_shift=(
            "Kali's Rahu-amplification means teaching is mass-broadcast — "
            "Sadhguru, Jordan Peterson, Andrew Huberman, Naval Ravikant "
            "occupy slot once held by village acharyas. Knowledge "
            "transmission disintermediated."
        ),
        paristhiti_shift=(
            "Hindu identity politicized rather than lived. Secularization "
            "(Berger 1967) means dharma is one option on marketplace of "
            "worldviews."
        ),
        modern_manifestation=(
            "PhD-holder, university professor, public intellectual, "
            "well-respected podcaster, MBA-with-mission, lifelong-learner. "
            "Yuval Harari (Jupiter-9H as historian-philosopher), Brené "
            "Brown (academic→popular teacher). 9H father may be secular "
            "mentor (PhD advisor, founding CEO) rather than biological "
            "pitr."
        ),
        invariant_mechanism=(
            "Jupiter expands the house. 9H is house of EXPANSION OF "
            "MEANING-FRAMEWORKS. Exalted Jupiter there always produces "
            "native whose life-purpose is TRANSMISSION OF MEANING TO "
            "OTHERS — whether the transmission flows through a Vedic "
            "recitation hall, TED stage, or Substack newsletter is "
            "desh-kaal cosmetic."
        ),
        modern_references=("Berger Sacred Canopy",
                           "Wuthnow After Heaven dweller→seeker"),
    ),

    TranslationRecord(
        key="bhava_12_planet_Ketu",
        classification="bhava_placement",
        domain=Domain.DHARMA,
        shloka="Ketu in 12H produces moksha-labha (liberation-gain), "
               "vairagya (dispassion), videsha-vasa (foreign residence).",
        classical_references=("BPHS Ch.27.46", "Jaimini Sutra 1.2.71-76",
                              "Phaladeepika 19.18"),
        ancient_manifestation=(
            "Native took sannyasa often in third or fourth ashrama, "
            "withdrew to forest hermitage, wandered as parivrajaka, or "
            "joined monastic order (Buddhist sangha, later Advaita matha). "
            "'Foreign' (videsha) meant leaving janmabhumi — karmically "
            "heavy. Kalapani (crossing seas) literally cost caste-status. "
            "Native was structurally peripheral to social reproduction "
            "but central to spiritual production."
        ),
        desh_shift=(
            "'Foreign' now positive — H-1B, OPT, immigrant-success "
            "narrative. NRIs valorized."
        ),
        kaal_shift=(
            "Eliade Sacred and Profane — modern subject reconstructs "
            "sacred from fragments: Vipassana, ayahuasca, Goenka 10-day "
            "retreats, MDMA-assisted therapy, psilocybin trials. "
            "Psychedelic renaissance is the structural equivalent of "
            "forest-sadhana for post-secular seeker."
        ),
        paristhiti_shift=(
            "Wuthnow (After Heaven 1998): dweller spirituality displaced "
            "by seeker. Bellah's Sheila-ism — privatized self-authored "
            "religion — is the dominant 12H-Ketu phenotype."
        ),
        modern_manifestation=(
            "Digital nomad in Bali/Tulum. Vipassana-circuit attendee. "
            "Psychedelic explorer. Ashrama-tourist. 'Spiritual but not "
            "religious'. Transpersonal-psychology client. Goenka-meditator "
            "who codes for SaaS between retreats. Modal biographical: "
            "leaving natal religion in young-adulthood then reconstructing "
            "personal sadhana from multiple traditions."
        ),
        invariant_mechanism=(
            "Ketu severs attachment to matters of its house. 12H is house "
            "of dissolution-of-self-into-larger-totality. The conjunction "
            "always produces a native whose life-arc bends toward "
            "DISSOLUTION OF PERSONAL IDENTITY INTO TRANSPERSONAL SPACE — "
            "whether that space is named Brahman, Nirvana, the Unitive "
            "State, the Flow State, or 'ego death on mushrooms'."
        ),
        modern_references=("Eliade Sacred and Profane",
                           "Wuthnow After Heaven",
                           "Bellah Habits of the Heart"),
    ),

    TranslationRecord(
        key="Pitra Dosha",
        classification="yoga",
        domain=Domain.DHARMA,
        shloka="Sun afflicted by Rahu/Saturn (esp. in 9H) or 9L in 6/8/12 "
               "= pitra-rin (unpaid debt to ancestors). Classical remedy: "
               "tarpana at Gaya, Tripindi Shraddha, Pitr Paksha rites.",
        classical_references=("Brihat Parashara Dosha Adhyaya",
                              "Tamil Siddha + Telugu Jyotisha"),
        ancient_manifestation=(
            "Native experienced interrupted lineage — father died early, "
            "family lost ancestral land/ritual obligations, shraddha rites "
            "went unperformed, native structurally barred from full "
            "lineage-dharma participation. In a culture organized around "
            "vamsha and pitr-rin, this was catastrophic karmic position "
            "requiring expiation at Gaya."
        ),
        desh_shift=(
            "Joint families fragmented into nuclear/single-parent globally. "
            "Ancestor-rites performed by <5% of urban Hindus."
        ),
        kaal_shift=(
            "Post-Freudian psychology reframed lineage-trouble as "
            "intergenerational trauma. Bowen family-systems theory; "
            "Wolynn (It Didn't Start With You 2016) on epigenetic "
            "transmission."
        ),
        paristhiti_shift=(
            "'Father wound' (Bly Iron John 1990) is secular vocabulary. "
            "Men's-work, IFS therapy, Hellinger family-constellations are "
            "operational remedies."
        ),
        modern_manifestation=(
            "Unresolved relationship with biological father (absent, "
            "abusive, addicted, emotionally-unavailable). Inability to "
            "access 'mature masculine' (Moore & Gillette). Reluctance to "
            "commit / take responsibility / claim authority. Repeated "
            "self-sabotage at threshold of becoming father-figure oneself. "
            "Therapy modalities: family-constellation work, IFS, men's "
            "circles, depth-psychology."
        ),
        invariant_mechanism=(
            "Rahu's confusion-of-source obscures Sun's authority-"
            "transmission function. Native cannot receive adhikara "
            "(legitimate authority) cleanly through paternal line. "
            "Whether remedy is Tripindi Shraddha at Gaya or six-month "
            "immersion in Bowen family-systems therapy, the karmic WORK "
            "is identical: make ancestor-line conscious, conduct "
            "unfinished psychic business, reclaim right to wield "
            "authority in own life."
        ),
        modern_references=("Wolynn It Didn't Start With You",
                           "Bly Iron John",
                           "Moore & Gillette King Warrior Magician Lover",
                           "Yehuda Holocaust transgenerational cortisol"),
    ),

    # ╔════ HEALTH / MORTALITY ════════════════════════════════════════╗

    TranslationRecord(
        key="bhava_8_planet_Saturn",
        classification="bhava_placement",
        domain=Domain.HEALTH,
        shloka="Saturn as ayur-karaka in 8H well-placed indicates long "
               "life (Purna-ayu 70-100). Afflicted Saturn-8 indicates "
               "chronic wasting illness or Alpa-ayu (<32).",
        classical_references=("BPHS Ch.40 Ayur-Daya",
                              "Phaladeepika 8.1 ayu-bands"),
        ancient_manifestation=(
            "Sage faced population where ~50% children died before age 5, "
            "adult life expectancy conditional on reaching 20 was ~50-55. "
            "Saturn-8 well-placed predicted reaching Purna-ayu band — "
            "non-trivial achievement requiring escape from malaria, "
            "dysentery, childbirth fever, smallpox, trauma. Literal "
            "mortality prediction; Ayurvedic intervention could marginally "
            "extend but not bend the curve."
        ),
        desh_shift=(
            "Global life expectancy 73.4 (UN WPP 2024); India 70.1. "
            "Antibiotics (1940s), vaccines, sanitation, ICU eliminated "
            "most acute mortality below age 60. Reaching 70 now default."
        ),
        kaal_shift=(
            "Kali Yuga shift from infectious to chronic-degenerative-"
            "mental illness. New doshic balance (sedentary, processed "
            "food, screen-strain, sleep-debt)."
        ),
        paristhiti_shift=(
            "Saturn's domain stretched. The 'slow chronic wasting' Saturn "
            "once produced as TB-death at 45 now produces type-2 diabetes "
            "diagnosed at 45 and managed until 85."
        ),
        modern_manifestation=(
            "Saturn-8 well-placed → reaches 85-95, but last 15 years are "
            "chronic-disease-management years (diabetes on metformin, "
            "hypertension on amlodipine, mild CKD, osteoarthritis). "
            "Saturn-8 afflicted → premature aging markers, early-onset "
            "chronic disease (diabetes at 35), telomere-shortening profile, "
            "but rarely death before 60 in OECD contexts. Marker now "
            "indexes TRAJECTORY SHAPE (steep vs gradual decline curve) "
            "not terminal age."
        ),
        invariant_mechanism=(
            "Saturn governs time-rate of bodily decay — entropy gradient "
            "of physical vehicle. Whether gradient terminates at 45 "
            "(ancient) or 85 (modern), Saturn's signature reads steepness "
            "of decline curve and native's relationship to embodied "
            "finitude."
        ),
        modern_references=("UN WPP 2024 life expectancy",
                           "Caldwell Demographic Transition Theory",
                           "WHO Global Burden of Disease 2021"),
    ),

    TranslationRecord(
        key="bhava_1_planet_Rahu",
        classification="bhava_placement",
        domain=Domain.HEALTH,
        shloka="Rahu in 1H brings roga-bahulyam (disease multiplicity), "
               "vish-prayogah (poisoning), graha-baadha (planetary "
               "torment).",
        classical_references=("BPHS Ch.40",
                              "Phaladeepika echoes 1H Rahu"),
        ancient_manifestation=(
            "Mysterious illness in 3000 BCE - 500 CE: parasitic infestation "
            "(helminths, leishmaniasis), heavy-metal poisoning (mercury/"
            "arsenic in tantric preparations gone wrong), envenomation, "
            "graha-baadha (illness attributable to non-human agents). "
            "Rahu the chaya-graha governed categorically UNSEEN causation "
            "— what we now call invisible-pathogen disease."
        ),
        desh_shift=(
            "Acute infectious 'mysterious' illness largely demystified "
            "(microbe theory 1860s; immunology 1900s)."
        ),
        kaal_shift=(
            "New category of illness-without-clear-cause emerged: "
            "autoimmune (lupus, Hashimoto's, MS, Crohn's — incidence up "
            "3-9% per year per Bach NEJM 2002 hygiene hypothesis), "
            "environmental sensitivities, chronic fatigue (ME/CFS, "
            "long-COVID, fibromyalgia), addiction-as-disease."
        ),
        paristhiti_shift=(
            "Modern 'poisoning' = ultraprocessed food, microplastic load, "
            "endocrine disruptors, dopamine dysregulation. Kleinman's "
            "Illness Narratives 1988 frames these as canonical modern "
            "'contested illnesses'."
        ),
        modern_manifestation=(
            "Autoimmune disorder (immune system attacking own tissues — "
            "Rahu signature of self-mistaken-for-other). Allergies and "
            "intolerances multiplying. Environmental sensitivity. "
            "Long-COVID, post-vaccine syndromes, chronic-fatigue patterns. "
            "'I've seen 12 doctors and nobody knows what's wrong.' "
            "Substance-use disorder (Rahu = the substance one cannot stop "
            "ingesting). Screen-addiction syndromes."
        ),
        invariant_mechanism=(
            "Rahu governs boundary-confusion of self/other at the bodily "
            "level — what crosses into the body and is misidentified as "
            "self (autoimmune), or what the body craves but cannot "
            "integrate (addiction). Substrate of confusion changes; "
            "karmic structure persists."
        ),
        modern_references=("Bach NEJM 2002 hygiene hypothesis",
                           "Kleinman Illness Narratives",
                           "Foucault medicalization"),
    ),

    TranslationRecord(
        key="moon_afflicted_by_rahu_saturn",
        classification="bhava_placement",
        domain=Domain.HEALTH,
        shloka="Moon-Rahu conjunction produces unmada (frenzy/mania); "
               "Moon-Saturn produces dainyam (melancholy, dejection, "
               "poverty-of-spirit). Vish-yoga indicates mental affliction, "
               "joylessness.",
        classical_references=("BPHS Ch.7 + Ch.40",
                              "Saravali on Vish-yoga"),
        ancient_manifestation=(
            "Classical lexicon had unmada (frenzy/mania), apasmara "
            "(epilepsy/seizure), vish-vega (poison-velocity, agitated "
            "states), dainyam (melancholic dejection) — but LACKED "
            "differential vocabulary of modern psychiatry. Severe mental "
            "illness framed as graha-baadha, treated with mantras, "
            "Atharvanic ritual, herbal preparations (Brahmi, Shankhapushpi, "
            "Jatamansi). Mild-moderate depression/anxiety were INVISIBLE "
            "CATEGORIES — language did not segment them. People were "
            "'weak', 'unfortunate', 'joyless' — not 'depressed'."
        ),
        desh_shift=(
            "DSM/ICD apparatus (post-1952) created the language of mood "
            "disorder. WHO estimates 280M people globally with depression "
            "(4%), anxiety affects 301M."
        ),
        kaal_shift=(
            "Foucault Madness and Civilization (1961) and Kleinman "
            "Rethinking Psychiatry (1988) document how psychiatric "
            "categories CREATE visibility of conditions that always "
            "existed but lacked nomenclature. Kali-Yuga manifestation of "
            "Moon-affliction has expanded into THE DOMINANT ILLNESS "
            "SIGNATURE of the 21st century."
        ),
        paristhiti_shift=(
            "Therapy normalized in metros. SSRIs widely prescribed. "
            "Mental-health-awareness influencer class. Mindfulness apps."
        ),
        modern_manifestation=(
            "Moon-Rahu → bipolar spectrum, anxiety, panic, OCD, "
            "dissociative episodes, substance-use comorbidity, eating "
            "disorders (Rahu's foreign-ingestion + Moon's nourishment "
            "domain). Moon-Saturn → MDD, dysthymia/PDD, SAD, postpartum, "
            "attachment disorders, 'joyless competence' (high-functioning "
            "but anhedonic). Moon-Ketu → dissociation, derealization, "
            "sleep paralysis, vairagya-shading-into-depression spectrum. "
            "Therapy, SSRIs, contemplative practice are required "
            "interventions."
        ),
        invariant_mechanism=(
            "Moon = manas (mind/feeling-substrate). Affliction to Moon = "
            "turbulence in feeling-substrate. Whether labeled unmada or "
            "bipolar-I, the karmic signature is the same: the native's "
            "relationship to their own emotional weather is structurally "
            "unstable."
        ),
        modern_references=("Foucault Madness and Civilization",
                           "Kleinman Rethinking Psychiatry",
                           "WHO mental health prevalence data"),
    ),

    TranslationRecord(
        key="bhava_8_planet_Mars",
        classification="bhava_placement",
        domain=Domain.HEALTH,
        shloka="Mars in 8H brings death by weapon, fire, water (shastra-"
               "ghata-agni-jalair).",
        classical_references=("BPHS Ch.40 Arishta-yogas",
                              "Saravali Ch.36"),
        ancient_manifestation=(
            "Surgery without anesthesia (introduced 1846 CE) meant "
            "Sushruta's procedures carried 30-50% mortality from shock, "
            "sepsis, hemorrhage. War wounds, snake-bite, fire, drowning "
            "were primary causes of male mortality in 15-40 cohort. Mars-8 "
            "was LITERAL CAUSE-OF-DEATH PREDICTOR: the native would die "
            "by blade, by fever, by bleeding."
        ),
        desh_shift=(
            "Trauma medicine, blood banking (1914), aseptic surgery (Lister "
            "1867), anesthesia, emergency response transformed acute "
            "trauma from death-event to SURVIVED medical episode."
        ),
        kaal_shift=(
            "WHO injury mortality fell from ~15% of total deaths in 1900 "
            "to ~8% globally; in OECD nations ~4%."
        ),
        paristhiti_shift=(
            "Most surgeries are elective and survived. Anesthesia routine."
        ),
        modern_manifestation=(
            "Mars-8 native now presents as multiple surgeries in a "
            "lifetime (appendectomy, ACL repair, C-section, cardiac stent), "
            "accident-prone (motorcycle, sports injury), frequent ER "
            "visits, anesthesia exposures, blood transfusions — but these "
            "are SURVIVED chapters, not terminal events. Often develops "
            "somatic relationship with hospitals — comfortable with "
            "medical procedures, perhaps working in EMS, surgery, military. "
            "Mars-8 death-signature migrated to cause-of-eventual-death "
            "(more likely cardiovascular or trauma than cancer/dementia) "
            "rather than age-of-death."
        ),
        invariant_mechanism=(
            "Mars in the randhra (hidden/transformative) house governs "
            "native's karmic relationship to BODILY VIOLATION — incisions "
            "into the flesh, blood crossing the body-boundary. Whether "
            "violation is fatal (ancient) or therapeutic (modern), the "
            "lifetime COUNT and INTENSITY of bodily-boundary-crossings is "
            "what Mars-8 indexes."
        ),
        modern_references=("Lister aseptic surgery",
                           "WHO Global Burden of Disease 2021 injury data"),
    ),

    TranslationRecord(
        key="Sarpa Dosha",
        classification="yoga",
        domain=Domain.HEALTH,
        shloka="Rahu/Ketu in 1/5/9 indicates karmic burden along the "
               "Lagna-Trikona axis — self, intellect, dharma.",
        classical_references=("Nadi tradition synthesis",
                              "Sanjay Rath expansion"),
        ancient_manifestation=(
            "Curse of serpent-deities, hereditary illness (the 'serpent' "
            "as ancestral karma coiled around the lineage), required "
            "snake-puja remedy at Naga-shrines. The 1/5/9 trikona "
            "afflicted by shadow-planets meant the family's dharmic "
            "continuity itself was karmically blocked — failed conceptions, "
            "intellect-blocks, dharma-rejection across generations."
        ),
        desh_shift=(
            "Naga-puja and snake-shrines marginal in urban contexts. "
            "Hereditary-illness mapping moved to genetic counseling, "
            "family-medical-history tracking."
        ),
        kaal_shift=(
            "Inherited-trauma psychology displaces the literal serpent-"
            "curse framing. Family-systems therapy normalizes the "
            "concept of inherited patterns."
        ),
        paristhiti_shift=(
            "Generational therapy work, MMPI-style personality patterns, "
            "genealogical narrative therapy."
        ),
        modern_manifestation=(
            "Inherited family trauma patterns. Generational psychological "
            "themes (depression-cluster, addiction-cluster, identity-"
            "uncertainty cluster across siblings/cousins). Genealogical "
            "karma manifest as repeating-relationship-failures, "
            "career-self-sabotage, intellect-blocks (test anxiety, "
            "learning disabilities). Some natives experience kundalini-"
            "awakening phenomena or sleep paralysis interpreting as "
            "Sarpa awakening."
        ),
        invariant_mechanism=(
            "Shadow-planets on the Trikona axis bind the soul's dharmic "
            "continuity to ancestral unfinished business. Whether the "
            "remedy is Naga-puja at Mannarsala or 5 years of family-"
            "constellation work, the karmic move — RELEASING THE "
            "ANCESTRAL COIL FROM THE DHARMIC AXIS — is identical."
        ),
        modern_references=("Bowen family systems",
                           "Mark Wolynn It Didn't Start With You",
                           "Hellinger Familienstellen"),
    ),

    # ─── Phase 8.6 additions (post-v1 expansion) ──────────────────────

    TranslationRecord(
        key="Venus_afflicted_combust_or_dusthana",
        classification="bhava_placement",
        domain=Domain.KINSHIP,
        shloka=("Venus combust by Sun, in debilitation (Virgo), or in "
                "6/8/12 from Lagna damages bhogya (enjoyment) and "
                "dampatya-sukha (marital happiness)."),
        classical_references=("BPHS Ch.32 Karakadhyaya",
                              "Phaladeepika Ch.15.16"),
        ancient_manifestation=(
            "Venus signified the wife as bhoga-patni — sensual-domestic "
            "partner whose role was procreation, ritual partnership "
            "(saha-dharmini), household management. Afflicted Venus "
            "manifested as: barren wife (religious crisis under Putra-"
            "dharma), wife of low kula-shila, repeated wife-deaths "
            "(serial remarriage for Brahmin men), sensory deprivation "
            "(Venus = arts, perfume, beauty — denied through poverty)."
        ),
        desh_shift=(
            "Wife no longer principally bhoga-patni; she is co-earner, "
            "co-decision-maker, often primary breadwinner in urban India "
            "(Census 2011 trend continuing)."
        ),
        kaal_shift=(
            "Beauty/sensuality (Venus) has industrialized — cosmetics, "
            "fashion, OTT entertainment, pornography make bhoga "
            "abundantly accessible OUTSIDE marriage, decoupling Venus "
            "from spouse-karaka in lived experience."
        ),
        paristhiti_shift=(
            "Sensuality without marriage (cohabitation, hookup culture), "
            "marriage without sensuality (~15% urban Indian marriages "
            "sexless by 5th year per ICMR), IVF/surrogacy decouple "
            "procreation from sexuality."
        ),
        modern_manifestation=(
            "Native may have abundant romantic/aesthetic life but no "
            "stable partnership (bhoga without kalatra). Marriage that "
            "lacks sensual-aesthetic life — companionate cohabitation, "
            "sexless after children. Affairs (Venus seeks expression "
            "elsewhere when starved at home). Aesthetic-career profile "
            "(designer, artist, hospitality) conflicting with marital "
            "stability. Modern vandhyatva manifests as voluntary "
            "childlessness (DINK), IVF struggles, postponed fertility."
        ),
        invariant_mechanism=(
            "Venus is the capacity for harmonious union and sensual "
            "exchange. Affliction degrades that capacity. Whether the "
            "manifestation is Vedic barren-wife or modern sexless-DINK-"
            "marriage is contextual envelope; the inner deficit — "
            "rasa-bhanga, a break in the flow of harmonious exchange — "
            "is invariant."
        ),
        modern_references=("ICMR sexless-marriage studies",
                           "Census 2011 female workforce participation",
                           "Esther Perel Mating in Captivity"),
    ),

    TranslationRecord(
        key="Mars-Venus association",
        classification="yoga",
        domain=Domain.KINSHIP,
        shloka=("Mars-Venus association produces paradara-rati (attraction "
                "to others' spouses), gupta-kama (clandestine desire), "
                "skill in kama-shastra. Malefic-aspected escalates to "
                "vyabhichara (adultery)."),
        classical_references=("Saravali Ch.34", "Phaladeepika Ch.13.6",
                              "Jataka Parijata Ch.7"),
        ancient_manifestation=(
            "Patrilineal kinship (Trautmann 1981) made female chastity "
            "lineage-purity. Mars-Venus male natives could engage "
            "courtesans (ganika) without dharmic transgression; female "
            "natives were severely controlled — Mars-Venus typically "
            "expressed as kulata (woman of 'loose conduct') and rapid "
            "social ruin. Doctrine was framed asymmetrically because the "
            "paristhiti was asymmetric."
        ),
        desh_shift=(
            "Female sexuality no longer monopolized by lineage-honor in "
            "urban contexts. Sex-work decriminalization debates ongoing."
        ),
        kaal_shift=(
            "Public discourse of consent, choice, agency. Dating apps "
            "(Tinder/Bumble/Hinge India 50M+ users 2024) institutionalize "
            "Mars-Venus pattern — sexual selection at scale, "
            "low-commitment encounters norm for ages 22-30."
        ),
        paristhiti_shift=(
            "Serial monogamy as norm. Polyamory in urban-progressive "
            "circles. Sexual confidence as cultural ideal."
        ),
        modern_manifestation=(
            "Serial monogamy, overlapping relationships, situationships. "
            "Sexual openness, polyamory in progressive circles. Career "
            "in fashion, film, hospitality, OTT — Mars-Venus aesthetic-"
            "passion fusion. Affairs within marriage (Indian extramarital-"
            "dating apps like Gleeden report rapid growth). For women: "
            "Mars-Venus now expresses as AGENCY (chosen partners, sexual "
            "confidence) rather than ruination — paristhiti changed "
            "faster than doctrine. Risk: drama-addiction in relationships, "
            "attraction to unavailable partners, intensity-mistaken-for-love."
        ),
        invariant_mechanism=(
            "Mars (desire-pursuit) + Venus (object-of-desire) on the same "
            "axis intensifies kama and reduces patience for slow-cultivated "
            "prema. The INTENSITY and SHORT-FUSE are invariant; whether "
            "they ruin a Vedic woman's reputation or fuel a Bumble account "
            "is contextual."
        ),
        modern_references=("Trautmann 1981 Dravidian kinship",
                           "Tinder/Bumble India 2024 user data",
                           "Esther Perel State of Affairs"),
    ),

    TranslationRecord(
        key="strong_10L",
        classification="bhava_placement",
        domain=Domain.CAREER_WEALTH,
        shloka=("Lord of 10H in dignity in Kendra/Trikona, aspected by "
                "benefics, gives rajya — sovereignty, fame, command over "
                "others, conduct of great works (maha-karma)."),
        classical_references=("BPHS Ch.26 Bhava-phala",
                              "Phaladeepika Ch.13"),
        ancient_manifestation=(
            "Rajya literally meant kingship or feudatory rank — samanta, "
            "mahamatya, senapati, royal treasurer, chief temple "
            "administrator (sthanika). For Brahmanas it meant kulapati "
            "of a major gurukula. For Vaishyas it meant sreshthin (head "
            "of merchant guild — the srenis system documented in "
            "Arthasastra). Status was monotonic, lifelong, hereditary-"
            "leaning, visible (palanquin, retinue, royal seal)."
        ),
        desh_shift=(
            "Indian economy moved agrarian → colonial-extractive → "
            "Nehruvian-industrial → 1991 liberalization → IT services → "
            "platform/creator. Status unbundled from birth across "
            "1850-2000 (Tirthankar Roy)."
        ),
        kaal_shift=(
            "Authority is now plural and contestable. No single throne; "
            "many thrones (CEO, MP, viral creator, top surgeon, fund "
            "manager). Holland's RIASEC career typology and Schein's "
            "career anchors show modern careers as SELF-CONSTRUCTED "
            "portfolios."
        ),
        paristhiti_shift=(
            "Strong 10L now expresses through whichever modality the "
            "native's other karakas indicate."
        ),
        modern_manifestation=(
            "Sun-flavored 10L → C-suite, founder-CEO, elected office, "
            "military rank. Moon-flavored → hospitality, FMCG, public-"
            "facing healthcare leadership. Mars → surgery, defense "
            "contracting, real-estate development, sports. Mercury → "
            "consulting partner, tech executive, top journalist, trader. "
            "Jupiter → judge, professor-emeritus, central-bank governor, "
            "religious head. Venus → fashion/luxury/film executive, "
            "diplomatic post. Saturn → infrastructure czar, bureaucracy "
            "chief, operations head of Fortune 500."
        ),
        invariant_mechanism=(
            "Strong 10L produces RECOGNIZED COMMAND OVER A DOMAIN OF "
            "ACTION. The substrate determines what counts as a domain "
            "(province vs P&L vs subreddit) but the karmic signature — "
            "the world routes its respect and resources to this native's "
            "decisions — is constant."
        ),
        modern_references=("Tirthankar Roy India economic history",
                           "Holland RIASEC career typology",
                           "Schein career anchors"),
    ),

    TranslationRecord(
        key="strong_11L",
        classification="bhava_placement",
        domain=Domain.CAREER_WEALTH,
        shloka=("Lord of 11H exalted or in own sign in Kendra/Trikona = "
                "gains from many sources (nana-desa-labha), many friends, "
                "fulfillment of all desires (sarva-kama-purti), "
                "flourishing elder siblings."),
        classical_references=("BPHS Ch.26",),
        ancient_manifestation=(
            "Labha in agrarian society = harvest yields, tribute from "
            "sub-feudatories, gifts from kin-network, marriage alliances "
            "bringing dowry + political coalition. 11H literally tracked "
            "the guild network (sreni) — merchant's reach across trading "
            "cities, Brahmana's network of patron-families, Kshatriya's "
            "web of allied clans. In low-trust pre-institutional society, "
            "who you knew determined what flowed to you."
        ),
        desh_shift=(
            "Networks have become measurable, portable, asymmetric — "
            "LinkedIn (1B+ users), alumni networks, customer bases, "
            "audience email lists, GitHub stars, Substack subscribers."
        ),
        kaal_shift=(
            "Reid Hoffman's network=net-worth thesis; Metcalfe's Law "
            "applies to careers — value scales with the square of "
            "connections."
        ),
        paristhiti_shift=(
            "Multiple-income-stream culture (rental + salary + side-"
            "business + investments + creator-revenue) is the literal "
            "modern reading of nana-desa-labha — gains from many places."
        ),
        modern_manifestation=(
            "LinkedIn-influencer / B2B sales executive whose deal-flow "
            "comes from network. Angel investor / scout whose returns "
            "track network quality. VC partner whose career is literally "
            "network-monetization. Recruiter, headhunter, executive coach "
            "— pure 11H professions. Community-builder / membership-"
            "business founder. Salesperson-as-rainmaker. Politician whose "
            "constituency = labha-base. Diaspora-network entrepreneur "
            "(Patel motel network, Marwari trade network — invariant "
            "ancient-to-modern)."
        ),
        invariant_mechanism=(
            "Strong 11L produces gains compounded through HUMAN-NETWORK "
            "DENSITY. Native is a hub through which mutual benefit flows, "
            "and the network itself becomes the asset. Whether the "
            "network is a sreni of cloth merchants across the Deccan or "
            "a Slack community of 50,000 SaaS founders, the karmic "
            "signature — desire fulfilled through coalition — is unchanged."
        ),
        modern_references=("Reid Hoffman network=net-worth",
                           "Kevin Kelly 1000 True Fans",
                           "Metcalfe's Law applied to careers"),
    ),

    TranslationRecord(
        key="Saraswati",
        classification="yoga",
        domain=Domain.CAREER_WEALTH,
        shloka=("Mercury + Jupiter + Venus in Kendra/Trikona/2H with "
                "Jupiter in own/exalted = Saraswati Yoga. Native becomes "
                "learned in all sastras, a poet, scholar, wealthy, "
                "famous, dear to kings — his words become artha "
                "(wealth-bearing)."),
        classical_references=("Mantreshvara via Phaladeepika 6.13",),
        ancient_manifestation=(
            "Kavi-pandita who recited at court receiving gold coins per "
            "verse (Kalidasa archetype). The jyotisi / vaidya whose "
            "knowledge was directly monetizable. Royal advisor whose "
            "vak (speech) decided policy. Temple acharya whose pravachanas "
            "drew patrons. Knowledge was scarce, oral, lineage-transmitted, "
            "economically privileged."
        ),
        desh_shift=(
            "Information has gone from scarce to over-abundant. Saraswati "
            "now favors those who SYNTHESIZE and DISTRIBUTE rather than "
            "merely POSSESS."
        ),
        kaal_shift=(
            "Kali Mercury-amplification means written/digital word "
            "travels infinitely. Single book or course earns for decades "
            "(Tim Ferriss, James Clear)."
        ),
        paristhiti_shift=(
            "Creator economy (Kevin Kelly's 1000 True Fans) is the "
            "modern Saraswati substrate — direct-to-audience monetization "
            "of expertise."
        ),
        modern_manifestation=(
            "Author whose books generate royalties for life + speaking "
            "fees + course revenue. Solo consultant / fractional executive "
            "who charges premium for synthesized expertise. YouTube "
            "educator / Substack writer with paid tier (Lex Fridman / "
            "Tim Ferriss / Andrew Huberman). Investment-research analyst "
            "whose newsletters are subscribed by funds. Lawyer / doctor "
            "whose treatise becomes canonical reference. Academic-turned-"
            "public-intellectual (Pinker, Haidt). AI-era twist: operator "
            "who wields LLMs as force multipliers on own expertise."
        ),
        invariant_mechanism=(
            "Saraswati produces SPEECH/WRITING THAT CONVERTS DIRECTLY TO "
            "WEALTH WITHOUT INTERMEDIARY LABOR. Native's words ARE the "
            "goods. Whether medium is palm-leaf manuscript copied by "
            "scribes or Substack hitting 100k subscribers, the karmic "
            "signature — vak becomes artha — is identical."
        ),
        modern_references=("Kevin Kelly 1000 True Fans",
                           "Tim Ferriss / James Clear royalty patterns",
                           "Naval Ravikant on specific knowledge"),
    ),

    TranslationRecord(
        key="Saraswati",
        classification="yoga",
        domain=Domain.DHARMA,
        shloka=("Saraswati Yoga viewed through dharma lens: native becomes "
                "kavi, vagmi, shastrajna, prasiddha-vidvan — poet, "
                "eloquent, scripture-knower, famous learned-one. Master "
                "of kavya, natya, alankara."),
        classical_references=("Saravali 38.1-3", "Phaladeepika 6.21"),
        ancient_manifestation=(
            "Kavi in original sense — composer of Sanskrit kavya, court-"
            "poet to a king (rajakavi), composer of devotional stotras, "
            "shastra-commentator. M+J+V triumvirate maps to classical "
            "fusion of shastra (system) + kavya (art) + bhakti (devotional "
            "sweetness). Kalidasa, Bhartrhari, Alvar poet-saints occupy "
            "this slot."
        ),
        desh_shift=(
            "Sanskrit court-poet has no modern analog as a profession; "
            "structural slot fragmented into novelist, essayist, "
            "screenwriter, intellectual-podcast-host, public-academic, "
            "'thought-leader'."
        ),
        kaal_shift=(
            "Geertz (Interpretation of Cultures 1973) — culture is a "
            "'web of significance' people spin themselves into. "
            "Saraswati-yoga native in 2026 spins this web through "
            "Twitter threads, longform Substacks, viral op-eds, "
            "bestselling nonfiction."
        ),
        paristhiti_shift=(
            "Audience is global and digital-native. Patronage by a king "
            "(Vikramaditya) is replaced by patronage by an algorithm "
            "(recommendation engines) and an audience (paid subscribers, "
            "Patreon)."
        ),
        modern_manifestation=(
            "Public intellectual with media reach (Malcolm Gladwell, "
            "Tyler Cowen, Maria Popova of Marginalian). Polymathic "
            "creative (Brian Eno, Rick Rubin). Academic-with-audience "
            "(Mary Beard, Cornel West). Indian diaspora Saraswati-yoga "
            "native often shows up as elite-university humanities "
            "professor who also writes for The New Yorker."
        ),
        invariant_mechanism=(
            "M+J+V fuses analytic precision (Mercury), wisdom-frame "
            "(Jupiter), aesthetic-affective resonance (Venus). The yoga "
            "always produces a native whose function is TO RENDER HIGH-"
            "COMPLEXITY MEANING INTO TRANSMISSIBLE-BEAUTIFUL FORM FOR A "
            "PUBLIC AUDIENCE. The audience changes; the function is "
            "invariant."
        ),
        modern_references=("Geertz Interpretation of Cultures",
                           "Maria Popova Marginalian model"),
    ),

    TranslationRecord(
        key="9L_in_12H",
        classification="bhava_placement",
        domain=Domain.DHARMA,
        shloka=("9L in 12H produces videsha-dharma (foreign dharma), "
                "sannyasa-bhagya (ascetic-fortune), pitr-viyoga "
                "(separation from father)."),
        classical_references=("BPHS Bhava-pati-phala adhyaya",
                              "Phaladeepika 15.9"),
        ancient_manifestation=(
            "Native's fortune was located OUTSIDE the social grid — "
            "typically through sannyasa (the 12H reading) or teerthayatra "
            "to distant teerthas. Loss of paternal religion was karmically "
            "grave; native reconstructed dharma as renunciate or hermit. "
            "The split between fortune (9H) and loss (12H) was a karmic "
            "forcing-function toward liberation."
        ),
        desh_shift=(
            "'Foreign' is the modal middle-class Indian aspiration; the "
            "12H foreign-residence is now the H-1B/OPT/PR pathway."
        ),
        kaal_shift=(
            "Globalization has inverted the valence of videsha — diaspora-"
            "dharma (Indian gurus teaching in California, yoga-teachers "
            "in Berlin) is the dominant mode of dharma transmission."
        ),
        paristhiti_shift=(
            "Many natives experience loss of inherited religion in "
            "young-adulthood followed by reconstruction of personal "
            "sadhana in a foreign context — the literal Hindu-American "
            "second-generation pattern, or American who finds Buddhism "
            "in Thailand."
        ),
        modern_manifestation=(
            "NRI dharma-teacher, foreign-based yoga-instructor, immigrant "
            "intellectual whose meaning-frame is built abroad, second-"
            "generation diaspora native who reconstructs Hindu practice "
            "on different terms than parents, expat who finds spiritual "
            "home in adopted country. The 'loss of family religion' is "
            "real but no longer catastrophic — it's now the precondition "
            "for SELF-AUTHORED dharma."
        ),
        invariant_mechanism=(
            "9L in 12H always relocates the fortune-of-meaning OUTSIDE "
            "THE INHERITED SOCIAL CONTAINER. Whether the container exited "
            "is a Vedic gotra in 500 CE or a Hindu-American suburban "
            "household in 2010 is desh-kaal cosmetic. The karmic work is: "
            "build dharma from outside the inheritance, not inside it."
        ),
        modern_references=("Indian diaspora religion studies (Vasudha "
                           "Narayanan, Diana Eck)",
                           "Wuthnow seeker spirituality"),
    ),

    TranslationRecord(
        key="Ketu_6H_or_8H",
        classification="bhava_placement",
        domain=Domain.HEALTH,
        shloka=("Ketu in 6H destroys enemies/disease (Vipareeta-flavor); "
                "Ketu in 8H brings avyakta-rogah (inexplicable illness). "
                "Ketu is moksha-karaka, dissolving bodily attachment."),
        classical_references=("BPHS Ch.40",
                              "Jaimini Sutras on Ketu moksha-karaka"),
        ancient_manifestation=(
            "Ketu's 'headless' signature mapped to decapitation in war, "
            "wounds of forgotten cause, fevers of mysterious origin that "
            "broke suddenly, possession-states, sudden falling-away of a "
            "limb (leprosy was canonical 'Ketu' disease — body parts "
            "dissociating from the whole). Acute, inexplicable, often "
            "spiritually-framed."
        ),
        desh_shift=(
            "Battlefield mortality rare for civilians."
        ),
        kaal_shift=(
            "PSYCHOLOGICAL and IMMUNOLOGICAL equivalents emerged as "
            "recognized categories: PTSD (named 1980 DSM-III), "
            "dissociative disorders, autoimmune disease (immune system "
            "'forgetting' self/non-self), psychosomatic medicine. The "
            "body-disowning-itself signature found new substrates."
        ),
        paristhiti_shift=(
            "Mental-health literacy normalizes the category of "
            "psychosomatic illness."
        ),
        modern_manifestation=(
            "Ketu-6 → autoimmune disease (immune burning away own tissue "
            "— Ketu's signature of self-immolation turned inward), "
            "psoriasis, eczema as somatic expression of unprocessed "
            "emotion. Sudden inexplicable recoveries (Vipareeta flavor — "
            "'spontaneous remission'). Patient who finds healing through "
            "RENUNCIATION (going vegan, leaving career, monastic retreat "
            "resolves the illness). Ketu-8 → dissociative states, sleep "
            "paralysis, near-death experiences, psychedelic-occasioned "
            "ego-dissolution, sudden cardiac events without warning, "
            "'silent' pathology found incidentally on imaging."
        ),
        invariant_mechanism=(
            "Ketu governs THE BODY EXPERIENCED AS NOT-SELF — whether "
            "through dismemberment (ancient), autoimmune attack (modern), "
            "or dissociative depersonalization (modern). The karmic theme "
            "is the dissolution of body-identification."
        ),
        modern_references=("van der Kolk Body Keeps the Score",
                           "Kleinman Rethinking Psychiatry",
                           "Bach NEJM 2002 autoimmune epidemiology"),
    ),

    TranslationRecord(
        key="Vipareeta Raja",
        classification="yoga",
        domain=Domain.HEALTH,
        shloka=("VRY in 6/8/12 viewed through health lens: native gains "
                "Raja-status through illness/adversity-navigation. The "
                "wound becomes the medicine offered to others."),
        classical_references=("Phaladeepika 6.34", "BPHS Ch.36"),
        ancient_manifestation=(
            "Native afflicted by chronic illness or 'enemy'-bhava "
            "activation, but with VRY operative, became a sannyasi, "
            "vaidya (healer who has personally suffered), tantric, or "
            "warrior who channeled adversity into renunciation and "
            "spiritual authority. Illness was the gateway to vairagya. "
            "Documented in hagiographies of physicians-who-were-patients."
        ),
        desh_shift=(
            "The illness-narrative economy (Kleinman, Frank's Wounded "
            "Storyteller 1995) and social-media platform economy have "
            "created the chronic-illness-as-public-identity pattern."
        ),
        kaal_shift=(
            "Cancer-survivor advocacy, mental-health awareness leadership, "
            "addiction-recovery testimony, chronic-illness influencer "
            "accounts have monetary, social, identity returns that "
            "classical India did not provide."
        ),
        paristhiti_shift=(
            "Memoir + Instagram is the modern equivalent of the "
            "spiritual-authority-after-illness arc."
        ),
        modern_manifestation=(
            "Develops cancer at 35, writes a bestselling memoir, becomes "
            "patient-advocacy figure. Becomes addicted, recovers, founds "
            "rehab/sober-coaching practice. Diagnosed bipolar, becomes "
            "mental-health-awareness influencer. Chronic illness drives "
            "into integrative medicine, becomes practitioner. The "
            "dushtana-bhava activation generates the crisis that produces "
            "the public platform. Ancient template (illness → renunciation "
            "→ spiritual authority) and modern template (illness → "
            "narrative → social/economic authority) are structurally "
            "isomorphic."
        ),
        invariant_mechanism=(
            "Dushtana houses are crisis-as-catalyst engines. Whether the "
            "platform is monastic-renunciation (ancient) or memoir-and-"
            "Instagram (modern), the yoga produces the same karmic move: "
            "THE WOUND BECOMES THE MEDICINE OFFERED TO OTHERS."
        ),
        modern_references=("Arthur Frank Wounded Storyteller",
                           "Kleinman Illness Narratives",
                           "Atul Gawande writer-physician archetype"),
    ),

    TranslationRecord(
        key="Sunapha_or_Anapha_or_Durudhura",
        classification="yoga",
        domain=Domain.KINSHIP,
        shloka=("Planets (not Sun) in 2nd from Moon = Sunapha (wealth-"
                "acquisition through own effort); in 12th = Anapha "
                "(refined character, expenses, charity); both = "
                "Durudhura (servants, vehicles, comforts)."),
        classical_references=("BPHS Ch.36.10-13", "Saravali Ch.13"),
        ancient_manifestation=(
            "2H from Moon = family/voice/resources flowing TO Moon-mind; "
            "12H = expenditure/withdrawal from Moon-mind. These were "
            "lineage-property yogas — Sunapha natives accumulated through "
            "paternal/maternal lineage networks; Anapha gave dharmic "
            "disposition and vairagya (renunciation); Durudhura gave the "
            "rich householder (servants, conveyances)."
        ),
        desh_shift=(
            "Lineage wealth less determining; self-made wealth dominant "
            "in urban professional class."
        ),
        kaal_shift=(
            "Renunciation (Anapha) culturally devalued; 'balanced "
            "lifestyle' / minimalism is the secular substitute."
        ),
        paristhiti_shift=(
            "Servants → cleaning services, dishwashers, Uber, food-"
            "delivery — the Durudhura bhoga package is now SaaS-mediated "
            "convenience."
        ),
        modern_manifestation=(
            "Sunapha: self-earned income; brand/family reputation as "
            "launchpad; 2nd-bhava-from-Moon planets indicate channel "
            "(Sun = authority/government, Mercury = communication/IT, "
            "Mars = engineering/military, Venus = creative/hospitality). "
            "Anapha: refined-character professional, philanthropy, "
            "charitable giving, sometimes lifestyle-spending without "
            "accumulation. Durudhura: high-consumption urban professional "
            "life — multiple homes, frequent travel, services-mediated "
            "convenience, staff."
        ),
        invariant_mechanism=(
            "Moon-as-fulcrum + flanking-planet structure governs the "
            "texture of livelihood-flow around the emotional center. "
            "Whether flow is grain-and-cattle or salary-and-equity is "
            "contextual; the temperamental signature (acquisitive Sunapha "
            "vs refined Anapha vs luxuriating Durudhura) is invariant."
        ),
        modern_references=("Indian urban consumer-class spending patterns",
                           "Joan Williams class-as-culture framework"),
    ),

    TranslationRecord(
        key="Matr Dosha",
        classification="yoga",
        domain=Domain.HEALTH,
        shloka=("Moon afflicted by Rahu/Saturn in 4H, or Moon-Rahu "
                "conjunction = Matr Dosha. Symmetric counterpart to "
                "Pitra Dosha on maternal/emotional axis."),
        classical_references=("Phaladeepika commentary",
                              "modern synthesis Sanjay Rath"),
        ancient_manifestation=(
            "Native suffered mother's early death, distance through "
            "father's co-wives, or maternal-line karma manifesting as "
            "emotional disturbance. In joint-family context, manifested "
            "as fractured matr-sambandha (mother-relationship) and the "
            "downstream consequences for women's standing."
        ),
        desh_shift=(
            "Maternal mortality dropped dramatically. Mother-child dyad "
            "isolated in nuclear family; the relationship has more "
            "psychological intensity (less social diffusion)."
        ),
        kaal_shift=(
            "Attachment theory (Bowlby, Ainsworth), maternal-attunement "
            "research (Tronick still-face paradigm), and intergenerational-"
            "trauma psychology have given vocabulary to what doctrine "
            "called Matr Dosha."
        ),
        paristhiti_shift=(
            "Therapy modalities specifically target maternal attachment "
            "wounds; women's-circles, somatic therapy, parts-work all "
            "address the matr-sambandha layer."
        ),
        modern_manifestation=(
            "Postpartum mood disorders. Eating disorders (Moon = "
            "nourishment, Rahu/Saturn = distortion). Anxious or avoidant "
            "attachment style. Conflict with mother surfacing in "
            "adulthood as therapy-content. Difficulty receiving care. "
            "For women: difficulty inhabiting the maternal role (PND, "
            "ambivalence about motherhood). For men: choosing partners "
            "who replicate mother's wounded pattern."
        ),
        invariant_mechanism=(
            "Rahu/Saturn afflicting Moon turbulates the emotional-"
            "nourishment substrate. The injury to the FEELING-OF-BEING-"
            "HELD is invariant whether mother died of childbirth fever "
            "(ancient) or was depressed and emotionally absent (modern)."
        ),
        modern_references=("Bowlby attachment theory",
                           "Ainsworth Strange Situation paradigm",
                           "Tronick still-face research"),
    ),

    TranslationRecord(
        key="bhava_5_planet_Jupiter",
        classification="bhava_placement",
        domain=Domain.DHARMA,
        shloka="Jupiter in 5H gives mantra-siddhi (mantra-accomplishment), "
               "putra-saukhya (joy through children), vidya-vaibhava "
               "(splendor through learning).",
        classical_references=("BPHS Ch.23", "Phaladeepika 8.13"),
        ancient_manifestation=(
            "Native received and accomplished a bija-mantra from his guru, "
            "practiced japa and anushthana (formal sustained practice). "
            "Fruit appeared as: (a) a son performing his death rites to "
            "liberate ancestors, (b) Vedic recitation mastery, "
            "(c) accumulated poorva-punya visible as good fortune. 5H "
            "was simultaneously bank account of merit AND channel of "
            "creative expression."
        ),
        desh_shift=(
            "Mantra-practice dislocated from caste-eligibility and "
            "guru-sanction. Anyone can stream Vipassana intro or learn "
            "TM from a Maharishi-trained teacher."
        ),
        kaal_shift=(
            "Sustained attention itself is the scarce resource "
            "(McGilchrist Master and His Emissary). 5H discipline now "
            "manifests as 'deep work' (Cal Newport) and 'flow' "
            "(Csikszentmihalyi)."
        ),
        paristhiti_shift=(
            "Children no longer karmically-mandatory for ancestor-"
            "liberation. Voluntary childlessness normalized. Creative "
            "output (code, books, art, products) substitutes structurally "
            "for biological progeny."
        ),
        modern_manifestation=(
            "Sustained meditation practitioner (long-time Vipassana, Zen, "
            "TM). Elite programmer with decade-deep focus (modern "
            "equivalent of mantra-anushthana). Mathematician, classical-"
            "musician, writer-with-deep-practice. Naval Ravikant's "
            "'specific knowledge from sustained practice' is the modern "
            "5H-Jupiter philosophy. 'Children' generalizes to creative-"
            "progeny — products of sustained focused effort that outlive "
            "the maker."
        ),
        invariant_mechanism=(
            "5H is where poorva-punya converts into PRESENT CAPACITY FOR "
            "SUSTAINED FOCUSED CREATION. Jupiter expands that capacity. "
            "Whether the focus-discipline is japa, zazen, deep work, or "
            "flow state, the karmic mechanism — CONCENTRATED ATTENTION "
            "as the engine of creation and liberation — is invariant."
        ),
        modern_references=("Csikszentmihalyi Flow",
                           "Cal Newport Deep Work",
                           "McGilchrist Master and His Emissary"),
    ),
)


# ─── Lookup API ───────────────────────────────────────────────────────


def translate_yoga(yoga_name: str) -> tuple[TranslationRecord, ...]:
    """All translation records for an active yoga.

    Returns a tuple because some yogas span multiple domains (e.g.
    Gajakesari has separate kinship + career-wealth readings).
    """
    return tuple(r for r in _TRANSLATIONS
                 if r.key == yoga_name and r.classification == "yoga")


def translate_bhava_planet(
    bhava: int, planet: str,
) -> tuple[TranslationRecord, ...]:
    """All translation records keyed on a specific bhava-planet pair.

    For example, ``translate_bhava_planet(8, "Saturn")`` returns the
    Saturn-8H ayur-karaka record. The key is canonically formatted as
    ``"bhava_<N>_planet_<P>"``.
    """
    key = f"bhava_{bhava}_planet_{planet}"
    return tuple(r for r in _TRANSLATIONS
                 if r.key == key and r.classification == "bhava_placement")


def translate_by_key(key: str) -> tuple[TranslationRecord, ...]:
    """Generic lookup — useful for special configurations like
    ``moon_afflicted_by_rahu_saturn``."""
    return tuple(r for r in _TRANSLATIONS if r.key == key)


def translations_by_domain(
    domain: str,
) -> tuple[TranslationRecord, ...]:
    """Return all records in a domain — useful for browsing."""
    return tuple(r for r in _TRANSLATIONS if r.domain == domain)


def all_translations() -> tuple[TranslationRecord, ...]:
    """The full registry — for diagnostic / completeness checks."""
    return _TRANSLATIONS


def format_translation(record: TranslationRecord) -> str:
    """Render one translation record as multi-line plain text."""
    lines = [
        f"=== {record.key} ({record.domain}) ===",
        "",
        f"SHLOKA: {record.shloka}",
        f"  Classical refs: {' | '.join(record.classical_references)}",
        "",
        f"ANCIENT manifestation:",
        f"  {record.ancient_manifestation}",
        "",
        "DKP shift:",
        f"  DESH: {record.desh_shift}",
        f"  KAAL: {record.kaal_shift}",
        f"  PARISTHITI: {record.paristhiti_shift}",
        "",
        f"MODERN manifestation:",
        f"  {record.modern_manifestation}",
        "",
        f"INVARIANT karmic mechanism:",
        f"  {record.invariant_mechanism}",
    ]
    if record.modern_references:
        lines.append(f"  Modern refs: {' | '.join(record.modern_references)}")
    return "\n".join(lines)


def translations_for_reading(
    active_yoga_names: Iterable[str],
    afflicted_bhava_planet_pairs: Iterable[tuple[int, str]] = (),
) -> tuple[TranslationRecord, ...]:
    """Convenience: collect all translations relevant to a Reading.

    Args:
        active_yoga_names: yoga names from ``Reading.active_yogas``.
        afflicted_bhava_planet_pairs: (bhava, planet) tuples for placements
            the Reading flags as significant (e.g. afflicted lord, strong
            karaka in dusthana).

    Returns:
        Combined tuple of TranslationRecord — deduplicated by key+domain.
    """
    seen: set[tuple[str, str]] = set()
    out: list[TranslationRecord] = []
    for yname in active_yoga_names:
        for r in translate_yoga(yname):
            sig = (r.key, r.domain)
            if sig not in seen:
                seen.add(sig)
                out.append(r)
    for bhava, planet in afflicted_bhava_planet_pairs:
        for r in translate_bhava_planet(bhava, planet):
            sig = (r.key, r.domain)
            if sig not in seen:
                seen.add(sig)
                out.append(r)
    return tuple(out)
