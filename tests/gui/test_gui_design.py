"""TST-0022 – Design: Seitenleiste, Seitenkopf, Fachfarben, Ablegen, leere Zustände (CON-0016)."""

from pathlib import Path

from PySide6.QtCore import QEvent, QMimeData, QPointF, QRect, Qt, QUrl
from PySide6.QtGui import QDropEvent, QFocusEvent, QImage, QPainter, QShortcut
from PySide6.QtWidgets import QApplication, QStyleOptionViewItem

from konfiplaner.anwendung import Sitzung
from konfiplaner.gui.design import DUNKEL, fachfarbe
from konfiplaner.gui.fachfarben import KonferenzDelegate, konferenz_name
from konfiplaner.gui.hauptfenster import (
    SCHRITTE,
    SEITE_DATEN,
    SEITE_KONFERENZEN,
    SEITE_LEHRKRAEFTE,
    SEITE_PLANEN,
    SEITE_REGELN,
    Hauptfenster,
)
from konfiplaner.gui.seitenleiste import AKTUELL, FERTIG, GESPERRT, OFFEN
from tests.gui.test_gui_ablaeufe import FakeDialoge
from tests.unit.test_fixierungen_und_aenderungen import MI, ZEILEN
from tests.xlsx_helfer import PERSONEN, lehrer_mit_terminen, schreibe


def fenster(qtbot, tmp_path, laden=True):
    d = FakeDialoge()
    d.datei = schreibe(
        tmp_path / "k.xlsx",
        lehrer_mit_terminen(ZEILEN, ("Deutsch", *MI), ("Sport", "Mi", "15:00", "16:00"), ("Kunst", *MI)),
    )
    f = Hauptfenster(Sitzung(), d, auto_laden=False)
    qtbot.addWidget(f)
    f.show()
    if laden:
        f.datei_oeffnen()
    return f


