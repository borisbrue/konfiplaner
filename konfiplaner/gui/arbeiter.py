"""Führt die Planung in einem Hintergrund-Thread aus (SPEC-0005 FR-04)."""

from __future__ import annotations

import threading

from PySide6.QtCore import QObject, Qt, QThread, Signal, Slot

from konfiplaner.anwendung import Sitzung
from konfiplaner.modell import ModellFehler
from konfiplaner.planer import Fortschritt
from konfiplaner.restriktionen import KonfigurationsFehler
from konfiplaner.update import UpdateFehler, UpdateQuelle, suche_update


class PlanungsArbeiter(QObject):
    fortschritt = Signal(float, float)  # Zielwert, Sekunden
    fertig = Signal(object)  # Plan
    fehler = Signal(str)

    def __init__(self, sitzung: Sitzung, teil: bool = False) -> None:
        super().__init__()
        self._sitzung = sitzung
        self._teil = teil
        self.abbruch = threading.Event()

    @Slot()
    def lauf(self) -> None:
        try:
            planen = self._sitzung.teil_neu_planen if self._teil else self._sitzung.planen
            plan = planen(self._melde, self.abbruch)
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

    def __init__(self, sitzung: Sitzung, teil: bool = False) -> None:
        self.thread = QThread()
        self.arbeiter = PlanungsArbeiter(sitzung, teil)
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


class UpdateLauf(QObject):
    """Fragt die neueste Version im Hintergrund ab; ein Fehler meldet sich nur per Signal (SPEC-0015 FR-02)."""

    fertig = Signal(object)  # UpdateInfo | None
    fehler = Signal(str)

    def __init__(self, quelle: UpdateQuelle, eigene: str) -> None:
        super().__init__()
        self._quelle, self._eigene = quelle, eigene
        self.thread = QThread()
        self.moveToThread(self.thread)
        self.thread.started.connect(self._lauf)
        # direkt: QThread lebt im Hauptthread, der beim Schließen auf das Ende wartet (sonst Verklemmung)
        self.fertig.connect(self.thread.quit, Qt.ConnectionType.DirectConnection)
        self.fehler.connect(self.thread.quit, Qt.ConnectionType.DirectConnection)

    def start(self) -> None:
        self.thread.start()

    @Slot()
    def _lauf(self) -> None:
        try:
            self.fertig.emit(suche_update(self._quelle, self._eigene))
        except UpdateFehler as e:
            self.fehler.emit(str(e))
        except Exception as e:  # noqa: BLE001 – der Thread darf nie still sterben
            self.fehler.emit(f"Unerwarteter Fehler: {e}")

    def warte(self, ms: int = 6000) -> bool:
        return self.thread.wait(ms)
