"""TST-0023 – Design-Tokens, Kontrast, Fachfarben, Stilregeln und Schrift (CON-0016)."""

import re

import pytest
from PySide6.QtCore import QtMsgType, qInstallMessageHandler
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QCheckBox, QComboBox, QLineEdit, QPushButton, QTableView, QTabWidget

from konfiplaner.gui import design
from konfiplaner.gui.design import (
    DUNKEL,
    FACHFARBEN_REIHEN,
    FACHFARBEN_TON,
    fachfarbe,
    fachpunkt,
    installiere,
    kontrast,
    lade_schrift,
    palette,
    punkt,
    qss,
    registriere_fachfarben,
)

FLAECHEN = ("tafel", "eingabe", "flaeche", "zebra", "erhoeht")


# ── Tokens ──────────────────────────────────────────────────────────────────
def test_alle_farben_sind_gueltige_hexwerte():
    for name, wert in vars(DUNKEL).items():
        if isinstance(wert, str):
            assert re.fullmatch(r"#[0-9A-Fa-f]{6}", wert), name


def test_groessenskala_ist_absteigend():
    assert DUNKEL.gross > DUNKEL.mittel > DUNKEL.normal > DUNKEL.klein >= 11
    assert DUNKEL.radius > DUNKEL.radius_klein > 0


def test_kontrastfunktion():
    assert kontrast("#000000", "#FFFFFF") == pytest.approx(21.0, rel=1e-3)
    assert kontrast("#777777", "#777777") == pytest.approx(1.0)
    assert kontrast("#111111", "#EEEEEE") == kontrast("#EEEEEE", "#111111")


# ── Kontrast (WCAG AA) ──────────────────────────────────────────────────────
@pytest.mark.parametrize("flaeche", FLAECHEN)
def test_text_und_gedaempfter_text_erreichen_aa_auf_allen_flaechen(flaeche):
    grund = getattr(DUNKEL, flaeche)
    assert kontrast(DUNKEL.kreide, grund) >= 4.5
    assert kontrast(DUNKEL.gedaempft, grund) >= 4.5


@pytest.mark.parametrize("status", ["konflikt", "fehler", "ok", "hinweis", "akzent"])
@pytest.mark.parametrize("flaeche", ["tafel", "flaeche", "zebra"])
def test_statusfarben_und_akzent_sind_als_text_lesbar(status, flaeche):
    assert kontrast(getattr(DUNKEL, status), getattr(DUNKEL, flaeche)) >= 4.5


def test_hauptaktion_ist_lesbar_auch_beim_ueberfahren():
    assert kontrast(DUNKEL.auf_akzent, DUNKEL.akzent) >= 4.5
    assert kontrast(DUNKEL.auf_akzent, DUNKEL.akzent_hover) >= 4.5


def test_text_auf_der_auswahl_ist_lesbar():
    assert kontrast(DUNKEL.kreide, "#4A4026") >= 4.5 and kontrast(DUNKEL.kreide, "#55482A") >= 4.5


def test_fokusring_hebt_sich_von_den_flaechen_ab():
    for flaeche in FLAECHEN:
        assert kontrast(DUNKEL.akzent, getattr(DUNKEL, flaeche)) >= 3.0


# ── Fachfarben ──────────────────────────────────────────────────────────────
def test_fachfarben_erreichen_3_zu_1_auf_den_flaechen(qapp):
    registriere_fachfarben([f"K{i}" for i in range(36)])
    for i in range(36):
        for flaeche in ("flaeche", "zebra", "tafel"):
            assert kontrast(fachfarbe(f"K{i}"), getattr(DUNKEL, flaeche)) >= 3.0, (i, flaeche)


def test_sechsunddreissig_unterscheidbare_fachfarben(qapp):
    registriere_fachfarben([f"K{i}" for i in range(36)])
    assert len({fachfarbe(f"K{i}").name() for i in range(36)}) == 36
    assert len(FACHFARBEN_TON) * len(FACHFARBEN_REIHEN) == 36


def test_26_konferenzen_bekommen_26_verschiedene_farben(qapp):
    registriere_fachfarben([f"Konferenz {i}" for i in range(26)])
    assert len({fachfarbe(f"Konferenz {i}").name() for i in range(26)}) == 26


def test_fachfarben_meiden_das_kreidegelb_des_akzents(qapp):
    registriere_fachfarben([f"K{i}" for i in range(36)])
    akzent = QColor(DUNKEL.akzent).hue()
    for i in range(36):
        assert abs((fachfarbe(f"K{i}").hue() - akzent + 180) % 360 - 180) >= 20


