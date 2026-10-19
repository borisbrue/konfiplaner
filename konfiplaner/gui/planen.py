"""Seite „Planen": Zeitlimit, Start, Fortschritt und Abbruch (SPEC-0005 FR-04)."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from konfiplaner.anwendung import Sitzung
from konfiplaner.gui.arbeiter import PlanungsLauf
from konfiplaner.modell import Plan


class PlanenSeite(QWidget):
    plan_fertig = Signal(object)
    laeuft_geaendert = Signal(bool)
    hinweis = Signal(str)

    def __init__(self, sitzung: Sitzung) -> None:
        super().__init__()
        self.sitzung = sitzung
        self._lauf: PlanungsLauf | None = None
        self.voraussetzung = QLabel("")
        self.voraussetzung.setWordWrap(True)
        self.zeitlimit = QDoubleSpinBox()
        self.zeitlimit.setRange(1, 3600)
        self.zeitlimit.setDecimals(0)
        self.zeitlimit.setSuffix(" s")
        self.zeitlimit.setAccessibleName("Zeitlimit")
        self.zeitlimit.setValue(sitzung.zeitlimit_s)
        self.zeitlimit.valueChanged.connect(self._zeitlimit_geaendert)
        self.planen = QPushButton("&Planen")
        self.planen.setDefault(True)
        self.abbrechen = QPushButton("&Abbrechen")
        self.abbrechen.setEnabled(False)
        self.balken = QProgressBar()
        self.balken.setRange(0, 1)
        self.balken.setTextVisible(False)
        self.stand = QLabel("")
        form = QFormLayout()
        form.addRow("Zeitlimit:", self.zeitlimit)
        knoepfe = QHBoxLayout()
        knoepfe.addWidget(self.planen)
        knoepfe.addWidget(self.abbrechen)
        knoepfe.addStretch(1)
        wurzel = QVBoxLayout(self)
        wurzel.addWidget(self.voraussetzung)
        wurzel.addLayout(form)
        wurzel.addLayout(knoepfe)
        wurzel.addWidget(self.balken)
        wurzel.addWidget(self.stand)
        wurzel.addStretch(1)
        self.planen.clicked.connect(self.starte)
        self.abbrechen.clicked.connect(self.breche_ab)
        self.aktualisieren()

    @property
    def laeuft(self) -> bool:
        return self._lauf is not None

    def aktualisieren(self) -> None:
        hindernisse = self.sitzung.planungshindernisse()
        self.voraussetzung.setText(
            "Bereit zum Planen." if not hindernisse else "Planen nicht möglich: " + "; ".join(hindernisse)
        )
        self.planen.setEnabled(not hindernisse and not self.laeuft)

    def _zeitlimit_geaendert(self, wert: float) -> None:
        self.sitzung.zeitlimit_s = float(wert)
        self.sitzung.speichere()

    def starte(self) -> None:
        if self.laeuft or not self.sitzung.planbar:
            return
        self._lauf = PlanungsLauf(self.sitzung)
        self._lauf.arbeiter.fortschritt.connect(self._fortschritt)
        self._lauf.arbeiter.fertig.connect(self._fertig)
        self._lauf.arbeiter.fehler.connect(self._fehler)
        self.planen.setEnabled(False)
        self.abbrechen.setEnabled(True)
        self.balken.setRange(0, 0)
        self.stand.setText("Planung läuft…")
        self.laeuft_geaendert.emit(True)
        self._lauf.start()

    def breche_ab(self) -> None:
        if self._lauf:
            self._lauf.abbrechen()
            self.abbrechen.setEnabled(False)
            self.stand.setText("Abbruch angefordert…")

    def beende(self) -> None:
        """Bricht einen laufenden Lauf ab und wartet auf den Thread (beim Schließen des Fensters)."""
        if self._lauf:
            self._lauf.abbrechen()
            self._lauf.warte(10000)

    def _fortschritt(self, zielwert: float, sekunden: float) -> None:
        self.stand.setText(f"Beste bisherige Lösung: Zielwert {zielwert:g} nach {sekunden:.1f} s")

    def _beenden(self) -> None:
        lauf, self._lauf = self._lauf, None
        if lauf:
            lauf.warte()
        self.abbrechen.setEnabled(False)
        self.balken.setRange(0, 1)
        self.aktualisieren()
        self.laeuft_geaendert.emit(False)

    def _fertig(self, plan: Plan) -> None:
        self._beenden()
        zusatz = {
            "optimal": "optimal",
            "machbar": "nicht optimal (Zeitlimit oder Abbruch)",
            "kein_plan": "kein Plan möglich",
        }[plan.status]
        self.stand.setText(f"Fertig: {len(plan.termine)} Termine, {zusatz}")
        self.plan_fertig.emit(plan)

    def _fehler(self, text: str) -> None:
        self._beenden()
        self.stand.setText(f"Fehler: {text}")
        self.hinweis.emit(text)
