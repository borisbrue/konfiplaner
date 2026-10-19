"""Tabellenmodelle für die Ansichten."""

from __future__ import annotations

from collections.abc import Callable
from datetime import time
from typing import Any

from PySide6.QtCore import QAbstractTableModel, QModelIndex, QPersistentModelIndex, Qt, Signal
from PySide6.QtGui import QColor

from konfiplaner.anwendung import Sitzung
from konfiplaner.modell import ModellFehler

LEER = QModelIndex()
HINWEIS_FARBE = QColor(255, 170, 0, 70)
FEHLER_FARBE = QColor(220, 50, 50, 70)


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
    ) -> None:
        super().__init__()
        self._kopf, self._zeilen, self._faerbung = kopf, zeilen or [], faerbung

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
        return None

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole
    ) -> Any:
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self._kopf[section]
        return None

    def zeilen(self) -> list[list]:
        return self._zeilen


class ThemenModell(QAbstractTableModel):
    """Themenwerte der Sitzung; Wichtigkeit, Mindestanzahl und Dauer sind bearbeitbar (SPEC-0005 FR-10)."""

    KOPF = ("Thema", "Wichtigkeit (1–5)", "Mindestanzahl", "Dauer (Minuten)")
    FELDER = (None, "wichtigkeit", "mindestanzahl", "dauer_min")
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
        wert = (t.name, t.wichtigkeit, t.mindestanzahl, t.dauer_min)[index.column()]
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
            self._sitzung.setze_thema(index.row(), **{feld: int(str(value).strip())})
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
