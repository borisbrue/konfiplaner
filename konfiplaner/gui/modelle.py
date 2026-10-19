"""Tabellenmodelle für die Ansichten."""

from __future__ import annotations

from collections.abc import Callable
from datetime import time
from typing import Any

from PySide6.QtCore import (
    QAbstractItemModel,
    QAbstractTableModel,
    QModelIndex,
    QPersistentModelIndex,
    Qt,
    Signal,
)
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QComboBox, QStyledItemDelegate, QStyleOptionViewItem, QWidget

from konfiplaner.anwendung import Sitzung
from konfiplaner.gui.design import DUNKEL
from konfiplaner.modell import ModellFehler

LEER = QModelIndex()


def _tint(hex_: str, alpha: int) -> QColor:
    c = QColor(hex_)
    c.setAlpha(alpha)
    return c


# Zeilenhinterlegung: Koralle für Konflikte und Hinweise, Rose für Fehler (immer mit Text daneben)
HINWEIS_FARBE = _tint(DUNKEL.konflikt, 58)
FEHLER_FARBE = _tint(DUNKEL.fehler, 62)
TEXT_HINWEIS = QColor(DUNKEL.konflikt)
TEXT_FEHLER = QColor(DUNKEL.fehler)
TEXT_OK = QColor(DUNKEL.ok)


def formatiere(wert: Any) -> str:
    if isinstance(wert, time):
        return f"{wert:%H:%M}"
    return "" if wert is None else str(wert)


class TabellenModell(QAbstractTableModel):
    """Schreibgeschützte Tabelle aus Kopf und Zeilen; `faerbung(zeile)` liefert optional eine Hintergrundfarbe."""

    def __init__(
        self,
        kopf: list[str],
        zeilen: list[list] | None = None,
        faerbung: Callable[[list], QColor | None] | None = None,
        schrift: Callable[[list, int], QColor | None] | None = None,
    ) -> None:
        super().__init__()
        self._kopf, self._zeilen, self._faerbung = kopf, zeilen or [], faerbung
        self._schrift = schrift  # Textfarbe je Zelle (Status in Farbe, immer zusätzlich als Text)

    def setze(self, zeilen: list[list], kopf: list[str] | None = None) -> None:
        self.beginResetModel()
        if kopf is not None:
            self._kopf = kopf
        self._zeilen = zeilen
        self.endResetModel()

    def rowCount(self, parent: QModelIndex | QPersistentModelIndex = LEER) -> int:
        return 0 if parent.isValid() else len(self._zeilen)

    def columnCount(self, parent: QModelIndex | QPersistentModelIndex = LEER) -> int:
        return 0 if parent.isValid() else len(self._kopf)

    def data(
        self, index: QModelIndex | QPersistentModelIndex, role: int = Qt.ItemDataRole.DisplayRole
    ) -> Any:
        if not index.isValid():
            return None
        zeile = self._zeilen[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            return formatiere(zeile[index.column()]) if index.column() < len(zeile) else ""
        if role == Qt.ItemDataRole.BackgroundRole and self._faerbung:
            return self._faerbung(zeile)
        if role == Qt.ItemDataRole.ForegroundRole and self._schrift:
            return self._schrift(zeile, index.column())
        if role == Qt.ItemDataRole.TextAlignmentRole and index.column() < len(zeile):
            wert = zeile[index.column()]
            if isinstance(wert, (int, float)) and not isinstance(wert, bool):
                return int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        return None

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole
    ) -> Any:
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self._kopf[section]
        if role == Qt.ItemDataRole.TextAlignmentRole and orientation == Qt.Orientation.Horizontal:
            zahlen = bool(self._zeilen) and all(
                isinstance(z[section], int) and not isinstance(z[section], bool)
                for z in self._zeilen
                if section < len(z)
            )
            return int(
                (Qt.AlignmentFlag.AlignRight if zahlen else Qt.AlignmentFlag.AlignLeft)
                | Qt.AlignmentFlag.AlignVCenter
            )
        return None

    def zeilen(self) -> list[list]:
        return self._zeilen


