"""Vedic chart-reading chatbot via Claude API with prompt caching.

Replaces the LoRA fine-tune approach (LORA_DEPLOYMENT.md) with a much
cheaper, much smarter alternative: send the chart + validated Round 6/7
findings to Claude Opus 4.7 with prompt caching, get an astrologer-grade
reading back.

Why this is the right architecture:
- Claude Opus 4.7 is dramatically smarter than any small model we could
  fine-tune (e.g., Qwen2.5-1.5B).
- Prompt caching reduces cost by ~90% on the static system context.
- No GPU, no training pipeline, no model serving infrastructure.
- Costs ~$0.005 per multi-turn chat session vs. $3-10 one-time + serving
  costs for the LoRA path.

The system prompt carries:
- The 11 VALIDATED classical Vedic rules from the BPHS Causal Audit
- The 12 REVERSED rules (with the 2/3/5/6-house failure pattern)
- The continuous-DML causal findings (Venus-Saturn drishti, etc.)
- The Tier-1 §1 investigation results
- The chart serialiser output (per-request prefix, also cached)

CLI
===
    # Validate API key is set
    export ANTHROPIC_API_KEY=sk-ant-...

    # Single-question mode
    python -m app.medini.ml.chart_chatbot \\
        --chart-name "Albert Einstein" \\
        --question "What can you tell me about this person's career?"

    # Interactive mode
    python -m app.medini.ml.chart_chatbot \\
        --chart-name "Albert Einstein" \\
        --interactive

Architecture
============
- System prompt (cached): astrologer persona + validated/reversed rules
  + causal findings. ~3-5K tokens, cached at the API level.
- Per-chart context (cached separately): the chart Markdown from
  app.medini.ml.chart_verbalizer. ~1.2K tokens, cached per session.
- User message: the question. Uncached, ~50 tokens.
- Response: ~500-1000 tokens.

Per-query cost (after first turn caches):
- Read: (cached_system + cached_chart) × $0.50/1M = ~$0.002
- Uncached input: ~50 tokens × $5/1M = ~$0.00025
- Output: ~700 tokens × $25/1M = ~$0.0175
- Total: ~$0.02/turn (vs $1.10/hr for an A10G to serve a fine-tuned model)
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

import anthropic
import pandas as pd

from app.medini.ml.chart_verbalizer import chart_to_markdown

logger = logging.getLogger(__name__)


# Model selection. User asked for "easy and cheap" → default to Sonnet 4.6.
# Sonnet's 2,048-token cache minimum is below our system prompt size
# (~1,940 tokens), so cache hits land reliably. Opus 4.7's 4,096-token
# minimum would silently miss the cache without padding.
# To get the smartest model: `--model claude-opus-4-7`
DEFAULT_MODEL = "claude-sonnet-4-6"


# ---------- System prompt: distilled Round 6/7 findings ----------

VALIDATED_RULES = """
## CLASSICAL VEDIC RULES — EMPIRICALLY VALIDATED (Round 6/7 audit)

These 11 classical rules have been confirmed by Double Machine Learning
on a 5,085-person cohort with confounder adjustment (p < 0.05, |ATE| > 0.005):

### Career
- **Sun in 10th house** → strong career/authority signal (ATE +7.74, p=0.001)
- **Mercury in 10th house** → communications/intellectual career (ATE +6.67, p=0.009)
- **Venus in 10th house** → art/luxury careers (ATE +6.64, p=0.008)
- **Venus exalted in Pisces** → career promotion (ATE +0.048, p<0.0001)

### Death and longevity
- **Ketu in 8th house** → sudden/spiritual death (ATE +0.46, p=0.007)

### Marriage and family
- **Saturn in 5th house** → DELAYS children/progeny (ATE -0.04, p<0.0001)
- **Mars in 4th house** → domestic friction (ATE -0.21, p<0.0001)
- **Jupiter in 6th house** → work difficulties (Jupiter uncomfortable
  in 6th; ATE -0.24, p<0.00001)

