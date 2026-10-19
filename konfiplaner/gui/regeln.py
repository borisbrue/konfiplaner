"""Seite „Regeln": Restriktionen ein-/ausschalten und gewichten (SPEC-0005 FR-03)."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
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
ZEILENHOEHE = 60  # drei Zeilen Beschreibung passen hinein


def _umhuellt(widget: QWidget) -> QWidget:
    """Setzt ein Bedienfeld mit Rand in die Zelle, damit es vertikal zentriert und nicht zellhoch ist."""
    huelle = QWidget()
    huelle.setObjectName("zellenhuelle")
    layout = QVBoxLayout(huelle)
    layout.setContentsMargins(6, 0, 6, 0)
    layout.addStretch(1)
    layout.addWidget(widget)
    layout.addStretch(1)
    return huelle


class RegelnSeite(QWidget):
    hinweis = Signal(str)

    def __init__(self, sitzung: Sitzung, dialoge) -> None:
        super().__init__()
        self.sitzung, self.dialoge = sitzung, dialoge
        self.tabelle = QTableWidget(0, len(SPALTEN))
        self.tabelle.setHorizontalHeaderLabels(SPALTEN)
        self.tabelle.setAccessibleName("Regeln")
        self.tabelle.verticalHeader().setVisible(False)
        kopf = self.tabelle.horizontalHeader()
        kopf.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        kopf.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        kopf.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        kopf.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        kopf.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.tabelle.setColumnWidth(1, 196)
        self.tabelle.setColumnWidth(2, 92)
        self.tabelle.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.tabelle.setWordWrap(True)
        self.tabelle.verticalHeader().setDefaultSectionSize(ZEILENHOEHE)
        self.tabelle.verticalHeader().setMinimumSectionSize(ZEILENHOEHE)
        self.standard = QPushButton("&Standard wiederherstellen")
        self.laden = QPushButton("Regeln aus &Datei laden…")
        knoepfe = QHBoxLayout()
        knoepfe.addWidget(self.standard)
        knoepfe.addWidget(self.laden)
        knoepfe.addStretch(1)
        wurzel = QVBoxLayout(self)
        erklaerung = QLabel(
            "Harte Regeln müssen gelten, sonst gibt es keinen Plan. Weiche Regeln dürfen verletzt werden; "
            "ein höheres Gewicht macht eine Verletzung teurer."
        )
        erklaerung.setObjectName("hinweis")
        erklaerung.setWordWrap(True)
        wurzel.addWidget(erklaerung)
        wurzel.addWidget(self.tabelle, 1)
        wurzel.addLayout(knoepfe)
        self.standard.clicked.connect(self._standard)
        self.laden.clicked.connect(self._lade_datei)
        self.aktualisieren()

    def aktualisieren(self) -> None:
        regeln = self.sitzung.regeln()
        self.tabelle.setRowCount(len(regeln))
        self._regeln = {r.name: r for r in regeln}
        self._boxen: dict[str, QComboBox] = {}
        self._spins: dict[str, QDoubleSpinBox] = {}
        for zeile, r in enumerate(regeln):
            name = QTableWidgetItem(r.name)
            name.setToolTip(r.parameter_text or r.name)
            self.tabelle.setItem(zeile, 0, name)
            box, spin = self._typ_auswahl(r), self._gewicht(r)
            self._boxen[r.name], self._spins[r.name] = box, spin
            self.tabelle.setCellWidget(zeile, 1, _umhuellt(box))
            self.tabelle.setCellWidget(zeile, 2, _umhuellt(spin))
            beschreibung = r.beschreibung or ""
            if not r.bearbeitbar:
                beschreibung = (beschreibung + " " if beschreibung else "") + "(Parameter nur per Regeldatei)"
            beschreibung_item = QTableWidgetItem(beschreibung)
            beschreibung_item.setToolTip(beschreibung)
            self.tabelle.setItem(zeile, 3, beschreibung_item)
        self.tabelle.horizontalHeader().setStretchLastSection(True)

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

    def typ_auswahl(self, name: str) -> QComboBox:
        """Auswahlfeld der Art (hart/weich/aus) einer Regel."""
        return self._boxen[name]

    def gewichtsfeld(self, name: str) -> QDoubleSpinBox:
        return self._spins[name]

    def _zeile(self, name: str) -> int:
        return next(i for i in range(self.tabelle.rowCount()) if self.tabelle.item(i, 0).text() == name)

    def _typ_geaendert(self, name: str, box: QComboBox) -> None:
        self._aenderung(name)

    def _aenderung(self, name: str) -> None:
        typ = self._boxen[name].currentData()
        gewicht = self._spins[name].value()
        try:
            self.sitzung.setze_regel(name, typ, gewicht)
        except KonfigurationsFehler as e:
            self.hinweis.emit(str(e))
            self.aktualisieren()
            return
        self._spins[name].setEnabled(typ == "weich")
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
