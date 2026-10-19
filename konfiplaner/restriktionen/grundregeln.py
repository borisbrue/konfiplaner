"""Mitgelieferte Grundregeln (SPEC-0003 FR-04). Alle sind über die Konfiguration anpassbar."""

from __future__ import annotations

from typing import Any

from konfiplaner.restriktionen.basis import Registry, Restriktion
from konfiplaner.restriktionen.kontext import Planungskontext

STANDARD_REGISTRY = Registry()


def restriktion(klasse):
    """Dekorator: registriert eine Restriktion in der Standard-Registry."""
    return STANDARD_REGISTRY.registriere(klasse)


@restriktion
class Themenabdeckung(Restriktion):
    name = "themenabdeckung"

    def anwenden(self, ctx: Planungskontext, werte: dict[str, Any]) -> None:
        for t in ctx.modell.themen:
            ctx.bedingung(
                [(1, ctx.aktiv(t.name, j)) for j in ctx.termine(t.name)],
                1,
                None,
                f"Thema {t.name} findet nicht statt",
            )


@restriktion
class Mindestanzahl(Restriktion):
    name = "mindestanzahl"

    def anwenden(self, ctx: Planungskontext, werte: dict[str, Any]) -> None:
        for t in ctx.modell.themen:
            for j in ctx.termine(t.name):
                terme = [(1, ctx.teilnahme(p.name, t.name, j)) for p in ctx.modell.personen_zu(t.name)]
                terme.append((-t.mindestanzahl, ctx.aktiv(t.name, j)))
                ctx.bedingung(
                    terme, 0, None, f"Thema {t.name}: Mindestanzahl {t.mindestanzahl} nicht erreicht"
                )


@restriktion
class Schwerpunkte(Restriktion):
    name = "schwerpunkte"

    def anwenden(self, ctx: Planungskontext, werte: dict[str, Any]) -> None:
        for p in ctx.modell.personen:
            for t in p.themen:
                ctx.bedingung(
                    [(1, ctx.teilnahme(p.name, t, j)) for j in ctx.termine(t)],
                    1,
                    1,
                    f"{p.name} nimmt nicht an Schwerpunkt {t} teil",
                )


@restriktion
class KeineUeberschneidung(Restriktion):
    name = "keine_ueberschneidung"

    def anwenden(self, ctx: Planungskontext, werte: dict[str, Any]) -> None:
        for p in ctx.modell.personen:
            for s in range(len(ctx.modell.zeitslots)):
                terme = [(1, ctx.praesenz(p.name, t, j, s)) for t in p.themen for j in ctx.termine(t)]
                ctx.bedingung(terme, None, 1, f"{p.name} hat im Slot {s} zwei Termine gleichzeitig")


@restriktion
class Verfuegbarkeit(Restriktion):
    name = "verfuegbarkeit"

    def anwenden(self, ctx: Planungskontext, werte: dict[str, Any]) -> None:
        modell = ctx.modell
        for p in modell.personen:
            if p.name not in modell.verfuegbarkeit:
                continue
            for s in range(len(modell.zeitslots)):
                if modell.verfuegbar(p.name, s):
                    continue
                terme = [(1, ctx.praesenz(p.name, t, j, s)) for t in p.themen for j in ctx.termine(t)]
                ctx.bedingung(terme, None, 0, f"{p.name} ist im Slot {s} nicht verfügbar")


@restriktion
class Wichtigkeit(Restriktion):
    """Wichtige Themen bekommen früher liegende Slots (Strafe = Wichtigkeit × Slot-Index)."""

    name = "wichtigkeit"
    standard_typ = "weich"
    erlaubte_typen = ("weich", "aus")

    def anwenden(self, ctx: Planungskontext, werte: dict[str, Any]) -> None:
        for t in ctx.modell.themen:
            for j in ctx.termine(t.name):
                terme = [(t.wichtigkeit * slot, var) for slot, var in ctx.startterme(t.name, j) if slot]
                if terme:
                    ctx.strafe(terme, f"Thema {t.name} liegt nicht im besten Slot")


GRUNDREGELN = (
    "themenabdeckung",
    "mindestanzahl",
    "schwerpunkte",
    "keine_ueberschneidung",
    "verfuegbarkeit",
    "wichtigkeit",
)
