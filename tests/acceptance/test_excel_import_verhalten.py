"""TST-0002 – Excel-Import (CON-0002). Die Testnamen folgen den Szenarien der .feature-Datei."""

from datetime import datetime, time

import pytest

from konfiplaner.excel_import import ImportDateiFehler, importiere
from konfiplaner.modell import Thema
from tests.xlsx_helfer import PERSONEN, SLOTS, THEMEN, schreibe


def lese(tmp_path, blaetter, **kw):
    return importiere(schreibe(tmp_path / "t.xlsx", blaetter), **kw)


def test_gueltige_datei_im_minimalformat(tmp_path):
    erg = lese(tmp_path, {"Personen": PERSONEN})
    assert not erg.meldungen
    assert [p.name for p in erg.personen] == ["Anna", "Ben"]


def test_themenset_ohne_blatt_themen_mit_standardwerten(tmp_path):
    erg = lese(tmp_path, {"Personen": PERSONEN})
    assert erg.themen == [Thema("Taufe", 3, 1, 45), Thema("Abendmahl", 3, 1, 45)]
    assert not erg.themen_aus_blatt


def test_vollstaendige_datei_liefert_modell(tmp_path):
    erg = lese(tmp_path, {"Personen": PERSONEN, "Themen": THEMEN, "Zeitslots": SLOTS})
    m = erg.modell
    assert m is not None and len(m.zeitslots) == 3
    assert m.thema("Abendmahl") == Thema("Abendmahl", 5, 2, 90)


def test_modell_fehlt_ohne_zeitslots(tmp_path):
    assert lese(tmp_path, {"Personen": PERSONEN}).modell is None


def test_unbekanntes_thema_bei_vorhandenem_blatt_themen(tmp_path):
    personen = [*PERSONEN, ["Cem", "Firmung", "Taufe"]]
    erg = lese(tmp_path, {"Personen": personen, "Themen": THEMEN, "Zeitslots": SLOTS})
    f = erg.fehler[0]
    assert (f.blatt, f.zeile, f.spalte) == ("Personen", 4, "Thema 1")
    assert "Firmung" in f.text
    assert erg.modell is None


def test_zwei_gleiche_themen(tmp_path):
    erg = lese(tmp_path, {"Personen": [*PERSONEN, ["Cem", "Taufe", "Taufe"]]})
    assert [(f.zeile, f.spalte) for f in erg.fehler] == [(4, "Thema 2")]


def test_mehrere_fehler_auf_einmal(tmp_path):
    personen = [PERSONEN[0], ["", "Taufe", "Abendmahl"], ["Ben", "Taufe", "Taufe"], ["Cem", None, "Taufe"]]
    erg = lese(tmp_path, {"Personen": personen})
    assert sorted(f.zeile for f in erg.fehler) == [2, 3, 4]


def test_doppelte_person_ist_nur_eine_warnung(tmp_path):
    erg = lese(tmp_path, {"Personen": [*PERSONEN, ["Anna", "Taufe", "Abendmahl"]]})
    assert not erg.fehler and len(erg.warnungen) == 1 and erg.warnungen[0].zeile == 4
    assert len(erg.personen) == 2


@pytest.mark.parametrize(
    "kopf",
    [
        ["name", "thema1", "THEMA 2"],
        [" Name ", "Thema_1", "thema-2"],
        ["Konfirmand", "Schwerpunkt 1", "Schwerpunkt 2"],
    ],
)
def test_ueberschriften_sind_tolerant(tmp_path, kopf):
    erg = lese(tmp_path, {"Personen": [kopf, *PERSONEN[1:]]})
    assert not erg.meldungen and len(erg.personen) == 2


def test_spaltenzuordnung_ist_konfigurierbar(tmp_path):
    erg = lese(
        tmp_path,
        {"Personen": [["Teilnehmer", "A", "B"], ["Anna", "Taufe", "Abendmahl"]]},
        zuordnung={"name": ["Teilnehmer"], "thema_1": ["A"], "thema_2": ["B"]},
    )
    assert not erg.meldungen and erg.personen[0].name == "Anna"


def test_fehlende_spalte_wird_gemeldet(tmp_path):
    erg = lese(tmp_path, {"Personen": [["Name", "Thema 1"], ["Anna", "Taufe"]]})
    assert any(f.spalte == "Thema 2" and f.zeile == 1 for f in erg.fehler)


def test_fehlendes_pflichtblatt(tmp_path):
    erg = lese(tmp_path, {"Themen": THEMEN})
    assert erg.fehler[0].blatt == "Personen"


def test_themen_werte_werden_geprueft(tmp_path):
    themen = [THEMEN[0], ["Taufe", 9, 2, 45], ["Abendmahl", 3, "viele", 90], ["Taufe", 1, 1, 45]]
    erg = lese(tmp_path, {"Personen": PERSONEN, "Themen": themen})
    assert {(f.zeile, f.spalte) for f in erg.fehler} >= {(2, "Wichtigkeit"), (3, "Mindestanzahl")}


