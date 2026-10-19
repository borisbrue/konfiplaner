"""Hauptfenster: Schritte Daten → Regeln → Planen → Ergebnis, Export per Schaltfläche oder Menü."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QEvent
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QMainWindow, QTabWidget

from konfiplaner.anwendung import Sitzung
from konfiplaner.excel_export import ExportFehler, ZielDateiExistiertFehler
from konfiplaner.excel_import import ImportDateiFehler
from konfiplaner.gui.daten import DatenSeite
from konfiplaner.gui.dialoge import Dialoge
from konfiplaner.gui.ergebnis import ErgebnisSeite
from konfiplaner.gui.konferenzen import KonferenzenSeite
from konfiplaner.gui.planen import PlanenSeite
from konfiplaner.gui.regeln import RegelnSeite
from konfiplaner.modell import Plan

SEITE_DATEN, SEITE_KONFERENZEN, SEITE_REGELN, SEITE_PLANEN, SEITE_ERGEBNIS = range(5)


class Hauptfenster(QMainWindow):
    def __init__(self, sitzung: Sitzung, dialoge: Dialoge | None = None, auto_laden: bool = True) -> None:
        super().__init__()
        self.sitzung = sitzung
        self.dialoge = dialoge or Dialoge(self)
        self._gemeldete_aenderung: float | None = None
        self.setWindowTitle("KonfiPlaner")
        self.resize(1100, 760)

        self.daten = DatenSeite(sitzung)
        self.konferenzen = KonferenzenSeite(sitzung)
        self.regeln = RegelnSeite(sitzung, self.dialoge)
        self.planen = PlanenSeite(sitzung)
        self.ergebnis = ErgebnisSeite(sitzung)
        self.reiter = QTabWidget()
        self.reiter.addTab(self.daten, "1  Daten")
        self.reiter.addTab(self.konferenzen, "2  Konferenzen")
        self.reiter.addTab(self.regeln, "3  Regeln")
        self.reiter.addTab(self.planen, "4  Planen")
        self.reiter.addTab(self.ergebnis, "5  Ergebnis")
        self.setCentralWidget(self.reiter)

        self._menue()
        self.daten.oeffnen.clicked.connect(self.datei_oeffnen)
        self.daten.neu_laden.clicked.connect(self.neu_laden)
        self.daten.daten_geaendert.connect(self._daten_geaendert)
        for seite in (self.daten, self.konferenzen, self.regeln, self.planen):
            seite.hinweis.connect(self.statusBar().showMessage)
        self.konferenzen.auswahl_geaendert.connect(self._auswahl_geaendert)
        self.planen.plan_fertig.connect(self._plan_fertig)
        self.planen.laeuft_geaendert.connect(self._laeuft_geaendert)
        self.ergebnis.export_gewuenscht.connect(self.exportieren)
        self._aktualisiere_zustand()

        if auto_laden and sitzung.datei and sitzung.datei.exists():
            self._lade(sitzung.datei, still=True)

    def _menue(self) -> None:
        datei = self.menuBar().addMenu("&Datei")
        self.aktion_oeffnen = QAction("Excel-Datei &öffnen…", self, shortcut=QKeySequence.StandardKey.Open)
        self.aktion_oeffnen.triggered.connect(self.datei_oeffnen)
        self.aktion_export = QAction("Plan &exportieren…", self, shortcut=QKeySequence("Ctrl+E"))
        self.aktion_export.triggered.connect(self.exportieren)
        ende = QAction("&Beenden", self, shortcut=QKeySequence.StandardKey.Quit)
        ende.triggered.connect(self.close)
        datei.addActions([self.aktion_oeffnen, self.aktion_export])
        datei.addSeparator()
        datei.addAction(ende)

    # ── Zustand ──────────────────────────────────────────────────────────────
    def _aktualisiere_zustand(self) -> None:
        geladen = self.sitzung.ergebnis is not None
        laeuft = self.planen.laeuft
        self.reiter.setTabEnabled(SEITE_KONFERENZEN, geladen and not laeuft)
        self.reiter.setTabEnabled(SEITE_REGELN, geladen and not laeuft)
        self.reiter.setTabEnabled(SEITE_PLANEN, geladen)
        self.reiter.setTabEnabled(SEITE_ERGEBNIS, self.sitzung.plan is not None)
        self.reiter.setTabEnabled(SEITE_DATEN, not laeuft)
        self.aktion_export.setEnabled(self.sitzung.plan is not None and not laeuft)
        self.aktion_oeffnen.setEnabled(not laeuft)
        self.planen.aktualisieren()

    def _daten_geaendert(self) -> None:
        self.konferenzen.aktualisieren()
        self.ergebnis.aktualisieren()
        self._aktualisiere_zustand()

    def _auswahl_geaendert(self) -> None:
        self.ergebnis.aktualisieren()
        self._aktualisiere_zustand()

    def _laeuft_geaendert(self, laeuft: bool) -> None:
        self._aktualisiere_zustand()
        if laeuft:
            self.statusBar().showMessage("Planung läuft…")

    def _plan_fertig(self, plan: Plan) -> None:
        self.ergebnis.aktualisieren()
        self._aktualisiere_zustand()
        self.reiter.setCurrentIndex(SEITE_ERGEBNIS)
        self.statusBar().showMessage(
            {
                "optimal": "Plan berechnet",
                "machbar": "Plan berechnet (nicht optimal)",
                "kein_plan": "Kein Plan möglich – siehe Hinweise",
            }[plan.status]
        )

    # ── Laden (FR-02) ────────────────────────────────────────────────────────
    def datei_oeffnen(self) -> None:
        start = self.sitzung.datei.parent if self.sitzung.datei else None
        pfad = self.dialoge.datei_oeffnen(start)
        if pfad is not None:
            self._lade(pfad)

    def neu_laden(self) -> None:
        if self.sitzung.datei is not None:
            self._lade(self.sitzung.datei)

    def _lade(self, pfad: Path, still: bool = False) -> None:
        try:
            erg = self.sitzung.lade(pfad)
        except (ImportDateiFehler, OSError) as e:
            if not still:
                self.dialoge.fehler("Datei laden", str(e))
            return
        self._gemeldete_aenderung = None
        self.regeln.aktualisieren()  # das Profil der Datei kann Regeln umstellen
        self.konferenzen.aktualisieren()
        self.daten.aktualisieren()
        self.ergebnis.aktualisieren()
        self._aktualisiere_zustand()
        if erg.fehler:
            self.reiter.setCurrentIndex(SEITE_DATEN)
            offen = sum(1 for z in erg.aufloesungen if z.status != "sicher")
            if erg.lehrerliste and offen:
                self.daten.reiter.setCurrentIndex(self.daten.TAB_NORMALISIERUNG)
                self.statusBar().showMessage(
                    f"{offen} Konferenznamen noch nicht zugeordnet – Reiter Normalisierung"
                )
            else:
                self.statusBar().showMessage(
                    f"{len(erg.fehler)} Fehler in der Datei – bitte korrigieren und neu laden"
                )
        elif self.sitzung.planbar and erg.lehrerliste:
            self.reiter.setCurrentIndex(SEITE_KONFERENZEN)  # hier wird die Auswahl getroffen (SPEC-0009)
            self.statusBar().showMessage(f"{pfad.name} geladen – Konferenzen auswählen oder direkt planen")
        elif self.sitzung.planbar:
            self.reiter.setCurrentIndex(SEITE_PLANEN)
            self.statusBar().showMessage(f"{pfad.name} geladen – bereit zum Planen")
        else:
            self.reiter.setCurrentIndex(SEITE_DATEN)
            self.statusBar().showMessage("Datei geladen – bitte Zeitslots erzeugen (Reiter Zeitslots)")

    def pruefe_dateiaenderung(self) -> bool:
        """Bietet das Neuladen an, wenn die Datei seit dem Laden verändert wurde. True, wenn neu geladen."""
        s = self.sitzung
        if self.planen.laeuft or not s.datei_geaendert() or s.datei is None:
            return False
        mtime = s.datei.stat().st_mtime
        if self._gemeldete_aenderung == mtime:
            return False
        self._gemeldete_aenderung = mtime
        if self.dialoge.ja_nein(
            "Datei geändert",
            f"{s.datei.name} wurde verändert. Neu laden?\n"
            "(Änderungen an Themenwerten und Zeitslots gehen verloren.)",
        ):
            self.neu_laden()
            return True
        return False

    def changeEvent(self, event: QEvent) -> None:
        super().changeEvent(event)
        if event.type() == QEvent.Type.ActivationChange and self.isActiveWindow():
            self.pruefe_dateiaenderung()

    # ── Export (FR-06) ───────────────────────────────────────────────────────
    def exportieren(self) -> None:
        if self.sitzung.plan is None:
            return
        ziel = self.dialoge.export_ziel(self.sitzung.letzter_exportordner)
        if ziel is None:
            return
        ueberschreiben = False
        while True:
            try:
                self.sitzung.exportiere(ziel, ueberschreiben)
            except ZielDateiExistiertFehler:
                if not self.dialoge.ja_nein(
                    "Datei existiert", f"{ziel.name} existiert bereits. Überschreiben?"
                ):
                    self.statusBar().showMessage("Export abgebrochen")
                    return
                ueberschreiben = True
                continue
            except ExportFehler as e:
                self.dialoge.fehler("Export", str(e))
                return
            break
        self.statusBar().showMessage(f"Exportiert nach {ziel}")

    def closeEvent(self, event) -> None:
        self.planen.beende()
        self.sitzung.speichere()
        super().closeEvent(event)
