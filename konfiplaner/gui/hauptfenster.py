"""Hauptfenster: Schritte Daten → Regeln → Planen → Ergebnis, Export per Schaltfläche oder Menü."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QEvent
from PySide6.QtGui import QAction, QKeySequence, QShortcut
from PySide6.QtWidgets import QHBoxLayout, QLabel, QMainWindow, QTabWidget, QVBoxLayout, QWidget

from konfiplaner.anwendung import Sitzung
from konfiplaner.excel_export import ExportFehler, ZielDateiExistiertFehler
from konfiplaner.excel_import import ImportDateiFehler
from konfiplaner.gui.daten import DatenSeite
from konfiplaner.gui.design import registriere_fachfarben
from konfiplaner.gui.dialoge import Dialoge
from konfiplaner.gui.ergebnis import ErgebnisSeite
from konfiplaner.gui.konferenzen import KonferenzenSeite
from konfiplaner.gui.lehrkraefte import LehrkraefteSeite
from konfiplaner.gui.planen import PlanenSeite
from konfiplaner.gui.regeln import RegelnSeite
from konfiplaner.gui.seitenleiste import AKTUELL, FERTIG, GESPERRT, OFFEN, Seitenleiste
from konfiplaner.modell import Plan

(
    SEITE_DATEN,
    SEITE_KONFERENZEN,
    SEITE_LEHRKRAEFTE,
    SEITE_REGELN,
    SEITE_PLANEN,
    SEITE_ERGEBNIS,
) = range(6)


SCHRITTE = (
    ("Daten", "Daten laden", "Excel-Liste öffnen, Fehler prüfen und Konferenznamen vereinheitlichen."),
    (
        "Konferenzen",
        "Konferenzen auswählen",
        "Nur ausgewählte Konferenzen werden geplant. Wer eine verliert, behält die übrigen.",
    ),
    (
        "Lehrkräfte",
        "Lehrkräfte zuordnen",
        "Konferenzen, Rangfolge und Termine ändern, danach nur die Geänderten neu verplanen.",
    ),
    ("Regeln", "Planungsregeln", "Legt fest, was gelten muss und was nur gelten soll."),
    ("Planen", "Plan berechnen", "Berechnet, wer an welcher Konferenz teilnimmt."),
    ("Ergebnis", "Ergebnis prüfen", "Plan nach Termin, Person und Thema ansehen und als Excel exportieren."),
)


class Seitenstapel(QTabWidget):
    """Die Seiten des Ablaufs; die Tab-Leiste ist versteckt, die Seitenleiste übernimmt (SPEC-0011 FR-05)."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("seiten")
        self.tabBar().hide()
        self.setDocumentMode(True)
        # Tabellen scrollen selbst; so bleibt das Fenster ab 1024×600 bedienbar (SPEC-0011 FR-12)
        self.setMinimumSize(520, 240)


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
        self.lehrkraefte = LehrkraefteSeite(sitzung)
        self.regeln = RegelnSeite(sitzung, self.dialoge)
        self.planen = PlanenSeite(sitzung)
        self.ergebnis = ErgebnisSeite(sitzung)
        self.reiter = Seitenstapel()
        for seite, (kurz, _titel, _hilfe) in zip(
            (self.daten, self.konferenzen, self.lehrkraefte, self.regeln, self.planen, self.ergebnis),
            SCHRITTE,
            strict=True,
        ):
            self.reiter.addTab(seite, kurz)

        self.leiste = Seitenleiste([k for k, _, _ in SCHRITTE])
        self.leiste.gewaehlt.connect(self._waehle_seite)
        self.seitentitel = QLabel("")
        self.seitentitel.setObjectName("seitentitel")
        self.seitenhilfe = QLabel("")
        self.seitenhilfe.setObjectName("seitenhilfe")
        self.seitenhilfe.setWordWrap(True)
        rechts = QVBoxLayout()
        rechts.setContentsMargins(30, 26, 30, 10)
        rechts.setSpacing(2)
        rechts.addWidget(self.seitentitel)
        rechts.addWidget(self.seitenhilfe)
        rechts.addSpacing(14)
        rechts.addWidget(self.reiter, 1)
        zentrum = QWidget()
        zentrum.setObjectName("seite")
        huelle = QHBoxLayout(zentrum)
        huelle.setContentsMargins(0, 0, 0, 0)
        huelle.setSpacing(0)
        huelle.addWidget(self.leiste)
        huelle.addLayout(rechts, 1)
        self.setCentralWidget(zentrum)
        self.setAcceptDrops(True)
        self.statusBar().setSizeGripEnabled(False)
        self.reiter.currentChanged.connect(lambda _i: self._aktualisiere_leiste())
        for i in range(len(SCHRITTE)):
            QShortcut(QKeySequence(f"Ctrl+{i + 1}"), self, activated=lambda i=i: self._waehle_seite(i))

        self._menue()
        self.daten.oeffnen.clicked.connect(self.datei_oeffnen)
        self.daten.neu_laden.clicked.connect(self.neu_laden)
        self.daten.daten_geaendert.connect(self._daten_geaendert)
        for seite in (self.daten, self.konferenzen, self.lehrkraefte, self.regeln, self.planen):
            seite.hinweis.connect(self._hinweis)
        self.konferenzen.auswahl_geaendert.connect(self._auswahl_geaendert)
        self.regeln.profil_geaendert.connect(self._auswahl_geaendert)
        self.lehrkraefte.aenderung.connect(self._zuordnung_geaendert)
        self.lehrkraefte.neu_planen_gewuenscht.connect(self._neu_planen)
        self.planen.teil_gescheitert.connect(lambda _p: self.lehrkraefte.aktualisieren())
        self.planen.plan_fertig.connect(self._plan_fertig)
        self.planen.laeuft_geaendert.connect(self._laeuft_geaendert)
        self.ergebnis.export_gewuenscht.connect(self.exportieren)
        self.ergebnis.plan_geaendert.connect(self._brett_geaendert)
        self.ergebnis.hinweis.connect(self._hinweis)
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
        self.reiter.setTabEnabled(SEITE_LEHRKRAEFTE, geladen and not laeuft)
        self.reiter.setTabEnabled(SEITE_REGELN, geladen and not laeuft)
        self.reiter.setTabEnabled(SEITE_PLANEN, geladen)
        self.reiter.setTabEnabled(SEITE_ERGEBNIS, self.sitzung.plan is not None)
        self.reiter.setTabEnabled(SEITE_DATEN, not laeuft)
        self.aktion_export.setEnabled(self.sitzung.plan is not None and not laeuft)
        self.aktion_oeffnen.setEnabled(not laeuft)
        self.planen.aktualisieren()
        self._aktualisiere_leiste()

    def _hinweis(self, text: str) -> None:
        self.statusBar().showMessage(text)
        self._aktualisiere_leiste()

    def _waehle_seite(self, i: int) -> None:
        if self.reiter.isTabEnabled(i):
            self.reiter.setCurrentIndex(i)

    def _kurzstatus(self) -> list[str]:
        """Eine kurze Zeile je Schritt (SPEC-0011 FR-05)."""
        s = self.sitzung
        erg = s.ergebnis
        if erg is None:
            return [
                "Noch keine Datei",
                "Zuerst Datei laden",
                "Zuerst Datei laden",
                "Zuerst Datei laden",
                "Zuerst Datei laden",
                "Noch kein Plan",
            ]
        konferenzen = s.konferenzen()
        ansicht = s.lehrkraefte()
        markiert = sum(1 for a in ansicht if a.markiert)
        geaendert = sum(1 for a in ansicht if a.geaendert)
        if markiert:
            lehrer = f"{markiert} neu zu verplanen"
        elif s.neu_zuordnen:
            lehrer = f"{len(s.neu_zuordnen)} neu zuordnen"
        else:
            lehrer = f"{geaendert} geändert" if geaendert else "Unverändert"
        regeln = s.regeln()
        hart, weich = sum(r.typ == "hart" for r in regeln), sum(r.typ == "weich" for r in regeln)
        if self.planen.laeuft:
            planen = "Läuft …"
        elif not s.planbar:
            planen = "Noch nicht möglich"
        else:
            planen = "Plan berechnet" if s.plan is not None else "Bereit"
        ergebnis = (
            {"optimal": "Optimal", "machbar": "Nicht optimal", "kein_plan": "Kein Plan"}[s.plan.status]
            if s.plan is not None
            else "Noch kein Plan"
        )
        daten = f"{len(erg.personen)} Lehrkräfte" + (f", {len(erg.fehler)} Fehler" if erg.fehler else "")
        return [
            daten,
            f"{sum(k.ausgewaehlt for k in konferenzen)} von {len(konferenzen)} ausgewählt",
            lehrer,
            f"{hart} hart, {weich} weich",
            planen,
            ergebnis,
        ]

    def _aktualisiere_leiste(self) -> None:
        """Seitenleiste und Seitenkopf folgen dem Zustand der Sitzung."""
        aktuell = self.reiter.currentIndex()
        fertig = {
            SEITE_DATEN: self.sitzung.ergebnis is not None and not self.sitzung.ergebnis.fehler,
            SEITE_PLANEN: self.sitzung.plan is not None,
            SEITE_ERGEBNIS: self.sitzung.plan is not None,
        }
        for i, text in enumerate(self._kurzstatus()):
            if not self.reiter.isTabEnabled(i):
                zustand = GESPERRT
            elif i == aktuell:
                zustand = AKTUELL
            else:
                zustand = FERTIG if fertig.get(i) else OFFEN
            self.leiste.setze_schritt(i, text, zustand)
        _kurz, titel, hilfe = SCHRITTE[aktuell]
        self.seitentitel.setText(titel)
        self.seitenhilfe.setText(hilfe)
        datei = self.sitzung.datei
        self.leiste.setze_datei(datei.name if datei and self.sitzung.ergebnis else "Keine Datei geladen")

    def _daten_geaendert(self) -> None:
        self.konferenzen.aktualisieren()
        self.lehrkraefte.aktualisieren()
        self.ergebnis.aktualisieren()
        self._aktualisiere_zustand()

    def _auswahl_geaendert(self) -> None:
        self.lehrkraefte.aktualisieren()
        self.ergebnis.aktualisieren()
        self._aktualisiere_zustand()

    def _brett_geaendert(self) -> None:
        """Nach einer Verschiebung auf dem Brett: Seitenleiste und Lehrkräfte folgen dem Plan."""
        self.lehrkraefte.aktualisieren()
        self._aktualisiere_zustand()

    def _zuordnung_geaendert(self) -> None:
        self.konferenzen.aktualisieren()
        self._aktualisiere_zustand()

    def _neu_planen(self, teil: bool) -> None:
        """Wechselt zur Seite „Planen" und startet die (Teil-)Neuplanung (SPEC-0010 FR-08)."""
        self.reiter.setCurrentIndex(SEITE_PLANEN)
        self.planen.starte(teil=teil)

    def _laeuft_geaendert(self, laeuft: bool) -> None:
        self._aktualisiere_zustand()
        if laeuft:
            self.statusBar().showMessage("Planung läuft…")

    def _plan_fertig(self, plan: Plan) -> None:
        self.lehrkraefte.aktualisieren()
        self.ergebnis.aktualisieren()
        self.ergebnis.reiter.setCurrentIndex(0)  # das Verteilungsbrett ist der Einstieg
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
        registriere_fachfarben([t.name for t in self.sitzung.themen])
        self.regeln.aktualisieren()  # das Profil der Datei kann Regeln umstellen
        self.konferenzen.aktualisieren()
        self.lehrkraefte.aktualisieren()
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

    # ── Ablegen (SPEC-0011 FR-10) ────────────────────────────────────────────
    def dragEnterEvent(self, event) -> None:
        if not self.planen.laeuft and event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:
        pfade = [Path(u.toLocalFile()) for u in event.mimeData().urls() if u.isLocalFile()]
        excel = next((p for p in pfade if p.suffix.lower() == ".xlsx"), None)
        if excel is None:
            name = pfade[0].name if pfade else "Datei"
            self.statusBar().showMessage(f"„{name}“ ignoriert: abgelegt werden kann nur eine .xlsx-Datei")
            return
        event.acceptProposedAction()
        self._lade(excel)

    def closeEvent(self, event) -> None:
        self.planen.beende()
        self.sitzung.speichere()
        super().closeEvent(event)
