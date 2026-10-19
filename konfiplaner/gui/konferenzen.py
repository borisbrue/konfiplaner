"""Seite „Konferenzen": Auswahl der stattfindenden Konferenzen (SPEC-0009 FR-07)."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from konfiplaner.anwendung import Sitzung
from konfiplaner.gui.design import fachpunkt
from konfiplaner.gui.fachfarben import LeerListe

SPALTEN = ["Konferenz", "Mitglieder", "Vorsitz", "Termine"]


class KonferenzenSeite(QWidget):
    auswahl_geaendert = Signal()
    hinweis = Signal(str)

    def __init__(self, sitzung: Sitzung) -> None:
        super().__init__()
        self.sitzung = sitzung
        self._sperre = False
        self.alle = QPushButton("&Alle")
        self.keine = QPushButton("&Keine")
        self.zaehler = QLabel("")
        knoepfe = QHBoxLayout()
        knoepfe.addWidget(self.alle)
        knoepfe.addWidget(self.keine)
        knoepfe.addWidget(self.zaehler, 1)
        self.tabelle = QTableWidget(0, len(SPALTEN))
        self.tabelle.setHorizontalHeaderLabels(SPALTEN)
        self.tabelle.setAccessibleName("Konferenzen")
        self.tabelle.verticalHeader().setVisible(False)
        self.tabelle.setAlternatingRowColors(True)
        kopfzeile = self.tabelle.horizontalHeader()
        kopfzeile.setStretchLastSection(False)
        kopfzeile.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.neu_zuordnen = LeerListe("Niemand: Alle haben noch eine Konferenz.")
        self.neu_zuordnen.setAccessibleName("Lehrkräfte zum Neu-Zuordnen")
        self.ohne_konferenz = LeerListe("Niemand: Alle haben in der Datei eine Konferenz.")
        self.ohne_konferenz.setAccessibleName("Lehrkräfte ohne Konferenz")
        listen = QHBoxLayout()
        for titel, liste in (
            ("Neu zuordnen (Konferenz abgewählt)", self.neu_zuordnen),
            ("Ohne Konferenz (schon in der Datei)", self.ohne_konferenz),
        ):
            spalte = QVBoxLayout()
            ueberschrift = QLabel(titel)
            ueberschrift.setWordWrap(True)
            spalte.addWidget(ueberschrift)
            spalte.addWidget(liste, 1)
            listen.addLayout(spalte)
        wurzel = QVBoxLayout(self)
        wurzel.addLayout(knoepfe)
        wurzel.addWidget(self.tabelle, 3)
        wurzel.addLayout(listen, 2)
        self.alle.clicked.connect(lambda: self._alle(True))
        self.keine.clicked.connect(lambda: self._alle(False))
        self.tabelle.itemChanged.connect(self._geaendert)
        self.aktualisieren()

    def aktualisieren(self) -> None:
        self._sperre = True
        try:
            konferenzen = self.sitzung.konferenzen()
            self.tabelle.setRowCount(len(konferenzen))
            for zeile, k in enumerate(konferenzen):
                name = QTableWidgetItem(k.name)
                name.setFlags(
                    Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsSelectable
                )
                name.setCheckState(Qt.CheckState.Checked if k.ausgewaehlt else Qt.CheckState.Unchecked)
                name.setIcon(fachpunkt(k.name))
                self.tabelle.setItem(zeile, 0, name)
                for spalte, wert in ((1, str(k.mitglieder)), (2, k.vorsitz or ""), (3, str(k.termine))):
                    eintrag = QTableWidgetItem(wert)
                    eintrag.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                    if spalte in (1, 3):
                        eintrag.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    self.tabelle.setItem(zeile, spalte, eintrag)
            kopfzeile = self.tabelle.horizontalHeader()
            kopfzeile.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            for spalte in (1, 2, 3):
                kopfzeile.setSectionResizeMode(spalte, QHeaderView.ResizeMode.ResizeToContents)
            for spalte in (1, 3):  # Zahlen rechtsbündig, auch die Überschrift
                self.tabelle.horizontalHeaderItem(spalte).setTextAlignment(
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )
            gewaehlt = sum(1 for k in konferenzen if k.ausgewaehlt)
            self.zaehler.setText(f"{gewaehlt} von {len(konferenzen)} Konferenzen ausgewählt")
            self.neu_zuordnen.clear()
            self.neu_zuordnen.addItems(self.sitzung.neu_zuordnen)
            self.ohne_konferenz.clear()
            self.ohne_konferenz.addItems(
                self.sitzung.ergebnis.ohne_konferenz if self.sitzung.ergebnis else []
            )
        finally:
            self._sperre = False

    def _geaendert(self, eintrag: QTableWidgetItem) -> None:
        if self._sperre or eintrag.column() != 0:
            return
        self.sitzung.waehle(eintrag.text(), eintrag.checkState() == Qt.CheckState.Checked)
        self.aktualisieren()
        self.auswahl_geaendert.emit()

    def _alle(self, ausgewaehlt: bool) -> None:
        self.sitzung.waehle_alle(ausgewaehlt)
        self.aktualisieren()
        self.auswahl_geaendert.emit()
        self.hinweis.emit("Alle Konferenzen ausgewählt" if ausgewaehlt else "Keine Konferenz ausgewählt")
