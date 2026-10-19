"""Persistenz der Benutzereinstellungen, unabhängig von Qt (SPEC-0005 FR-07/FR-09)."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Protocol

import yaml

log = logging.getLogger(__name__)


class Einstellungsspeicher(Protocol):
    def laden(self) -> dict[str, Any]: ...

    def speichern(self, daten: dict[str, Any]) -> None: ...


def standard_pfad() -> Path:
    basis = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    return basis / "konfiplaner" / "einstellungen.yaml"


class YamlEinstellungen:
    """Speichert die Einstellungen als YAML-Datei. Unlesbare Dateien gelten als leer."""

    def __init__(self, pfad: Path | None = None) -> None:
        self.pfad = Path(pfad) if pfad else standard_pfad()

    def laden(self) -> dict[str, Any]:
        try:
            daten = yaml.safe_load(self.pfad.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return {}
        except (OSError, yaml.YAMLError):
            log.warning("Einstellungen nicht lesbar: %s", self.pfad)
            return {}
        return daten if isinstance(daten, dict) else {}

    def speichern(self, daten: dict[str, Any]) -> None:
        try:
            self.pfad.parent.mkdir(parents=True, exist_ok=True)
            self.pfad.write_text(yaml.safe_dump(daten, allow_unicode=True, sort_keys=True), encoding="utf-8")
        except OSError:
            log.warning("Einstellungen nicht speicherbar: %s", self.pfad)


class KeineEinstellungen:
    """Speicher ohne Wirkung (Tests, Wegwerf-Sitzungen)."""

    def laden(self) -> dict[str, Any]:
        return {}

    def speichern(self, daten: dict[str, Any]) -> None:
        return None
