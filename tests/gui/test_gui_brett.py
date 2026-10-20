"""TST-0026 – Verteilungsbrett: Spalten, Karten, Ziehen, Menü und Rückgängig (CON-0018)."""

from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import QDragEnterEvent, QDragLeaveEvent, QDropEvent
from PySide6.QtWidgets import QApplication

from konfiplaner.anwendung import MANUELL, Sitzung
from konfiplaner.gui.brett import MIME, Brett, SpaltenListe
from konfiplaner.gui.hauptfenster import SEITE_ERGEBNIS, SEITE_LEHRKRAEFTE, Hauptfenster
from tests.gui.test_gui_ablaeufe import FakeDialoge, plane_und_warte
from tests.xlsx_helfer import lehrerliste, schreibe

ZEILEN = [
    ["Eins", "Anna", "", "Deutsch", "Sport", None, "Deutsch"],
    ["Zwei", "Ben", "", "Sport", "Kunst", None, "Sport"],
    ["Drei", "Cem", "", "Kunst", "Deutsch", None, "Kunst"],
    ["Vier", "Dora", "", "Deutsch", "Sport", None, None],
    ["Fünf", "Eva", "", "Sport", "Kunst", None, None],
    ["Sechs", "Finn", "", "Kunst", "Deutsch", None, None],
    ["Sieben", "Gil", "", "Sport", None, None, None],
    ["Acht", "Hanna", "", None, None, None, None],
]


def fenster(qtbot, tmp_path, planen=True):
    d = FakeDialoge()
    blaetter = lehrerliste(ZEILEN, zeitslots=False)
    blaetter["Zeitslots"] = [["Tag", "Start", "Ende"], ["Sa", "09:00", "09:45"]]
    d.datei = schreibe(tmp_path / "k.xlsx", blaetter)
    f = Hauptfenster(Sitzung(), d, auto_laden=False)
    qtbot.addWidget(f)
    f.show()
    f.datei_oeffnen()
    if planen:
        plane_und_warte(qtbot, f)
    return f


def spalte(f, konferenz):
    return f.ergebnis.brett.feld(konferenz)


def karte(f, konferenz, name):
    liste = spalte(f, konferenz).liste
    return next(
        liste.item(i)
        for i in range(liste.count())
        if liste.item(i).data(Qt.ItemDataRole.UserRole).name == name
    )


def namen(f, konferenz):
    liste = spalte(f, konferenz).liste
    return [liste.item(i).data(Qt.ItemDataRole.UserRole).name for i in range(liste.count())]


