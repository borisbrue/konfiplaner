"""Startpunkt der Desktop-Anwendung (`uv run konfiplaner`)."""

from __future__ import annotations

import faulthandler
import logging
import sys

from PySide6.QtWidgets import QApplication

from konfiplaner.anwendung import Sitzung
from konfiplaner.einstellungen import YamlEinstellungen, standard_pfad
from konfiplaner.gui.design import installiere
from konfiplaner.gui.hauptfenster import Hauptfenster
from konfiplaner.restriktionen import STANDARD_REGISTRY, RegistrierungsFehler

log = logging.getLogger(__name__)


def _absturzprotokoll() -> None:
    """Schreibt bei einem Absturz den Python-Stack neben die Einstellungen (hilft bei der Fehlersuche)."""
    try:
        pfad = standard_pfad().with_name("absturz.log")
        pfad.parent.mkdir(parents=True, exist_ok=True)
        faulthandler.enable(open(pfad, "a"))  # noqa: SIM115 – muss für die Laufzeit offen bleiben
    except OSError:
        log.warning("Absturzprotokoll nicht verfügbar", exc_info=True)


def main() -> int:
    logging.basicConfig(level=logging.INFO)
    _absturzprotokoll()
    app = QApplication(sys.argv)
    app.setApplicationName("KonfiPlaner")
    installiere(app)  # dunkles Design (SPEC-0011)
    try:
        STANDARD_REGISTRY.lade_entry_points()
    except RegistrierungsFehler:
        log.warning("Plugin-Restriktionen konnten nicht geladen werden", exc_info=True)
    fenster = Hauptfenster(Sitzung(YamlEinstellungen()))
    fenster.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
