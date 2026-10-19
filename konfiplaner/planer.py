"""Solver-unabhängige Planer-Schnittstelle (SPEC-0002 FR-11/FR-12)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from konfiplaner.modell import Modell, Plan
from konfiplaner.restriktionen import Konfiguration


@dataclass(frozen=True)
class PlanerOptionen:
    zeitlimit_s: float = 60.0
    seed: int = 1
    # 0 = Solver wählt. Reproduzierbare Pläne gibt es nur mit 1 Worker (SPEC-0002 NFR).
    arbeiter: int = 0


@dataclass(frozen=True)
class Fortschritt:
    """Zwischenstand während der Suche (niedriger ist besser)."""

    zielwert: float
    sekunden: float


class Abbruchsignal(Protocol):
    """Kompatibel zu `threading.Event`."""

    def is_set(self) -> bool: ...


class Planer(Protocol):
    def planen(
        self,
        modell: Modell,
        konfiguration: Konfiguration,
        optionen: PlanerOptionen | None = None,
        fortschritt: Callable[[Fortschritt], None] | None = None,
        abbruch: Abbruchsignal | None = None,
    ) -> Plan: ...
