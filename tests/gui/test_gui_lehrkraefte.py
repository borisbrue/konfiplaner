"""TST-0020 – Lehrkräfte, Dialoge und Teilneuplanung in der GUI (CON-0015)."""

from PySide6.QtCore import QItemSelectionModel, Qt

from konfiplaner.anwendung import Sitzung
from konfiplaner.gui.hauptfenster import SEITE_ERGEBNIS, SEITE_LEHRKRAEFTE, SEITE_PLANEN, Hauptfenster
from konfiplaner.gui.lehrkraft_dialoge import LehrkraftDialog, SammelDialog
from konfiplaner.modell import ModellFehler
from tests.gui.test_gui_ablaeufe import BlockierenderPlaner, FakeDialoge, plane_und_warte
from tests.unit.test_fixierungen_und_aenderungen import MI, ZEILEN
from tests.xlsx_helfer import lehrer_mit_terminen, schreibe

AUSWAHL = QItemSelectionModel.SelectionFlag.Select | QItemSelectionModel.SelectionFlag.Rows


def fenster(qtbot, tmp_path, planer=None):
    d = FakeDialoge()
    d.datei = schreibe(
        tmp_path / "k.xlsx",
        lehrer_mit_terminen(ZEILEN, ("Deutsch", *MI), ("Sport", "Mi", "15:00", "16:00"), ("Kunst", *MI)),
    )
    f = Hauptfenster(Sitzung(planer=planer), d, auto_laden=False)
    qtbot.addWidget(f)
    f.show()
    f.datei_oeffnen()
    f.reiter.setCurrentIndex(SEITE_LEHRKRAEFTE)
    return f


def waehle(f, *namen):
    t, p = f.lehrkraefte.tabelle, f.lehrkraefte.proxy
    t.clearSelection()
    for i in range(p.rowCount()):
        if p.index(i, 0).data() in namen:
            t.selectionModel().select(p.index(i, 0), AUSWAHL)


def zeile(f, name):
    p = f.lehrkraefte.proxy
    return next(
        [p.index(i, c).data() for c in range(5)] for i in range(p.rowCount()) if p.index(i, 0).data() == name
    )


def dialog_mit(aktion):
    """Ersetzt das Ausführen eines Dialogs: `aktion(dialog)` bedient ihn, danach wird übernommen."""

    def ausfuehren(d):
        aktion(d)
        return d.uebernehmen()

    return ausfuehren


def waehle_eintrag(liste, text):
    e = liste.findItems(text, Qt.MatchFlag.MatchStartsWith)[0]
    liste.setCurrentItem(e)
    e.setSelected(True)
    return e


def haken(liste, text, an=True):
    liste.findItems(text, Qt.MatchFlag.MatchStartsWith)[0].setCheckState(
        Qt.CheckState.Checked if an else Qt.CheckState.Unchecked
    )


def teilnahmen(f):
    return {(z[3]): set(z[6].split(", ")) for z in f.ergebnis.modelle["Termine"].zeilen()}


def test_tabelle_zeigt_konferenzen_vorsitz_und_status(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path)
    assert f.lehrkraefte.proxy.rowCount() == 6
    assert zeile(f, "Anna Eins")[:3] == ["Anna Eins", "Deutsch › Sport › Kunst", "Deutsch"]
    assert zeile(f, "Dora Vier")[4] == ""
    assert "6 Lehrkräfte, 0 neu zu verplanen" in f.lehrkraefte.zaehler.text()


def test_suche_und_filter(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path)
    f.lehrkraefte.suche.setText("anna")
    assert f.lehrkraefte.proxy.rowCount() == 1
    f.lehrkraefte.suche.setText("kunst")  # sucht auch in den Konferenzen
    assert f.lehrkraefte.proxy.rowCount() == 3
    f.lehrkraefte.suche.setText("")
    f.lehrkraefte.filterwahl.setCurrentIndex(1)  # Neu zu verplanen
    assert f.lehrkraefte.proxy.rowCount() == 0
    f.sitzung.setze_konferenzen(["Anna Eins"], ["Sport"])
    f.lehrkraefte.aktualisieren()
    assert f.lehrkraefte.proxy.rowCount() == 1


