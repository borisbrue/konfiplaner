"""TST-0011 – Sitzung, Zeitraster und Einstellungen, ohne Qt (CON-0010)."""

import os
import threading
from datetime import time

import pytest

from konfiplaner.anwendung import Sitzung
from konfiplaner.einstellungen import YamlEinstellungen, standard_pfad
from konfiplaner.excel_export import ZielDateiExistiertFehler
from konfiplaner.excel_import import ImportDateiFehler
from konfiplaner.modell import ModellFehler
from konfiplaner.restriktionen import KonfigurationsFehler
from konfiplaner.zeitraster import erzeuge_slots
from tests.xlsx_helfer import PERSONEN, SLOTS, schreibe


@pytest.fixture
def datei(tmp_path):
    personen = [PERSONEN[0], *[[f"P{i}", "Taufe", "Abendmahl"] for i in range(4)]]
    return schreibe(tmp_path / "konfis.xlsx", {"Personen": personen})


def test_zeitraster_erzeugt_lueckenlose_slots_je_tag():
    slots = erzeuge_slots(["Sa", "So"], time(9), time(11, 30), 45)
    assert len(slots) == 6  # 2 Tage x 3 Slots, Rest von 15 Minuten entfällt
    assert (slots[0].tag, slots[0].start, slots[0].ende) == ("Sa", time(9), time(9, 45))
    assert slots[2].ende == time(11, 15) and slots[3].tag == "So"


@pytest.mark.parametrize(
    "tage,beginn,ende,laenge",
    [
        (["Sa"], time(9), time(8), 45),
        (["Sa"], time(9), time(9, 30), 45),
        ([" "], time(9), time(12), 45),
        (["Sa", "Sa"], time(9), time(12), 45),
        (["Sa"], time(9), time(12), 0),
    ],
)
def test_zeitraster_lehnt_unsinn_ab(tage, beginn, ende, laenge):
    with pytest.raises(ModellFehler):
        erzeuge_slots(tage, beginn, ende, laenge)


def test_nicht_planbar_ohne_datei_und_ohne_slots(datei):
    s = Sitzung()
    assert not s.planbar and s.planungshindernisse() == ["Keine Datei geladen"]
    s.lade(datei)
    assert s.planungshindernisse() == ["Keine Zeitslots"]
    s.erzeuge_zeitslots("Sa", time(9), time(12), 45)
    assert s.planbar


def test_nicht_planbar_bei_fehlern_in_der_datei(tmp_path):
    s = Sitzung()
    s.lade(schreibe(tmp_path / "x.xlsx", {"Personen": [PERSONEN[0], ["A", "T", "T"]], "Zeitslots": SLOTS}))
    assert not s.planbar and "1 Fehler" in s.planungshindernisse()[0]
    with pytest.raises(ModellFehler):
        s.planen()


def test_unlesbare_datei_laesst_zustand_unveraendert(datei, tmp_path):
    s = Sitzung()
    s.lade(datei)
    kaputt = tmp_path / "kaputt.xlsx"
    kaputt.write_bytes(b"x")
    with pytest.raises(ImportDateiFehler):
        s.lade(kaputt)
    assert s.datei == datei and len(s.ergebnis.personen) == 4


def test_themenwerte_bearbeiten_und_validieren(datei):
    s = Sitzung()
    s.lade(datei)
    s.setze_thema(0, mindestanzahl=2, wichtigkeit=5)
    assert (s.themen[0].mindestanzahl, s.themen[0].wichtigkeit) == (2, 5)
    with pytest.raises(ModellFehler):
        s.setze_thema(0, wichtigkeit=9)
    assert s.themen[0].wichtigkeit == 5


def test_voller_durchlauf_laden_planen_exportieren(datei, tmp_path):
    s = Sitzung()
    s.lade(datei)
    s.setze_thema(0, mindestanzahl=2)
    s.setze_thema(1, mindestanzahl=2)
    s.erzeuge_zeitslots("Sa", time(9), time(12), 45)
    aufrufe = []
    plan = s.planen(aufrufe.append)
    assert plan.status in ("optimal", "machbar") and aufrufe
    assert set(s.tabellen()) == {"Termine", "Personen", "Themen", "Hinweise"}
    ziel = tmp_path / "plan.xlsx"
    s.exportiere(ziel)
    assert ziel.exists() and s.letzter_exportordner == tmp_path
    with pytest.raises(ZielDateiExistiertFehler):
        s.exportiere(ziel)


