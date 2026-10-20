"""Visuelles Design (SPEC-0011): Design-Tokens, Fachfarben, Stilregeln, Schrift und Palette.

Das Design heißt „Schiefertafel bei Abendlicht": dunkler Schiefer als Grund, Kreide als Text und
Akzent. Die Farbe trägt die Fachkonferenz: jede Konferenz hat ihre Fachfarbe wie auf einem
Stundenplan; alles andere bleibt ruhig und neutral.
"""

from __future__ import annotations

import tempfile
import zlib
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QFontDatabase, QIcon, QPainter, QPalette, QPen, QPixmap
from PySide6.QtWidgets import QApplication

SCHRIFTFAMILIE = "Atkinson Hyperlegible Next"
SCHRIFT_ORDNER = Path(__file__).parent / "ressourcen" / "schrift"


@dataclass(frozen=True)
class Tokens:
    """Alle Farben, Radien und Größen an einer Stelle."""

    # Flächen, von hinten nach vorn
    tafel: str = "#11171C"  # Fensterhintergrund
    eingabe: str = "#0E1318"  # Eingabefelder, etwas tiefer als die Tafel
    flaeche: str = "#182027"  # Tabellen und Listen
    zebra: str = "#1C252D"  # jede zweite Tabellenzeile
    erhoeht: str = "#222C36"  # Schaltflächen, Kopfzeilen
    erhoeht_hover: str = "#2A3541"
    linie: str = "#2C3844"
    linie_stark: str = "#3B4A59"
    # Schrift
    kreide: str = "#E9ECEF"
    gedaempft: str = "#9AA7B3"
    # Akzent: Kreidegelb für Hauptaktion und aktuellen Schritt
    akzent: str = "#F2C44E"
    akzent_hover: str = "#F7D36F"
    auf_akzent: str = "#1D1706"
    # Status (immer mit Text, nie nur Farbe)
    konflikt: str = "#F0825F"
    fehler: str = "#EE7185"
    ok: str = "#62CFA3"
    hinweis: str = "#6DB9F0"
    # Maße
    radius_klein: int = 6
    radius: int = 10
    # Schriftgrößen in Pixeln (Skala)
    gross: int = 24
    mittel: int = 15
    normal: int = 14
    klein: int = 12


DUNKEL = Tokens()

# Zwölf Farbtöne ohne das Gelb des Akzents. Die Reihenfolge ist absichtlich gemischt:
# aufeinanderfolgende Konferenzen (nach Namen sortiert) bekommen weit auseinanderliegende Töne.
FACHFARBEN_TON = (205, 18, 130, 295, 80, 235, 352, 160, 265, 105, 325, 185)
MIN_KONTRAST_FACHFARBE = 3.2  # als grafisches Objekt mindestens 3:1 (WCAG), mit Reserve


# ── Kontrast ────────────────────────────────────────────────────────────────
def _linear(c: float) -> float:
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def luminanz(farbe: str | QColor) -> float:
    c = QColor(farbe)
    return 0.2126 * _linear(c.redF()) + 0.7152 * _linear(c.greenF()) + 0.0722 * _linear(c.blueF())


def kontrast(vordergrund: str | QColor, hintergrund: str | QColor) -> float:
    """WCAG-Kontrastverhältnis (1 bis 21)."""
    a, b = luminanz(vordergrund), luminanz(hintergrund)
    hell, dunkel = max(a, b), min(a, b)
    return (hell + 0.05) / (dunkel + 0.05)


# ── Fachfarben ──────────────────────────────────────────────────────────────
_register: dict[str, QColor] = {}


# (Sättigung, Helligkeit) je Reihe; drei Reihen mal zwölf Töne = 36 unterscheidbare Fachfarben
FACHFARBEN_REIHEN = ((150, 165), (115, 215), (190, 140))


