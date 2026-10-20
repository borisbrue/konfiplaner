"""TST-0024 – Verteilung (CON-0017). Die Testnamen folgen den Szenarien der .feature-Datei."""

import random
import time

from konfiplaner.anwendung import Sitzung
from tests.xlsx_helfer import PERSONEN, SLOTS, lehrerliste, schreibe

EIN_SLOT = [["Tag", "Start", "Ende"], ["Sa", "09:00", "09:45"]]


def lade(tmp_path, zeilen, **kw):
    blaetter = lehrerliste(zeilen, zeitslots=False)
    blaetter["Zeitslots"] = EIN_SLOT
    s = Sitzung()
    s.lade(schreibe(tmp_path / "l.xlsx", blaetter))
    return s


def teil(plan):
    return {t.thema: set(t.teilnehmer) for t in plan.termine}


def test_lehrerliste_planbar_ohne_regelaenderung(tmp_path):
    zeilen = [
        ["A", "A", "", "Deutsch", "Sport", "Kunst", "Deutsch"],
        ["B", "B", "", "Sport", "Kunst", None, "Sport"],
        ["C", "C", "", "Kunst", "Deutsch", None, "Kunst"],
        ["D", "D", "", "Deutsch", "Sport", None, None],
    ]
    s = lade(tmp_path, zeilen)
    assert s.planbar and s.planen().status in ("optimal", "machbar")


def test_jede_lehrkraft_genau_eine_konferenz_im_selben_slot(tmp_path):
    zeilen = [
        [
            f"N{i}",
            f"V{i}",
            "",
            "Deutsch",
            "Englisch",
            None,
            "Deutsch" if i == 0 else ("Englisch" if i == 1 else None),
        ]
        for i in range(8)
    ]
    plan = lade(tmp_path, zeilen).planen()
    alle = [n for t in plan.termine for n in t.teilnehmer]
    assert len(alle) == len(set(alle)) == 8


def test_konferenzen_gleich_gross(tmp_path):
    zeilen = [[f"N{i}", f"V{i}", "", "Deutsch", "Englisch", None, None] for i in range(5)]
    zeilen += [[f"M{i}", f"W{i}", "", "Englisch", "Deutsch", None, None] for i in range(5)]
    zeilen[0][6], zeilen[5][6] = "Deutsch", "Englisch"
    plan = lade(tmp_path, zeilen).planen()
    assert sorted(len(v) for v in teil(plan).values()) == [5, 5]


def test_ausgleich_geht_vor_rangfolge(tmp_path):
    zeilen = [[f"A{i}", "x", "", "Deutsch", "Sport", None, None] for i in range(8)]
    zeilen += [[f"S{i}", "y", "", "Sport", None, None, None] for i in range(2)]
    zeilen[0][6], zeilen[8][6] = "Deutsch", "Sport"
    g = sorted(len(v) for v in teil(lade(tmp_path, zeilen).planen()).values())
    assert g == [5, 5]  # statt 8 und 2


def test_vorsitz_ist_gesetzt(tmp_path):
    zeilen = [
        ["A", "Anna", "", "Deutsch", "Sport", None, "Sport"],
        ["B", "Ben", "", "Deutsch", None, None, "Deutsch"],
        ["C", "Cem", "", "Deutsch", "Sport", None, None],
    ]
    plan = lade(tmp_path, zeilen).planen()
    assert "Anna A" in teil(plan)["Sport"]


def test_keine_verstossmeldungen_fuer_nicht_besuchte_konferenzen(tmp_path):
    zeilen = [
        [
            f"N{i}",
            f"V{i}",
            "",
            "Deutsch",
            "Englisch",
            None,
            "Deutsch" if i == 0 else ("Englisch" if i == 1 else None),
        ]
        for i in range(6)
    ]
    plan = lade(tmp_path, zeilen).planen()
    assert plan.verstoesse == []


def test_ein_treffen_je_konferenz(tmp_path):
    zeilen = [
        [
            f"N{i}",
            f"V{i}",
            "",
            "Deutsch",
            "Englisch",
            None,
            "Deutsch" if i == 0 else ("Englisch" if i == 1 else None),
        ]
        for i in range(6)
    ]
    plan = lade(tmp_path, zeilen).planen()
    assert sorted(t.thema for t in plan.termine) == ["Deutsch", "Englisch"]


def test_selbst_gesetzte_regel_und_tipp(tmp_path):
    zeilen = [
        [
            f"N{i}",
            f"V{i}",
            "",
            "Deutsch",
            "Englisch",
            None,
            "Deutsch" if i == 0 else ("Englisch" if i == 1 else None),
        ]
        for i in range(4)
    ]
    s = lade(tmp_path, zeilen)
    s.setze_regel("schwerpunkte", "hart", 1.0)
    plan = s.planen()
    assert plan.status == "kein_plan" and "weich" in s.tipp(plan)


def test_minimalformat_bleibt_wie_bisher(tmp_path):
    s = Sitzung()
    s.lade(schreibe(tmp_path / "m.xlsx", {"Personen": PERSONEN, "Zeitslots": SLOTS}))
    assert s.wirksames_profil() == "klassisch"
    typen = {r.name: r.typ for r in s.regeln()}
    assert typen["schwerpunkte"] == "hart" and typen["verteilung"] == "aus"


def test_echte_groesse_101_lehrkraefte_16_konferenzen(tmp_path):
    rnd = random.Random(11)
    namen = [f"Konferenz{i:02d}" for i in range(16)]
    zeilen = []
    for i in range(101):
        k = rnd.choice([1, 2, 2, 2, 3])
        gewaehlt = rnd.sample(namen, k)
        zeilen.append([f"N{i}", f"V{i}", "", *gewaehlt, *[None] * (3 - k), namen[i] if i < 16 else None])
    s = lade(tmp_path, zeilen)
    s.zeitlimit_s = 30
    t0 = time.perf_counter()
    plan = s.planen()
    assert plan.status in ("optimal", "machbar") and time.perf_counter() - t0 < 30
    anzahl = {}
    for t in plan.termine:
        for n in t.teilnehmer:
            anzahl[n] = anzahl.get(n, 0) + 1
    assert set(anzahl.values()) == {1} and len(plan.termine) == 16
