"""TST-0010 – GUI-Abläufe per pytest-qt, offscreen (CON-0010). Testnamen folgen den Szenarien der .feature-Datei."""

import threading
from datetime import time
from pathlib import Path

import pytest
from PySide6.QtCore import Qt

from konfiplaner.anwendung import Sitzung
from konfiplaner.einstellungen import YamlEinstellungen
from konfiplaner.gui.hauptfenster import (
    SEITE_DATEN,
    SEITE_ERGEBNIS,
    SEITE_KONFERENZEN,
    SEITE_PLANEN,
    Hauptfenster,
)
from konfiplaner.modell import Plan
from tests.xlsx_helfer import PERSONEN, SLOTS, schreibe


class FakeDialoge:
    def __init__(self) -> None:
        self.datei: Path | None = None
        self.ziel: Path | None = None
        self.antwort = True
        self.fehler_meldungen: list[str] = []
        self.fragen: list[str] = []

    def datei_oeffnen(self, start):
        return self.datei

    def regeldatei_oeffnen(self, start):
        return None

    def export_ziel(self, start):
        return self.ziel

    def ja_nein(self, titel, text):
        self.fragen.append(text)
        return self.antwort

    def fehler(self, titel, text):
        self.fehler_meldungen.append(text)

    def info(self, titel, text):
        pass


class BlockierenderPlaner:
    """Läuft, bis das Abbruchsignal kommt; liefert dann die 'beste bisherige Lösung'."""

    def __init__(self) -> None:
        self.gestartet = threading.Event()

    def planen(self, modell, konfiguration, optionen=None, fortschritt=None, abbruch=None):
        self.gestartet.set()
        abbruch.wait(30)  # threading.Event des Arbeiters
        return Plan("machbar")


PERSONEN_VIELE = [PERSONEN[0], *[[f"P{i}", "Taufe", "Abendmahl"] for i in range(6)]]


def fenster(qtbot, tmp_path, blaetter=None, planer=None, **kw):
    dialoge = FakeDialoge()
    sitzung = Sitzung(kw.pop("einstellungen", None), planer=planer)
    f = Hauptfenster(sitzung, dialoge, auto_laden=kw.pop("auto_laden", False))
    qtbot.addWidget(f)
    f.show()
    if blaetter is not None:
        dialoge.datei = schreibe(tmp_path / "konfis.xlsx", blaetter)
    return f, dialoge


def plane_und_warte(qtbot, f):
    with qtbot.waitSignal(f.planen.plan_fertig, timeout=60000):
        qtbot.mouseClick(f.planen.planen, Qt.MouseButton.LeftButton)


def test_voller_durchlauf(qtbot, tmp_path):
    f, d = fenster(qtbot, tmp_path, {"Personen": PERSONEN_VIELE, "Zeitslots": SLOTS})
    qtbot.mouseClick(f.daten.oeffnen, Qt.MouseButton.LeftButton)
    assert f.reiter.currentIndex() == SEITE_PLANEN and f.planen.planen.isEnabled()
    plane_und_warte(qtbot, f)
    assert f.reiter.currentIndex() == SEITE_ERGEBNIS
    assert f.ergebnis.modelle["Termine"].rowCount() > 0 and f.ergebnis.modelle["Personen"].rowCount() > 0
    d.ziel = tmp_path / "plan.xlsx"
    qtbot.mouseClick(f.ergebnis.exportieren, Qt.MouseButton.LeftButton)
    assert d.ziel.exists() and "Exportiert" in f.statusBar().currentMessage()


def test_fehlerhafte_datei_zeigt_fehlerliste_und_sperrt_planen(qtbot, tmp_path):
    kaputt = [PERSONEN[0], ["Anna", "Taufe", "Taufe"], ["Ben", "Taufe", "Abendmahl"]]
    f, _ = fenster(qtbot, tmp_path, {"Personen": kaputt, "Zeitslots": SLOTS})
    f.datei_oeffnen()
    assert f.reiter.currentIndex() == SEITE_DATEN
    assert f.daten.meldungen.rowCount() == 1
    assert not f.planen.planen.isEnabled() and "Fehler" in f.planen.voraussetzung.text()


