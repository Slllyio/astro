# Data acquisition plan — feeding the pre-registered replication

> Drafted 2026-06-11. **Live web verification was blocked by an account session
> limit (resets 06:50 UTC); figures drawn from this repo's existing importers are
> firm, figures for external sources are from prior knowledge and marked ⚠ for
> re-confirmation once search is available.** Goal set by
> `replication_preregistration.md`: **≥ ~9,000 auspicious first events** (marriage/
> career/education) with birth-time-quality charts to resolve IRR 1.10 at 80% power.

## 1. The real bottleneck is EVENTS, not charts

We can already build **60,000+ charts** from sources we have importers for. What's
scarce is **dated life events joined to those charts** — the current corpus has
only **4,590 events** (LunarAstro). Birth data is abundant and cheap; *dated
biography events* (marriage/career/death with a year) are the constraint. Every
acquisition decision below is judged on **net new (time + dated-event) pairs**,
not new charts.

## 2. What we already have importers for (firm — from `app/medini/etl/`)

| source | importer | size | has TIME? | has DATED EVENTS? | license posture |
|---|---|---|---|---|---|
| LunarAstro scrape | `lunarastro_importer` | 35,931 recs (31,341 people + **4,590 events**) | 96.7% | **yes** (the only rich event source we use) | research scrape, no license |
| ASTROCRM / holos (ADB-derived) | `holos_importer` | **61,583** AA+A births; 6,488 with vocation | yes | no (birth + category only) | derived from Astro-Databank, no LICENSE |
| VedAstro | `vedastro_importer` | ~15,800 AA births + MarriageInfoDataset | yes | **marriage outcomes** (dates? ⚠ verify) | **MIT** |
| Lapaas good-time-finder | `lapaas_importer` | 8,722 people | yes | partial | GitHub, no LICENSE |
| Kala charts DB | `kala_metadata_importer` | ~1,160 charts by occupation | yes | no (occupation only) | GitHub |
| Astro-Databank (Wayback) | `wayback_scraper` | ~32k snapshots / **~14k unique entries** | yes (Rodden-rated) | **biographies = dated events** | facts; ADB wiki terms ⚠ |

**Takeaway:** the charts are solved. Two existing assets are under-exploited for
*events*: the **Wayback Astro-Databank biographies** (~14k entries, each with a
dated life-event narrative we have not parsed) and a **Wikidata join** (below).

## 3. Ranked acquisition targets for NEW dated events

### Tier 1 — accessible now, highest event yield
1. **Astro-Databank biographies via Wayback (`wayback_scraper` already pivots
   here).** ~14k unique Rodden-rated entries; each wiki page has a biography +
   often an explicit dated event list ("1955 married", "1972 elected"). Parsing
   these for (event_class, year) is the single biggest near-term event source we
   can legally reach (Wayback snapshots predate the JS bot challenge). **Est. yield
   if ~40% of 14k entries give ≥1 datable auspicious event → ~5,000–8,000 events.**
   This alone could approach the 9k target. *Build: an event-date extractor over
   the archived HTML (regex + a small date/category parser; the biographies are
   semi-structured).*
2. **Wikidata join (scalable event multiplier).** Wikidata carries millions of
   *dated* life events as structured claims: marriage **P26** with `start time`
   qualifiers, death **P570**, positions-held **P39** / employer **P108** with
   start dates, awards **P166** with `point in time`. Join by **name + birth date**
   to our birth-*time* charts (ADB/VedAstro/LunarAstro). Any matched person can
   contribute several dated events. ⚠ verify how many humans carry hour-precision
   births in Wikidata (P569 precision) — likely few, so use Wikidata for the
   *events* and the astro DBs for the *time*. **Est. yield: thousands of marriage/
   death/career dates for already-charted public figures.** *Build: a Wikidata
   Query Service / dump puller + name-birthdate matcher with `resolve_persons_dedup`.*
3. **VedAstro MarriageInfoDataset (MIT).** Confirm whether it carries marriage
   **dates** or only outcomes (⚠ the importer notes "outcome"); if dated, it's a
   clean, licensed marriage-event drop joined on RowKey to the 15.8k charts.

### Tier 2 — accessible, moderate yield
4. **More LunarAstro endpoints.** We scraped `/kundli-all` + `/kundli-details`;
   ⚠ check whether the site now exposes more event-bearing pages or a larger export
   than the 35,931 we have.
