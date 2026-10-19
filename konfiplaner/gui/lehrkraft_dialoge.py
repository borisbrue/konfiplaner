"""Dialoge zur manuellen Zuordnung (SPEC-0010 FR-12). Die Logik liegt in `Sitzung`; hier nur die Bedienung."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from konfiplaner.anwendung import Sitzung
from konfiplaner.modell import ModellFehler


def _liste(name: str, mehrfach: bool = False) -> QListWidget:
    liste = QListWidget()
    liste.setAccessibleName(name)
    if mehrfach:
        liste.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
    return liste


def _haken_liste(name: str, eintraege: list[tuple[str, object, bool]]) -> QListWidget:
    liste = _liste(name)
    for text, daten, an in eintraege:
        e = QListWidgetItem(text)
        e.setData(Qt.ItemDataRole.UserRole, daten)
        e.setFlags(e.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        e.setCheckState(Qt.CheckState.Checked if an else Qt.CheckState.Unchecked)
        liste.addItem(e)
    return liste


def _gehakt(liste: QListWidget) -> set:
    return {
        liste.item(i).data(Qt.ItemDataRole.UserRole)
        for i in range(liste.count())
        if liste.item(i).checkState() == Qt.CheckState.Checked
    }


class LehrkraftDialog(QDialog):
    """Bearbeiten einer Lehrkraft: Konferenzen und Rangfolge, Vorsitz, gesperrte und feste Termine."""

    def __init__(self, sitzung: Sitzung, name: str, eltern: QWidget | None = None) -> None:
        super().__init__(eltern)
        self.sitzung, self.name = sitzung, name
        self.setWindowTitle(f"Lehrkraft bearbeiten: {name}")
        ansicht = next(a for a in sitzung.lehrkraefte() if a.name == name)
        alle = [k.name for k in sitzung.konferenzen()]
        zugeordnet = list(sitzung.konferenzen_von(name))

        # Reiter Konferenzen: Zugeordnet (Rangfolge) und Verfügbare
        self.zugeordnet = _liste("Zugeordnete Konferenzen in Rangfolge")
        self.zugeordnet.addItems(zugeordnet)
        self.verfuegbar = _liste("Weitere Konferenzen")
        self.verfuegbar.addItems([k for k in alle if k not in zugeordnet])
        self.hinzu, self.weg = QPushButton("← &Hinzufügen"), QPushButton("&Entfernen →")
        self.hoch, self.runter = QPushButton("▲ &Höher"), QPushButton("▼ &Tiefer")
        mitte = QVBoxLayout()
        for k in (self.hinzu, self.weg, self.hoch, self.runter):
            mitte.addWidget(k)
        mitte.addStretch(1)
        links, rechts = QVBoxLayout(), QVBoxLayout()
        links.addWidget(QLabel("Zugeordnet (Rangfolge: oben = Fachkonferenz I)"))
        links.addWidget(self.zugeordnet)
        rechts.addWidget(QLabel("Weitere Konferenzen"))
        rechts.addWidget(self.verfuegbar)
        konferenzen = QWidget()
        h = QHBoxLayout(konferenzen)
        h.addLayout(links, 1)
        h.addLayout(mitte)
        h.addLayout(rechts, 1)
        self.hinzu.clicked.connect(self._hinzufuegen)
        self.weg.clicked.connect(self._entfernen)
        self.hoch.clicked.connect(lambda: self._verschiebe(-1))
        self.runter.clicked.connect(lambda: self._verschiebe(1))

        # Reiter Vorsitz
        self._chair = {k.name: k.vorsitz for k in sitzung.konferenzen()}
        self.vorsitz = _haken_liste(
            "Konferenzen mit dieser Lehrkraft als Vorsitz",
            [
                (f"{k}" + (f" (jetzt: {v})" if v and v != name else ""), k, v == name)
                for k, v in self._chair.items()
            ],
        )
        vorsitz = QWidget()
        v = QVBoxLayout(vorsitz)
        v.addWidget(
            QLabel("Häkchen setzen = diese Lehrkraft leitet die Konferenz (ersetzt den bisherigen Vorsitz).")
        )
        v.addWidget(self.vorsitz)

        # Reiter Termine (richtet sich nach den Konferenzen des Reiters „Konferenzen")
        aenderung = sitzung.zuordnung.personen.get(name)
        self._gesperrt0 = set(aenderung.nicht_verfuegbar) if aenderung else set()
        self._fest0 = set(aenderung.fest) if aenderung else set()
        self.gesperrt = _liste("Nicht verfügbare Termine")
        self.fest = _liste("Fest vorgegebene Teilnahme")
        termin_seite = QWidget()
        t = QHBoxLayout(termin_seite)
        for titel, liste in (("Nicht verfügbar", self.gesperrt), ("Teilnahme fest vorgeben", self.fest)):
            spalte = QVBoxLayout()
            spalte.addWidget(QLabel(titel))
            spalte.addWidget(liste)
            t.addLayout(spalte)
        self._aktualisiere_termine()

        self.reiter = QTabWidget()
        self.reiter.addTab(konferenzen, "Konferenzen")
        self.reiter.addTab(vorsitz, "Vorsitz")
        self.reiter.addTab(termin_seite, "Termine")
        self.fehler = QLabel("")
        self.fehler.setWordWrap(True)
        tasten = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        tasten.button(QDialogButtonBox.StandardButton.Ok).setProperty("primaer", True)
        tasten.accepted.connect(self.accept)
        tasten.rejected.connect(self.reject)
        wurzel = QVBoxLayout(self)
        wurzel.addWidget(QLabel(f"Aktuell wirksam: {' › '.join(ansicht.konferenzen) or 'keine Konferenz'}"))
        wurzel.addWidget(self.reiter, 1)
        wurzel.addWidget(self.fehler)
        wurzel.addWidget(tasten)
        self.resize(720, 460)

    # ── Konferenzliste bearbeiten ────────────────────────────────────────────
    def _aktualisiere_termine(self) -> None:
        """Baut die Terminlisten für die aktuell zugeordneten Konferenzen auf; Häkchen bleiben erhalten."""
        gesperrt = _gehakt(self.gesperrt) if self.gesperrt.count() else self._gesperrt0
        fest = _gehakt(self.fest) if self.fest.count() else self._fest0
        zugeordnet = set(self.konferenzen())
        termine = [
            (self.sitzung.termin_text(k.name, j), (k.name, j))
            for k in self.sitzung.ausgewaehlte_themen()
            if k.name in zugeordnet
            for j in range(len(k.festtermine))
        ]
        for liste, gehakt in ((self.gesperrt, gesperrt), (self.fest, fest)):
            liste.clear()
            for text, daten in termine:
                e = QListWidgetItem(text)
                e.setData(Qt.ItemDataRole.UserRole, daten)
                e.setFlags(e.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                e.setCheckState(Qt.CheckState.Checked if daten in gehakt else Qt.CheckState.Unchecked)
                liste.addItem(e)

    def konferenzen(self) -> list[str]:
        return [self.zugeordnet.item(i).text() for i in range(self.zugeordnet.count())]

    def _hinzufuegen(self) -> None:
        for e in self.verfuegbar.selectedItems():
            self.zugeordnet.addItem(self.verfuegbar.takeItem(self.verfuegbar.row(e)))
        self._aktualisiere_termine()

    def _entfernen(self) -> None:
        for e in self.zugeordnet.selectedItems():
            self.verfuegbar.addItem(self.zugeordnet.takeItem(self.zugeordnet.row(e)))
        self._aktualisiere_termine()

    def _verschiebe(self, richtung: int) -> None:
        zeile = self.zugeordnet.currentRow()
        ziel = zeile + richtung
        if zeile < 0 or not 0 <= ziel < self.zugeordnet.count():
            return
        e = self.zugeordnet.takeItem(zeile)
        self.zugeordnet.insertItem(ziel, e)
        self.zugeordnet.setCurrentRow(ziel)

    # ── Übernehmen ───────────────────────────────────────────────────────────
    def uebernehmen(self) -> bool:
        """Wendet alle Eingaben an. Bei einem Fehler bleibt der Dialog offen und nennt ihn."""
        s = self.sitzung
        try:
            s.setze_konferenzen([self.name], self.konferenzen())
            chair = _gehakt(self.vorsitz)
            for konferenz, bisher in self._chair.items():
                if konferenz in chair and bisher != self.name:
                    s.setze_vorsitz(konferenz, self.name)
                elif konferenz not in chair and bisher == self.name:
                    s.setze_vorsitz(konferenz, None)
            s.setze_nicht_verfuegbar(self.name, _gehakt(self.gesperrt))
            s.setze_fest(self.name, _gehakt(self.fest))
        except ModellFehler as e:
            self.fehler.setText(str(e))
            return False
        return True

    def accept(self) -> None:
        if self.uebernehmen():
            super().accept()


class SammelDialog(QDialog):
    """Konferenzen für mehrere Lehrkräfte gleichzeitig hinzufügen, entfernen oder ersetzen."""

    AKTIONEN = (("Hinzufügen", "hinzufuegen"), ("Entfernen", "entfernen"), ("Ersetzen durch", "ersetzen"))

    def __init__(self, sitzung: Sitzung, namen: list[str], eltern: QWidget | None = None) -> None:
        super().__init__(eltern)
        self.sitzung, self.namen = sitzung, namen
        self.setWindowTitle(f"Sammeländerung für {len(namen)} Lehrkräfte")
        self.aktion = QComboBox()
        self.aktion.setAccessibleName("Aktion")
        for text, wert in self.AKTIONEN:
            self.aktion.addItem(text, wert)
        self.konferenzen = _liste("Konferenzen", mehrfach=True)
        self.konferenzen.addItems([k.name for k in sitzung.konferenzen()])
        self.position = QSpinBox()
        self.position.setAccessibleName("Position")
        self.position.setRange(0, 20)
        self.position.setSpecialValueText("am Ende")
        self.fehler = QLabel("")
        self.fehler.setWordWrap(True)
        tasten = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        tasten.button(QDialogButtonBox.StandardButton.Ok).setProperty("primaer", True)
        tasten.accepted.connect(self.accept)
        tasten.rejected.connect(self.reject)
        zeile = QHBoxLayout()
        zeile.addWidget(self.aktion)
        zeile.addWidget(QLabel("Position:"))
        zeile.addWidget(self.position)
        zeile.addStretch(1)
        wurzel = QVBoxLayout(self)
        wurzel.addWidget(QLabel(f"Betrifft: {', '.join(namen[:6])}{' …' if len(namen) > 6 else ''}"))
        wurzel.addLayout(zeile)
        wurzel.addWidget(self.konferenzen, 1)
        wurzel.addWidget(self.fehler)
        wurzel.addWidget(tasten)
        self.resize(520, 440)

    def uebernehmen(self) -> bool:
        gewaehlt = [e.text() for e in self.konferenzen.selectedItems()]
        if not gewaehlt:
            self.fehler.setText("Bitte mindestens eine Konferenz auswählen")
            return False
        try:
            self.sitzung.aendere_konferenzen(
                self.namen, self.aktion.currentData(), gewaehlt, self.position.value() or None
            )
        except ModellFehler as e:
            self.fehler.setText(str(e))
            return False
        return True

    def accept(self) -> None:
        if self.uebernehmen():
            super().accept()
