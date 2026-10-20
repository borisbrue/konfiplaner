"""TST-0030 – Hinweiskarte, „Später“ und manuelle Prüfung ohne Netz (CON-0020)."""

import time
from datetime import datetime, timedelta

from konfiplaner.anwendung import Sitzung
from konfiplaner.einstellungen import YamlEinstellungen
from konfiplaner.gui.hauptfenster import Hauptfenster
from konfiplaner.update import UpdateFehler, eigene_version
from tests.gui.test_gui_ablaeufe import FakeDialoge

URL = "https://example.invalid/releases/v9.9.9"


class Quelle:
    def __init__(self, tag=None, fehler=None):
        self.tag, self.fehler, self.abfragen = tag, fehler, 0

    def neueste(self):
        self.abfragen += 1
        if self.fehler:
            raise self.fehler
        return (
            {"tag_name": self.tag, "html_url": URL.replace("9.9.9", self.tag.lstrip("v"))}
            if self.tag
            else None
        )


def fenster(qtbot, tmp_path, quelle, auto=True, vorher=None):
    pfad = tmp_path / "e.yaml"
    sitzung = Sitzung(YamlEinstellungen(pfad))
    if vorher:
        vorher(sitzung)
    d = FakeDialoge()
    f = Hauptfenster(sitzung, d, auto_laden=False, update_quelle=quelle, auto_update=auto)
    qtbot.addWidget(f)
    f.show()
    return f, d, pfad


def fertig(qtbot, f):
    qtbot.waitUntil(lambda: f._update_lauf is None, timeout=3000)


def test_version_steht_unten_in_der_seitenleiste(qtbot, tmp_path):
    f, _, _ = fenster(qtbot, tmp_path, Quelle(), auto=False)
    assert f.leiste.version.text() == f"Version {eigene_version()}"


def test_neuere_version_zeigt_karte_mit_ansehen_und_spaeter(qtbot, tmp_path):
    f, _, _ = fenster(qtbot, tmp_path, Quelle("v9.9.9"))
    fertig(qtbot, f)
    assert f.leiste.update_karte.isVisible() and f.leiste.update_text.text() == "Version 9.9.9 verfügbar"
    assert f.leiste.ansehen.text() == "Ansehen" and f.leiste.spaeter.text() == "Später"


def test_ohne_neuere_version_keine_karte(qtbot, tmp_path):
    f, _, _ = fenster(qtbot, tmp_path, Quelle("v0.0.1"))
    fertig(qtbot, f)
    assert not f.leiste.update_karte.isVisible()


def test_verbindungsfehler_beim_start_bleibt_still(qtbot, tmp_path):
    f, d, _ = fenster(qtbot, tmp_path, Quelle(fehler=UpdateFehler("weg")))
    fertig(qtbot, f)
    assert not f.leiste.update_karte.isVisible() and not d.fehler_meldungen
    assert "Keine Verbindung" not in f.statusBar().currentMessage()
    assert f.reiter.isEnabled()


def test_spaeter_blendet_nur_diese_version_aus(qtbot, tmp_path):
    f, _, _ = fenster(qtbot, tmp_path, Quelle("v9.9.9"))
    fertig(qtbot, f)
    f.leiste.spaeter.click()
    assert not f.leiste.update_karte.isVisible()
    # nächster Start (nach mehr als 24 Stunden): gleiche Version bleibt aus, neuere erscheint
    spaeter = datetime.now() + timedelta(days=2)
    g, _, _ = fenster(qtbot, tmp_path, Quelle("v9.9.9"), auto=False)
    g._jetzt = lambda: spaeter
    g.suche_update(manuell=False)
    fertig(qtbot, g)
    assert not g.leiste.update_karte.isVisible()
    h, _, _ = fenster(qtbot, tmp_path, Quelle("v9.9.10"), auto=False)
    h.suche_update(manuell=False)
    fertig(qtbot, h)
    assert h.leiste.update_text.text() == "Version 9.9.10 verfügbar"


def test_ansehen_oeffnet_die_release_seite(qtbot, tmp_path):
    f, d, _ = fenster(qtbot, tmp_path, Quelle("v9.9.9"))
    fertig(qtbot, f)
    f.leiste.ansehen.click()
    assert d.urls == [URL]


def test_manuelle_pruefung_meldet_aktuell_und_fehler(qtbot, tmp_path):
    f, _, _ = fenster(qtbot, tmp_path, Quelle("v0.0.1"), auto=False)
    f.aktion_update.trigger()
    fertig(qtbot, f)
    assert "aktuell" in f.statusBar().currentMessage()
    f.update_quelle = Quelle(fehler=UpdateFehler("weg"))
    f.aktion_update.trigger()
    fertig(qtbot, f)
    assert "Keine Verbindung" in f.statusBar().currentMessage()


def test_manuelle_pruefung_zeigt_ausgeblendete_version_wieder(qtbot, tmp_path):
    f, _, _ = fenster(
        qtbot, tmp_path, Quelle("v9.9.9"), vorher=lambda s: s.blende_update_aus("9.9.9"), auto=False
    )
    f.aktion_update.trigger()
    fertig(qtbot, f)
    assert f.leiste.update_karte.isVisible() and "9.9.9" in f.statusBar().currentMessage()


def test_pruefung_hoechstens_einmal_am_tag(qtbot, tmp_path):
    q = Quelle("v0.0.1")
    f, _, _ = fenster(qtbot, tmp_path, q)
    fertig(qtbot, f)
    assert q.abfragen == 1
    q2 = Quelle("v0.0.1")
    g, _, _ = fenster(qtbot, tmp_path, q2)
    assert q2.abfragen == 0 and g._update_lauf is None  # weniger als 24 Stunden her


def test_abschalten_gilt_nur_fuer_den_start_manuell_geht_weiter(qtbot, tmp_path):
    q = Quelle("v9.9.9")
    f, _, _ = fenster(qtbot, tmp_path, q, vorher=lambda s: setattr(s, "update_pruefung", False))
    assert q.abfragen == 0
    f.aktion_update.trigger()
    fertig(qtbot, f)
    assert q.abfragen == 1 and f.leiste.update_karte.isVisible()


def test_schliessen_waehrend_der_abfrage_stuerzt_nicht_ab(qtbot, tmp_path):
    class Langsam(Quelle):
        def neueste(self):
            time.sleep(0.3)
            return super().neueste()

    f, _, _ = fenster(qtbot, tmp_path, Langsam("v9.9.9"))
    lauf = f._update_lauf
    assert lauf is not None  # die Abfrage läuft noch
    f.close()
    assert lauf.thread.isFinished() and not f.leiste.update_karte.isVisible()


def test_fenster_bleibt_mit_karte_ab_1024_mal_600_bedienbar(qtbot, tmp_path):
    f, _, _ = fenster(qtbot, tmp_path, Quelle("v9.9.9"))
    fertig(qtbot, f)
    f.resize(1024, 600)
    assert f.minimumSizeHint().height() <= 600 and f.minimumSizeHint().width() <= 1024
