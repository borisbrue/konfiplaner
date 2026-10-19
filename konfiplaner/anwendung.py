"""Qt-freie Anwendungsschicht: Zustand und Abläufe der Anwendung (SPEC-0005 FR-11).

Die GUI zeigt `Sitzung` nur an; Fachlogik bleibt in Import, Registry, Planer und Export.
"""

from __future__ import annotations

import dataclasses
import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import time
from pathlib import Path
from typing import Any

from konfiplaner.einstellungen import Einstellungsspeicher, KeineEinstellungen
from konfiplaner.excel_export import exportiere, tabellen
from konfiplaner.excel_import import Importergebnis, importiere
from konfiplaner.modell import Modell, ModellFehler, Plan, Thema, Zeitslot
from konfiplaner.normalisierung import VORSCHLAG, Normalisierung
from konfiplaner.planer import Abbruchsignal, Fortschritt, Planer, PlanerOptionen
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

log = logging.getLogger(__name__)

THEMENWERTE = ("wichtigkeit", "mindestanzahl", "dauer_min")
# Voreinstellung bei Dateien mit Konferenzterminen (SPEC-0008 FR-06): gleichzeitige Konferenzen sind erwartet
PROFIL_FESTTERMINE = {"schwerpunkte": ("weich", 1.0)}
STANDARD_ZEITLIMIT_S = 60.0
STANDARD_ZEITRASTER = {"tage": "Samstag", "beginn": "09:00", "ende": "12:00", "laenge_min": 45}


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
        self.speichere()
        return ergebnis

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
        if not self.zeitslots:
            gruende.append("Keine Zeitslots")
        return gruende

    @property
    def planbar(self) -> bool:
        return not self.planungshindernisse()

    def modell(self) -> Modell:
        if self.ergebnis is None:
            raise ModellFehler("Keine Datei geladen")
        return self.ergebnis.baue_modell(
            list(self.themen), list(self.zeitslots), {k: set(v) for k, v in self.verfuegbarkeit.items()}
        )

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
        plan = self.planer.planen(
            modell, self.konfiguration, PlanerOptionen(zeitlimit_s=self.zeitlimit_s), fortschritt, abbruch
        )
        if self.ergebnis is not None:
            plan.warnungen += [f"{name} hat keine Konferenz" for name in self.ergebnis.ohne_konferenz]
        self.plan, self.plan_modell = plan, modell
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
