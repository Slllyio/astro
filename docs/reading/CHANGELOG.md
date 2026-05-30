# `ReadingOutput` schema CHANGELOG

This file logs every change to `app/reading/schema.py` that ships as a new
`Meta.schema_version` value. The schema is the public contract for every
downstream consumer (CLI, future LLM narrators, frontend, RAG layers); we
follow strict semver:

- **MAJOR** (`1.x.x` -> `2.0.0`) — breaking change: field removed, type
  narrowed, validator added that rejects previously-valid input.
- **MINOR** (`1.0.0` -> `1.1.0`) — additive change: new optional field, new
  enum value, new top-level Literal value. Old consumers keep working.
- **PATCH** (`1.0.0` -> `1.0.1`) — clarification, doc-only, regenerated
  `json-schema.json` after a non-functional refactor.

`Meta.schema_version` is a `Literal[...]` of the currently-emitted version
PLUS every prior version that remains accepted on read. Bumping a MINOR
extends the Literal without removing the older value.

---

## 1.1.0 — V1.5 wiring (2026-05-30)

**Additive (MINOR).** Old `1.0.0` payloads remain valid and are still
accepted on read. New default emitted value is `"1.1.0"`.

### `SequencesBlock` — two new optional fields

Both default to `None` and are emitted by the deterministic Stage-5 path of
`_run_core_pipeline` whenever the chart envelope carries `d1`:

- `chara_dasha: dict[str, Any] | None` — V1.5 D-17. Jaimini sign-frame
  84-year cycle. Shape mirrors
  `app.reading.sequences.chara_dasha.CharaDashaResult.model_dump(mode="json")`.
- `yogini_dasha: dict[str, Any] | None` — V1.5 D-18. 36-year specialty dasha
  (8 yoginis). Shape mirrors
  `app.reading.sequences.yogini_dasha.YoginiDashaResult.model_dump(mode="json")`.

Both fields carry `dict[str, Any]` rather than their concrete Pydantic models
because the concrete result models live alongside their sequence modules;
importing them into `schema.py` would create a circular import. The sequence
modules emit `.model_dump(mode="json")` dicts that pass through unchanged.

### `DomainsBlock.<domain>.cross_checks` — modern-life appended findings

`enrich_with_modern_signals` (V1.5 module) runs after Stage 6 and appends
`classification="primitive"` Findings with IDs prefixed `modern_life.*` to
each domain's `cross_checks` list. The shape of `cross_checks` is unchanged
(`list[Finding]`); only the count grows. Runs in the `--no-enrich` path —
deterministic, no LLM / RAG.

### Schema version Literal extended

```python
schema_version: Literal["1.0.0", "1.1.0"] = "1.1.0"
```

---

## 1.0.0 — initial public lock (2026-05-27)

First fully-locked schema accompanying the V1 reading engine. Stable
9-top-level-key envelope; `extra="forbid"` discipline on every model.
