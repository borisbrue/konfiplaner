"""TST-0017 – Feste Termine im Modell, Zeitraster-Ableitung und Solver (CON-0013)."""

from datetime import time

import pytest

from konfiplaner.modell import Modell, ModellFehler, Person, Thema, Zeitslot
from konfiplaner.planer import PlanerOptionen
from konfiplaner.restriktionen import standard_konfiguration
from konfiplaner.restriktionen.basis import RegelEinstellung
from konfiplaner.restriktionen.grundregeln import RANGFAKTOREN
from konfiplaner.solver import CpSatPlaner
from konfiplaner.zeitraster import raster_aus_fenstern
from tests.helfer import slots


def fenster(tag, von, bis):
    return Zeitslot(tag, time(*von), time(*bis))


# ── Zeitraster aus Zeitfenstern ─────────────────────────────────────────────
def test_raster_bei_teilueberlappung_hat_drei_abschnitte():
    r = raster_aus_fenstern([fenster("Mi", (14, 0), (15, 30)), fenster("Mi", (15, 0), (16, 0))])
    assert [(z.start, z.ende) for z in r] == [
        (time(14), time(15)),
        (time(15), time(15, 30)),
        (time(15, 30), time(16)),
    ]


def test_raster_laesst_luecken_weg():
    r = raster_aus_fenstern([fenster("Mi", (14, 0), (15, 0)), fenster("Mi", (17, 0), (18, 0))])
    assert [(z.start, z.ende) for z in r] == [(time(14), time(15)), (time(17), time(18))]


def test_raster_behaelt_tage_in_reihenfolge_des_auftretens():
    r = raster_aus_fenstern(
        [fenster("Do", (9, 0), (10, 0)), fenster("Mi", (9, 0), (10, 0)), fenster("Do", (11, 0), (12, 0))]
    )
    assert [z.tag for z in r] == ["Do", "Do", "Mi"]


def test_gleiche_fenster_ergeben_einen_abschnitt():
    assert len(raster_aus_fenstern([fenster("Mi", (14, 0), (15, 0))] * 3)) == 1


# ── Modell ──────────────────────────────────────────────────────────────────
def modell_mit_fenstern(*fs, **kw):
    raster = raster_aus_fenstern(list(fs))
    themen = [Thema("A", festtermine=tuple(fs[:1])), Thema("B", festtermine=tuple(fs[1:]))]
    return Modell(themen, [Person("P", ("A", "B"))], raster, **kw)


def test_fest_bloecke_bilden_fenster_auf_slots_ab():
    m = modell_mit_fenstern(fenster("Mi", (14, 0), (15, 30)), fenster("Mi", (15, 0), (16, 0)))
    assert m.fest_bloecke("A") == [(0, 2)]  # 14:00–15:00 und 15:00–15:30
    assert m.fest_bloecke("B") == [(1, 2)]  # 15:00–15:30 und 15:30–16:00


def test_fest_bloecke_ohne_festtermine_sind_leer():
    assert Modell([Thema("A")], [], slots(3)).fest_bloecke("A") == []


def test_festtermin_der_nicht_aufs_raster_passt_ist_ein_fehler():
    with pytest.raises(ModellFehler, match="passt nicht"):
        Modell([Thema("A", festtermine=(fenster("Mo", (8, 10), (8, 40)),))], [], slots(4))


def test_festtermin_ueber_luecke_ist_ein_fehler():
    raster = [fenster("Mi", (14, 0), (15, 0)), fenster("Mi", (16, 0), (17, 0))]
    with pytest.raises(ModellFehler):
        Modell([Thema("A", festtermine=(fenster("Mi", (14, 0), (17, 0)),))], [], raster)


def test_unbekannte_hauptkonferenz():
    with pytest.raises(ModellFehler, match="Hauptkonferenz"):
        Modell([Thema("A", haupt="X")], [], slots(2))


def test_themen_mit_festterminen_gelten_nicht_als_ohne_block():
    m = Modell([Thema("A", dauer_min=999, festtermine=(fenster("Mo", (8, 0), (8, 45)),))], [], slots(2))
    assert m.bloecke_fehlen() == []


# ── Solver ──────────────────────────────────────────────────────────────────
def plane(m, konfig=None):
    return CpSatPlaner().planen(m, konfig or standard_konfiguration(), PlanerOptionen(zeitlimit_s=20))


def weich():
    k = standard_konfiguration()
    k.einstellungen["schwerpunkte"] = RegelEinstellung("schwerpunkte", "weich", 1.0)
    return k


def test_solver_verschiebt_feste_termine_nicht():
    # Slot 0 wäre frei und wichtiger Themen bekommen früh liegende Slots – der Festtermin bleibt trotzdem
    raster = slots(6)
    m = Modell([Thema("A", wichtigkeit=5, festtermine=(raster[4],))], [Person("P", ("A",))], raster)
    plan = plane(m)
    assert [(t.thema, t.start_slot, t.anzahl_slots) for t in plan.termine] == [("A", 4, 1)]


