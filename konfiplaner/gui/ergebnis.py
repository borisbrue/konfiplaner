"""Seite „Ergebnis": Plan nach Termin, Person und Thema, Hinweise, Export (SPEC-0005 FR-05/FR-06)."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QTableView, QTabWidget, QVBoxLayout, QWidget

from konfiplaner.anwendung import Sitzung
from konfiplaner.excel_export import SPALTEN
from konfiplaner.gui.daten import _tabelle
from konfiplaner.gui.modelle import FEHLER_FARBE, HINWEIS_FARBE, TabellenModell

REITER = {"Termine": "Nach Termin", "Personen": "Nach Person", "Themen": "Nach Thema", "Hinweise": "Hinweise"}


def _faerbe_thema(zeile: list):
    return FEHLER_FARBE if zeile[4] == "nein" else None


def _faerbe_hinweis(zeile: list):
    return HINWEIS_FARBE


class ErgebnisSeite(QWidget):
    export_gewuenscht = Signal()

    def __init__(self, sitzung: Sitzung) -> None:
        super().__init__()
        self.sitzung = sitzung
        self.status = QLabel("Noch kein Plan")
        self.status.setWordWrap(True)
        self.exportieren = QPushButton("Als &Excel exportieren…")
        self.exportieren.setEnabled(False)
        self.exportieren.clicked.connect(self.export_gewuenscht)
        faerbungen = {"Themen": _faerbe_thema, "Hinweise": _faerbe_hinweis}
        self.modelle = {n: TabellenModell(SPALTEN[n], faerbung=faerbungen.get(n)) for n in REITER}
        self.tabellen: dict[str, QTableView] = {n: _tabelle(m, REITER[n]) for n, m in self.modelle.items()}
        self.reiter = QTabWidget()
        for name, tabelle in self.tabellen.items():
            self.reiter.addTab(tabelle, REITER[name])
        kopf = QHBoxLayout()
        kopf.addWidget(self.status, 1)
        kopf.addWidget(self.exportieren)
        wurzel = QVBoxLayout(self)
        wurzel.addLayout(kopf)
        wurzel.addWidget(self.reiter, 1)

    def aktualisieren(self) -> None:
        plan = self.sitzung.plan
        if plan is None:
            self.status.setText("Noch kein Plan")
            self.exportieren.setEnabled(False)
            for m in self.modelle.values():
                m.setze([])
            return
        for name, zeilen in self.sitzung.tabellen().items():
            self.modelle[name].setze(zeilen)
        for tabelle in self.tabellen.values():
            tabelle.resizeColumnsToContents()
        text = {
            "optimal": "Plan ist optimal",
            "machbar": "Plan ist gültig, aber nicht als optimal bewiesen",
            "kein_plan": "Kein Plan möglich",
        }[plan.status]
        details = [
            f"{len(plan.termine)} Termine",
            f"{len(plan.verstoesse)} Verstöße",
            f"{len(plan.warnungen)} Warnungen",
        ]
        if plan.status == "kein_plan":
            details = [*plan.begruendung[:3]]
        self.status.setText(f"{text} – " + "; ".join(details))
        self.exportieren.setEnabled(True)
