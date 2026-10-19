"""Solver-unabhängige Schnittstelle, über die Restriktionen Bedingungen formulieren."""

from __future__ import annotations

from typing import Protocol

from konfiplaner.modell import Modell

Var = object
"""Undurchsichtiges Handle einer Entscheidungsvariable; nur der Solver-Adapter kennt den Typ."""

Term = tuple[int, Var]
"""(Koeffizient, Variable)."""


class Planungskontext(Protocol):
    """Was eine Restriktion vom Solver sehen darf (SPEC-0003 FR-07).

    Ein Thema hat 1..n *Terminkandidaten* (Index j). Ein Kandidat ist `aktiv`, wenn er
    stattfindet, und belegt dann genau einen Block aus aufeinanderfolgenden Slots.
    """

    modell: Modell

    def termine(self, thema: str) -> range:
        """Indizes der Terminkandidaten des Themas."""

    def aktiv(self, thema: str, j: int) -> Var: ...

    def teilnahme(self, person: str, thema: str, j: int) -> Var:
        """Person nimmt am Kandidaten teil (nur für Schwerpunktthemen der Person)."""

    def praesenz(self, person: str, thema: str, j: int, slot: int) -> Var:
        """Person ist im Slot im Kandidaten anwesend (Teilnahme und Slot belegt)."""

    def startterme(self, thema: str, j: int) -> list[tuple[int, Var]]:
        """(Slot-Index, Startvariable) für jeden möglichen Startslot des Kandidaten."""

    def bedingung(
        self, terme: list[Term], untergrenze: int | None, obergrenze: int | None, text: str
    ) -> None:
        """Fordert `untergrenze <= Σ koeff*var <= obergrenze`.

        Je nach Typ der Restriktion hart (muss gelten) oder weich (Verstoß kostet das Gewicht).
        """

    def strafe(self, terme: list[Term], text: str) -> None:
        """Fügt `Σ koeff*var * gewicht` zur Zielfunktion hinzu (nur weiche Restriktionen)."""
