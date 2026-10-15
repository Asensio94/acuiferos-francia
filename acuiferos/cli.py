"""Command line: refresh the piezometers, their monthly levels and VigiEau; render the page."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta

import requests
import typer

from . import hubeau, store, vigieau
from .config import DATA_DIR, DEPARTMENTS_GEOJSON, REFRESH_MONTHS
from .ips import months_before

app = typer.Typer(add_completion=False, help="Acuíferos de Francia: groundwater levels against their own history.")

# A piezometer is followed if it has a reading in the last 45 days; older ones have stopped.
ACTIVE_DAYS = 45


@app.command()
def fetch(station: str = "", workers: int = 4, limit: int = 0, until: str = ""):
    """Refresh the station list and the monthly series (full history for new piezometers)."""
    http = hubeau.session()
    today = date.fromisoformat(until) if until else date.today()
    found = [store.station_row(s) for s in hubeau.fetch_stations(http, today - timedelta(days=ACTIVE_DAYS))]
    # A station that drops out of the active list keeps its row and series: it may come back,
    # and the page reports it as without data rather than forgetting it.
    known = {s["bss_id"]: s for s in store.load_stations()}
    known.update({s["bss_id"]: s for s in found})
    store.save_stations(list(known.values()))
    active = [s for s in found if not station or s["bss_id"] == station or s["code_bss"] == station]
    if limit:
        active = active[:limit]
    typer.echo(f"{len(found)} active piezometers; reading {len(active)}")

    latest = store.load_latest()
    failed = []
    with ThreadPoolExecutor(workers) as pool:
        jobs = {pool.submit(_refresh, hubeau.session(), s, today): s for s in active}
        for i, job in enumerate(as_completed(jobs), 1):
            s = jobs[job]
            try:
                last = job.result()
            except (requests.RequestException, RuntimeError) as e:
                failed.append(s["code_bss"])
                typer.echo(f"  ! {s['code_bss']}: {e.__class__.__name__}")
                continue
            if last:
                latest[s["bss_id"]] = {"bss_id": s["bss_id"], "date": last[0], "level": f"{last[1]:.3f}"}
            if i % 200 == 0:
                typer.echo(f"  {i}/{len(active)}")
    store.save_latest(latest)
    typer.echo(f"done; {len(failed)} failed")
    # A few failures are the API's bad moments; most of them is an outage worth a red run.
    if len(failed) > max(20, len(active) // 10):
        raise typer.Exit(1)


def _refresh(http, s: dict, today: date):
    old = store.load_monthly(s["bss_id"])
    if old:
        since = months_before(max(old), REFRESH_MONTHS)[-1]
        start = date.fromisoformat(since + "-01")
    else:
        start = date.fromisoformat(s["first"]) if s["first"] else date(1900, 1, 1)
        since = start.isoformat()[:7]
    levels = hubeau.fetch_levels(http, s["code_bss"], start, today)
    store.save_monthly(s["bss_id"], store.merge_monthly(old, store.monthly_means(levels), since))
    return max(levels) if levels else None


@app.command("vigieau")
def fetch_vigieau(day: str = ""):
    """Today's drought restriction level per department."""
    rows = vigieau.fetch(hubeau.session())
    store.append_vigieau(day or date.today().isoformat(), rows)
    typer.echo(f"{len(rows)} departments; {sum(bool(r['groundwater']) for r in rows)} with groundwater restrictions")


@app.command()
def geo():
    """Download the department outlines once (they change only with the map of France)."""
    r = requests.get(DEPARTMENTS_GEOJSON, timeout=120)
    r.raise_for_status()
    (DATA_DIR / "departements.geojson").write_bytes(r.content)
    typer.echo(f"{len(r.content) // 1024} kB")


@app.command()
def page(until: str = ""):
    """Classify the last complete month and render docs/."""
    from . import web
    out = web.render(date.fromisoformat(until) if until else None)
    typer.echo(f"wrote {out}")


if __name__ == "__main__":
    app()
