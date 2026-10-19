"""TST-0018 – Konferenzauswahl in der GUI (CON-0014)."""

from PySide6.QtCore import Qt

from konfiplaner.anwendung import Sitzung
from konfiplaner.gui.hauptfenster import SEITE_ERGEBNIS, SEITE_KONFERENZEN, Hauptfenster
from tests.gui.test_gui_ablaeufe import FakeDialoge, plane_und_warte
from tests.unit.test_auswahl_in_der_sitzung import MI, ZEILEN
from tests.xlsx_helfer import lehrer_mit_terminen, schreibe


def fenster(qtbot, tmp_path):
    d = FakeDialoge()
    d.datei = schreibe(
        tmp_path / "k.xlsx",
        lehrer_mit_terminen(ZEILEN, ("Deutsch", *MI), ("Sport", *MI), ("Kunst", "Mi", "15:00", "16:00")),
    )
    f = Hauptfenster(Sitzung(), d, auto_laden=False)
    qtbot.addWidget(f)
    f.show()
    f.datei_oeffnen()
    return f


def haken(f, name, an):
    seite = f.konferenzen
    zeile = next(i for i in range(seite.tabelle.rowCount()) if seite.tabelle.item(i, 0).text() == name)
    seite.tabelle.item(zeile, 0).setCheckState(Qt.CheckState.Checked if an else Qt.CheckState.Unchecked)


def test_lehrerliste_landet_auf_der_seite_konferenzen(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path)
    assert f.reiter.currentIndex() == SEITE_KONFERENZEN
    t = f.konferenzen.tabelle
    assert t.rowCount() == 3 and f.konferenzen.zaehler.text() == "3 von 3 Konferenzen ausgewählt"
    zeile = {t.item(i, 0).text(): [t.item(i, c).text() for c in (1, 2, 3)] for i in range(3)}
    assert zeile["Sport"] == ["3", "Ben Zwei", "1"]
    assert all(t.item(i, 0).checkState() == Qt.CheckState.Checked for i in range(3))


def test_abwaehlen_zeigt_neu_zuordnen_und_wirkt_im_plan(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path)
    haken(f, "Kunst", False)
    k = f.konferenzen
    assert [k.neu_zuordnen.item(i).text() for i in range(k.neu_zuordnen.count())] == ["Cem Drei"]
    assert [k.ohne_konferenz.item(i).text() for i in range(k.ohne_konferenz.count())] == ["Dora Vier"]
    assert k.zaehler.text() == "2 von 3 Konferenzen ausgewählt"
    plane_und_warte(qtbot, f)
    assert f.reiter.currentIndex() == SEITE_ERGEBNIS
    assert "Kunst" not in [z[3] for z in f.ergebnis.modelle["Termine"].zeilen()]
    assert ["Warnung", "Cem Drei hat durch die Auswahl keine Konferenz"] in f.ergebnis.modelle[
        "Hinweise"
    ].zeilen()


def test_alle_und_keine(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path)
    qtbot.mouseClick(f.konferenzen.keine, Qt.MouseButton.LeftButton)
    assert (
        f.konferenzen.zaehler.text() == "0 von 3 Konferenzen ausgewählt" and not f.planen.planen.isEnabled()
    )
    assert "Keine Konferenz ausgewählt" in f.planen.voraussetzung.text()
    qtbot.mouseClick(f.konferenzen.alle, Qt.MouseButton.LeftButton)
    assert f.konferenzen.zaehler.text() == "3 von 3 Konferenzen ausgewählt" and f.planen.planen.isEnabled()


def test_aenderung_der_auswahl_verwirft_den_plan_in_der_gui(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path)
    plane_und_warte(qtbot, f)
    assert f.reiter.isTabEnabled(SEITE_ERGEBNIS)
    f.reiter.setCurrentIndex(SEITE_KONFERENZEN)
    haken(f, "Sport", False)
    assert not f.reiter.isTabEnabled(SEITE_ERGEBNIS) and f.sitzung.plan is None


def test_konferenzseite_ist_beschriftet(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path)
    k = f.konferenzen
    assert k.alle.text().strip() and k.keine.text().strip()
    for w in (k.tabelle, k.neu_zuordnen, k.ohne_konferenz):
        assert w.accessibleName()


def test_minimalformat_geht_weiter_direkt_zu_planen(qtbot, tmp_path):
    from tests.gui.test_gui_ablaeufe import PERSONEN_VIELE
    from tests.xlsx_helfer import SLOTS

    d = FakeDialoge()
    d.datei = schreibe(tmp_path / "m.xlsx", {"Personen": PERSONEN_VIELE, "Zeitslots": SLOTS})
    f = Hauptfenster(Sitzung(), d, auto_laden=False)
    qtbot.addWidget(f)
    f.datei_oeffnen()
    from konfiplaner.gui.hauptfenster import SEITE_PLANEN

    assert f.reiter.currentIndex() == SEITE_PLANEN
