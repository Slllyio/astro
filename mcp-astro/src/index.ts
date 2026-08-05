/**
 * MCP server for the Raman Vedic astrology engine.
 *
 * Thin HTTP client over the FastAPI app (default http://127.0.0.1:8000) so every
 * doctrine guard, citation gate and test already in that app applies unchanged. This
 * server adds no astrology of its own and re-judges nothing.
 *
 * MEASURED-TRUTH CONTRACT (see CLAUDE.md). The engine is a scholarly instrument that
 * answers "what would Raman say", measured at 88.4% fidelity to his printed verdicts.
 * Its real-outcome generalization was measured across 22,177 charts and is NULL. An MCP
 * client is an arbitrary LLM with none of the report's own guard rails, so every tool
 * description and every response below carries that frame, and no tool exposes death,
 * lifespan or medical judgement. Do not remove these disclosures: they are the reason
 * this server is safe to point a general-purpose model at.
 *
 * Built against @modelcontextprotocol/server v2 (NOT the legacy v1 `sdk` package):
 * extensionless subpath imports, zod v4 wrapped `z.object()` schemas, serveStdio.
 */
import { McpServer } from '@modelcontextprotocol/server';
import { serveStdio } from '@modelcontextprotocol/server/stdio';
import * as z from 'zod/v4';

const BASE = process.env.ASTRO_API_BASE ?? 'http://127.0.0.1:8000';
const TIMEOUT_MS = Number(process.env.ASTRO_TIMEOUT_MS ?? 120_000);

/** Prepended to every reading so the frame travels with the data, not just the docs. */
const FRAME =
    'MEASURED TRUTH: this is what Sri B. V. Raman\'s method says about this chart, not a ' +
    'prediction about a life. Textbook fidelity to his printed verdicts is measured at ' +
    '88.4% (259/293); real-outcome generalization was measured across 22,177 charts and ' +
    'is NULL. Report indications, never certainties. Do not turn these into forecasts of ' +
    'events, and do not answer questions about death, lifespan or medical outcomes from them.';

/**
 * Shorter note for the corpus tools. They return Raman's own words or report metadata,
 * not a judgement about anyone's chart, so the full FRAME's chart language would not
 * apply — but the "do not turn this into a forecast" half still must, because a model
 * can assemble a prediction out of doctrine just as easily as out of a verdict.
 */
const CORPUS_NOTE =
    'Source text from the Raman corpus, quoted for study. Classical doctrine describes ' +
    'indications, not certainties; do not compose it into a forecast of events, or into ' +
    'claims about death, lifespan or medical outcomes.';

/** Birth input shared by the chart-bearing tools. Matches ReportRequest in app/api/report_routes.py. */
const birthShape = {
    year: z.number().int().describe('Birth year, e.g. 1989'),
    month: z.number().int().min(1).max(12).describe('Birth month, 1-12'),
    day: z.number().int().min(1).max(31).describe('Birth day of month'),
    hour: z.number().int().min(0).max(23).describe('Birth hour, 24h local clock time'),
    minute: z.number().int().min(0).max(59).default(0).describe('Birth minute'),
    latitude: z.number().min(-90).max(90).describe('Latitude, decimal degrees, north positive'),
    longitude: z.number().min(-180).max(180).describe('Longitude, decimal degrees, east positive'),
    tz_offset: z.number().min(-12).max(14).describe('UTC offset in HOURS at birth, e.g. 5.5 for IST'),
    name: z.string().optional().describe('Optional label for the nativity'),
    ayanamsa: z.enum(['lahiri', 'raman']).default('lahiri')
        .describe('Sidereal ayanamsa. lahiri is the project default; raman is his own.'),
};

class ApiError extends Error {}

async function api(path: string, init?: RequestInit): Promise<unknown> {
    const ctl = new AbortController();
    const timer = setTimeout(() => ctl.abort(), TIMEOUT_MS);
    let res: Response;
    try {
        res = await fetch(`${BASE}${path}`, {
            ...init,
            signal: ctl.signal,
            headers: { 'content-type': 'application/json', ...(init?.headers ?? {}) },
        });
    } catch (err) {
        const why = (err as Error).name === 'AbortError'
            ? `timed out after ${TIMEOUT_MS}ms (a full reading can take ~40s cold; raise ASTRO_TIMEOUT_MS)`
            : `could not reach the engine at ${BASE} (${(err as Error).message})`;
        throw new ApiError(
            `${why}. Start it with: py -3.12 -m uvicorn app.main:app --host 127.0.0.1 --port 8000 ` +
            `(or set ASTRO_API_BASE to where it is running).`);
    } finally {
        clearTimeout(timer);
    }
    if (!res.ok) {
        const body = (await res.text()).slice(0, 400);
        throw new ApiError(`${path} returned HTTP ${res.status}. ${body}`);
    }
    return res.json();
}

