# Doctrine audit — 2026 Q3

## NOT a blocking CI gate

Per spec Section 7, this audit is **report-only**. LLM-grader
variance makes a hard CI gate flaky; instead this workflow stages
a deterministic Bangalore-baseline reading on a quarterly cadence
and a human dispatches the `bphs-doctrine-reviewer` agent against
the staged JSON. The agent's verdict is filed separately.

## Inputs

The canonical Bangalore baseline pinned in `CLAUDE.md`:

```
--dob 1990-07-15 --time 12:00 --tz +05:30 --lat 12.97 --lon 77.59
```

## Artefact

See [`doctrine-2026-Q3.json`](./doctrine-2026-Q3.json).

## Manual follow-up

1. Open the staged JSON.
2. Dispatch the `bphs-doctrine-reviewer` agent (see
   `.claude/agents/bphs-doctrine-reviewer.md`) with the JSON as
   input.
3. File the reviewer's verdict in `docs/audits/verdicts/`.

## Sanity checks the reviewer should confirm

- `meta.schema_version == "1.1.0"` (V1.5 wiring; `"1.0.0"` accepted on read)
- `meta.doctrine_config` echoes the locked D-1..D-16 defaults
- `chart.lagna_longitude` ≈ 173.99° (Virgo lagna)
- Mercury MD is current at the reading-generation date
- All 6 domains are populated
- `warnings == []`