def test_doppeltes_thema_im_blatt(tmp_path):
    themen = [THEMEN[0], ["Taufe", 3, 2, 45], ["Taufe", 1, 1, 45]]
    erg = lese(tmp_path, {"Personen": [PERSONEN[0], ["Anna", "Taufe", "Taufe2"]], "Themen": themen})
    assert any("doppelt" in f.text for f in erg.fehler)


def test_zeiten_in_verschiedenen_formaten(tmp_path):
    slots = [SLOTS[0], ["Mo", time(8, 0), datetime(2026, 1, 1, 8, 45)], ["Mo", 0.375, "9:30"]]
    erg = lese(tmp_path, {"Personen": PERSONEN, "Zeitslots": slots})
    assert not erg.fehler
    assert [(s.start, s.ende) for s in erg.zeitslots] == [(time(8), time(8, 45)), (time(9), time(9, 30))]


def test_ende_vor_start(tmp_path):
    erg = lese(tmp_path, {"Personen": PERSONEN, "Zeitslots": [SLOTS[0], ["Mo", "09:00", "08:00"]]})
    assert erg.fehler[0].spalte == "Ende"


def test_verfuegbarkeiten(tmp_path):
    verf = [["Person", "Tag", "Start"], ["Anna", "Mo", "08:45"], ["Anna", "Mo", time(9, 30)]]
    erg = lese(tmp_path, {"Personen": PERSONEN, "Zeitslots": SLOTS, "Verfügbarkeiten": verf})
    assert not erg.fehler
    assert erg.verfuegbarkeit == {"Anna": {1, 2}}
    assert erg.modell.verfuegbar("Ben", 0) and not erg.modell.verfuegbar("Anna", 0)


def test_verfuegbarkeiten_fehler(tmp_path):
    verf = [["Person", "Tag", "Start"], ["Zora", "Mo", "08:45"], ["Anna", "Di", "08:45"]]
    erg = lese(tmp_path, {"Personen": PERSONEN, "Zeitslots": SLOTS, "Verfügbarkeiten": verf})
    assert {(f.zeile, f.spalte) for f in erg.fehler} == {(2, "Person"), (3, "Start")}


def test_verfuegbarkeiten_ohne_zeitslots(tmp_path):
    erg = lese(
        tmp_path,
        {"Personen": PERSONEN, "Verfügbarkeiten": [["Person", "Tag", "Start"], ["Anna", "Mo", "08:00"]]},
    )
    assert erg.fehler


def test_leere_zeilen_werden_ignoriert(tmp_path):
    erg = lese(tmp_path, {"Personen": [*PERSONEN, [None, None, None], ["  ", " ", ""]]})
    assert not erg.meldungen


def test_formelzellen_zaehlen_mit_dem_berechneten_wert(tmp_path):
    # Eine frisch von openpyxl geschriebene Formel hat keinen berechneten Wert -> klare Meldung statt Absturz
    erg = lese(tmp_path, {"Personen": [PERSONEN[0], ['="An"&"na"', "Taufe", "Abendmahl"]]})
    assert [(f.zeile, f.spalte) for f in erg.fehler] == [(2, "Name")]


def test_umlaute_bleiben_erhalten(tmp_path):
    erg = lese(tmp_path, {"Personen": [PERSONEN[0], ["Jörg Müßig", "Tauffragen", "Ökumene"]]})
    assert erg.personen[0].name == "Jörg Müßig" and erg.personen[0].themen == ("Tauffragen", "Ökumene")


def test_beschaedigte_datei(tmp_path):
    datei = tmp_path / "kaputt.xlsx"
    datei.write_bytes(b"das ist keine excel-datei")
    with pytest.raises(ImportDateiFehler, match="kaputt.xlsx"):
        importiere(datei)


def test_nicht_vorhandene_datei(tmp_path):
    with pytest.raises(ImportDateiFehler):
        importiere(tmp_path / "gibt_es_nicht.xlsx")


def test_importdauer_500_personen_30_themen(tmp_path):
    import time as t

    themen = [THEMEN[0], *[[f"T{i}", 3, 2, 45] for i in range(30)]]
    personen = [PERSONEN[0], *[[f"P{i}", f"T{i % 30}", f"T{(i + 1) % 30}"] for i in range(500)]]
    pfad = schreibe(tmp_path / "gross.xlsx", {"Personen": personen, "Themen": themen, "Zeitslots": SLOTS})
    t0 = t.perf_counter()
    erg = importiere(pfad)
    assert t.perf_counter() - t0 < 2 and not erg.fehler and len(erg.personen) == 500
