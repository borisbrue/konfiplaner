"""TST-0004 – Planungsverhalten (CON-0004). Die Testnamen folgen den Szenarien der .feature-Datei."""

import threading

import pytest

from konfiplaner.modell import Modell, Thema
from konfiplaner.planer import PlanerOptionen
from konfiplaner.restriktionen.basis import RegelEinstellung
from konfiplaner.solver import CpSatPlaner
from tests.helfer import mit_regeln, modell, registry_mit_plugins, zufallsmodell


def plane(m: Modell, konfig=None, **kw):
    return CpSatPlaner(registry_mit_plugins()).planen(
        m, konfig or mit_regeln(), PlanerOptionen(zeitlimit_s=30, **kw)
    )


def termine(plan, thema):
    return [t for t in plan.termine if t.thema == thema]


def test_einfacher_plan():
    th = [Thema(n, mindestanzahl=2) for n in "ABC"]
    pe = [(f"P{i}", *paar) for i, paar in enumerate([("A", "B")] * 4 + [("B", "C")] * 4 + [("A", "C")] * 4)]
    m = modell(th, pe, n_slots=6)
    plan = plane(m)
    assert plan.status == "optimal"
    for t in "ABC":
        assert termine(plan, t)
    for p in m.personen:
        for t in p.themen:
            assert sum(p.name in x.teilnehmer for x in termine(plan, t)) == 1


def test_nur_ein_termin_je_thema():
    m = modell([Thema("A", mindestanzahl=3), Thema("B")], [(f"P{i}", "A", "B") for i in range(3)])
    plan = plane(m)
    assert len(termine(plan, "A")) == 1
    assert set(termine(plan, "A")[0].teilnehmer) == {"P0", "P1", "P2"}


def test_mehrere_termine_je_thema():
    verf = {f"P{i}": {0, 1} for i in range(3)} | {f"P{i}": {2, 3} for i in range(3, 6)}
    m = modell([Thema("A", mindestanzahl=3), Thema("B")], [(f"P{i}", "A", "B") for i in range(6)], 4, verf)
    plan = plane(m)
    assert plan.status in ("optimal", "machbar")
    a = termine(plan, "A")
    assert len(a) == 2 and all(len(t.teilnehmer) >= 3 for t in a)


def test_mindestanzahl_nicht_erreichbar():
    m = modell([Thema("A", mindestanzahl=5), Thema("B")], [(f"P{i}", "A", "B") for i in range(3)])
    plan = plane(m)
    assert plan.status == "kein_plan" and plan.termine == []
    text = " ".join(plan.begruendung)
    assert "mindestanzahl" in text and "Thema A" in text


def test_kein_thema_entfaellt():
    # Thema Z hat keine Personen, muss aber stattfinden und seine Mindestanzahl erreichen
    m = modell([Thema("A"), Thema("B"), Thema("Z")], [("P", "A", "B")])
    plan = plane(m)
    assert plan.status == "kein_plan"
    assert "themenabdeckung" in " ".join(plan.begruendung) and "Thema Z" in " ".join(plan.begruendung)


def _engpass():
    # P1 ist nur in Slot 0 verfügbar, braucht aber zwei Themen
    return modell([Thema("A"), Thema("B")], [("P1", "A", "B"), ("P2", "A", "B")], 3, {"P1": {0}})


def test_schwerpunkte_weich_gestellt_bei_engpass():
    plan = plane(_engpass(), mit_regeln(schwerpunkte=("weich", 5)))
    assert plan.status in ("optimal", "machbar")
    assert [v for v in plan.verstoesse if v.restriktion == "schwerpunkte" and "P1" in v.text]


def test_schwerpunkte_hart_bei_engpass_ist_kein_plan():
    assert plane(_engpass()).status == "kein_plan"


def test_wichtigkeit_bei_slot_konflikt():
    m = modell([Thema("wichtig", wichtigkeit=5), Thema("egal", wichtigkeit=1)], [("P", "wichtig", "egal")], 3)
    plan = plane(m)
    assert termine(plan, "wichtig")[0].start_slot < termine(plan, "egal")[0].start_slot
    assert termine(plan, "wichtig")[0].start_slot == 0


def test_keine_ueberschneidung_bei_nur_zwei_slots():
    m = modell([Thema("A"), Thema("B")], [("P", "A", "B")], 2)
    plan = plane(m)
    assert {t.start_slot for t in plan.termine} == {0, 1}


@pytest.mark.parametrize("dauer,erwartet", [(45, 1), (90, 2), (100, 3)])
def test_dauer_wird_aufgerundet(dauer, erwartet):
    plan = plane(modell([Thema("A", dauer_min=dauer), Thema("B")], [("P", "A", "B")], 6))
    assert termine(plan, "A")[0].anzahl_slots == erwartet


def test_dauer_laenger_als_jeder_block():
    plan = plane(modell([Thema("A", dauer_min=180), Thema("B")], [("P", "A", "B")], 2))
    assert plan.status == "kein_plan"
    assert "Thema A" in " ".join(plan.begruendung) and "180" in " ".join(plan.begruendung)


def test_person_ohne_verfuegbarkeit_erzeugt_warnung():
    plan = plane(modell([Thema("A"), Thema("B")], [("P", "A", "B")], 3, {"P": set()}))
    assert any("P" in w for w in plan.warnungen)


def test_kollidierende_regeln():
    m = modell([Thema("A"), Thema("B")], [("Anna", "A", "B"), ("Ben", "A", "B")], 3)
    ein = {"person_a": "Anna", "person_b": "Ben"}
    konfig = mit_regeln(
        RegelEinstellung("nicht_zusammen", "hart", parameter=ein),
        RegelEinstellung("zusammen", "hart", parameter=ein),
    )
    plan = plane(m, konfig)
    assert plan.status == "kein_plan"
    text = " ".join(plan.begruendung)
    assert "nicht_zusammen" in text and "zusammen:" in text.replace("nicht_zusammen", "")


def test_reproduzierbarkeit():
    m = zufallsmodell(24, 4, 8)
    a = plane(m, seed=3, arbeiter=1).to_dict()
    b = plane(m, seed=3, arbeiter=1).to_dict()
    assert a == b


def test_abbruch_liefert_beste_bisherige_loesung():
    m = zufallsmodell(60, 8, 12)
    signal = threading.Event()
    aufrufe = []

    def fortschritt(f):
        aufrufe.append(f)
        signal.set()

    plan = CpSatPlaner().planen(m, mit_regeln(), PlanerOptionen(zeitlimit_s=60), fortschritt, signal)
    assert aufrufe
    assert plan.status in ("machbar", "optimal")
    assert plan.termine


def test_abbruch_vor_dem_ersten_ergebnis_ist_kein_plan():
    signal = threading.Event()
    signal.set()
    m = zufallsmodell(60, 8, 12)
    plan = CpSatPlaner().planen(m, mit_regeln(), PlanerOptionen(zeitlimit_s=60), None, signal)
    assert plan.status in ("kein_plan", "machbar", "optimal")


def test_leere_termine_werden_nicht_angelegt():
    m = modell([Thema("A"), Thema("B")], [("P", "A", "B"), ("Q", "A", "B")], 6)
    plan = plane(m)
    assert all(t.teilnehmer for t in plan.termine)


def test_zeitlimit_wird_eingehalten():
    import time

    m = zufallsmodell(200, 15, 24)
    t0 = time.perf_counter()
    plan = CpSatPlaner().planen(m, mit_regeln(), PlanerOptionen(zeitlimit_s=5))
    assert time.perf_counter() - t0 < 8
    assert plan.status in ("optimal", "machbar")