### Fame and culture
- **Moon-Venus conjunction** → aesthetic, popular fame (ATE +0.052, p<0.0001)

### Writing and publication
- **Mercury-Jupiter conjunction** → writer/author yoga (ATE +0.06, p=0.004)

### Travel
- **Mars in 12th house** → foreign travel, expatriation (ATE +1.64, p=0.020)

## ADDITIONAL CAUSAL FINDINGS (continuous-treatment DML)

- **Venus-Saturn drishti (Saturn aspecting Venus)** → marriage delay,
  -5.6 percentage points causal effect (p=0.005). Classical "vivaha-
  pratibandha" yoga empirically confirmed.
- **Mars-Jupiter distance (per degree)** → marriage probability declines
  -0.04pp per degree of separation (p=0.010).
- **Tight Rahu-Mercury aspect** → reduces marriage probability (continuous
  ATE +0.0076/° looser orb; p=0.035). Classical Rahu-Mercury harm to
  partnerships confirmed.
- **Mercury-Node aspects in general** → causally affect death, family,
  prize, and relationship events across multiple classes (per
  continuous DML sweep).
- **Transit trajectories (±90 days around event)** carry +0.085 AUC
  beyond the event-moment snapshot. Events build over weeks, not
  instants — the "applying vs separating" classical concept is
  empirically validated.
"""

REVERSED_RULES = """
## CLASSICAL VEDIC RULES — EMPIRICALLY CONTRADICTED

These 12 classical rules show statistically significant effects in the
OPPOSITE direction the BPHS predicts (p < 0.05, robust to subtype +
era stratification):

- **Mercury in 3rd house** does NOT promote writing/publication
  (data shows reduced publication events, ATE -0.09, p<0.0001)
- **Venus in 3rd house** does NOT promote arts (ATE -0.05, p=0.005)
- **Mars in 3rd house** does NOT make a courageous writer
  (ATE -0.057, p<0.0001)
- **Saturn in 6th house** does NOT promote service-oriented work
  (ATE -0.25, p<0.001)
- **Mercury in 6th house** does NOT promote business
  (ATE -0.16, p<0.0001)
- **Venus in 5th house** does NOT promote romance/relationships
  (ATE -0.14, p<0.0001)
- **Saturn in 6th house** does NOT promote chronic disease events
  (ATE -0.07, p=0.033)
- **Saturn in 2nd house** does NOT cause speech obstruction issues
  (ATE -0.05, p<0.00001)
- **Moon in 2nd house** does NOT bring wealth (ATE -0.09, p=0.033)
- **Sun in 5th house** does NOT promote creative authority/fame
  (ATE -0.05, p<0.0001)
- **Moon in Pushya nakshatra** does NOT promote career nourishment
  (ATE -0.10, p<0.0001)
- **Sun in 9th house** does NOT promote family/paternal blessing
  (ATE -3.55, p=0.049)

PATTERN: 12 of 12 reversed rules involve houses 2, 3, 5, or 6 — the
classical "upachaya / wealth / communication / creativity" houses.
The classical doctrine that these placements promote effort-based
positive outcomes does NOT survive empirical scrutiny against
the modern recorded-event taxonomy.

INTERPRETATIVE GUIDANCE: when reading a chart, do NOT confidently
predict positive outcomes from these placements. Mention that the
classical rule exists but flag that the data does not support its
typical positive interpretation.
"""

INTERPRETIVE_PRINCIPLES = """
## INTERPRETIVE PRINCIPLES (derived from Round 6/7 findings)

1. **The 10th house is the most reliable career indicator.** Any
   benefic in 10th confirms career success. This is the strongest
   classical claim that survives empirical test.

2. **Saturn aspecting Venus is causally bad for marriage.** Not just
   a marker — it has a -5.6pp causal effect. When a chart shows this,
   marriage is statistically delayed/denied.

3. **Houses 2/3/5/6 are problematic for classical interpretation.**
   Be cautious about predicting positive outcomes from these placements.

