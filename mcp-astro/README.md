# astro-raman MCP server

Exposes the Raman Vedic astrology engine to any MCP client. Six read-only tools: cast a
chart, get a full reading, get one house with its evidence, resolve a citation to Raman's
verbatim text, search the doctrine corpus, and list the report's section contract.

It is a thin HTTP client over the FastAPI app, so every doctrine guard, citation gate and
test already in that app applies unchanged. The server adds no astrology of its own and
re-judges nothing.

## Why the disclosures are not decoration

`CLAUDE.md` binds this project to reporting both accuracy axes side by side: textbook
fidelity to Raman's printed verdicts is measured at **88.4%** (259/293), and real-outcome
generalization, measured across **22,177 charts**, is **NULL**.

The report's own LLM surfaces enforce that with a regex tripwire and a refusal gate. **An
MCP client has none of those guards** — it is an arbitrary model that could take
"H7 afflicted" and tell someone their marriage will fail. So the server carries the frame
itself:

- every tool description ends with the Measured-Truth statement (chart tools) or a corpus
  note (doctrine tools),
- every chart response repeats it in the body, and `structuredContent` carries a
  `measured_truth` field,
- **no tool exposes death, lifespan or medical judgement**, and the smoke test asserts none
  ever appears.

Do not strip these. They are the reason this server is safe to point a general model at.

## Setup

Requires Node >= 20 and the engine running:

```bash
py -3.12 -m uvicorn app.main:app --host 127.0.0.1 --port 8000   # from the repo root
cd mcp-astro && npm install
node smoke.mjs        # 14 checks, needs the engine up
```

Register with Claude Code:

```bash
claude mcp add astro-raman -- npx tsx E:/astro/mcp-astro/src/index.ts
```

Or in a client's MCP config:

```json
{
  "mcpServers": {
    "astro-raman": {
      "command": "npx",
      "args": ["tsx", "E:/astro/mcp-astro/src/index.ts"],
      "env": { "ASTRO_API_BASE": "http://127.0.0.1:8000" }
    }
  }
}
```

`ASTRO_API_BASE` (default `http://127.0.0.1:8000`) and `ASTRO_TIMEOUT_MS` (default 120000)
are the only knobs.

## Tools

| Tool | Cost | Notes |
|---|---|---|
| `cast_chart` | ~30ms | D-1/D-9/D-10, ascendant, running Mahadasha, panchanga |
| `get_house_verdict` | ~2.6s | One house: lord, significations, testimony counts |
| `get_reading` | ~3s | The complete reading in Markdown, ~200k chars |
| `resolve_citation` | ~50ms | Citation token to verbatim corpus text |
| `search_doctrine` | ~350ms | RAG search, returns snippets with citations |
| `list_report_sections` | ~20ms | The 53-section contract |

`cast_chart` deliberately calls `/chart/calculate`, not `/report`: the report endpoint
builds all 53 sections, and casting needs none of them. Measured 0.23s vs the full build.

## Notes for the next person

Built against **`@modelcontextprotocol/server` v2**, not the legacy v1 `@modelcontextprotocol/sdk`
package. The differences bite:

- imports have **no `.js` suffix** (`@modelcontextprotocol/server/stdio`)
- `inputSchema` takes a **wrapped `z.object({...})`**, not a raw shape
- **zod v4 only** (>= 4.2.0); v3 typechecks fine and fails at runtime
- `.tool()` is removed; use `registerTool`
- `serveStdio(factory)` replaces manual transport wiring
- **stdout is the JSON-RPC channel** — log with `console.error` or you corrupt the protocol

Four bugs here were invisible to typechecking and only appeared over the wire, which is
what `smoke.mjs` exists to catch:

1. `structuredContent` is **silently dropped** unless the tool declares an `outputSchema`.
2. `POST /report` wraps its payload — the body is under `report`, so a top-level
   `d.proformas` lookup returns nothing and the tool reports "no proforma computed".
3. `current_mahadasha` is an object; interpolating it yields `[object Object]`.
4. `/report/source` answers **HTTP 200 with `{resolved: false}`** for an unknown citation,
   so an `res.ok` check calls a failed lookup a success.

`evaluation.xml` holds 10 questions whose answers were computed by driving the real server,
not written from memory.
