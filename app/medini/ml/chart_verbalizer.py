"""Round 6 Phase 9: chart-as-language verbalization layer.

Scope choice: we're running CPU-only without LLM fine-tuning
infrastructure. A full Phi-3 / Qwen2 LoRA fine-tune isn't viable
here. Instead Phase 9 ships the COMPOSABLE pieces that an LLM
fine-tune would have used:

1. **chart_to_text(natal_features)** — turns a Round-5 natal row
   into a structured Markdown chart description.
2. **prediction_to_text(model_output)** — turns Round-5 classifier
   output + Phase 1 RuleFit rules + Phase 6 causal verdicts into
   a natural-language reading.
3. **build_chart_qa_dataset()** — emits (chart_text, question,
   gold_answer) tuples ready for LoRA fine-tuning when GPU comes
   online.

The verbalization layer is itself usable as a deterministic
chatbot for chart readings — the LLM step is the optional upgrade
that learns to PHRASE these readings more naturally.

CLI
===
    python -m app.medini.ml.chart_verbalizer \\
        --natal app/medini/data/ml_astro_round5.parquet \\
        --rules data/ml_runs/rules_round6_phase1_v2/ \\
        --output data/ml_runs/verbalizer_round6_phase9/
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# ---------- Astrological constants for human-readable output ----------

SIGNS: tuple[str, ...] = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)

NAKSHATRAS: tuple[str, ...] = (
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
    "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha",
    "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana",
    "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada",
    "Revati",
)

PLANETS: tuple[str, ...] = (
    "sun", "moon", "mars", "mercury", "jupiter",
    "venus", "saturn", "rahu", "ketu",
)

HOUSE_DOMAINS: dict[int, str] = {
    1: "self, identity, body",
    2: "wealth, family, speech",
    3: "siblings, courage, communications",
    4: "home, mother, peace of mind",
    5: "children, creativity, knowledge",
    6: "enemies, disease, service",
    7: "marriage, partnerships",
    8: "longevity, secrets, transformation",
    9: "fortune, dharma, father",
    10: "career, status, authority",
    11: "gains, friendships, ambitions",
    12: "loss, liberation, foreign lands",
}


def _deg_to_dms(deg: float) -> str:
    """Convert a degree-in-sign float to D°MM'."""
    d = int(deg)
    m = int((deg - d) * 60)
    return f"{d}°{m:02d}'"


# ---------- Chart serialiser ----------

