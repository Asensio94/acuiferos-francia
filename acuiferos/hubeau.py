"""Hub'Eau piezometry API: the active piezometers and their daily levels."""
from __future__ import annotations

import csv
import io
import time
from datetime import date

import requests

from .config import BAD_NATURE, BAD_QUALIFICATION, HUBEAU, HUBEAU_DEPTH

STATION_FIELDS = ("code_bss,bss_id,code_commune_insee,nom_commune,code_departement,nom_departement,"
                  "x,y,altitude_station,date_debut_mesure,date_fin_mesure,codes_masse_eau_edl,"
                  "noms_masse_eau_edl,libelle_pe")
LEVEL_FIELDS = "date_mesure,niveau_nappe_eau,qualification,code_nature_mesure"


def session() -> requests.Session:
    s = requests.Session()
    s.headers["User-Agent"] = "acuiferos-francia (+https://github.com/Asensio94/acuiferos-francia)"
    return s


def get(http: requests.Session, path: str, params: dict, tries: int = 5) -> requests.Response:
    """GET with retries. Now and then the API holds a connection open without answering; a short
    read timeout and a new try is much faster than waiting for it."""
    for attempt in range(tries):
        try:
            r = http.get(f"{HUBEAU}/{path}", params=params, timeout=(10, 30))
            if r.status_code in (200, 206):
                return r
            if r.status_code < 500 and r.status_code != 429:
                r.raise_for_status()
        except (requests.ConnectionError, requests.Timeout):
            if attempt == tries - 1:
                raise
        time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"Hub'Eau {path} failed {tries} times: {params}")


def fetch_stations(http: requests.Session, active_on: date) -> list[dict]:
    """Piezometers with at least one reading on or after `active_on`."""
    rows, page = [], 1
    while True:
        j = get(http, "stations", {"date_recherche": active_on.isoformat(), "fields": STATION_FIELDS,
                                   "size": 1000, "page": page}).json()
        rows += j["data"]
        if not j.get("next"):
            return rows
        page += 1


def fetch_levels(http: requests.Session, code_bss: str, start: date, end: date) -> list[tuple[str, float]]:
    """Daily levels (m NGF) between two dates, without the readings the method leaves out.

    Read as CSV, about half the size of the JSON and answered faster. A query never returns more
    than 20 000 rows, so a span that fills the page is halved until each piece fits."""
    params = {"code_bss": code_bss, "date_debut_mesure": start.isoformat(),
              "date_fin_mesure": end.isoformat(), "fields": LEVEL_FIELDS, "size": HUBEAU_DEPTH,
              "sort": "asc"}
    text = get(http, "chroniques.csv", params).content.decode("utf-8")
    rows = list(csv.DictReader(io.StringIO(text), delimiter=";"))
    if len(rows) >= HUBEAU_DEPTH and start < end:
        mid = date.fromordinal((start.toordinal() + end.toordinal()) // 2)
        return fetch_levels(http, code_bss, start, mid) + fetch_levels(
            http, code_bss, date.fromordinal(mid.toordinal() + 1), end)
    return clean(rows)


def clean(rows: list[dict]) -> list[tuple[str, float]]:
    out = []
    for r in rows:
        if r.get("niveau_nappe_eau") in (None, "") or not r.get("date_mesure"):
            continue
        if r.get("qualification") in BAD_QUALIFICATION or r.get("code_nature_mesure") in BAD_NATURE:
            continue
        out.append((r["date_mesure"][:10], float(r["niveau_nappe_eau"])))
    return out