def test_klick_auf_fehler_markiert_die_quelle(qtbot, tmp_path):
    kaputt = [PERSONEN[0], ["Anna", "Taufe", "Abendmahl"], ["Ben", "Taufe", "Taufe"]]
    f, _ = fenster(qtbot, tmp_path, {"Personen": kaputt})
    f.datei_oeffnen()
    with qtbot.waitSignal(f.daten.quelle_markiert) as signal:
        f.daten.meldungs_tabelle.clicked.emit(f.daten.meldungen.index(0, 0))
    assert signal.args == ["Personen", 3, "Thema 2"]
    aktuell = f.daten.vorschau_tabelle.currentIndex()
    assert (aktuell.row(), aktuell.column()) == (1, 2)  # Excel-Zeile 3 = zweite Datenzeile, Spalte Thema 2
    assert "Zeile 3" in f.statusBar().currentMessage()


def test_themenwerte_und_zeitslots_ergaenzen(qtbot, tmp_path):
    f, _ = fenster(qtbot, tmp_path, {"Personen": PERSONEN_VIELE})
    f.datei_oeffnen()
    assert f.reiter.currentIndex() == SEITE_DATEN and not f.planen.planen.isEnabled()
    assert "Zeitslots" in f.planen.voraussetzung.text()
    f.daten.tage.setText("Samstag")
    qtbot.mouseClick(f.daten.erzeugen, Qt.MouseButton.LeftButton)
    assert f.planen.planen.isEnabled() and f.daten.slots.rowCount() == 4  # 09:00–12:00 in 45-min-Slots
    index = f.daten.themen.index(0, 2)
    assert f.daten.themen.setData(index, "3") and f.sitzung.themen[0].mindestanzahl == 3


def test_ungueltiger_themenwert_wird_abgelehnt(qtbot, tmp_path):
    f, _ = fenster(qtbot, tmp_path, {"Personen": PERSONEN_VIELE})
    f.datei_oeffnen()
    with qtbot.waitSignal(f.daten.themen.abgelehnt):
        assert not f.daten.themen.setData(f.daten.themen.index(0, 1), "9")
    with qtbot.waitSignal(f.daten.themen.abgelehnt):
        assert not f.daten.themen.setData(f.daten.themen.index(0, 1), "abc")
    assert f.sitzung.themen[0].wichtigkeit == 3


def test_planen_nicht_moeglich_ohne_datei(qtbot, tmp_path):
    f, _ = fenster(qtbot, tmp_path)
    assert not f.planen.planen.isEnabled()
    assert not f.reiter.isTabEnabled(SEITE_ERGEBNIS) and not f.aktion_export.isEnabled()


