"""Lehrerliste (Nachname, Vorname, Fachkonferenz I–III, Vorsitzende) einlesen (SPEC-0007)."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from konfiplaner.modell import Person, Thema
from konfiplaner.normalisierung import SICHER, VORSCHLAG, Aufloesung, Normalisierung, bereinige, schluessel

if TYPE_CHECKING:
    from konfiplaner.excel_import import Importergebnis

FK_MUSTER = re.compile(r"^(?:ggf\w*\s+)?(?:fachkonferenz|fk)\s*(iii|ii|i|3|2|1)\b")
RANG = {"i": 0, "1": 0, "ii": 1, "2": 1, "iii": 2, "3": 2}
STANDARD_WICHTIGKEIT, STANDARD_MINDESTANZAHL, STANDARD_DAUER_MIN = 3, 1, 45


def _norm(text: Any) -> str:
    return re.sub(r"[\s_\-.:]+", " ", str(text or "").strip().lower()).strip()


class Spalten:
    """Spaltenindizes einer Lehrerliste (None = fehlt)."""

    def __init__(self, kopf: list[Any]) -> None:
        self.nachname = self.vorname = self.vorsitz = None
        self.fk: dict[int, int] = {}
        self.titel: dict[int, str] = {}
        for i, zelle in enumerate(kopf):
            n = _norm(zelle)
            if n.startswith("nachname") and self.nachname is None:
                self.nachname = i
            elif n.startswith("vorname") and self.vorname is None:
                self.vorname = i
            elif n.startswith("vorsitz") and self.vorsitz is None:
                self.vorsitz = i
            elif (m := FK_MUSTER.match(n)) and RANG[m.group(1)] not in self.fk:
                self.fk[RANG[m.group(1)]] = i
                self.titel[i] = bereinige(zelle)

    @property
    def erkannt(self) -> bool:
        return self.nachname is not None and self.vorname is not None


def ist_lehrerliste(kopf: list[Any]) -> bool:
    return Spalten(kopf).erkannt


def _zelle(zeile: list[Any], i: int | None) -> str:
    return bereinige(zeile[i]) if i is not None and i < len(zeile) else ""


def lese_lehrerliste(
    blatt: str, zeilen: list[list[Any]], normalisierung: Normalisierung, erg: Importergebnis
) -> None:
    """Füllt `erg` mit Personen, Konferenzen (Themen), Auflösungen und Meldungen."""
    from konfiplaner.excel_import import Meldung

    sp = Spalten(zeilen[0])
    erg.lehrerliste = True
    daten = [(nr, z) for nr, z in enumerate(zeilen[1:], start=2) if any(bereinige(c) for c in z)]

    def meld(schwere: str, nr: int, spalte: str, text: str) -> None:
        erg.meldungen.append(Meldung(schwere, blatt, nr, spalte, text))

    # 1. Konferenzsatz: Vorsitz-Werte, sonst einfache Werte (ohne Trennzeichen)
    kanon: dict[str, str] = {}
    quellen = [sp.vorsitz] if sp.vorsitz is not None else list(sp.fk.values())
    for _, z in daten:
        for i in quellen:
            text = _zelle(z, i)
            if text and (sp.vorsitz is not None or not re.search(r"[/,;]", text)):
                kanon.setdefault(schluessel(text), text)
    for ziel in normalisierung.konferenzen_aus_bestaetigungen():
        kanon.setdefault(schluessel(ziel), ziel)
    kanon_liste = list(kanon.values())

    # 2. Zellen auflösen und zählen
    zaehler: dict[str, int] = {}
    ersttexte: dict[str, str] = {}
    aufgeloest: dict[str, Aufloesung] = {}

    def loese(text: str) -> Aufloesung:
        a = normalisierung.loese(text, kanon_liste)
        key = a.schluessel
        zaehler[key] = zaehler.get(key, 0) + 1
        ersttexte.setdefault(key, text)
        aufgeloest.setdefault(key, a)
        return a

    personen: list[tuple[int, str, list[tuple[int, Aufloesung]], Aufloesung | None]] = []
    for nr, z in daten:
        name = bereinige(f"{_zelle(z, sp.vorname)} {_zelle(z, sp.nachname)}")
        zellen = []
        for rang in sorted(sp.fk):
            text = _zelle(z, sp.fk[rang])
            if text:
                zellen.append((sp.fk[rang], loese(text)))
        vorsitz = loese(_zelle(z, sp.vorsitz)) if _zelle(z, sp.vorsitz) else None
        personen.append((nr, name, zellen, vorsitz))

    # 3. Personen, Fehler und Warnungen
    gesehen: dict[str, int] = {}
    mitglieder: dict[str, None] = {}
    vorsitze: dict[str, str] = {}
    for nr, name, zellen, vorsitz in personen:
        if not name:
            meld("fehler", nr, "Name", "Name fehlt")
            continue
        for i, a in zellen:
            if a.status != SICHER:
                titel = sp.titel[i]
                hinweis = (
                    f" – Vorschlag: {', '.join(a.konferenzen)}"
                    if a.status == VORSCHLAG
                    else " – kein Vorschlag"
                )
                meld("fehler", nr, titel, f"{ersttexte[a.schluessel]!r} ist nicht zugeordnet{hinweis}")
        if vorsitz is not None:
            if vorsitz.status != SICHER:
                meld("fehler", nr, "Vorsitzende", f"{ersttexte[vorsitz.schluessel]!r} ist nicht zugeordnet")
            elif len(vorsitz.konferenzen) != 1:
                meld("fehler", nr, "Vorsitzende", "Der Vorsitz muss genau eine Konferenz sein")
            else:
                konf = vorsitz.konferenzen[0]
                if konf in vorsitze and vorsitze[konf] != name:
                    meld("fehler", nr, "Vorsitzende", f"Konferenz {konf} hat schon einen Vorsitz")
                else:
                    vorsitze[konf] = name
        if name in gesehen:
            meld("warnung", nr, "Name", f"Name {name} kommt doppelt vor (erste Zeile {gesehen[name]} gilt)")
            continue
        gesehen[name] = nr
        konferenzen = tuple(dict.fromkeys(k for _, a in zellen if a.status == SICHER for k in a.konferenzen))
        for k in konferenzen:
            mitglieder.setdefault(k)
        erg.personen.append(Person(name, konferenzen))
        erg.quelle[(blatt, nr)] = name
        if not zellen:
            erg.ohne_konferenz.append(name)
            meld("warnung", nr, "Fachkonferenz", f"{name} hat keine Konferenz")

    # 4. Konferenzen als Themen (Reihenfolge: Konferenzsatz, dann weitere), Standardwerte
    namen = list(dict.fromkeys([*kanon_liste, *mitglieder, *vorsitze]))
    erg.themen = [
        Thema(n, STANDARD_WICHTIGKEIT, STANDARD_MINDESTANZAHL, STANDARD_DAUER_MIN, vorsitze.get(n))
        for n in namen
        if n in mitglieder or n in vorsitze
    ]
    erg.aufloesungen = [
        Aufloesung(ersttexte[k], k, a.konferenzen, a.status, zaehler[k]) for k, a in aufgeloest.items()
    ]
