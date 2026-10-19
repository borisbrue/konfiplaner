"""Manuelle Änderungen an der Zuordnung der Lehrkräfte (SPEC-0010): Zustand und Persistenz, ohne Qt."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

Termin = tuple[str, int]  # (Konferenz, Index in `Thema.festtermine`)


def _termine(daten: Any) -> frozenset[Termin]:
    ergebnis = set()
    if isinstance(daten, list):
        for e in daten:
            if (
                isinstance(e, (list, tuple))
                and len(e) == 2
                and isinstance(e[0], str)
                and isinstance(e[1], int)
            ):
                ergebnis.add((e[0], e[1]))
    return frozenset(ergebnis)


@dataclass
class LehrerAenderung:
    """Abweichungen einer Lehrkraft von der Datei. `konferenzen=None` heißt: wie in der Datei."""

    konferenzen: tuple[str, ...] | None = None
    nicht_verfuegbar: frozenset[Termin] = frozenset()
    fest: frozenset[Termin] = frozenset()

    def leer(self) -> bool:
        return self.konferenzen is None and not self.nicht_verfuegbar and not self.fest

    def als_dict(self) -> dict[str, Any]:
        return {
            "konferenzen": list(self.konferenzen) if self.konferenzen is not None else None,
            "nicht_verfuegbar": sorted([k, j] for k, j in self.nicht_verfuegbar),
            "fest": sorted([k, j] for k, j in self.fest),
        }

    @classmethod
    def aus_dict(cls, daten: Any) -> LehrerAenderung:
        if not isinstance(daten, dict):
            return cls()
        konf = daten.get("konferenzen")
        ok = isinstance(konf, list) and all(isinstance(k, str) for k in konf)
        return cls(
            tuple(dict.fromkeys(konf)) if ok else None,
            _termine(daten.get("nicht_verfuegbar")),
            _termine(daten.get("fest")),
        )


@dataclass
class Zuordnung:
    """Alle manuellen Änderungen zu einer Datei."""

    datei: str | None = None
    personen: dict[str, LehrerAenderung] = field(default_factory=dict)
    vorsitz: dict[str, str | None] = field(default_factory=dict)  # Konferenz -> Person (None = keiner)
    markiert: set[str] = field(default_factory=set)

    def leer(self) -> bool:
        return not self.personen and not self.vorsitz and not self.markiert

    def aenderung(self, name: str) -> LehrerAenderung:
        return self.personen.setdefault(name, LehrerAenderung())

    def bereinige(self) -> None:
        for name in [n for n, a in self.personen.items() if a.leer()]:
            del self.personen[name]

    def als_dict(self) -> dict[str, Any]:
        return {
            "datei": self.datei,
            "personen": {n: a.als_dict() for n, a in self.personen.items() if not a.leer()},
            "vorsitz": {k: v for k, v in self.vorsitz.items()},
            "markiert": sorted(self.markiert),
        }

    @classmethod
    def aus_dict(cls, daten: Any) -> Zuordnung:
        z = cls()
        if not isinstance(daten, dict):
            return z
        z.datei = daten.get("datei") if isinstance(daten.get("datei"), str) else None
        if isinstance(daten.get("personen"), dict):
            for name, a in daten["personen"].items():
                aenderung = LehrerAenderung.aus_dict(a)
                if not aenderung.leer():
                    z.personen[str(name)] = aenderung
        if isinstance(daten.get("vorsitz"), dict):
            z.vorsitz = {str(k): (v if isinstance(v, str) else None) for k, v in daten["vorsitz"].items()}
        if isinstance(daten.get("markiert"), list):
            z.markiert = {str(n) for n in daten["markiert"]}
        return z