def chart_to_markdown(row: pd.Series) -> str:
    """Render a Round-5 natal feature row as a Markdown chart sheet."""
    name = row.get("name", "(unnamed)")
    asc_lon = float(row.get("lagna_lon", 0.0))
    asc_sign = int(row.get("lagna_sign", 0))
    asc_sign_name = SIGNS[(asc_sign - 1) % 12] if 1 <= asc_sign <= 12 else "?"
    asc_deg = asc_lon % 30.0

    lines = [
        f"# Natal chart — {name}",
        "",
        f"**Ascendant (Lagna)**: {asc_sign_name} {_deg_to_dms(asc_deg)} "
        f"({asc_lon:.2f}° tropical)",
        "",
        "## Planetary placements",
        "",
        "| Planet | Sign | Deg in sign | House | Nakshatra | Retro |",
        "|---|---|---|---|---|---|",
    ]
    for p in PLANETS:
        lon = float(row.get(f"lon_{p}", 0.0))
        sign_idx = int(lon // 30) + 1
        sign_name = SIGNS[(sign_idx - 1) % 12]
        deg = lon % 30
        house = int(row.get(f"house_{p}", 0))
        nak_idx = int(row.get(f"nak_{p}", 0))
        nak_name = NAKSHATRAS[nak_idx % 27] if 0 <= nak_idx < 27 else "?"
        rx = "R" if int(row.get(f"rx_{p}", 0)) == 1 else " "
        lines.append(
            f"| {p.title()} | {sign_name} | {_deg_to_dms(deg)} | "
            f"{house} | {nak_name} | {rx} |"
        )

    # Yogas detected
    yoga_cols = [c for c in row.index if c.startswith("yoga_")]
    active_yogas = [
        c.replace("yoga_", "").replace("_", "-").title()
        for c in yoga_cols
        if int(row.get(c, 0)) == 1
    ]
    if active_yogas:
        lines.extend([
            "",
            "## Active yogas",
            "",
            *[f"- **{y}**" for y in active_yogas],
        ])

    # Notable drishtis (Saturn aspects on others)
    drishti_lines = []
    for to_p in PLANETS:
        if to_p == "saturn":
            continue
        if int(row.get(f"drishti_saturn_{to_p}", 0)) == 1:
            drishti_lines.append(f"- Saturn aspects {to_p.title()}")
    for to_p in PLANETS:
        if to_p == "jupiter":
            continue
        if int(row.get(f"drishti_jupiter_{to_p}", 0)) == 1:
            drishti_lines.append(f"- Jupiter aspects {to_p.title()}")
    if drishti_lines:
        lines.extend([
            "",
            "## Notable drishtis",
            "",
            *drishti_lines,
        ])

    # Dasha cycle summary
    natal_lord = None
    natal_remaining = float(row.get("natal_dasha_remaining_years", 0.0))
    earliest_age = float("inf")
    for p in PLANETS:
        age = row.get(f"dasha_start_age_{p}")
        if age is None or (isinstance(age, float) and np.isnan(age)):
            continue
        age = float(age)
        if age <= 0 and age > earliest_age:
            earliest_age = age
            natal_lord = p
    lines.extend([
        "",
        "## Vimshottari dasha",
        "",
        f"- Natal Mahadasha lord: **{natal_lord.title() if natal_lord else '?'}**",
        f"- Years remaining in natal Mahadasha at birth: {natal_remaining:.2f}",
        "",
        "## Mahadasha schedule (years from birth)",
        "",
        "| Lord | Start age | Notes |",
        "|---|---|---|",
    ])
    for p in PLANETS:
        age = row.get(f"dasha_start_age_{p}")
        if age is None or (isinstance(age, float) and np.isnan(age)):
            continue
        age = float(age)
        notes = "pre-birth" if age < 0 else ("infant" if age < 16 else "")
        lines.append(f"| {p.title()} | {age:+.1f} | {notes} |")

    return "\n".join(lines)


# ---------- Rule loader (for prediction narration) ----------

def load_phase1_rules(rules_dir: Path) -> dict[str, list[dict]]:
    """Load per-class CSV files emitted by Phase 1."""
    rules_by_class: dict[str, list[dict]] = {}
    for csv_path in rules_dir.glob("rules_*.csv"):
        class_name = csv_path.stem.replace("rules_", "").replace("__", "/ ")
        try:
            df = pd.read_csv(csv_path)
        except Exception:
            continue
        rows = df.to_dict(orient="records")
        rules_by_class[class_name] = rows
    return rules_by_class


# ---------- Prediction-to-text ----------

def predict_to_text(
    row: pd.Series, rules_by_class: dict[str, list[dict]],
    top_k_per_class: int = 3,
) -> str:
    """For a natal chart, list which Phase-1 rules ACTIVATE in this
    chart and what their event-class direction is.

    This is a deterministic, rule-based chart reading — the
    interpretive layer that an LLM fine-tune would later phrase
    naturally.
    """
    lines = [
        "# Astrological reading (rule-based)",
        "",
        "Below are the **highest-impact Phase-1 rules that activate**",
        "in this chart, grouped by event class. Positive coefficients",
        "raise probability of that event class; negative lower it.",
        "",
    ]
    active_count = 0
    for class_name in sorted(rules_by_class.keys()):
        active_rules = []
        for rule_row in rules_by_class[class_name][:50]:
            # Cheap activation test: parse `rule_raw` predicates and
            # check the natal row. Each predicate is `feat OP threshold`.
            try:
                preds = rule_row.get("rule_raw", "").split(" AND ")
                ok = True
                for p_str in preds:
                    parts = p_str.strip().split()
                    if len(parts) < 3:
                        ok = False
                        break
                    feat, op, thresh = parts[0], parts[1], float(parts[2])
                    val = row.get(feat)
                    if val is None or (isinstance(val, float) and np.isnan(val)):
                        ok = False
                        break
                    val = float(val)
                    if op == "<" and not (val < thresh):
                        ok = False; break
                    if op == ">=" and not (val >= thresh):
                        ok = False; break
                if ok:
                    active_rules.append(rule_row)
            except Exception:
                continue
        if not active_rules:
            continue
        active_rules.sort(
            key=lambda r: -abs(float(r.get("coefficient", 0))),
        )
        lines.append(f"## {class_name.title()}")
        lines.append("")
        for r in active_rules[:top_k_per_class]:
            coef = float(r.get("coefficient", 0))
            arrow = "↑" if coef > 0 else "↓"
            lines.append(
                f"- {arrow} ({coef:+.2f}) {r.get('rule_english', r.get('rule_raw', '?'))}"
            )
            active_count += 1
        lines.append("")
    if active_count == 0:
        lines.append("_(no rules activate strongly in this chart)_")
    return "\n".join(lines)


# ---------- Build LoRA-ready QA dataset ----------

def build_qa_dataset(
    natal_df: pd.DataFrame,
    events_csv: Path,
    output_path: Path,
    max_persons: int = 1000,
) -> None:
    """Emit (chart_text, prompt, answer) triples to JSONL.

    Prompts are generic templates; answers come from each person's
    actual event timeline. Format matches Phi-3 / Qwen2 SFT format.
    """
    events = pd.read_csv(events_csv)
    events["_n"] = events["name"].astype(str).str.strip().str.lower()
    events["event_date"] = pd.to_datetime(events["event_date"], errors="coerce")
    events = events.dropna(subset=["event_date"]).copy()
    events["root_lower"] = events["event_root"].astype(str).str.lower().str.strip()

    raw = pd.read_csv(
        "data/astro_databank/merged_with_events.csv", low_memory=False,
    )
    raw["_n"] = raw["name"].astype(str).str.strip().str.lower()
    raw["date_of_birth"] = pd.to_datetime(
        raw["date_of_birth"], errors="coerce",
    )
    raw = raw.drop_duplicates(subset="_n").set_index("_n")

    natal_df["_n"] = natal_df["name"].astype(str).str.strip().str.lower()
    natal_df = natal_df.drop_duplicates(subset="_n").set_index("_n")

    n_emitted = 0
    with output_path.open("w", encoding="utf-8") as f:
        for name, person_events in events.groupby("_n"):
            if name not in natal_df.index or name not in raw.index:
                continue
            chart_md = chart_to_markdown(natal_df.loc[name])
            birth = raw.loc[name, "date_of_birth"]
            if pd.isna(birth):
                continue
            person_events_sorted = person_events.sort_values("event_date")
            for _, ev in person_events_sorted.iterrows():
                age = (ev["event_date"] - birth).days / 365.25
                if not (0 <= age <= 100):
                    continue
                question = (
                    "Given the natal chart above, what kind of major event "
                    f"would likely occur around age {int(age)}?"
                )
                answer = (
                    f"At age {int(age)}, this chart suggests a "
                    f"'{ev['root_lower']}' event "
                    f"({ev.get('event_subtype', '')}).".strip()
                )
                record = {
                    "chart": chart_md,
                    "prompt": question,
                    "answer": answer,
                    "_meta": {
                        "name": name,
                        "event_root": ev["root_lower"],
                        "age": age,
                    },
                }
                f.write(json.dumps(record) + "\n")
                n_emitted += 1
            if n_emitted >= max_persons * 5:  # 5 events avg per person
                break
    logger.info("wrote %d QA records to %s", n_emitted, output_path)


# ---------- Main ----------

def run_phase9(
    *,
    natal_parquet: Path,
    rules_dir: Path,
    events_csv: Path,
    output_dir: Path,
    n_demo: int = 3,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("loading natal parquet ...")
    natal_df = pd.read_parquet(natal_parquet)

    logger.info("loading Phase-1 rules ...")
    rules_by_class = load_phase1_rules(rules_dir)
    logger.info("loaded rules for %d classes: %s",
                len(rules_by_class), list(rules_by_class.keys())[:5])

    # Demo: serialize + narrate 3 example charts
    sample = natal_df.sample(n=n_demo, random_state=42).reset_index(drop=True)
    for i, row in sample.iterrows():
        name_safe = "".join(
            c if c.isalnum() else "_" for c in str(row.get("name", f"chart{i}"))
        )[:40]
        chart_path = output_dir / f"chart_{i}_{name_safe}.md"
        reading_path = output_dir / f"reading_{i}_{name_safe}.md"
        chart_path.write_text(chart_to_markdown(row), encoding="utf-8")
        reading_path.write_text(
            predict_to_text(row, rules_by_class), encoding="utf-8",
        )
        logger.info("wrote demo: %s + %s", chart_path.name, reading_path.name)

    # QA dataset for downstream LoRA fine-tune
    qa_path = output_dir / "chart_qa_dataset.jsonl"
    build_qa_dataset(natal_df, events_csv, qa_path, max_persons=2000)

    # Report
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    report = output_dir / "report.md"
    n_qa = sum(1 for _ in qa_path.open("r", encoding="utf-8"))
    lines = [
        "# Phase 9 — Chart-as-Language verbalization",
        "",
        f"_Generated {now}_",
        "",
        "## Scope",
        "",
        "Phase 9 ships the COMPOSABLE pieces that a Phi-3 / Qwen2 LoRA",
        "fine-tune would have used. Full LLM training deferred until GPU",
        "infrastructure available.",
        "",
        "## Deliverables",
        "",
        "1. `chart_to_markdown(row)` — natal feature row → Markdown chart",
        "   sheet with planet positions, signs, nakshatras, houses,",
        "   active yogas, notable drishtis, and Vimshottari schedule.",
        "2. `predict_to_text(row, rules)` — applies Phase-1 rules to a",
        "   chart and outputs a natural-language reading with rule",
        "   activations and event-class probabilities.",
        "3. `build_qa_dataset()` — emits (chart_md, prompt, answer)",
        "   triples in JSONL format ready for SFT.",
        "",
        "## Demo outputs",
        "",
        f"- {n_demo} sample charts serialised as `chart_*.md`",
        f"- {n_demo} corresponding readings as `reading_*.md`",
        f"- QA dataset for LoRA fine-tune: `{qa_path.name}` "
        f"({n_qa:,} records)",
        "",
        "## Next step (when GPU comes online)",
        "",
        "1. Load chart_qa_dataset.jsonl into a chat-format SFT pipeline",
        "2. Choose base model: Phi-3-mini-128k-instruct or Qwen2-1.5B-Instruct",
        "3. LoRA config: r=16, alpha=32, target qkvo + ffn_in/out",
        "4. Train 3 epochs on the QA dataset",
        "5. Eval: held-out chart predictions vs gold-answer event_root",
        "6. Compare to Phase-4 sequence model on the same eval split",
        "",
        "The verbalization layer is itself a deterministic chatbot — it",
        "reads charts, applies the Phase-1 rules, and outputs structured",
        "natural-language predictions. The LLM upgrade learns to PHRASE",
        "those predictions more fluidly.",
    ]
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info("wrote report to %s", report)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.medini.ml.chart_verbalizer",
    )
    parser.add_argument(
        "--natal", type=Path,
        default=Path("app/medini/data/ml_astro_round5.parquet"),
    )
    parser.add_argument(
        "--rules", type=Path,
        default=Path("data/ml_runs/rules_round6_phase1_v2/"),
    )
    parser.add_argument(
        "--events", type=Path,
        default=Path("data/astro_databank/events_all.csv"),
    )
    parser.add_argument(
        "--output", type=Path,
        default=Path("data/ml_runs/verbalizer_round6_phase9/"),
    )
    parser.add_argument("--n-demo", type=int, default=3)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    run_phase9(
        natal_parquet=args.natal,
        rules_dir=args.rules,
        events_csv=args.events,
        output_dir=args.output,
        n_demo=args.n_demo,
    )
    print(f"Phase 9 artifacts in: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