def test_bearbeiten_konferenzen_und_rangfolge(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path)

    def aktion(d: LehrkraftDialog):
        assert d.konferenzen() == ["Deutsch", "Sport", "Kunst"]
        d.zugeordnet.setCurrentRow(1)
        d.hoch.click()  # Sport vor Deutsch
        d.zugeordnet.setCurrentRow(2)
        d.weg.click()  # Kunst entfernen
        assert d.konferenzen() == ["Sport", "Deutsch"] and d.verfuegbar.count() == 1

    f.lehrkraefte.dialog_ausfuehren = dialog_mit(aktion)
    f.lehrkraefte.bearbeite("Anna Eins")
    assert zeile(f, "Anna Eins")[1] == "Sport › Deutsch"
    assert "geändert" in zeile(f, "Anna Eins")[4] and "neu zu verplanen" in zeile(f, "Anna Eins")[4]
    assert "1 neu zu verplanen" in f.lehrkraefte.zaehler.text()
    assert "Anna Eins geändert" in f.statusBar().currentMessage()


def test_bearbeiten_hinzufuegen_vorsitz_und_termine(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path)

    def aktion(d: LehrkraftDialog):
        waehle_eintrag(d.verfuegbar, "Deutsch")
        d.hinzu.click()
        assert d.konferenzen() == ["Sport", "Deutsch"]
        # die Terminlisten folgen den Konferenzen
        assert [d.fest.item(i).text() for i in range(d.fest.count())] == [
            "Deutsch: Mi 14:00–15:00",
            "Sport: Mi 15:00–16:00",
        ]
        haken(d.vorsitz, "Deutsch")  # übernimmt den Vorsitz von Anna
        haken(d.vorsitz, "Sport", False)
        haken(d.gesperrt, "Sport")
        haken(d.fest, "Deutsch")

    f.lehrkraefte.dialog_ausfuehren = dialog_mit(aktion)
    f.lehrkraefte.bearbeite("Ben Zwei")
    s = f.sitzung
    assert {k.name: k.vorsitz for k in s.konferenzen()} == {
        "Deutsch": "Ben Zwei",
        "Sport": None,
        "Kunst": "Cem Drei",
    }
    a = {x.name: x for x in s.lehrkraefte()}["Ben Zwei"]
    assert (
        a.konferenzen == ("Sport", "Deutsch")
        and a.nicht_verfuegbar == (("Sport", 0),)
        and a.fest == (("Deutsch", 0),)
    )
    assert set(s.markiert) == {"Anna Eins", "Ben Zwei"}  # alter und neuer Vorsitz


def test_dialog_zeigt_vorsitz_anderer_und_vorhandene_termine(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path)
    f.sitzung.setze_nicht_verfuegbar("Anna Eins", {("Kunst", 0)})
    d = LehrkraftDialog(f.sitzung, "Eva Fünf")
    assert d.vorsitz.findItems("Deutsch (jetzt: Anna Eins)", Qt.MatchFlag.MatchExactly)
    d2 = LehrkraftDialog(f.sitzung, "Anna Eins")
    gesperrt = {
        d2.gesperrt.item(i).text(): d2.gesperrt.item(i).checkState() for i in range(d2.gesperrt.count())
    }
    assert gesperrt["Kunst: Mi 14:00–15:00"] == Qt.CheckState.Checked
    assert gesperrt["Deutsch: Mi 14:00–15:00"] == Qt.CheckState.Unchecked


def test_dialog_zeigt_fehler_und_bleibt_offen(qtbot, tmp_path, monkeypatch):
    f = fenster(qtbot, tmp_path)
    d = LehrkraftDialog(f.sitzung, "Anna Eins")

    def kaputt(*_a, **_k):
        raise ModellFehler("Das geht nicht")

    monkeypatch.setattr(f.sitzung, "setze_fest", kaputt)
    assert not d.uebernehmen() and d.fehler.text() == "Das geht nicht"


def test_sammelaenderung_hinzufuegen_an_position(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path)
    waehle(f, "Ben Zwei", "Cem Drei")

    def aktion(d: SammelDialog):
        assert d.aktion.currentData() == "hinzufuegen" and len(d.namen) == 2
        waehle_eintrag(d.konferenzen, "Deutsch")
        d.position.setValue(1)

    f.lehrkraefte.dialog_ausfuehren = dialog_mit(aktion)
    f.lehrkraefte.sammeln()
    assert zeile(f, "Ben Zwei")[1] == "Deutsch › Sport" and zeile(f, "Cem Drei")[1] == "Deutsch › Kunst"
    assert (
        "2 Lehrkräfte geändert" in f.statusBar().currentMessage()
        and "2 neu zu verplanen" in f.lehrkraefte.zaehler.text()
    )


