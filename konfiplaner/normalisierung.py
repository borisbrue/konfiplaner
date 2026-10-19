"""Normalisierung uneinheitlicher Konferenznamen (SPEC-0007).

Ein Rohwert aus der Liste wird einer oder mehreren Konferenzen des Konferenzsatzes zugeordnet.
Nur bestätigte Zuordnungen und exakte Treffer sind `sicher`; alles Abgeleitete ist ein `vorschlag`,
den die Fachseite bestätigen muss.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

SICHER, VORSCHLAG, UNBEKANNT = "sicher", "vorschlag", "unbekannt"
MIN_PRAEFIX = 3

# Bekannte Kurzformen; gelten nur als Vorschlag und nur, wenn das Ziel im Konferenzsatz liegt
SYNONYME = {
    "philosophie": "PPL",
    "philo": "PPL",
    "hauswirtschaft": "HW",
    "ge": "Geschichte",
    "gesellschaftslehre": "GL",
    "naturwissenschaften": "NW",
    "naturwissenschaft": "NW",
}


def bereinige(text: Any) -> str:
    """Text mit zusammengefassten Leerzeichen (Anzeigeform)."""
    return " ".join(str(text or "").split())


def schluessel(roh: Any) -> str:
    """Vergleichsform: ohne Groß-/Kleinschreibung, Leerzeichen um `/`, `,` und `;` entfernt."""
    return re.sub(r"\s*([/,;])\s*", r"\1", bereinige(roh).casefold())


@dataclass(frozen=True)
class Aufloesung:
    roh: str
    schluessel: str
    konferenzen: tuple[str, ...]
    status: str
    vorkommen: int = 0


class Normalisierung:
    """Bestätigte Zuordnungen Rohwert → Konferenzen und die Ableitung von Vorschlägen."""

    def __init__(self, bestaetigt: dict[str, list[str]] | None = None) -> None:
        self._bestaetigt: dict[str, tuple[str, ...]] = {}
        for roh, konferenzen in (bestaetigt or {}).items():
            self.bestaetige(roh, konferenzen)

    # ── Bestätigte Zuordnungen ───────────────────────────────────────────────
    def bestaetige(self, roh: str, konferenzen: list[str] | tuple[str, ...]) -> None:
        namen = list(dict.fromkeys(bereinige(k) for k in konferenzen if bereinige(k)))
        if not namen:
            raise ValueError("Mindestens eine Konferenz nötig")
        key = schluessel(roh)
        if not key:
            raise ValueError("Leerer Rohwert")
        self._bestaetigt[key] = tuple(namen)

    def entferne(self, roh: str) -> None:
        self._bestaetigt.pop(schluessel(roh), None)

    def bestaetigt(self) -> dict[str, list[str]]:
        return {k: list(v) for k, v in self._bestaetigt.items()}

    def konferenzen_aus_bestaetigungen(self) -> list[str]:
        return list(dict.fromkeys(k for ziele in self._bestaetigt.values() for k in ziele))

    @classmethod
    def aus_dict(cls, daten: Any) -> Normalisierung:
        """Tolerant gegenüber kaputten Einstellungen: ungültige Einträge werden übersprungen."""
        n = cls()
        if isinstance(daten, dict):
            for roh, ziele in daten.items():
                if isinstance(ziele, str):
                    ziele = [ziele]
                if isinstance(ziele, list) and ziele and all(isinstance(z, str) for z in ziele):
                    try:
                        n.bestaetige(str(roh), ziele)
                    except ValueError:
                        continue
        return n

    # ── Auflösung ────────────────────────────────────────────────────────────
    def loese(self, roh: str, kanon: list[str]) -> Aufloesung:
        key = schluessel(roh)
        text = bereinige(roh)
        if key in self._bestaetigt:
            return Aufloesung(text, key, self._bestaetigt[key], SICHER)
        namen = {schluessel(k): k for k in kanon}
        if key in namen:
            return Aufloesung(text, key, (namen[key],), SICHER)
        vorschlag = self._vorschlag(key, namen)
        if vorschlag:
            return Aufloesung(text, key, vorschlag, VORSCHLAG)
        return Aufloesung(text, key, (), UNBEKANNT)

    def _vorschlag(self, key: str, namen: dict[str, str]) -> tuple[str, ...]:
        teile = [t for t in re.split(r"[/,;]", key) if t.strip()]
        ergebnis: list[str] = []
        for teil in teile:
            gefunden = self._teil(teil.strip(), namen)
            if not gefunden:
                return ()
            ergebnis.extend(gefunden)
        return tuple(dict.fromkeys(ergebnis))

    def _teil(self, teil: str, namen: dict[str, str]) -> list[str]:
        einfach = self._einfach(teil, namen)
        if einfach:
            return [einfach]
        woerter = teil.split()
        if len(woerter) > 1:
            # „NW Biologie": alle Wörter einzeln zuordenbar -> mehrere Konferenzen
            einzeln = [self._einfach(w, namen) for w in woerter]
            if all(einzeln):
                return [e for e in einzeln if e]
            # „Deutsch im Wechsel": erstes Wort ist die Konferenz
            erste = [n for k, n in namen.items() if teil.startswith(k + " ")]
            if len(erste) == 1:
                return erste
        return []

    @staticmethod
    def _einfach(teil: str, namen: dict[str, str]) -> str | None:
        if teil in namen:
            return namen[teil]
        ziel = SYNONYME.get(teil)
        if ziel and schluessel(ziel) in namen:
            return namen[schluessel(ziel)]
        if len(teil) >= MIN_PRAEFIX:
            treffer = [n for k, n in namen.items() if k.startswith(teil)]
            if len(treffer) == 1:
                return treffer[0]
        return None