def _fachfarbe_aus_index(i: int) -> QColor:
    ton = FACHFARBEN_TON[i % len(FACHFARBEN_TON)]
    saettigung, helligkeit = FACHFARBEN_REIHEN[(i // len(FACHFARBEN_TON)) % len(FACHFARBEN_REIHEN)]
    farbe = QColor.fromHsl(ton, saettigung, helligkeit)
    # Blau und Violett sind dunkler als andere Töne: so lange aufhellen, bis sie sich abheben
    while kontrast(farbe, DUNKEL.zebra) < MIN_KONTRAST_FACHFARBE and helligkeit < 250:
        helligkeit += 6
        farbe = QColor.fromHsl(ton, saettigung, helligkeit)
    return farbe


def registriere_fachfarben(namen: list[str]) -> None:
    """Weist den Konferenzen einer Datei Farben zu: nach Namen sortiert, daher stabil und ohne Doppelte.

    Eine Auswahl ändert die Farben nicht, nur der Satz aller Konferenzen zählt.
    """
    _register.clear()
    for i, name in enumerate(sorted(dict.fromkeys(namen), key=str.casefold)):
        _register[name] = _fachfarbe_aus_index(i)


def fachfarbe(name: str) -> QColor:
    """Farbe einer Konferenz; unbekannte Namen bekommen eine stabile Farbe aus dem Namen."""
    if name in _register:
        return QColor(_register[name])
    return _fachfarbe_aus_index(zlib.crc32(name.casefold().encode()))


def punkt(farbe_hex: str, durchmesser: int = 10, ring: bool = False) -> QIcon:
    """Kleiner Farbpunkt als Symbol. Bewusst ohne Zwischenspeicher: Pixmaps dürfen die QApplication nicht überleben."""
    px = QPixmap(durchmesser * 2, durchmesser * 2)
    px.fill(Qt.GlobalColor.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(farbe_hex))
    r = QRectF(2, 2, durchmesser * 2 - 4, durchmesser * 2 - 4)
    p.drawEllipse(r)
    p.end()
    return QIcon(px)


def fachpunkt(name: str, durchmesser: int = 10) -> QIcon:
    return punkt(fachfarbe(name).name(), durchmesser)


# ── Schrift ─────────────────────────────────────────────────────────────────
def lade_schrift() -> str:
    """Lädt die gebündelte Schrift; gibt den Familiennamen zurück, sonst den der Systemschrift."""
    geladen = 0
    for ttf in sorted(SCHRIFT_ORDNER.glob("*.ttf")):
        if QFontDatabase.addApplicationFont(str(ttf)) >= 0:
            geladen += 1
    return (
        SCHRIFTFAMILIE
        if geladen and SCHRIFTFAMILIE in QFontDatabase.families()
        else QApplication.font().family()
    )


# ── Palette ─────────────────────────────────────────────────────────────────
def palette(t: Tokens = DUNKEL) -> QPalette:
    p = QPalette()
    rollen = {
        QPalette.ColorRole.Window: t.tafel,
        QPalette.ColorRole.WindowText: t.kreide,
        QPalette.ColorRole.Base: t.flaeche,
        QPalette.ColorRole.AlternateBase: t.zebra,
        QPalette.ColorRole.Text: t.kreide,
        QPalette.ColorRole.Button: t.erhoeht,
        QPalette.ColorRole.ButtonText: t.kreide,
        QPalette.ColorRole.ToolTipBase: t.erhoeht,
        QPalette.ColorRole.ToolTipText: t.kreide,
        QPalette.ColorRole.Highlight: "#55482A",
        QPalette.ColorRole.HighlightedText: t.kreide,
        QPalette.ColorRole.PlaceholderText: t.gedaempft,
        QPalette.ColorRole.Link: t.hinweis,
        QPalette.ColorRole.BrightText: t.fehler,
    }
    for rolle, farbe in rollen.items():
        p.setColor(rolle, QColor(farbe))
    for rolle in (QPalette.ColorRole.Text, QPalette.ColorRole.ButtonText, QPalette.ColorRole.WindowText):
        p.setColor(QPalette.ColorGroup.Disabled, rolle, QColor(t.gedaempft).darker(130))
    return p


# ── Stilregeln ──────────────────────────────────────────────────────────────
def _haken_symbole(t: Tokens) -> dict[str, str]:
    """Zeichnet die Häkchen-Symbole für Kontrollkästchen in einen Temp-Ordner und gibt die Pfade zurück."""
    ordner = Path(tempfile.gettempdir()) / "konfiplaner-design"
    pfade: dict[str, str] = {}
    try:
        ordner.mkdir(exist_ok=True)
        for name, gefuellt, haken in (("aus", False, False), ("an", True, True)):
            px = QPixmap(36, 36)
            px.fill(Qt.GlobalColor.transparent)
            p = QPainter(px)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            rand = QColor(t.akzent if gefuellt else t.linie_stark)
            p.setPen(QPen(rand, 2.5))
            p.setBrush(QColor(t.akzent) if gefuellt else QColor(t.eingabe))
            p.drawRoundedRect(QRectF(3, 3, 30, 30), 8, 8)
            if haken:
                p.setPen(
                    QPen(
                        QColor(t.auf_akzent),
                        4,
                        Qt.PenStyle.SolidLine,
                        Qt.PenCapStyle.RoundCap,
                        Qt.PenJoinStyle.RoundJoin,
                    )
                )
                p.drawPolyline([QPointF(10, 19), QPointF(16, 25), QPointF(26, 12)])
            p.end()
            datei = ordner / f"haken_{name}.png"
            px.save(str(datei))
            pfade[name] = datei.as_posix()
    except OSError:
        return {}
    return pfade


def qss(t: Tokens = DUNKEL, familie: str = SCHRIFTFAMILIE, symbole: dict[str, str] | None = None) -> str:
    sym = symbole or {}
    haken = ""
    if sym:
        haken = f"""
QCheckBox::indicator, QTableView::indicator, QListView::indicator {{
    width: 18px; height: 18px; border: none; background: transparent; image: url({sym["aus"]});
}}
QCheckBox::indicator:checked, QTableView::indicator:checked, QListView::indicator:checked {{
    image: url({sym["an"]});
}}
"""
    return f"""
* {{ font-family: "{familie}"; font-size: {t.normal}px; outline: none; }}
QMainWindow, QDialog, QWidget#seite {{ background: {t.tafel}; color: {t.kreide}; }}
QWidget {{ color: {t.kreide}; }}
QLabel {{ background: transparent; }}
QLabel#hinweis, QLabel[gedaempft="true"] {{ color: {t.gedaempft}; }}
QLabel#seitentitel {{ font-size: {t.gross}px; font-weight: 700; }}
QLabel#seitenhilfe {{ color: {t.gedaempft}; font-size: {t.mittel}px; }}
QLabel#leer {{ color: {t.gedaempft}; font-size: {t.mittel}px; }}
QLabel[zustand="bereit"] {{ color: {t.ok}; font-weight: 600; font-size: {t.mittel}px; }}
QLabel[zustand="blockiert"] {{ color: {t.konflikt}; font-weight: 600; font-size: {t.mittel}px; }}
QLabel#leertitel {{ font-size: {t.gross - 2}px; font-weight: 700; }}
QWidget#ablage {{ border: 2px dashed {t.linie_stark}; border-radius: 16px; background: transparent; }}
QWidget#ablage QLabel {{ border: none; }}

/* Schaltflächen: neutral, die Hauptaktion in Kreidegelb */
QPushButton {{
    background: {t.erhoeht}; color: {t.kreide}; border: 1px solid {t.linie_stark};
    border-radius: {t.radius_klein + 2}px; padding: 7px 16px; min-height: 20px; font-weight: 500;
}}
QPushButton:hover {{ background: {t.erhoeht_hover}; }}
QPushButton:pressed {{ background: {t.linie}; }}
QPushButton:focus {{ border: 2px solid {t.akzent}; padding: 6px 15px; }}
QPushButton:disabled {{ color: {t.gedaempft}; background: {t.zebra}; border-color: {t.linie}; }}
QPushButton[primaer="true"] {{
    background: {t.akzent}; color: {t.auf_akzent}; border: 1px solid {t.akzent}; font-weight: 700;
}}
QPushButton[primaer="true"]:hover {{ background: {t.akzent_hover}; }}
QPushButton[primaer="true"]:focus {{ border: 2px solid {t.kreide}; padding: 6px 15px; }}
QPushButton[primaer="true"]:disabled {{ background: {t.erhoeht}; color: {t.gedaempft}; border-color: {t.linie}; }}

/* Eingaben */
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTimeEdit {{
    background: {t.eingabe}; color: {t.kreide}; border: 1px solid {t.linie_stark};
    border-radius: {t.radius_klein + 2}px; padding: 6px 10px; min-height: 20px;
    selection-background-color: #55482A; selection-color: {t.kreide};
}}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QTimeEdit:focus {{
    border: 2px solid {t.akzent}; padding: 5px 9px;
}}
QLineEdit:disabled, QComboBox:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled, QTimeEdit:disabled {{
    color: {t.gedaempft}; background: {t.tafel}; border-color: {t.linie};
}}
QComboBox::drop-down {{ border: none; width: 26px; }}
QComboBox QAbstractItemView {{
    background: {t.erhoeht}; border: 1px solid {t.linie_stark}; border-radius: {t.radius_klein}px;
    selection-background-color: #55482A; padding: 4px; outline: none;
}}
QSpinBox::up-button, QSpinBox::down-button, QDoubleSpinBox::up-button, QDoubleSpinBox::down-button,
QTimeEdit::up-button, QTimeEdit::down-button {{ width: 18px; border: none; background: transparent; }}

/* Tabellen und Listen: ruhig, ohne Gitter */
QTableView, QTableWidget, QListWidget, QListView {{
    background: {t.flaeche}; alternate-background-color: {t.zebra}; color: {t.kreide};
    border: 1px solid {t.linie}; border-radius: {t.radius}px; gridline-color: transparent;
    selection-background-color: #4A4026; selection-color: {t.kreide};
}}
QTableView::item, QListView::item {{ padding: 6px 10px; border: none; }}
QTableView::item:selected, QListView::item:selected {{ background: #4A4026; color: {t.kreide}; }}
QTableView::item:hover, QListView::item:hover {{ background: {t.erhoeht}; }}
QHeaderView {{ background: transparent; border: none; }}
QHeaderView::section {{
    background: {t.erhoeht}; color: {t.gedaempft}; font-weight: 600; padding: 8px 10px;
    border: none; border-bottom: 1px solid {t.linie_stark};
}}
QHeaderView::section:first {{ border-top-left-radius: {t.radius - 2}px; }}
QHeaderView::section:last {{ border-top-right-radius: {t.radius - 2}px; }}
QTableCornerButton::section {{ background: {t.erhoeht}; border: none; }}
{haken}
/* Reiter innerhalb der Seiten: unterstrichen statt Kästchen */
QTabWidget::pane {{ border: none; top: 0; }}
QTabBar {{ background: transparent; }}
QTabBar::tab {{
    background: transparent; color: {t.gedaempft}; padding: 9px 16px; margin-right: 4px;
    border: none; border-bottom: 2px solid transparent; font-weight: 500;
}}
QTabBar::tab:hover {{ color: {t.kreide}; }}
QTabBar::tab:selected {{ color: {t.kreide}; border-bottom: 2px solid {t.akzent}; font-weight: 700; }}
QTabBar::tab:disabled {{ color: {t.linie_stark}; }}

/* Fortschritt, Rollbalken, Teiler, Statuszeile, Menüs */
QProgressBar {{ background: {t.erhoeht}; border: none; border-radius: 3px; max-height: 6px; min-height: 6px; }}
QProgressBar::chunk {{ background: {t.akzent}; border-radius: 3px; }}
QScrollBar:vertical {{ background: transparent; width: 12px; margin: 2px; }}
QScrollBar:horizontal {{ background: transparent; height: 12px; margin: 2px; }}
QScrollBar::handle {{ background: {t.linie_stark}; border-radius: 4px; min-height: 28px; min-width: 28px; }}
QScrollBar::handle:hover {{ background: {t.gedaempft}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}
QSplitter::handle {{ background: transparent; height: 8px; }}
QStatusBar {{ background: {t.tafel}; color: {t.gedaempft}; border-top: 1px solid {t.linie}; padding: 2px 8px; }}
QStatusBar::item {{ border: none; }}
QMenuBar {{ background: {t.tafel}; color: {t.kreide}; padding: 2px 6px; }}
QMenuBar::item {{ padding: 6px 10px; border-radius: {t.radius_klein}px; background: transparent; }}
QMenuBar::item:selected {{ background: {t.erhoeht}; }}
QMenu {{ background: {t.erhoeht}; border: 1px solid {t.linie_stark}; border-radius: {t.radius}px; padding: 6px; }}
QMenu::item {{ padding: 7px 22px; border-radius: {t.radius_klein}px; }}
QMenu::item:selected {{ background: {t.erhoeht_hover}; }}
QMenu::separator {{ height: 1px; background: {t.linie}; margin: 6px 4px; }}
QToolTip {{ background: {t.erhoeht}; color: {t.kreide}; border: 1px solid {t.linie_stark}; padding: 6px 8px; }}
QWidget#zellenhuelle {{ background: transparent; }}
QDialogButtonBox QPushButton {{ min-width: 84px; }}
QMessageBox {{ background: {t.tafel}; }}
QFileDialog QWidget {{ background: {t.tafel}; }}
"""


def installiere(app: QApplication, t: Tokens = DUNKEL) -> str:
    """Schaltet das dunkle Design für die ganze Anwendung ein. Gibt die verwendete Schriftfamilie zurück."""
    app.setStyle("Fusion")
    familie = lade_schrift()
    schrift = QFont(familie)
    schrift.setPixelSize(t.normal)
    app.setFont(schrift)
    app.setPalette(palette(t))
    app.setStyleSheet(qss(t, familie, _haken_symbole(t)))
    return familie