def test_sammelaenderung_entfernen_und_ersetzen(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path)
    waehle(f, "Anna Eins", "Eva Fünf")

    def entfernen(d: SammelDialog):
        d.aktion.setCurrentIndex(1)
        waehle_eintrag(d.konferenzen, "Sport")

    f.lehrkraefte.dialog_ausfuehren = dialog_mit(entfernen)
    f.lehrkraefte.sammeln()
    assert zeile(f, "Anna Eins")[1] == "Deutsch › Kunst" and zeile(f, "Eva Fünf")[1] == "Deutsch"
    waehle(f, "Anna Eins", "Eva Fünf")

    def ersetzen(d: SammelDialog):
        d.aktion.setCurrentIndex(2)
        waehle_eintrag(d.konferenzen, "Kunst")

    f.lehrkraefte.dialog_ausfuehren = dialog_mit(ersetzen)
    f.lehrkraefte.sammeln()
    assert zeile(f, "Anna Eins")[1] == "Kunst" and zeile(f, "Eva Fünf")[1] == "Kunst"


def test_sammelaenderung_ohne_auswahl_ist_ein_fehler(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path)
    d = SammelDialog(f.sitzung, ["Anna Eins"])
    assert not d.uebernehmen() and "mindestens eine Konferenz" in d.fehler.text()


def test_zuruecksetzen(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path)
    f.sitzung.setze_konferenzen(["Anna Eins", "Ben Zwei"], ["Kunst"])
    f.lehrkraefte.aktualisieren()
    waehle(f, "Anna Eins")
    qtbot.mouseClick(f.lehrkraefte.zuruecksetzen, Qt.MouseButton.LeftButton)
    assert zeile(f, "Anna Eins")[1] == "Deutsch › Sport › Kunst" and zeile(f, "Ben Zwei")[1] == "Kunst"
    assert f.sitzung.markiert == ["Ben Zwei"]


def test_knoepfe_je_nach_auswahl(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path)
    s = f.lehrkraefte
    waehle(f)
    assert (
        not s.bearbeiten.isEnabled()
        and not s.sammel.isEnabled()
        and not s.teil.isEnabled()
        and s.alles.isEnabled()
    )
    waehle(f, "Anna Eins")
    assert s.bearbeiten.isEnabled() and s.sammel.isEnabled() and s.zuruecksetzen.isEnabled()
    waehle(f, "Anna Eins", "Ben Zwei")
    assert not s.bearbeiten.isEnabled() and s.sammel.isEnabled()
    f.sitzung.setze_konferenzen(["Anna Eins"], ["Sport"])
    s.aktualisieren()
    assert s.teil.isEnabled()


def test_doppelklick_oeffnet_den_bearbeiten_dialog(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path)
    geoeffnet = []
    f.lehrkraefte.dialog_ausfuehren = lambda d: geoeffnet.append(type(d).__name__) or False
    waehle(f, "Cem Drei")
    f.lehrkraefte.tabelle.doubleClicked.emit(f.lehrkraefte.proxy.index(0, 0))
    assert geoeffnet == ["LehrkraftDialog"]


def test_teilneuplanung_aendert_nur_die_markierte_lehrkraft(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path)
    plane_und_warte(qtbot, f)
    vorher = teilnahmen(f)
    f.reiter.setCurrentIndex(SEITE_LEHRKRAEFTE)
    f.lehrkraefte.dialog_ausfuehren = dialog_mit(
        lambda d: (d.zugeordnet.clear(), d.zugeordnet.addItem("Sport"))
    )
    f.lehrkraefte.bearbeite("Dora Vier")
    assert "Dora Vier" in vorher["Deutsch"] and f.sitzung.markiert == ["Dora Vier"]
    with qtbot.waitSignal(f.planen.plan_fertig, timeout=60000):
        qtbot.mouseClick(f.lehrkraefte.teil, Qt.MouseButton.LeftButton)
    nachher = teilnahmen(f)
    assert f.reiter.currentIndex() == SEITE_ERGEBNIS and f.sitzung.markiert == []
    unterschiede = {n for k in vorher for n in vorher[k] ^ nachher[k]}
    assert unterschiede == {"Dora Vier"} and "Dora Vier" in nachher["Sport"]
    assert "Teilneuplanung" in f.planen.stand.text() or "Fertig" in f.planen.stand.text()
    assert "0 neu zu verplanen" in f.lehrkraefte.zaehler.text()
    assert "Sport (Mi 15:00–16:00)" in zeile(f, "Dora Vier")[3]


