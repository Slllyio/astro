# `app.reading.cli` — CLI reference

The reading engine ships as a single-command CLI that takes birth data and
emits a structured JSON kundli analysis matching the
[`ReadingOutput`](json-schema.md) contract.

This page is the **user-facing reference**. For the JSON shape see
[`docs/reading/json-schema.md`](json-schema.md). For doctrine choices echoed
into every reading see [`docs/doctrine-decisions.md`](../doctrine-decisions.md).

---

## Synopsis

```
python -m app.reading.cli \
    --dob YYYY-MM-DD \
    --time HH:MM \
    --tz ±HH:MM \
    --lat <decimal_degrees> \
    --lon <decimal_degrees> \
    [--out PATH] \
    [--no-enrich] \
    [--verbose]
```

The five astronomical inputs are **required**. Output defaults to stdout; pass
`--out PATH` to write to disk instead (recommended for >100 KB outputs).

---

## Required arguments

| Flag | Type | Description |
|------|------|-------------|
| `--dob` | `YYYY-MM-DD` | Date of birth in ISO date form. Year must be in the Swiss Ephemeris range (roughly 5400 BCE — 5400 CE). |
| `--time` | `HH:MM` | Time of birth, 24-hour clock, **local civil time** at the birthplace. |
| `--tz` | `±HH:MM` | Signed UTC offset for the birthplace at that date. The CLI does **not** accept tz-database names (`Asia/Kolkata`) — pass `+05:30` explicitly. |
| `--lat` | float in `[-90, 90]` | Latitude in decimal degrees. Negative = South. |
| `--lon` | float in `[-180, 180]` | Longitude in decimal degrees. Negative = West. |

Birth data is validated by `ChartInput` (Pydantic `extra="forbid"`). Out-of-range
latitudes / longitudes or malformed date / time strings fail with exit code 1.

---

## Optional arguments

| Flag | Default | Description |
|------|---------|-------------|
| `--out PATH` | none (stdout) | Write the JSON document to `PATH` instead of stdout. Stdout is silenced when `--out` is given. |
| `--no-enrich` | off (enrichment on) | Skip Tier-3 enrichment (RAG citations, consensus scoring, dispute surfacing, robustness scoring, contradiction detection). Useful when the doctrine RAG index isn't deployed or when you only need core findings. |
| `--verbose` | off | Emit DEBUG-level logs to stderr. Stdout still carries the JSON document. |

---

## Exit codes

The CLI never raises an unhandled exception — every failure path resolves to a
documented exit code (spec Section 5).

| Code | Meaning | When |
|------|---------|------|
| `0` | success | Output is valid JSON conforming to `ReadingOutput`. |
| `1` | bad input | `ChartInput` validation failed (out-of-range lat/lon, malformed date / time / tz, missing required arg). Pydantic error written to stderr. |
| `2` | ephemeris / chart failure | Swiss Ephemeris call failed or natal-chart computation raised. Full traceback logged to stderr via `logger.exception`. |
| `3` | schema validation failure | Engine produced an output that failed `ReadingOutput.model_validate`. This is an **engine bug** — file an issue. |
| `4` | RAG index missing (graceful) | Tier-3 enrichment requested but the knowledge index isn't present. Current behaviour: exit `0` with a `warnings` entry; exit `4` reserved for a future `--strict` flag. |

---

## Worked examples

### 1. Bangalore baseline (the pinning chart)

The project's canonical regression anchor: 1990-07-15 at 12:00 IST, Bangalore.
Pins Mercury MD, Virgo Lagna ~173.99°, Moon at Revati pada 3.

```
python -m app.reading.cli \
    --dob 1990-07-15 \
    --time 12:00 \
    --tz +05:30 \
    --lat 12.97 \
    --lon 77.59 \
    --out reading-bangalore.json
```

Expected output: a ~1 MB JSON document with the 9 top-level keys populated and
zero `warnings`.

### 2. Western-format birth (London)

Western consumers pass the same flags — no city-name lookup is done; you must
supply the coordinates yourself.