5. **Shared Jagannatha Hora `.jhd` / Kala `.cht` collections on GitHub.** Hobbyist
   bundles of notable-chart files; ⚠ find named repos. Birth data mostly; events
   only where filenames/notes carry them — low event yield, high dedup overlap.

### Tier 3 — gold standard, but institutional/slow
6. **1958 NCDS & 1970 BCS70 British birth cohorts (UK Data Service).** These
   famously record **time of birth** (the basis of Dean's "time twins" work) AND,
   as multi-decade panel studies, carry **richly dated life events** — marriage,
   divorce, employment, children, mortality — for ~17k people each. This is the
   *ideal* (registry-quality time + longitudinal events) and independent
   researchers **can** apply, but it requires a UK Data Service application,
   ethics/declared use, and the data is anonymized (no public figures). ⚠ confirm
   birth-time variable is in the released files (it is referenced in Dean & Kelly's
   methodology). **Highest scientific quality; weeks of lead time.**
7. **Gauquelin archives at CURA (`cura.free.fr`, Guinard).** ~25,000+ registry
   (AA-quality) timed births of professionals. Free, machine-readable. But carries
   **profession, not dated life events** — useful for *career-class membership*
   tests and as a clean birth-time pool, not for event timing. Good for a
   profession-specific sub-study, not the main event count.

## 4. Projected path to the 9,000-event target

| step | new auspicious events (est.) | cumulative | confidence |
|---|---|---|---|
| current (LunarAstro) | ~2,700 in-band | 2,700 | firm |
| + ADB Wayback biography parse | +4,000–6,000 | ~7,000–8,700 | ⚠ depends on parse hit-rate |
| + Wikidata event join | +2,000–4,000 | **~9,000–12,000** | ⚠ depends on name-match rate |
| + NCDS/BCS70 (if pursued) | +large, anonymized | — | separate, gold-standard track |

**The combination of (1) ADB-Wayback biographies + (2) Wikidata events is the
realistic route to clearing the power threshold without institutional access**,
and both reach data we can legally use (archived facts; CC0 Wikidata).

## 5. Quality, legal, and dedup notes

- **Rodden ratings:** keep AA (birth certificate) and A (from memory) only for the
  primary test; tag B/C/DD and exclude, as the existing pipeline does.
- **Facts vs copyright:** raw birth data (date/time/place) are facts, not
  copyrightable; biography *text* and a database's *selection/arrangement* can be.
  Use facts + dated events, not verbatim prose; honor each site's ToS; prefer the
  explicitly-licensed sources (VedAstro MIT, Wikidata CC0) where possible.
- **Dedup is mandatory:** ADB, VedAstro, ASTROCRM, Astrotheme, and most celebrity
  DBs all *derive from Astro-Databank* — huge overlap. Run every new source through
  `resolve_persons_dedup` (name + birth datetime + coords) before counting events,
  or the "new" events are double-counts that inflate n without adding independence
  (and would break the pre-registration's independence assumption).
- **Independence caveat for the replication:** the pre-registered test wants an
  *independent* corpus. ADB-derived additions overlap our existing ASTROCRM/VedAstro
  charts — so for a clean confirmation, the **events** can be new even if the
  **charts** overlap, but ideally draw the confirmation sample from persons not in
  the current LunarAstro set. NCDS/BCS70 is the only fully-independent option.

## 6. Immediate next steps (no new scraping infra needed for the first two)

1. **Build an ADB-Wayback event extractor** over the snapshots `wayback_scraper`
   already retrieves: parse biography sections → (person, event_class, year) →
   feed the existing `events` schema. *Biggest bang, uses data we can already fetch.*
2. **Build a Wikidata event puller + name/birthdate matcher** to attach P26/P570/
   P39 dated events to our charted persons. CC0, scalable.
3. **Verify (after session reset):** VedAstro marriage-date granularity; current
   LunarAstro export size; Wikidata birth-time precision counts; NCDS birth-time
   variable availability and application route. These four ⚠ items need live
   confirmation but do not block steps 1–2.

*Re-run the blocked deep-research pass after 06:50 UTC to firm up the ⚠ figures and
surface any named Kaggle/HuggingFace ADB-with-biographies dumps; this plan's
structure (events-bottleneck → Wayback + Wikidata → optional cohort gold standard)
will not change.*