def test_planung_abbrechen_haelt_gui_bedienbar(qtbot, tmp_path):
    planer = BlockierenderPlaner()
    f, _ = fenster(qtbot, tmp_path, {"Personen": PERSONEN_VIELE, "Zeitslots": SLOTS}, planer=planer)
    f.datei_oeffnen()
    qtbot.mouseClick(f.planen.planen, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(planer.gestartet.is_set, timeout=5000)
    assert f.planen.laeuft and f.planen.abbrechen.isEnabled() and not f.planen.planen.isEnabled()
    f.statusBar().showMessage("lebt")  # GUI-Thread antwortet
    assert f.statusBar().currentMessage() == "lebt"
    with qtbot.waitSignal(f.planen.plan_fertig, timeout=5000) as signal:
        qtbot.mouseClick(f.planen.abbrechen, Qt.MouseButton.LeftButton)
    assert signal.args[0].status == "machbar" and not f.planen.laeuft
    assert f.reiter.currentIndex() == SEITE_ERGEBNIS


def test_regel_anpassen_wirkt_auf_die_planung(qtbot, tmp_path):
    f, _ = fenster(qtbot, tmp_path, {"Personen": PERSONEN_VIELE, "Zeitslots": SLOTS})
    f.datei_oeffnen()
    zeile = f.regeln._zeile("schwerpunkte")
    box, gewicht = f.regeln.tabelle.cellWidget(zeile, 1), f.regeln.tabelle.cellWidget(zeile, 2)
    assert not gewicht.isEnabled()
    box.setCurrentIndex(box.findData("weich"))
    gewicht.setValue(4)
    assert gewicht.isEnabled()
    regel = {r.name: r for r in f.sitzung.regeln()}["schwerpunkte"]
    assert (regel.typ, regel.gewicht) == ("weich", 4.0)


def test_einstellungen_werden_wiederhergestellt(qtbot, tmp_path):
    speicher = tmp_path / "e.yaml"
    f, d = fenster(
        qtbot,
        tmp_path,
        {"Personen": PERSONEN_VIELE, "Zeitslots": SLOTS},
        einstellungen=YamlEinstellungen(speicher),
    )
    f.datei_oeffnen()
    box = f.regeln.tabelle.cellWidget(f.regeln._zeile("schwerpunkte"), 1)
    box.setCurrentIndex(box.findData("weich"))
    f.close()

    neu = Hauptfenster(Sitzung(YamlEinstellungen(speicher)), FakeDialoge())
    qtbot.addWidget(neu)
    assert neu.sitzung.datei == d.datei and str(d.datei) in neu.daten.pfad.text()
    assert {r.name: r for r in neu.sitzung.regeln()}["schwerpunkte"].typ == "weich"
    assert neu.reiter.currentIndex() == SEITE_PLANEN  # Datei wurde wieder geladen


def test_export_ueberschreiben_nur_nach_bestaetigung(qtbot, tmp_path):
    f, d = fenster(qtbot, tmp_path, {"Personen": PERSONEN_VIELE, "Zeitslots": SLOTS})
    f.datei_oeffnen()
    plane_und_warte(qtbot, f)
    d.ziel = tmp_path / "plan.xlsx"
    d.ziel.write_text("alt")
    d.antwort = False
    f.exportieren()
    assert d.ziel.read_text() == "alt" and d.fragen and "abgebrochen" in f.statusBar().currentMessage()
    d.antwort = True
    f.exportieren()
    assert d.ziel.read_bytes()[:2] == b"PK"  # xlsx = zip


def test_export_fehler_wird_gemeldet(qtbot, tmp_path):
    f, d = fenster(qtbot, tmp_path, {"Personen": PERSONEN_VIELE, "Zeitslots": SLOTS})
    f.datei_oeffnen()
    plane_und_warte(qtbot, f)
    d.ziel = tmp_path / "plan.xlsx"
    (tmp_path / "~$plan.xlsx").write_text("")
    f.exportieren()
    assert d.fehler_meldungen and "geöffnet" in d.fehler_meldungen[0]


def test_unlesbare_datei_zeigt_meldung_statt_absturz(qtbot, tmp_path):
    f, d = fenster(qtbot, tmp_path)
    d.datei = tmp_path / "kaputt.xlsx"
    d.datei.write_bytes(b"x")
    f.datei_oeffnen()
    assert d.fehler_meldungen and "kaputt.xlsx" in d.fehler_meldungen[0]
    assert f.sitzung.ergebnis is None


def test_geaenderte_datei_bietet_neuladen_an(qtbot, tmp_path):
    import os

    f, d = fenster(qtbot, tmp_path, {"Personen": PERSONEN_VIELE, "Zeitslots": SLOTS})
    f.datei_oeffnen()
    assert not f.pruefe_dateiaenderung()
    os.utime(d.datei, (d.datei.stat().st_atime, d.datei.stat().st_mtime + 10))
    assert f.pruefe_dateiaenderung() and d.fragen
    assert not f.pruefe_dateiaenderung()  # nicht erneut fragen, wenn nichts Neues


def test_ergebnis_hebt_verletzungen_hervor(qtbot, tmp_path):
    # Mindestanzahl 5, aber nur 6 Personen mit zwei Themen, deren Termine sich nicht ausgehen -> Themen "nein" möglich
    f, _ = fenster(qtbot, tmp_path, {"Personen": PERSONEN_VIELE, "Zeitslots": SLOTS})
    f.datei_oeffnen()
    plan = Plan("machbar", warnungen=["Hinweis"])
    f.sitzung.plan, f.sitzung.plan_modell = plan, f.sitzung.modell()
    f.ergebnis.aktualisieren()
    themen = f.ergebnis.modelle["Themen"]
    assert themen.data(themen.index(0, 0), Qt.ItemDataRole.BackgroundRole) is not None  # Erfüllt = nein
    hinweise = f.ergebnis.modelle["Hinweise"]
    assert hinweise.rowCount() == 2  # Status + Warnung
    assert hinweise.data(hinweise.index(0, 0), Qt.ItemDataRole.BackgroundRole) is not None
    assert "nicht als optimal" in f.ergebnis.status.text()


def test_alle_bedienelemente_sind_beschriftet(qtbot, tmp_path):
    f, _ = fenster(qtbot, tmp_path, {"Personen": PERSONEN_VIELE, "Zeitslots": SLOTS})
    f.datei_oeffnen()
    for knopf in (
        f.daten.oeffnen,
        f.daten.neu_laden,
        f.daten.erzeugen,
        f.planen.planen,
        f.planen.abbrechen,
        f.ergebnis.exportieren,
        f.regeln.standard,
    ):
        assert knopf.text().strip()
    for tabelle in (
        f.daten.meldungs_tabelle,
        f.daten.themen_tabelle,
        f.daten.slot_tabelle,
        *f.ergebnis.tabellen.values(),
    ):
        assert tabelle.accessibleName()


@pytest.mark.parametrize("seite", [SEITE_DATEN, SEITE_PLANEN])
def test_fenster_passt_auf_kleine_bildschirme(qtbot, tmp_path, seite):
    f, _ = fenster(qtbot, tmp_path, {"Personen": PERSONEN_VIELE, "Zeitslots": SLOTS})
    f.datei_oeffnen()
    f.reiter.setCurrentIndex(seite)
    f.resize(1024, 600)
    assert f.minimumSizeHint().width() <= 1024 and f.minimumSizeHint().height() <= 600


def test_vorsitz_in_themen_tabelle_waehlen(qtbot, tmp_path):
    f, _ = fenster(qtbot, tmp_path, {"Personen": PERSONEN_VIELE, "Zeitslots": SLOTS})
    f.datei_oeffnen()
    modell = f.daten.themen
    assert modell.columnCount() == 5 and modell.headerData(4, Qt.Orientation.Horizontal) == "Vorsitz"
    assert modell.setData(modell.index(0, 4), "P1")
    assert f.sitzung.themen[0].vorsitz == "P1" and modell.data(modell.index(0, 4)) == "P1"
    with qtbot.waitSignal(modell.abgelehnt):
        assert not modell.setData(modell.index(0, 4), "Unbekannt")
    assert modell.setData(modell.index(0, 4), "")  # "(keiner)"
    assert f.sitzung.themen[0].vorsitz is None


def test_vorsitz_auswahl_bietet_alle_personen(qtbot, tmp_path):
    f, _ = fenster(qtbot, tmp_path, {"Personen": PERSONEN_VIELE, "Zeitslots": SLOTS})
    f.datei_oeffnen()
    delegate = f.daten.themen_tabelle.itemDelegateForColumn(4)
    box = delegate.createEditor(f.daten, None, f.daten.themen.index(0, 4))
    namen = [box.itemData(i) for i in range(box.count())]
    assert namen[0] == "" and set(namen[1:]) == set(f.sitzung.personen_namen())


def test_planen_mit_vorsitz_ueber_die_gui(qtbot, tmp_path):
    f, _ = fenster(qtbot, tmp_path, {"Personen": PERSONEN_VIELE, "Zeitslots": SLOTS})
    f.datei_oeffnen()
    f.daten.themen.setData(f.daten.themen.index(0, 4), "P3")
    plane_und_warte(qtbot, f)
    termine = f.ergebnis.modelle["Termine"].zeilen()
    assert termine and all(z[4] == "P3" for z in termine if z[3] == f.sitzung.themen[0].name)


# ── Lehrerliste und Normalisierung (SPEC-0007) ──────────────────────────────
def lehrer_fenster(qtbot, tmp_path, zeilen=None):
    from tests.xlsx_helfer import LEHRER, lehrerliste

    daten = [*LEHRER, *(zeilen or [])]
    return fenster(qtbot, tmp_path, lehrerliste(daten))


def test_gui_zeigt_normalisierung_und_personen_ohne_konferenz(qtbot, tmp_path):
    f, _ = lehrer_fenster(
        qtbot,
        tmp_path,
        [["Berg", "Eva", "", "Mathe", None, None, None], ["Wolf", "Uwe", "", None, None, None, None]],
    )
    f.datei_oeffnen()
    d = f.daten
    assert d.reiter.isTabVisible(d.TAB_NORMALISIERUNG) and d.reiter.isTabVisible(d.TAB_OHNE)
    assert [d.ohne_konferenz.item(i).text() for i in range(d.ohne_konferenz.count())] == ["Uwe Wolf"]
    erste = d.normalisierung.zeile(0)  # offene Werte stehen oben
    assert (erste.roh, erste.status) == ("Mathe", "vorschlag")
    assert d.normalisierung.data(d.normalisierung.index(0, 3)) == "Vorschlag – bitte bestätigen"
    assert d.normalisierung.data(d.normalisierung.index(0, 0), Qt.ItemDataRole.BackgroundRole) is not None
    assert not f.planen.planen.isEnabled()  # Fehler offen -> nicht planbar


def test_gui_alle_vorschlaege_uebernehmen_macht_planbar(qtbot, tmp_path):
    f, _ = lehrer_fenster(qtbot, tmp_path, [["Berg", "Eva", "", "Mathe", "Sport/Deutsch", None, None]])
    f.datei_oeffnen()
    assert f.daten.vorschlaege.isEnabled()
    qtbot.mouseClick(f.daten.vorschlaege, Qt.MouseButton.LeftButton)
    assert not f.sitzung.ergebnis.fehler and f.sitzung.planbar and f.planen.planen.isEnabled()
    assert not f.daten.vorschlaege.isEnabled() and f.daten.meldungen.rowCount() == 0
    assert "Vorschläge übernommen" in f.statusBar().currentMessage()


def test_gui_zuordnung_von_hand_aendern(qtbot, tmp_path):
    f, _ = lehrer_fenster(qtbot, tmp_path, [["Berg", "Eva", "", "TC", None, None, None]])
    f.datei_oeffnen()
    modell = f.daten.normalisierung
    assert (modell.zeile(0).roh, modell.zeile(0).status) == ("TC", "unbekannt")
    with qtbot.waitSignal(modell.abgelehnt):
        assert not modell.setData(modell.index(0, 2), "  ")
    assert modell.setData(modell.index(0, 2), "Technik")
    assert not f.sitzung.ergebnis.fehler
    assert next(p for p in f.sitzung.ergebnis.personen if p.name == "Eva Berg").themen == ("Technik",)


def test_gui_lehrerliste_plant_und_exportiert_vorsitz(qtbot, tmp_path):
    f, _ = lehrer_fenster(qtbot, tmp_path, [["Wolf", "Uwe", "", None, None, None, None]])
    f.datei_oeffnen()
    assert f.reiter.currentIndex() == SEITE_KONFERENZEN and f.planen.planen.isEnabled()
    plane_und_warte(qtbot, f)
    termine = f.ergebnis.modelle["Termine"].zeilen()
    assert {z[3]: z[4] for z in termine}["Deutsch"] == "Anna Meier"
    hinweise = f.ergebnis.modelle["Hinweise"].zeilen()
    assert ["Warnung", "Uwe Wolf hat keine Konferenz"] in hinweise


def test_gui_minimalformat_blendet_lehrerlisten_reiter_aus(qtbot, tmp_path):
    f, _ = fenster(qtbot, tmp_path, {"Personen": PERSONEN_VIELE, "Zeitslots": SLOTS})
    f.datei_oeffnen()
    assert not f.daten.reiter.isTabVisible(f.daten.TAB_NORMALISIERUNG)
    assert not f.daten.reiter.isTabVisible(f.daten.TAB_OHNE)


# ── Konferenzplanung mit festen Terminen (SPEC-0008) ────────────────────────
def termine_fenster(qtbot, tmp_path, *termine):
    from tests.xlsx_helfer import lehrer_mit_terminen

    zeilen = [
        ["Eins", "Anna", "", "Deutsch", "Sport", None, None],
        ["Zwei", "Ben", "", "Deutsch", None, None, "Deutsch"],
        ["Drei", "Cem", "", "Sport", None, None, "Sport"],
    ]
    return fenster(qtbot, tmp_path, lehrer_mit_terminen(zeilen, *termine))


def test_gui_zeigt_termine_je_konferenz_und_sperrt_das_zeitraster(qtbot, tmp_path):
    f, _ = termine_fenster(
        qtbot, tmp_path, ("Deutsch", "Mi", "14:00", "15:00"), ("Sport", "Mi", "15:00", "16:00")
    )
    f.datei_oeffnen()
    d = f.daten
    assert d.reiter.isTabVisible(d.TAB_TERMINE)
    assert [z[:4] for z in d.termine.zeilen()] == [
        ["Deutsch", "Mi", time(14), time(15)],
        ["Sport", "Mi", time(15), time(16)],
    ]
    assert not d.erzeugen.isEnabled() and not d.tage.isEnabled()
    assert "Konferenzen" in d.slot_info.text()
    assert f.reiter.currentIndex() == SEITE_KONFERENZEN and f.planen.planen.isEnabled()


def test_gui_plant_gleichzeitige_konferenzen_und_zeigt_konflikte(qtbot, tmp_path):
    f, _ = termine_fenster(
        qtbot, tmp_path, ("Deutsch", "Mi", "14:00", "15:00"), ("Sport", "Mi", "14:00", "15:00")
    )
    f.datei_oeffnen()
    plane_und_warte(qtbot, f)
    hinweise = f.ergebnis.modelle["Hinweise"].zeilen()
    assert ["Verstoß", "schwerpunkte: Anna Eins nimmt nicht an Schwerpunkt Sport teil"] in hinweise
    assert "1 Verstöße" in f.ergebnis.status.text()
    # Regel zeigt sich in der Regelverwaltung als weich (Profil), ohne dass jemand sie gesetzt hat
    zeile = f.regeln._zeile("schwerpunkte")
    assert f.regeln.tabelle.cellWidget(zeile, 1).currentData() == "weich"


def test_gui_ohne_konferenzblatt_hat_keinen_termine_reiter(qtbot, tmp_path):
    f, _ = fenster(qtbot, tmp_path, {"Personen": PERSONEN_VIELE, "Zeitslots": SLOTS})
    f.datei_oeffnen()
    assert not f.daten.reiter.isTabVisible(f.daten.TAB_TERMINE) and f.daten.erzeugen.isEnabled()
