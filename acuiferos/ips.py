"""Standardised piezometric index: how a month's level compares with the same month in other years.

The BRGM's IPS puts each monthly mean on the distribution of the same calendar month across the
whole record and maps it to seven classes. Here the distribution is the empirical one (the rank of
the month among the others), with no fitted curve, so every class can be checked by sorting a column.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from statistics import NormalDist, median

from .config import COMPLETE_SHARE, MIN_REFERENCE_YEARS

# Upper probability of each class, the BRGM bulletin's thresholds.
CLASSES = [
    (0.10, "very_low", "Muy bajo"),
    (0.20, "low", "Bajo"),
    (0.40, "mod_low", "Moderadamente bajo"),
    (0.60, "normal", "En torno a lo normal"),
    (0.80, "mod_high", "Moderadamente alto"),
    (0.90, "high", "Alto"),
    (1.01, "very_high", "Muy alto"),
]
LABELS = {key: label for _, key, label in CLASSES}
LOW_CLASSES = {"very_low", "low"}


@dataclass(frozen=True)
class Reading:
    month: str
    status: str                  # "ok", "no_data", "incomplete" or "short_record"
    value: float | None = None   # monthly mean, m NGF
    days: int = 0
    years: int = 0               # other years with the same calendar month
    p: float | None = None       # share of those years with a lower level (empirical)
    ips: float | None = None     # p on the standard normal scale
    cls: str | None = None
    record: str = ""             # "low" or "high" when no other year went beyond it


def class_of(p: float) -> str:
    # Lower half: a class holds its upper bound (p = 0.10 is "muy bajo"); upper half, its lower
    # bound (p = 0.90 is "alto"... and above). Symmetric, so 0.5 is always "normal".
    for upper, key, _ in CLASSES:
        if (p <= upper if p < 0.5 else p < upper):
            return key
    return "very_high"


def probability(value: float, reference: list[float]) -> float:
    """Weibull plotting position of `value` among `reference` plus itself: rank / (n + 1).
    Ties count half, so a month equal to all others sits at 0.5."""
    below = sum(r < value for r in reference)
    ties = sum(r == value for r in reference)
    return (below + 0.5 * ties + 1) / (len(reference) + 2)


def months_before(month: str, n: int) -> list[str]:
    y, m = int(month[:4]), int(month[5:7])
    out = []
    for _ in range(n):
        m -= 1
        if m == 0:
            y, m = y - 1, 12
        out.append(f"{y:04d}-{m:02d}")
    return out


def usual_days(series: dict[str, tuple[float, int]], month: str) -> int:
    """Readings the station usually has in a month: the median of the 24 months before `month`.
    A well read once a month and a logger read every day are judged on their own rhythm."""
    counts = [series[m][1] for m in months_before(month, 24) if m in series]
    return int(median(counts)) if counts else 1


def classify(series: dict[str, tuple[float, int]], month: str) -> Reading:
    if month not in series:
        return Reading(month, "no_data")
    value, days = series[month]
    if days < max(1, ceil(COMPLETE_SHARE * usual_days(series, month))):
        return Reading(month, "incomplete", value, days)
    reference = [v for m, (v, _) in series.items() if m[5:] == month[5:] and m != month]
    if len(reference) < MIN_REFERENCE_YEARS:
        return Reading(month, "short_record", value, days, len(reference))
    p = probability(value, reference)
    record = "low" if value < min(reference) else "high" if value > max(reference) else ""
    return Reading(month, "ok", value, days, len(reference), round(p, 4),
                   round(NormalDist().inv_cdf(p), 3), class_of(p), record)


def band(series: dict[str, tuple[float, int]], exclude_year: str = "") -> dict[int, dict]:
    """Per calendar month: min, 10th, 50th and 90th percentile and max of the monthly means,
    for the chart behind each piezometer's curve."""
    by_month: dict[int, list[float]] = {}
    for m, (v, _) in series.items():
        if m[:4] != exclude_year:
            by_month.setdefault(int(m[5:7]), []).append(v)
    out = {}
    for k, values in by_month.items():
        values.sort()
        out[k] = {"n": len(values), "min": values[0], "p10": _quantile(values, 0.10),
                  "p50": _quantile(values, 0.50), "p90": _quantile(values, 0.90), "max": values[-1]}
    return out


def metres(series: dict[str, tuple[float, int]], reading: Reading, altitude: str) -> tuple[float | None, float | None]:
    """The reading in metres: against the median of the same month in the other years (negative is
    below), and below the station's reference altitude (negative: above it, an artesian well or a
    wrong altitude). The first needs a classified month; the second only a level and an altitude."""
    anomaly = depth = None
    if reading.status == "ok":
        ref = band(series, exclude_year=reading.month[:4]).get(int(reading.month[5:7]))
        if ref:
            anomaly = round(reading.value - ref["p50"], 2)
    if reading.value is not None and altitude:
        depth = round(float(altitude) - reading.value, 1)
    return anomaly, depth


def _quantile(sorted_values: list[float], q: float) -> float:
    pos = q * (len(sorted_values) - 1)
    lo = int(pos)
    hi = min(lo + 1, len(sorted_values) - 1)
    return round(sorted_values[lo] + (sorted_values[hi] - sorted_values[lo]) * (pos - lo), 3)
