"""Fachfarben in Tabellen und Listen (SPEC-0011 FR-04): Farbpunkt vor jedem Konferenznamen."""

from __future__ import annotations

from PySide6.QtCore import QModelIndex, QPersistentModelIndex, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QPainter, QPalette
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QListWidget,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
)

from konfiplaner.gui.design import DUNKEL, fachfarbe

PUNKT = 9.0
LUECKE = 7.0
RAND = 10.0


def konferenz_name(token: str) -> str:
    """Name einer Konferenz aus einem Eintrag wie „Deutsch (Mi 14:00–15:00)“."""
    return token.partition(" (")[0].strip()


class KonferenzDelegate(QStyledItemDelegate):
    """Zeichnet Konferenznamen mit Fachfarbe; mehrere Namen sind durch `trenner` getrennt.

    Der Name steht immer neben dem Punkt, die Farbe ist nie der einzige Hinweis.
    """

    def __init__(self, eltern, trenner: str = ", ", anzeige: str | None = None) -> None:
        super().__init__(eltern)
        self.trenner = trenner
        self.anzeige = anzeige if anzeige is not None else trenner.strip() or ","

    def _teile(self, text: str) -> list[str]:
        return [t for t in (x.strip() for x in text.split(self.trenner)) if t]

    def paint(
        self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex | QPersistentModelIndex
    ) -> None:
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        text, opt.text = opt.text, ""
        widget = opt.widget
        style = widget.style() if widget else QApplication.style()
        style.drawControl(QStyle.ControlElement.CE_ItemViewItem, opt, painter, widget)
        gewaehlt = bool(opt.state & QStyle.StateFlag.State_Selected)
        vorn = opt.palette.color(QPalette.ColorRole.HighlightedText if gewaehlt else QPalette.ColorRole.Text)
        hinten = QColor(DUNKEL.gedaempft)
        painter.save()
        painter.setClipRect(opt.rect)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        fm = painter.fontMetrics()
        x = opt.rect.left() + RAND
        mitte = opt.rect.center().y()
        for i, teil in enumerate(self._teile(text)):
            if i:
                painter.setPen(hinten)
                gap = f" {self.anzeige} "
                painter.drawText(
                    QRectF(x, opt.rect.top(), fm.horizontalAdvance(gap), opt.rect.height()),
                    Qt.AlignmentFlag.AlignVCenter,
                    gap,
                )
                x += fm.horizontalAdvance(gap)
            name, _, rest = teil.partition(" (")
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(fachfarbe(name.strip()))
            painter.drawEllipse(QRectF(x, mitte - PUNKT / 2, PUNKT, PUNKT))
            x += PUNKT + LUECKE
            painter.setPen(vorn)
            breite = fm.horizontalAdvance(name)
            painter.drawText(
                QRectF(x, opt.rect.top(), breite + 2, opt.rect.height()), Qt.AlignmentFlag.AlignVCenter, name
            )
            x += breite
            if rest:
                zusatz = f" ({rest}"
                painter.setPen(hinten)
                painter.drawText(
                    QRectF(x, opt.rect.top(), fm.horizontalAdvance(zusatz) + 2, opt.rect.height()),
                    Qt.AlignmentFlag.AlignVCenter,
                    zusatz,
                )
                x += fm.horizontalAdvance(zusatz)
        painter.restore()

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex | QPersistentModelIndex) -> QSize:
        basis = super().sizeHint(option, index)
        fm = option.fontMetrics
        breite = RAND * 2
        for i, teil in enumerate(self._teile(str(index.data() or ""))):
            breite += (fm.horizontalAdvance(f" {self.anzeige} ") if i else 0) + PUNKT + LUECKE
            breite += fm.horizontalAdvance(teil.replace(" (", " ("))
        return QSize(int(max(breite, 40)), basis.height())


def fachfarben_anwenden(ansicht: QAbstractItemView, spalten: dict[int, str]) -> None:
    """Setzt den Fachfarben-Delegate für Spalten {Index: Trenner}."""
    for spalte, trenner in spalten.items():
        ansicht.setItemDelegateForColumn(spalte, KonferenzDelegate(ansicht, trenner))


class LeerListe(QListWidget):
    """Liste, die bei fehlenden Einträgen einen Hinweis zeigt, was als Nächstes zu tun ist."""

    def __init__(self, platzhalter: str = "") -> None:
        super().__init__()
        self.platzhalter = platzhalter

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        if self.count() == 0 and self.platzhalter:
            p = QPainter(self.viewport())
            p.setPen(QColor(DUNKEL.gedaempft))
            p.drawText(
                self.viewport().rect().adjusted(16, 0, -16, 0),
                Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
                self.platzhalter,
            )
