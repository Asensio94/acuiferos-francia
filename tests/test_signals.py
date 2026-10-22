import json
from datetime import datetime, timezone
from pathlib import Path

from jsonschema import Draft202012Validator

from acuiferos import signals
from acuiferos.ips import classify
from acuiferos.report import Point, Report

# A copy of estado-iba's signals.schema.json (the contract every sibling publishes in). If estado-iba
# changes it, copy it again: this test is what tells the bot's signals.json still passes.
SCHEMA = json.loads((Path(__file__).parent / "signals.schema.json").read_text(encoding="utf-8"))


def station(bss_id, insee="59532", lon="2.1696", lat="50.97109"):
    return {"bss_id": bss_id, "code_bss": f"{bss_id}/P", "commune_insee": insee, "commune": "Saint-Georges-sur-l'Aa",
            "department": "59", "department_name": "Nord", "lon": lon, "lat": lat, "altitude": "2.9",
            "first": "2000-01-01", "last": "2026-10-16", "water_body": "AG314", "water_body_name": "Sables",
            "aquifer": ""}


def point(bss_id, level, **kw):
    series = {f"{y}-09": (round(10.0 + (y - 2000) * 0.01, 2), 30) for y in range(2000, 2026)}
    series["2026-09"] = (level, 30)
    r = classify(series, "2026-09")
    return Point(station(bss_id, **kw), series, r, r, r)


def report():
    pts = [point("BSS1", 9.0), point("BSS2", 10.035, insee="2A004"), point("BSS3", 10.13), point("BSS4", 11.0),
           point("BSS5", 9.5, insee="", lon="", lat="")]
    return Report("2026-09", pts, [], "2026-10-21")


def test_only_the_low_classes_become_signals():
    rep = report()
    assert {p.station["bss_id"]: p.now.cls for p in rep.points} == {
        "BSS1": "very_low", "BSS2": "low", "BSS3": "normal", "BSS4": "very_high", "BSS5": "very_low"}
    doc = signals.document(rep, {"BSS1": {"date": "2026-10-20"}}, datetime(2026, 10, 22, 7, 5, tzinfo=timezone.utc))
    by = {s["id"]: s for s in doc["signals"]}
    assert list(by) == ["BSS1", "BSS2", "BSS5"]
    s = by["BSS1"]
    assert (s["country"], s["kind"], s["precision"], s["status"]) == ("FR", "groundwater_level", "punto", "muy bajo")
    assert s["date"] == "2026-10-20" and by["BSS2"]["date"] == "2026-10-16"  # last reading, else the station's last
    assert s["municipalities"] == ["59532"] and by["BSS2"]["municipalities"] == ["2A004"]
    assert s["url"] == "https://asensio94.github.io/acuiferos-francia/#BSS1"
    assert s["value"]["unit"] == "m" and s["value"]["amount"] < 0
    assert s["details"]["point"] == [2.1696, 50.97109] and s["details"]["record"] is True
    assert s["title"] == "Nappe très basse à Saint-Georges-sur-l'Aa en septembre 2026"
    assert by["BSS2"]["status"] == "bajo" and by["BSS2"]["title"].startswith("Nappe basse")
    assert by["BSS5"]["municipalities"] == [] and "point" not in by["BSS5"]["details"]


def test_the_file_follows_the_contract_of_estado_iba():
    doc = signals.document(report(), {}, datetime(2026, 10, 22, 7, 5, tzinfo=timezone.utc))
    assert doc["generated"] == "2026-10-22T07:05Z" and set(doc["coverage"]) == {"FR"}
    errors = [f"{list(e.absolute_path)}: {e.message}" for e in Draft202012Validator(SCHEMA).iter_errors(doc)]
    assert errors == []
