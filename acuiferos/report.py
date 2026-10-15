"""The month's picture: every piezometer classified, departments summed up and set against VigiEau."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from statistics import median

from . import store, vigieau
from .config import DISCORDANT_LOW_SHARE, LOW_P, MIN_DEPARTMENT_POINTS, NORMAL_P
from .ips import LOW_CLASSES, Reading, classify, months_before


@dataclass
class Point:
    station: dict
    series: dict
    now: Reading           # the last complete month
    year_ago: Reading      # the same month a year earlier
    month_ago: Reading     # the month before


@dataclass
class Department:
    code: str
    name: str
    restriction: str | None              # VigiEau groundwater level, "" for none, None if unknown
    points: list[Point] = field(default_factory=list)

    @property
    def classified(self) -> list[Point]:
        return [p for p in self.points if p.now.status == "ok"]

    @property
    def low(self) -> int:
        return sum(p.now.cls in LOW_CLASSES for p in self.classified)

    @property
    def low_share(self) -> float | None:
        return self.low / len(self.classified) if self.classified else None

    @property
    def median_p(self) -> float | None:
        ps = [p.now.p for p in self.classified]
        return median(ps) if ps else None

    @property
    def flag(self) -> str:
        """An indication, not a verdict: the levels and the restriction point in different directions.
        - "low_unrestricted": half or more of the piezometers low or very low, and no groundwater
          restriction beyond vigilance.
        - "restricted_normal": groundwater in alerte renforcée or crise while the median piezometer
          is around normal or higher."""
        if self.restriction is None or len(self.classified) < MIN_DEPARTMENT_POINTS:
            return ""
        level = vigieau.rank(self.restriction)
        if self.low_share >= DISCORDANT_LOW_SHARE and level <= 1:
            return "low_unrestricted"
        if level >= 3 and self.median_p > NORMAL_P:
            return "restricted_normal"
        return ""


@dataclass
class Report:
    month: str
    points: list[Point]
    departments: list[Department]
    vigieau_date: str

    @property
    def classified(self) -> list[Point]:
        return [p for p in self.points if p.now.status == "ok"]

    def low_share_vs_year_ago(self) -> tuple[float, float, int] | None:
        """Share of low piezometers now and a year ago, over those classified both times,
        so the comparison is not moved by stations that started or stopped in between."""
        both = [p for p in self.classified if p.year_ago.status == "ok"]
        if not both:
            return None
        now = sum(p.now.p <= LOW_P for p in both) / len(both)
        before = sum(p.year_ago.p <= LOW_P for p in both) / len(both)
        return now, before, len(both)


def last_complete_month(today: date) -> str:
    return months_before(f"{today:%Y-%m}", 1)[0]


def build(today: date) -> Report:
    month = last_complete_month(today)
    year_ago = f"{int(month[:4]) - 1}{month[4:]}"
    month_ago = months_before(month, 1)[0]
    snapshots = store.load_vigieau()
    vigieau_date = max((r["date"] for r in snapshots), default="")
    restrictions = {r["department"]: r for r in snapshots if r["date"] == vigieau_date}

    points = []
    for s in store.load_stations():
        series = store.load_monthly(s["bss_id"])
        if not series:
            continue
        points.append(Point(s, series, classify(series, month), classify(series, year_ago),
                            classify(series, month_ago)))

    departments: dict[str, Department] = {}
    for code, r in restrictions.items():
        departments[code] = Department(code, r["department_name"], r["groundwater"])
    for p in points:
        code = p.station["department"]
        if code not in departments:
            departments[code] = Department(code, p.station["department_name"], None)
        departments[code].points.append(p)
    return Report(month, points, sorted(departments.values(), key=lambda d: d.code), vigieau_date)
