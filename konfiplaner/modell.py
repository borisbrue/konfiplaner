"""Domänenmodell: Eingabe (Thema, Person, Zeitslot, Modell) und Ergebnis (Plan)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time
from typing import Literal


class ModellFehler(ValueError):
    """Ungültige Modelldaten."""


@dataclass(frozen=True)
class Thema:
    name: str
    wichtigkeit: int = 3
    mindestanzahl: int = 1
    dauer_min: int = 45
    vorsitz: str | None = None  # Name einer Person; muss in jedem Termin des Themas sein

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ModellFehler("Thema ohne Namen")
        if not 1 <= self.wichtigkeit <= 5:
            raise ModellFehler(f"Thema {self.name}: Wichtigkeit muss 1 bis 5 sein")
        if self.mindestanzahl < 1:
            raise ModellFehler(f"Thema {self.name}: Mindestanzahl muss mindestens 1 sein")
        if self.dauer_min < 1:
            raise ModellFehler(f"Thema {self.name}: Dauer muss mindestens 1 Minute sein")


@dataclass(frozen=True)
class Person:
    name: str
    themen: tuple[str, ...]  # 0 bis n verschiedene Schwerpunktthemen in Rangfolge (SPEC-0007 FR-12)

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ModellFehler("Person ohne Namen")
        if len(set(self.themen)) != len(self.themen):
            raise ModellFehler(f"Person {self.name}: Schwerpunktthemen müssen verschieden sein")


@dataclass(frozen=True)
class Zeitslot:
    tag: str
    start: time
    ende: time

    def __post_init__(self) -> None:
        if self.ende <= self.start:
            raise ModellFehler(f"Zeitslot {self.tag}: Ende liegt nicht nach dem Start")

    @property
    def dauer_min(self) -> int:
        d = date(2000, 1, 1)
        return int((datetime.combine(d, self.ende) - datetime.combine(d, self.start)).total_seconds() // 60)


@dataclass
class Modell:
    """Eingabe der Planung. `verfuegbarkeit` ordnet Personen erlaubte Slot-Indizes zu;
    Personen ohne Eintrag sind jederzeit verfügbar."""

    themen: list[Thema]
    personen: list[Person]
    zeitslots: list[Zeitslot]
    verfuegbarkeit: dict[str, set[int]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        namen = [t.name for t in self.themen]
        if len(set(namen)) != len(namen):
            raise ModellFehler("Themennamen müssen eindeutig sein")
        personen = [p.name for p in self.personen]
        if len(set(personen)) != len(personen):
            raise ModellFehler("Personennamen müssen eindeutig sein")
        for p in self.personen:
            for t in p.themen:
                if t not in namen:
                    raise ModellFehler(f"Person {p.name}: unbekanntes Thema {t}")
        for t in self.themen:
            if t.vorsitz is not None and t.vorsitz not in personen:
                raise ModellFehler(f"Thema {t.name}: unbekannter Vorsitz {t.vorsitz}")
        for name, slots in self.verfuegbarkeit.items():
            if name not in personen:
                raise ModellFehler(f"Verfügbarkeit für unbekannte Person {name}")
            if any(not 0 <= s < len(self.zeitslots) for s in slots):
                raise ModellFehler(f"Verfügbarkeit von {name}: unbekannter Slot")

    def thema(self, name: str) -> Thema:
        return next(t for t in self.themen if t.name == name)

    def personen_zu(self, thema: str) -> list[Person]:
        """Personen, die an Terminen des Themas teilnehmen können: Schwerpunkt oder Vorsitz."""
        vorsitz = self.thema(thema).vorsitz
        return [p for p in self.personen if thema in p.themen or p.name == vorsitz]

    def themen_von(self, person: str) -> list[str]:
        """Themen, in denen die Person Termine hat: Schwerpunkte und Themen mit ihr als Vorsitz."""
        p = next(x for x in self.personen if x.name == person)
        return [t.name for t in self.themen if t.name in p.themen or t.vorsitz == person]

    def verfuegbar(self, person: str, slot: int) -> bool:
        erlaubt = self.verfuegbarkeit.get(person)
        return erlaubt is None or slot in erlaubt

    def bloecke_fehlen(self) -> list[str]:
        """Themen, deren Dauer in keinen zusammenhängenden Zeitblock passt."""
        return [t.name for t in self.themen if not self.bloecke(t.name)]

    def _zusammenhaengend(self, i: int) -> bool:
        a, b = self.zeitslots[i - 1], self.zeitslots[i]
        return a.tag == b.tag and a.ende == b.start

    def bloecke(self, thema: str) -> dict[int, int]:
        """Mögliche Startslots eines Themas -> Anzahl benötigter aufeinanderfolgender Slots.

        Die Dauer wird auf ganze Slots aufgerundet.
        """
        ziel = self.thema(thema).dauer_min
        ergebnis: dict[int, int] = {}
        n = len(self.zeitslots)
        for start in range(n):
            summe, i = 0, start
            while i < n and (i == start or self._zusammenhaengend(i)):
                summe += self.zeitslots[i].dauer_min
                if summe >= ziel:
                    ergebnis[start] = i - start + 1
                    break
                i += 1
        return ergebnis


Status = Literal["optimal", "machbar", "kein_plan"]


@dataclass(frozen=True)
class Termin:
    thema: str
    start_slot: int
    anzahl_slots: int
    teilnehmer: tuple[str, ...]


@dataclass(frozen=True)
class Verstoss:
    restriktion: str
    text: str


@dataclass
class Plan:
    status: Status
    termine: list[Termin] = field(default_factory=list)
    verstoesse: list[Verstoss] = field(default_factory=list)
    begruendung: list[str] = field(default_factory=list)
    warnungen: list[str] = field(default_factory=list)
    seed: int | None = None

    def to_dict(self) -> dict:
        d: dict = {
            "status": self.status,
            "termine": [
                {
                    "thema": t.thema,
                    "start_slot": t.start_slot,
                    "anzahl_slots": t.anzahl_slots,
                    "teilnehmer": list(t.teilnehmer),
                }
                for t in self.termine
            ],
        }
        if self.seed is not None:
            d["seed"] = self.seed
        if self.begruendung:
            d["begruendung"] = list(self.begruendung)
        if self.verstoesse:
            d["verstoesse"] = [{"restriktion": v.restriktion, "text": v.text} for v in self.verstoesse]
        if self.warnungen:
            d["warnungen"] = list(self.warnungen)
        return d
