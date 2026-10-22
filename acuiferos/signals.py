"""docs/signals.json: the low piezometers, as signals for Estado de las IBA (its CONTRATO.md, version 2).

One signal per piezometer whose last complete month is "bajo" or "muy bajo", the same classes the
page counts: nothing new is decided here. France only, so the file is version 2 with its country.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone

from .config import DOCS_DIR
from .ips import LOW_CLASSES, metres
from .report import Point, Report

SOURCE = "acuiferos-francia"
SITE = "https://asensio94.github.io/acuiferos-francia/"
KIND = "groundwater_level"
# The class as a canonical word of the contract, and the title in French, the language of France's page.
STATUS = {"very_low": "muy bajo", "low": "bajo"}
TITLE = {"very_low": "Nappe très basse", "low": "Nappe basse"}
MONTHS = "janvier février mars avril mai juin juillet août septembre octobre novembre décembre".split()
INSEE = re.compile(r"^(\d{5}|2[AB]\d{3})$")
COVERAGE = {"label": "Toute la France", "sites": None,
            "note": "Piézomètres de Hub'Eau (banque ADES, BRGM) avec au moins 15 ans de référence ; un signal "
                    "quand le dernier mois complet est bas ou très bas face au même mois des autres années."}


def signal(p: Point, latest: dict | None) -> dict:
    s, r = p.station, p.now
    anomaly, _ = metres(p.series, r, s["altitude"])
    where = s["commune"] or s["code_bss"]
    details = {"code_bss": s["code_bss"], "month": r.month, "p": r.p, "years": r.years,
               "level": round(r.value, 2), "record": r.record == "low",
               "water_body": s["water_body_name"] or None, "department": s["department"] or None}
    if s["lon"] and s["lat"]:
        details["point"] = [float(s["lon"]), float(s["lat"])]
    return {
        "id": s["bss_id"], "country": "FR", "kind": KIND,
        # The last reading of the well, which may be after the month it is judged on (details.month).
        "date": (latest or {}).get("date") or s["last"] or f"{r.month}-01",
        "title": f"{TITLE[r.cls]} à {where} en {MONTHS[int(r.month[5:7]) - 1]} {r.month[:4]}",
        "url": f"{SITE}#{s['bss_id']}",
        "municipalities": [s["commune_insee"]] if INSEE.match(s["commune_insee"] or "") else [],
        "precision": "punto", "status": STATUS[r.cls],
        "value": {"amount": anomaly, "unit": "m"} if anomaly is not None else None,
        "details": details,
    }


def document(rep: Report, latest: dict[str, dict], now: datetime) -> dict:
    low = sorted((p for p in rep.classified if p.now.cls in LOW_CLASSES), key=lambda p: p.station["bss_id"])
    return {"source": SOURCE, "version": 2, "generated": now.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
            "coverage": {"FR": COVERAGE},
            "signals": [signal(p, latest.get(p.station["bss_id"])) for p in low]}


def write(rep: Report, latest: dict[str, dict], now: datetime) -> dict:
    doc = document(rep, latest, now)
    (DOCS_DIR / "signals.json").write_text(json.dumps(doc, ensure_ascii=False, separators=(",", ":")),
                                           encoding="utf-8")
    return doc
