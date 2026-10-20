"""Seite „Einladung": Tagesablauf bearbeiten und als Word-Datei exportieren (SPEC-0014 FR-08)."""

from __future__ import annotations

from datetime import date, time
from pathlib import Path

from PySide6.QtCore import QDate, QTime, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPlainTextEdit,
    QPushButton,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)

from konfiplaner.anwendung import Sitzung
from konfiplaner.excel_export import ExportFehler, ZielDateiExistiertFehler
from konfiplaner.tagesplan import Block

ZEITARTEN = {"bereich": "Von – bis", "ab": "Ab", "um": "Um"}


def _qdatum(d: date | None) -> QDate:
    return QDate(d.year, d.month, d.day) if d else QDate(2000, 1, 1)


def _qzeit(t: time | None) -> QTime:
    return QTime(t.hour, t.minute) if t else QTime(0, 0)


class EinladungSeite(QWidget):
    hinweis = Signal(str)

    def __init__(self, sitzung: Sitzung, dialoge) -> None:
        super().__init__()
        self.sitzung, self.dialoge = sitzung, dialoge
        self._sperre = False
        self._bloecke: list[Block] = []

        # Kopf
        self.datum = QDateEdit()
        self.datum.setCalendarPopup(True)
        self.datum.setDisplayFormat("dd.MM.yyyy")
        self.datum.setSpecialValueText("kein Datum")
        self.datum.setMinimumDate(QDate(2000, 1, 1))
        self.datum.setAccessibleName("Datum")
        self.titel = QLineEdit()
        self.titel.setAccessibleName("Titel")
        self.thema = QLineEdit()
        self.thema.setAccessibleName("Thema")
        self.ziele = QPlainTextEdit()
        self.ziele.setAccessibleName("Ziele, eines pro Zeile")
        self.ziele.setFixedHeight(84)
        self.arbeitsformen = QLineEdit()
        self.arbeitsformen.setAccessibleName("Arbeitsformen")
        self.vorbereitung = QLineEdit()
        self.vorbereitung.setAccessibleName("Vorbereitung")
        self.verschriftlichung = QLineEdit()
        self.verschriftlichung.setAccessibleName("Verschriftlichung")
        kopf = QFormLayout()
        kopf.addRow("Datum:", self.datum)
        kopf.addRow("Titel:", self.titel)
        kopf.addRow("Thema:", self.thema)
        kopf.addRow("Ziele (eines pro Zeile):", self.ziele)
        kopf.addRow("Arbeitsformen:", self.arbeitsformen)
        kopf.addRow("Vorbereitung:", self.vorbereitung)
        kopf.addRow("Verschriftlichung:", self.verschriftlichung)

        # Blockliste und Detail
        self.liste = QListWidget()
        self.liste.setAccessibleName("Zeitblöcke")
        self.liste.setMinimumHeight(120)
        self.neu = QPushButton("&Hinzufügen")
        self.loeschen = QPushButton("&Löschen")
        self.hoch = QPushButton("Nach &oben")
        self.runter = QPushButton("Nach &unten")
        listenknoepfe = QHBoxLayout()
        for k in (self.neu, self.loeschen, self.hoch, self.runter):
            listenknoepfe.addWidget(k)
        self.zeitart = QComboBox()
        self.zeitart.setAccessibleName("Zeitangabe")
        for schluessel, text in ZEITARTEN.items():
            self.zeitart.addItem(text, schluessel)
        self.beginn = QTimeEdit()
        self.beginn.setDisplayFormat("HH:mm")
        self.beginn.setAccessibleName("Beginn")
        self.ende = QTimeEdit()
        self.ende.setDisplayFormat("HH:mm")
        self.ende.setAccessibleName("Ende")
        zeitzeile = QHBoxLayout()
        for w in (self.zeitart, self.beginn, self.ende):
            zeitzeile.addWidget(w)
        zeitzeile.addStretch(1)
        self.block_titel = QLineEdit()
        self.block_titel.setAccessibleName("Titel des Blocks")
        self.block_inhalt = QPlainTextEdit()
        self.block_inhalt.setAccessibleName("Inhalt des Blocks")
        self.block_inhalt.setFixedHeight(96)
        self.block_wer = QLineEdit()
        self.block_wer.setAccessibleName("Wer oder wie")
        self.konferenzblock = QCheckBox("Gewählte Fachkonferenzen automatisch eintragen")
        self.detail = QWidget()
        detail = QFormLayout(self.detail)
        detail.addRow("Zeit:", zeitzeile)
        detail.addRow("Titel:", self.block_titel)
        detail.addRow("Inhalt:", self.block_inhalt)
        detail.addRow("Wer/Wie:", self.block_wer)
        detail.addRow("", self.konferenzblock)

        # Fuß
        self.logo_text = QLabel("")
        self.logo_text.setObjectName("hinweis")
        self.logo_waehlen = QPushButton("&Logo wählen…")
        self.logo_entfernen = QPushButton("Logo entfernen")
        self.pruefung = QLabel("")
        self.pruefung.setWordWrap(True)
        self.pruefung.setObjectName("hinweis")
        self.export = QPushButton("Einladung als &Word exportieren…")
        self.export.setProperty("primaer", True)
        fuss = QHBoxLayout()
        fuss.addWidget(self.logo_waehlen)
        fuss.addWidget(self.logo_entfernen)
        fuss.addWidget(self.logo_text, 1)
        fuss.addWidget(self.export)

        spalte_links = QVBoxLayout()
        spalte_links.addLayout(kopf)
        spalte_links.addStretch(1)
        spalte_rechts = QVBoxLayout()
        spalte_rechts.addWidget(self.liste, 1)
        spalte_rechts.addLayout(listenknoepfe)
        spalte_rechts.addWidget(self.detail)
        oben = QHBoxLayout()
        oben.addLayout(spalte_links, 1)
        oben.addLayout(spalte_rechts, 1)
        wurzel = QVBoxLayout(self)
        wurzel.addLayout(oben, 1)
        wurzel.addWidget(self.pruefung)
        wurzel.addLayout(fuss)

        for feld in (self.titel, self.thema, self.arbeitsformen, self.vorbereitung, self.verschriftlichung):
            feld.textChanged.connect(self._kopf_geaendert)
        self.ziele.textChanged.connect(self._kopf_geaendert)
        self.datum.dateChanged.connect(self._kopf_geaendert)
        self.liste.currentRowChanged.connect(self._block_gewaehlt)
        for feld in (self.block_titel, self.block_wer):
            feld.textChanged.connect(self._block_geaendert)
        self.block_inhalt.textChanged.connect(self._block_geaendert)
        self.zeitart.currentIndexChanged.connect(self._block_geaendert)
        self.beginn.timeChanged.connect(self._block_geaendert)
        self.ende.timeChanged.connect(self._block_geaendert)
        self.konferenzblock.toggled.connect(self._block_geaendert)
        self.neu.clicked.connect(self._hinzufuegen)
        self.loeschen.clicked.connect(self._loeschen)
        self.hoch.clicked.connect(lambda: self._verschieben(-1))
        self.runter.clicked.connect(lambda: self._verschieben(1))
        self.logo_waehlen.clicked.connect(self._logo_waehlen)
        self.logo_entfernen.clicked.connect(self._logo_entfernen)
        self.export.clicked.connect(self.exportieren)
        self.aktualisieren()

    # ── Anzeige ─────────────────────────────────────────────────────────────
    def aktualisieren(self) -> None:
        """Füllt die Felder aus dem Tagesplan der Sitzung."""
        plan = self.sitzung.tagesplan
        self._sperre = True
        try:
            self.datum.setDate(_qdatum(plan.datum))
            self.titel.setText(plan.titel)
            self.thema.setText(plan.thema)
            self.ziele.setPlainText("\n".join(plan.ziele))
            self.arbeitsformen.setText(plan.arbeitsformen)
            self.vorbereitung.setText(plan.vorbereitung)
            self.verschriftlichung.setText(plan.verschriftlichung)
            self._bloecke = list(plan.bloecke)
        finally:
            self._sperre = False
        self._liste_fuellen(0)
        self._logo_anzeigen()

    def _liste_fuellen(self, zeile: int) -> None:
        self._sperre = True
        try:
            self.liste.clear()
            for b in self._bloecke:
                self.liste.addItem(f"{b.zeit_text}  {b.titel}".strip())
            if self._bloecke:
                self.liste.setCurrentRow(min(max(zeile, 0), len(self._bloecke) - 1))
        finally:
            self._sperre = False
        self._block_gewaehlt(self.liste.currentRow())
        self._pruefen()

    def _block_gewaehlt(self, zeile: int) -> None:
        if self._sperre:
            return
        vorhanden = 0 <= zeile < len(self._bloecke)
        self.detail.setEnabled(vorhanden)
        self.loeschen.setEnabled(vorhanden)
        self.hoch.setEnabled(vorhanden and zeile > 0)
        self.runter.setEnabled(vorhanden and zeile < len(self._bloecke) - 1)
        if not vorhanden:
            return
        b = self._bloecke[zeile]
        self._sperre = True
        try:
            self.zeitart.setCurrentIndex(max(0, self.zeitart.findData(b.zeitart)))
            self.beginn.setTime(_qzeit(b.beginn))
            self.ende.setTime(_qzeit(b.ende or b.beginn))
            self.block_titel.setText(b.titel)
            self.block_inhalt.setPlainText(b.inhalt)
            self.block_wer.setText(b.wer)
            self.konferenzblock.setChecked(b.art == "konferenzen")
        finally:
            self._sperre = False
        self.ende.setEnabled(b.zeitart == "bereich")

    def _pruefen(self) -> None:
        hinweise = self.sitzung.tagesplan.pruefe()
        self.pruefung.setText("\n".join(h.text for h in hinweise))
        self.export.setEnabled(not any(h.fehler for h in hinweise))

    # ── Bearbeiten ──────────────────────────────────────────────────────────
    def _kopf_geaendert(self) -> None:
        if self._sperre:
            return
        d = self.datum.date()
        datum = None if d == self.datum.minimumDate() else date(d.year(), d.month(), d.day())
        ziele = tuple(z.strip() for z in self.ziele.toPlainText().splitlines() if z.strip())
        self.sitzung.setze_tagesplan(
            self.sitzung.tagesplan.mit(
                datum=datum,
                titel=self.titel.text(),
                thema=self.thema.text(),
                ziele=ziele,
                arbeitsformen=self.arbeitsformen.text(),
                vorbereitung=self.vorbereitung.text(),
                verschriftlichung=self.verschriftlichung.text(),
            )
        )

    def _block_geaendert(self, *_args) -> None:
        zeile = self.liste.currentRow()
        if self._sperre or not 0 <= zeile < len(self._bloecke):
            return
        art = self.zeitart.currentData()
        beginn = self.beginn.time()
        ende = self.ende.time()
        self.ende.setEnabled(art == "bereich")
        self._bloecke[zeile] = Block(
            beginn=time(beginn.hour(), beginn.minute()),
            ende=time(ende.hour(), ende.minute()) if art == "bereich" else None,
            zeitart=art,
            titel=self.block_titel.text(),
            inhalt=self.block_inhalt.toPlainText(),
            wer=self.block_wer.text(),
            art="konferenzen" if self.konferenzblock.isChecked() else "frei",
        )
        self._bloecke_speichern()
        b = self._bloecke[zeile]
        self.liste.item(zeile).setText(f"{b.zeit_text}  {b.titel}".strip())

    def _bloecke_speichern(self) -> None:
        self.sitzung.setze_tagesplan(self.sitzung.tagesplan.mit(bloecke=tuple(self._bloecke)))
        self._pruefen()

    def _hinzufuegen(self) -> None:
        zeile = self.liste.currentRow()
        vorlage = self._bloecke[zeile] if 0 <= zeile < len(self._bloecke) else None
        beginn = (vorlage.ende or vorlage.beginn) if vorlage else time(8, 0)
        self._bloecke.insert(zeile + 1, Block(beginn, None, "um", "Neuer Block"))
        self._bloecke_speichern()
        self._liste_fuellen(zeile + 1)

    def _loeschen(self) -> None:
        zeile = self.liste.currentRow()
        if not 0 <= zeile < len(self._bloecke):
            return
        del self._bloecke[zeile]
        self._bloecke_speichern()
        self._liste_fuellen(zeile)

    def _verschieben(self, richtung: int) -> None:
        zeile = self.liste.currentRow()
        ziel = zeile + richtung
        if not (0 <= zeile < len(self._bloecke) and 0 <= ziel < len(self._bloecke)):
            return
        self._bloecke[zeile], self._bloecke[ziel] = self._bloecke[ziel], self._bloecke[zeile]
        self._bloecke_speichern()
        self._liste_fuellen(ziel)

    # ── Logo und Export ─────────────────────────────────────────────────────
    def _logo_anzeigen(self) -> None:
        logo = self.sitzung.logo
        if logo is None:
            self.logo_text.setText("Kein Logo")
        elif logo.is_file():
            self.logo_text.setText(logo.name)
        else:
            self.logo_text.setText(f"{logo.name} nicht gefunden")
        self.logo_entfernen.setEnabled(logo is not None)

    def _logo_waehlen(self) -> None:
        pfad = self.dialoge.logo_oeffnen(self.sitzung.logo.parent if self.sitzung.logo else None)
        if pfad is not None:
            self.sitzung.setze_logo(pfad)
            self._logo_anzeigen()

    def _logo_entfernen(self) -> None:
        self.sitzung.setze_logo(None)
        self._logo_anzeigen()

    def exportieren(self) -> None:
        ziel = self.dialoge.einladung_ziel(self.sitzung.letzter_exportordner)
        if ziel is None:
            return
        ueberschreiben = False
        while True:
            try:
                self.sitzung.exportiere_einladung(ziel, ueberschreiben)
            except ZielDateiExistiertFehler:
                if not self.dialoge.ja_nein(
                    "Datei existiert", f"{ziel.name} existiert bereits. Überschreiben?"
                ):
                    self.hinweis.emit("Export abgebrochen")
                    return
                ueberschreiben = True
                continue
            except ExportFehler as e:
                self.dialoge.fehler("Einladung", str(e))
                return
            break
        logo = self.sitzung.logo
        zusatz = " (Logo nicht gefunden, ohne Logo)" if logo is not None and not logo.is_file() else ""
        self.hinweis.emit(f"Einladung exportiert: {Path(ziel).name}{zusatz}")
