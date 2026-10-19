"""Gemeinsame Testdaten und Beispiel-Restriktionen."""

from __future__ import annotations

import random
from datetime import time
from typing import Any, ClassVar

from konfiplaner.modell import Modell, Person, Thema, Zeitslot
from konfiplaner.restriktionen import STANDARD_REGISTRY, Konfiguration, Restriktion, standard_konfiguration
from konfiplaner.restriktionen.basis import RegelEinstellung


def slots(n: int, tag: str = "Mo", laenge: int = 45, beginn_min: int = 8 * 60) -> list[Zeitslot]:
    def z(minuten: int) -> time:
        return time(minuten // 60, minuten % 60)

    pro_tag = 16
    return [
        Zeitslot(
            tag if i < pro_tag else f"{tag}{i // pro_tag}",
            z(beginn_min + (i % pro_tag) * laenge),
            z(beginn_min + (i % pro_tag + 1) * laenge),
        )
        for i in range(n)
    ]


def modell(
    themen: list[Thema],
    personen: list[tuple[str, str, str]],
    n_slots: int = 6,
    verfuegbar: dict[str, set[int]] | None = None,
) -> Modell:
    return Modell(themen, [Person(n, (a, b)) for n, a, b in personen], slots(n_slots), verfuegbar or {})


def mit_regeln(*zusaetze: RegelEinstellung, **typ_aenderungen: tuple[str, float]) -> Konfiguration:
    """Standardkonfiguration plus zusätzliche Einstellungen und geänderte Typen {name: (typ, gewicht)}."""
    k = standard_konfiguration()
    for name, (typ, gewicht) in typ_aenderungen.items():
        k.einstellungen[name] = RegelEinstellung(name, typ, gewicht)
    for z in zusaetze:
        k.einstellungen[z.name] = z
    return k


class NichtZusammen(Restriktion):
    name = "nicht_zusammen"
    parameter: ClassVar[dict[str, tuple[type, bool]]] = {"person_a": (str, True), "person_b": (str, True)}

    def anwenden(self, ctx: Any, werte: dict[str, Any]) -> None:
        a, b = werte["person_a"], werte["person_b"]
        gemeinsam = set(next(p for p in ctx.modell.personen if p.name == a).themen) & set(
            next(p for p in ctx.modell.personen if p.name == b).themen
        )
        for t in gemeinsam:
            for j in ctx.termine(t):
                ctx.bedingung(
                    [(1, ctx.teilnahme(a, t, j)), (1, ctx.teilnahme(b, t, j))],
                    None,
                    1,
                    f"{a} und {b} sitzen gemeinsam im Thema {t}",
                )


class Zusammen(Restriktion):
    name = "zusammen"
    parameter: ClassVar[dict[str, tuple[type, bool]]] = {"person_a": (str, True), "person_b": (str, True)}

    def anwenden(self, ctx: Any, werte: dict[str, Any]) -> None:
        a, b = werte["person_a"], werte["person_b"]
        gemeinsam = set(next(p for p in ctx.modell.personen if p.name == a).themen) & set(
            next(p for p in ctx.modell.personen if p.name == b).themen
        )
        for t in gemeinsam:
            for j in ctx.termine(t):
                ctx.bedingung(
                    [(1, ctx.teilnahme(a, t, j)), (-1, ctx.teilnahme(b, t, j))],
                    0,
                    0,
                    f"{a} und {b} sind nicht gemeinsam im Thema {t}",
                )


def registry_mit_plugins():
    r = STANDARD_REGISTRY.kopie()
    r.registriere(NichtZusammen)
    r.registriere(Zusammen)
    return r


def zufallsmodell(personen: int, themen: int, n_slots: int, seed: int = 7, mindest: int = 3) -> Modell:
    rnd = random.Random(seed)
    th = [
        Thema(f"T{i}", wichtigkeit=rnd.randint(1, 5), mindestanzahl=mindest, dauer_min=rnd.choice([45, 90]))
        for i in range(themen)
    ]
    pe = []
    for i in range(personen):
        a, b = rnd.sample([t.name for t in th], 2)
        pe.append((f"P{i}", a, b))
    return modell(th, pe, n_slots)