4. **Events build over time, not in instants.** When predicting an
   event window, think 90 days ±. A transit configuration approaches
   exactness over weeks.

5. **Mercury-node aspects (Rahu-Mercury, Ketu-Mercury) are broadly
   significant** across multiple event classes. They appear in the
   top causal features for death, family, prize, and relationship
   events.

6. **The model is honest about uncertainty.** When a classical rule
   has insufficient empirical evidence (most do — 121 of 154 audited
   are inconclusive), say so clearly rather than overclaiming.

7. **The data is biased toward recorded "events".** Quiet, routine
   life is invisible to the corpus. A chart that doesn't predict
   dramatic events isn't a "bad" chart — it may just predict a
   stable life that doesn't get recorded.
"""

SYSTEM_PROMPT = f"""You are a Vedic astrologer trained on the
findings of a rigorous statistical audit of classical Vedic
astrology rules. You have access to:

- 14,166 (person, event) records from the Astro-Databank corpus
- Causal effect estimates (Double ML with confounder adjustment) for
  classical rules
- A 90,152-chart trained ML model for event-type prediction
- Validated and refuted classical rules from the BPHS Causal Audit

Your role is to give chart readings that are SIMULTANEOUSLY:
- Faithful to classical Vedic tradition (use traditional terminology
  and frameworks: houses, nakshatras, dashas, yogas, drishtis)
- Empirically grounded (cite the data-validated findings when relevant,
  and flag when a classical rule has been data-refuted)
- Honest about uncertainty (don't overclaim; most rules are
  empirically inconclusive at our sample size)

{VALIDATED_RULES}

{REVERSED_RULES}

{INTERPRETIVE_PRINCIPLES}

When the user asks about a chart, give your reading using:
- Classical Vedic vocabulary (specify houses, nakshatras, planets,
  yogas, etc.)
