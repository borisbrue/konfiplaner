"""TST-0024 – Verteilung in der GUI: Profilwahl, Tipp und planbare Lehrerliste (CON-0017)."""

from konfiplaner.anwendung import PROFIL_NAMEN, Sitzung
from konfiplaner.gui.hauptfenster import SEITE_ERGEBNIS, SEITE_PLANEN, SEITE_REGELN, Hauptfenster
from tests.gui.test_gui_ablaeufe import FakeDialoge, plane_und_warte
from tests.xlsx_helfer import lehrer_mit_terminen, schreibe

ZEILEN = [
    ["Eins", "Anna", "", "Deutsch", "Sport", None, "Deutsch"],
    ["Zwei", "Ben", "", "Sport", "Deutsch", None, "Sport"],
    ["Drei", "Cem", "", "Deutsch", "Sport", None, None],
    ["Vier", "Dora", "", "Sport", "Deutsch", None, None],
]


def fenster(qtbot, tmp_path):
    d = FakeDialoge()
    blaetter = lehrer_mit_terminen(
        ZEILEN, ("Deutsch", "Sa", "09:00", "09:45"), ("Sport", "Sa", "09:00", "09:45")
    )
    del blaetter["Konferenzen"]  # wie in der Praxis: Zeitraster mit einem Slot, keine Konferenztermine
    blaetter["Zeitslots"] = [["Tag", "Start", "Ende"], ["Sa", "09:00", "09:45"]]
    d.datei = schreibe(tmp_path / "k.xlsx", blaetter)
    f = Hauptfenster(Sitzung(), d, auto_laden=False)
    qtbot.addWidget(f)
    f.show()
    f.datei_oeffnen()
    return f


def test_lehrerliste_ist_ohne_regelaenderung_planbar(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path)
    assert f.sitzung.planbar and f.sitzung.wirksames_profil() == "verteilen"
    plane_und_warte(qtbot, f)
    assert f.reiter.currentIndex() == SEITE_ERGEBNIS and f.sitzung.plan.status in ("optimal", "machbar")
    assert "Plan ist optimal" in f.ergebnis.status.text()
    assert sorted(len(z[6].split(", ")) for z in f.ergebnis.modelle["Termine"].zeilen()) == [2, 2]


def test_profilauswahl_in_den_regeln(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path)
    f.reiter.setCurrentIndex(SEITE_REGELN)
    box = f.regeln.profil
    assert [box.itemData(i) for i in range(box.count())] == list(PROFIL_NAMEN) and box.currentData() == "auto"
    box.setCurrentIndex(box.findData("klassisch"))
    assert f.sitzung.profil == "klassisch"
    assert f.regeln.typ_auswahl("schwerpunkte").currentData() == "hart"
    assert f.regeln.typ_auswahl("verteilung").currentData() == "aus"
    assert "Profil" in f.statusBar().currentMessage()
    box.setCurrentIndex(box.findData("auto"))
    assert f.regeln.typ_auswahl("schwerpunkte").currentData() == "aus"


def test_profilwechsel_aktualisiert_die_seitenleiste_und_verwirft_den_plan(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path)
    plane_und_warte(qtbot, f)
    assert f.reiter.isTabEnabled(SEITE_ERGEBNIS)
    f.reiter.setCurrentIndex(SEITE_REGELN)
    f.regeln.profil.setCurrentIndex(f.regeln.profil.findData("klassisch"))
    assert not f.reiter.isTabEnabled(SEITE_ERGEBNIS)
    assert f.leiste.schritte[3].status == "6 hart, 1 weich"  # klassisch: schwerpunkte hart, Verteilung aus


def test_tipp_erscheint_bei_klassischem_profil_im_ergebnis_und_auf_der_planen_seite(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path)
    f.sitzung.setze_profil("klassisch")
    f.regeln.aktualisieren()
    plane_und_warte(qtbot, f)
    assert f.sitzung.plan.status == "kein_plan"
    assert "Kein Plan möglich" in f.ergebnis.status.text() and "Tipp" in f.ergebnis.status.text()
    assert "Verteilen" in f.ergebnis.status.text()
    assert "Tipp" in f.planen.stand.text()


def test_kein_tipp_bei_gueltigem_plan(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path)
    plane_und_warte(qtbot, f)
    assert "Tipp" not in f.ergebnis.status.text() and "Tipp" not in f.planen.stand.text()


def test_regelseite_zeigt_die_neuen_regeln_mit_beschreibung(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path)
    for name, typ in (
        ("verteilung", "hart"),
        ("rangfolge", "weich"),
        ("ausgleich", "weich"),
        ("schwerpunkte", "aus"),
    ):
        assert f.regeln.typ_auswahl(name).currentData() == typ
    assert f.regeln.typ_auswahl("rangfolge").count() == 2  # nur weich oder aus
    assert f.regeln.typ_auswahl("verteilung").count() == 3


def test_planen_seite_nennt_den_umfang_im_profil(qtbot, tmp_path):
    f = fenster(qtbot, tmp_path)
    f.reiter.setCurrentIndex(SEITE_PLANEN)
    assert "2 Konferenzen" in f.planen.umfang.text() and "4 Lehrkräfte" in f.planen.umfang.text()
