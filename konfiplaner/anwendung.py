"""Qt-freie Anwendungsschicht: Zustand und Abläufe der Anwendung (SPEC-0005 FR-11).

Die GUI zeigt `Sitzung` nur an; Fachlogik bleibt in Import, Registry, Planer und Export.
"""

from __future__ import annotations

import copy
import dataclasses
import logging
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from pathlib import Path
from typing import Any

from konfiplaner.einladung import exportiere_einladung
from konfiplaner.einstellungen import Einstellungsspeicher, KeineEinstellungen
from konfiplaner.excel_export import exportiere, tabellen
from konfiplaner.excel_import import Importergebnis, importiere
from konfiplaner.modell import Modell, ModellFehler, Person, Plan, Thema, Zeitslot
from konfiplaner.normalisierung import VORSCHLAG, Normalisierung
from konfiplaner.planer import Abbruchsignal, Fixierungen, Fortschritt, Planer, PlanerOptionen
from konfiplaner.restriktionen import (
    STANDARD_REGISTRY,
    Konfiguration,
    KonfigurationsFehler,
    RegelEinstellung,
    Registry,
    standard_konfiguration,
)
from konfiplaner.solver import CpSatPlaner
from konfiplaner.tagesplan import Tagesplan
from konfiplaner.zeitraster import erzeuge_slots
from konfiplaner.zuordnung import LehrerAenderung, Termin, Zuordnung

log = logging.getLogger(__name__)

THEMENWERTE = ("wichtigkeit", "mindestanzahl", "dauer_min")
# Voreinstellung bei Dateien mit Konferenzterminen (SPEC-0008 FR-06): gleichzeitige Konferenzen sind erwartet
PROFIL_FESTTERMINE = {"schwerpunkte": ("weich", 1.0)}
# Standard für Lehrerlisten (SPEC-0012): jede Lehrkraft nimmt an mindestens einer ihrer Konferenzen teil,
# Vorliebe nach Rangfolge, möglichst gleich große Konferenzen; „alle besuchen" ist aus
PROFIL_VERTEILEN = {
    "schwerpunkte": ("aus", 1.0),
    "verteilung": ("hart", 1.0),
    "rangfolge": ("weich", 1.0),
    "ausgleich": ("weich", 1.0),
}
PROFILE = {"verteilen": PROFIL_VERTEILEN, "festtermine": PROFIL_FESTTERMINE, "klassisch": {}}
PROFIL_NAMEN = {
    "auto": "Automatisch (Lehrerliste: Verteilen)",
    "verteilen": "Verteilen: mindestens eine Konferenz, Rest nach Rangfolge und Ausgleich",
    "festtermine": "Rangfolge bei gleichzeitigen Terminen",
    "klassisch": "Klassisch: alle Konferenzen besuchen",
}
PRUEFPRAEFIX = "Prüfung: "
MANUELL = "Der Plan wurde auf dem Verteilungsbrett von Hand angepasst"
MAX_RUECKGAENGIG = 50
TIPP_SCHWERPUNKTE = (
    "Tipp: Die Regel „schwerpunkte“ verlangt, dass jede Lehrkraft alle ihre Konferenzen besucht. "
    "Unter „Regeln“ das Profil „Verteilen“ wählen oder die Regel auf „weich“ stellen."
)
STANDARD_ZEITLIMIT_S = 60.0
STANDARD_ZEITRASTER = {"tage": "Samstag", "beginn": "09:00", "ende": "12:00", "laenge_min": 45}


@dataclass(frozen=True)
class KonferenzAnsicht:
    """Eine Konferenz für die Auswahl (SPEC-0009)."""

    name: str
    ausgewaehlt: bool
    mitglieder: int  # Personen, die die Konferenz in der Datei haben
    vorsitz: str | None
    termine: int


@dataclass(frozen=True)
class LehrerAnsicht:
    """Eine Lehrkraft für die Zuordnung (SPEC-0010 FR-09)."""

    name: str
    konferenzen: tuple[str, ...]  # wirksam: nach Änderung und Auswahl, in Rangfolge
    original: tuple[str, ...]  # laut Datei
    vorsitz_von: tuple[str, ...]
    nicht_verfuegbar: tuple[Termin, ...]
    fest: tuple[Termin, ...]
    teilnahmen: tuple[str, ...]  # aus dem Plan, z. B. "Deutsch (Mi 14:00–15:00)"
    geaendert: bool
    markiert: bool
    neu_zuordnen: bool


@dataclass(frozen=True)
class KartenAnsicht:
    """Eine Lehrkraft auf dem Verteilungsbrett (SPEC-0013 FR-03)."""

    name: str
    weitere: tuple[str, ...]  # weitere Konferenzen im Set der Lehrkraft
    vorsitz: bool  # gesperrt: leitet diese Konferenz
    hat_konferenz: bool


@dataclass(frozen=True)
class SpaltenAnsicht:
    """Eine Spalte des Bretts; `konferenz=None` ist „Ohne Zuteilung“."""

    konferenz: str | None
    karten: tuple[KartenAnsicht, ...]
    vorsitz: str | None
    mindestanzahl: int
    ziel: int
    teilnehmer: int
    unterbesetzt: bool


@dataclass(frozen=True)
class VerschiebeFolge:
    ausnahme: bool
    hinweise: tuple[str, ...]  # Prüfhinweise nach der Änderung


@dataclass(frozen=True)
class RegelAnsicht:
    """Eine Restriktion für die Regelverwaltung."""

    name: str
    typ: str
    gewicht: float
    erlaubte_typen: tuple[str, ...]
    bearbeitbar: bool  # False: braucht Pflichtparameter, nur per Konfigurationsdatei
    parameter_text: str
    beschreibung: str


