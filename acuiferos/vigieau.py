"""VigiEau: the drought restriction level in force in each department, today."""
from __future__ import annotations

import requests

from .config import VIGIEAU

# The four levels of the French drought framework, from least to most severe.
LEVELS = ["vigilance", "alerte", "alerte_renforcee", "crise"]
LABELS = {"": "Sin restricción", "vigilance": "Vigilancia", "alerte": "Alerta",
          "alerte_renforcee": "Alerta reforzada", "crise": "Crisis"}


def rank(level: str) -> int:
    """0 for no restriction, 1 (vigilance) to 4 (crise)."""
    return LEVELS.index(level) + 1 if level in LEVELS else 0


def fetch(http: requests.Session) -> list[dict]:
    r = http.get(f"{VIGIEAU}/departements", timeout=60)
    r.raise_for_status()
    return [parse(d) for d in r.json()]


def parse(d: dict) -> dict:
    """The highest level in force in any zone of the department, per kind of water.
    `groundwater` is the one this project compares with the piezometers."""
    return {"department": d["code"], "department_name": d["nom"],
            "groundwater": d.get("niveauGraviteSouMax") or "", "surface": d.get("niveauGraviteSupMax") or "",
            "drinking": d.get("niveauGraviteAepMax") or "", "max": d.get("niveauGraviteMax") or ""}