class ThemenModell(QAbstractTableModel):
    """Themenwerte der Sitzung; Wichtigkeit, Mindestanzahl und Dauer sind bearbeitbar (SPEC-0005 FR-10)."""

    KOPF = ("Thema", "Wichtigkeit (1–5)", "Mindestanzahl", "Dauer (Minuten)", "Vorsitz")
    FELDER = (None, "wichtigkeit", "mindestanzahl", "dauer_min", "vorsitz")
    abgelehnt = Signal(str)
    geaendert = Signal()

    def __init__(self, sitzung: Sitzung) -> None:
        super().__init__()
        self._sitzung = sitzung

    def neu(self) -> None:
        self.beginResetModel()
        self.endResetModel()

    def rowCount(self, parent: QModelIndex | QPersistentModelIndex = LEER) -> int:
        return 0 if parent.isValid() else len(self._sitzung.themen)

    def columnCount(self, parent: QModelIndex | QPersistentModelIndex = LEER) -> int:
        return 0 if parent.isValid() else len(self.KOPF)

    def data(
        self, index: QModelIndex | QPersistentModelIndex, role: int = Qt.ItemDataRole.DisplayRole
    ) -> Any:
        if not index.isValid():
            return None
        t = self._sitzung.themen[index.row()]
        wert = (t.name, t.wichtigkeit, t.mindestanzahl, t.dauer_min, t.vorsitz or "")[index.column()]
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            return str(wert)
        return None

    def flags(self, index: QModelIndex | QPersistentModelIndex) -> Qt.ItemFlag:
        basis = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
        return basis | Qt.ItemFlag.ItemIsEditable if index.column() else basis

    def setData(
        self, index: QModelIndex | QPersistentModelIndex, value: Any, role: int = Qt.ItemDataRole.EditRole
    ) -> bool:
        feld = self.FELDER[index.column()] if index.isValid() else None
        if role != Qt.ItemDataRole.EditRole or feld is None:
            return False
        try:
            eingabe = str(value).strip() if feld == "vorsitz" else int(str(value).strip())
            self._sitzung.setze_thema(index.row(), **{feld: eingabe})
        except (ValueError, ModellFehler) as e:
            self.abgelehnt.emit(str(e) if isinstance(e, ModellFehler) else "Bitte eine ganze Zahl eingeben")
            return False
        self.dataChanged.emit(index, index)
        self.geaendert.emit()
        return True

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole
    ) -> Any:
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self.KOPF[section]
        return None


class VorsitzDelegate(QStyledItemDelegate):
    """Auswahl des Vorsitzes aus den Personen (oder „keiner") statt freier Texteingabe."""

    def __init__(self, sitzung: Sitzung, eltern: QWidget | None = None) -> None:
        super().__init__(eltern)
        self._sitzung = sitzung

    def createEditor(
        self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex | QPersistentModelIndex
    ) -> QWidget:
        box = QComboBox(parent)
        box.setAccessibleName("Vorsitz")
        box.addItem("(keiner)", "")
        for name in self._sitzung.personen_namen():
            box.addItem(name, name)
        return box

    def setEditorData(self, editor: QWidget, index: QModelIndex | QPersistentModelIndex) -> None:
        if isinstance(editor, QComboBox):
            editor.setCurrentIndex(max(0, editor.findData(index.data(Qt.ItemDataRole.EditRole) or "")))

    def setModelData(
        self, editor: QWidget, model: QAbstractItemModel, index: QModelIndex | QPersistentModelIndex
    ) -> None:
        if isinstance(editor, QComboBox):
            model.setData(index, editor.currentData(), Qt.ItemDataRole.EditRole)


STATUS_TEXT = {"sicher": "sicher", "vorschlag": "Vorschlag – bitte bestätigen", "unbekannt": "unbekannt"}


class NormalisierungsModell(QAbstractTableModel):
    """Rohwerte der Lehrerliste mit Vorkommen, bearbeitbarer Zuordnung und Status (SPEC-0007 FR-11)."""

    KOPF = ("Rohwert", "Vorkommen", "Zuordnung (mit Komma trennen)", "Status")
    abgelehnt = Signal(str)
    geaendert = Signal()

    def __init__(self, sitzung: Sitzung) -> None:
        super().__init__()
        self._sitzung = sitzung
        self._zeilen: list = []

    def neu(self) -> None:
        self.beginResetModel()
        erg = self._sitzung.ergebnis
        rang = {"unbekannt": 0, "vorschlag": 1, "sicher": 2}
        self._zeilen = (
            sorted(erg.aufloesungen, key=lambda a: (rang[a.status], -a.vorkommen, a.roh)) if erg else []
        )
        self.endResetModel()

    def zeile(self, i: int):
        return self._zeilen[i]

    def rowCount(self, parent: QModelIndex | QPersistentModelIndex = LEER) -> int:
        return 0 if parent.isValid() else len(self._zeilen)

    def columnCount(self, parent: QModelIndex | QPersistentModelIndex = LEER) -> int:
        return 0 if parent.isValid() else len(self.KOPF)

    def data(
        self, index: QModelIndex | QPersistentModelIndex, role: int = Qt.ItemDataRole.DisplayRole
    ) -> Any:
        if not index.isValid():
            return None
        a = self._zeilen[index.row()]
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            return (a.roh, str(a.vorkommen), ", ".join(a.konferenzen), STATUS_TEXT[a.status])[index.column()]
        if role == Qt.ItemDataRole.BackgroundRole:
            return {"unbekannt": FEHLER_FARBE, "vorschlag": HINWEIS_FARBE}.get(a.status)
        return None

    def flags(self, index: QModelIndex | QPersistentModelIndex) -> Qt.ItemFlag:
        basis = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
        return basis | Qt.ItemFlag.ItemIsEditable if index.column() == 2 else basis

    def setData(
        self, index: QModelIndex | QPersistentModelIndex, value: Any, role: int = Qt.ItemDataRole.EditRole
    ) -> bool:
        if role != Qt.ItemDataRole.EditRole or index.column() != 2:
            return False
        namen = [n.strip() for n in str(value).split(",") if n.strip()]
        if not namen:
            self.abgelehnt.emit("Mindestens eine Konferenz eintragen")
            return False
        self._sitzung.bestaetige(self._zeilen[index.row()].roh, namen)
        self.geaendert.emit()
        return True

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole
    ) -> Any:
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self.KOPF[section]
        return None
