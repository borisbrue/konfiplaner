"""Seite „Daten": Datei laden, Fehlerliste, Vorschau, Themenwerte und Zeitslots (SPEC-0005 FR-02/FR-10)."""

from __future__ import annotations

from datetime import time

from PySide6.QtCore import QModelIndex, QTime, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTableView,
    QTabWidget,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)

from konfiplaner.anwendung import Sitzung
from konfiplaner.excel_import import ImportDateiFehler, finde_spalte, rohdaten
from konfiplaner.gui.modelle import (
    FEHLER_FARBE,
    HINWEIS_FARBE,
    NormalisierungsModell,
    TabellenModell,
    ThemenModell,
    VorsitzDelegate,
)
from konfiplaner.modell import ModellFehler

MELDUNGS_KOPF = ["Schwere", "Blatt", "Zeile", "Spalte", "Meldung"]


def _tabelle(modell, name: str) -> QTableView:
    t = QTableView()
    t.setModel(modell)
    t.setAccessibleName(name)
    t.setAlternatingRowColors(True)
    t.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    t.horizontalHeader().setStretchLastSection(True)
    t.verticalHeader().setVisible(False)
    return t


class DatenSeite(QWidget):
    daten_geaendert = Signal()
    hinweis = Signal(str)
    quelle_markiert = Signal(str, int, str)  # Blatt, Excel-Zeile, Spalte

    def __init__(self, sitzung: Sitzung) -> None:
        super().__init__()
        self.sitzung = sitzung
        self._roh: dict[str, list[list[str]]] = {}

        self.oeffnen = QPushButton("Excel-Datei &öffnen…")
        self.neu_laden = QPushButton("&Neu laden")
        self.neu_laden.setEnabled(False)
        self.pfad = QLabel("Noch keine Datei geladen")
        self.pfad.setWordWrap(True)
        self.zusammenfassung = QLabel("")

        kopf = QHBoxLayout()
        kopf.addWidget(self.oeffnen)
        kopf.addWidget(self.neu_laden)
        kopf.addWidget(self.pfad, 1)

        self.meldungen = TabellenModell(MELDUNGS_KOPF, faerbung=self._meldung_farbe)
        self.meldungs_tabelle = _tabelle(self.meldungen, "Fehlerliste")
        self.meldungs_tabelle.clicked.connect(self._markiere_quelle)
        self.meldungs_tabelle.activated.connect(self._markiere_quelle)

        self.blatt_auswahl = QComboBox()
        self.blatt_auswahl.setAccessibleName("Blatt der Vorschau")
        self.vorschau = TabellenModell([])
        self.vorschau_tabelle = _tabelle(self.vorschau, "Vorschau der Excel-Datei")
        vorschau = QWidget()
        v = QVBoxLayout(vorschau)
        v.addWidget(self.blatt_auswahl)
        v.addWidget(self.vorschau_tabelle)
        self.blatt_auswahl.currentTextChanged.connect(self._zeige_blatt)

        self.themen = ThemenModell(sitzung)
        self.themen.abgelehnt.connect(self.hinweis)
        self.themen.geaendert.connect(self.daten_geaendert)
        self.themen_tabelle = _tabelle(self.themen, "Themenwerte")
        self.themen_tabelle.setItemDelegateForColumn(4, VorsitzDelegate(sitzung, self.themen_tabelle))
        themen = QWidget()
        t = QVBoxLayout(themen)
        t.addWidget(
            QLabel("Wichtigkeit, Mindestanzahl, Dauer und Vorsitz lassen sich durch Doppelklick ändern.")
        )
        t.addWidget(self.themen_tabelle)

        self.slots = TabellenModell(["Tag", "Start", "Ende"])
        self.slot_tabelle = _tabelle(self.slots, "Zeitslots")
        self.tage = QLineEdit()
        self.tage.setAccessibleName("Tage, durch Komma getrennt")
        self.beginn, self.ende = QTimeEdit(), QTimeEdit()
        for feld in (self.beginn, self.ende):
            feld.setDisplayFormat("HH:mm")
        self.beginn.setAccessibleName("Beginn")
        self.ende.setAccessibleName("Ende")
        self.laenge = QSpinBox()
        self.laenge.setRange(5, 480)
        self.laenge.setSingleStep(5)
        self.laenge.setSuffix(" min")
        self.laenge.setAccessibleName("Slotlänge")
        self.erzeugen = QPushButton("Zeitslots &erzeugen")
        form = QFormLayout()
        form.addRow("Tage (mit Komma trennen):", self.tage)
        form.addRow("Beginn:", self.beginn)
        form.addRow("Ende:", self.ende)
        form.addRow("Slotlänge:", self.laenge)
        form.addRow(self.erzeugen)
        self.slot_info = QLabel("")
        slots = QWidget()
        s = QVBoxLayout(slots)
        s.addLayout(form)
        s.addWidget(self.slot_info)
        s.addWidget(self.slot_tabelle, 1)
        self.erzeugen.clicked.connect(self._erzeuge_slots)

        self.normalisierung = NormalisierungsModell(sitzung)
        self.normalisierung.abgelehnt.connect(self.hinweis)
        self.normalisierung.geaendert.connect(self._normalisierung_geaendert)
        self.normalisierung_tabelle = _tabelle(self.normalisierung, "Normalisierung der Konferenznamen")
        kopf_n = self.normalisierung_tabelle.horizontalHeader()
        kopf_n.setStretchLastSection(False)
        kopf_n.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        kopf_n.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        kopf_n.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        kopf_n.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.vorschlaege = QPushButton("&Alle Vorschläge übernehmen")
        self.vorschlaege.clicked.connect(self._alle_vorschlaege)
        normalisierung = QWidget()
        n = QVBoxLayout(normalisierung)
        n.addWidget(
            self._hinweistext(
                "Uneinheitliche Konferenznamen einmal zuordnen. Orange: Vorschlag, bitte prüfen und bestätigen; "
                "rot: unbekannt. Die Zuordnung (Spalte 3) lässt sich durch Doppelklick ändern."
            )
        )
        n.addWidget(self.vorschlaege)
        n.addWidget(self.normalisierung_tabelle, 1)

        self.ohne_konferenz = QListWidget()
        self.ohne_konferenz.setAccessibleName("Lehrkräfte ohne Konferenz")
        ohne = QWidget()
        o = QVBoxLayout(ohne)
        o.addWidget(
            self._hinweistext("Diese Personen haben keine Konferenz und nehmen an keinem Termin teil:")
        )
        o.addWidget(self.ohne_konferenz, 1)

        self.reiter = QTabWidget()
        self.reiter.addTab(vorschau, "Vorschau")
        self.reiter.addTab(themen, "Themen")
        self.reiter.addTab(slots, "Zeitslots")
        self.reiter.addTab(normalisierung, "Normalisierung")
        self.reiter.addTab(ohne, "Ohne Konferenz")
        self.TAB_NORMALISIERUNG, self.TAB_OHNE = 3, 4

        teiler = QSplitter()
        teiler.setOrientation(teiler.orientation().Vertical)
        oben = QWidget()
        o = QVBoxLayout(oben)
        o.setContentsMargins(0, 0, 0, 0)
        o.addWidget(self.zusammenfassung)
        o.addWidget(self.meldungs_tabelle)
        teiler.addWidget(oben)
        teiler.addWidget(self.reiter)
        teiler.setSizes([200, 400])

        wurzel = QVBoxLayout(self)
        wurzel.addLayout(kopf)
        wurzel.addWidget(teiler, 1)
        self.aktualisieren()

    # ── Anzeige ──────────────────────────────────────────────────────────────
    @staticmethod
    def _meldung_farbe(zeile: list):
        return FEHLER_FARBE if zeile[0] == "Fehler" else HINWEIS_FARBE

    def aktualisieren(self) -> None:
        s = self.sitzung
        erg = s.ergebnis
        self.neu_laden.setEnabled(s.datei is not None and s.datei.exists())
        self.pfad.setText(str(s.datei) if s.datei else "Noch keine Datei geladen")
        zeilen = []
        if erg:
            zeilen = [
                ["Fehler" if m.schwere == "fehler" else "Warnung", m.blatt, m.zeile, m.spalte, m.text]
                for m in erg.meldungen
            ]
            teile = [
                f"{len(erg.personen)} Personen",
                f"{len(s.themen)} Themen",
                f"{len(s.zeitslots)} Zeitslots",
                f"{len(erg.fehler)} Fehler",
                f"{len(erg.warnungen)} Warnungen",
            ]
            self.zusammenfassung.setText(", ".join(teile))
        else:
            self.zusammenfassung.setText("")
        self.meldungen.setze(zeilen)
        self.meldungs_tabelle.resizeColumnsToContents()
        self.meldungs_tabelle.horizontalHeader().setStretchLastSection(True)
        lehrerliste = bool(erg and erg.lehrerliste)
        self.reiter.setTabVisible(self.TAB_NORMALISIERUNG, lehrerliste)
        self.reiter.setTabVisible(self.TAB_OHNE, lehrerliste)
        self.normalisierung.neu()
        offen = sum(1 for a in erg.aufloesungen if a.status != "sicher") if lehrerliste and erg else 0
        self.vorschlaege.setEnabled(
            any(a.status == "vorschlag" for a in erg.aufloesungen) if lehrerliste and erg else False
        )
        self.ohne_konferenz.clear()
        self.ohne_konferenz.addItems(erg.ohne_konferenz if lehrerliste and erg else [])
        if lehrerliste and erg:
            self.zusammenfassung.setText(
                self.zusammenfassung.text()
                + f", {len(erg.ohne_konferenz)} ohne Konferenz, {offen} Zuordnungen offen"
            )
        self.themen.neu()
        self.slots.setze([[z.tag, z.start, z.ende] for z in s.zeitslots])
        quelle = "aus der Datei" if erg and erg.zeitslots and s.zeitslots == erg.zeitslots else "erzeugt"
        self.slot_info.setText(
            f"{len(s.zeitslots)} Zeitslots ({quelle})" if s.zeitslots else "Keine Zeitslots"
        )
        raster = s.zeitraster
        self.tage.setText(str(raster["tage"]))
        self.beginn.setTime(QTime.fromString(str(raster["beginn"]), "HH:mm"))
        self.ende.setTime(QTime.fromString(str(raster["ende"]), "HH:mm"))
        self.laenge.setValue(int(raster["laenge_min"]))
        self._lade_vorschau()

    def _lade_vorschau(self) -> None:
        self._roh = {}
        if self.sitzung.datei and self.sitzung.datei.exists():
            try:
                self._roh = rohdaten(self.sitzung.datei)
            except ImportDateiFehler:
                self._roh = {}
        self.blatt_auswahl.blockSignals(True)
        self.blatt_auswahl.clear()
        self.blatt_auswahl.addItems(list(self._roh))
        self.blatt_auswahl.blockSignals(False)
        self._zeige_blatt(self.blatt_auswahl.currentText())

    def _zeige_blatt(self, blatt: str) -> None:
        zeilen = self._roh.get(blatt, [])
        kopf = zeilen[0] if zeilen else []
        self.vorschau.setze([z + [""] * (len(kopf) - len(z)) for z in zeilen[1:]], kopf)

    @staticmethod
    def _hinweistext(text: str) -> QLabel:
        label = QLabel(text)
        label.setWordWrap(True)
        return label

    # ── Normalisierung (SPEC-0007) ───────────────────────────────────────────
    def _normalisierung_geaendert(self) -> None:
        self.aktualisieren()
        self.daten_geaendert.emit()

    def _alle_vorschlaege(self) -> None:
        anzahl = self.sitzung.bestaetige_vorschlaege()
        self.aktualisieren()
        self.daten_geaendert.emit()
        self.hinweis.emit(f"{anzahl} Vorschläge übernommen")

    # ── Fehlerliste → Quelle (FR-02) ─────────────────────────────────────────
    def _markiere_quelle(self, index: QModelIndex) -> None:
        zeile = self.meldungen.zeilen()[index.row()]
        _, blatt, excel_zeile, spalte, _text = zeile
        if blatt in self._roh and self.blatt_auswahl.currentText() != blatt:
            self.blatt_auswahl.setCurrentText(blatt)
        self.reiter.setCurrentIndex(0)
        kopf = self._roh.get(blatt, [[]])[0]
        spalten_index = finde_spalte(kopf, spalte) if spalte else None
        daten_zeile = excel_zeile - 2
        if 0 <= daten_zeile < self.vorschau.rowCount():
            ziel = self.vorschau.index(daten_zeile, spalten_index or 0)
            self.vorschau_tabelle.setCurrentIndex(ziel)
            self.vorschau_tabelle.scrollTo(ziel)
        self.quelle_markiert.emit(blatt, excel_zeile, spalte)
        self.hinweis.emit(
            f"Quelle: Blatt {blatt}, Zeile {excel_zeile}" + (f", Spalte {spalte}" if spalte else "")
        )

    # ── Zeitslots erzeugen (FR-10) ───────────────────────────────────────────
    def _erzeuge_slots(self) -> None:
        def zeit(feld: QTimeEdit) -> time:
            return feld.time().toPython()

        try:
            self.sitzung.erzeuge_zeitslots(
                self.tage.text(), zeit(self.beginn), zeit(self.ende), self.laenge.value()
            )
        except ModellFehler as e:
            self.hinweis.emit(str(e))
            return
        self.aktualisieren()
        self.daten_geaendert.emit()