def pruefe_plan(plan: Plan, modell: Modell) -> list[str]:
    """Prüfhinweise: Mindestanzahl je Termin, Vorsitz in jedem Termin, keine Überschneidung."""
    hinweise: list[str] = []
    for t in plan.termine:
        thema = modell.thema(t.thema)
        if len(t.teilnehmer) < thema.mindestanzahl:
            hinweise.append(
                f"{t.thema} hat {len(t.teilnehmer)} von mindestens {thema.mindestanzahl} Teilnehmenden"
            )
        if thema.vorsitz and thema.vorsitz not in t.teilnehmer:
            hinweise.append(f"Vorsitz {thema.vorsitz} fehlt in {t.thema}")
    belegt: dict[tuple[str, int], str] = {}
    for t in plan.termine:
        for name in t.teilnehmer:
            for slot in range(t.start_slot, t.start_slot + t.anzahl_slots):
                andere = belegt.setdefault((name, slot), t.thema)
                if andere != t.thema:
                    hinweise.append(f"{name} hat zwei Termine gleichzeitig: {andere} und {t.thema}")
    return list(dict.fromkeys(hinweise))


class Sitzung:
    def __init__(
        self,
        einstellungen: Einstellungsspeicher | None = None,
        registry: Registry = STANDARD_REGISTRY,
        planer: Planer | None = None,
    ) -> None:
        self._speicher = einstellungen or KeineEinstellungen()
        self.registry = registry
        self.planer: Planer = planer or CpSatPlaner(registry)
        self.datei: Path | None = None
        self.ergebnis: Importergebnis | None = None
        self.themen: list[Thema] = []
        self.zeitslots: list[Zeitslot] = []
        self.verfuegbarkeit: dict[str, set[int]] = {}
        self.plan: Plan | None = None
        self.plan_modell: Modell | None = None
        self.konfiguration = self._basiskonfiguration()
        self.zeitlimit_s = STANDARD_ZEITLIMIT_S
        self.zeitraster: dict[str, Any] = dict(STANDARD_ZEITRASTER)
        self.letzter_exportordner: Path | None = None
        self._mtime: float | None = None
        self.normalisierung = Normalisierung()
        self.abgewaehlt: set[str] = set()  # abgewählte Konferenzen (SPEC-0009)
        self.zuordnung = Zuordnung()  # manuelle Änderungen (SPEC-0010)
        self._gespeicherte_zuordnung = Zuordnung()
        self._gesetzt: set[str] = set()  # von Hand gesetzte Regeln (verdrängen das Profil)
        self.profil = "auto"  # auto | verteilen | festtermine | klassisch (SPEC-0012)
        self.tagesplan = Tagesplan()  # Ablauf des Tages für die Einladung (SPEC-0014)
        self.logo: Path | None = None
        self.update_pruefung = True  # Update-Hinweis beim Start (SPEC-0015)
        self.letzte_updatepruefung: datetime | None = None
        self.ausgeblendete_version: str | None = None
        self._rueckgaengig: list[tuple[Plan, Plan, str, LehrerAenderung | None, frozenset[str]]] = []
        self._themenwerte: dict[str, dict[str, int]] = {}
        self._lade_einstellungen()

    # ── Einstellungen (FR-07) ───────────────────────────────────────────────
    def _basiskonfiguration(self) -> Konfiguration:
        k = standard_konfiguration()
        for name in self.registry.namen():
            if name not in k.einstellungen:
                k.einstellungen[name] = RegelEinstellung(name, "aus")
        return k

    def _lade_einstellungen(self) -> None:
        daten = self._speicher.laden()
        if isinstance(daten.get("letzte_datei"), str):
            self.datei = Path(daten["letzte_datei"])
        if isinstance(daten.get("zeitlimit_s"), (int, float)) and daten["zeitlimit_s"] > 0:
            self.zeitlimit_s = float(daten["zeitlimit_s"])
        if isinstance(daten.get("zeitraster"), dict):
            self.zeitraster.update(daten["zeitraster"])
        if isinstance(daten.get("letzter_exportordner"), str):
            self.letzter_exportordner = Path(daten["letzter_exportordner"])
        self._gespeicherte_zuordnung = Zuordnung.aus_dict(daten.get("zuordnung"))
        if daten.get("profil") in ("auto", *PROFILE):
            self.profil = daten["profil"]
        self.tagesplan = Tagesplan.aus_dict(daten.get("tagesplan"))
        if isinstance(daten.get("logo"), str):
            self.logo = Path(daten["logo"])
        if isinstance(daten.get("update_pruefung"), bool):
            self.update_pruefung = daten["update_pruefung"]
        if isinstance(daten.get("ausgeblendete_version"), str):
            self.ausgeblendete_version = daten["ausgeblendete_version"]
        try:
            self.letzte_updatepruefung = datetime.fromisoformat(daten["letzte_updatepruefung"])
        except (KeyError, TypeError, ValueError):
            self.letzte_updatepruefung = None
        ab = daten.get("abgewaehlte_konferenzen")
        if isinstance(ab, list):
            self.abgewaehlt = {str(n) for n in ab}
        self.normalisierung = Normalisierung.aus_dict(daten.get("normalisierung"))
        werte = daten.get("themenwerte")
        if isinstance(werte, dict):
            self._themenwerte = {
                str(n): {k: v for k, v in w.items() if k in THEMENWERTE and isinstance(v, int)}
                for n, w in werte.items()
                if isinstance(w, dict)
            }
        regeln = daten.get("regeln")
        if isinstance(regeln, dict):
            standard = self._basiskonfiguration()
            for name, eintrag in regeln.items():
                try:
                    neu = Konfiguration.aus_dict({"restriktionen": {name: eintrag}}, self.registry, standard)
                except (KonfigurationsFehler, TypeError, KeyError):
                    log.warning("Gespeicherte Regel %s ignoriert", name)
                    continue
                self.konfiguration = Konfiguration.aus_dict(
                    {"restriktionen": {name: eintrag}}, self.registry, self.konfiguration
                )
                if neu.einstellungen[name] != standard.einstellungen.get(name):
                    self._gesetzt.add(name)  # weicht vom Standard ab: von Hand gesetzt

    def speichere(self) -> None:
        self._speicher.speichern(
            {
                "letzte_datei": str(self.datei) if self.datei else None,
                "zeitlimit_s": self.zeitlimit_s,
                "zeitraster": dict(self.zeitraster),
                "letzter_exportordner": str(self.letzter_exportordner) if self.letzter_exportordner else None,
                "normalisierung": self.normalisierung.bestaetigt(),
                "abgewaehlte_konferenzen": sorted(self.abgewaehlt),
                "profil": self.profil,
                "tagesplan": self.tagesplan.als_dict(),
                "logo": str(self.logo) if self.logo else None,
                "update_pruefung": self.update_pruefung,
                "ausgeblendete_version": self.ausgeblendete_version,
                "letzte_updatepruefung": self.letzte_updatepruefung.isoformat()
                if self.letzte_updatepruefung
                else None,
                "zuordnung": self.zuordnung.als_dict()
                if self.datei
                else self._gespeicherte_zuordnung.als_dict(),
                "themenwerte": {n: dict(w) for n, w in self._themenwerte.items()},
                "regeln": {
                    n: {"typ": e.typ, "gewicht": e.gewicht, "parameter": dict(e.parameter)}
                    for n, e in self.konfiguration.einstellungen.items()
                    if n in self._gesetzt
                },
            }
        )

    # ── Daten laden und ergänzen (FR-02, FR-10) ─────────────────────────────
    def lade(self, pfad: str | Path) -> Importergebnis:
        """Liest die Datei; `ImportDateiFehler` bei unlesbaren Dateien (Zustand bleibt dann unverändert)."""
        pfad = Path(pfad)
        ergebnis = importiere(pfad, normalisierung=self.normalisierung)
        erzeugte_slots = self.zeitslots if self.datei == pfad and not ergebnis.zeitslots else []
        self.datei, self.ergebnis = pfad, ergebnis
        # Beim Neuladen bleiben geänderte Themenwerte und erzeugte Zeitslots erhalten (SPEC-0007 FR-10)
        self.themen = [
            dataclasses.replace(t, **self._themenwerte[t.name]) if t.name in self._themenwerte else t
            for t in ergebnis.themen
        ]
        self.zeitslots = list(ergebnis.zeitslots) or list(erzeugte_slots)
        self.verfuegbarkeit = {k: set(v) for k, v in ergebnis.verfuegbarkeit.items()}
        self.plan = self.plan_modell = None
        self._mtime = pfad.stat().st_mtime
        self._wende_profil()
        self._uebernehme_zuordnung(pfad)
        self.speichere()
        return ergebnis

    def _uebernehme_zuordnung(self, pfad: Path) -> None:
        """Gespeicherte manuelle Änderungen gelten nur für dieselbe Datei (SPEC-0010 FR-10)."""
        if self.zuordnung.datei == str(pfad):
            return  # Neuladen derselben Datei: der Zustand bleibt
        gespeichert = self._gespeicherte_zuordnung
        self.zuordnung = gespeichert if gespeichert.datei == str(pfad) else Zuordnung()
        self.zuordnung.datei = str(pfad)
        self._gespeicherte_zuordnung = Zuordnung()

    def wirksames_profil(self) -> str:
        """Gewähltes Profil; bei „auto“ folgt es der Datei (SPEC-0012 FR-01)."""
        if self.profil in PROFILE:
            return self.profil
        erg = self.ergebnis
        if erg is not None and erg.lehrerliste:
            return "verteilen"
        return "festtermine" if erg is not None and erg.festtermine else "klassisch"

    def setze_profil(self, profil: str) -> None:
        if profil != "auto" and profil not in PROFILE:
            raise ModellFehler(f"Unbekanntes Profil {profil}")
        self.profil = profil
        self._wende_profil()
        self.plan = self.plan_modell = None
        self.speichere()

    def _wende_profil(self) -> None:
        """Regeln, die niemand von Hand gesetzt hat, folgen dem Profil (SPEC-0008 FR-06, SPEC-0012 FR-01)."""
        gewaehlt = PROFILE[self.wirksames_profil()]
        standard = self._basiskonfiguration()
        for name in {n for p in PROFILE.values() for n in p}:
            if name in self._gesetzt or name not in standard.einstellungen:
                continue
            typ_gewicht = gewaehlt.get(name)
            self.konfiguration.einstellungen[name] = (
                RegelEinstellung(name, *typ_gewicht) if typ_gewicht else standard.einstellungen[name]
            )

    def neu_laden(self) -> Importergebnis:
        if self.datei is None:
            raise ModellFehler("Keine Datei geladen")
        return self.lade(self.datei)

    def datei_geaendert(self) -> bool:
        """True, wenn die geladene Datei seit dem Laden verändert wurde."""
        if self.datei is None or self._mtime is None:
            return False
        try:
            return self.datei.stat().st_mtime != self._mtime
        except OSError:
            return False

    def setze_thema(self, index: int, **felder: Any) -> None:
        """Ändert Wichtigkeit, Mindestanzahl, Dauer oder Vorsitz; ungültige Werte lösen `ModellFehler` aus."""
        if "vorsitz" in felder:
            name = (felder["vorsitz"] or "").strip() or None
            if name is not None and name not in self.personen_namen():
                raise ModellFehler(f"Unbekannte Person {name} als Vorsitz")
            felder["vorsitz"] = name
        neu = dataclasses.replace(self.themen[index], **felder)
        self.themen[index] = neu
        werte = {k: v for k, v in felder.items() if k in THEMENWERTE}
        if werte:
            self._themenwerte.setdefault(neu.name, {}).update(werte)
        self.plan = self.plan_modell = None

    # ── Normalisierung (SPEC-0007 FR-07) ────────────────────────────────────
    def bestaetige(self, roh: str, konferenzen: list[str]) -> Importergebnis:
        """Bestätigt eine Zuordnung für alle Vorkommen und liest die Datei neu ein."""
        self.normalisierung.bestaetige(roh, konferenzen)
        return self._nach_normalisierung()

    def bestaetige_vorschlaege(self) -> int:
        """Bestätigt alle offenen Vorschläge; Rückgabe: Anzahl."""
        offen = [a for a in (self.ergebnis.aufloesungen if self.ergebnis else []) if a.status == VORSCHLAG]
        for a in offen:
            self.normalisierung.bestaetige(a.roh, list(a.konferenzen))
        if offen:
            self._nach_normalisierung()
        return len(offen)

    def _nach_normalisierung(self) -> Importergebnis:
        self.speichere()
        return self.neu_laden()

    def personen_namen(self) -> list[str]:
        return [p.name for p in self.ergebnis.personen] if self.ergebnis else []

    def erzeuge_zeitslots(self, tage: str, beginn: time, ende: time, laenge_min: int) -> list[Zeitslot]:
        if self.ergebnis is not None and self.ergebnis.festtermine:
            raise ModellFehler(
                "Die Zeitslots stammen aus dem Blatt Konferenzen und lassen sich hier nicht erzeugen"
            )
        slots = erzeuge_slots([t for t in tage.split(",")], beginn, ende, laenge_min)
        self.zeitslots = slots
        self.verfuegbarkeit = {}  # Slot-Indizes der Datei passen nicht mehr
        self.zeitraster = {
            "tage": tage,
            "beginn": f"{beginn:%H:%M}",
            "ende": f"{ende:%H:%M}",
            "laenge_min": laenge_min,
        }
        self.plan = self.plan_modell = None
        self.speichere()
        return slots

    def planungshindernisse(self) -> list[str]:
        gruende = []
        if self.ergebnis is None:
            return ["Keine Datei geladen"]
        if self.ergebnis.fehler:
            gruende.append(f"{len(self.ergebnis.fehler)} Fehler in der Datei")
        if not self.ergebnis.personen:
            gruende.append("Keine Personen")
        if self.ergebnis.themen and not self.ausgewaehlte_themen():
            gruende.append("Keine Konferenz ausgewählt")
        if not self.zeitslots:
            gruende.append("Keine Zeitslots")
        return gruende

    @property
    def planbar(self) -> bool:
        return not self.planungshindernisse()

    def modell(self) -> Modell:
        if self.ergebnis is None:
            raise ModellFehler("Keine Datei geladen")
        themen, personen = self.ausgewaehlte_themen(), self.effektive_personen()
        verfuegbar = {k: set(v) for k, v in self.verfuegbarkeit.items()}
        modell = self.ergebnis.baue_modell(themen, list(self.zeitslots), verfuegbar, personen)
        gesperrt = self._gesperrte_slots(modell)
        if gesperrt:
            alle = set(range(len(modell.zeitslots)))
            for name, slots in gesperrt.items():
                verfuegbar[name] = verfuegbar.get(name, alle) - slots
            modell = self.ergebnis.baue_modell(themen, list(self.zeitslots), verfuegbar, personen)
        return modell

    def _gesperrte_slots(self, modell: Modell) -> dict[str, set[int]]:
        """Slots der Termine, an denen eine Lehrkraft nicht kann (SPEC-0010 FR-04)."""
        namen = {t.name for t in modell.themen}
        personen = {p.name for p in modell.personen}
        ergebnis: dict[str, set[int]] = {}
        for name, a in self.zuordnung.personen.items():
            if name not in personen:
                continue
            for konferenz, j in a.nicht_verfuegbar:
                bloecke = modell.fest_bloecke(konferenz) if konferenz in namen else []
                if j < len(bloecke):
                    start, anzahl = bloecke[j]
                    ergebnis.setdefault(name, set()).update(range(start, start + anzahl))
        return ergebnis

    # ── Manuelle Zuordnung (SPEC-0010) ──────────────────────────────────────
    def _person(self, name: str) -> Person:
        for p in self.ergebnis.personen if self.ergebnis else []:
            if p.name == name:
                return p
        raise ModellFehler(f"Unbekannte Lehrkraft {name}")

    def _konferenz(self, name: str) -> Thema:
        for t in self.themen:
            if t.name == name:
                return t
        raise ModellFehler(f"Unbekannte Konferenz {name}")

    def konferenzen_von(self, name: str) -> tuple[str, ...]:
        """Konferenzen einer Lehrkraft nach manueller Änderung, vor der Auswahl (in Rangfolge)."""
        self._person(name)
        return self._basis_konferenzen(name)

    def _basis_konferenzen(self, name: str) -> tuple[str, ...]:
        return next(p.themen for p in self._basis_personen() if p.name == name)

    def _markiere(self, *namen: str | None) -> None:
        self.zuordnung.markiert |= {n for n in namen if n}
        self.zuordnung.bereinige()
        self.speichere()

    def setze_konferenzen(self, personen: list[str], konferenzen: list[str]) -> None:
        """Ersetzt die geordnete Konferenzliste für die Lehrkräfte (SPEC-0010 FR-01)."""
        neu = tuple(dict.fromkeys(self._konferenz(k).name for k in konferenzen))
        for name in personen:
            self._person(name)
            if neu != self._basis_konferenzen(name):
                self.zuordnung.aenderung(name).konferenzen = neu
                self._markiere(name)

    def aendere_konferenzen(
        self, personen: list[str], aktion: str, konferenzen: list[str], position: int | None = None
    ) -> None:
        """Sammeländerung (SPEC-0010 FR-02): `hinzufuegen` (Position ab 1, sonst am Ende), `entfernen`, `ersetzen`."""
        if aktion not in ("hinzufuegen", "entfernen", "ersetzen"):
            raise ModellFehler(f"Unbekannte Aktion {aktion}")
        gewaehlt = [self._konferenz(k).name for k in konferenzen]
        for name in personen:
            alt = list(self._basis_konferenzen(self._person(name).name))
            if aktion == "ersetzen":
                neu = list(dict.fromkeys(gewaehlt))
            elif aktion == "entfernen":
                neu = [k for k in alt if k not in gewaehlt]
            else:
                neu = list(alt)
                stelle = len(neu) if position is None else max(0, min(position - 1, len(neu)))
                for k in gewaehlt:
                    if k not in neu:
                        neu.insert(stelle, k)
                        stelle += 1
            if tuple(neu) != tuple(alt):
                self.zuordnung.aenderung(name).konferenzen = tuple(neu)
                self._markiere(name)

    def setze_vorsitz(self, konferenz: str, person: str | None) -> None:
        """Ändert den Vorsitz; alter und neuer Vorsitz werden markiert (SPEC-0010 FR-03, FR-07)."""
        t = self._konferenz(konferenz)
        if person:
            self._person(person)
        alt = self._vorsitz(t)
        neu = person or None
        if neu == alt:
            return
        if neu == t.vorsitz:
            self.zuordnung.vorsitz.pop(konferenz, None)  # entspricht wieder der Datei
        else:
            self.zuordnung.vorsitz[konferenz] = neu
        self._markiere(alt, neu)

    def setze_nicht_verfuegbar(self, person: str, termine: set[Termin]) -> None:
        self._person(person)
        self._pruefe_termine(termine)
        a = self.zuordnung.aenderung(person)
        if frozenset(termine) != a.nicht_verfuegbar:
            a.nicht_verfuegbar = frozenset(termine)
            self._markiere(person)

    def setze_zuweisung(self, person: str, konferenzen: set[str]) -> None:
        """Weist die Lehrkraft fest Konferenzen zu: sie nimmt an mindestens einem Termin teil (SPEC-0012 FR-09)."""
        self._person(person)
        namen = {self._konferenz(k).name for k in konferenzen}
        a = self.zuordnung.aenderung(person)
        if tuple(sorted(namen)) != tuple(sorted(a.zuweisung)):
            a.zuweisung = tuple(sorted(namen))
            self._markiere(person)

    def tipp(self, plan: Plan | None = None) -> str | None:
        """Hinweis, wie sich ein fehlender Plan beheben lässt (SPEC-0012 FR-08)."""
        plan = plan or self.plan
        if plan is None or plan.status != "kein_plan":
            return None
        harte = self.konfiguration.einstellungen.get("schwerpunkte")
        if (
            harte is not None
            and harte.typ == "hart"
            and any("Regel schwerpunkte" in g for g in plan.begruendung)
        ):
            return TIPP_SCHWERPUNKTE
        return None

    # ── Verteilungsbrett (SPEC-0013) ────────────────────────────────────────
    def verteilung(self) -> list[SpaltenAnsicht]:
        """Spalten des Bretts: „Ohne Zuteilung“ und je Konferenz im Plan eine Spalte."""
        if self.plan is None or self.plan_modell is None:
            return []
        m = self.plan_modell
        sets = {p.name: p for p in self.effektive_personen()}
        besucht: dict[str, set[str]] = {}
        for t in self.plan.termine:
            for name in t.teilnehmer:
                besucht.setdefault(name, set()).add(t.thema)
        mit_konferenz = sum(1 for p in m.personen if m.themen_von(p.name))
        ziel = max(1, round(mit_konferenz / len(m.themen))) if mit_konferenz and m.themen else 1

        def karte(name: str, aktuell: str | None, chef: bool) -> KartenAnsicht:
            menge = sets[name].themen if name in sets else ()
            weitere = tuple(k for k in menge if k != aktuell and k in {t.name for t in m.themen})
            return KartenAnsicht(name, weitere, chef, bool(menge) or chef)

        spalten: list[SpaltenAnsicht] = []
        ohne = [p.name for p in m.personen if p.name not in besucht]
        spalten.append(
            SpaltenAnsicht(None, tuple(karte(n, None, False) for n in ohne), None, 0, 0, len(ohne), False)
        )
        for t in m.themen:
            mitglieder = sorted(
                (n for n, ks in besucht.items() if t.name in ks), key=lambda n: (n != t.vorsitz, n.casefold())
            )
            termine = [x for x in self.plan.termine if x.thema == t.name]
            klein = any(len(x.teilnehmer) < t.mindestanzahl for x in termine) or not termine
            spalten.append(
                SpaltenAnsicht(
                    t.name,
                    tuple(karte(n, t.name, n == t.vorsitz) for n in mitglieder),
                    t.vorsitz,
                    t.mindestanzahl,
                    ziel,
                    len(mitglieder),
                    klein,
                )
            )
        return spalten

    def pruefe_verteilung(self) -> list[str]:
        """Prüfhinweise zum aktuellen Plan: Mindestanzahl, Vorsitz, Überschneidung (SPEC-0013 FR-07)."""
        if self.plan is None or self.plan_modell is None:
            return []
        return pruefe_plan(self.plan, self.plan_modell)

    def _setze_pruefhinweise(self, plan: Plan, modell: Modell) -> Plan:
        """Ersetzt die Prüfhinweise im Plan und vermerkt die manuelle Anpassung."""
        warnungen = [w for w in plan.warnungen if not w.startswith(PRUEFPRAEFIX)]
        if MANUELL not in warnungen:
            warnungen.insert(0, MANUELL)
        hinweise = [PRUEFPRAEFIX + h for h in pruefe_plan(plan, modell)]
        return dataclasses.replace(plan, warnungen=warnungen + hinweise)

    @property
    def kann_rueckgaengig(self) -> bool:
        return bool(self._rueckgaengig) and self._rueckgaengig[-1][1] is self.plan

    def verschiebe(self, person: str, ziel: str, von: str | None = None) -> VerschiebeFolge:
        """Legt die Lehrkraft in die Ziel-Konferenz und merkt die Zuweisung (SPEC-0013 FR-04, FR-06)."""
        if self.plan is None or self.plan_modell is None:
            raise ModellFehler("Kein Plan vorhanden")
        m, plan = self.plan_modell, self.plan
        self._person(person)
        if ziel not in {t.name for t in m.themen}:
            raise ModellFehler(f"{ziel} findet nicht statt")
        if von == ziel:
            return VerschiebeFolge(False, tuple(self.pruefe_verteilung()))
        if von is not None and m.thema(von).vorsitz == person:
            raise ModellFehler(
                f"{person} ist Vorsitz von {von} und lässt sich nicht verschieben: Den Vorsitz zuerst im Dialog Bearbeiten ändern"
            )

        def belegt(t) -> set[int]:
            return set(range(t.start_slot, t.start_slot + t.anzahl_slots))

        meine = [i for i, t in enumerate(plan.termine) if person in t.teilnehmer]
        kandidaten = [i for i, t in enumerate(plan.termine) if t.thema == ziel]
        if not kandidaten:
            raise ModellFehler(f"{ziel} hat keinen Termin im Plan")

        def konflikte(k: int) -> list[int]:
            return [
                i
                for i in meine
                if plan.termine[i].thema != ziel
                and (plan.termine[i].thema == von or belegt(plan.termine[i]) & belegt(plan.termine[k]))
            ]

        wahl = min(kandidaten, key=lambda k: (len(konflikte(k)), k))
        raus = set(konflikte(wahl)) | {i for i in meine if plan.termine[i].thema == von}
        for i in raus:
            if m.thema(plan.termine[i].thema).vorsitz == person:
                raise ModellFehler(
                    f"{person} ist Vorsitz von {plan.termine[i].thema} (gleiche Zeit) und lässt sich nicht verschieben"
                )
        basis = self.konferenzen_von(person)
        ausnahme = ziel not in basis and m.thema(ziel).vorsitz != person

        vorher = copy.deepcopy(self.zuordnung.personen.get(person))
        markiert_vorher = frozenset(self.zuordnung.markiert)
        reihenfolge = {p.name: i for i, p in enumerate(m.personen)}
        neue = []
        for i, t in enumerate(plan.termine):
            namen = [n for n in t.teilnehmer if not (n == person and i in raus)]
            if i == wahl and person not in namen:
                namen.append(person)
            neue.append(
                dataclasses.replace(t, teilnehmer=tuple(sorted(namen, key=lambda n: reihenfolge.get(n, 0))))
            )
        a = self.zuordnung.aenderung(person)
        a.zuweisung = tuple(sorted((set(a.zuweisung) - ({von} if von else set())) | {ziel}))
        if ausnahme:
            a.konferenzen = (*basis, ziel)
        neu = self._setze_pruefhinweise(dataclasses.replace(plan, termine=neue), m)
        self.plan = neu
        self._rueckgaengig.append((plan, neu, person, vorher, markiert_vorher))
        del self._rueckgaengig[:-MAX_RUECKGAENGIG]
        self.speichere()
        return VerschiebeFolge(ausnahme, tuple(self.pruefe_verteilung()))

    def rueckgaengig(self) -> bool:
        """Nimmt die letzte Verschiebung zurück: Plan, Set und Zuweisung der Lehrkraft (SPEC-0013 FR-08)."""
        if not self.kann_rueckgaengig:
            self._rueckgaengig.clear()
            return False
        alt, _neu, person, aenderung, markiert = self._rueckgaengig.pop()
        self.plan = alt
        if aenderung is None:
            self.zuordnung.personen.pop(person, None)
        else:
            self.zuordnung.personen[person] = aenderung
        self.zuordnung.markiert = set(markiert)
        self.speichere()
        return True

    def setze_fest(self, person: str, termine: set[Termin]) -> None:
        """Gibt die Teilnahme an Konferenzterminen fest vor (SPEC-0010 FR-05)."""
        self._person(person)
        self._pruefe_termine(termine)
        wirksam = {t.name for t in self.ausgewaehlte_themen()}
        for konferenz, _ in termine:
            if konferenz not in self._basis_konferenzen(person):
                raise ModellFehler(f"{konferenz} ist keine Konferenz von {person}")
            if konferenz not in wirksam:
                raise ModellFehler(f"{konferenz} ist abgewählt")
        a = self.zuordnung.aenderung(person)
        if frozenset(termine) != a.fest:
            a.fest = frozenset(termine)
            self._markiere(person)

    def _pruefe_termine(self, termine: set[Termin]) -> None:
        for konferenz, j in termine:
            t = self._konferenz(konferenz)
            if not 0 <= j < len(t.festtermine):
                raise ModellFehler(f"{konferenz} hat keinen Termin {j + 1}")

    def zuruecksetzen(self, person: str) -> None:
        """Verwirft alle Änderungen einer Lehrkraft (SPEC-0010 FR-09)."""
        self._person(person)
        hatte = person in self.zuordnung.personen
        self.zuordnung.personen.pop(person, None)
        for konferenz, name in list(self.zuordnung.vorsitz.items()):
            if name == person or self._konferenz(konferenz).vorsitz == person:
                del self.zuordnung.vorsitz[konferenz]
        if person in self.zuordnung.markiert:
            self.zuordnung.markiert.discard(person)  # die Änderung war noch nicht eingeplant
        elif hatte and self.plan is not None:
            self.zuordnung.markiert.add(person)  # der Plan enthält die verworfene Änderung
        self.speichere()

    @property
    def markiert(self) -> list[str]:
        namen = {p.name for p in self.ergebnis.personen} if self.ergebnis else set()
        return sorted(n for n in self.zuordnung.markiert if n in namen)

    def lehrkraefte(self) -> list[LehrerAnsicht]:
        if self.ergebnis is None:
            return []
        wirksam = {p.name: p for p in self.effektive_personen()}
        neu = set(self.neu_zuordnen)
        vorsitz: dict[str, list[str]] = {}
        for t in self.ausgewaehlte_themen():
            if t.vorsitz:
                vorsitz.setdefault(t.vorsitz, []).append(t.name)
        ansicht = []
        for p in self.ergebnis.personen:
            a = self.zuordnung.personen.get(p.name, LehrerAenderung())
            geaendert = not a.leer() or any(
                name == p.name or self._konferenz(k).vorsitz == p.name
                for k, name in self.zuordnung.vorsitz.items()
            )
            ansicht.append(
                LehrerAnsicht(
                    p.name,
                    wirksam[p.name].themen,
                    p.themen,
                    tuple(vorsitz.get(p.name, ())),
                    tuple(sorted(a.nicht_verfuegbar)),
                    tuple(sorted(a.fest)),
                    self._teilnahmen(p.name),
                    geaendert,
                    p.name in self.zuordnung.markiert,
                    p.name in neu,
                )
            )
        return ansicht

    def _teilnahmen(self, name: str) -> tuple[str, ...]:
        if self.plan is None or self.plan_modell is None:
            return ()
        zeilen = []
        for t in self.plan.termine:
            if name in t.teilnehmer:
                z = self.plan_modell.zeitslots[t.start_slot]
                ende = self.plan_modell.zeitslots[t.start_slot + t.anzahl_slots - 1].ende
                zeilen.append(f"{t.thema} ({z.tag} {z.start:%H:%M}–{ende:%H:%M})")
        return tuple(zeilen)

    def termin_text(self, konferenz: str, j: int) -> str:
        """Beschriftung eines Konferenztermins, z. B. „Deutsch: Mi 14:00–15:00“."""
        f = self._konferenz(konferenz).festtermine[j]
        return f"{konferenz}: {f.tag} {f.start:%H:%M}–{f.ende:%H:%M}"

    def _fixierungen(self, modell: Modell, teil: bool) -> Fixierungen | None:
        """Feste Teilnahmen der Lehrkräfte und, bei `teil`, der bisherige Plan der nicht markierten."""
        teilnahmen: dict[str, dict[tuple[str, int], bool]] = {}
        termine: dict[str, tuple[int, ...]] = {}
        namen = {t.name for t in modell.themen}
        if teil and self.plan is not None:
            neu_planen = set(self.zuordnung.markiert)
            for t in self.plan.termine:
                if t.thema not in namen:
                    continue
                termine[t.thema] = (*termine.get(t.thema, ()), t.start_slot)
                for p in modell.personen:
                    if p.name not in neu_planen:
                        teilnahmen.setdefault(p.name, {})[t.thema, t.start_slot] = p.name in t.teilnehmer
        for name, a in self.zuordnung.personen.items():
            for konferenz, j in a.fest:
                bloecke = modell.fest_bloecke(konferenz) if konferenz in namen else []
                if j < len(bloecke) and name in {p.name for p in modell.personen}:
                    teilnahmen.setdefault(name, {})[konferenz, bloecke[j][0]] = True
        zuweisungen = {
            name: tuple(k for k in a.zuweisung if k in namen)
            for name, a in self.zuordnung.personen.items()
            if a.zuweisung and name in {p.name for p in modell.personen}
        }
        fix = Fixierungen(teilnahmen, termine, {n: k for n, k in zuweisungen.items() if k})
        return None if fix.leer() else fix

    def _ergaenze_warnungen(self, plan: Plan) -> None:
        if self.ergebnis is not None:
            plan.warnungen += [f"{name} hat keine Konferenz" for name in self.ergebnis.ohne_konferenz]
            plan.warnungen += [f"{name} hat durch die Auswahl keine Konferenz" for name in self.neu_zuordnen]

    def teil_neu_planen(
        self, fortschritt: Callable[[Fortschritt], None] | None = None, abbruch: Abbruchsignal | None = None
    ) -> Plan:
        """Plant nur die markierten Lehrkräfte neu, alle anderen bleiben wie im Plan (SPEC-0010 FR-08).

        Ohne Plan oder ohne Markierung wird vollständig geplant. Bei „kein_plan" bleiben Plan und Markierung.
        """
        if self.plan is None or not self.markiert:
            return self.planen(fortschritt, abbruch)
        hindernisse = self.planungshindernisse()
        if hindernisse:
            raise ModellFehler("; ".join(hindernisse))
        modell = self.modell()
        plan = self._plane(modell, self._fixierungen(modell, teil=True), fortschritt, abbruch)
        if plan.status != "kein_plan":
            self.plan, self.plan_modell = plan, modell
            self.zuordnung.markiert.clear()
            self.speichere()
        return plan

    def _plane(self, modell: Modell, fixierungen: Fixierungen | None, fortschritt, abbruch) -> Plan:
        zusatz = {"fixierungen": fixierungen} if fixierungen is not None else {}
        plan = self.planer.planen(
            modell,
            self.konfiguration,
            PlanerOptionen(
                zeitlimit_s=self.zeitlimit_s,
                # Lehrerlisten im Profil „Verteilen“: eine Konferenz ist ein Treffen (SPEC-0012 FR-06)
                max_termine_je_thema=1 if self.wirksames_profil() == "verteilen" else 3,
            ),
            fortschritt,
            abbruch,
            **zusatz,
        )
        self._ergaenze_warnungen(plan)
        return plan

    # ── Konferenzauswahl (SPEC-0009) ────────────────────────────────────────
    def konferenzen(self) -> list[KonferenzAnsicht]:
        mitglieder = Counter(t for p in self._basis_personen() for t in p.themen)
        return [
            KonferenzAnsicht(
                t.name,
                t.name not in self.abgewaehlt,
                mitglieder[t.name],
                self._vorsitz(t),
                len(t.festtermine),
            )
            for t in self.themen
        ]

    def waehle(self, name: str, ausgewaehlt: bool) -> None:
        if name not in {t.name for t in self.themen}:
            raise ModellFehler(f"Unbekannte Konferenz {name}")
        (self.abgewaehlt.discard if ausgewaehlt else self.abgewaehlt.add)(name)
        self._auswahl_geaendert()

    def waehle_alle(self, ausgewaehlt: bool = True) -> None:
        self.abgewaehlt = set() if ausgewaehlt else {t.name for t in self.themen}
        self._auswahl_geaendert()

    def _auswahl_geaendert(self) -> None:
        self.plan = self.plan_modell = None
        self.speichere()

    def ausgewaehlte_themen(self) -> list[Thema]:
        """Themen der ausgewählten Konferenzen; eine abgewählte Hauptkonferenz wird nicht mehr referenziert."""
        return [
            dataclasses.replace(
                t, haupt=None if t.haupt in self.abgewaehlt else t.haupt, vorsitz=self._vorsitz(t)
            )
            for t in self.themen
            if t.name not in self.abgewaehlt
        ]

    def _vorsitz(self, t: Thema) -> str | None:
        """Wirksamer Vorsitz: manuelle Änderung (falls die Person existiert) vor der Datei."""
        if t.name in self.zuordnung.vorsitz:
            name = self.zuordnung.vorsitz[t.name]
            return name if name in self.personen_namen() else None
        return t.vorsitz

    def _basis_personen(self) -> list[Person]:
        """Personen mit manuell geänderten Konferenzen, noch vor der Auswahl."""
        if self.ergebnis is None:
            return []
        bekannt = {t.name for t in self.themen}
        ergebnis = []
        for p in self.ergebnis.personen:
            a = self.zuordnung.personen.get(p.name)
            if a is not None and a.konferenzen is not None:
                p = dataclasses.replace(p, themen=tuple(k for k in a.konferenzen if k in bekannt))
            ergebnis.append(p)
        return ergebnis

    def effektive_personen(self) -> list[Person]:
        """Personen mit den Konferenzen der Auswahl; die übrigen rücken in der Rangfolge nach."""
        return [
            dataclasses.replace(p, themen=tuple(t for t in p.themen if t not in self.abgewaehlt))
            for p in self._basis_personen()
        ]

    @property
    def neu_zuordnen(self) -> list[str]:
        """Personen, die durch die Auswahl ihre letzte Konferenz verloren haben."""
        return [
            p.name
            for p, e in zip(self._basis_personen(), self.effektive_personen(), strict=True)
            if p.themen and not e.themen
        ]

    # ── Regeln (FR-03) ──────────────────────────────────────────────────────
    def regeln(self) -> list[RegelAnsicht]:
        ansicht = []
        for name in self.registry.namen():
            klasse = self.registry.hole(name)
            e = self.konfiguration.einstellungen.get(name, RegelEinstellung(name, "aus"))
            pflicht = any(p for _, p in klasse.parameter.values())
            ansicht.append(
                RegelAnsicht(
                    name,
                    e.typ,
                    e.gewicht,
                    klasse.erlaubte_typen,
                    not pflicht,
                    ", ".join(f"{k}={v}" for k, v in e.parameter.items()),
                    klasse.beschreibung,
                )
            )
        return ansicht

    def setze_regel(self, name: str, typ: str, gewicht: float = 1.0) -> None:
        """Setzt Typ und Gewicht; Parameter bleiben. `KonfigurationsFehler` bei ungültigen Werten."""
        alt = self.konfiguration.einstellungen.get(name, RegelEinstellung(name, "aus"))
        self.konfiguration = Konfiguration.aus_dict(
            {"restriktionen": {name: {"typ": typ, "gewicht": gewicht, "parameter": dict(alt.parameter)}}},
            self.registry,
            self.konfiguration,
        )
        self._gesetzt.add(name)
        self.speichere()

    def regeln_zuruecksetzen(self) -> None:
        self.konfiguration = self._basiskonfiguration()
        self._gesetzt.clear()
        self._wende_profil()
        self.speichere()

    def lade_regeldatei(self, pfad: str | Path) -> None:
        vorher = dict(self.konfiguration.einstellungen)
        self.konfiguration = Konfiguration.aus_yaml(Path(pfad), self.registry, self.konfiguration)
        self._gesetzt |= {n for n, e in self.konfiguration.einstellungen.items() if vorher.get(n) != e}
        self.speichere()

    # ── Planen und Ergebnis (FR-04, FR-05) ──────────────────────────────────
    def planen(
        self, fortschritt: Callable[[Fortschritt], None] | None = None, abbruch: Abbruchsignal | None = None
    ) -> Plan:
        """Blockierend; die GUI ruft dies in einem Worker-Thread auf."""
        hindernisse = self.planungshindernisse()
        if hindernisse:
            raise ModellFehler("; ".join(hindernisse))
        modell = self.modell()
        plan = self._plane(modell, self._fixierungen(modell, teil=False), fortschritt, abbruch)
        self.plan, self.plan_modell = plan, modell
        if plan.status != "kein_plan":
            self.zuordnung.markiert.clear()  # „Alles neu planen" (SPEC-0010 FR-07)
            self.speichere()
        return plan

    def tabellen(self) -> dict[str, list[list]]:
        if self.plan is None or self.plan_modell is None:
            return {}
        return tabellen(self.plan, self.plan_modell)

    def exportiere(self, ziel: str | Path, ueberschreiben: bool = False) -> None:
        if self.plan is None or self.plan_modell is None:
            raise ModellFehler("Kein Plan vorhanden")
        exportiere(self.plan, self.plan_modell, ziel, ueberschreiben)
        self.letzter_exportordner = Path(ziel).parent
        self.speichere()

    # ── Tagesplan und Einladung (SPEC-0014) ─────────────────────────────────
    def setze_tagesplan(self, plan: Tagesplan) -> None:
        self.tagesplan = plan
        self.speichere()

    def setze_logo(self, pfad: Path | None) -> None:
        self.logo = pfad
        self.speichere()

    def ausgewaehlte_konferenzen(self) -> list[str]:
        return [k.name for k in self.konferenzen() if k.ausgewaehlt]

    def exportiere_einladung(self, ziel: str | Path, ueberschreiben: bool = False) -> None:
        exportiere_einladung(self.tagesplan, self.ausgewaehlte_konferenzen(), ziel, ueberschreiben, self.logo)
        self.letzter_exportordner = Path(ziel).parent
        self.speichere()

    # ── Update-Hinweis (SPEC-0015) ──────────────────────────────────────────
    def update_faellig(self, jetzt: datetime) -> bool:
        """Der Start-Check läuft höchstens einmal in 24 Stunden und nur, wenn er nicht abgeschaltet ist."""
        if not self.update_pruefung:
            return False
        return self.letzte_updatepruefung is None or jetzt - self.letzte_updatepruefung >= timedelta(hours=24)

    def markiere_update_geprueft(self, jetzt: datetime) -> None:
        self.letzte_updatepruefung = jetzt
        self.speichere()

    def blende_update_aus(self, version: str | None) -> None:
        self.ausgeblendete_version = version
        self.speichere()


__all__ = ["RegelAnsicht", "Sitzung"]
