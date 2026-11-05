"""Natal decode API — planets at birth, decoded with disclosed provenance.

Deliberately a separate module from ``app/api/empirical_routes.py``: that
router's promise is "serves what survived the tournament protocol and nothing
else", and a natal decode is not a survivor claim — it is the tradition's
reading, framed as such (``NATAL_FRAMING`` leads every response).

Endpoints:
  POST /empirical/natal        — birth data in, full decode out (json | markdown)
  GET  /empirical/natal/page   — minimal self-contained form for humans

Usage (dev):
    py -3.12 -m uvicorn app.main:app --reload
    curl -X POST http://127.0.0.1:8000/empirical/natal \
        -H 'Content-Type: application/json' \
        -d '{"year":1990,"month":7,"day":15,"hour":12,"minute":0,
             "latitude":12.97,"longitude":77.59,"tz_offset":5.5}'
"""

from __future__ import annotations

import asyncio
import datetime as _dt
import logging
from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.empirical.natal.chart import BirthMoment, assemble_chart
from app.empirical.natal.decoder import decode
from app.empirical.natal.render import render, to_markdown

logger = logging.getLogger(__name__)

natal_router = APIRouter(prefix="/empirical/natal", tags=["empirical"])


class NatalRequest(BaseModel):
    """A birth as the user states it. Mirrors ``report_routes.ReportRequest``:
    fixed float offset (not an IANA zone), clamped coordinates, extra=forbid."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    year: int = Field(..., ge=1800, le=2100)
    month: int = Field(..., ge=1, le=12)
    day: int = Field(..., ge=1, le=31)
    hour: int = Field(12, ge=0, le=23)
    minute: int = Field(0, ge=0, le=59)
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    tz_offset: float = Field(..., ge=-12.0, le=14.0)
    time_known: bool = True
    house_system: Literal[
        "placidus", "koch", "whole_sign", "equal",
        "porphyry", "regiomontanus", "campanus",
    ] = "placidus"
    fmt: Literal["json", "markdown"] = Field("json", alias="format")

    @model_validator(mode="after")
    def _calendar_valid(self) -> "NatalRequest":
        """Reject Feb 30 and friends here — swe.julday would silently
        arithmetic past an impossible date instead of failing."""
        try:
            _dt.date(self.year, self.month, self.day)
        except ValueError as exc:
            raise ValueError(f"not a real calendar date: {exc}") from exc
        return self


@natal_router.post("")
async def post_natal(req: NatalRequest) -> Any:
    """Compute the chart and decode it. CPU-bound swisseph work runs in a
    thread per the locked ``asyncio.to_thread`` convention."""
    moment = BirthMoment(
        year=req.year,
        month=req.month,
        day=req.day,
        hour=req.hour,
        minute=req.minute,
        latitude=req.latitude,
        longitude=req.longitude,
        tz_offset=req.tz_offset,
        time_known=req.time_known,
    )

    def _work() -> Any:
        decoded = decode(assemble_chart(moment, house_system=req.house_system))
        if req.fmt == "markdown":
            return to_markdown(decoded)
        return render(decoded)

    try:
        result = await asyncio.to_thread(_work)
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    if req.fmt == "markdown":
        return PlainTextResponse(result, media_type="text/markdown")
    return result


# The page is static: user input never enters markup. The response markdown is
# inserted exclusively via textContent (repo safe-DOM rule — no innerHTML).
_PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Natal decode</title>
<style>
  :root { color-scheme: light dark; }
  body { font-family: system-ui, sans-serif; max-width: 60rem; margin: 2rem auto; padding: 0 1rem; }
  form { display: grid; grid-template-columns: repeat(auto-fit, minmax(9rem, 1fr)); gap: .6rem; align-items: end; }
  label { display: flex; flex-direction: column; font-size: .85rem; gap: .2rem; }
  input, select, button { padding: .4rem; font: inherit; }
  button { grid-column: 1 / -1; cursor: pointer; }
  pre { white-space: pre-wrap; border: 1px solid color-mix(in srgb, currentColor 25%, transparent);
        border-radius: .5rem; padding: 1rem; margin-top: 1.5rem; }
  .frame { font-style: italic; opacity: .85; }
</style>
</head>
<body>
<h1>Natal decode — Western tropical</h1>
<p class="frame">Reports what the Western tropical tradition associates with the
planets at your birth. Not a validated measurement, not a prediction — the full
disclosure accompanies every reading.</p>
<form id="f">
  <label>Year <input name="year" type="number" value="1990" min="1800" max="2100" required></label>
  <label>Month <input name="month" type="number" value="7" min="1" max="12" required></label>
  <label>Day <input name="day" type="number" value="15" min="1" max="31" required></label>
  <label>Hour <input name="hour" type="number" value="12" min="0" max="23"></label>
  <label>Minute <input name="minute" type="number" value="0" min="0" max="59"></label>
  <label>Latitude <input name="latitude" type="number" value="12.97" step="any" min="-90" max="90" required></label>
  <label>Longitude <input name="longitude" type="number" value="77.59" step="any" min="-180" max="180" required></label>
  <label>UTC offset <input name="tz_offset" type="number" value="5.5" step="any" min="-12" max="14" required></label>
  <label>House system
    <select name="house_system">
      <option value="placidus" selected>Placidus</option>
      <option value="koch">Koch</option>
      <option value="whole_sign">Whole sign</option>
      <option value="equal">Equal</option>
      <option value="porphyry">Porphyry</option>
      <option value="regiomontanus">Regiomontanus</option>
      <option value="campanus">Campanus</option>
    </select>
  </label>
  <label><span>Birth time known</span> <input name="time_known" type="checkbox" checked></label>
  <button type="submit">Decode</button>
</form>
<pre id="out">Submit a birth to see the reading.</pre>
<script>
"use strict";
const form = document.getElementById("f");
const out = document.getElementById("out");
form.addEventListener("submit", async (ev) => {
  ev.preventDefault();
  out.textContent = "Computing…";
  const fd = new FormData(form);
  const body = {
    year: Number(fd.get("year")),
    month: Number(fd.get("month")),
    day: Number(fd.get("day")),
    hour: Number(fd.get("hour") || 12),
    minute: Number(fd.get("minute") || 0),
    latitude: Number(fd.get("latitude")),
    longitude: Number(fd.get("longitude")),
    tz_offset: Number(fd.get("tz_offset")),
    house_system: fd.get("house_system"),
    time_known: fd.get("time_known") === "on",
    format: "markdown",
  };
  try {
    const resp = await fetch("/empirical/natal", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const text = await resp.text();
    out.textContent = resp.ok ? text : ("Error " + resp.status + ": " + text);
  } catch (err) {
    out.textContent = "Request failed: " + err;
  }
});
</script>
</body>
</html>
"""


@natal_router.get("/page", response_class=HTMLResponse)
async def natal_page() -> HTMLResponse:
    """The human-facing form. Static markup; responses land via textContent."""
    return HTMLResponse(_PAGE)
