"""Solver-unabhängige Planer-Schnittstelle (SPEC-0002 FR-11/FR-12)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
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
class Fixierungen:
    """Harte Vorgaben an den Solver (SPEC-0010 FR-06).

    `teilnahmen`: Person -> {(Thema, Startslot): True = nimmt teil, False = nimmt nicht teil}.
    `termine`: Thema -> Startslots, die genau so stattfinden (aufsteigend); weitere Termine entfallen.
    """

    teilnahmen: dict[str, dict[tuple[str, int], bool]] = field(default_factory=dict)
    termine: dict[str, tuple[int, ...]] = field(default_factory=dict)

    def leer(self) -> bool:
        return not self.teilnahmen and not self.termine


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
        fixierungen: Fixierungen | None = None,
    ) -> Plan: ...
