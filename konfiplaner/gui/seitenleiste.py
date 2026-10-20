"""Seitenleiste mit den Schritten des Ablaufs (SPEC-0011 FR-05)."""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPen
from PySide6.QtWidgets import (
    QAbstractButton,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from konfiplaner.gui.design import DUNKEL, Tokens

AKTUELL, FERTIG, OFFEN, GESPERRT = "aktuell", "fertig", "offen", "gesperrt"


class SchrittKnopf(QAbstractButton):
    """Ein Schritt: Nummer (oder Haken), Name und Kurzstatus."""

    def __init__(self, nummer: int, titel: str, t: Tokens = DUNKEL) -> None:
        super().__init__()
        self.nummer, self.titel, self.status, self.zustand, self.t = nummer, titel, "", OFFEN, t
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAccessibleName(f"Schritt {nummer}: {titel}")

    def setze(self, status: str, zustand: str) -> None:
        self.status, self.zustand = status, zustand
        self.setEnabled(zustand != GESPERRT)
        self.setAccessibleDescription(f"{status}, {zustand}")
        self.setCursor(
            Qt.CursorShape.ForbiddenCursor if zustand == GESPERRT else Qt.CursorShape.PointingHandCursor
        )
        self.update()

    def sizeHint(self) -> QSize:
        return QSize(236, 54)

    def minimumSizeHint(self) -> QSize:
        return QSize(236, 42)  # in kleinen Fenstern rücken die Schritte zusammen (z. B. bei der Update-Karte)

    def paintEvent(self, _event) -> None:
        t, p = self.t, QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        flaeche = QRectF(self.rect()).adjusted(8, 3, -8, -3)
        gesperrt = self.zustand == GESPERRT
        if self.zustand == AKTUELL:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(t.erhoeht))
            p.drawRoundedRect(flaeche, t.radius, t.radius)
        elif self.underMouse() and not gesperrt:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(t.zebra))
            p.drawRoundedRect(flaeche, t.radius, t.radius)
        if self.hasFocus() and self._tastaturfokus:
            p.setPen(QPen(QColor(t.akzent), 2))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(flaeche.adjusted(1, 1, -1, -1), t.radius, t.radius)
        # Nummer oder Haken im Kreis
        d = 28.0
        kreis = QRectF(flaeche.left() + 12, flaeche.center().y() - d / 2, d, d)
        font = QFont(self.font())
        font.setPixelSize(t.normal)
        font.setWeight(QFont.Weight.Bold)
        if self.zustand == AKTUELL:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(t.akzent))
            p.drawEllipse(kreis)
            farbe = QColor(t.auf_akzent)
        elif self.zustand == FERTIG:
            p.setPen(QPen(QColor(t.ok), 2))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(kreis.adjusted(1, 1, -1, -1))
            farbe = QColor(t.ok)
        else:
            p.setPen(QPen(QColor(t.linie_stark if not gesperrt else t.linie), 2))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(kreis.adjusted(1, 1, -1, -1))
            farbe = QColor(t.gedaempft if not gesperrt else t.linie_stark)
        p.setFont(font)
        p.setPen(farbe)
        if self.zustand == FERTIG:
            p.setPen(
                QPen(farbe, 2.4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
            )
            cx, cy = kreis.center().x(), kreis.center().y()
            self._haken(p, cx, cy)
        else:
            p.drawText(kreis, Qt.AlignmentFlag.AlignCenter, str(self.nummer))
        # Text
        x = kreis.right() + 14
        breite = flaeche.right() - x - 8
        titel_font = QFont(self.font())
        titel_font.setPixelSize(t.normal + 1)
        titel_font.setWeight(QFont.Weight.DemiBold)
        status_font = QFont(self.font())
        status_font.setPixelSize(t.klein)
        p.setFont(titel_font)
        p.setPen(QColor(t.gedaempft if gesperrt else t.kreide))
        mitte = flaeche.center().y()
        p.drawText(QRectF(x, mitte - 21, breite, 20), Qt.AlignmentFlag.AlignVCenter, self.titel)
        p.setFont(status_font)
        p.setPen(QColor(t.linie_stark if gesperrt else t.gedaempft))
        elide = QFontMetrics(status_font).elidedText(self.status, Qt.TextElideMode.ElideRight, int(breite))
        p.drawText(QRectF(x, mitte + 1, breite, 18), Qt.AlignmentFlag.AlignVCenter, elide)

    @staticmethod
    def _haken(p: QPainter, cx: float, cy: float) -> None:
        p.drawPolyline([QPointF(cx - 5, cy + 0.5), QPointF(cx - 1.5, cy + 4), QPointF(cx + 5, cy - 4)])

    def enterEvent(self, event) -> None:
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self.update()
        super().leaveEvent(event)

    def focusInEvent(self, event) -> None:
        self._tastaturfokus = event.reason() in (
            Qt.FocusReason.TabFocusReason,
            Qt.FocusReason.BacktabFocusReason,
            Qt.FocusReason.ShortcutFocusReason,
        )
        self.update()
        super().focusInEvent(event)

    def focusOutEvent(self, event) -> None:
        self.update()
        super().focusOutEvent(event)

    def keyPressEvent(self, event) -> None:
        if event.key() in (Qt.Key.Key_Down, Qt.Key.Key_Up):
            self.focusNextPrevChild(event.key() == Qt.Key.Key_Down)
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            self.click()
        else:
            super().keyPressEvent(event)


class Seitenleiste(QWidget):
    gewaehlt = Signal(int)
    update_ansehen = Signal()
    update_spaeter = Signal()

    def __init__(self, titel: list[str], t: Tokens = DUNKEL) -> None:
        super().__init__()
        self.setObjectName("seitenleiste")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedWidth(252)
        self.setStyleSheet(
            f"QWidget#seitenleiste {{ background: {t.eingabe}; border-right: 1px solid {t.linie}; }}"
        )
        marke = QLabel("KonfiPlaner")
        marke.setStyleSheet(
            f"font-size: 21px; font-weight: 700; color: {t.kreide}; padding: 4px 20px 0 20px;"
        )
        unter = QLabel("Fachkonferenzen planen")
        unter.setStyleSheet(f"font-size: {t.klein + 1}px; color: {t.gedaempft}; padding: 0 20px 18px 20px;")
        self.datei = QLabel("Keine Datei geladen")
        self.datei.setStyleSheet(
            f"font-size: {t.klein}px; color: {t.gedaempft}; padding: 10px 20px 14px 20px;"
        )
        self.datei.setWordWrap(True)
        self.version = QLabel("")
        self.version.setStyleSheet(
            f"font-size: {t.klein}px; color: {t.gedaempft}; padding: 0 20px 12px 20px;"
        )
        self.update_text = QLabel("")
        self.update_text.setStyleSheet(f"font-weight: 600; color: {t.kreide};")
        self.update_text.setWordWrap(True)
        self.ansehen = QPushButton("Ansehen")
        self.ansehen.setProperty("primaer", True)
        self.ansehen.setAccessibleName("Neue Version ansehen")
        self.spaeter = QPushButton("Später")
        self.spaeter.setAccessibleName("Hinweis auf neue Version ausblenden")
        self.ansehen.clicked.connect(self.update_ansehen)
        self.spaeter.clicked.connect(self.update_spaeter)
        self.update_karte = QFrame()
        self.update_karte.setObjectName("updatekarte")
        self.update_karte.setStyleSheet(
            f"QFrame#updatekarte {{ background: {t.flaeche}; border: 1px solid {t.akzent}; border-radius: 10px; }}"
        )
        karte = QVBoxLayout(self.update_karte)
        karte.setContentsMargins(12, 10, 12, 10)
        karte.setSpacing(8)
        karte.addWidget(self.update_text)
        knoepfe = QHBoxLayout()
        knoepfe.setSpacing(8)
        knoepfe.addWidget(self.ansehen)
        knoepfe.addWidget(self.spaeter)
        karte.addLayout(knoepfe)
        self.update_karte.setVisible(False)
        karten_huelle = QVBoxLayout()
        karten_huelle.setContentsMargins(12, 0, 12, 0)
        karten_huelle.addWidget(self.update_karte)
        self.schritte = [SchrittKnopf(i + 1, name, t) for i, name in enumerate(titel)]
        wurzel = QVBoxLayout(self)
        wurzel.setContentsMargins(0, 22, 0, 0)
        wurzel.setSpacing(0)
        wurzel.addWidget(marke)
        wurzel.addWidget(unter)
        for i, s in enumerate(self.schritte):
            s.clicked.connect(lambda _c=False, i=i: self.gewaehlt.emit(i))
            wurzel.addWidget(s)
        wurzel.addStretch(1)
        wurzel.addLayout(karten_huelle)
        wurzel.addWidget(self.datei)
        wurzel.addWidget(self.version)

    def setze_schritt(self, i: int, status: str, zustand: str) -> None:
        self.schritte[i].setze(status, zustand)

    def setze_datei(self, text: str) -> None:
        self.datei.setText(text)

    def setze_version(self, text: str) -> None:
        self.version.setText(text)

    def zeige_update(self, version: str | None) -> None:
        """Zeigt die Hinweiskarte „Version X verfügbar“ oder blendet sie aus (SPEC-0015 FR-04)."""
        self.update_text.setText(f"Version {version} verfügbar" if version else "")
        self.update_karte.setVisible(bool(version))
