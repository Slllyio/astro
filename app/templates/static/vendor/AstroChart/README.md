# AstroChart (vendored)

**Source**: https://github.com/AstroDraw/AstroChart (commit at clone time, depth=1)
**Version**: 3.0.2 (per upstream `package.json`)
**License**: MIT (see `LICENSE` in this directory)
**Vendored**: 2026-05-26

## What it is

Pure-TypeScript SVG astrology chart renderer. Takes planet positions as input,
draws the zodiac wheel + planet glyphs + aspect lines. **Does NOT compute
positions** — feed it values from our existing `app.core.ephemeris_engine`.

## What's here

- `astrochart.js` (97 KB) — the pre-built UMD bundle from upstream's `dist/`. No
  build step needed; drop directly into a `<script>` tag.
- `LICENSE` — MIT.
- `README.md` — this file.

The full upstream repo (tests, docs, source TS, webpack config) is NOT vendored
— only the runtime artifact.

## How to wire up (when ready)

1. **Mount static files in FastAPI** (currently NOT wired; project ships
   templates inline without a static mount):

   ```python
   # app/main.py
   from fastapi.staticfiles import StaticFiles
   app.mount(
       "/static",
       StaticFiles(directory="app/templates/static"),
       name="static",
   )
   ```

2. **Reference from a Jinja template**:

   ```html
   <script src="/static/vendor/AstroChart/astrochart.js"></script>
   <div id="chart-paper"></div>
   <script>
     const chart = new astrology.Chart('chart-paper', 800, 800);
     const radix = chart.radix({
       planets: {
         "Sun":    [{{ sun_lon }}],
         "Moon":   [{{ moon_lon }}],
         "Mars":   [{{ mars_lon }}],
       },
       cusps: [{{ asc }}],
     });
   </script>
   ```

3. **Natural integration target**: `app/templates/nadi_chart.html` (currently
   form-only; would benefit from a chart wheel below the JSON output).

## Upgrade path

To pull a newer upstream release:

```bash
cd /tmp && git clone --depth 1 https://github.com/AstroDraw/AstroChart.git
cp AstroChart/dist/astrochart.js  e:/astro/app/templates/static/vendor/AstroChart/
cp AstroChart/LICENSE             e:/astro/app/templates/static/vendor/AstroChart/
# update Version + Vendored date in this README
```

## Not vendored on purpose

- npm dependencies (project has no `package.json`)
- TypeScript source (we use the pre-built bundle)
- Tests/docs/examples (browse upstream on GitHub when needed)
