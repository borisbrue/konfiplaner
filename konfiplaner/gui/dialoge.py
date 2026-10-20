"""Dialoge hinter einer kleinen Schnittstelle, damit Abläufe ohne Benutzereingabe testbar sind."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QFileDialog, QMessageBox, QWidget


class Dialoge:
    """Standardimplementierung mit echten Qt-Dialogen."""

    def __init__(self, eltern: QWidget | None = None) -> None:
        self.eltern = eltern

    def datei_oeffnen(self, start: Path | None) -> Path | None:
        pfad, _ = QFileDialog.getOpenFileName(
            self.eltern, "Excel-Datei öffnen", str(start or Path.home()), "Excel-Dateien (*.xlsx)"
        )
        return Path(pfad) if pfad else None

    def regeldatei_oeffnen(self, start: Path | None) -> Path | None:
        pfad, _ = QFileDialog.getOpenFileName(
            self.eltern, "Regelkonfiguration laden", str(start or Path.home()), "YAML (*.yaml *.yml)"
        )
        return Path(pfad) if pfad else None

    def export_ziel(self, start: Path | None) -> Path | None:
        vorschlag = str((start or Path.home()) / "Terminplan.xlsx")
        pfad, _ = QFileDialog.getSaveFileName(
            self.eltern,
            "Terminplan exportieren",
            vorschlag,
            "Excel-Dateien (*.xlsx)",
            options=QFileDialog.Option.DontConfirmOverwrite,
        )
        if not pfad:
            return None
        return Path(pfad if pfad.lower().endswith(".xlsx") else pfad + ".xlsx")

    def einladung_ziel(self, start: Path | None) -> Path | None:
        vorschlag = str((start or Path.home()) / "Einladung.docx")
        pfad, _ = QFileDialog.getSaveFileName(
            self.eltern,
            "Einladung exportieren",
            vorschlag,
            "Word-Dokumente (*.docx)",
            options=QFileDialog.Option.DontConfirmOverwrite,
        )
        if not pfad:
            return None
        return Path(pfad if pfad.lower().endswith(".docx") else pfad + ".docx")

    def logo_oeffnen(self, start: Path | None) -> Path | None:
        pfad, _ = QFileDialog.getOpenFileName(
            self.eltern, "Logo wählen", str(start or Path.home()), "Bilder (*.png *.jpg *.jpeg)"
        )
        return Path(pfad) if pfad else None

    def url_oeffnen(self, url: str) -> None:
        QDesktopServices.openUrl(QUrl(url))

    def ja_nein(self, titel: str, text: str) -> bool:
        antwort = QMessageBox.question(self.eltern, titel, text)
        return antwort == QMessageBox.StandardButton.Yes

    def fehler(self, titel: str, text: str) -> None:
        QMessageBox.warning(self.eltern, titel, text)

    def info(self, titel: str, text: str) -> None:
        QMessageBox.information(self.eltern, titel, text)
