from acuiferos import vigieau
from acuiferos.ips import CLASSES
from acuiferos.web import FLAGS as FLAGS_ES
from acuiferos.web_fr import FLAGS, LABELS, RESTRICTIONS, _n, _pct, month_name


def test_every_label_has_its_french_wording():
    assert set(LABELS) == {key for _, key, _ in CLASSES}
    assert set(RESTRICTIONS) == set(vigieau.LABELS)
    assert set(FLAGS) == set(FLAGS_ES)


def test_french_number_formats():
    assert _n(2617) == "2 617"
    assert _pct(0.643) == "64 %"
    assert month_name("2026-09") == "septembre 2026"
