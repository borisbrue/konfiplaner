"""Qt-freie Anwendungsschicht: Zustand und Abläufe der Anwendung (SPEC-0005 FR-11).

Die GUI zeigt `Sitzung` nur an; Fachlogik bleibt in Import, Registry, Planer und Export.
"""

from __future__ import annotations

import dataclasses
import logging
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from datetime import time
from pathlib import Path
from typing import Any

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
from konfiplaner.zeitraster import erzeuge_slots
from konfiplaner.zuordnung import LehrerAenderung, Termin, Zuordnung

log = logging.getLogger(__name__)

THEMENWERTE = ("wichtigkeit", "mindestanzahl", "dauer_min")
# Voreinstellung bei Dateien mit Konferenzterminen (SPEC-0008 FR-06): gleichzeitige Konferenzen sind erwartet
PROFIL_FESTTERMINE = {"schwerpunkte": ("weich", 1.0)}
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
class RegelAnsicht:
    """Eine Restriktion für die Regelverwaltung."""

    name: str
    typ: str
    gewicht: float
    erlaubte_typen: tuple[str, ...]
    bearbeitbar: bool  # False: braucht Pflichtparameter, nur per Konfigurationsdatei
    parameter_text: str
    beschreibung: str


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

    def _wende_profil(self) -> None:
        """Regeln, die niemand von Hand gesetzt hat, folgen der Datei (Festtermine -> weiche Schwerpunkte)."""
        fest = self.ergebnis is not None and self.ergebnis.festtermine
        standard = self._basiskonfiguration()
        for name, (typ, gewicht) in PROFIL_FESTTERMINE.items():
            if name in self._gesetzt or name not in standard.einstellungen:
                continue
            self.konfiguration.einstellungen[name] = (
                RegelEinstellung(name, typ, gewicht) if fest else standard.einstellungen[name]
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
        fix = Fixierungen(teilnahmen, termine)
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
            PlanerOptionen(zeitlimit_s=self.zeitlimit_s),
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


__all__ = ["RegelAnsicht", "Sitzung"]