def ziehen_nach(f, von, name, nach):
    """Simuliert: Karte `name` aus Spalte `von` auf die Spalte `nach` fallen lassen."""
    quelle, ziel = spalte(f, von).liste, spalte(f, nach).liste
    daten = quelle.mimeData([karte(f, von, name)])
    ereignis = QDropEvent(
        QPointF(5, 5),
        Qt.DropAction.MoveAction,
        daten,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    ziel.dropEvent(ereignis)
    return ereignis


def drag_ereignis(liste, daten, klasse=QDragEnterEvent):
    return klasse(
        QPoint(5, 5),
        Qt.DropAction.MoveAction,
        daten,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )


def beweglich(f, konferenz="Sport"):
    liste = spalte(f, konferenz).liste
    for i in range(liste.count()):
        k = liste.item(i).data(Qt.ItemDataRole.UserRole)
        if not k.vorsitz and k.weitere:
            return k
    raise AssertionError("keine bewegliche Karte")


# ── Aufbau ──────────────────────────────────────────────────────────────────
def test_verteilung_ist_der_erste_reiter_im_ergebnis_und_wird_gezeigt(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path)
    assert f.reiter.currentIndex() == SEITE_ERGEBNIS
    assert f.ergebnis.reiter.tabText(0) == "Verteilung" and f.ergebnis.reiter.currentIndex() == 0
    assert f.ergebnis.reiter.widget(0) is f.ergebnis.brett


def test_eine_spalte_je_konferenz_und_ohne_zuteilung(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path)
    assert [fe.spalte.konferenz for fe in f.ergebnis.brett.felder] == [None, "Deutsch", "Sport", "Kunst"]
    assert namen(f, None) == ["Hanna Acht"]
    assert "Ohne Zuteilung" in f.ergebnis.brett.felder[0].findChildren(type(f.seitentitel))[0].text()


def test_kopf_zeigt_zahlen(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path)
    text = spalte(f, "Sport").zahlen.text()
    assert "Teilnehmende" in text and "mindestens 1" in text and "Ziel 2" in text
    assert not spalte(f, "Sport").warnung.isVisible()


def test_vorsitz_steht_oben_und_ist_gesperrt(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path)
    assert namen(f, "Sport")[0] == "Ben Zwei"
    item = karte(f, "Sport", "Ben Zwei")
    assert (
        not item.flags() & Qt.ItemFlag.ItemIsDragEnabled
        and "Vorsitz" in item.toolTip()
        and "Bearbeiten" in item.toolTip()
    )
    frei = karte(f, "Sport", beweglich(f).name)
    assert frei.flags() & Qt.ItemFlag.ItemIsDragEnabled and "Weitere Konferenzen" in frei.toolTip()


def test_karte_nennt_name_und_weitere_konferenzen(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path)
    k = karte(f, "Kunst", "Cem Drei").data(Qt.ItemDataRole.UserRole)
    assert k.name == "Cem Drei" and k.weitere == ("Deutsch",) and k.vorsitz
    liste = spalte(f, "Sport").liste
    assert liste.mimeTypes() == [MIME]


def test_ohne_plan_zeigt_das_brett_den_naechsten_schritt(qtbot, tmp_path):
    s = Sitzung()
    brett = Brett(s)
    qtbot.addWidget(brett)
    brett.show()
    assert brett.felder == [] and brett.leer.isVisible() and "Zuerst planen" in brett.leer.text()
    assert not brett.rolle.isVisible()


def test_hochkant_scrollt_waagerecht_bei_vielen_spalten(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path)
    f.resize(1024, 600)
    brett = f.ergebnis.brett
    assert brett.rolle.widgetResizable() and brett.felder[0].width() == brett.felder[1].width() == 236


# ── Ziehen und Ablegen ──────────────────────────────────────────────────────
def test_karte_in_eine_andere_konferenz_ziehen(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path)
    k = beweglich(f)
    ziel = k.weitere[0]
    ereignis = ziehen_nach(f, "Sport", k.name, ziel)
    assert ereignis.dropAction() == Qt.DropAction.IgnoreAction  # Qt hängt nichts selbst um
    assert k.name in namen(f, ziel) and k.name not in namen(f, "Sport")
    termine = {z[3]: z[6] for z in f.ergebnis.modelle["Termine"].zeilen()}
    assert (
        k.name in termine[ziel] and k.name not in termine["Sport"]
    )  # alle Tabellen zeigen die neue Verteilung
    assert f"{k.name}: Sport → {ziel}" in f.statusBar().currentMessage()


def test_nach_dem_ziehen_stimmen_status_und_andere_ansichten(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path)
    k = beweglich(f)
    ziehen_nach(f, "Sport", k.name, k.weitere[0])
    assert "von Hand angepasst" in f.ergebnis.status.text()
    assert MANUELL in f.sitzung.plan.warnungen
    f.reiter.setCurrentIndex(SEITE_LEHRKRAEFTE)
    p = f.lehrkraefte.proxy
    zeile = next(i for i in range(p.rowCount()) if p.index(i, 0).data() == k.name)
    assert k.weitere[0] in p.index(zeile, 4).data()  # „Teilnahme im Plan“
    assert f.leiste.schritte[5].status.endswith("") and f.leiste.schritte[5].zustand in (
        "fertig",
        "offen",
        "aktuell",
    )


def test_ablegen_in_die_gleiche_spalte_aendert_nichts(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path)
    k = beweglich(f)
    plan = f.sitzung.plan
    ereignis = ziehen_nach(f, "Sport", k.name, "Sport")
    assert not ereignis.isAccepted() and f.sitzung.plan is plan


def test_ablegen_ausserhalb_des_sets_ist_eine_ausnahme(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path)
    ziehen_nach(f, "Sport", "Gil Sieben", "Kunst")  # Gil hat nur Sport im Set
    assert "Gil Sieben" in namen(f, "Kunst")
    assert "Ausnahme" in f.statusBar().currentMessage() and "ergänzt" in f.statusBar().currentMessage()
    assert f.sitzung.konferenzen_von("Gil Sieben") == ("Sport", "Kunst")


def test_aus_ohne_zuteilung_in_eine_konferenz(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path)
    ziehen_nach(f, None, "Hanna Acht", "Deutsch")
    assert namen(f, None) == [] and "Hanna Acht" in namen(f, "Deutsch")


def test_in_ohne_zuteilung_kann_nicht_abgelegt_werden(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path)
    k = beweglich(f)
    ereignis = ziehen_nach(f, "Sport", k.name, None)
    assert not ereignis.isAccepted() and k.name in namen(f, "Sport")


def test_vorsitz_kann_nicht_verschoben_werden_und_meldung_nennt_den_weg(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path)
    ziehen_nach(f, "Sport", "Ben Zwei", "Kunst")  # auch wenn jemand es erzwingt
    assert "Ben Zwei" in namen(f, "Sport")
    assert "Vorsitz" in f.statusBar().currentMessage() and "Bearbeiten" in f.statusBar().currentMessage()


# ── Rückmeldung beim Ziehen ─────────────────────────────────────────────────
def test_zielspalte_zeigt_set_oder_ausnahme(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path)
    k = beweglich(f)
    im_set, ausserhalb = (
        spalte(f, k.weitere[0]),
        spalte(f, next(n for n in ("Deutsch", "Sport", "Kunst") if n != "Sport" and n not in k.weitere)),
    )
    daten = spalte(f, "Sport").liste.mimeData([karte(f, "Sport", k.name)])
    im_set.liste.dragEnterEvent(drag_ereignis(im_set.liste, daten))
    assert im_set.property("ziel") == "imset" and not im_set.ausnahme.isVisible()
    im_set.liste.dragLeaveEvent(QDragLeaveEvent())
    assert im_set.property("ziel") == ""
    ausserhalb.liste.dragEnterEvent(drag_ereignis(ausserhalb.liste, daten))
    assert ausserhalb.property("ziel") == "ausnahme" and ausserhalb.ausnahme.isVisible()
    assert "Ausnahme" in ausserhalb.ausnahme.text()
    ausserhalb.liste.dragLeaveEvent(QDragLeaveEvent())
    assert ausserhalb.property("ziel") == "" and not ausserhalb.ausnahme.isVisible()


def test_eigene_spalte_nimmt_keine_karte_an(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path)
    k = beweglich(f)
    daten = spalte(f, "Sport").liste.mimeData([karte(f, "Sport", k.name)])
    ereignis = drag_ereignis(spalte(f, "Sport").liste, daten)
    spalte(f, "Sport").liste.dragEnterEvent(ereignis)
    assert not ereignis.isAccepted() and spalte(f, "Sport").property("ziel") == ""


def test_fremde_daten_werden_ignoriert(qtbot, tmp_path):
    from PySide6.QtCore import QMimeData

    f = fenster(qtbot, tmp_path)
    fremd = QMimeData()
    fremd.setText("irgendein Text")
    ereignis = drag_ereignis(spalte(f, "Sport").liste, fremd)
    spalte(f, "Sport").liste.dragEnterEvent(ereignis)
    assert not ereignis.isAccepted()
    kaputt = QMimeData()
    kaputt.setData(MIME, b"{kein json")
    ereignis = QDropEvent(
        QPointF(1, 1),
        Qt.DropAction.MoveAction,
        kaputt,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    spalte(f, "Sport").liste.dropEvent(ereignis)
    assert not ereignis.isAccepted()


# ── Prüfhinweise ────────────────────────────────────────────────────────────
def test_unter_mindestanzahl_ist_im_kopf_und_in_der_pruefung_sichtbar(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path, planen=False)
    f.sitzung.setze_thema(
        next(i for i, t in enumerate(f.sitzung.themen) if t.name == "Kunst"), mindestanzahl=3
    )
    plane_und_warte(qtbot, f)
    k = beweglich(f, "Kunst")
    ziehen_nach(f, "Kunst", k.name, k.weitere[0])
    brett = f.ergebnis.brett
    assert (
        spalte(f, "Kunst").warnung.isVisible() and spalte(f, "Kunst").warnung.text() == "unter Mindestanzahl"
    )
    assert brett.pruefung.isVisible() and "mindestens 3" in brett.pruefung.text()
    export = [r[1] for r in f.ergebnis.modelle["Hinweise"].zeilen() if r[0] == "Warnung"]
    assert any("mindestens 3" in text for text in export)


# ── Tastatur ────────────────────────────────────────────────────────────────
def test_menue_verschiebt_und_kennzeichnet_ausnahmen(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path)
    k = beweglich(f)
    gesehen = []

    def waehle_erste(menue):
        gesehen.extend(a.text() for a in menue.actions())
        return next(a for a in menue.actions() if "Ausnahme" not in a.text())

    f.ergebnis.brett.menue_ausfuehren = waehle_erste
    f.ergebnis.brett.menue(karte(f, "Sport", k.name), "Sport")
    assert len(gesehen) == 2 and any("(Ausnahme)" in t for t in gesehen) or len(gesehen) == 2
    assert k.weitere[0] in gesehen and "Sport" not in gesehen
    assert k.name in namen(f, k.weitere[0])


def test_menue_per_enter_auf_der_karte(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path)
    k = beweglich(f)
    liste = spalte(f, "Sport").liste
    aufgerufen = []
    f.ergebnis.brett.menue_ausfuehren = lambda m: aufgerufen.append(len(m.actions())) or None
    liste.itemActivated.emit(karte(f, "Sport", k.name))
    assert aufgerufen == [2] and k.name in namen(f, "Sport")  # Menü abgebrochen: nichts geschieht


def test_menue_beim_vorsitz_erklaert_den_weg(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path)
    f.ergebnis.brett.menue(karte(f, "Sport", "Ben Zwei"), "Sport")
    assert "Bearbeiten" in f.statusBar().currentMessage()


# ── Rückgängig ──────────────────────────────────────────────────────────────
def test_rueckgaengig_per_schaltflaeche(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path)
    brett = f.ergebnis.brett
    assert not brett.rueckgaengig.isEnabled()
    k = beweglich(f)
    ziehen_nach(f, "Sport", k.name, k.weitere[0])
    assert brett.rueckgaengig.isEnabled()
    qtbot.mouseClick(brett.rueckgaengig, Qt.MouseButton.LeftButton)
    assert k.name in namen(f, "Sport") and not brett.rueckgaengig.isEnabled()
    assert MANUELL not in f.sitzung.plan.warnungen
    assert "rückgängig" in f.statusBar().currentMessage()
    assert "optimal" in f.ergebnis.status.text().lower()


def test_rueckgaengig_mehrfach_und_ohne_nichts_zu_tun(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path)
    brett = f.ergebnis.brett
    k = beweglich(f)
    ziehen_nach(f, "Sport", k.name, k.weitere[0])
    ziehen_nach(f, "Sport", "Gil Sieben", "Kunst")
    assert brett.mache_rueckgaengig() and brett.mache_rueckgaengig()
    assert not brett.mache_rueckgaengig() and "Nichts" in f.statusBar().currentMessage()


def test_strg_z_macht_rueckgaengig(qtbot, tmp_path):
    from PySide6.QtGui import QShortcut

    f = fenster(qtbot, tmp_path)
    k = beweglich(f)
    ziehen_nach(f, "Sport", k.name, k.weitere[0])
    kuerzel = [x for x in f.ergebnis.brett.findChildren(QShortcut) if x.key().toString() == "Ctrl+Z"]
    assert kuerzel
    kuerzel[0].activated.emit()
    assert k.name in namen(f, "Sport")


# ── Zuweisung und Neuplanung ────────────────────────────────────────────────
def test_verschiebung_bleibt_bei_alles_neu_planen(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path)
    k = beweglich(f)
    ziel = k.weitere[0]
    ziehen_nach(f, "Sport", k.name, ziel)
    f.sitzung.planen()
    f.ergebnis.aktualisieren()
    assert k.name in namen(f, ziel)


def test_zuruecksetzen_loest_die_zuweisung_und_markiert(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path)
    k = beweglich(f)
    ziehen_nach(f, "Sport", k.name, k.weitere[0])
    f.sitzung.zuruecksetzen(k.name)
    assert f.sitzung.markiert == [k.name] and not f.sitzung.zuordnung.personen.get(k.name)


def test_beschriftung_und_zugaenglichkeit(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path)
    brett = f.ergebnis.brett
    assert brett.rueckgaengig.text().strip() and brett.rolle.accessibleName()
    assert all(
        isinstance(fe.liste, SpaltenListe) and fe.liste.accessibleName().startswith("Spalte")
        for fe in brett.felder
    )
    assert QApplication.instance() is not None