def test_abbruch_wird_durchgereicht(datei):
    s = Sitzung()
    s.lade(datei)
    s.erzeuge_zeitslots("Sa", time(9), time(12), 45)
    signal = threading.Event()
    signal.set()
    plan = s.planen(abbruch=signal)
    assert plan.status in ("kein_plan", "machbar", "optimal")


def test_regeln_anzeigen_und_aendern():
    s = Sitzung()
    namen = {r.name: r for r in s.regeln()}
    assert namen["schwerpunkte"].typ == "hart" and namen["wichtigkeit"].typ == "weich"
    assert namen["wichtigkeit"].erlaubte_typen == ("weich", "aus")
    s.setze_regel("schwerpunkte", "weich", 4)
    assert {r.name: r for r in s.regeln()}["schwerpunkte"].gewicht == 4
    with pytest.raises(KonfigurationsFehler):
        s.setze_regel("wichtigkeit", "hart")
    s.regeln_zuruecksetzen()
    assert {r.name: r for r in s.regeln()}["schwerpunkte"].typ == "hart"


def test_geaenderte_regel_wirkt_beim_planen(tmp_path):
    s = Sitzung()
    # P1 nur in einem Slot verfügbar: mit harten Schwerpunkten unlösbar, mit weichen lösbar
    personen = [PERSONEN[0], ["P1", "A", "B"], ["P2", "A", "B"]]
    verf = [["Person", "Tag", "Start"], ["P1", "Mo", "08:00"]]
    s.lade(schreibe(tmp_path / "e.xlsx", {"Personen": personen, "Zeitslots": SLOTS, "Verfügbarkeiten": verf}))
    assert s.planen().status == "kein_plan"
    s.setze_regel("schwerpunkte", "weich", 5)
    assert s.planen().status in ("optimal", "machbar")


def test_einstellungen_werden_gemerkt(datei, tmp_path):
    speicher = YamlEinstellungen(tmp_path / "cfg" / "e.yaml")
    s = Sitzung(speicher)
    s.lade(datei)
    s.setze_regel("schwerpunkte", "weich", 3)
    s.zeitlimit_s = 12
    s.erzeuge_zeitslots("Fr, Sa", time(10), time(12), 30)
    neu = Sitzung(YamlEinstellungen(tmp_path / "cfg" / "e.yaml"))
    assert neu.datei == datei and neu.zeitlimit_s == 12
    assert {r.name: r for r in neu.regeln()}["schwerpunkte"].typ == "weich"
    assert neu.zeitraster["tage"] == "Fr, Sa" and neu.zeitraster["laenge_min"] == 30


def test_kaputte_einstellungsdatei_gilt_als_leer(tmp_path):
    pfad = tmp_path / "e.yaml"
    pfad.write_text("::: kein yaml [", encoding="utf-8")
    s = Sitzung(YamlEinstellungen(pfad))
    assert s.datei is None and s.zeitlimit_s == 60.0


def test_unbekannte_gespeicherte_regel_wird_ignoriert(tmp_path):
    pfad = tmp_path / "e.yaml"
    pfad.write_text(
        "regeln:\n  gibt_es_nicht:\n    typ: hart\n  schwerpunkte:\n    typ: vielleicht\n", encoding="utf-8"
    )
    s = Sitzung(YamlEinstellungen(pfad))
    assert {r.name: r for r in s.regeln()}["schwerpunkte"].typ == "hart"


def test_standardpfad_folgt_xdg(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    assert standard_pfad() == tmp_path / "konfiplaner" / "einstellungen.yaml"


def test_datei_geaendert_erkennt_neuere_datei(datei):
    s = Sitzung()
    s.lade(datei)
    assert not s.datei_geaendert()
    os.utime(datei, (datei.stat().st_atime, datei.stat().st_mtime + 10))
    assert s.datei_geaendert()
    s.neu_laden()
    assert not s.datei_geaendert()
