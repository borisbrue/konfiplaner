"""Seite „Ergebnis": Plan nach Termin, Person und Thema, Hinweise, Export (SPEC-0005 FR-05/FR-06)."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QTableView, QTabWidget, QVBoxLayout, QWidget

from konfiplaner.anwendung import Sitzung
from konfiplaner.excel_export import SPALTEN
from konfiplaner.gui.daten import _tabelle
from konfiplaner.gui.design import DUNKEL
from konfiplaner.gui.fachfarben import fachfarben_anwenden
from konfiplaner.gui.modelle import (
    FEHLER_FARBE,
    HINWEIS_FARBE,
    TEXT_FEHLER,
    TEXT_HINWEIS,
    TEXT_OK,
    TabellenModell,
)

REITER = {"Termine": "Nach Termin", "Personen": "Nach Person", "Themen": "Nach Thema", "Hinweise": "Hinweise"}


def _schrift_thema(zeile: list, spalte: int):
    if spalte == 4:
        return TEXT_OK if zeile[4] == "ja" else TEXT_FEHLER
    return None


def _schrift_hinweis(zeile: list, spalte: int):
    if spalte == 0:
        return TEXT_FEHLER if zeile[0] == "Begründung" else TEXT_HINWEIS
    return None


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
        self.exportieren.setProperty("primaer", True)
        self.exportieren.setEnabled(False)
        self.exportieren.clicked.connect(self.export_gewuenscht)
        faerbungen = {"Themen": _faerbe_thema, "Hinweise": _faerbe_hinweis}
        schriften = {"Themen": _schrift_thema, "Hinweise": _schrift_hinweis}
        self.modelle = {
            n: TabellenModell(SPALTEN[n], faerbung=faerbungen.get(n), schrift=schriften.get(n))
            for n in REITER
        }
        self.tabellen: dict[str, QTableView] = {n: _tabelle(m, REITER[n]) for n, m in self.modelle.items()}
        for name, spalte in (("Termine", 3), ("Personen", 4), ("Themen", 0)):
            fachfarben_anwenden(self.tabellen[name], {spalte: ", "})
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
        farbe = {"optimal": DUNKEL.ok, "machbar": DUNKEL.konflikt, "kein_plan": DUNKEL.fehler}[plan.status]
        tipp = self.sitzung.tipp(plan)
        zusatz = f"<br><span style='color:{DUNKEL.hinweis}'>{tipp}</span>" if tipp else ""
        self.status.setText(f"<b style='color:{farbe}'>{text}</b> – " + "; ".join(details) + zusatz)
        self.exportieren.setEnabled(True)
