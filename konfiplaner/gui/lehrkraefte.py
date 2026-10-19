"""Seite „Lehrkräfte": manuelle Zuordnung und Teilneuplanung (SPEC-0010 FR-12)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from PySide6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    QPersistentModelIndex,
    QSortFilterProxyModel,
    Qt,
    Signal,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from konfiplaner.anwendung import LehrerAnsicht, Sitzung
from konfiplaner.gui.lehrkraft_dialoge import LehrkraftDialog, SammelDialog
from konfiplaner.gui.modelle import FEHLER_FARBE, HINWEIS_FARBE
from konfiplaner.modell import ModellFehler

LEER = QModelIndex()
KOPF = ("Lehrkraft", "Konferenzen (Rangfolge)", "Vorsitz", "Teilnahme im Plan", "Status")
FILTER = (
    ("Alle", lambda a: True),
    ("Neu zu verplanen", lambda a: a.markiert),
    ("Geändert", lambda a: a.geaendert),
    ("Neu zuordnen", lambda a: a.neu_zuordnen),
    ("Ohne Konferenz", lambda a: not a.konferenzen),
)


def status(a: LehrerAnsicht) -> str:
    teile = []
    if a.neu_zuordnen:
        teile.append("neu zuordnen")
    elif not a.konferenzen:
        teile.append("ohne Konferenz")
    if a.geaendert:
        teile.append("geändert")
    if a.markiert:
        teile.append("neu zu verplanen")
    return ", ".join(teile)


class LehrerModell(QAbstractTableModel):
    def __init__(self, sitzung: Sitzung) -> None:
        super().__init__()
        self._sitzung = sitzung
        self._zeilen: list[LehrerAnsicht] = []

    def neu(self) -> None:
        self.beginResetModel()
        self._zeilen = self._sitzung.lehrkraefte()
        self.endResetModel()

    def ansicht(self, zeile: int) -> LehrerAnsicht:
        return self._zeilen[zeile]

    def rowCount(self, parent: QModelIndex | QPersistentModelIndex = LEER) -> int:
        return 0 if parent.isValid() else len(self._zeilen)

    def columnCount(self, parent: QModelIndex | QPersistentModelIndex = LEER) -> int:
        return 0 if parent.isValid() else len(KOPF)

    def data(
        self, index: QModelIndex | QPersistentModelIndex, role: int = Qt.ItemDataRole.DisplayRole
    ) -> Any:
        if not index.isValid():
            return None
        a = self._zeilen[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            return (
                a.name,
                " › ".join(a.konferenzen),
                ", ".join(a.vorsitz_von),
                "; ".join(a.teilnahmen),
                status(a),
            )[index.column()]
        if role == Qt.ItemDataRole.BackgroundRole:
            if a.neu_zuordnen:
                return FEHLER_FARBE
            if a.markiert:
                return HINWEIS_FARBE
        return None

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole
    ) -> Any:
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return KOPF[section]
        return None


class FilterModell(QSortFilterProxyModel):
    def __init__(self, quelle: LehrerModell) -> None:
        super().__init__()
        self.setSourceModel(quelle)
        self._quelle = quelle
        self.text = ""
        self.filter: Callable[[LehrerAnsicht], bool] = FILTER[0][1]

    def aktualisiere(self) -> None:
        self.beginFilterChange()
        self.endFilterChange()

    def filterAcceptsRow(self, zeile: int, eltern: QModelIndex | QPersistentModelIndex) -> bool:
        a = self._quelle.ansicht(zeile)
        suche = self.text.casefold().strip()
        passt = not suche or suche in a.name.casefold() or any(suche in k.casefold() for k in a.konferenzen)
        return passt and self.filter(a)


class LehrkraefteSeite(QWidget):
    aenderung = Signal()
    neu_planen_gewuenscht = Signal(bool)  # True = nur markierte (Teilneuplanung)
    hinweis = Signal(str)

    def __init__(self, sitzung: Sitzung) -> None:
        super().__init__()
        self.sitzung = sitzung
        # In Tests ersetzbar: führt einen Dialog aus und liefert, ob er angenommen wurde
        self.dialog_ausfuehren: Callable[[QDialog], bool] = lambda d: d.exec() == QDialog.DialogCode.Accepted

        self.suche = QLineEdit()
        self.suche.setPlaceholderText("Suche nach Name oder Konferenz")
        self.suche.setAccessibleName("Suche")
        self.filterwahl = QComboBox()
        self.filterwahl.setAccessibleName("Filter")
        for text, _ in FILTER:
            self.filterwahl.addItem(text)
        self.zaehler = QLabel("")
        kopf = QHBoxLayout()
        kopf.addWidget(self.suche, 1)
        kopf.addWidget(self.filterwahl)

        self.modell = LehrerModell(sitzung)
        self.proxy = FilterModell(self.modell)
        self.tabelle = QTableView()
        self.tabelle.setModel(self.proxy)
        self.tabelle.setAccessibleName("Lehrkräfte")
        self.tabelle.setAlternatingRowColors(True)
        self.tabelle.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabelle.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.tabelle.verticalHeader().setVisible(False)
        kopfzeile = self.tabelle.horizontalHeader()
        kopfzeile.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        kopfzeile.setStretchLastSection(True)

        self.bearbeiten = QPushButton("&Bearbeiten…")
        self.sammel = QPushButton("&Sammeländerung…")
        self.zuruecksetzen = QPushButton("&Zurücksetzen")
        self.teil = QPushButton("&Markierte neu verplanen")
        self.alles = QPushButton("&Alles neu planen")
        knoepfe = QHBoxLayout()
        for k in (self.bearbeiten, self.sammel, self.zuruecksetzen):
            knoepfe.addWidget(k)
        knoepfe.addStretch(1)
        knoepfe.addWidget(self.teil)
        knoepfe.addWidget(self.alles)

        hinweis = QLabel(
            "Konferenzen, Rangfolge, Vorsitz und Termine einzelner oder mehrerer Lehrkräfte ändern. "
            "Geänderte Lehrkräfte sind orange markiert; „Markierte neu verplanen“ berechnet nur sie neu, "
            "der Plan der übrigen bleibt unverändert."
        )
        hinweis.setWordWrap(True)
        wurzel = QVBoxLayout(self)
        wurzel.addWidget(hinweis)
        wurzel.addLayout(kopf)
        wurzel.addWidget(self.tabelle, 1)
        wurzel.addWidget(self.zaehler)
        wurzel.addLayout(knoepfe)

        self.suche.textChanged.connect(self._filter)
        self.filterwahl.currentIndexChanged.connect(self._filter)
        self.tabelle.doubleClicked.connect(lambda _i: self.bearbeite_auswahl())
        self.tabelle.selectionModel().selectionChanged.connect(lambda *_: self._knoepfe())
        self.bearbeiten.clicked.connect(self.bearbeite_auswahl)
        self.sammel.clicked.connect(self.sammeln)
        self.zuruecksetzen.clicked.connect(self.setze_zurueck)
        self.teil.clicked.connect(lambda: self.neu_planen_gewuenscht.emit(True))
        self.alles.clicked.connect(lambda: self.neu_planen_gewuenscht.emit(False))
        self.aktualisieren()

    # ── Anzeige ──────────────────────────────────────────────────────────────
    def aktualisieren(self) -> None:
        auswahl = self.ausgewaehlte_namen()
        self.modell.neu()
        self.proxy.aktualisiere()
        for zeile in range(self.proxy.rowCount()):
            if self.proxy.index(zeile, 0).data() in auswahl:
                self.tabelle.selectRow(zeile)
        markiert = len(self.sitzung.markiert)
        self.zaehler.setText(f"{self.modell.rowCount()} Lehrkräfte, {markiert} neu zu verplanen")
        self._knoepfe()

    def _filter(self) -> None:
        self.proxy.text = self.suche.text()
        self.proxy.filter = FILTER[self.filterwahl.currentIndex()][1]
        self.proxy.aktualisiere()
        self._knoepfe()

    def _knoepfe(self) -> None:
        n = len(self.ausgewaehlte_namen())
        geladen = self.sitzung.ergebnis is not None
        self.bearbeiten.setEnabled(n == 1)
        self.sammel.setEnabled(n >= 1)
        self.zuruecksetzen.setEnabled(n >= 1)
        self.teil.setEnabled(geladen and self.sitzung.planbar and bool(self.sitzung.markiert))
        self.alles.setEnabled(geladen and self.sitzung.planbar)

    def ausgewaehlte_namen(self) -> list[str]:
        return [self.proxy.index(i.row(), 0).data() for i in self.tabelle.selectionModel().selectedRows()]

    # ── Aktionen ─────────────────────────────────────────────────────────────
    def bearbeite(self, name: str) -> None:
        if self.dialog_ausfuehren(LehrkraftDialog(self.sitzung, name, self)):
            self._geaendert(f"{name} geändert")

    def bearbeite_auswahl(self) -> None:
        namen = self.ausgewaehlte_namen()
        if len(namen) == 1:
            self.bearbeite(namen[0])

    def sammeln(self) -> None:
        namen = self.ausgewaehlte_namen()
        if namen and self.dialog_ausfuehren(SammelDialog(self.sitzung, namen, self)):
            self._geaendert(f"{len(namen)} Lehrkräfte geändert")

    def setze_zurueck(self) -> None:
        namen = self.ausgewaehlte_namen()
        try:
            for name in namen:
                self.sitzung.zuruecksetzen(name)
        except ModellFehler as e:
            self.hinweis.emit(str(e))
            return
        if namen:
            self._geaendert(f"{len(namen)} Lehrkräfte zurückgesetzt")

    def _geaendert(self, text: str) -> None:
        self.aktualisieren()
        self.aenderung.emit()
        self.hinweis.emit(text)
