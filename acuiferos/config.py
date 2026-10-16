"""Paths and the few parameters the method depends on (all shown on the page)."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
MONTHLY_DIR = DATA_DIR / "monthly"
DOCS_DIR = ROOT / "docs"
POINTS_DIR = DOCS_DIR / "p"

HUBEAU = "https://hubeau.eaufrance.fr/api/v1/niveaux_nappes"
VIGIEAU = "https://api.vigieau.gouv.fr/api"
# Departments, simplified from IGN Admin Express (Licence Ouverte), pinned to a commit.
DEPARTMENTS_GEOJSON = ("https://cdn.jsdelivr.net/gh/gregoiredavid/france-geojson@v2.1.1/"
                       "departements-version-simplifiee.geojson")

# Hub'Eau never serves more than 20 000 rows of one query, however it is paged.
HUBEAU_DEPTH = 20_000
# Each run re-reads this many months before the last one stored: raw readings get validated
# and corrected for a while after they are first published.
REFRESH_MONTHS = 3

MIN_REFERENCE_YEARS = 15     # same calendar month in at least this many other years
COMPLETE_SHARE = 0.66        # a month counts if it has this share of the station's usual readings
MIN_DEPARTMENT_POINTS = 3    # fewer classified piezometers: no department verdict
LOW_P = 0.20                 # "bajo" or worse
DISCORDANT_LOW_SHARE = 0.5   # half the department low with no groundwater restriction
NORMAL_P = 0.40              # median above this: "en torno a lo normal" or higher

# Interpolated map: inverse-distance weighting of the probability of nearby piezometers. Full colour
# up to SURFACE_FULL_KM from the nearest one, fading out by SURFACE_MAX_KM, nothing beyond.
SURFACE_FULL_KM = 10
SURFACE_MAX_KM = 30

# Readings left out: flagged wrong by the producer, or taken while the well was pumping or
# influenced by nearby pumping (Sandre nature codes D and I).
BAD_QUALIFICATION = {"Incorrecte"}
BAD_NATURE = {"D", "I"}
