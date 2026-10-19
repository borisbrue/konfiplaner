"""Führt die Planung in einem Hintergrund-Thread aus (SPEC-0005 FR-04)."""

from __future__ import annotations

import threading

from PySide6.QtCore import QObject, QThread, Signal, Slot

from konfiplaner.anwendung import Sitzung
from konfiplaner.modell import ModellFehler
from konfiplaner.planer import Fortschritt
from konfiplaner.restriktionen import KonfigurationsFehler


class PlanungsArbeiter(QObject):
    fortschritt = Signal(float, float)  # Zielwert, Sekunden
    fertig = Signal(object)  # Plan
    fehler = Signal(str)

    def __init__(self, sitzung: Sitzung) -> None:
        super().__init__()
        self._sitzung = sitzung
        self.abbruch = threading.Event()

    @Slot()
    def lauf(self) -> None:
        try:
            plan = self._sitzung.planen(self._melde, self.abbruch)
        except (ModellFehler, KonfigurationsFehler) as e:
            self.fehler.emit(str(e))
        except (ValueError, RuntimeError, OSError) as e:  # der Thread darf nicht still sterben
            self.fehler.emit(f"Unerwarteter Fehler bei der Planung: {e}")
        else:
            self.fertig.emit(plan)

    def _melde(self, f: Fortschritt) -> None:
        self.fortschritt.emit(f.zielwert, f.sekunden)


class PlanungsLauf:
    """Besitzt Thread und Arbeiter eines Laufs und räumt danach auf."""

    def __init__(self, sitzung: Sitzung) -> None:
        self.thread = QThread()
        self.arbeiter = PlanungsArbeiter(sitzung)
        self.arbeiter.moveToThread(self.thread)
        self.thread.started.connect(self.arbeiter.lauf)
        self.arbeiter.fertig.connect(self.thread.quit)
        self.arbeiter.fehler.connect(self.thread.quit)

    def start(self) -> None:
        self.thread.start()

    def abbrechen(self) -> None:
        self.arbeiter.abbruch.set()

    def warte(self, ms: int = 5000) -> bool:
        return self.thread.wait(ms)