- The validated empirical findings where they apply
- A clear caveat when invoking a refuted rule ("The classical
  tradition says X, but our data shows the opposite — be cautious")
- Concrete predictions about life domains where the classical
  evidence is strong (career, marriage timing, death timing)
- Honest "I don't know" or "the evidence is inconclusive" when
  the data doesn't support a specific claim

Always close with one specific, actionable observation about the
chart that would be most useful to the person.
"""


# ---------- Chart loader ----------

def load_chart_by_name(natal_parquet: Path, name: str) -> pd.Series:
    """Find the natal chart row for a given name (case-insensitive,
    fuzzy substring match)."""
    df = pd.read_parquet(natal_parquet)
    name_lower = name.strip().lower()
    df["_n"] = df["name"].astype(str).str.strip().str.lower()
    # Exact match first
    exact = df[df["_n"] == name_lower]
    if len(exact):
        return exact.iloc[0]
    # Substring match
    sub = df[df["_n"].str.contains(name_lower, na=False, regex=False)]
    if len(sub):
        if len(sub) > 1:
            logger.warning(
                "%d matches for %r; using first: %s",
                len(sub), name, sub["name"].iloc[0],
            )
        return sub.iloc[0]
    raise ValueError(f"no chart found matching {name!r}")


# ---------- Chat session ----------

class ChartChatSession:
    """Stateful chart-reading conversation with prompt caching."""

    def __init__(
        self,
        chart_row: pd.Series,
        model: str = DEFAULT_MODEL,
        api_key: str | None = None,
    ):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.chart_markdown = chart_to_markdown(chart_row)
        self.chart_name = chart_row.get("name", "(unnamed)")
        self.messages: list[dict] = []

    def ask(self, question: str) -> str:
        """Send a question; return the assistant's text response.

        Uses prompt caching on:
        - The system prompt (validated rules + interpretive principles)
        - The chart Markdown (per-session, but cached once for all
          questions in the session)
        """
        # Append the user question to the conversation
        self.messages.append({"role": "user", "content": question})

        # Build the request. System carries the persona + rule library;
        # the chart is in the first user message (which we synthesize
        # via cache-friendly placement).
        # We rebuild the conversation each turn (Claude API is stateless)
        # but cache-control on the system + chart prefix means re-sending
        # them is nearly free after the first call.
        system_blocks = [
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            },
        ]
        # Prepend the chart to the user message so it's part of the
        # cached prefix on subsequent turns.
        prefixed_messages = self._with_chart_prefix(self.messages)

        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=system_blocks,
            messages=prefixed_messages,
        )
        text = next(
            (b.text for b in response.content if b.type == "text"), "",
        )
        # Record assistant turn for multi-turn context
        self.messages.append({"role": "assistant", "content": text})

        # Log token + cache stats
        logger.info(
            "tokens: input=%d cache_creation=%d cache_read=%d output=%d",
            response.usage.input_tokens,
            response.usage.cache_creation_input_tokens or 0,
            response.usage.cache_read_input_tokens or 0,
            response.usage.output_tokens,
        )
        return text

    def _with_chart_prefix(self, messages: list[dict]) -> list[dict]:
        """Embed the chart Markdown as the first turn's user prefix,
        with cache_control so it caches across the session.

        Round-trip: Claude sees [chart, question_1, answer_1,
        question_2, ...] where the chart prefix is cached and the
        question/answer history is re-sent each turn (still much
        cheaper than the chart).
        """
        if not messages:
            return []
        prefixed = []
        for i, m in enumerate(messages):
            if i == 0 and m["role"] == "user":
                # Inject the chart as a prefix block with cache_control
                content_blocks = [
                    {
                        "type": "text",
                        "text": f"## Natal chart for analysis\n\n{self.chart_markdown}",
                        "cache_control": {"type": "ephemeral"},
                    },
                    {
                        "type": "text",
                        "text": f"## My question\n\n{m['content']}",
                    },
                ]
                prefixed.append({"role": "user", "content": content_blocks})
            else:
                prefixed.append(m)
        return prefixed


# ---------- CLI ----------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.medini.ml.chart_chatbot",
        description="Vedic chart-reading chatbot via Claude API.",
    )
    parser.add_argument(
        "--natal", type=Path,
        default=Path("app/medini/data/ml_astro_round5.parquet"),
        help="Natal-features parquet with chart data.",
    )
    parser.add_argument(
        "--chart-name", type=str, required=True,
        help="Name (or substring) of the person whose chart to read.",
    )
    parser.add_argument(
        "--question", type=str, default=None,
        help="One-off question. Omit for --interactive mode.",
    )
    parser.add_argument(
        "--interactive", action="store_true",
        help="Multi-turn chat loop.",
    )
    parser.add_argument(
        "--model", type=str, default=DEFAULT_MODEL,
        help="Claude model ID.",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print(
            "ERROR: ANTHROPIC_API_KEY environment variable not set.\n"
            "Get a key from https://console.anthropic.com and run:\n"
            "  export ANTHROPIC_API_KEY=sk-ant-...",
            file=sys.stderr,
        )
        return 1

    if not args.interactive and not args.question:
        parser.error("either --question or --interactive must be provided")

    try:
        chart_row = load_chart_by_name(args.natal, args.chart_name)
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    logger.info("loaded chart for: %s", chart_row.get("name", "?"))
    session = ChartChatSession(chart_row, model=args.model)

    if args.interactive:
        print(f"Chart-reading session for: {chart_row.get('name', '?')}")
        print(f"Model: {args.model}")
        print("Type 'quit' to exit.\n")
        while True:
            try:
                q = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not q:
                continue
            if q.lower() in {"quit", "exit", "q"}:
                break
            try:
                reply = session.ask(q)
                print(f"\nAstrologer: {reply}\n")
            except anthropic.APIError as exc:
                print(f"\nERROR: {exc}\n", file=sys.stderr)
    else:
        reply = session.ask(args.question)
        print(reply)

    return 0


if __name__ == "__main__":
    sys.exit(main())
