/**
 * End-to-end smoke test: drives the server over real MCP stdio, exactly as a client would.
 *
 * This exists because every bug found while building this server was invisible to
 * typechecking and only appeared over the wire: `structuredContent` silently dropped when
 * no outputSchema is declared, the /report envelope hiding proformas under `report`,
 * `current_mahadasha` rendering as "[object Object]", and an unresolvable citation
 * returning HTTP 200 so it looked like a success.
 *
 * Requires the engine running:  py -3.12 -m uvicorn app.main:app --host 127.0.0.1 --port 8000
 * Run:                          node smoke.mjs
 */
import { spawn } from 'node:child_process';

const MAINPURI = {
    year: 1989, month: 10, day: 12, hour: 10, minute: 2,
    latitude: 27.23, longitude: 79.03, tz_offset: 5.5, name: 'Mainpuri',
};

const srv = spawn('npx', ['tsx', 'src/index.ts'], { stdio: ['pipe', 'pipe', 'pipe'], shell: true });
let buf = '';
const pending = new Map();
srv.stdout.on('data', (d) => {
    buf += d;
    let i;
    while ((i = buf.indexOf('\n')) >= 0) {
        const line = buf.slice(0, i).trim();
        buf = buf.slice(i + 1);
        if (!line) continue;
        try {
            const m = JSON.parse(line);
            if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); }
        } catch { /* non-JSON line on stdout would itself be a bug; ignore here */ }
    }
});

let id = 0;
const call = (method, params) => new Promise((res, rej) => {
    const myId = ++id;
    pending.set(myId, res);
    srv.stdin.write(JSON.stringify({ jsonrpc: '2.0', id: myId, method, params }) + '\n');
    setTimeout(() => rej(new Error(`timeout on ${method}`)), 120_000);
});

let pass = 0, fail = 0;
function check(name, cond, detail = '') {
    if (cond) { pass++; console.log(`  PASS  ${name}`); }
    else { fail++; console.log(`  FAIL  ${name}${detail ? ' — ' + detail : ''}`); }
}

try {
    const init = await call('initialize', {
        protocolVersion: '2026-07-28', capabilities: {},
        clientInfo: { name: 'smoke', version: '1' },
    });
    srv.stdin.write(JSON.stringify({ jsonrpc: '2.0', method: 'notifications/initialized' }) + '\n');
    check('initialize handshake', init.result?.serverInfo?.name === 'astro-raman');

    const list = await call('tools/list', {});
    const tools = list.result?.tools ?? [];
    check('six tools advertised', tools.length === 6, `got ${tools.length}`);
    check('every tool carries a disclosure',
        tools.every(t => /MEASURED TRUTH|Raman corpus/.test(t.description ?? '')));
    check('every tool marked read-only',
        tools.every(t => t.annotations?.readOnlyHint === true));
    check('no death/lifespan tool exposed',
        !tools.some(t => /death|lifespan|longevity|medical/i.test(t.name)));

    const chart = await call('tools/call', { name: 'cast_chart', arguments: MAINPURI });
    const chartText = chart.result?.content?.[0]?.text ?? '';
    check('cast_chart: Scorpio ascendant (known fixture)', /Ascendant: Scorpio/.test(chartText));
    check('cast_chart: mahadasha rendered, not [object Object]',
        /Running Mahadasha: \w+ \d{4}/.test(chartText) && !/\[object Object\]/.test(chartText));

    const h7 = await call('tools/call', { name: 'get_house_verdict', arguments: { ...MAINPURI, house: 7 } });
    check('house verdict: structuredContent survives', !!h7.result?.structuredContent);
    check('house verdict: H7 lord is Venus (known fixture)',
        h7.result?.structuredContent?.lord === 'Venus',
        `got ${h7.result?.structuredContent?.lord}`);
    check('house verdict: verdict present',
        typeof h7.result?.structuredContent?.verdict === 'string');

    const cite = await call('tools/call', { name: 'resolve_citation', arguments: { cite: 'HTJAH-II:4465-4472' } });
    check('citation resolves to verbatim text',
        !cite.result?.isError && (cite.result?.content?.[0]?.text ?? '').length > 120);

    const bad = await call('tools/call', { name: 'resolve_citation', arguments: { cite: 'NOPE-9:1' } });
    check('unresolvable citation reports isError (API returns HTTP 200)',
        bad.result?.isError === true);

    const search = await call('tools/call', { name: 'search_doctrine', arguments: { q: 'seventh house marriage', top: 3 } });
    check('doctrine search returns passages',
        !search.result?.isError && (search.result?.content?.[0]?.text ?? '').length > 60);

    const secs = await call('tools/call', { name: 'list_report_sections', arguments: {} });
    check('section list returns the contract',
        /\d+ sections:/.test(secs.result?.content?.[0]?.text ?? ''));
} catch (err) {
    fail++;
    console.log(`  FAIL  harness — ${err.message}`);
    console.log('        Is the engine running on http://127.0.0.1:8000 ?');
} finally {
    srv.kill();
}

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
