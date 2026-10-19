"""Restriktions-Schnittstelle, Registry und Konfiguration (SPEC-0003)."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from importlib import metadata
from pathlib import Path
from typing import Any, ClassVar

import yaml
from jsonschema import Draft202012Validator

from konfiplaner.modell import Plan, Verstoss
from konfiplaner.restriktionen.kontext import Planungskontext

TYPEN = ("hart", "weich", "aus")
ENTRY_POINT_GRUPPE = "konfiplaner.restriktionen"
SCHEMA_PFAD = Path(__file__).resolve().parents[2] / ".sdd/contracts/data/regel-konfiguration.schema.json"


class RegistrierungsFehler(ValueError):
    """Restriktion kann nicht registriert werden (z. B. doppelter Name)."""


class KonfigurationsFehler(ValueError):
    """Ungültige Regel-Konfiguration; `regel` nennt die betroffene Restriktion."""

    def __init__(self, meldung: str, regel: str | None = None) -> None:
        super().__init__(meldung)
        self.regel = regel


class Restriktion:
    """Basisklasse einer Planungsregel.

    Unterklassen setzen `name` (eindeutig), `standard_typ` und optional `parameter`
    (Name -> (Typ, Pflicht)) und implementieren `anwenden`.
    """

    name: ClassVar[str]
    standard_typ: ClassVar[str] = "hart"
    erlaubte_typen: ClassVar[tuple[str, ...]] = TYPEN
    parameter: ClassVar[dict[str, tuple[type, bool]]] = {}
    beschreibung: ClassVar[str] = ""

    def pruefe_parameter(self, werte: dict[str, Any]) -> None:
        for pname, (ptyp, pflicht) in self.parameter.items():
            if pname not in werte:
                if pflicht:
                    raise KonfigurationsFehler(f"Restriktion {self.name}: Parameter {pname} fehlt", self.name)
                continue
            if not isinstance(werte[pname], ptyp):
                raise KonfigurationsFehler(
                    f"Restriktion {self.name}: Parameter {pname} muss {ptyp.__name__} sein", self.name
                )
        for pname in werte:
            if pname not in self.parameter:
                raise KonfigurationsFehler(
                    f"Restriktion {self.name}: unbekannter Parameter {pname}", self.name
                )

    def anwenden(self, ctx: Planungskontext, werte: dict[str, Any]) -> None:
        raise NotImplementedError

    def erklaere(self, plan: Plan, werte: dict[str, Any]) -> list[Verstoss]:
        """Optional: Verstöße im fertigen Plan in Klartext (Standard: keine zusätzlichen)."""
        return []


class Registry:
    """Verzeichnis aller Restriktionen nach Namen."""

    def __init__(self) -> None:
        self._regeln: dict[str, type[Restriktion]] = {}

    def registriere(self, klasse: type[Restriktion]) -> type[Restriktion]:
        """Registriert eine Klasse; auch als Dekorator nutzbar."""
        name = getattr(klasse, "name", None)
        if not name:
            raise RegistrierungsFehler(f"{klasse.__name__} hat keinen Namen")
        if name in self._regeln:
            raise RegistrierungsFehler(f"Restriktion {name} ist bereits registriert")
        if klasse.standard_typ not in klasse.erlaubte_typen:
            raise RegistrierungsFehler(f"Restriktion {name}: Standardtyp nicht erlaubt")
        self._regeln[name] = klasse
        return klasse

    def lade_entry_points(self, gruppe: str = ENTRY_POINT_GRUPPE) -> None:
        for ep in metadata.entry_points(group=gruppe):
            self.registriere(ep.load())

    def kopie(self) -> Registry:
        """Unabhängige Kopie, z. B. um Plugins ohne Wirkung auf die Standard-Registry zu ergänzen."""
        neu = Registry()
        neu._regeln = dict(self._regeln)
        return neu

    def hole(self, name: str) -> type[Restriktion]:
        try:
            return self._regeln[name]
        except KeyError:
            raise KonfigurationsFehler(f"Unbekannte Restriktion {name}", name) from None

    def namen(self) -> list[str]:
        return list(self._regeln)

    def __contains__(self, name: str) -> bool:
        return name in self._regeln


@dataclass(frozen=True)
class RegelEinstellung:
    name: str
    typ: str
    gewicht: float = 1.0
    parameter: dict[str, Any] = field(default_factory=dict)


@dataclass
class Konfiguration:
    """Aktivierung, Typ, Gewicht und Parameter je Restriktion."""

    einstellungen: dict[str, RegelEinstellung]

    @classmethod
    def standard(cls, registry: Registry, grundregeln: Iterable[str]) -> Konfiguration:
        return cls({n: RegelEinstellung(n, registry.hole(n).standard_typ) for n in grundregeln})

    @classmethod
    def aus_dict(
        cls, daten: dict[str, Any], registry: Registry, basis: Konfiguration | None = None
    ) -> Konfiguration:
        """Prüft `daten` (Schema CON-0007 plus Registry) und legt sie über `basis`."""
        schema = _lade_schema()
        fehler = sorted(Draft202012Validator(schema).iter_errors(daten), key=lambda e: list(e.path))
        if fehler:
            pfad = "/".join(str(p) for p in fehler[0].path) or "(Wurzel)"
            raise KonfigurationsFehler(f"Ungültige Konfiguration bei {pfad}: {fehler[0].message}")
        ergebnis = dict(basis.einstellungen) if basis else {}
        for name, eintrag in daten["restriktionen"].items():
            klasse = registry.hole(name)
            typ = eintrag["typ"]
            if typ not in klasse.erlaubte_typen:
                raise KonfigurationsFehler(f"Restriktion {name}: Typ {typ} nicht erlaubt", name)
            werte = dict(eintrag.get("parameter", {}))
            klasse().pruefe_parameter(werte)
            ergebnis[name] = RegelEinstellung(name, typ, float(eintrag.get("gewicht", 1.0)), werte)
        return cls(ergebnis)

    @classmethod
    def aus_yaml(cls, pfad: Path, registry: Registry, basis: Konfiguration | None = None) -> Konfiguration:
        return cls.aus_dict(yaml.safe_load(Path(pfad).read_text(encoding="utf-8")), registry, basis)

    def aktive(self) -> list[RegelEinstellung]:
        return [e for e in self.einstellungen.values() if e.typ != "aus"]


def _lade_schema() -> dict:
    import json

    return json.loads(SCHEMA_PFAD.read_text(encoding="utf-8"))
