from acuiferos import hubeau, store
from acuiferos.ips import band, class_of, classify, metres, months_before, probability, usual_days
from acuiferos.report import Department, Point
from acuiferos.ips import Reading


def series(values_by_year: dict[int, float], month: int = 9, days: int = 30) -> dict:
    return {f"{y}-{month:02d}": (v, days) for y, v in values_by_year.items()}


def test_class_thresholds_follow_the_bulletin():
    assert class_of(0.05) == "very_low"
    assert class_of(0.10) == "very_low"
    assert class_of(0.15) == "low"
    assert class_of(0.40) == "mod_low"
    assert class_of(0.5) == "normal"
    assert class_of(0.60) == "mod_high"
    assert class_of(0.90) == "very_high"
    assert class_of(0.85) == "high"
    assert class_of(1.0) == "very_high"


def test_probability_is_the_weibull_rank():
    ref = list(range(1, 20))                     # 19 other years
    assert probability(0, ref) == 1 / 21         # lowest of 20
    assert probability(100, ref) == 20 / 21      # highest of 20
    assert probability(5, [5] * 18) == 0.5       # all tied: the middle


def test_classify_needs_fifteen_other_years():
    s = series({y: float(y) for y in range(2012, 2027)})   # 14 other years
    assert classify(s, "2026-09").status == "short_record"
    s = series({y: float(y) for y in range(2011, 2027)})   # 15 other years
    r = classify(s, "2026-09")
    assert r.status == "ok" and r.years == 15 and r.cls == "very_high" and r.record == "high"


def test_record_low_and_missing_month():
    s = series({y: 10.0 for y in range(2000, 2026)} | {2026: 9.0})
    r = classify(s, "2026-09")
    assert r.cls == "very_low" and r.record == "low"
    assert classify(s, "2026-08").status == "no_data"


def test_incomplete_month_is_judged_on_the_wells_own_rhythm():
    s = {m: (10.0, 30) for m in months_before("2026-09", 24)}
    s["2026-09"] = (10.0, 12)                     # a daily logger with 12 days
    assert classify(s, "2026-09").status == "incomplete"
    manual = {m: (10.0, 1) for m in months_before("2026-09", 24)}
    assert usual_days(manual, "2026-09") == 1     # read once a month: one reading is a full month


def test_months_before_crosses_the_year():
    assert months_before("2026-02", 3) == ["2026-01", "2025-12", "2025-11"]


def test_band_quantiles():
    b = band({f"{y}-09": (float(i), 30) for i, y in enumerate(range(2000, 2011))})
    assert b[9] == {"n": 11, "min": 0.0, "p10": 1.0, "p50": 5.0, "p90": 9.0, "max": 10.0}


def test_monthly_means_weigh_days_not_readings():
    levels = [("2026-09-01", 10.0), ("2026-09-01", 12.0), ("2026-09-02", 14.0), ("2026-10-01", 1.0)]
    assert store.monthly_means(levels) == {"2026-09": (12.5, 2), "2026-10": (1.0, 1)}


def test_merge_replaces_the_refreshed_months():
    old = {"2026-06": (1.0, 30), "2026-07": (2.0, 30), "2026-08": (3.0, 30)}
    new = {"2026-08": (4.0, 31)}
    assert store.merge_monthly(old, new, "2026-07") == {"2026-06": (1.0, 30), "2026-08": (4.0, 31)}


def test_clean_drops_wrong_and_pumped_readings():
    rows = [
        {"date_mesure": "2026-09-01", "niveau_nappe_eau": 1.0, "qualification": "Correcte", "code_nature_mesure": "N"},
        {"date_mesure": "2026-09-02", "niveau_nappe_eau": 2.0, "qualification": "Incorrecte", "code_nature_mesure": "N"},
        {"date_mesure": "2026-09-03", "niveau_nappe_eau": 3.0, "qualification": "Correcte", "code_nature_mesure": "D"},
        {"date_mesure": "2026-09-04", "niveau_nappe_eau": None, "qualification": "Correcte", "code_nature_mesure": "N"},
    ]
    assert hubeau.clean(rows) == [("2026-09-01", 1.0)]


def _point(p: float, cls: str) -> Point:
    r = Reading("2026-09", "ok", 1.0, 30, 20, p, 0.0, cls)
    return Point({}, {}, r, r, r)


def test_department_flags():
    low = [_point(0.05, "very_low"), _point(0.15, "low"), _point(0.5, "normal")]
    assert Department("01", "Ain", "", low).flag == "low_unrestricted"
    assert Department("01", "Ain", "vigilance", low).flag == "low_unrestricted"
    assert Department("01", "Ain", "alerte", low).flag == ""
    normal = [_point(0.5, "normal"), _point(0.7, "mod_high"), _point(0.3, "mod_low")]
    assert Department("01", "Ain", "crise", normal).flag == "restricted_normal"
    assert Department("01", "Ain", "crise", normal[:2]).flag == ""      # too few points
    assert Department("01", "Ain", None, low).flag == ""                # VigiEau unknown


def test_metres_against_the_usual_level_and_below_the_station():
    s = series({y: 100.0 + (y - 2000) * 0.1 for y in range(2000, 2026)} | {2026: 99.0})
    r = classify(s, "2026-09")
    anomaly, depth = metres(s, r, "112.5")
    assert anomaly == round(99.0 - 101.25, 2)    # median of 100.0 ... 102.5
    assert depth == 13.5
    assert metres(s, r, "95")[1] == -4.0         # artesian, or a wrong altitude
    short = classify(series({2025: 100.0, 2026: 99.0}), "2026-09")
    assert metres(series({2025: 100.0, 2026: 99.0}), short, "")  == (None, None)
