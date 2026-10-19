"""Startpunkt der Desktop-Anwendung (`uv run konfiplaner`)."""

from __future__ import annotations

import logging
import sys

from PySide6.QtWidgets import QApplication

from konfiplaner.anwendung import Sitzung
from konfiplaner.einstellungen import YamlEinstellungen
from konfiplaner.gui.hauptfenster import Hauptfenster
from konfiplaner.restriktionen import STANDARD_REGISTRY, RegistrierungsFehler

log = logging.getLogger(__name__)


def main() -> int:
    logging.basicConfig(level=logging.INFO)
    app = QApplication(sys.argv)
    app.setApplicationName("KonfiPlaner")
    try:
        STANDARD_REGISTRY.lade_entry_points()
    except RegistrierungsFehler:
        log.warning("Plugin-Restriktionen konnten nicht geladen werden", exc_info=True)
    fenster = Hauptfenster(Sitzung(YamlEinstellungen()))
    fenster.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