def drop(f, *pfade: Path) -> None:
    daten = QMimeData()
    daten.setUrls([QUrl.fromLocalFile(str(p)) for p in pfade])
    f.dropEvent(
        QDropEvent(
            QPointF(10, 10),
            Qt.DropAction.CopyAction,
            daten,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
    )


def schritt(f, i):
    return f.leiste.schritte[i]


def test_seitenleiste_zeigt_alle_schritte_mit_nummer_name_und_kurzstatus(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path)
    assert [s.titel for s in f.leiste.schritte] == [
        "Daten",
        "Konferenzen",
        "Lehrkräfte",
        "Regeln",
        "Planen",
        "Ergebnis",
    ]
    assert [s.nummer for s in f.leiste.schritte] == [1, 2, 3, 4, 5, 6]
    assert schritt(f, 0).status == "6 Lehrkräfte" and schritt(f, 1).status == "3 von 3 ausgewählt"
    assert schritt(f, 2).status == "Unverändert" and schritt(f, 3).status == "6 hart, 3 weich"
    assert schritt(f, 4).status == "Bereit" and schritt(f, 5).status == "Noch kein Plan"
    assert all(s.accessibleName().startswith("Schritt ") for s in f.leiste.schritte)
    assert not f.reiter.tabBar().isVisible()  # die Seitenleiste ersetzt die Tab-Leiste


def test_kurzstatus_folgt_dem_stand(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path)
    f.konferenzen.tabelle.item(0, 0).setCheckState(Qt.CheckState.Unchecked)
    assert schritt(f, 1).status == "2 von 3 ausgewählt"
    f.sitzung.setze_konferenzen(["Anna Eins"], ["Sport"])
    f.lehrkraefte.aktualisieren()
    f._aktualisiere_zustand()
    assert schritt(f, 2).status == "1 neu zu verplanen"
    f.sitzung.planen()
    f.ergebnis.aktualisieren()
    f._aktualisiere_zustand()
    assert schritt(f, 4).status == "Plan berechnet" and schritt(f, 5).status in ("Optimal", "Nicht optimal")
    assert schritt(f, 4).zustand == OFFEN or schritt(f, 4).zustand == FERTIG


def test_zustaende_aktuell_fertig_gesperrt(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path)
    f.reiter.setCurrentIndex(SEITE_LEHRKRAEFTE)
    zustaende = [s.zustand for s in f.leiste.schritte]
    assert zustaende[SEITE_LEHRKRAEFTE] == AKTUELL and zustaende[SEITE_DATEN] == FERTIG
    assert zustaende[5] == GESPERRT  # noch kein Plan


def test_ohne_datei_sind_alle_schritte_ausser_daten_gesperrt(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path, laden=False)
    assert [s.zustand for s in f.leiste.schritte] == [AKTUELL] + [GESPERRT] * 5
    assert not any(s.isEnabled() for s in f.leiste.schritte[1:])
    assert schritt(f, 1).status == "Zuerst Datei laden" and schritt(f, 0).status == "Noch keine Datei"
    f.leiste.gewaehlt.emit(SEITE_PLANEN)
    assert f.reiter.currentIndex() == SEITE_DATEN  # gesperrte Schritte öffnen sich nicht


def test_wechsel_per_klick_und_seitenkopf(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path)
    qtbot.mouseClick(schritt(f, SEITE_PLANEN), Qt.MouseButton.LeftButton)
    assert f.reiter.currentIndex() == SEITE_PLANEN
    assert f.seitentitel.text() == "Plan berechnen" and "wer an welcher Konferenz" in f.seitenhilfe.text()
    assert schritt(f, SEITE_PLANEN).zustand == AKTUELL


def test_jede_seite_hat_titel_und_erklaerenden_satz(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path)
    f.sitzung.planen()
    f.ergebnis.aktualisieren()
    f._aktualisiere_zustand()
    gesehen = set()
    for i, (_kurz, titel, hilfe) in enumerate(SCHRITTE):
        f.reiter.setCurrentIndex(i)
        assert f.seitentitel.text() == titel and f.seitenhilfe.text() == hilfe and len(hilfe) > 30
        gesehen.add(titel)
    assert len(gesehen) == 6


def kuerzel(f):
    return {k.key().toString(): k for k in f.findChildren(QShortcut)}


def test_strg_zahl_wechselt_die_seite(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path)
    k = kuerzel(f)
    assert set(k) >= {f"Ctrl+{i}" for i in range(1, 7)}
    k["Ctrl+3"].activated.emit()
    assert f.reiter.currentIndex() == SEITE_LEHRKRAEFTE
    k["Ctrl+2"].activated.emit()
    assert f.reiter.currentIndex() == SEITE_KONFERENZEN
    k["Ctrl+6"].activated.emit()
    assert f.reiter.currentIndex() == SEITE_KONFERENZEN  # Ergebnis ist gesperrt (noch kein Plan)
    k["Ctrl+1"].activated.emit()
    assert f.reiter.currentIndex() == SEITE_DATEN


def test_pfeiltasten_bewegen_den_fokus_in_der_seitenleiste(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path)
    schritt(f, 0).setFocus()
    qtbot.keyClick(schritt(f, 0), Qt.Key.Key_Down)
    assert f.focusWidget() is schritt(f, 1)
    qtbot.keyClick(schritt(f, 1), Qt.Key.Key_Up)
    assert f.focusWidget() is schritt(f, 0)
    qtbot.keyClick(schritt(f, 0), Qt.Key.Key_Down)
    qtbot.keyClick(schritt(f, 1), Qt.Key.Key_Return)
    assert f.reiter.currentIndex() == SEITE_KONFERENZEN


def test_fokusring_nur_bei_tastaturbedienung(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path)
    s = schritt(f, 0)
    QApplication.sendEvent(s, QFocusEvent(QEvent.Type.FocusIn, Qt.FocusReason.MouseFocusReason))
    assert not s._tastaturfokus
    QApplication.sendEvent(s, QFocusEvent(QEvent.Type.FocusIn, Qt.FocusReason.TabFocusReason))
    assert s._tastaturfokus


def test_primaere_aktion_je_seite_ist_hervorgehoben(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path)
    assert f.daten.oeffnen.property("primaer") is True
    assert f.planen.planen.property("primaer") is True and not f.planen.abbrechen.property("primaer")
    assert f.ergebnis.exportieren.property("primaer") is True
    assert f.lehrkraefte.teil.property("primaer") is True and not f.lehrkraefte.alles.property("primaer")
    assert not f.daten.neu_laden.property("primaer") and not f.konferenzen.alle.property("primaer")


def test_fachfarbe_ist_in_konferenzliste_und_tabellen_gleich(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path)
    erwartet = fachfarbe("Deutsch").name()
    # Konferenzen: Punkt im Symbol der Zeile
    t = f.konferenzen.tabelle
    zeile = next(i for i in range(t.rowCount()) if t.item(i, 0).text() == "Deutsch")
    assert t.item(zeile, 0).icon().pixmap(20, 20).toImage().pixelColor(10, 10).name() == erwartet
    # Lehrkräfte und Ergebnis: Punkt vom Delegate
    f.sitzung.planen()
    f.ergebnis.aktualisieren()
    for ansicht, spalte in ((f.lehrkraefte.tabelle, 1), (f.ergebnis.tabellen["Termine"], 3)):
        delegate = ansicht.itemDelegateForColumn(spalte)
        assert isinstance(delegate, KonferenzDelegate)
        zeilen = [
            r
            for r in range(ansicht.model().rowCount())
            if "Deutsch" in str(ansicht.model().index(r, spalte).data())
        ]
        assert zeilen
        bild = QImage(400, 30, QImage.Format.Format_ARGB32)
        bild.fill(Qt.GlobalColor.black)
        maler = QPainter(bild)
        option = QStyleOptionViewItem()
        option.rect, option.widget, option.font = QRect(0, 0, 400, 30), ansicht, ansicht.font()
        option.palette = ansicht.palette()
        # der Delegate zeichnet den Punkt vor dem ersten Namen; bei „Deutsch" an erster Stelle in der Zeile
        index = ansicht.model().index(zeilen[0], spalte)
        if str(index.data()).startswith("Deutsch"):
            delegate.paint(maler, option, index)
            maler.end()
            assert bild.pixelColor(14, 15).name() == erwartet
        else:
            maler.end()


def test_konferenzname_aus_eintrag():
    assert konferenz_name("Deutsch (Mi 14:00–15:00)") == "Deutsch" and konferenz_name(" Sport ") == "Sport"


def test_leerer_zustand_nennt_den_naechsten_schritt(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path, laden=False)
    assert f.daten.stapel.currentWidget() is f.daten.leer
    texte = [w.text() for w in f.daten.leer.findChildren(type(f.seitentitel))]
    assert "Noch keine Datei" in texte and "Excel-Datei öffnen oder hier ablegen." in texte
    f.datei_oeffnen()
    assert f.daten.stapel.currentWidget() is f.daten.inhalt


def test_leere_listen_sagen_was_los_ist(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path)
    assert f.konferenzen.neu_zuordnen.platzhalter.startswith("Niemand")
    assert f.konferenzen.neu_zuordnen.count() == 0 and f.konferenzen.ohne_konferenz.count() == 0


def test_datei_ablegen_laedt_sie(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path, laden=False)
    datei = schreibe(tmp_path / "abgelegt.xlsx", {"Personen": PERSONEN})
    drop(f, datei)
    assert (
        f.sitzung.datei == datei and f.sitzung.ergebnis is not None and len(f.sitzung.ergebnis.personen) == 2
    )
    assert schritt(f, 0).zustand in (FERTIG, AKTUELL) and f.leiste.datei.text() == "abgelegt.xlsx"


def test_andere_datei_ablegen_wird_ignoriert_und_erklaert(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path, laden=False)
    text = tmp_path / "notizen.txt"
    text.write_text("x")
    drop(f, text)
    assert f.sitzung.ergebnis is None
    assert "notizen.txt" in f.statusBar().currentMessage() and ".xlsx" in f.statusBar().currentMessage()


def test_mehrere_dateien_ablegen_nimmt_die_erste_excel_datei(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path, laden=False)
    text = tmp_path / "a.txt"
    text.write_text("x")
    datei = schreibe(tmp_path / "b.xlsx", {"Personen": PERSONEN})
    drop(f, text, datei)
    assert f.sitzung.datei == datei


def test_statuswerte_stehen_als_text_und_in_farbe(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path)
    f.sitzung.setze_konferenzen(["Anna Eins"], ["Sport"])
    f.lehrkraefte.aktualisieren()
    p = f.lehrkraefte.proxy
    zeile = next(i for i in range(p.rowCount()) if p.index(i, 0).data() == "Anna Eins")
    status = p.index(zeile, 3)
    assert "neu zu verplanen" in status.data()
    assert status.data(Qt.ItemDataRole.ForegroundRole).name().lower() == DUNKEL.konflikt.lower()
    assert p.index(zeile, 0).data(Qt.ItemDataRole.BackgroundRole) is not None


def test_ergebnis_status_ist_farbig_und_im_klartext(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path)
    f.sitzung.planen()
    f.ergebnis.aktualisieren()
    text = f.ergebnis.status.text()
    assert "Plan ist optimal" in text and DUNKEL.ok in text


def test_planen_seite_nennt_den_umfang(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path)
    assert f.planen.umfang.text() == "Geplant werden 3 Konferenzen mit 3 festen Terminen für 6 Lehrkräfte."
    assert f.planen.voraussetzung.property("zustand") == "bereit"
    f.sitzung.waehle_alle(False)
    f.planen.aktualisieren()
    assert f.planen.voraussetzung.property("zustand") == "blockiert"


def test_dateiname_in_der_seitenleiste(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path, laden=False)
    assert f.leiste.datei.text() == "Keine Datei geladen"
    f.datei_oeffnen()
    assert f.leiste.datei.text() == "k.xlsx"


def test_pruefschritte_bekommen_haken_nach_dem_ansehen(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path)
    for seite in (SEITE_KONFERENZEN, SEITE_LEHRKRAEFTE, SEITE_REGELN):
        assert schritt(f, seite).zustand != FERTIG
    for seite in (SEITE_KONFERENZEN, SEITE_LEHRKRAEFTE, SEITE_REGELN, SEITE_PLANEN):
        f.reiter.setCurrentIndex(seite)
    assert [schritt(f, i).zustand for i in (1, 2, 3)] == [FERTIG] * 3
    f.neu_laden()  # neue Daten: Prüfschritte beginnen von vorn
    assert [schritt(f, i).zustand for i in (1, 2, 3)] != [FERTIG] * 3 and schritt(f, 2).zustand == OFFEN