def test_fachfarbe_ist_stabil_und_unabhaengig_von_der_reihenfolge(qapp):
    registriere_fachfarben(["Sport", "Deutsch", "Kunst"])
    a = {n: fachfarbe(n).name() for n in ("Sport", "Deutsch", "Kunst")}
    registriere_fachfarben(["Kunst", "Sport", "Deutsch"])
    assert {n: fachfarbe(n).name() for n in a} == a


def test_unbekannte_namen_haben_eine_stabile_farbe_ohne_beachtung_der_schreibweise(qapp):
    registriere_fachfarben([])
    assert fachfarbe("Latein").name() == fachfarbe("latein").name() == fachfarbe("LATEIN").name()


def test_punkt_symbole(qapp):
    assert not punkt("#ff0000").isNull() and not fachpunkt("Deutsch").isNull()
    img = punkt("#ff0000", 10).pixmap(20, 20).toImage()
    assert img.pixelColor(10, 10).name() == "#ff0000" and img.pixelColor(0, 0).alpha() == 0


# ── Palette und Stilregeln ──────────────────────────────────────────────────
def test_palette_ist_dunkel_mit_hellem_text(qapp):
    p = palette()
    assert design.luminanz(p.color(QPalette.ColorRole.Window)) < 0.03
    assert design.luminanz(p.color(QPalette.ColorRole.WindowText)) > 0.7
    assert kontrast(p.color(QPalette.ColorRole.Text), p.color(QPalette.ColorRole.Base)) >= 4.5
    assert p.color(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text) != p.color(QPalette.ColorRole.Text)


def test_stilregeln_enthalten_fokus_hauptaktion_und_keine_grossbuchstaben():
    text = qss(DUNKEL, "Test")
    assert "QPushButton:focus" in text and DUNKEL.akzent in text
    assert 'QPushButton[primaer="true"]' in text
    assert "uppercase" not in text  # Beschriftungen in normaler Schreibweise


def test_stilregeln_werden_ohne_fehler_gelesen(qapp):
    meldungen: list[str] = []

    def sammle(art, _kontext, text):
        if art in (QtMsgType.QtWarningMsg, QtMsgType.QtCriticalMsg):
            meldungen.append(text)

    vorher = qInstallMessageHandler(sammle)
    try:
        installiere(qapp)
        for w in (QPushButton("x"), QLineEdit(), QComboBox(), QTableView(), QTabWidget(), QCheckBox("a")):
            w.ensurePolished()
            w.show()
            w.hide()
    finally:
        qInstallMessageHandler(vorher)
    assert not [m for m in meldungen if "stylesheet" in m.lower() or "parse" in m.lower()], meldungen


def test_installation_setzt_fusion_schrift_und_palette(qapp, monkeypatch):
    gesetzt: list[str] = []
    original = qapp.setStyle
    monkeypatch.setattr(qapp, "setStyle", lambda name: (gesetzt.append(name), original(name))[1])
    familie = installiere(qapp)
    assert gesetzt == ["Fusion"] and DUNKEL.tafel in qapp.styleSheet()
    assert qapp.font().family() == familie == design.SCHRIFTFAMILIE
    assert qapp.font().pixelSize() == DUNKEL.normal
    assert qapp.palette().color(QPalette.ColorRole.Window).name().lower() == DUNKEL.tafel.lower()


def test_haken_symbole_werden_erzeugt(qapp):
    sym = design._haken_symbole(DUNKEL)
    assert set(sym) == {"aus", "an"}
    from pathlib import Path

    assert all(Path(p).exists() for p in sym.values())
    assert "image: url(" in qss(DUNKEL, "Test", sym)


# ── Schrift ─────────────────────────────────────────────────────────────────
def test_schrift_ist_gebuendelt_mit_lizenz():
    ordner = design.SCHRIFT_ORDNER
    assert (ordner / "OFL.txt").read_text(encoding="utf-8").count("SIL Open Font License") >= 1
    assert {p.name for p in ordner.glob("*.ttf")} >= {
        f"AtkinsonHyperlegibleNext-{w}.ttf" for w in ("Regular", "Medium", "SemiBold", "Bold")
    }


def test_schrift_laedt(qapp):
    assert lade_schrift() == design.SCHRIFTFAMILIE


def test_fehlende_schrift_faellt_auf_die_systemschrift_zurueck(qapp, monkeypatch, tmp_path):
    monkeypatch.setattr(design, "SCHRIFT_ORDNER", tmp_path)
    monkeypatch.setattr(design, "SCHRIFTFAMILIE", "Gibt Es Nicht")
    assert lade_schrift() == qapp.font().family()