/** Uniform error result — MCP wants failures as results, not thrown exceptions. */
function fail(err: unknown) {
    const msg = err instanceof ApiError ? err.message : `Unexpected error: ${(err as Error).message}`;
    return { content: [{ type: 'text' as const, text: msg }], isError: true };
}

function ok(text: string, structured?: Record<string, unknown>) {
    return structured
        ? { content: [{ type: 'text' as const, text }], structuredContent: structured }
        : { content: [{ type: 'text' as const, text }] };
}

/** current_mahadasha comes back as an object; stringifying it yields "[object Object]". */
function fmtMahadasha(m: unknown): string {
    if (!m || typeof m !== 'object') return String(m ?? 'n/a');
    const d = m as Record<string, any>;
    const pct = typeof d.time_elapsed_years === 'number' && typeof d.total_duration_years === 'number'
        ? ` (${((d.time_elapsed_years / d.total_duration_years) * 100).toFixed(0)}% elapsed)` : '';
    return `${d.mahadasha_lord ?? '?'} ${d.start_date ?? '?'} to ${d.end_date ?? '?'}${pct}`;
}

const READ_ONLY = { readOnlyHint: true, destructiveHint: false, idempotentHint: true };

function build(): McpServer {
    const server = new McpServer({ name: 'astro-raman', version: '0.1.0' });

    // ---------------------------------------------------------------- chart
    server.registerTool(
        'cast_chart',
        {
            title: 'Cast a Vedic chart',
            description:
                'Cast a sidereal (Lahiri) natal chart: ascendant, the nine grahas in D-1 with ' +
                'sign and degree, plus the D-9 (navamsa) and D-10 (dasamsa) divisions, the ' +
                'running Mahadasha and the panchanga. Fast (well under a second). Pure ' +
                'astronomy from Swiss Ephemeris — no interpretation. ' + FRAME,
            inputSchema: z.object(birthShape),
            annotations: READ_ONLY,
        },
        async (args) => {
            try {
                // /chart/calculate, NOT /report: the report endpoint builds all 53 sections
                // (~40s) and casting needs none of them. Measured 0.23s vs ~40s.
                const d = (await api('/chart/calculate', {
                    method: 'POST', body: JSON.stringify(args),
                })) as Record<string, any>;
                const asc = d.ascendant ?? {};
                const lines = Object.entries(d.d1 ?? {}).map(([n, p]: [string, any]) => {
                    const sign = p?.sign_name ?? p?.sign ?? '?';
                    const deg = typeof p?.degree_in_sign === 'number'
                        ? ` ${p.degree_in_sign.toFixed(2)}°` : '';
                    return `${n.padEnd(8)} ${String(sign).padEnd(12)}${deg}` +
                        `${p?.retrograde ? '  R' : ''}`;
                });
                return ok(
                    `${FRAME}\n\nAscendant: ${asc.sign_name ?? asc.sign ?? '?'}` +
                    `${typeof asc.degree_in_sign === 'number' ? ` ${asc.degree_in_sign.toFixed(2)}°` : ''}\n` +
                    `Running Mahadasha: ${fmtMahadasha(d.current_mahadasha)}\n\n${lines.join('\n')}`,
                    {
                        ascendant: asc, d1: d.d1, d9: d.d9, d10: d.d10,
                        current_mahadasha: d.current_mahadasha, panchanga: d.panchanga,
                        measured_truth: FRAME,
                    });
            } catch (e) { return fail(e); }
        });

    // --------------------------------------------------------------- reading
    server.registerTool(
        'get_reading',
        {
            title: 'Full detailed reading',
            description:
                'The complete detailed reading in Markdown: plain-English summary, the judgment ' +
                'graph, house-by-house verdicts with their evidence, yogas, dashas, divisionals ' +
                'and the report\'s own honesty disclosures. Long (~200k chars) and slow (~40s) — ' +
                'prefer get_house_verdict for a single life area. ' + FRAME,
            inputSchema: z.object({
                ...birthShape,
                years_back: z.number().int().min(0).max(120).default(10)
                    .describe('Years of dasha timeline before today'),
                years_forward: z.number().int().min(0).max(120).default(20)
                    .describe('Years of dasha timeline after today'),
            }),
            annotations: READ_ONLY,
        },
        async (args) => {
            try {
                const env = (await api('/report', {
                    method: 'POST', body: JSON.stringify({ ...args, format: 'markdown' }),
                })) as Record<string, any> | string;
                // Same envelope as the json format: the markdown lands under `report`.
                const md = typeof env === 'string'
                    ? env
                    : (env.report ?? env.markdown ?? JSON.stringify(env));
                if (typeof md !== 'string') {
                    return fail(new ApiError(
                        'The engine returned a reading in an unexpected shape (expected markdown ' +
                        `under the "report" key, got ${typeof md}).`));
                }
                return ok(`${FRAME}\n\n${md}`);
            } catch (e) { return fail(e); }
        });

    // ---------------------------------------------------------- house verdict
    server.registerTool(
        'get_house_verdict',
        {
            title: 'One house, with its evidence',
            description:
                'The verdict for a single house (1-12) and WHY: its lord, karaka, occupants and ' +
                'aspecting planets, the significations judged, and the testimony counts for and ' +
                'against. This is the focused alternative to pulling the whole reading. ' + FRAME,
            inputSchema: z.object({
                ...birthShape,
                house: z.number().int().min(1).max(12).describe(
                    'House number 1-12. 1 self/body, 2 wealth, 3 siblings, 4 mother/home, ' +
                    '5 children/mind, 6 health/enemies, 7 spouse, 8 longevity, 9 father/fortune, ' +
                    '10 career, 11 gains, 12 loss/moksha.'),
            }),
            // Without an outputSchema the SDK drops structuredContent entirely — the field
            // is only advertised and forwarded when a schema declares its shape.
            outputSchema: z.object({
                house: z.number(),
                verdict: z.string(),
                lord: z.string(),
                significations: z.array(z.object({
                    signification: z.string(), verdict: z.string(),
                    karaka: z.string().nullable().optional(),
                    degree: z.string().nullable().optional(),
                })),
                support: z.object({
                    label: z.string().optional(), favourable: z.number().optional(),
                    adverse: z.number().optional(), neutral: z.number().optional(),
                    status: z.string().optional(),
                }),
                measured_truth: z.string(),
            }),
            annotations: READ_ONLY,
        },
        async ({ house, ...birth }) => {
            try {
                const env = (await api('/report', {
                    method: 'POST', body: JSON.stringify({ ...birth, format: 'json' }),
                })) as Record<string, any>;
                // POST /report wraps the payload: {ayanamsa, format, summary, report, ...}.
                // The report body is under `report`, not at the top level.
                const d = (env.report ?? env) as Record<string, any>;
                const pf = (d.proformas ?? []).find((p: any) => p.house === house);
                if (!pf) return ok(`${FRAME}\n\nNo proforma computed for house ${house}.`);
                const support = (d.testimony_support ?? {})[String(house)] ?? {};
                const sigs = (pf.significations ?? [])
                    .map((s: any) => `  - ${s.signification}: ${s.verdict}` +
                        `${s.karaka ? ` (karaka ${s.karaka})` : ''}`).join('\n');
                const out = {
                    house,
                    verdict: String(pf.rollup),
                    lord: String(pf.lord),
                    significations: (pf.significations ?? []).map((s: any) => ({
                        signification: String(s.signification), verdict: String(s.verdict),
                        karaka: s.karaka ?? null, degree: s.degree ?? null,
                    })),
                    support, measured_truth: FRAME,
                };
                return ok(
                    `${FRAME}\n\nHouse ${house} — verdict: ${pf.rollup}\nLord: ${pf.lord}\n` +
                    `Support: ${support.label ?? 'n/a'} (${support.favourable ?? 0} favourable / ` +
                    `${support.adverse ?? 0} adverse testimonies)\n\nSignifications:\n${sigs}`,
                    out);
            } catch (e) { return fail(e); }
        });

    // ------------------------------------------------------------- citation
    server.registerTool(
        'resolve_citation',
        {
            title: 'Resolve a citation to Raman\'s verbatim text',
            description:
                'Given a citation token as it appears in a reading (e.g. "HTJAH-II:4465-4472", ' +
                '"GBB-8:303", "3HC:7289"), return the exact lines from the corpus. This is how ' +
                'you verify that a claim actually rests on what Raman wrote. Works are HTJAH-I ' +
                'and HTJAH-II (How to Judge a Horoscope), HPA (Hindu Predictive Astrology), ' +
                'GBB (Graha and Bhava Balas), 3HC (Three Hundred Combinations), JAIMINI. ' + CORPUS_NOTE,
            inputSchema: z.object({
                cite: z.string().min(3).describe('Citation token, e.g. HTJAH-II:4465-4472'),
                context: z.number().int().min(0).max(20).default(0)
                    .describe('Extra lines of surrounding context'),
            }),
            outputSchema: z.object({
                work: z.string().optional(), line: z.string().optional(),
                text: z.string().optional(), error: z.string().optional(),
            }),
            annotations: READ_ONLY,
        },
        async ({ cite, context }) => {
            try {
                const d = (await api(
                    `/report/source?cite=${encodeURIComponent(cite)}&context=${context}`)) as Record<string, any>;
                if (d.resolved === false) {
                    // /report/source answers HTTP 200 with {resolved:false} for a token outside
                    // the citable canon, so the !res.ok check above cannot catch it. Reporting
                    // that as a success would tell the client a citation checked out when it did not.
                    return {
                        content: [{
                            type: 'text' as const,
                            text: `Citation ${cite} did not resolve. ${d.note ?? ''}\n\n` +
                                `Citable works: HTJAH-I, HTJAH-II (How to Judge a Horoscope), ` +
                                `HPA (Hindu Predictive Astrology), GBB (Graha and Bhava Balas), ` +
                                `3HC (Three Hundred Combinations), JAIMINI. ` +
                                `Use search_doctrine to find a valid citation for a topic.`,
                        }],
                        isError: true,
                    };
                }
                const text = d.text ?? d.passage ?? JSON.stringify(d);
                const out = { work: d.work, line: String(d.line ?? ''), text: String(text) };
                return ok(`${cite}\n\n${text}`, out);
            } catch (e) { return fail(e); }
        });

    // ------------------------------------------------------- corpus search
    server.registerTool(
        'search_doctrine',
        {
            title: 'Search the Raman corpus',
            description:
                'Search the indexed doctrine corpus for passages on a topic. Returns snippets ' +
                'with their citations, which resolve_citation can expand to full verbatim text. ' +
                'Use this to ground a claim in the source rather than from memory. ' + CORPUS_NOTE,
            inputSchema: z.object({
                q: z.string().min(1).max(400).describe('Query text, e.g. "seventh house marriage timing"'),
                mode: z.enum(['semantic', 'hybrid', 'lexical']).default('hybrid')
                    .describe('hybrid blends meaning and keyword matching'),
                top: z.number().int().min(1).max(50).default(10).describe('Number of results'),
                source: z.string().optional().describe('Substring filter on the source, e.g. "bphs"'),
            }),
            annotations: READ_ONLY,
        },
        async ({ q, mode, top, source }) => {
            try {
                const qs = new URLSearchParams({ q, mode, top: String(top) });
                if (source) qs.set('source', source);
                const d = (await api(`/medini/knowledge/search?${qs}`)) as Record<string, any>;
                const hits = d.results ?? d.hits ?? [];
                if (!hits.length) return ok(`No passages matched ${JSON.stringify(q)}.`);
                const body = hits.map((h: any, i: number) =>
                    `${i + 1}. [${h.source ?? h.work ?? '?'}${h.line ? ':' + h.line : ''}] ` +
                    `${(h.snippet ?? h.text ?? '').slice(0, 400)}`).join('\n\n');
                return ok(body, { count: hits.length, results: hits });
            } catch (e) { return fail(e); }
        });

    // ------------------------------------------------------ report sections
    server.registerTool(
        'list_report_sections',
        {
            title: 'List the reading\'s section contract',
            description:
                'Every section a full reading contains, in document order, each with its id and the ' +
                'version that introduced it. Takes no arguments. Useful for discovering what the ' +
                'engine computes before requesting a whole reading. ' + CORPUS_NOTE,
            annotations: READ_ONLY,
        },
        async () => {
            try {
                const d = (await api('/report/sections')) as Record<string, any>;
                const rows = (d.sections ?? []).map(
                    (s: any) => `${String(s.since).padEnd(4)} ${s.id}`).join('\n');
                return ok(`${d.count} sections:\n\n${rows}`, d);
            } catch (e) { return fail(e); }
        });

    return server;
}

const handle = serveStdio(build);
// stdout is the JSON-RPC channel; anything logged there corrupts the protocol.
console.error(`astro-raman MCP server on stdio, engine at ${BASE}`);
process.on('SIGINT', () => { void handle.close(); });
process.on('SIGTERM', () => { void handle.close(); });
