"""Seite „Regeln": Restriktionen ein-/ausschalten und gewichten (SPEC-0005 FR-03)."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from konfiplaner.anwendung import RegelAnsicht, Sitzung
from konfiplaner.restriktionen import KonfigurationsFehler

TYP_ANZEIGE = {"hart": "Muss gelten (hart)", "weich": "Soll gelten (weich)", "aus": "Aus"}
SPALTEN = ["Regel", "Art", "Gewicht", "Beschreibung"]


class RegelnSeite(QWidget):
    hinweis = Signal(str)

    def __init__(self, sitzung: Sitzung, dialoge) -> None:
        super().__init__()
        self.sitzung, self.dialoge = sitzung, dialoge
        self.tabelle = QTableWidget(0, len(SPALTEN))
        self.tabelle.setHorizontalHeaderLabels(SPALTEN)
        self.tabelle.setAccessibleName("Regeln")
        self.tabelle.verticalHeader().setVisible(False)
        self.tabelle.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.standard = QPushButton("&Standard wiederherstellen")
        self.laden = QPushButton("Regeln aus &Datei laden…")
        knoepfe = QHBoxLayout()
        knoepfe.addWidget(self.standard)
        knoepfe.addWidget(self.laden)
        knoepfe.addStretch(1)
        wurzel = QVBoxLayout(self)
        wurzel.addWidget(
            QLabel(
                "Harte Regeln müssen gelten, sonst gibt es keinen Plan. Weiche Regeln dürfen verletzt werden; "
                "ein höheres Gewicht macht eine Verletzung teurer."
            )
        )
        wurzel.addWidget(self.tabelle, 1)
        wurzel.addLayout(knoepfe)
        self.standard.clicked.connect(self._standard)
        self.laden.clicked.connect(self._lade_datei)
        self.aktualisieren()

    def aktualisieren(self) -> None:
        regeln = self.sitzung.regeln()
        self.tabelle.setRowCount(len(regeln))
        self._regeln = {r.name: r for r in regeln}
        for zeile, r in enumerate(regeln):
            name = QTableWidgetItem(r.name)
            name.setToolTip(r.parameter_text or r.name)
            self.tabelle.setItem(zeile, 0, name)
            self.tabelle.setCellWidget(zeile, 1, self._typ_auswahl(r))
            self.tabelle.setCellWidget(zeile, 2, self._gewicht(r))
            beschreibung = r.beschreibung or ""
            if not r.bearbeitbar:
                beschreibung = (beschreibung + " " if beschreibung else "") + "(Parameter nur per Regeldatei)"
            self.tabelle.setItem(zeile, 3, QTableWidgetItem(beschreibung))
        self.tabelle.resizeColumnsToContents()

    def _typ_auswahl(self, r: RegelAnsicht) -> QComboBox:
        box = QComboBox()
        box.setAccessibleName(f"Art der Regel {r.name}")
        for typ in r.erlaubte_typen:
            box.addItem(TYP_ANZEIGE[typ], typ)
        box.setCurrentIndex(max(0, box.findData(r.typ)))
        box.setEnabled(r.bearbeitbar or r.typ != "aus")
        box.currentIndexChanged.connect(lambda _i, n=r.name, b=box: self._typ_geaendert(n, b))
        return box

    def _gewicht(self, r: RegelAnsicht) -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setAccessibleName(f"Gewicht der Regel {r.name}")
        spin.setRange(0.1, 100.0)
        spin.setSingleStep(0.5)
        spin.setValue(r.gewicht)
        spin.setEnabled(r.typ == "weich")
        spin.valueChanged.connect(lambda _v, n=r.name: self._aenderung(n))
        return spin

    def _zeile(self, name: str) -> int:
        return next(i for i in range(self.tabelle.rowCount()) if self.tabelle.item(i, 0).text() == name)

    def _typ_geaendert(self, name: str, box: QComboBox) -> None:
        self._aenderung(name)

    def _aenderung(self, name: str) -> None:
        zeile = self._zeile(name)
        typ = self.tabelle.cellWidget(zeile, 1).currentData()
        gewicht = self.tabelle.cellWidget(zeile, 2).value()
        try:
            self.sitzung.setze_regel(name, typ, gewicht)
        except KonfigurationsFehler as e:
            self.hinweis.emit(str(e))
            self.aktualisieren()
            return
        self.tabelle.cellWidget(zeile, 2).setEnabled(typ == "weich")
        self.hinweis.emit(
            f"Regel {name}: {TYP_ANZEIGE[typ]}" + (f", Gewicht {gewicht:g}" if typ == "weich" else "")
        )

    def _standard(self) -> None:
        self.sitzung.regeln_zuruecksetzen()
        self.aktualisieren()
        self.hinweis.emit("Regeln auf Standard zurückgesetzt")

    def _lade_datei(self) -> None:
        pfad = self.dialoge.regeldatei_oeffnen(self.sitzung.datei.parent if self.sitzung.datei else None)
        if pfad is None:
            return
        try:
            self.sitzung.lade_regeldatei(pfad)
        except (KonfigurationsFehler, OSError, ValueError) as e:
            self.dialoge.fehler("Regeldatei", f"{pfad.name} konnte nicht geladen werden:\n{e}")
            return
        self.aktualisieren()
        self.hinweis.emit(f"Regeln aus {pfad.name} geladen")
