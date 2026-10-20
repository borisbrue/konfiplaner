"""Mitgelieferte Grundregeln (SPEC-0003 FR-04). Alle sind über die Konfiguration anpassbar."""

from __future__ import annotations

from typing import Any

from konfiplaner.restriktionen.basis import Registry, Restriktion
from konfiplaner.restriktionen.kontext import Planungskontext

STANDARD_REGISTRY = Registry()
RANGFAKTOREN = (100, 10, 1)  # Konferenz I, II, III und weitere (SPEC-0008 FR-05)
AUSGLEICH_FAKTOR = 150  # je Person Abweichung von der Zielgröße; mehr als der Rang-Unterschied I/II (90)


def restriktion(klasse):
    """Dekorator: registriert eine Restriktion in der Standard-Registry."""
    return STANDARD_REGISTRY.registriere(klasse)


@restriktion
class Themenabdeckung(Restriktion):
    name = "themenabdeckung"
    beschreibung = "Jedes Thema findet mindestens einmal statt."

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
    beschreibung = "Jeder Termin erreicht die Mindestanzahl seines Themas."

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
    beschreibung = "Jede Person nimmt an je einem Termin ihrer beiden Schwerpunktthemen teil."

    def anwenden(self, ctx: Planungskontext, werte: dict[str, Any]) -> None:
        for p in ctx.modell.personen:
            for rang, t in enumerate(p.themen):
                # Rangfolge: entgangene Teilnahme an Konferenz I kostet mehr als an II, an II mehr als an III
                faktor = RANGFAKTOREN[min(rang, len(RANGFAKTOREN) - 1)]
                # Der Vorsitz ist in allen Terminen seines Themas; hier genügt mindestens einer
                obergrenze = None if ctx.modell.thema(t).vorsitz == p.name else 1
                ctx.bedingung(
                    [(1, ctx.teilnahme(p.name, t, j)) for j in ctx.termine(t)],
                    1,
                    obergrenze,
                    f"{p.name} nimmt nicht an Schwerpunkt {t} teil",
                    faktor,
                )


@restriktion
class KeineUeberschneidung(Restriktion):
    name = "keine_ueberschneidung"
    beschreibung = "Niemand hat zwei Termine gleichzeitig."

    def anwenden(self, ctx: Planungskontext, werte: dict[str, Any]) -> None:
        for p in ctx.modell.personen:
            for s in range(len(ctx.modell.zeitslots)):
                terme = [
                    (1, ctx.praesenz(p.name, t, j, s))
                    for t in ctx.modell.themen_von(p.name)
                    for j in ctx.termine(t)
                ]
                ctx.bedingung(terme, None, 1, f"{p.name} hat im Slot {s} zwei Termine gleichzeitig")


@restriktion
class Verfuegbarkeit(Restriktion):
    name = "verfuegbarkeit"
    beschreibung = "Personen nehmen nur in Slots teil, in denen sie verfügbar sind."

    def anwenden(self, ctx: Planungskontext, werte: dict[str, Any]) -> None:
        modell = ctx.modell
        for p in modell.personen:
            if p.name not in modell.verfuegbarkeit:
                continue
            for s in range(len(modell.zeitslots)):
                if modell.verfuegbar(p.name, s):
                    continue
                terme = [
                    (1, ctx.praesenz(p.name, t, j, s))
                    for t in ctx.modell.themen_von(p.name)
                    for j in ctx.termine(t)
                ]
                ctx.bedingung(terme, None, 0, f"{p.name} ist im Slot {s} nicht verfügbar")


@restriktion
class Vorsitz(Restriktion):
    name = "vorsitz"
    beschreibung = "Der Vorsitz eines Themas ist in jedem Termin dieses Themas."

    def anwenden(self, ctx: Planungskontext, werte: dict[str, Any]) -> None:
        for t in ctx.modell.themen:
            if t.vorsitz is None:
                continue
            for j in ctx.termine(t.name):
                # Teilnahme == aktiv: der Vorsitz ist genau dann dabei, wenn der Termin stattfindet
                ctx.bedingung(
                    [(1, ctx.teilnahme(t.vorsitz, t.name, j)), (-1, ctx.aktiv(t.name, j))],
                    0,
                    0,
                    f"Vorsitz {t.vorsitz} fehlt im Thema {t.name}",
                )


@restriktion
class Verteilung(Restriktion):
    """Jede Lehrkraft mit Konferenz nimmt an mindestens einer teil; der Rest verteilt sich (SPEC-0012)."""

    name = "verteilung"
    beschreibung = "Jede Lehrkraft nimmt an mindestens einer ihrer Konferenzen teil."
    standard_typ = "aus"

    def anwenden(self, ctx: Planungskontext, werte: dict[str, Any]) -> None:
        for p in ctx.modell.personen:
            konferenzen = ctx.modell.themen_von(p.name)
            if not konferenzen:
                continue
            terme = [(1, ctx.teilnahme(p.name, t, j)) for t in konferenzen for j in ctx.termine(t)]
            ctx.bedingung(terme, 1, None, f"{p.name} nimmt an keiner ihrer Konferenzen teil")


@restriktion
class Rangfolge(Restriktion):
    """Vorliebe für die erste, dann die zweite Konferenz; keine Verstoßmeldungen (SPEC-0012 FR-03)."""

    name = "rangfolge"
    beschreibung = "Lehrkräfte besuchen bevorzugt ihre erste Konferenz, dann die zweite."
    standard_typ = "aus"
    erlaubte_typen = ("weich", "aus")

    def anwenden(self, ctx: Planungskontext, werte: dict[str, Any]) -> None:
        for p in ctx.modell.personen:
            for rang, t in enumerate(p.themen):
                faktor = RANGFAKTOREN[min(rang, len(RANGFAKTOREN) - 1)]
                # Kosten = faktor * (1 - besucht): die Konstante entfällt, besucht senkt die Kosten
                terme = [(-faktor, ctx.teilnahme(p.name, t, j)) for j in ctx.termine(t)]
                ctx.strafe(terme, f"{p.name} besucht {t} nicht")


@restriktion
class Ausgleich(Restriktion):
    """Konferenzen möglichst gleich groß (SPEC-0012 FR-04)."""

    name = "ausgleich"
    beschreibung = "Die Konferenzen sollen möglichst gleich viele Teilnehmende haben."
    standard_typ = "aus"
    erlaubte_typen = ("weich", "aus")

    def anwenden(self, ctx: Planungskontext, werte: dict[str, Any]) -> None:
        modell = ctx.modell
        mit_konferenz = sum(1 for p in modell.personen if modell.themen_von(p.name))
        konferenzen = [t for t in modell.themen if modell.personen_zu(t.name)]
        if not mit_konferenz or not konferenzen:
            return
        ziel = max(1, round(mit_konferenz / len(konferenzen)))
        for t in konferenzen:
            terme = [
                (1, ctx.teilnahme(p.name, t.name, j))
                for p in modell.personen_zu(t.name)
                for j in ctx.termine(t.name)
            ]
            ctx.abweichung(terme, ziel, f"{t.name} weicht von {ziel} Teilnehmenden ab", AUSGLEICH_FAKTOR)


@restriktion
class Wichtigkeit(Restriktion):
    """Wichtige Themen bekommen früher liegende Slots (Strafe = Wichtigkeit × Slot-Index)."""

    name = "wichtigkeit"
    beschreibung = "Wichtigere Themen bekommen früher liegende Slots."
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
    "vorsitz",
    "verteilung",
    "rangfolge",
    "ausgleich",
    "wichtigkeit",
)