def test_jeder_feste_termin_findet_statt_auch_ohne_teilnehmer():
    raster = slots(4)
    m = Modell([Thema("A", festtermine=(raster[0], raster[2]))], [Person("P", ("A",))], raster)
    plan = plane(m)
    # zwei Termine, Mindestanzahl 1, aber nur eine Person -> der zweite Termin erreicht sie nicht
    assert plan.status == "kein_plan" and "mindestanzahl" in " ".join(plan.begruendung)


def test_person_nimmt_je_konferenz_an_hoechstens_einem_termin_teil():
    raster = slots(4)
    m = Modell(
        [Thema("A", festtermine=(raster[0], raster[2]))], [Person("P", ("A",)), Person("Q", ("A",))], raster
    )
    plan = plane(m)
    assert plan.status in ("optimal", "machbar")
    teil = [n for t in plan.termine for n in t.teilnehmer]
    assert sorted(teil) == ["P", "Q"]


def test_rangfolge_erste_konferenz_gewinnt_bei_ueberschneidung():
    raster = slots(2)
    gleich = (raster[0],)
    m = Modell(
        [
            Thema("I", festtermine=gleich),
            Thema("II", festtermine=gleich),
            Thema("III", festtermine=gleich),
            Thema("Z", festtermine=(raster[1],)),
        ],
        [Person("P", ("I", "II", "III")), Person("Q", ("Z",)), Person("R", ("II",)), Person("S", ("III",))],
        raster,
    )
    plan = plane(m, weich())
    teil = {t.thema: t.teilnehmer for t in plan.termine}
    assert "P" in teil["I"] and "P" not in teil["II"] and "P" not in teil["III"]
    verstoesse = sorted(v.text for v in plan.verstoesse)
    assert any("P nimmt nicht an Schwerpunkt II" in t for t in verstoesse)
    assert any("P nimmt nicht an Schwerpunkt III" in t for t in verstoesse)
    assert not any("P nimmt nicht an Schwerpunkt I teil" in t for t in verstoesse)


def test_rangfolge_zweite_vor_dritter():
    raster = slots(1)
    m = Modell(
        [Thema("I", festtermine=(raster[0],)), Thema("II", festtermine=(raster[0],))],
        [Person("P", ("II", "I")), Person("Q", ("I",)), Person("R", ("II",))],  # Rang: II ist die erste von P
        raster,
    )
    plan = plane(m, weich())
    teil = {t.thema: t.teilnehmer for t in plan.termine}
    assert "P" in teil["II"] and "P" not in teil["I"]


def test_rangfaktoren_sind_absteigend():
    assert list(RANGFAKTOREN) == sorted(RANGFAKTOREN, reverse=True) and RANGFAKTOREN[-1] >= 1


def test_vorsitz_ist_in_allen_festterminen():
    raster = slots(4)
    m = Modell(
        [Thema("A", vorsitz="C", festtermine=(raster[0], raster[2]))],
        [Person("C", ()), Person("P", ("A",)), Person("Q", ("A",))],
        raster,
    )
    plan = plane(m)
    assert plan.status in ("optimal", "machbar")
    assert all("C" in t.teilnehmer for t in plan.termine) and len(plan.termine) == 2


def test_teilueberlappung_verhindert_doppelte_teilnahme():
    r = raster_aus_fenstern([fenster("Mi", (14, 0), (15, 30)), fenster("Mi", (15, 0), (16, 0))])
    m = Modell(
        [
            Thema("A", festtermine=(fenster("Mi", (14, 0), (15, 30)),)),
            Thema("B", festtermine=(fenster("Mi", (15, 0), (16, 0)),)),
        ],
        [Person("P", ("A", "B")), Person("Q", ("A",)), Person("R", ("B",))],
        r,
    )
    plan = plane(m, weich())
    assert sum("P" in t.teilnehmer for t in plan.termine) == 1
    assert len(plan.verstoesse) == 1


def test_getrennte_fenster_ohne_konflikt():
    r = raster_aus_fenstern([fenster("Mi", (14, 0), (15, 0)), fenster("Mi", (15, 0), (16, 0))])
    m = Modell(
        [Thema("A", festtermine=(r[0],)), Thema("B", festtermine=(r[1],))], [Person("P", ("A", "B"))], r
    )
    plan = plane(m, weich())
    assert sum("P" in t.teilnehmer for t in plan.termine) == 2 and not plan.verstoesse


def test_vorsitz_in_zwei_gleichzeitigen_konferenzen_ist_kein_plan():
    raster = slots(1)
    m = Modell(
        [
            Thema("A", vorsitz="C", festtermine=(raster[0],)),
            Thema("B", vorsitz="C", festtermine=(raster[0],)),
        ],
        [Person("C", ()), Person("P", ("A",)), Person("Q", ("B",))],
        raster,
    )
    plan = plane(m)
    text = " ".join(plan.begruendung)
    assert plan.status == "kein_plan" and "Thema A" in text and "Thema B" in text