```
python -m app.reading.cli \
    --dob 1985-03-22 \
    --time 06:45 \
    --tz +00:00 \
    --lat 51.5074 \
    --lon -0.1278 \
    --out reading-london.json
```

Note the negative longitude for west-of-Greenwich.

### 3. Reykjavík (high-latitude polar edge case)

The engine handles latitudes where Placidus / Koch would fail; Sripati bhava
cusps remain defined. Reykjavík is a useful smoke test for polar edge cases.

```
python -m app.reading.cli \
    --dob 2000-12-21 \
    --time 11:30 \
    --tz +00:00 \
    --lat 64.1466 \
    --lon -21.9426 \
    --out reading-reykjavik.json
```

Expect: no exceptions; ascendant may shift unusually quickly with small `--time`
changes — verify via the `robustness` block in the output.

### 4. `--no-enrich` for speed

When you only need core findings (primitives, foundations, practitioner,
sequences, domains) and want to skip the RAG-citation pass:

```
python -m app.reading.cli \
    --dob 1990-07-15 \
    --time 12:00 \
    --tz +05:30 \
    --lat 12.97 \
    --lon 77.59 \
    --no-enrich \
    --out reading-quick.json
```

This drops citations, consensus, dispute, robustness, and contradiction fields
to their zero-state defaults but keeps every classical finding.

### 5. Verbose stdout pipe to `jq`

Pipe the JSON straight to `jq` for ad-hoc exploration while logging to stderr:

```
python -m app.reading.cli \
    --dob 1990-07-15 \
    --time 12:00 \
    --tz +05:30 \
    --lat 12.97 \
    --lon 77.59 \
    --verbose \
  | jq '.domains.career.overall_verdict.verdict'
```

---

## Output shape overview

The output JSON has exactly 9 top-level keys (locked by `Meta.schema_version`
`1.0.0`). Full schema in [`json-schema.md`](json-schema.md).

| Key | Stage | Contents |
|-----|-------|----------|
| `meta` | — | Engine + chart envelope; `schema_version`, `stability`, `engine_version`, `python_version`, `swiss_ephemeris_version`, `generated_at`, `chart_input` echo, `doctrines_used`, full `doctrine_config` (16 D-N decisions), `enrichment_enabled`, `stage_timings_ms`. |
| `chart` | Stage 1 | Natal raw outputs: `lagna_longitude`, `ayanamsa`, `planets`, `cusps`, `extras`. |
| `primitives` | Stage 2 (Tier-0) | Findings from karakas, arudha, dignities, etc. Indexed by module. |
| `foundations` | Stage 3 (Tier-1) | Functional nature, bhava chalit, argala, …. |
| `practitioner` | Stage 4 (Tier-2) | MKS, Kala Sarpa, Neech Bhanga, doctrine layer. |
| `sequences` | Stage 5 | 4 named sequence results: `amsha_bala_krama`, `career_executive`, `md_judgments[]`, `ad_judgments[]`. |
| `domains` | Stage 6 | 6 named domain readings: `career`, `marriage`, `children`, `wealth`, `health`, `education`. |
| `contradictions` | Stage 8.3 | Cross-finding disagreements detected by `contradiction_detector.py`. Severity `soft` or `hard`. |
| `warnings` | — | Non-fatal engine diagnostics. Empty list on the canonical Bangalore baseline. |

---

## Performance budget

Spec Section 16 outer ceilings (regression-tested in
`tests/reading/test_performance.py`):

| Mode | Budget | Typical |
|------|--------|---------|
| `--no-enrich`, cold cache | < 8 s | ~0.3 s |
| full pipeline, cold cache | < 12 s | ~0.6 s |
| full pipeline, warm cache | < 7 s | sub-second |

If the CLI exceeds these budgets on commodity hardware (8-core, 16 GB), please
file a performance issue with `--verbose` output attached.

---

## Versioning

- Schema (`meta.schema_version`) is currently `1.0.0`.
  Additive changes bump minor (1.1.0); breaking changes bump major (2.0.0).
- Doctrine variants are echoed into `meta.doctrine_config` — every reading is
  self-describing about which doctrine decisions produced it.
- CLI flag names and exit codes are stable across the `1.x` schema line.
