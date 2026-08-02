# Sharing the reading app — quick-share guide

How to let other people use the फलादेशः reading app from your machine, safely and at $0
per reading. This is the "quick share link" flow: your computer runs the app, a tunnel
gives it a temporary public HTTPS URL, and you send that URL to the people you trust.

## What visitors get

- The full page-turning manuscript report at `/report/page` — **mobile compatible**
  (portrait phones get a single-column, swipe-to-turn book).
- The **chart-specific feedback questions** on the last leaf — answers land in your local
  `astro.db` (`chart_feedback` table), anonymously.
- The **Ask panel** and the walled **AI-interpretation panel** — served by the LOCAL
  Ollama model on your GPU. Zero per-reading cost, nothing leaves your machine.

**What to tell visitors about speed.** The deterministic report — every chart, table, the
house-by-house reading and the Nichod — renders in ~2s and is identical whichever model
serves. Only the narrated panels wait on the GPU. On `gemma4:12b` (the default), measured on
the dev machine: Ask ≈ 15s, "read as one story" ≈ 25s, and Hindi roughly doubles it because
the answer is generated in English, guarded, then translated. One GPU means concurrent
visitors queue. On the small model those drop to ~7s at markedly worse citation quality
(see the table below).

**Some answers will be engine prose, by design.** The guard refuses any draft carrying
prediction/decree language ("promises", "will", a dated indication) and serves the report's
own deterministic text instead — measured at ~12% of answers on the 12B. A visitor seeing
plain prose in the Ask panel is the safety net working, not a failure.

## One-time setup

1. **Ollama** (already installed): the daemon serves on `http://localhost:11434`. The
   narrative model is `REPORT_LLM_MODEL`, which defaults to the **stock `gemma4:12b`** —
   NOT the project's `astro-analyst` LoRA.

   Measured head-to-head 2026-08-03 on 34 genuinely held-out rows, scored by the same guard
   the serving path uses (`eval_analysis_llm.py`):

   | | citation-clean | guard pass | crisp pass |
   |---|---|---|---|
   | `gemma4:12b` (stock, no fine-tune) | **85.3%** | 88.2% | 70.6% |
   | `astro-analyst` (the 1.5B LoRA) | 44.1% | 73.5% | 47.1% |
   | Claude teacher (reference) | 91.2% | 100% | 100% |

   The stock 12B wins on every axis, including the voice and crispness the LoRA existed to
   teach. The 1.5B is capacity-limited for citation precision across ~20 facts — corpus
   quality was not the constraint, since the same corpus's teacher rows score 91.2%.
   `OLLAMA_MODEL` stays on the fast small model for high-frequency paths; only the report's
   narrative surfaces use `REPORT_LLM_MODEL`.

   > **Superseded numbers.** This guide previously quoted "95% guard / 0.966 grounding" for
   > `astro-analyst`. That eval was contaminated: training read every corpus row while the
   > eval held out ~1/8 by `person_id` hash, so the student was scored on 74 of 588 rows it
   > had been fine-tuned on. `drop_holdout` (2026-08-03) fixed it; the table above is the
   > first uncontaminated measurement.

2. **Env for the shared run** — the app defaults are already safe
   (`REPORT_LLM_BACKEND=ollama`), so the only flag you need is:

   ```powershell
   $env:REPORT_LLM_ENABLED = "true"     # Ask + AI-interpret on the local model
   ```

   **If you point `REPORT_LLM_MODEL` at a reasoning model, keep its two companions set.**
   `gemma4:12b` advertises `thinking` in its `/api/show` capabilities, and on a ~3.1k-token
   evidence prompt it otherwise spends its ENTIRE token budget in the thinking channel and
   returns `done_reason="length"` with an EMPTY response — which the client raises as
   `OllamaUnavailable`, silently degrading every single answer to deterministic prose while
   the app still looks perfectly healthy. The config defaults already carry them
   (`REPORT_LLM_THINK=false`, `REPORT_LLM_NUM_CTX=8192`, `REPORT_LLM_TIMEOUT_SECONDS=120`);
   don't drop them when overriding the model. They are harmless on non-reasoning models.

   To serve the fast small model instead (see the latency note below):

   ```powershell
   $env:REPORT_LLM_MODEL = "astro-analyst"   # or qwen2.5:1.5b for the stock small model
   ```

   Do **NOT** set `ANTHROPIC_API_KEY` in the shared process. The public path never needs
   it, and leaving it unset makes overspend impossible by construction. (If Ollama is not
   running, both panels degrade gracefully — the reading itself is fully deterministic.)

## Run + tunnel

```powershell
# 1. the app
py -3.12 -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# 2. the tunnel (pick one)
cloudflared tunnel --url http://localhost:8000     # no account needed, free
# or
ngrok http 8000
```

Share the printed `https://….trycloudflare.com` (or ngrok) URL +
the path `/report/page`.

## Safety notes (read before sharing)

- **The tunnel exposes YOUR machine.** Keep it short-lived, share only with people you
  trust, and Ctrl-C the tunnel when done. The URL dies with it.
- **SQLite is fine at this scale** (WAL mode, a handful of concurrent readers). The
  feedback rows are in `astro.db` — back it up if the answers matter to you.
- The heavy endpoints (`POST /report`, `/report/ask`, `/report/insights`, `/report/explain`,
  `/report/ai-interpret`) each cost seconds of YOUR CPU/GPU per call — and on a 12B, 15-25s
  each, holding the GPU for that whole time. A hostile visitor could keep your machine busy —
  another reason for trusted-circle sharing, not a public link on social media.
- **Check the birth-details leaf renders before you send the link.** It is the one leaf with
  a non-standard layout (a full-width language strip above the triptych), and a CSS
  regression there once left visitors with a language dropdown and no birth fields at all,
  on a leaf that cannot scroll. Cast one chart yourself through the tunnel URL — not just
  localhost — before sharing.
- The honesty frame ships everywhere by design: the report's information-content
  disclosure, the Ask panel's honesty note, and the AI panel's disclaimer banner. Do not
  edit those out when sharing — they are what makes the reading honest
  (see CLAUDE.md ★★ Measured Truth).

## Reading the feedback later

```powershell
py -3.12 -c "import sqlite3; [print(r) for r in sqlite3.connect('astro.db').execute(
  'select created_at, chart_key, question_id, answer, free_text from chart_feedback order by id desc limit 20')]"
```

## When you outgrow the tunnel

Real hosting (Render/Fly/VPS) needs: `ENVIRONMENT=prod`, a rotated `SECRET_KEY`,
Postgres via `DATABASE_URL`, Google OAuth redirect updated to the public domain, and a
host with a GPU (or CPU-only Ollama with a small model) for the LLM panels. That is a
separate exercise — this doc is the quick path.