def test_teilneuplanung_die_nicht_aufgeht_laesst_plan_und_markierung(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path)
    plane_und_warte(qtbot, f)
    alt = f.sitzung.plan
    f.sitzung.setze_nicht_verfuegbar("Ben Zwei", {("Sport", 0)})  # Vorsitz kann nicht
    f.lehrkraefte.aktualisieren()
    f.reiter.setCurrentIndex(SEITE_LEHRKRAEFTE)
    with qtbot.waitSignal(f.planen.teil_gescheitert, timeout=60000):
        qtbot.mouseClick(f.lehrkraefte.teil, Qt.MouseButton.LeftButton)
    assert f.sitzung.plan is alt and f.sitzung.markiert == ["Ben Zwei"]
    assert f.reiter.currentIndex() == SEITE_PLANEN
    assert "Teilneuplanung nicht möglich" in f.planen.stand.text() and "Sport" in f.planen.stand.text()
    assert "nicht möglich" in f.statusBar().currentMessage()
    assert "neu zu verplanen" in zeile(f, "Ben Zwei")[4]


def test_alles_neu_planen_loescht_markierungen(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path)
    f.sitzung.setze_konferenzen(["Anna Eins"], ["Sport"])
    f.lehrkraefte.aktualisieren()
    with qtbot.waitSignal(f.planen.plan_fertig, timeout=60000):
        qtbot.mouseClick(f.lehrkraefte.alles, Qt.MouseButton.LeftButton)
    assert f.sitzung.markiert == [] and f.reiter.currentIndex() == SEITE_ERGEBNIS
    assert "1 neu zu verplanen" not in f.lehrkraefte.zaehler.text()


def test_lehrkraefte_seite_ist_waehrend_der_planung_gesperrt(qtbot, tmp_path):
    planer = BlockierenderPlaner()
    f = fenster(qtbot, tmp_path, planer)
    f.reiter.setCurrentIndex(SEITE_PLANEN)
    qtbot.mouseClick(f.planen.planen, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(planer.gestartet.is_set, timeout=5000)
    assert not f.reiter.isTabEnabled(SEITE_LEHRKRAEFTE)
    with qtbot.waitSignal(f.planen.plan_fertig, timeout=5000):
        qtbot.mouseClick(f.planen.abbrechen, Qt.MouseButton.LeftButton)
    assert f.reiter.isTabEnabled(SEITE_LEHRKRAEFTE)


def test_neu_zuordnen_aus_der_auswahl_wird_ueber_die_seite_geloest(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path)
    f.sitzung.waehle("Kunst", False)  # Cem Drei hat nur Kunst
    f.lehrkraefte.aktualisieren()
    assert "neu zuordnen" in zeile(f, "Cem Drei")[4]
    f.lehrkraefte.filterwahl.setCurrentIndex(3)
    assert [f.lehrkraefte.proxy.index(i, 0).data() for i in range(f.lehrkraefte.proxy.rowCount())] == [
        "Cem Drei"
    ]
    f.lehrkraefte.dialog_ausfuehren = dialog_mit(
        lambda d: (d.zugeordnet.clear(), d.zugeordnet.addItem("Sport"))
    )
    f.lehrkraefte.bearbeite("Cem Drei")
    assert f.sitzung.neu_zuordnen == []
    assert f.lehrkraefte.proxy.rowCount() == 0  # nicht mehr in der Liste „Neu zuordnen"
    f.lehrkraefte.filterwahl.setCurrentIndex(0)
    assert zeile(f, "Cem Drei")[1] == "Sport"


def test_lehrkraefte_seite_ist_beschriftet(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path)
    s = f.lehrkraefte
    for knopf in (s.bearbeiten, s.sammel, s.zuruecksetzen, s.teil, s.alles):
        assert knopf.text().strip()
    for w in (s.tabelle, s.suche, s.filterwahl):
        assert w.accessibleName()
    d = LehrkraftDialog(f.sitzung, "Anna Eins")
    for w in (d.zugeordnet, d.verfuegbar, d.vorsitz, d.gesperrt, d.fest):
        assert w.accessibleName()
    assert SammelDialog(f.sitzung, ["Anna Eins"]).konferenzen.accessibleName()
