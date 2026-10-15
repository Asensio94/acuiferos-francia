"""Files under data/: the station list, one monthly series per piezometer, VigiEau by day."""
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from statistics import fmean

from .config import DATA_DIR, MONTHLY_DIR

STATION_COLUMNS = ["bss_id", "code_bss", "commune_insee", "commune", "department", "department_name",
                   "lon", "lat", "altitude", "first", "last", "water_body", "water_body_name", "aquifer"]
VIGIEAU_COLUMNS = ["date", "department", "department_name", "groundwater", "surface", "drinking", "max"]


def _write(path: Path, columns: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, columns, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def _read(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def station_row(s: dict) -> dict:
    """One Hub'Eau station as a flat row. Only the first water body is kept: a piezometer
    almost always sits in one, and the page needs a single name."""
    bodies, names = s.get("codes_masse_eau_edl") or [], s.get("noms_masse_eau_edl") or []
    return {
        "bss_id": s["bss_id"], "code_bss": s["code_bss"], "commune_insee": s.get("code_commune_insee") or "",
        "commune": s.get("nom_commune") or "", "department": s.get("code_departement") or "",
        "department_name": s.get("nom_departement") or "",
        "lon": round(s["x"], 5) if s.get("x") is not None else "",
        "lat": round(s["y"], 5) if s.get("y") is not None else "",
        "altitude": s.get("altitude_station") or "", "first": s.get("date_debut_mesure") or "",
        "last": s.get("date_fin_mesure") or "", "water_body": bodies[0] if bodies else "",
        "water_body_name": names[0] if names else "", "aquifer": s.get("libelle_pe") or "",
    }


def save_stations(rows: list[dict]) -> None:
    _write(DATA_DIR / "stations.csv", STATION_COLUMNS, sorted(rows, key=lambda r: r["bss_id"]))


def load_stations() -> list[dict]:
    return _read(DATA_DIR / "stations.csv")


def monthly_means(levels: list[tuple[str, float]]) -> dict[str, tuple[float, int]]:
    """Month → (mean level, days with a reading). Several readings on one day count as that
    day's mean, so a well read hourly and one read daily weigh the same."""
    days: dict[str, list[float]] = defaultdict(list)
    for day, level in levels:
        days[day].append(level)
    months: dict[str, list[float]] = defaultdict(list)
    for day, values in days.items():
        months[day[:7]].append(fmean(values))
    return {m: (round(fmean(v), 3), len(v)) for m, v in sorted(months.items())}


def load_monthly(bss_id: str) -> dict[str, tuple[float, int]]:
    return {r["month"]: (float(r["mean"]), int(r["days"])) for r in _read(MONTHLY_DIR / f"{bss_id}.csv")}


def save_monthly(bss_id: str, series: dict[str, tuple[float, int]]) -> None:
    rows = [{"month": m, "mean": f"{v:.3f}", "days": n} for m, (v, n) in sorted(series.items())]
    _write(MONTHLY_DIR / f"{bss_id}.csv", ["month", "mean", "days"], rows)


def merge_monthly(old: dict, new: dict, since: str) -> dict:
    """Months from `since` on are replaced by the fresh reading, even if it no longer has them."""
    kept = {m: v for m, v in old.items() if m < since}
    kept.update({m: v for m, v in new.items() if m >= since})
    return kept


def load_latest() -> dict[str, dict]:
    return {r["bss_id"]: r for r in _read(DATA_DIR / "latest.csv")}


def save_latest(latest: dict[str, dict]) -> None:
    _write(DATA_DIR / "latest.csv", ["bss_id", "date", "level"],
           [latest[k] for k in sorted(latest)])


def load_vigieau() -> list[dict]:
    return _read(DATA_DIR / "vigieau.csv")


def append_vigieau(day: str, rows: list[dict]) -> None:
    """One snapshot a day; a second run on the same day replaces the first."""
    kept = [r for r in load_vigieau() if r["date"] != day]
    _write(DATA_DIR / "vigieau.csv", VIGIEAU_COLUMNS, kept + [{**r, "date": day} for r in rows])
